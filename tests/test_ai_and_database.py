import json
from unittest.mock import Mock, patch
from conftest import WALLET, sample, signature
from services.analyzer import analyze
from services.ai_explainer import explain
from test_rpc import response


def test_local_without_key(config,db):
    report=analyze(WALLET,sample(),6)
    for lang in ['pt','en']:
        r=explain(report,lang,True,config,db)
        assert r['source']=='local' and r['language']==lang and r['fallback_reason']=='not_configured'


def test_llm_receives_only_selected_facts(config,db):
    config['LLM_ENABLED']=True; config['LLM_API_KEY']='secret'
    answer={'done':True,'done_reason':'stop','message':{'content':'Limited observations, not proof of fraud.'}}
    with patch('services.ai_explainer.requests.post',return_value=response(envelope=answer)) as post:
        r=explain(analyze(WALLET,sample(),6),'en',True,config,db)
        body=post.call_args.kwargs['json']
        assert WALLET not in json.dumps(body)
        assert all(signature(i) not in json.dumps(body) for i in range(1,7))
        assert body['options']['num_predict']==512
        assert r['source']=='llm_unverified' and r['verified'] is False


def test_llm_failure_and_budget(config,db):
    config['LLM_ENABLED']=True; config['AI_DAILY_LIMIT']=1
    with patch('services.ai_explainer.requests.post',return_value=response(status=429)) as post:
        r=explain(analyze(WALLET,sample(),6),'pt',True,config,db)
        assert r['source']=='local'
        r=explain(analyze(WALLET,sample(),6),'pt',True,config,db)
        assert r['fallback_reason']=='daily_limit' and post.call_count==1


def test_truncated_llm_not_displayed(config,db):
    config['LLM_ENABLED']=True
    with patch('services.ai_explainer.requests.post',return_value=response(envelope={'done':True,'done_reason':'length'})):
        assert explain(analyze(WALLET,sample(),6),'pt',True,config,db)['source']=='local'


def test_database_expiry_and_quotas(db):
    db.put('expired',{'test':1},-1)
    assert db.get('expired') is None
    assert db.reserve('limit',1,60)[0] is True
    assert db.reserve('limit',1,60)[0] is False
    db.cleanup()
    with db.connect() as conn: assert conn.execute('SELECT count(*) FROM rpc_cache').fetchone()[0]==0

