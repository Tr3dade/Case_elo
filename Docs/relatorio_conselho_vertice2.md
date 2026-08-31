# Relatório de Diagnóstico e Conselho Consultivo — Projeto Vértice

**BootCamp Nova Geração · Elo Group · Cliente simulado: Vértice Retail**
**Documento:** artefato de processo (evidência de rastreabilidade) — análise quantitativa + análise qualitativa via conselho de perspectivas
**Squad:** [preencher nome da squad]

---

## 1. Contexto do case

A Vértice Retail é uma marca digital de moda, beleza e lifestyle que cresceu rápido via e-commerce, redes sociais, influenciadores e marketplace, mas viu a rentabilidade cair. A diretoria (CEO, CFO, CMO, COO) quer uma resposta objetiva em até 90 dias:

> Como podemos usar dados e IA para melhorar rentabilidade, eficiência operacional e qualidade da tomada de decisão nos próximos 90 dias?

A squad tinha duas vertentes candidatas em mente — **Margem** e **E-commerce** — e pediu uma análise de dados para decidir com evidência, mais uma leitura de conselho (múltiplas perspectivas) sobre qual caminho seguir.

---

## 2. Metodologia e bases utilizadas

Bases analisadas (fornecidas pela squad, formato CSV):

| Base | Registros | Uso nesta análise |
|---|---|---|
| `vendas.csv` | 27.759 pedidos | margem, receita, canal, categoria, devolução |
| `marketing.csv` | 3.500 campanhas | CAC, ROAS, investimento por canal |
| `clientes.csv` | 15.000 clientes | segmentação RFM, LTV |
| `atendimento.csv` | 35.841 tickets | volume, custo, CSAT por tema |
| `estoque.csv` | 5.000 SKUs | ruptura, giro (uso complementar) |

Período coberto pelas vendas: **jan/2023 a jan/2024**. Todas as métricas abaixo foram calculadas diretamente sobre os dados brutos (sem inferência), com o código documentado nesta seção.

---

## 3. Análise de dados por vertente

### 3.1 Vertente Margem

- Margem de contribuição geral: **54,4%** sobre receita líquida (R$ 10,27M em cima de R$ 18,89M).
- **Ao longo do tempo:** oscila entre 53% e 55% em todos os meses de 2023 — **não há tendência de queda estrutural**. O desconto médio sobe em novembro (Black Friday, 9,5%) e volta ao normal.
- **Por categoria:** homogêneo (54,1%–54,5%) — não há vilão aqui.
- **Por canal de venda:** o único desvio relevante é o **Marketplace, com 51,4%** de margem (vs. ~55% dos demais), sendo também o canal de maior volume (6.040 pedidos).
- **Devolução:** taxa geral de 14,9%, sem diferença relevante de margem entre pedidos devolvidos e não devolvidos. Motivos mais comuns: defeito, tamanho errado, atraso na entrega.

**Oportunidade estimada:** ~R$ 135 mil ao equalizar a margem do Marketplace ao patamar dos outros canais. Sinal real, mas concentrado e de magnitude moderada.

### 3.2 Vertente E-commerce / Marketing

- Todos os canais recebem investimento parecido (R$ 28M–33M) e o **CAC é quase idêntico entre eles** (R$ 3,95 a R$ 4,72).
- O **ROAS varia fortemente**: Influenciador (7,75) e TikTok Ads (4,67) muito acima de Marketplace (3,02) e Orgânico (3,01).
- Isso é um sinal forte de **má alocação de budget**: mesmo custo de aquisição, retorno até 2,5x diferente.
- **Cruzamento interessante:** o canal Marketplace aparece como o mais fraco nos dois lados — menor ROAS de marketing *e* menor margem de venda — o que reforça a possibilidade de tratar isso como um único fio narrativo.

