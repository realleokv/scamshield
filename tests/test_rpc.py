import json
from unittest.mock import Mock
import pytest
import requests
from conftest import WALLET, signature, transaction
from services.solana_rpc import SolanaRPC, RPCError, MAINNET_GENESIS, valid_transaction


def response(result=None,status=200,headers=None,envelope=None):
    r=Mock();r.status_code=status;r.headers=headers or {}
    r.__enter__=Mock(return_value=r);r.__exit__=Mock(return_value=False)
    raw=json.dumps(envelope if envelope is not None else {'jsonrpc':'2.0','id':1,'result':result}).encode()
    r.iter_content.return_value=[raw]
    return r


def client(config,db,responses):
    session=Mock();session.post.side_effect=responses
    return SolanaRPC(config,db,session)


def test_cache_prevents_second_network_call(config,db):
    c=client(config,db,[response(MAINNET_GENESIS)])
    assert c.call('getGenesisHash',[])==c.call('getGenesisHash',[])
    assert c.cache_hits==1 and c.session.post.call_count==1


def test_null_not_cached(config,db):
    c=client(config,db,[response(),response()])
    assert c.call('getTransaction',[]) is None
    assert c.call('getTransaction',[]) is None
    assert c.session.post.call_count==2


@pytest.mark.parametrize('payload',[{},[],{'jsonrpc':'2.0','id':2,'result':[]},{'jsonrpc':'2.0','id':1,'error':{'message':'secret'}}])
def test_rpc_bad_envelope(config,db,payload):
    c=client(config,db,[response(envelope=payload)])
    with pytest.raises(RPCError) as e:c.call('getGenesisHash',[])
    assert 'secret' not in str(e.value)


def test_connection_failure(config,db,monkeypatch):
    monkeypatch.setattr('services.solana_rpc.time.sleep',lambda _:None)
    c=client(config,db,[requests.ConnectionError('url secret'),requests.Timeout('secret')])
    with pytest.raises(RPCError) as e:c.call('getGenesisHash',[])
    assert e.value.status==503 and 'secret' not in str(e.value)
    assert c.session.post.call_count==2


def test_429_does_not_sleep_long(config,db):
    c=client(config,db,[response(status=429,headers={'Retry-After':'30'})])
    with pytest.raises(RPCError) as e:c.call('getGenesisHash',[])
    assert e.value.status==429 and e.value.retry_after==30


def test_short_429_retry(config,db,monkeypatch):
    monkeypatch.setattr('services.solana_rpc.time.sleep',lambda _:None)
    c=client(config,db,[response(status=429,headers={'Retry-After':'1'}),response(MAINNET_GENESIS)])
    assert c.call('getGenesisHash',[])==MAINNET_GENESIS


def test_read_only_method_allowlist(config,db):
    c=client(config,db,[])
    with pytest.raises(ValueError):c.call('sendTransaction',[])
    c.session.post.assert_not_called()


def test_wrong_network(config,db):
    c=client(config,db,[response('devnet-genesis')])
    with pytest.raises(RPCError) as e:c.collect(WALLET,1)
    assert e.value.code=='wrong_network'


def test_full_mainnet_genesis_from_live_protocol():
    from services.validation import valid_base58
    assert valid_base58(MAINNET_GENESIS,32)
    # A CAIP-2 reference is truncated and must not be accepted as the RPC hash.
    assert len(MAINNET_GENESIS)>32


def test_missing_account_does_not_prevent_history(config,db):
    c=client(config,db,[response(MAINNET_GENESIS),response({'value':None}),response([])])
    s=c.collect(WALLET,5)
    assert s['account']['status']=='not_found' and s['signatures']==[]


def test_partial_collection(config,db):
    c=client(config,db,[response(MAINNET_GENESIS),response({'value':None}),
                       response([{'signature':signature(1),'err':None,'blockTime':1700000000}]),response(None)])
    s=c.collect(WALLET,1)
    assert s['transactions']=={} and s['warnings']


def test_collect_valid_details_and_drop_duplicates(config,db):
    entries=[{'signature':signature(1),'err':None,'blockTime':1700000000}]*2
    c=client(config,db,[response(MAINNET_GENESIS),response({'value':None}),response(entries),response(transaction())])
    s=c.collect(WALLET,2)
    assert len(s['transactions'])==1 and s['dropped_records']==1


@pytest.mark.parametrize('tx',[None,{}, {'meta':None}, {'meta':{'err':None},'transaction':{}}])
def test_incomplete_transaction(tx):assert not valid_transaction(tx,signature(1),WALLET)


def test_mismatched_transaction_rejected():
    assert not valid_transaction(transaction(2),signature(1),WALLET)

