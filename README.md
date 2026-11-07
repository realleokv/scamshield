# ScamShield v1.0

**Know the risk before you trust.**

Ferramenta educacional para inspecionar indicadores em uma amostra pública de um endereço Solana. A aplicação consulta a Mainnet de verdade e mostra evidências verificáveis. Não conecta carteiras, não solicita seed phrase, não assina e não movimenta dinheiro.

## Comece aqui

O ZIP contém a pasta `scamshield`. Extraia o ZIP inteiro e abra essa pasta no VS Code ou no Explorador. Os comandos abaixo devem ser executados no **PowerShell**, na pasta que contém `app.py`. Não abra `index.html` diretamente: o Flask precisa estar rodando.

### 1. Python no Windows 11

Instale Python pelo [site oficial para Windows](https://www.python.org/downloads/windows/), escolhendo uma versão estável compatível. O projeto foi testado com Python 3.12. Use uma versão atualizada da série que escolher; não precisa instalar Rust, Node.js, React ou TypeScript.

No instalador clássico, habilite o launcher e a opção de adicionar Python ao PATH, quando disponíveis. Se o PC tiver políticas da escola, utilize a instalação autorizada. Feche e reabra o PowerShell depois de instalar.

```powershell
py -3.12 --version
```

Esse comando verifica se o Python 3.12 está instalado. Se você tiver outra versão compatível, use `py -3 --version` e troque apenas o comando de criação do ambiente por `py -3 -m venv .venv`. Versões diferentes da 3.12 não foram verificadas nesta entrega.

### 2. Entre na pasta

```powershell
cd "C:\caminho\onde\voce\extraiu\scamshield"
```

Substitua o caminho pelo local real. Dica: abra a pasta no Explorador, clique na barra de endereço, escreva `powershell` e pressione Enter.

### 3. Crie um ambiente virtual

```powershell
py -3.12 -m venv .venv
```

Isso cria uma pasta `.venv` com um Python isolado para o projeto. As dependências não precisam ser instaladas no Python global.

Os próximos comandos chamam diretamente esse Python. **Não é necessário ativar scripts nem alterar a política de execução do PowerShell.**

### 4. Instale as dependências

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

O `pip` baixa Flask, Requests, python-dotenv e Waitress. SQLite já acompanha Python. A instalação das dependências precisa de internet.

### 5. Configure o ambiente

```powershell
Copy-Item .env.example .env
notepad .env
```

Execute `Copy-Item` apenas na primeira configuração; não substitua um `.env` já configurado. O Bloco de Notas permite ajustar as opções. Para começar, mantenha:

```dotenv
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
RPC_TIMEOUT=8
TRUSTED_HOSTS=localhost,127.0.0.1,[::1]
LLM_ENABLED=false
LLM_URL=http://127.0.0.1:11434/api/chat
LLM_MODEL=qwen2.5:1.5b
LLM_API_KEY=
AI_DAILY_LIMIT=20
```

O RPC público funciona sem chave, mas pode impor limites. Se usar outro provedor, configure **um endpoint Solana Mainnet HTTPS**. O código confirma a rede por `getGenesisHash`. A URL nunca é enviada ao navegador. Não publique `.env` se ele contiver chaves.

### 6. Inicie o Flask

```powershell
.\.venv\Scripts\python.exe app.py
```

Mantenha esse terminal aberto. O servidor de desenvolvimento deve anunciar `http://127.0.0.1:5000`. Para encerrar, use Ctrl+C. Debug está desligado.

### 7. Abra no navegador

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000). Cole o endereço público, selecione 5 transações para começar e clique em **Analyze Wallet**. O indicador superior confirma apenas o backend; a conexão com a blockchain é conferida durante a análise.

Use o botão de exemplo ou cole:

```text
vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg
```