**Oportunidade estimada:** potencialmente grande (o total investido em canais de baixo ROAS soma ~R$ 90M), mas a estimativa assume que realocar budget mantém o ROAS marginal constante — **suposição otimista que precisa ser validada** (é comum haver retornos decrescentes ao escalar um canal).

### 3.3 Vertente Atendimento (identificada nesta análise)

- **"Onde está meu pedido?" é a maior categoria de tickets** (10.765 de 35.841, ~30% do volume), com CSAT baixo (2,99) e custo de R$ 159,7 mil — a categoria mais cara do dataset.
- CSAT geral mais baixo aparece em "Defeito" (2,82); o único tema com CSAT alto é "Elogio" (4,57), como esperado.
- **Custo operacional total de atendimento: R$ 532 mil.**
- Cruzamento com canal de origem do pedido: **não há concentração por canal** — a taxa de tickets por pedido (~0,43–0,47) e a taxa específica de "onde está meu pedido" (~0,12–0,14) são parecidas em todos os canais. Ou seja, **este não é um problema de canal, é um problema estrutural de comunicação/logística pós-venda** que atinge a base toda igualmente.

**Oportunidade estimada:** a categoria "onde está meu pedido" sozinha custa ~R$ 160 mil/ano em operação e tem o segundo pior CSAT — é o tema com maior potencial de automação de triagem (Módulo B do case) e ganho rápido de produtividade.

### 3.4 Vertente Clientes / Segmentação (identificada nesta análise)

- Segmentação RFM já vem pronta na base: **Campeão** (LTV médio R$ 26.671) até **Hibernando** (LTV médio R$ 2.667) — quase **10x de diferença**.
- **24,8% da base (3.724 clientes) está em Churn ou Hibernando** — praticamente inativos, mas ainda recebendo o mesmo tipo de investimento de marketing que os demais.
- Isso levanta a pergunta: quanto do orçamento de aquisição/retenção está sendo mal direcionado para clientes que provavelmente não vão converter de novo?

**Oportunidade estimada:** não quantificável diretamente sem dados de custo de retenção por segmento, mas o tamanho da base inativa (quase 1 em cada 4 clientes) é grande o suficiente para justificar investigação.

### 3.5 Resumo comparativo

| Vertente | Força do sinal | Tamanho da oportunidade | Causa-raiz | Módulo de IA natural |
|---|---|---|---|---|
| Margem | Moderado, concentrado no Marketplace | ~R$ 135 mil | Pouco clara fora do Marketplace | C — priorização de margem |
| E-commerce | Forte (CAC igual, ROAS muito diferente) | Potencialmente grande, mas com suposição a validar | Clara — má alocação de budget | A — funil e eficiência de canais |
| Atendimento | Forte (30% do volume, maior custo, CSAT baixo) | ~R$ 160 mil + ganho de produtividade | Clara — falha de comunicação pós-venda, não é problema de canal | B — classificador de tickets |
| Clientes | Moderado (grande base inativa) | Não quantificado ainda | Requer mais dados de custo de retenção | Segmentação para direcionar ações |

---

## 4. Mudança de critério entre rodada 1 e rodada 2 do Conselho

A primeira rodada do conselho (registrada no Anexo A, ao final deste documento, como evidência de rastreabilidade do processo) julgou as vertentes por **impacto financeiro/operacional real**, como se a Vértice Retail fosse uma empresa de verdade decidindo onde investir. Isso é um critério legítimo de negócio, mas **não é o critério que a banca do bootcamp usa para avaliar a entrega**.

A grade de avaliação exige 8 blocos de entrega (Diagnóstico executivo, Análises e insights, Dashboard de gestão, Protótipo ou demo de IA, Business case, Roadmap 30-60-90, Governança e riscos, Pitch executivo) e nota a squad em **5 dimensões explícitas: Prompts utilizados, Agentes desenvolvidos, Clareza da solução, Qualidade das evidências, Storytelling executivo**.

