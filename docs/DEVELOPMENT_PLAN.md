# ScamShield — plano de desenvolvimento

Versão 1.0 · Plano de até 48 horas · Solana Hackathon 2026

## Escopo e decisão técnica

Entregar um fluxo completo: endereço público → RPC Mainnet → amostra → indicadores → evidências → explicação. Python/Flask no backend; HTML/CSS/JavaScript puro no frontend; SQLite local. Não adicionar login, contratos, token próprio, NFT, pagamentos, React ou Rust.

As regras são determinísticas. A IA apenas explica métricas já calculadas. Históricos pequenos não geram pontos de risco. Nenhuma pontuação é probabilidade de fraude.

## Prioridades e dependências

| Prioridade | Trabalho | Depende de | Critério de aceitação |
| --- | --- | --- | --- |
| P0 | Validação e configuração | Contrato de entrada | Base58 de 32 bytes aceita; entradas inválidas retornam 400 |
| P0 | Cliente RPC e cache | Validação | Leitura real Mainnet; timeout e 429 tratados |
| P0 | Coleta e normalização | RPC | Contar assinaturas, detalhes e lacunas separadamente |
| P0 | Indicadores | Dados normalizados | Evidências por assinatura; falsos positivos documentados |
| P0 | Relatório REST | Indicadores | Índice null quando incompleto; UTC e rede explícitos |
| P0 | Interface funcional | API | Formulário, loading, erros, indicadores e links |
| P0 | Testes e README | Cada módulo | Suíte sem rede; instalação reproduzível |
| P1 | IA local opcional | Evidências estáveis | API Ollama real na demo ou fallback rotulado |
| P1 | Exportação e páginas de ajuda | Relatório | JSON válido e explicações claras |
| P1 | Vídeo e submissão | MVP estável | Vídeo dentro do limite e materiais com créditos |
| P2 | SPL, grafos, simulação | Fora da v1 | Não iniciar antes da entrega P0 |

## Cronograma

| Tempo desde abertura | Foco | Saída concreta |
| --- | --- | --- |
| H0–H2 | Regras e recorte | Fontes, limites e trilhas escolhidas |
| H2–H4 | Arquitetura e documento | Contratos, regras, esquema SQLite |
| H4–H10 | Backend básico | Validação, RPC real, cache e erros |
| H10–H18 | Motor e testes | Burst, repetição, cobertura e casos negativos |
| H18–H28 | Frontend | Dashboard móvel, relatório e tratamento de falhas |
| H28–H34 | Integração e proteção | Limites, timeouts, headers, logs seguros |
| H34–H38 | IA opcional | Ollama configurável, quotas e fallback |
| H38–H42 | Verificação real e revisão | Relatório real, correções, documentos consistentes |
| H42–H44 | Demonstração | Vídeo de até dois minutos e texto revisado |
| H44–H47h45 | Submissão e margem | Materiais enviados e acesso público conferido |

O plano distribui atividades, não exige 48 horas acordado. Divida tarefas entre integrantes ou reduza escopo, mantendo descanso. Esta tabela não é um apontamento de horas efetivamente trabalhadas. A versão entregue já cobre as etapas de implementação e testes registradas em `VALIDATION.md`.

## Agenda do evento em São Paulo

A [agenda oficial](https://events.mlh.com/events/15200-solana-hackathon), consultada em 7/11/2026, informa:

- Início: **6/11/2026 às 14h**.
- Submissão inicial: **8/11/2026 às 12h**.
- Encerramento do desenvolvimento e submissão final: **8/11/2026 às 13h45**.
- Cerimônia de encerramento: **8/11/2026 às 14h**.

Conversão de EST para America/Sao_Paulo. A janela divulgada de código é de 47h45, não 48 horas exatas. O cabeçalho geral do evento não substitui o deadline específico de submissão. Confirme eventuais mudanças no portal.

Como o evento já está em andamento, não reinicie a contagem por este plano. A partir do recebimento: instale e valide P0, revise as regras, faça uma consulta real, só então tente o modelo local. Reserve tempo para vídeo e envio antes de pensar em novas features.

## Critérios de conclusão e verificação

1. Flask inicia sem debug e entrega as três páginas.
2. Requisição válida consulta a Mainnet, confirmada pelo genesis hash completo.
3. Ao menos uma amostra real retorna detalhes analisados.
4. Relatório distingue referência ao endereço, execução e saída reconhecida.
5. Cada alerta comportamental tem assinaturas verificáveis.
6. Dados insuficientes não são convertidos em zero ou segurança.
7. Falha de RPC apresenta erro ou relatório parcial visível.
8. Sem IA, o fluxo básico permanece operacional.
9. Testes automatizados essenciais são executados e registrados.
10. Revisão visual e navegação em um navegador real são feitas no PC de apresentação.

O resultado de cada verificação efetivamente feita acompanha `VALIDATION.md`. Integração LLM com mocks não equivale a inferência generativa real. Conclusão técnica não equivale a elegibilidade ou vitória na competição.

## Contingência

| Falha | Ação imediata | O que dizer na apresentação |
| --- | --- | --- |
| RPC 429 | Respeitar Retry-After, reduzir limite e aguardar | “O provedor limitou a consulta; o sistema trata essa falha.” |
| RPC inacessível | Configurar outro endpoint Mainnet confiável no .env | “Usamos um provedor de leitura; a disponibilidade pode variar.” |
| Internet cai | Mostrar captura real com data e origem | “Este é um relatório real capturado anteriormente.” |
| Modelo não carrega | Deixar IA desligada e usar resumo local | “Esta execução usa explicação determinística.” |
| IA inventa conteúdo | Descartar a explicação da demo; conferir evidências | “O texto de IA não é evidência e não altera regras.” |
| Falta de tempo | Congelar extras, revisar P0, gravar e enviar | Demonstrar somente o que funciona |
| UI com defeito local | Corrigir o problema mínimo e repetir fluxo | Não esconder a limitação em slides |

## Elegibilidade e atribuição

As regras gerais MLH permitem assistência de IA com transparência, restringem trabalho anterior e estabelecem regras adicionais para vídeos em eventos digitais. A página específica exige autorização parental para menores e mais de 50% de first-time hackers para Beginner. A definição exata aplicável à equipe deve ser confirmada no portal/organização.

O documento geral de Contest Terms encontrado menciona uma temporada encerrada em junho de 2026. Não o trate como comprovação suficiente dos termos territoriais ou de prêmios para novembro. Essa pendência administrativa não impede testar o projeto localmente.

Registre a participação substancial de ChatGPT nesta versão; mantenha evidências das revisões humanas. Não reutilize este pacote em outro evento como se tivesse sido desenvolvido durante aquele evento. Não publique nem envie automaticamente sem revisão da equipe.

## Depois do evento

v1.1: SPL e paginação com limites e testes. v1.2: dados rotulados, avaliação por entidade e tempo, curvas de falsos positivos e calibração. v2: simulação pré-assinatura com modelo de ameaças próprio. Só anunciar métricas de detecção depois de estudos reproduzíveis.

Referências: [MLH evento](https://events.mlh.com/events/15200-solana-hackathon), [regras gerais](https://github.com/MLH/mlh-policies/blob/main/standard-hackathon-rules.md), [Contest Terms encontrado](https://github.com/MLH/mlh-policies/blob/main/contest-terms.md).
