"""All fixture addresses/transactions here are synthetic; never feed the live UI."""
import copy
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from database.database import Database
from services.validation import ALPHABET
from services.analyzer import SYSTEM_PROGRAM


def encode(data):
    n = int.from_bytes(data, 'big'); out = ''
    while n:
        n, mod = divmod(n, 58); out = ALPHABET[mod] + out
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + out


WALLET = encode(bytes([7]) * 32)
DEST = encode(bytes([8]) * 32)


def signature(i): return encode(i.to_bytes(64, 'big'))


def transaction(i=1, amount=1_000_000, destination=DEST):
    return {'blockTime': 1700000000 + i, 'version': 'legacy', 'slot': 1,
            'meta': {'err': None, 'innerInstructions': []},
            'transaction': {'signatures': [signature(i)],
                            'message': {'accountKeys': [{'pubkey': WALLET}, {'pubkey': destination}],
                                        'instructions': [{'program': 'system', 'programId': SYSTEM_PROGRAM,
                                                          'parsed': {'type': 'transfer', 'info': {'source': WALLET, 'destination': destination, 'lamports': amount}}}]}}}


def sample(n=6, spacing=5):
    return {'signatures': [{'signature': signature(i), 'blockTime': 1700000000 + i * spacing, 'failed': False} for i in range(1, n+1)],
            'transactions': {signature(i): transaction(i) for i in range(1, n+1)},
            'account': {'status': 'available', 'owner': SYSTEM_PROGRAM, 'executable': False},
            'warnings': [], 'dropped_records': 0,
            'provenance': {'source': 'solana_json_rpc', 'commitment': 'finalized', 'cache_hits': 0,
                           'oldest_fetch_at': '2026-11-07T00:00:00Z', 'newest_fetch_at': '2026-11-07T00:00:00Z'}}


@pytest.fixture
def db(tmp_path): return Database(str(tmp_path / 'test.sqlite3'))


@pytest.fixture
def config(tmp_path):
    return {'RPC_URL':'https://rpc.example.test/?key=secret', 'RPC_TIMEOUT':2, 'RPC_DELAY':0,
            'ANALYSIS_DEADLINE':45, 'LLM_ENABLED':False, 'LLM_API_KEY':'', 'LLM_MODEL':'qwen2.5:1.5b',
            'LLM_URL':'http://127.0.0.1:11434/api/chat',
            'AI_DAILY_LIMIT':2, 'DATABASE_PATH':str(tmp_path/'api.sqlite3'),
            'TESTING':True, 'RATE_LIMIT':100, 'GLOBAL_RATE_LIMIT':200}


@pytest.fixture
def app(config):
    from app import create_app
    return create_app(config)