Isso muda o critério de decisão: a pergunta deixa de ser "qual vertente teria mais retorno se a empresa existisse de verdade" e passa a ser **"qual vertente/combinação de vertentes permite preencher os 8 blocos com solidez e performar bem nas 5 dimensões de nota"**. Os dados levantados (seção 3) continuam sendo a evidência-base; o que muda é a lente de julgamento do conselho.

---

## 5. Pergunta enquadrada para o Conselho (rodada 2)

> Considerando as mesmas quatro vertentes com sinal de dados (Margem, E-commerce/Marketing, Atendimento, Clientes) e a mesma restrição de prazo de bootcamp, qual vertente central — ou combinação de vertentes — dá à squad a melhor base para (a) preencher com solidez os 8 blocos exigidos na entrega à banca (Diagnóstico, Análises, Dashboard, Protótipo/demo de IA, Business case, Roadmap, Governança e riscos, Pitch executivo) e (b) performar bem nas 5 dimensões de nota (Prompts utilizados, Agentes desenvolvidos, Clareza da solução, Qualidade das evidências, Storytelling executivo)? O critério de decisão é qualidade e solidez da entrega avaliada pela banca — não o tamanho do impacto financeiro real.

---

## 6. As cinco perspectivas do Conselho (rodada 2)

### 🔴 O Contrarian
O risco real aqui não é escolher a vertente errada — é a squad escolher uma vertente com boa história e esquecer que duas das cinco notas (**Prompts utilizados** e **Agentes desenvolvidos**) são avaliadas separadamente da qualidade do diagnóstico. Se vocês construírem só um dashboard bonito de margem/canal (o que é essencialmente agregação e regra de negócio, sem IA de verdade), podem ter um "Diagnóstico executivo" impecável e ainda assim tomar nota baixa em Prompts e Agentes — porque não existe agente nenhum rodando ali. Do outro lado, se o classificador de atendimento for construído às pressas só para ter algo bonito de mostrar no slide 7, sem versionamento de prompt nem validação de acurácia, vocês perdem em "Qualidade das evidências" justamente na parte que deveria ser sua vitrine técnica. A armadilha é achar que "vertente certa" resolve a nota — não resolve. As 5 dimensões são avaliadas de forma cruzada e independente, e uma vertente brilhante mal documentada tira nota de qualquer jeito.

### 🔵 O First Principles Thinker
O bloco "Dashboard de gestão" no anexo da banca já entrega a resposta, e ninguém prestou atenção nisso: a descrição pede um painel que acompanhe **"margem, canais, clientes, operação e atendimento"** — ou seja, a banca não espera que a squad escolha UMA vertente para todo o case. Ela espera amplitude no dashboard e nas análises, e profundidade/foco no diagnóstico e no protótipo. Isso resolve a falsa dicotomia: "qual vertente escolher" é a pergunta errada para os blocos de Dashboard e Análises (ali cabe mostrar domínio de todo o data room), mas é a pergunta certa para os blocos de Diagnóstico executivo, Business case e Pitch executivo, que precisam de UM fio narrativo forte para não parecerem dispersos. A squad ganha nota reformulando a escolha: qual vertente ancora a narrativa central (para clareza e storytelling), versus quais dados entram como evidência de apoio no dashboard (para amplitude e qualidade das evidências).

### 🟢 O Expansionist
Pensem na nota como um placar de 5 colunas, não uma nota só. Dá pra maximizar todas as 5 com um desenho específico: usem Margem+E-commerce (o duplo sinal fraco do Marketplace) como o diagnóstico central — isso é ótimo para Clareza da solução e Storytelling executivo, porque é a história mais fácil de contar em um slide. Usem o classificador de atendimento como o agente de IA de fato construído — isso é o que garante nota em Prompts utilizados (documentem as versões do prompt!) e Agentes desenvolvidos, além de virar a cena mais forte do Pitch executivo (demo ao vivo). E usem Clientes/Segmentação como uma camada extra dentro do Dashboard de gestão (não como um segundo módulo de IA) — isso soma pontos de amplitude em Qualidade das evidências sem custar tempo de desenvolvimento de um agente novo. Esse desenho cobre as 5 dimensões com o menor número de módulos construídos — eficiência de nota por hora de trabalho.

