"""Read-only JSON-RPC, bounded transport, caching and explicit partial collection."""
import hashlib
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import requests
from .validation import valid_address, valid_signature, valid_time

MAINNET_GENESIS = '5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d'
ALLOWED_METHODS = {'getGenesisHash', 'getAccountInfo', 'getSignaturesForAddress', 'getTransaction'}


def iso(timestamp=None):
    return datetime.fromtimestamp(time.time() if timestamp is None else timestamp, timezone.utc).isoformat().replace('+00:00', 'Z')


class RPCError(Exception):
    def __init__(self, code='rpc_unavailable', status=503, retry_after=0):
        # Never propagate provider messages or URLs: they can contain API keys.
        super().__init__(code)
        self.code, self.status, self.retry_after = code, status, retry_after


def retry_seconds(header):
    try:
        seconds = float(header)
    except (ValueError, TypeError):
        try:
            seconds = parsedate_to_datetime(header).timestamp() - time.time()
        except (ValueError, TypeError, OverflowError):
            seconds = 2
    return max(1, min(3600, int(seconds)))


class SolanaRPC:
    def __init__(self, config, database, session=None):
        self.config, self.db = config, database
        self.session = session or requests.Session()
        self.cache_hits = 0
        self.fetch_times = []

    def close(self):
        self.session.close()

    def call(self, method, params, ttl=60):
        if method not in ALLOWED_METHODS:
            raise ValueError('Read-only RPC method required')
        key = hashlib.sha256(json.dumps([self.config['RPC_URL'], method, params], sort_keys=True).encode()).hexdigest()
        cached = self.db.get(key)
        if cached:
            self.cache_hits += 1
            self.fetch_times.append(cached[1])
            return cached[0]
        body = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
        for attempt in range(2):
            try:
                with self.session.post(self.config['RPC_URL'], json=body,
                                       timeout=(3, self.config['RPC_TIMEOUT']),
                                       allow_redirects=False, stream=True) as response:
                    if response.status_code == 429:
                        wait = retry_seconds(response.headers.get('Retry-After'))
                        if attempt == 0 and wait <= 2:
                            time.sleep(wait)
                            continue
                        raise RPCError('rpc_rate_limited', 429, wait)
                    if response.status_code >= 500:
                        if attempt == 0:
                            time.sleep(.5)
                            continue
                        raise RPCError()
                    if response.status_code != 200:
                        raise RPCError('rpc_unavailable', 503)
                    chunks = []
                    size = 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > 2_000_000:
                            raise RPCError('rpc_invalid_response', 502)
                        chunks.append(chunk)
                    data = json.loads(b''.join(chunks))
            except requests.RequestException:
                if attempt == 0:
                    time.sleep(.5)
                    continue
                raise RPCError() from None
            except (ValueError, UnicodeError):
                raise RPCError('rpc_invalid_response', 502) from None
            if not isinstance(data, dict) or data.get('jsonrpc') != '2.0' or data.get('id') != 1:
                raise RPCError('rpc_invalid_response', 502)
            if 'error' in data:
                raise RPCError('rpc_error', 502)
            if 'result' not in data:
                raise RPCError('rpc_invalid_response', 502)
            result = data['result']
            self.fetch_times.append(time.time())
            if result is not None:
                self.db.put(key, result, ttl)
            return result
        raise RPCError()

    def collect(self, wallet, limit):
        start = time.monotonic()
        if self.call('getGenesisHash', [], 3600) != MAINNET_GENESIS:
            raise RPCError('wrong_network', 503)
        warnings = []
        account = {'status': 'unavailable'}
        try:
            result = self.call('getAccountInfo', [wallet, {'encoding': 'base64', 'dataSlice': {'offset': 0, 'length': 0}, 'commitment': 'finalized'}])
            if not isinstance(result, dict) or 'value' not in result:
                raise RPCError('rpc_invalid_response', 502)
            value = result['value']
            if value is None:
                account = {'status': 'not_found'}
            elif (isinstance(value, dict) and type(value.get('executable')) is bool
                  and valid_address(value.get('owner'))):
                account = {'status': 'available', 'owner': value['owner'], 'executable': value['executable']}
            else:
                raise RPCError('rpc_invalid_response', 502)
        except RPCError as exc:
            warnings.append('account_' + exc.code)
        raw = self.call('getSignaturesForAddress', [wallet, {'limit': limit, 'commitment': 'finalized'}])
        if not isinstance(raw, list) or len(raw) > limit:
            raise RPCError('rpc_invalid_response', 502)
        signatures, seen = [], set()
        for entry in raw:
            if not isinstance(entry, dict) or not valid_signature(entry.get('signature')) or entry['signature'] in seen or 'err' not in entry:
                continue
            seen.add(entry['signature'])
            signatures.append({'signature': entry['signature'],
                               'blockTime': entry.get('blockTime') if valid_time(entry.get('blockTime')) else None,
                               'failed': entry['err'] is not None})
        dropped = len(raw) - len(signatures)
        if dropped:
            warnings.append('invalid_or_duplicate_signatures')
        transactions = {}
        for entry in signatures:
            if time.monotonic() - start > self.config['ANALYSIS_DEADLINE']:
                warnings.append('collection_deadline'); break
            signature = entry['signature']
            try:
                tx = self.call('getTransaction', [signature, {'encoding': 'jsonParsed', 'commitment': 'finalized', 'maxSupportedTransactionVersion': 0}], 3600)
                if valid_transaction(tx, signature, wallet):
                    transactions[signature] = tx
                else:
                    warnings.append('transaction_unavailable_or_incomplete')
            except RPCError as exc:
                warnings.append(exc.code)
                if exc.status in (429, 503):
                    break
            time.sleep(self.config.get('RPC_DELAY', .3))
        return {'signatures': signatures, 'transactions': transactions, 'account': account,
                'warnings': list(dict.fromkeys(warnings)), 'dropped_records': dropped,
                'provenance': {'source': 'solana_json_rpc', 'commitment': 'finalized',
                               'cache_hits': self.cache_hits,
                               'oldest_fetch_at': iso(min(self.fetch_times)) if self.fetch_times else None,
                               'newest_fetch_at': iso(max(self.fetch_times)) if self.fetch_times else None}}


def valid_transaction(tx, signature, wallet):
    if not isinstance(tx, dict) or not isinstance(tx.get('meta'), dict) or 'err' not in tx['meta']:
        return False
    transaction = tx.get('transaction')
    if not isinstance(transaction, dict) or not isinstance(transaction.get('signatures'), list) or signature not in transaction['signatures']:
        return False
    message = transaction.get('message')
    if not isinstance(message, dict) or not isinstance(message.get('instructions'), list) or not isinstance(message.get('accountKeys'), list):
        return False
    keys = [k.get('pubkey') if isinstance(k, dict) else k for k in message['accountKeys']]
    return wallet in keys

