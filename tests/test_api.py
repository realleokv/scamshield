import json
from unittest.mock import Mock
import pytest
from conftest import WALLET, sample
from services.solana_rpc import RPCError


def fake_rpc(app,data=None,error=None):
    rpc=Mock()
    if error:rpc.collect.side_effect=error
    else:rpc.collect.return_value=data if data is not None else sample()
    app.extensions['rpc_factory']=lambda:rpc
    return rpc


def test_pages_and_health(app):
    c=app.test_client()
    for path in ['/','/about','/how-it-works','/api/health']:
        r=c.get(path);assert r.status_code==200
        assert 'frame-ancestors' in r.headers['Content-Security-Policy']
    assert c.get('/api/health').json['rpc_checked'] is False


@pytest.mark.parametrize('body',[{},[],{'wallet':'bad'}, {'wallet':WALLET,'limit':True}, {'wallet':WALLET,'limit':26}, {'wallet':WALLET,'limit':0}, {'wallet':WALLET,'use_ai':'yes'}, {'wallet':WALLET,'language':'xx'}, {'wallet':WALLET,'rpc_url':'https://secret.test'}])
def test_invalid_input_does_not_call_rpc(app,body):
    rpc=fake_rpc(app)
    r=app.test_client().post('/api/analyze',json=body)
    assert r.status_code==400 and 'error' in r.json
    rpc.collect.assert_not_called()


def test_request_size_and_media_type(app):
    c=app.test_client()
    assert c.post('/api/analyze',data='not json').status_code==415
    assert c.post('/api/analyze',data='x'*5000,content_type='application/json').status_code==413
    assert c.post('/api/analyze',data='{',content_type='application/json').status_code==400


def test_report_and_history(app):
    rpc=fake_rpc(app)
    r=app.test_client().post('/api/analyze',json={'wallet':WALLET,'limit':6})
    assert r.status_code==200
    assert r.json['transactions_analyzed']==6 and r.json['explanation']['source']=='local'
    assert r.json['network']=='mainnet-beta' and r.json['request_id']
    assert 'rpc.example' not in r.get_data(as_text=True)
    with app.extensions['db'].connect() as conn:
        assert conn.execute('SELECT count(*) FROM analysis_history').fetchone()[0]==1
    rpc.close.assert_called_once()


def test_empty_report(app):
    fake_rpc(app,sample(0))
    r=app.test_client().post('/api/analyze',json={'wallet':WALLET})
    assert r.status_code==200 and r.json['experimental_alert_index']['value'] is None


@pytest.mark.parametrize('code,status',[('rpc_unavailable',503),('rpc_invalid_response',502),('rpc_rate_limited',429)])
def test_provider_failures(app,code,status):
    rpc=fake_rpc(app,error=RPCError(code,status,10 if status==429 else 0))
    r=app.test_client().post('/api/analyze',json={'wallet':WALLET})
    assert r.status_code==status and r.json['error']['code']==code
    if status==429:assert r.headers['Retry-After']=='10'
    rpc.close.assert_called_once()


def test_rate_limit_ignores_forwarded_ip(app):
    app.config['RATE_LIMIT']=1;fake_rpc(app)
    c=app.test_client()
    assert c.post('/api/analyze',json={'wallet':WALLET}).status_code==200
    r=c.post('/api/analyze',json={'wallet':WALLET},headers={'X-Forwarded-For':'8.8.8.8'})
    assert r.status_code==429


def test_cross_origin_is_rejected(app):
    fake_rpc(app)
    assert app.test_client().post('/api/analyze',json={'wallet':WALLET},headers={'Origin':'https://other.test'}).status_code==403


def test_exception_does_not_leak_details(app):
    fake_rpc(app,error=RuntimeError('key=TOP_SECRET'))
    r=app.test_client().post('/api/analyze',json={'wallet':WALLET})
    assert r.status_code==500 and 'TOP_SECRET' not in r.get_data(as_text=True)

