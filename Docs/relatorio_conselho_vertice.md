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

## 4. Pergunta enquadrada para o Conselho

> Dentro do case Vértice Retail — diretoria quer recuperar rentabilidade e eficiência em 90 dias; entregável final é uma apresentação executiva + protótipo de IA demonstrável + business case; a squad está em um bootcamp com prazo apertado — qual vertente deve ser o eixo central da solução: **Margem**, **E-commerce/Marketing**, **Atendimento**, ou **Segmentação de Clientes**? Considerar o sinal e a magnitude de oportunidade encontrados em cada base de dados (resumidos acima).

---

## 5. As cinco perspectivas do Conselho

### 🔴 O Contrarian
A vertente Margem é a mais frágil das quatro: fora do Marketplace, a margem é chapada — 54% em todo mês, toda categoria. R$ 135 mil não sustenta um "business case" de peso para uma diretoria de uma empresa que fatura quase R$ 19M em receita líquida no período. Cuidado também com o entusiasmo em cima do E-commerce: a conta de "realocar budget e manter o ROAS" é a armadilha clássica de quem nunca escalou um canal — ROAS de Influenciador em R$ 28M investidos não se sustenta linearmente se vocês triplicarem o aporte ali. E o módulo de Atendimento, por mais barato de demonstrar, resolve sintoma, não causa: se "onde está meu pedido" é 30% dos tickets e não varia por canal, o problema está na operação logística, não em um classificador de IA — automatizar a triagem não entrega o pacote e nem acelera o transporte. Antes de escolher, a squad precisa admitir que nenhuma das quatro vertentes, isoladamente, é um "smoking gun" óbvio — e isso deveria estar explícito na apresentação, não escondido atrás de um número bonito de slide.

### 🔵 O First Principles Thinker
Voltando à pergunta original da diretoria — "rentabilidade, eficiência operacional e qualidade de decisão" — isso não é uma escolha entre quatro vertentes isoladas, é uma pergunta sobre onde o dinheiro está vazando com o menor esforço de correção. Rentabilidade = margem × eficiência de aquisição. Os dados mostram que o Marketplace é fraco nos dois lados (menor ROAS de marketing E menor margem de venda) — isso não é coincidência de duas vertentes concorrentes, é o mesmo problema visto por duas lentes diferentes. A vertente "certa" não é Margem OU E-commerce: é reconhecer que ambas descrevem o mesmo sintoma (alocação ruim de recursos comerciais) e construir uma única narrativa de causa-efeito em cima disso. Atendimento e Clientes são vertentes genuinamente distintas — problemas operacionais e de retenção que não têm relação causal direta com o problema comercial. A squad ganha mais clareza (e um diagnóstico mais defensável perante o CFO) se parar de tratar isso como "qual dos quatro" e passar a tratar como "qual é a árvore de causas, e qual módulo de IA ataca o nó mais alto dela".

### 🟢 O Expansionist
Ninguém está olhando para o tamanho real do prêmio aqui. Sim, R$ 135 mil de margem é pequeno — mas o potencial de realocação de budget de marketing (~R$ 90M investidos em canais de ROAS ~3 vs. um canal que entrega 7,75) é, na pior das hipóteses conservadoras, de sete dígitos em receita incremental, mesmo assumindo retornos decrescentes. Essa é a vertente com teto mais alto de longe. E tem mais: a squad está deixando dinheiro na mesa ao não conectar Atendimento como parte da mesma história — um classificador de tickets que já existe como Módulo B pronto no case é fácil de construir, barato de demonstrar ao vivo, e ainda ataca custo operacional puro (R$ 532 mil/ano em atendimento, R$ 160 mil só na categoria "onde está meu pedido"). Por que escolher uma vertente quando dá pra apresentar um pacote de duas iniciativas com perfis de risco/retorno complementares — uma de upside ofensivo (realocação de marketing) e uma de eficiência defensiva e rápida (automação de triagem)? Isso também joga a favor do slide de "quick win vs. estrutural" que o roteiro da apresentação final pede.

### ⚪ O Outsider
Não conheço o negócio de vocês, só o que está na frente de mim: dois números saltam aos olhos de qualquer pessoa de fora. Primeiro, "CAC quase igual, ROAS 2,5x diferente entre canais" é a frase mais fácil de vender numa sala de diretoria — não exige contexto nenhum para entender que tem dinheiro mal alocado ali. Segundo, "Marketplace é ruim nos dois lados" é a cereja: dá pra abrir a apresentação com um slide único mostrando os dois gráficos lado a lado e a diretoria já entende o problema antes de vocês abrirem a boca. Isso é muito mais forte, como comunicação, do que "margem caiu 3 pontos percentuais nesse canal" ou "24,8% da base está inativa" — números que exigem mais explicação para gerar reação. Se o objetivo é convencer uma diretoria em 11 slides, a vertente que já vem com a história pronta e visual ganha. As outras duas (Atendimento, Clientes) são interessantes, mas soam mais como "itens de backlog" do que "a resposta que vocês foram contratados para dar".

