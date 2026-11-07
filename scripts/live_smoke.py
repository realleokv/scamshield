"""Explicit real read-only integration check. Not part of the offline pytest suite."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import Config
from database.database import Database
from services.solana_rpc import SolanaRPC, RPCError
from services.analyzer import analyze
from services.validation import valid_address

parser=argparse.ArgumentParser()
parser.add_argument('--wallet',default='vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg')
parser.add_argument('--limit',type=int,default=5)
parser.add_argument('--output',default='live_report.json')
args=parser.parse_args()
if not valid_address(args.wallet) or not 1<=args.limit<=25:parser.error('Valid wallet and limit 1–25 required')
config={key:getattr(Config,key) for key in dir(Config) if key.isupper()}
db=Database(config['DATABASE_PATH']);rpc=SolanaRPC(config,db)
try:
    report=analyze(args.wallet,rpc.collect(args.wallet,args.limit),args.limit)
    report['capture_note']='REAL RPC CAPTURE. Historical snapshot, not a live display or reputation claim.'
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('wallet','network','status','signatures_observed','transactions_analyzed','alerts','analyzed_at')},ensure_ascii=False))
    if report['transactions_analyzed']==0:
        print('No transaction details returned; full-path integration remains unverified.',file=sys.stderr)
        sys.exit(2)
except RPCError as exc:
    print(json.dumps({'status':'failed','code':exc.code}),file=sys.stderr);sys.exit(1)
finally:rpc.close()
