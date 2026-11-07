# Verificação da entrega — ScamShield v1.0

Executada em 7 de novembro de 2026 em Linux, com Python 3.12.14. Este registro distingue execução real, mocks e verificações não concluídas.

| Verificação | Resultado observado |
| --- | --- |
| `python -m pytest -q` | **77 testes aprovados**, execução final após adaptação para Ollama; 0 falhas |
| Inicialização `python app.py` | Flask iniciou com debug desligado, anunciado em 127.0.0.1:5000 |
| Inicialização com Waitress | Processo iniciado; `/api/health` respondeu HTTP 200 em requisição HTTP local |
| Templates Flask | `/`, `/about` e `/how-it-works` retornaram HTTP 200 e HTML renderizado |
| Consulta real pelo script | Mainnet confirmada; 5 assinaturas e 5 detalhes de transação obtidos e analisados |
| Fluxo completo da rota `/api/analyze` | Flask test client, sem mock de RPC: HTTP 200, 5 detalhes examinados e explicação local |
| Sintaxe JavaScript | `node --check static/js/app.js` terminou com código 0 |
| Lógica do frontend em DOM | jsdom 26: formulário, exemplo, loading, relatório, indicadores, transações, texto seguro, exportação JSON, links, erro e recuperação passaram |
| LLM opcional | Respostas, falhas e limites do adaptador Ollama testados com mocks; **não houve inferência real de modelo** |
| Navegador real / responsividade visual | **Não concluído neste ambiente**: Chromium bloqueado por `socket() Operation not permitted`; precisa de conferência no PC de apresentação |
| Instalação no Windows 11 | Comandos PowerShell fornecidos, mas não executados em Windows nesta entrega |
| Documento técnico | DOCX renderizado e 17 páginas conferidas visualmente |

## Evidências de rede

Comando executado na pasta do projeto:

```text
python scripts/live_smoke.py --limit 5 --output docs/live_capture.json
```

Resultado: código de saída 0. Captura em `2026-11-07T06:11:30.388398Z`, contendo atividade observada de `2026-03-31T06:44:28Z` a `2026-05-31T09:20:05Z`. O endpoint foi o RPC público Mainnet da Solana. Não foi necessária chave paga.

Uma segunda verificação percorreu a rota Flask, coleta real, motor, explicação e histórico, em `2026-11-07T06:18:40.659525Z`. O relatório correspondente está em `api_live_capture.json`. Ambas as capturas são **históricas**, não são carregadas automaticamente pelo dashboard e não representam garantia de disponibilidade futura.

Na amostra: Activity Burst não acionado; Repetitive Transfers com dados insuficientes; Limited Observed History acionado como cobertura. Nenhum alerta comportamental foi produzido; o índice completo permaneceu `null`. Não significa carteira segura.

## O que os testes isolados verificam

- Base58 válida e inválida; tamanho de 32 bytes; endereço de programa aceito como endereço.
- Corpo ausente, JSON inválido, campos extras, booleano como limite, limites de tamanho e origem.
- Carteira sem assinaturas, detalhes indisponíveis, respostas incompletas e rede incorreta.
- HTTP 429, Retry-After, falhas de conexão, timeout, erros RPC e cache.
- Bursts, datas desconhecidas, saídas repetidas em assinaturas distintas e transferências legítimas.
- Exclusão de falhas on-chain, entradas, autoenvios, tokens e tipos de instrução não suportados.
- Relatórios parciais, evidências, índice incompleto e limitações de cobertura.
- Banco, quotas, fallback determinístico e adaptador LLM com mocks.

Os testes verificam implementação, não acurácia antifraude. Não existe dataset rotulado, avaliação de recall ou calibração probabilística nesta entrega.

## Correção encontrada pela consulta real

A primeira tentativa usava uma referência truncada de rede para comparação. O RPC retorna o genesis hash Base58 completo. O código foi corrigido para `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d`, um teste de regressão foi acrescentado e a consulta real foi repetida com sucesso. Isso mostra por que mocks e verificação ao vivo cumprem papéis diferentes.

## Conferência final no computador de apresentação

1. Seguir o README e abrir as três páginas no navegador.
2. Consultar o endereço de exemplo com limite 5; verificar período e links.
3. Exportar o JSON e conferir os campos.
4. Testar em janela estreita e navegar pelos controles com Tab.
5. Se usar IA na apresentação, aquecer Ollama e verificar `explanation.source = llm_unverified`; conferir o texto com as evidências.
6. Gravar somente capacidades efetivamente demonstradas.
