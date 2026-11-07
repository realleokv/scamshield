# ScamShield — apresentação e submissão

Versão 1.0 · Solana Hackathon 2026 · 7/11/2026

## Pitch em inglês — aproximadamente 50 a 60 segundos

Hi, I'm Leo, and this is ScamShield for the Solana Hackathon.

Public blockchain data is transparent, but understanding it can be difficult. A list of transactions does not explain what a beginner should pay attention to.

ScamShield turns a small sample of Solana activity into readable, verifiable observations. It checks activity bursts and repeated native SOL transfers, links to the supporting transactions, and clearly shows missing data.

We built it with Python, Flask, SQLite and plain JavaScript. An optional local language model can explain structured findings without changing the underlying evidence. The core works without an AI service.

An unusual pattern is not proof of fraud. Our experimental alert index is not a scam probability.

Our goal is to help people understand the evidence before they decide whom to trust.

**Nota de uso:** o texto descreve capacidade opcional, não inferência LLM já demonstrada. Se não testar Ollama antes da apresentação, diga que a demo usa explicação determinística. Ensaie e cronometre: velocidade de fala varia.

## Demonstração de até dois minutos

Prepare o servidor local e verifique a internet antes de começar. Mantenha o Explorer aberto em outra aba. Não precisa conectar carteira. O vídeo deve mostrar o aplicativo, não apenas slides.

| Tempo | Na tela | Fala sugerida em inglês |
| --- | --- | --- |
| 0–15 s | Dashboard inicial | “Hi, I'm Leo. This is our demo for the Solana Hackathon. ScamShield makes public wallet activity easier to understand.” |
| 15–35 s | Insira o endereço público do exemplo; selecione 5 e analise | “We only need a public address. The backend checks the network and reads a bounded sample through Solana JSON-RPC.” |
| 35–60 s | Métricas e período | “These are the signatures observed and the transaction details retrieved. They are not the wallet's total history.” |
| 60–85 s | Indicadores e uma assinatura no Explorer | “Each rule explains its threshold. Missing data stays unknown. This link lets anyone verify the transaction independently.” |
| 85–105 s | Explicação | “The default summary is deterministic. The optional local language model receives structured metrics, and cannot change the score or evidence.” |
| 105–120 s | Limitações e exportação | “Unusual activity can be legitimate. We do not claim fraud detection accuracy. Next, we want to add tested token parsing and evaluate false positives.” |

Se a chamada demorar, explique o escopo enquanto aguarda. Para manter até dois minutos, a gravação pode mostrar uma análise recém-concluída; informe que é uma captura real e mantenha o horário visível. Não finja que houve consulta instantânea.

### Endereço e resultado verificado

Endereço público de demonstração:

```text
vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg
```

Fonte do endereço: [exemplo oficial de getAccountInfo](https://solana.com/docs/rpc/http/getaccountinfo). Não atribuímos proprietário ou reputação.

Na captura real incluída em `docs/live_capture.json`, realizada em **7/11/2026 às 03:11:30 de São Paulo** (06:11:30 UTC), foram observadas 5 assinaturas e examinados 5 detalhes. Activity Burst não foi acionado; Repetitive Transfers ficou com dados insuficientes, pois não havia saídas reconhecidas pelo parser; cobertura limitada foi informada. O índice ficou indisponível. Isso **não prova segurança**. A captura registra atividade observada entre 31/03 e 31/05/2026, e não entre início e fim da vida da carteira.

Para nova consulta, não espere a mesma contagem ou alertas. Links exatos das transações estão no JSON. Para demonstrar regras acionadas de forma controlada, rode os testes sintéticos e identifique-os explicitamente como testes; não os coloque no painel como se fossem atividade real desse endereço.

### AI Track

O evento busca IA e Solana desempenhando funções reais. Para apresentar o módulo generativo, instale Ollama, baixe o modelo, aqueça-o e confira se `explanation.source` é `llm_unverified`. Compare o texto com os indicadores. Mostre que o modelo não altera evidências. O adaptador foi validado com mocks nesta entrega; inferência real deve ser demonstrada pela equipe antes de alegar esse resultado. Assistência de ChatGPT para programar, por si só, não comprova atendimento à trilha.

## Texto de submissão em inglês

Conteúdo preparado para campos no estilo Devpost. A agenda oficial aponta **MLH Challenges** como destino; siga o formulário vigente. Substitua somente o que a equipe efetivamente mudou ou testou. Não há envio automático.

### Project name

ScamShield

### Tagline

Know the risk before you trust.

### Inspiration

Blockchain transparency is useful only when people can understand what they are looking at. We wanted to build a small tool that helps beginners inspect public Solana activity while clearly separating observations from speculation.

### What it does

ScamShield retrieves a bounded sample of public Solana transactions and reports activity bursts, repeated explicit native SOL transfers, and coverage limitations. Each indicator has a documented method and links to relevant transactions. It does not connect a wallet, request private keys, sign transactions, or label an address as criminal. The experimental alert index is not a probability of fraud.

### How we built it

The backend uses Python, Flask, Requests and SQLite. The frontend uses plain HTML, CSS and JavaScript. We query Solana JSON-RPC using finalized commitment, inspect parsed instructions, cache responses, and preserve missing-data states. An optional Ollama chat adapter explains selected structured metrics; a deterministic explanation keeps the core functional when a model is unavailable.

ChatGPT substantially assisted with research, architecture, documentation, code generation, interface implementation and tests. Human review and any subsequent team changes must be recorded in the repository. The optional local model is separate from the AI assistance used to build the project.

### Challenges we ran into

The main challenge was avoiding misleading conclusions from incomplete blockchain data. A transaction can reference an address without being initiated by it, a short sample does not establish wallet age, and balance changes are not enough to infer transfers. We also corrected a network-verification issue found by a real RPC test: the full genesis hash must be compared, not a truncated network reference.

### Accomplishments that we're proud of

The prototype includes a working read-only RPC pipeline, explicit coverage reporting, traceable indicators, a deterministic fallback, structured errors, request limits and an offline automated test suite. A real Mainnet sample with five transaction details was successfully analyzed. The project stays within a beginner-friendly Python and plain-JavaScript stack.

### What we learned

Parsed instructions and transaction metadata need careful validation. Missing information should remain unknown instead of being treated as a safe result. Testing transport failures and legitimate repetitive behavior is as important as triggering an alert. We also learned to separate model-generated explanations from independently inspectable evidence.

### What's next

Add tested SPL token parsing, bounded pagination, and evaluation on appropriately labelled cases. Measure false positives before making accuracy claims. A future pre-signing simulator would be a separate feature with its own threat model and validation.

## Checklist antes de enviar

- Confirmar inscrição de todos e autorização parental aplicável.
- Confirmar composição da equipe para Beginner; não presumir elegibilidade pelo título “estudante”.
- Revisar o código assistido por IA e registrar alterações humanas realmente feitas.
- Executar os testes e conferir o relatório de consulta real.
- Demonstrar LLM real caso a candidatura dependa de AI Track.
- Gravar vídeo de até dois minutos, começando pelo nome do evento.
- Publicar código e vídeo conforme as regras, sem `.env`, banco, chaves ou dados privados.
- Preencher o portal correto e verificar os termos de premiação vigentes.

Fonte da agenda e trilhas: [página oficial](https://events.mlh.com/events/15200-solana-hackathon). Regras gerais de autoria e vídeo: [MLH Standard Hackathon Rules](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md). Consulta em 7/11/2026; regras específicas atualizadas prevalecem.
