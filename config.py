"""Configuration is operator-controlled. No client may supply a provider URL."""
import os
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')


def number(name, default, low, high):
    value = int(os.getenv(name, default))
    if not low <= value <= high:
        raise ValueError(f'{name} must be between {low} and {high}')
    return value


class Config:
    RPC_URL = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    DATABASE_PATH = os.getenv('DATABASE_PATH', str(BASE_DIR / 'instance/scamshield.sqlite3'))
    MAX_CONTENT_LENGTH = 4096
    MAX_TRANSACTIONS = 25
    RPC_TIMEOUT = number('RPC_TIMEOUT', 8, 2, 15)
    ANALYSIS_DEADLINE = 45
    RPC_DELAY = 0.30
    RATE_LIMIT = 6
    GLOBAL_RATE_LIMIT = 30
    LLM_ENABLED = os.getenv('LLM_ENABLED', 'false').lower() == 'true'
    LLM_URL = os.getenv('LLM_URL', 'http://127.0.0.1:11434/api/chat')
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_MODEL = os.getenv('LLM_MODEL', 'qwen2.5:1.5b')
    AI_DAILY_LIMIT = number('AI_DAILY_LIMIT', 20, 0, 100)
    TRUSTED_HOSTS = [h.strip() for h in os.getenv('TRUSTED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',') if h.strip()]
    TESTING = False


def validate_config(config):
    url = urlsplit(config['RPC_URL'])
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment:
        raise ValueError('SOLANA_RPC_URL must be an HTTPS URL without userinfo or fragment')
    llm = urlsplit(config['LLM_URL'])
    local = llm.scheme == 'http' and llm.hostname in ('127.0.0.1', 'localhost', '::1')
    if not (local or llm.scheme == 'https') or not llm.hostname or llm.username or llm.password or llm.fragment:
        raise ValueError('LLM_URL must use HTTPS, or HTTP on loopback for local Ollama')