### ⚪ O Outsider
Uma coisa me chama atenção nessa grade que ninguém comentou: **"Prompts utilizados" é uma dimensão de nota própria**. Isso significa que a banca não quer só ver o resultado do agente — ela quer ver os prompts em si, como artefato. Isso conecta direto com aquela exigência de "artefatos de processo" no HTML do case (que pede resultados intermediários, cálculos, validações documentados). Ou seja: qualquer que seja a vertente escolhida, se a squad não guardar e mostrar a evolução dos prompts usados (não só o prompt final, mas as tentativas e ajustes), está deixando uma dimensória de nota inteira na mesa, independente de qual vertente escolherem. Isso é mais fácil de fazer bem com um agente de classificação de texto (tem iteração óbvia de prompt) do que com uma análise de margem (que é maioritariamente código determinístico, com pouco prompt para mostrar).

### 🟡 O Executor
Na prática, com o tempo de bootcamp que vocês têm, a ordem de construção importa mais que o debate teórico. Primeiro: montem o diagnóstico Margem+E-commerce (é rápido, é pandas e alguns gráficos, dá pra fazer em poucas horas). Segundo: construam o classificador de atendimento como agente real, com prompt versionado desde o rascunho até a versão final — guardem cada versão do prompt como artefato, isso é literalmente pontuação de "Prompts utilizados" de graça. Terceiro: montem o dashboard cobrindo margem, canal, cliente e atendimento juntos (a banca pediu isso explicitamente) — não precisa ser bonito, precisa ser completo. Quarto: usem o tempo que sobrar para lapidar o Pitch executivo (roteiro de 11 slides) e a seção de Governança e riscos, que ganha muito conteúdo de qualidade só de vocês documentarem os riscos reais do classificador (viés na priorização, alucinação na classificação, os 65% de tickets sem pedido vinculado). Não construam um segundo agente para Clientes — não há tempo, e não há necessidade dentro da grade de notas.

---

## 7. Revisão cruzada entre os conselheiros (rodada 2)

- **Resposta mais forte, segundo a maioria dos revisores:** a do Outsider — por identificar que "Prompts utilizados" é uma dimensão de nota separada e literal, algo que os outros quatro conselheiros mencionaram de forma indireta (Contrarian, Expansionist, Executor) mas sem nomear a implicação central: **documentar prompts é, por si só, uma fonte de nota independente da vertente escolhida**.
- **Maior ponto cego identificado:** a resposta do Expansionist, isoladamente, soa como "façam três coisas ao mesmo tempo" (diagnóstico + agente + dashboard ampliado) sem reconhecer, como o Executor fez, que isso só funciona se for sequenciado com disciplina de tempo — do contrário vira o mesmo risco de dispersão apontado na rodada 1.
- **O que todos deixaram passar:** nenhuma resposta comentou que a dimensão **"Agentes desenvolvidos"** está no plural na grade da banca — o que pode sinalizar (não é garantido, mas é um risco a considerar) que a banca valoriza mais de um agente funcionando, não apenas um. Isso é uma tensão real com a recomendação de "construam só um agente bem feito" e merece ser validado diretamente com os organizadores do bootcamp antes de a squad se comprometer com apenas um módulo de IA.

---

## 8. Veredito do Chairman (rodada 2)

### Onde o conselho concorda
Convergência forte em três pontos: (1) a escolha de vertente não é uma decisão única — ela se divide entre "qual ancora o diagnóstico/narrativa" (Margem+E-commerce, pelo duplo sinal do Marketplace) e "qual vira o agente de IA demonstrável" (Atendimento, pela natureza mais nativamente 'agentic' do problema de classificação de texto). (2) O Dashboard de gestão deve ter amplitude (margem, canal, cliente, atendimento), independentemente da vertente escolhida para o diagnóstico central — isso está explícito na própria descrição do bloco pela banca. (3) Documentar a evolução dos prompts utilizados é uma fonte de nota própria que nenhuma vertente resolve sozinha — é uma prática de processo, não uma escolha de tema.

