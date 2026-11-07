import copy
import pytest
from conftest import WALLET, DEST, sample, signature, transaction
from services.analyzer import analyze, extract_transfers
from services.validation import valid_address, valid_signature


@pytest.mark.parametrize('value',[None,'','0'*32,'O'*32,'l'*32,'https://x.com','1'*31,'1'*33,'1'*45,123,[], ' '+WALLET])
def test_invalid_addresses(value): assert not valid_address(value)


@pytest.mark.parametrize('value',[WALLET, DEST, '11111111111111111111111111111111', 'vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg'])
def test_valid_addresses(value): assert valid_address(value)


def test_burst_and_repetition():
    r=analyze(WALLET,sample(),6)
    assert r['alerts']==['ACTIVITY_BURST','REPETITIVE_TRANSFERS']
    assert r['experimental_alert_index']['value']==100
    assert r['experimental_alert_index']['is_probability'] is False
    assert all(valid_signature(e['signature']) for i in r['indicators'] for e in i['evidence'])


def test_coverage_does_not_add_points():
    s=sample(spacing=400)
    for i,t in enumerate(s['transactions'].values()): t['transaction']['message']['instructions'][0]['parsed']['info']['lamports']=100+i
    r=analyze(WALLET,s,6)
    assert r['experimental_alert_index']['value']==0
    assert r['indicators'][2]['status']=='triggered'


def test_empty_history_is_not_safe():
    r=analyze(WALLET,sample(0),25)
    assert r['transactions_analyzed']==0 and r['observed_period']['start'] is None
    assert r['experimental_alert_index']['value'] is None
    assert r['severity']=='unknown'


def test_missing_timestamps():
    s=sample();s['signatures'][0]['blockTime']=None
    r=analyze(WALLET,s,6)
    assert r['indicators'][0]['status']=='insufficient_data'
    assert r['experimental_alert_index']['value'] is None
    assert r['experimental_alert_index']['observed_points']==50


def test_missing_details_preserve_observations():
    s=sample();s['transactions']={}
    r=analyze(WALLET,s,6)
    assert r['status']=='partial' and r['transactions_unavailable']==6
    assert r['indicators'][1]['status']=='insufficient_data'
    assert r['indicators'][0]['status']=='triggered'


def test_three_instructions_in_one_transaction_are_not_three_transfers():
    s=sample(1);t=s['transactions'][signature(1)]
    t['transaction']['message']['instructions']*=4
    assert analyze(WALLET,s,1)['indicators'][1]['status']=='insufficient_data'


@pytest.mark.parametrize('mutation',['failed','incoming','self','token','float','negative','bad_dest','bad_info','with_seed'])
def test_untrusted_or_out_of_scope_transfers_not_counted(mutation):
    t=transaction();item=t['transaction']['message']['instructions'][0];info=item['parsed']['info']
    if mutation=='failed':t['meta']['err']={'InstructionError':[0,'error']}
    elif mutation=='incoming':info['source'],info['destination']=DEST,WALLET
    elif mutation=='self':info['destination']=WALLET
    elif mutation=='token':item['programId']=DEST
    elif mutation=='float':info['lamports']=1.5
    elif mutation=='negative':info['lamports']=-5
    elif mutation=='bad_dest':info['destination']='https://bad.test'
    elif mutation=='bad_info':item['parsed']['info']=[]
    elif mutation=='with_seed':item['parsed']['type']='transferWithSeed'
    assert extract_transfers(t,WALLET)==[]


def test_inner_instructions_are_supported():
    t=transaction();t['meta']['innerInstructions']=[{'index':0,'instructions':t['transaction']['message']['instructions']}]
    t['transaction']['message']['instructions']=[]
    assert len(extract_transfers(t,WALLET))==1


def test_burst_threshold_requires_half_sample():
    s=sample(12,1000)
    for i in range(5):s['signatures'][i]['blockTime']=1700000000+i
    assert analyze(WALLET,s,12)['indicators'][0]['status']=='not_triggered'

