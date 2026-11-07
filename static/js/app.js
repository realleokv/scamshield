'use strict';
const $ = (selector) => document.querySelector(selector);
const node = (tag, className, text) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = String(text);
  return el;
};
const date = (value) => value ? new Date(value).toLocaleString('pt-BR') : 'Desconhecido';
const short = (value) => value.slice(0, 10) + '…' + value.slice(-6);
const base58 = /^[1-9A-HJ-NP-Za-km-z]+$/;
const link = (kind, value, label) => {
  const a = node('a', '', label);
  if (typeof value === 'string' && base58.test(value) && value.length <= 88) {
    a.href = `https://explorer.solana.com/${kind}/${encodeURIComponent(value)}`;
    a.target = '_blank'; a.rel = 'noopener noreferrer';
  }
  return a;
};
const statusNames = {triggered: 'Observado', not_triggered: 'Não observado', insufficient_data: 'Dados insuficientes'};
const fallbackNames = {not_requested: 'Resumo local por regras, sem IA.', not_configured: 'IA não configurada. Resumo local por regras.', daily_limit: 'Cota diária de IA atingida. Resumo local.', provider_unavailable: 'IA indisponível. Resumo local.', invalid_response: 'Resposta de IA rejeitada. Resumo local.', incomplete_response: 'Resposta de IA incompleta. Resumo local.', invalid_model: 'Modelo não configurado corretamente. Resumo local.', input_limit: 'Limite de entrada da IA. Resumo local.'};

function metric(label, value, caption) {
  const box = node('div', 'metric');
  box.append(node('div', 'metric-label', label), node('div', 'metric-value', value), node('small', '', caption));
  return box;
}
function renderIndicator(data) {
  const box = node('article', 'indicator');
  const heading = node('div', 'indicator-head');
  heading.append(node('h3', '', data.title), node('span', 'badge ' + (data.category === 'coverage' ? 'badge-coverage' : data.status === 'triggered' ? 'badge-triggered' : ''), statusNames[data.status] || data.status));
  box.append(heading, node('p', '', data.description));
  const details = node('details'); details.append(node('summary', '', 'Método, métricas e limitações'));
  details.append(node('p', '', data.method));
  const list = node('ul');
  const metricLabels = {max_in_60s:'Maior grupo em 60 s',timestamped_signatures:'Assinaturas com data',fraction:'Fração no maior grupo',recognized_transfer_transactions:'Transações com saídas reconhecidas',repeated_groups:'Grupos repetidos',largest_group:'Maior grupo',signatures_observed:'Assinaturas observadas',span_seconds:'Intervalo em segundos',unavailable_details:'Detalhes indisponíveis',dropped_records:'Registros descartados'};
  Object.entries(data.metrics).forEach(([key,value]) => list.append(node('li', '', `${metricLabels[key] || key}: ${value ?? 'desconhecido'}`)));
  data.limitations.forEach(text => list.append(node('li', '', text)));
  details.append(list); box.append(details);
  if (data.evidence.length) {
    box.append(node('p', '', `Evidências verificáveis · severidade ${data.severity === 'medium' ? 'moderada' : data.severity}`));
    const links = node('div', 'evidence-links');
    data.evidence.forEach(item => {
      const a = link('tx', item.signature, short(item.signature) + ' ↗');
      a.title = item.lamports ? `Valor exato: ${item.lamports} lamports. Destino: ${item.destination}` : date(item.observed_at);
      links.append(a);
    }); box.append(links);
  }
  return box;
}