### Onde o conselho clashes
A tensão real é entre foco e cobertura: o Executor e o First Principles Thinker defendem construir **um** agente bem feito (Atendimento) para não diluir esforço; o Expansionist inclina para cobrir mais terreno (diagnóstico + agente + dashboard ampliado) para maximizar as 5 dimensões. A resolução não é ideológica — depende de quanto tempo real a squad tem e de uma pergunta prática levantada na revisão cruzada: a grade menciona "Agentes desenvolvidos" no plural, o que pode significar que a banca espera mais de um agente. Isso precisa ser esclarecido com quem avalia antes de a squad se comprometer com uma arquitetura de um agente só.

### Blind spots capturados na revisão cruzada
Dois pontos que só emergiram na revisão: (1) o plural em "Agentes desenvolvidos" como possível sinal de expectativa de múltiplos agentes — risco de nota se a squad entregar apenas um; (2) o fato de "Prompts utilizados" ser avaliado como evidência de processo conecta diretamente com a exigência de "artefatos de processo" do HTML do case — ou seja, a squad já tem uma obrigação contratual (do case) de guardar isso, e ignorar essa sobreposição é perder uma sinergia fácil entre exigência do case e critério de nota.

### A recomendação
Mantenham **Margem + E-commerce (Marketplace) como o diagnóstico central da narrativa** — é o que dá clareza e storytelling ao pitch executivo. Construam o **classificador de atendimento como o agente principal de IA**, documentando cada versão do prompt como artefato de processo (isso serve dois propósitos ao mesmo tempo: nota em "Prompts utilizados" e cumprimento da exigência de rastreabilidade do case). Ampliem o **dashboard de gestão para cobrir margem, canal, cliente e atendimento juntos**, mesmo que o diagnóstico central seja só sobre Marketplace — isso é literalmente o que a banca pede nesse bloco. **Antes de fechar a arquitetura com um agente só**, tirem 5 minutos para confirmar com os organizadores do bootcamp se "Agentes desenvolvidos" no plural implica expectativa de mais de um agente — se sim, um segundo agente leve (ex: um agente simples de priorização de margem, reaproveitando a mesma lógica do diagnóstico) resolve isso sem grande esforço extra.

### A primeira coisa a fazer
Antes de escrever qualquer linha de código, criem um arquivo (`prompts_log.md` ou similar) para registrar cada versão do prompt do classificador de atendimento desde a primeira tentativa — isso vira automaticamente artefato de processo e evidência para a dimensão "Prompts utilizados", e é a única ação desta rodada que não existia antes e que custa poucos minutos para começar certo.

---

## 9. Próximos passos sugeridos (atualizados pela rodada 2)

1. Confirmar com a organização do bootcamp se "Agentes desenvolvidos" (plural) implica expectativa de mais de um agente na entrega.
2. Criar o log de prompts do classificador de atendimento desde a primeira versão (artefato de processo + nota em "Prompts utilizados").
3. Construir o diagnóstico Margem+E-commerce (Marketplace) como narrativa central do Pitch executivo.
4. Construir o classificador de atendimento como agente de IA principal, com validação de acurácia registrada (evidência para "Qualidade das evidências").
5. Montar o dashboard de gestão cobrindo margem, canal, cliente e atendimento (amplitude exigida pela banca).
6. Redigir a seção de Governança e riscos citando explicitamente: viés de priorização do classificador, risco de alucinação na classificação de texto, e a limitação de dados de que 65% dos tickets não têm `order_id` vinculado a uma venda.
7. Deixar Clientes/Segmentação como nota do roadmap 30-60-90 (fase 60-90 dias), a menos que a resposta do item 1 exija um segundo agente — nesse caso, ele é o candidato mais barato de transformar em um agente simples.
8. Anexar este documento (incluindo o Anexo A, rodada 1) como artefato de processo — a mudança de critério e o motivo da atualização também são evidência de raciocínio consultivo.

