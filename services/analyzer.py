"""Pure, transparent heuristics. Observations are never a probability of fraud."""
from collections import defaultdict
from .validation import valid_address, valid_time
from .solana_rpc import iso

SYSTEM_PROGRAM = '11111111111111111111111111111111'


def evidence(signature, **extra):
    return {'signature': signature, 'explorer_url': f'https://explorer.solana.com/tx/{signature}', **extra}


def extract_transfers(tx, wallet):
    if tx['meta']['err'] is not None:
        return []
    instructions = list(tx['transaction']['message']['instructions'])
    inner = tx['meta'].get('innerInstructions')
    if isinstance(inner, list):
        for group in inner:
            if isinstance(group, dict) and isinstance(group.get('instructions'), list):
                instructions.extend(group['instructions'])
    found = []
    for item in instructions:
        if not isinstance(item, dict) or item.get('programId') != SYSTEM_PROGRAM:
            continue
        parsed = item.get('parsed')
        if not isinstance(parsed, dict) or parsed.get('type') != 'transfer':
            continue
        info = parsed.get('info')
        if not isinstance(info, dict):
            continue
        amount, source, dest = info.get('lamports'), info.get('source'), info.get('destination')
        if (source == wallet and valid_address(dest) and source != dest
                and type(amount) is int and 0 < amount <= 2**64 - 1):
            found.append({'source': source, 'destination': dest, 'lamports': str(amount)})
    return found


def indicator(id_, title, category, description, method, status, metrics, proofs, limitations):
    return {'id': id_, 'title': title, 'category': category, 'description': description,
            'method': method, 'status': status,
            'severity': 'medium' if status == 'triggered' and category == 'behavior' else ('info' if category == 'coverage' else 'none'),
            'metrics': metrics, 'evidence': proofs, 'limitations': limitations}