Esse endereço aparece na [documentação oficial de getAccountInfo](https://solana.com/docs/rpc/http/getaccountinfo). Seu uso aqui não indica propriedade, suspeita nem reputação. A atividade pode mudar. A consulta é exclusivamente de leitura.

## O que o sistema faz

1. Valida os caracteres Base58 e o tamanho decodificado de 32 bytes.
2. Confirma Mainnet, lê metadados e até 25 assinaturas recentes.
3. Obtém detalhes das transações com `getTransaction`, `jsonParsed`, `finalized` e suporte a legacy/v0.
4. Aplica regras determinísticas e informa dados ausentes.
5. Mostra evidências, período, explicação local ou IA opcional e exportação JSON.

### Entenda os três indicadores

| Indicador | Critério | Interpretação |
| --- | --- | --- |
| Activity Burst | Pelo menos 5 assinaturas em 60 segundos e 50% da amostra datada; nenhuma data ausente | Concentração observada, não autoria ou fraude |
| Repetitive Transfers | Mesmo destino e valor exato em 3 transações distintas com saídas explícitas de SOL bem-sucedidas | Repetição pode ser pagamento legítimo |
| Limited Observed History | Menos de 10 assinaturas, menos de 24 horas ou lacunas de dados | Limitação de cobertura, sem pontos |

São reconhecidas instruções externas e internas do **System Program**, tipo `transfer`, com quantia inteira positiva, origem igual ao endereço e destino diferente. Não inferimos transferências a partir de saldo líquido. Tokens SPL, swaps, `transferWithSeed`, NFTs e programas arbitrários não são interpretados.

`insufficient_data` significa que a regra não pôde ser calculada com segurança. `not_triggered` significa que o critério não apareceu no subconjunto analisável. **Nenhum dos dois significa “carteira segura”.**

### Índice Experimental de Alertas

Cada regra comportamental acionada soma 50 pontos. Cobertura soma zero. Só publicamos o índice de 0 a 100 quando as duas regras comportamentais são calculáveis. Caso contrário, o valor é `null` e mostramos apenas pontos observados, explicitamente parciais. Não é probabilidade de golpe; não existe precisão de classificação validada.

## IA opcional com Ollama

Sem Ollama, tudo funciona com **explicação local por regras**, identificada como tal. Isso não é IA generativa.

O adaptador opcional usa a [API local do Ollama](https://docs.ollama.com/api/chat). O modelo roda no PC, consumindo memória, processamento e energia, sem cobrança por token. O modelo não acompanha o ZIP.

1. Instale Ollama pelo [site e instruções oficiais](https://docs.ollama.com/windows).
2. Com Ollama em execução, baixe o modelo no PowerShell:

```powershell
ollama pull qwen2.5:1.5b
```

O primeiro download pode demorar. Espaço livre e desempenho dependem do computador. O modelo é uma sugestão pequena; a qualidade precisa de avaliação humana. Consulte sua licença na página do modelo antes de redistribuí-lo.

3. Faça um teste local e carregue o modelo antes da demonstração:

```powershell
ollama run qwen2.5:1.5b "Explique em uma frase por que atividade incomum não comprova fraude."
```

4. No `.env`, mude `LLM_ENABLED=false` para `LLM_ENABLED=true`. Reinicie Flask e marque “Usar IA opcional para explicar”.

O adaptador envia somente métricas e estados de regras. Endereços, assinaturas, memos e logs não entram no prompt. A resposta vem rotulada `llm_unverified`, não altera o índice e nunca é executada. O timeout da IA é de 20 segundos; modelo frio ou CPU lenta podem resultar em fallback. `num_predict=512`, contexto de 4.096 tokens, input de até 8.000 caracteres e 20 tentativas por dia limitam consumo. Respostas truncadas são descartadas. Pode haver cache de explicação por uma hora.

Uma instância remota compatível pode usar `LLM_URL` HTTPS e `LLM_API_KEY` no backend. Essa opção é para operador autorizado, com análise dos termos e custos do serviço. A URL é fixa na configuração; o formulário não aceita URLs.

**Validação desta entrega:** integração LLM testada com mocks; inferência de um modelo Ollama real não foi executada neste ambiente. A análise real e o resumo determinístico foram executados. Não anuncie a demo como IA generativa enquanto `source` for `local`.

## Testes

Instale dependências de testes:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

A suíte usa mocks e dados sintéticos, sem consultas de rede. Cobre validação, entradas inválidas, RPC incompleto, timeout, 429, cache, repetição, rajadas, cobertura, relatórios, quotas e IA. Resultados efetivamente executados constam em `docs/VALIDATION.md`.

Consulta real separada, com a aplicação instalada:

```powershell
.\.venv\Scripts\python.exe scripts\live_smoke.py --limit 5 --output live_report.json
```

O script consulta a Mainnet e salva o relatório no arquivo informado. Retorna código 1 se o RPC falhar e 2 se nenhum detalhe for obtido. Não participa automaticamente do pytest. O arquivo `docs/live_capture.json` é uma **captura real histórica de 7/11/2026**, não dados ao vivo; o dashboard padrão nunca o carrega.

### Exemplo da API pelo PowerShell

Com o servidor aberto, use outro PowerShell:

```powershell
$scamshieldBody = @{
    wallet = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"
    limit = 5
    language = "pt"
    use_ai = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/analyze" -Method Post -ContentType "application/json" -Body $scamshieldBody
```

`ConvertTo-Json` transforma os campos em JSON; `Invoke-RestMethod` envia a requisição. O contrato completo está em `docs/technical.md`, seções 25 e 26, e no documento Word.

## Cache, histórico e privacidade

O banco `instance/scamshield.sqlite3` é criado automaticamente. Não instale MySQL nem execute migrações manualmente. Cache de assinaturas/metadados: 60 s. Cache de transações/genesis hash: uma hora. Máximo de 2.000 entradas. Histórico: até sete dias e 500 relatórios; limpeza durante novas análises. Dados podem permanecer em disco se o aplicativo não for novamente executado. Não existe página pública de histórico.

O operador RPC recebe o endereço; o banco guarda a associação entre consultas e endereços públicos. Proteja o arquivo. Para apagá-lo, encerre o servidor e remova `instance/scamshield.sqlite3` e seus arquivos `-wal`/`-shm`, se existirem. Isso remove cache, histórico e contadores; não altera a blockchain.

## Segurança implementada

- Validação de Base58, tipos e campos; JSON de até 4 KiB.
- Até 25 detalhes por consulta e prazo de coleta de 45 s verificado entre chamadas.
- Timeouts de conexão/leitura, até um retry de RPC; nenhum retry automático de IA.
- Rate limit: 6 análises/IP/minuto, 30 globais/minuto e 2 análises simultâneas por processo.
- SQLite parametrizado; segredos somente no ambiente; mensagens de erro sem dados de provedor.
- Escape de templates, `textContent`, links Explorer construídos a partir de Base58, CSP e headers de proteção.
- URLs do cliente rejeitadas; redirects HTTP desabilitados; somente métodos RPC de leitura.

O backend não confia em `X-Forwarded-For`. Um proxy fará usuários compartilharem o mesmo limite por IP, a menos que seja configurado corretamente por quem opera. O MVP não é um serviço público endurecido contra ataques distribuídos.

## Servir com Waitress

Para uma execução WSGI local, encerre Flask e rode:

```powershell
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:5000 app:app
```

Hospedagem pública requer HTTPS, domínio em `TRUSTED_HOSTS`, proxy com limites e armazenamento persistente. Use uma instância no MVP; o semáforo não coordena processos diferentes. Não publique o servidor de desenvolvimento. Não há necessidade de comprar hospedagem para apresentar uma gravação local.

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| `py` não encontrado | Reabra o terminal após instalar; confira o launcher e PATH |
| `ModuleNotFoundError` | Instale requirements usando exatamente `.venv\Scripts\python.exe` |
| Porta 5000 ocupada | Feche a execução anterior ou use Waitress com porta 5001 |
| HTTP 429 | Aguarde Retry-After; não clique repetidamente; use limite 5 |
| RPC indisponível/403 | Confira internet e `.env`; o endpoint público pode bloquear IPs |
| `wrong_network` | Configure Mainnet, não Devnet; o app não muda a rede automaticamente |
| Dados insuficientes | É um resultado válido; não force um índice nem invente atividade |
| IA continua local | Confira LLM_ENABLED, serviço Ollama, modelo baixado, timeout e fallback_reason |
| Banco bloqueado | Evite vários processos; encerre execuções duplicadas |
| Host não permitido | Abra localhost/127.0.0.1; configure TRUSTED_HOSTS para deploy autorizado |

## Limitações e roadmap

Não há verificação de identidade, análise de todos os tokens, reputação externa, simulação pré-assinatura, histórico completo ou precisão antifraude demonstrada. O sistema confia no provedor RPC; não valida o consenso por conta própria. Alertas são observações, não acusações.

Próximos passos: parsing SPL com testes, paginação controlada, coleta rotulada, avaliação de falsos positivos e simulação pré-assinatura como módulo separado. Login, token próprio, NFTs e pagamentos não pertencem ao MVP.

## Hackathon e autoria

Leia `docs/PITCH.md` e `docs/DEVELOPMENT_PLAN.md`. Registre a equipe, obtenha autorização parental quando aplicável, mantenha o desenvolvimento dentro da janela oficial e siga o portal de submissão apontado pelo evento. Elegibilidade para Beginner depende da equipe, não apenas de experiência limitada em Solana. A documentação diferencia regras gerais e informações confirmadas do evento.

**Assistência de IA:** ChatGPT auxiliou substancialmente a pesquisa, arquitetura, documentação, geração de código, UI e testes desta versão em 7/11/2026. O desenvolvedor deve revisar o código, registrar suas alterações e declarar essa assistência na submissão. Não declarar que todo o código foi escrito manualmente. Ollama é uma integração opcional de execução, separada da IA usada para desenvolver.

Bibliotecas: Flask/Jinja/Werkzeug, Requests, python-dotenv, Waitress e pytest. SQLite é da biblioteca padrão. Nenhum código de projeto pessoal anterior foi importado nesta entrega. As licenças das dependências e de qualquer modelo devem ser preservadas conforme aplicável. Este README não atribui uma licença de publicação ao usuário; a equipe decide a licença do repositório antes de publicar.

Fontes oficiais: [evento MLH](https://events.mlh.com/events/15200-solana-hackathon), [regras gerais](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md), [Solana RPC](https://solana.com/docs/rpc), [Ollama](https://docs.ollama.com/api/chat), [Flask deploy](https://flask.palletsprojects.com/en/stable/deploying/). Catálogo completo em `docs/technical.md`.