---

## Anexo A — Conselho, rodada 1 (critério de ROI de negócio real — substituído pela rodada 2)

*Mantido aqui como artefato de rastreabilidade do processo, conforme exigido pelo case. Esta rodada foi descartada como veredito final porque julgou as vertentes por impacto financeiro real, e não pelo critério de avaliação da banca (ver seção 4).*

### Pergunta enquadrada (rodada 1)

> Dentro do case Vértice Retail — diretoria quer recuperar rentabilidade e eficiência em 90 dias; entregável final é uma apresentação executiva + protótipo de IA demonstrável + business case; a squad está em um bootcamp com prazo apertado — qual vertente deve ser o eixo central da solução: **Margem**, **E-commerce/Marketing**, **Atendimento**, ou **Segmentação de Clientes**? Considerar o sinal e a magnitude de oportunidade encontrados em cada base de dados.

### As cinco perspectivas (rodada 1)

**🔴 O Contrarian:** A vertente Margem é a mais frágil das quatro: fora do Marketplace, a margem é chapada — 54% em todo mês, toda categoria. R$ 135 mil não sustenta um "business case" de peso para uma diretoria de uma empresa que fatura quase R$ 19M em receita líquida no período. Cuidado também com o entusiasmo em cima do E-commerce: a conta de "realocar budget e manter o ROAS" é a armadilha clássica de quem nunca escalou um canal. E o módulo de Atendimento resolve sintoma, não causa: se "onde está meu pedido" não varia por canal, o problema está na operação logística, não em um classificador de IA.

**🔵 O First Principles Thinker:** Rentabilidade = margem × eficiência de aquisição. O Marketplace é fraco nos dois lados (menor ROAS de marketing E menor margem de venda) — isso não é coincidência de duas vertentes concorrentes, é o mesmo problema visto por duas lentes diferentes. A vertente "certa" não é Margem OU E-commerce: é reconhecer que ambas descrevem o mesmo sintoma.

**🟢 O Expansionist:** O potencial de realocação de budget de marketing é, na pior das hipóteses conservadoras, de sete dígitos em receita incremental. Além disso, a squad está deixando dinheiro na mesa ao não conectar Atendimento como parte da mesma história — barato de demonstrar e ataca custo operacional puro.

**⚪ O Outsider:** "CAC quase igual, ROAS 2,5x diferente entre canais" é a frase mais fácil de vender numa sala de diretoria. "Marketplace é ruim nos dois lados" é a cereja: um slide único com os dois gráficos já entende o problema antes de a squad abrir a boca.

**🟡 O Executor:** Um classificador de tickets (Módulo B) é o protótipo de IA mais rápido de montar e o mais "IA de verdade" para demonstrar. Recomendação prática: Margem/E-commerce (Marketplace) como diagnóstico central + classificador de atendimento como protótipo demonstrável. Não construam dois módulos de IA completos.

### Veredito (rodada 1)

Unificar Margem + E-commerce em torno do Marketplace como diagnóstico central de negócio, e usar o classificador de atendimento como protótipo de IA demonstrável — recomendação feita com base no tamanho de oportunidade financeira e facilidade de execução, não em critério de nota de banca. **Substituída pela recomendação da rodada 2 (seção 8), que chega a uma arquitetura de solução semelhante, mas com justificativa ancorada nos critérios reais de avaliação do bootcamp.**

---

*Documento gerado como artefato de processo do case Vértice Retail — BootCamp Nova Geração, Elo Group, 2026. Inclui as duas rodadas do conselho como evidência de rastreabilidade do raciocínio consultivo.*