def analyze(wallet, sample, limit):
    signatures, txs = sample['signatures'], sample['transactions']
    count = len(signatures)
    timed = sorted([x for x in signatures if valid_time(x.get('blockTime'))], key=lambda x: x['blockTime'])
    best, left = [], 0
    for right, row in enumerate(timed):
        while row['blockTime'] - timed[left]['blockTime'] > 60:
            left += 1
        if right - left + 1 > len(best):
            best = timed[left:right + 1]
    burst_status = 'insufficient_data'
    if len(timed) >= 5 and len(timed) == count:
        burst_status = 'triggered' if len(best) >= 5 and len(best) / len(timed) >= .5 else 'not_triggered'
    burst = indicator('ACTIVITY_BURST', 'Activity Burst', 'behavior',
                      'Concentração de referências ao endereço em um período curto.',
                      'Pelo menos 5 assinaturas em 60 s e 50% da amostra datada; exige 5 ou mais datas e nenhuma ausente.',
                      burst_status, {'max_in_60s': len(best), 'timestamped_signatures': len(timed),
                                     'fraction': round(len(best) / len(timed), 4) if timed else None},
                      [evidence(x['signature'], observed_at=iso(x['blockTime'])) for x in best] if burst_status == 'triggered' else [],
                      ['Referenciar o endereço não significa que ele iniciou a transação.',
                       'Bots, serviços legítimos e tentativas falhadas também podem formar rajadas.'])
    groups = defaultdict(set)
    eligible = set()
    transactions = []
    for row in signatures:
        sig = row['signature']; tx = txs.get(sig)
        transfers = extract_transfers(tx, wallet) if tx else []
        for transfer in transfers:
            groups[(transfer['source'], transfer['destination'], transfer['lamports'])].add(sig)
            eligible.add(sig)
        transactions.append({**evidence(sig), 'observed_at': iso(row['blockTime']) if row['blockTime'] else None,
                             'detail_status': 'available' if tx else 'unavailable',
                             'execution_status': ('failed' if tx['meta']['err'] is not None else 'success') if tx else ('failed' if row['failed'] else 'unknown'),
                             'outgoing_sol_transfers': transfers})
    repeated = [(key, sorted(sigs)) for key, sigs in groups.items() if len(sigs) >= 3]
    repeat_status = 'triggered' if repeated else ('not_triggered' if len(eligible) >= 3 and len(txs) == count else 'insufficient_data')
    repeat_proofs = []
    for (_, dest, amount), sigs in repeated:
        repeat_proofs.extend(evidence(sig, destination=dest, lamports=amount) for sig in sigs)
    repetitive = indicator('REPETITIVE_TRANSFERS', 'Repetitive Transfers', 'behavior',
                           'Saídas de SOL com mesmo destino e valor exato em transações distintas.',
                           'System Program transfer bem-sucedido; grupo por origem, destino e lamports em pelo menos 3 assinaturas distintas.',
                           repeat_status, {'recognized_transfer_transactions': len(eligible), 'repeated_groups': len(repeated),
                                           'largest_group': max((len(v) for v in groups.values()), default=0)},
                           repeat_proofs,
                           ['Somente SOL nativo parsed; tokens SPL, swaps e transferWithSeed não são interpretados.',
                            'Pagamentos recorrentes legítimos podem acionar a regra.',
                            'Alterações líquidas de saldo não são tratadas como transferências.'])
    span = timed[-1]['blockTime'] - timed[0]['blockTime'] if timed else None
    unavailable = count - len(txs)
    reasons = []
    if count < 10: reasons.append('Menos de 10 assinaturas observadas.')
    if span is None or span < 86400: reasons.append('Período observado inferior a 24 horas ou desconhecido.')
    if len(timed) < count: reasons.append('Há assinaturas sem data utilizável.')
    if unavailable: reasons.append('Há detalhes de transação indisponíveis.')
    if sample.get('dropped_records'): reasons.append('Registros inválidos ou duplicados foram descartados.')
    coverage = indicator('LIMITED_OBSERVED_HISTORY', 'Limited Observed History', 'coverage',
                         'Cobertura limitada da amostra; não é evidência de fraude.',
                         'Menos de 10 assinaturas, menos de 24 horas, datas ausentes, detalhes ausentes ou registros descartados.',
                         'triggered' if reasons else 'not_triggered',
                         {'signatures_observed': count, 'span_seconds': span, 'unavailable_details': unavailable,
                          'dropped_records': sample.get('dropped_records', 0)}, [], reasons or ['Mesmo uma amostra ampla não cobre o histórico completo.'])
    behavior = [burst, repetitive]
    observed = sum(50 for x in behavior if x['status'] == 'triggered')
    complete_score = all(x['status'] != 'insufficient_data' for x in behavior)
    partial = bool(unavailable or sample.get('warnings') or sample.get('dropped_records'))
    limitations = ['A análise cobre somente a amostra solicitada, não o histórico total nem a idade do endereço.',
                   'Alertas indicam comportamento, não fraude comprovada. Ausência de alertas não garante segurança.',
                   'Este MVP não simula uma transação futura nem detecta todos os golpes.',
                   'O parser reconhece apenas saídas explícitas de SOL nativo; saldos líquidos não provam transferências.']
    if count == limit: limitations.append('O limite da amostra foi atingido; pode existir mais atividade não consultada.')
    if sample['account'].get('executable') or sample['account'].get('owner') not in (None, SYSTEM_PROGRAM):
        limitations.append('O endereço pode representar programa ou conta de dados; não presuma uma carteira pessoal.')
    limitations += reasons
    if sample.get('warnings'): limitations.append('Coleta parcial: ' + ', '.join(sample['warnings']))
    return {'report_version': '1.0', 'wallet': wallet, 'network': 'mainnet-beta',
            'status': 'partial' if partial else 'completed', 'sample_limit': limit,
            'signatures_observed': count, 'transactions_analyzed': len(txs),
            'transactions_unavailable': unavailable,
            'successful_transactions': sum(tx['meta']['err'] is None for tx in txs.values()),
            'observed_period': {'start': iso(timed[0]['blockTime']) if timed else None,
                                'end': iso(timed[-1]['blockTime']) if timed else None, 'span_seconds': span},
            'account': sample['account'], 'indicators': behavior + [coverage],
            'alerts': [x['id'] for x in behavior if x['status'] == 'triggered'],
            'experimental_alert_index': {'name': 'Índice Experimental de Alertas',
                                        'value': observed if complete_score else None, 'observed_points': observed,
                                        'maximum': 100, 'weights': {'ACTIVITY_BURST': 50, 'REPETITIVE_TRANSFERS': 50, 'LIMITED_OBSERVED_HISTORY': 0},
                                        'is_probability': False},
            'severity': 'medium' if observed else ('none' if complete_score else 'unknown'),
            'transactions': transactions, 'limitations': list(dict.fromkeys(limitations)),
            'provenance': {**sample['provenance'], 'collection_partial': partial}, 'analyzed_at': iso()}