### 🟡 O Executor
Esqueçam a beleza estratégica por um segundo — o que dá pra construir e demonstrar ao vivo dentro do prazo do bootcamp? Um classificador de tickets (Módulo B) usando o texto de `atendimento.csv` é o protótipo de IA mais rápido de montar e o mais "IA de verdade" para demonstrar: alimentam a coluna `texto_cliente`, chamam a API do Claude com um prompt de classificação (tema, sentimento, prioridade, ação recomendada), e em algumas horas têm uma demo funcional com casos reais do dataset. Um "motor de priorização de margem" ou uma "análise de funil" é essencialmente um dashboard com regras de negócio — mais fácil de fazer, mas menos impressionante como "solução de IA" num slide de demonstração. Minha recomendação prática: usem a vertente Margem/E-commerce (Marketplace) como o diagnóstico de negócio central da apresentação — é isso que sustenta o business case — e usem o classificador de atendimento como o protótipo demonstrável ao vivo no slide 7. Não tentem construir dois módulos de IA completos; vão entregar dois protótipos capengas em vez de um bom.

---

## 6. Revisão cruzada entre os conselheiros (síntese)

- **Resposta mais forte, segundo a maioria dos revisores:** a do First Principles Thinker — por reformular a pergunta e apontar que Margem e E-commerce descrevem o mesmo problema (Marketplace fraco nos dois lados), em vez de tratá-los como concorrentes.
- **Maior ponto cego identificado:** o Outsider e o Expansionist, isoladamente, venderam a ideia de "empacotar tudo" sem reconhecer o risco (levantado pelo Executor) de a squad tentar construir dois módulos de IA e entregar os dois pela metade dentro do prazo do bootcamp.
- **O que todos deixaram passar:** nenhuma das cinco respostas questionou a suposição por trás da estimativa de oportunidade de E-commerce (retorno marginal constante ao realocar budget) com a mesma força que o Contrarian levantou — isso deveria estar explicitamente marcado como premissa a validar/testar no business case, não como número final de slide. Também não foi discutido que 65% dos tickets de atendimento não têm `order_id` correspondente em vendas — um ponto de qualidade de dados que merece nota na seção de governança/riscos da apresentação final.

---

## 7. Veredito do Chairman

### Onde o conselho concorda
Há convergência real em dois pontos: (1) Margem e E-commerce não são vertentes concorrentes — são o mesmo sintoma (o canal Marketplace performa mal em ROAS e em margem simultaneamente) visto por duas lentes, e a squad ganha uma narrativa mais forte se unificar as duas em um único diagnóstico. (2) A vertente Atendimento tem um sinal genuinamente forte e independente (30% do volume de tickets, maior custo, segundo pior CSAT) que é rápido de demonstrar como protótipo de IA.

### Onde o conselho diverge
A divergência real é sobre **quanto peso dar à oportunidade de E-commerce**. O Contrarian e o Executor tratam a estimativa de realocação de budget como especulativa (ROAS não escala linearmente); o Expansionist a trata como o maior prêmio disponível. Essa tensão não se resolve com mais debate — resolve-se **testando**: a squad deveria simular a realocação com uma curva de retorno decrescente conservadora (ex: ROAS marginal cai 30–50% ao dobrar investimento num canal) antes de colocar um número absoluto no business case.

### Pontos cegos capturados na revisão cruzada
Dois riscos de execução que só apareceram na revisão cruzada, não nas respostas originais: (1) risco de a squad tentar fazer dois módulos de IA completos e entregar ambos malfeitos dentro do prazo do bootcamp; (2) 65% dos tickets de atendimento não conseguem ser vinculados a um pedido — isso é uma limitação de dados que precisa aparecer na seção de governança e riscos da apresentação, não ser escondida.

### A recomendação
**Escolham a narrativa Margem + E-commerce unificada em torno do canal Marketplace como diagnóstico central de negócio** (ele sustenta o business case, é a história mais fácil de defender com números e é a que mais se conecta à pergunta literal da diretoria sobre rentabilidade). **Usem o classificador de atendimento (Módulo B) como o protótipo de IA demonstrável ao vivo** no slide 7 — não porque seja a vertente de maior oportunidade financeira, mas porque é o módulo tecnicamente mais rápido de construir bem dentro do prazo e ainda se conecta ao case (redução de custo operacional, produtividade). Não tentem transformar Atendimento ou Clientes em um segundo diagnóstico de negócio completo — isso dilui o foco da apresentação. Deixem a vertente Clientes/Segmentação como uma nota de "próxima fase" no roadmap 30-60-90, não como pilar da entrega atual.

### A primeira coisa a fazer
Antes de escrever qualquer slide, façam o teste de sensibilidade da estimativa de E-commerce: recalculem a oportunidade de realocação de budget assumindo pelo menos dois cenários de retorno decrescente (conservador e moderado) — isso transforma a vertente de maior potencial em um número que resiste a uma pergunta de CFO em vez de um número que quebra na primeira pergunta.

---

## 8. Próximos passos sugeridos (roadmap de trabalho da squad)

1. Validar a hipótese Marketplace (margem + ROAS) com um teste de sensibilidade de realocação de budget.
2. Prototipar o classificador de tickets (tema, sentimento, urgência, ação recomendada) usando `texto_cliente` de `atendimento.csv`.
3. Redigir o business case com dois números: ganho estimado de margem/eficiência comercial (com premissas explícitas) e economia operacional em atendimento.
4. Deixar Clientes/Segmentação documentado como hipótese para a fase 60-90 dias, não como entregável desta rodada.
5. Anexar este documento como artefato de processo (evidência de rastreabilidade), junto com o código usado nas análises.

---

*Documento gerado como artefato de processo do case Vértice Retail — BootCamp Nova Geração, Elo Group, 2026.*