function renderReport(report) {
  const root = $('#report'); root.replaceChildren();
  const top = node('div','report-top'), title = node('div');
  const h = node('h2','','Relatório da amostra'); h.id = 'report-heading';
  title.append(h, node('p','wallet-address',report.wallet), link('address',report.wallet,'Ver endereço no Explorer ↗'));
  const download = node('button','secondary-button','Exportar JSON ↓'); download.type='button';
  download.addEventListener('click',()=>{
    const blob = new Blob([JSON.stringify(report,null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob), a=document.createElement('a');
    a.href=url;a.download=`scamshield_${report.wallet.slice(0,8)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }); top.append(title,download);root.append(top);
  root.append(node('p','status-line',`${report.network} · ${report.status === 'partial' ? 'Coleta parcial' : 'Coleta concluída'} · ${date(report.analyzed_at)}`));
  if (report.status === 'partial') root.append(node('p','warning-note','Parte dos dados não pôde ser obtida. Os indicadores usam somente as evidências disponíveis.'));
  const score=report.experimental_alert_index;
  const metrics=node('div','metrics');
  metrics.append(metric('Assinaturas observadas',report.signatures_observed,`Limite solicitado: ${report.sample_limit}`),
    metric('Detalhes examinados',report.transactions_analyzed,`${report.transactions_unavailable} indisponíveis`),
    metric('Alertas comportamentais',report.alerts.length,'Cobertura não conta como alerta'),
    metric('Índice Experimental de Alertas',score.value === null ? '—' : `${score.value}/100`,score.value === null ? 'Dados insuficientes' : 'Não é probabilidade de golpe'));
  root.append(metrics,node('p','index-note',`Activity Burst: 50 pontos; Repetitive Transfers: 50; cobertura: 0. Pontos observados: ${score.observed_points}. O índice completo exige ambas as regras calculáveis.`));
  const columns=node('div','report-columns'), left=node('div'), right=node('div');
  report.indicators.forEach(ind=>left.append(renderIndicator(ind)));
  const exp=node('section','explanation');exp.append(node('p','eyebrow','EM LINGUAGEM SIMPLES'),node('h3','',report.explanation.source === 'local' ? 'Explicação local' : 'Explicação por IA · não verificada'));
  exp.append(node('p','explanation-text',report.explanation.text),node('p','',report.explanation.source === 'local' ? fallbackNames[report.explanation.fallback_reason] || 'Resumo local.' : 'Texto gerado por IA. Confira os fatos nas evidências; a IA não altera o índice.'));
  right.append(exp);
  const limits=node('section','limitations-box');limits.append(node('h3','','Limitações da análise'));const ul=node('ul');report.limitations.forEach(text=>ul.append(node('li','',text)));limits.append(ul);right.append(limits);
  right.append(node('p','provenance',`Período observado: ${date(report.observed_period.start)} até ${date(report.observed_period.end)}. Datas exibidas no fuso do navegador.`),
    node('p','provenance',`Origem: Solana JSON-RPC · finalized. Respostas de cache: ${report.provenance.cache_hits}. Coletas entre ${date(report.provenance.oldest_fetch_at)} e ${date(report.provenance.newest_fetch_at)}.`));
  columns.append(left,right);root.append(columns);
  const txBox=node('section','transaction-section');txBox.append(node('h3','','Transações na amostra'));
  if (!report.transactions.length) txBox.append(node('p','muted','Nenhuma assinatura foi retornada nesta consulta. Isso não comprova ausência de histórico.'));
  report.transactions.forEach(tx=>{
    const row=node('article','transaction'), info=node('div'), meta=node('div','transaction-meta');
    info.append(link('tx',tx.signature,short(tx.signature)+' ↗'),node('p','',date(tx.observed_at)));
    const execution={success:'Execução bem-sucedida',failed:'Falhou on-chain',unknown:'Execução não verificada'};
    meta.append(node('div','',execution[tx.execution_status]),node('div','',tx.detail_status === 'available' ? `${tx.outgoing_sol_transfers.length} saída(s) de SOL reconhecida(s)` : 'Detalhes indisponíveis'));
    row.append(info,meta);txBox.append(row);
  });root.append(txBox,node('p','provenance',`Request ID: ${report.request_id} · Regras v${report.report_version}`));
  $('#empty-state').hidden=true;root.hidden=false;root.focus({preventScroll:true});root.scrollIntoView({behavior:'smooth',block:'start'});
}

fetch('/api/health').then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{
  $('#backend-status').textContent='Backend disponível';
  if ($('#ai-note') && !data.ai_configured) $('#ai-note').textContent='IA não configurada neste servidor: o resumo será local. Com o Ollama habilitado no backend, a opção envia apenas métricas estruturadas ao Ollama configurado pelo operador, sem endereço ou assinatura.';
}).catch(()=>{$('#backend-status').textContent='Backend indisponível';});

if ($('#analyze-form')) {
  $('#example-button').addEventListener('click',()=>{$('#wallet').value='vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg';$('#wallet').focus();});
  $('#analyze-form').addEventListener('submit',async(event)=>{
    event.preventDefault();const error=$('#error'), loading=$('#loading'), button=$('#analyze-button');
    error.hidden=true;$('#report').hidden=true;loading.hidden=false;button.disabled=true;
    $('#analyze-form').setAttribute('aria-busy','true');
    const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),100000);
    try {
      const response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},signal:controller.signal,
        body:JSON.stringify({wallet:$('#wallet').value.trim(),limit:Number($('#limit').value),language:$('#language').value,use_ai:$('#use-ai').checked})});
      const data=await response.json();
      if(!response.ok)throw new Error((data.error?.message || 'Falha ao consultar.')+(data.error?.retry_after_seconds ? ` Aguarde ${data.error.retry_after_seconds} segundos.` : ''));
      renderReport(data);
    } catch(e) {
      error.textContent=e.name === 'AbortError' ? 'A consulta demorou demais. Tente novamente com uma amostra menor.' : e.message || 'Falha de conexão com o servidor.';
      error.hidden=false;error.focus();
    } finally {clearTimeout(timeout);loading.hidden=true;button.disabled=false;$('#analyze-form').removeAttribute('aria-busy');}
  });
}
