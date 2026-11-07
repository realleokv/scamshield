import hashlib
import json
import logging
import secrets
import threading
import time
from urllib.parse import urlsplit
from flask import Flask, jsonify, render_template, request, g
from werkzeug.exceptions import HTTPException
from config import Config, validate_config
from database.database import Database
from services.validation import valid_address
from services.solana_rpc import SolanaRPC, RPCError
from services.analyzer import analyze
from services.ai_explainer import explain

MESSAGES = {
    'rpc_unavailable': 'RPC indisponível. Aguarde ou configure outro provedor Mainnet no .env.',
    'rpc_rate_limited': 'O RPC limitou as consultas. Aguarde o tempo indicado e tente uma amostra menor.',
    'rpc_invalid_response': 'O RPC retornou dados incompletos ou incompatíveis.',
    'rpc_error': 'O RPC não conseguiu atender à consulta.',
    'wrong_network': 'O endpoint configurado não foi identificado como Solana Mainnet.',
}


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides: app.config.update(overrides)
    validate_config(app.config)
    db = Database(app.config['DATABASE_PATH'])
    gate = threading.BoundedSemaphore(2)
    salt = secrets.token_bytes(32)
    app.extensions['db'] = db
    app.extensions['rpc_factory'] = lambda: SolanaRPC(app.config, db)
    app.json.ensure_ascii = False

    def failure(code, message, status, retry_after=0):
        response = jsonify(error={'code': code, 'message': message, 'retryable': status in (429, 502, 503),
                                  **({'retry_after_seconds': retry_after} if retry_after else {})}, request_id=getattr(g, 'request_id', 'unavailable'))
        response.status_code = status
        if retry_after: response.headers['Retry-After'] = str(retry_after)
        return response

    @app.before_request
    def begin():
        g.request_id = secrets.token_hex(8)
        g.started = time.monotonic()
        if request.path == '/api/analyze':
            origin = request.headers.get('Origin')
            if origin:
                parsed = urlsplit(origin)
                if parsed.netloc != request.host or parsed.scheme != request.scheme:
                    return failure('cross_origin', 'Origem da requisição não permitida.', 403)
            db.cleanup()
            ip = hashlib.sha256(salt + (request.remote_addr or 'unknown').encode()).hexdigest()
            for bucket, maximum in [('ip:' + ip, app.config['RATE_LIMIT']), ('global', app.config['GLOBAL_RATE_LIMIT'])]:
                ok, wait = db.reserve(bucket, maximum, 60)
                if not ok: return failure('rate_limited', 'Muitas análises. Aguarde antes de tentar novamente.', 429, wait)

    @app.after_request
    def finish(response):
        response.headers.update({'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
                                 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
                                 'Cache-Control': 'no-store'})
        if request.path.startswith('/api/'):
            app.logger.info(json.dumps({'event': 'api_response', 'request_id': getattr(g, 'request_id', None),
                                        'status': response.status_code,
                                        'duration_ms': round((time.monotonic() - getattr(g, 'started', time.monotonic())) * 1000)}))
        return response

    @app.get('/')
    def index(): return render_template('index.html')

    @app.get('/about')
    def about(): return render_template('about.html')

    @app.get('/how-it-works')
    def how(): return render_template('how_it_works.html')

    @app.get('/api/health')
    def health():
        with db.connect() as conn: conn.execute('SELECT 1')
        return jsonify(status='ok', version='1.0', network='mainnet-beta', ai_configured=app.config['LLM_ENABLED'], rpc_checked=False)

    @app.post('/api/analyze')
    def analyze_wallet():
        if not request.is_json: return failure('unsupported_media_type', 'Envie Content-Type application/json.', 415)
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or set(body) - {'wallet', 'limit', 'language', 'use_ai'}:
            return failure('invalid_request', 'Envie somente wallet, limit, language e use_ai em um objeto JSON.', 400)
        wallet = body.get('wallet')
        wallet = wallet.strip() if isinstance(wallet, str) else wallet
        if not valid_address(wallet): return failure('invalid_wallet', 'Informe um endereço Base58 de 32 bytes.', 400)
        limit, language, use_ai = body.get('limit', 25), body.get('language', 'pt'), body.get('use_ai', False)
        if type(limit) is not int or not 1 <= limit <= 25 or language not in ('pt', 'en') or type(use_ai) is not bool:
            return failure('invalid_request', 'limit deve ser inteiro de 1 a 25; language pt/en; use_ai booleano.', 400)
        if not gate.acquire(blocking=False): return failure('busy', 'Duas análises já estão em andamento. Tente novamente.', 503, 10)
        rpc = None
        try:
            rpc = app.extensions['rpc_factory']()
            sample = rpc.collect(wallet, limit)
            report = analyze(wallet, sample, limit)
            report['explanation'] = explain(report, language, use_ai, app.config, db)
            report['request_id'] = g.request_id
            db.save_report(report)
            db.cleanup()
            return jsonify(report)
        except RPCError as exc:
            return failure(exc.code, MESSAGES.get(exc.code, 'Falha ao consultar a blockchain.'), exc.status, exc.retry_after)
        finally:
            if rpc is not None: rpc.close()
            gate.release()

    @app.errorhandler(Exception)
    def error(exc):
        if isinstance(exc, HTTPException):
            codes = {413: 'payload_too_large', 404: 'not_found', 405: 'method_not_allowed', 400: 'invalid_request'}
            return failure(codes.get(exc.code, 'http_error'), 'Requisição inválida ou recurso indisponível.', exc.code)
        # Log class only; exception strings may embed provider secrets.
        app.logger.error(json.dumps({'event': 'internal_error', 'type': type(exc).__name__, 'request_id': getattr(g, 'request_id', None)}))
        return failure('internal_error', 'Falha interna. Consulte o identificador da requisição nos logs.', 500)

    return app


logging.basicConfig(level=logging.INFO, format='%(message)s')
app = create_app()
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

