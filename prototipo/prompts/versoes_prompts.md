# Versões dos prompts

Cada prompt tem um identificador `nome-vN`. O identificador aparece no cabeçalho de cada execução do
`prompts/prompts_log.md` e no campo `versao_prompt` do resultado do agente. O texto de cada versão vive
no código (`montar_prompt` em `relatorio.py` e `SYSTEM_AGENTE` em `agente.py`). Mudou o texto ou o
protocolo? Incremente a versão no código e acrescente uma linha aqui com o motivo e o que se observou.
As entradas do log anteriores à `relatorio-v2` não têm etiqueta.

Todas as datas são de 2026. Os custos vêm do painel de consumo da Sandbox e do `prompts/uso_api.csv`
(comando `python uso_api.py`).

## 1. relatorio (`relatorio.py`, `montar_prompt`)

Caminho simples: uma chamada, o modelo só escreve o parágrafo em cima de um número já calculado.

| Versão | Data | O que mudou | Motivo e resultado |
|---|---|---|---|
| relatorio-v1 | 20/09 | Prompt original: analista financeiro, parágrafo de 3-4 frases, tom executivo, sem inventar números além dos fornecidos. | Primeira chamada real à Sandbox: números corretos (R$ 250, R$ 159.556,45, 81,1%, 0,93%), mas o modelo terminou com uma pergunta ("Seria útil que eu elaborasse uma apresentação executiva...?"), inadequada para um parágrafo que aparece na tela. |
| relatorio-v2 | 20/09 | Acrescentada a instrução: "Responda apenas com o parágrafo: sem saudação, sem perguntas e sem oferecer material adicional." | Chamada real seguinte: parágrafo limpo, sem pergunta final, todos os números conferem com o simulador. Custo médio observado: cerca de US$ 0,008 por relatório (4 chamadas reais). |

## 2. agente (`agente.py`, `SYSTEM_AGENTE`)

Caminho em que o modelo decide o que testar. Os números vêm sempre do motor determinístico
(`simulador.py`); o modelo escolhe as ações, observa os resultados e conclui com um memo.

### 2.1 Linha do tempo

| Versão | Data | Protocolo | O que mudou | Resultado |
|---|---|---|---|---|
| agente-v1 | 20/09 | Function calling nativo (`bind_tools`) | Primeira versão, com duas ferramentas. Missão de reproduzir o perfil dos canais próprios (e não de maximizar a isenção). | **2 execuções reais:** o modelo pediu só ferramentas da própria Sandbox (`search_filesystem`, `web_search`, `view_skill`, `execute_code`...) e nunca as nossas. Fallback nas duas (US$ 0,0367 e US$ 0,0424). Diagnóstico: `tool_choice` devolve HTTP 400; a documentação de `POST /api/chat/completions` lista só `model`, `messages`, `stream`, `temperature` e `max_tokens`; toda chamada com `tools` foi "sequestrada" pelas ferramentas da plataforma, enquanto as chamadas sem `tools` (o relatório) responderam normalmente. |
| agente-v2 | 20/09 | Texto (ReAct original): um objeto JSON por turno | Sem `tools`. O modelo responde com a ação (`perfil_canais_proprios`, `simular_threshold` ou `concluir`) e o código devolve a observação como mensagem do usuário. Proteções: limite de passos e de ações, orçamento de tempo, validação do memo, fallback. | **1ª execução real:** 6 passos (perfil, 250, 450, 300, 275, concluir), sem fallback, 35,3 s, US$ 0,0455; recomendou R$ 275 e os números conferem com o simulador. Quem decidiu o quê: o prompt **sugeria** começar pelos extremos 250 e 450; os valores 300 e 275, o momento de parar e a redação foram do modelo (300 e 275 não aparecem no prompt, e o `threshold_equivalente` nunca é enviado a ele). |
| agente-v2.1 | 20/09 | Igual à v2 | Acrescenta `raciocinio` em cada ação, o "caminho percorrido" montado pelo código, o campo estruturado `threshold_recomendado` e o teste de estabilidade `--n`. O prompt continua sugerindo os extremos 250 e 450. | **1ª execução real:** 6 passos (perfil, 250, 450, 300, 275, concluir), sem fallback, 81,8 s (um único passo levou 49 s), US$ 0,0458. Recomendou R$ 275, com `raciocinio` preenchido em todas as ações e o caminho citado no memo; os números conferem com o simulador. A sequência foi a mesma da v2. |
| agente-v3 | 20/09 | Igual à v2 | Igual à v2.1, com **uma única diferença: o prompt não dita os extremos**. Manda o modelo ler a rampa na observação do perfil, identificar o limite inferior (onde a isenção passa de zero) e o superior (onde chega a 100%), testar esses dois e refinar. Nenhum número da resposta (250, 275, 300, 450) aparece no prompt, e um teste automático garante isso. | **3 execuções reais:** sequência idêntica nas três (250 → 450 → 300 → 275), recomendado R$ 275 em 3 de 3, os dois extremos testados em 3 de 3, nenhum fallback; 95,7 s, 87,8 s e 36,4 s; US$ 0,0536, 0,0518 e 0,0440. O critério de adoção da seção 3 foi cumprido. Sem receber os números no prompt, o modelo testou 250 e 450 como primeiras simulações nas três execuções (a justificativa de cada passo está no `prompts_log.md`). |

### 2.2 O que cada versão faz de diferente

| | v2 | v2.1 | v3 |
|---|---|---|---|
| Quem indica os extremos da rampa (250 e 450)? | o prompt sugere | o prompt sugere | **o modelo deduz** lendo a rampa |
| Justificativa por ação (`raciocinio`) | não | sim | sim (e diz onde na rampa achou cada limite) |
| Threshold recomendado estruturado (`threshold_recomendado`) | não | sim | sim |
| Caminho percorrido (`caminho`, `caminho_texto`) | não | sim | sim |
| O memo cita o caminho | não | sim, em 1 ou 2 frases | sim, incluindo os limites que identificou |
| `python agente.py --n 3` (tabela de estabilidade) | não | sim | sim |

A v2.1 e a v3 têm **código idêntico**. Diferem só no prompt, no identificador `VERSAO_AGENTE` e no
docstring. Assim, se o comportamento mudar entre elas, a causa é a estratégia dita (ou não) pelo prompt.

### 2.3 O que são o `raciocinio` e o "caminho percorrido"

- **`raciocinio`:** uma frase que o modelo preenche em cada ação de ferramenta dizendo por que a
  escolheu (o "Thought" do ReAct). Fica na `trilha`, no `prompts_log.md` e no terminal (linhas `↳`).
  É a justificativa que o modelo **declara**, não uma janela para o processamento interno dele.
  Se faltar ou vier em formato errado, vira vazio e o turno continua válido.
- **Caminho percorrido:** montado pelo **código** a partir da trilha, e não narrado pelo modelo de
  memória. Cada passo traz o que foi testado e o que o motor devolveu (fatos: % de pedidos isentos,
  desvio em relação ao alvo, frete, margem recuperada) mais o `raciocinio` (a justificativa). Sai em
  duas formas: `caminho` (lista estruturada, para uma linha do tempo na tela) e `caminho_texto`.
  Motivo: se o modelo narrasse o caminho de memória, poderia inventar uma história plausível; assim,
  o que é fato vem do código e o que é justificativa vem do modelo, e a tela separa os dois.
- **`threshold_recomendado`:** campo da ação `concluir`. Vale se for um threshold simulado e com
  evidência; se faltar ou for inválido, usa-se o primeiro "R$ N" do memo que seja um threshold testado.
  No fallback é o threshold equivalente à política dos canais próprios.

### 2.4 Como descrever o agente na apresentação

Descrição que se sustenta com os dados acima: **"agente guiado"**. A estratégia inicial vem do prompt
(v2 e v2.1) ou é deduzida da rampa (v3); a busca fina, o momento de parar e a conclusão são do modelo;
todos os números vêm do motor determinístico; cada passo fica registrado com a justificativa; e há
proteções (limite de passos e de ações, orçamento de tempo, validação do memo, fallback determinístico).

Evite dizer que o agente "descobriu sozinho" o threshold: o problema é unidimensional, o alvo e o
desvio já vêm calculados pelo motor, e um `argmin` determinístico de poucas linhas chega ao mesmo R$ 275.
O valor do agente aqui é a justificativa auditável e a capacidade de acompanhar a política lida nos
dados, não achar algo que o código não acharia.

## 3. Experimento de estabilidade (v2.1 contra v3)

Uma execução não prova estabilidade. Para decidir qual versão apresentar:

```bash
python agente.py          # v2.1: uma execução, com progresso e justificativas
python agente.py --n 3    # v3: três execuções seguidas e tabela de estabilidade
python uso_api.py         # custo acumulado
```

A tabela do `--n` traz, por execução: a sequência de thresholds testados, o recomendado, se os dois
extremos da rampa foram simulados (`extremos`), se houve fallback, os segundos e o custo em US$. Numa execução
com fallback a coluna do recomendado fica `-`: quem escolheu foi o código, não o agente, e contar isso como
recomendação faria um agente instável parecer estável.

**Critério proposto para adotar a v3** (ajustável): nas 3 execuções, (a) nenhum fallback, (b) os dois
extremos testados em 3 de 3, (c) recomendações idênticas ou dentro de R$ 25 entre si. Se não cumprir,
apresenta-se a v2.1.

Resultados (preencher):

| Versão | Execuções | Fallback | Extremos testados | Recomendações | Tempo médio | Custo médio | Decisão |
|---|---|---|---|---|---|---|---|
| agente-v2.1 | 1 | 0 de 1 | 1 de 1 | 275 | 81,8 s | US$ 0,0458 | arquivada em `versoes/` |
| agente-v3 | 3 | 0 de 3 | 3 de 3 | 275, 275, 275 | 73,3 s (36,4 a 95,7 s) | US$ 0,0498 (total US$ 0,1494) | **adotada** (critério cumprido) |

**Decisão (20/09/2026):** a v3 é a versão em uso (`src/agente.py`). A v2.1 fica arquivada em `versoes/`, e como
o código das duas é idêntico fora do prompt, voltar para ela é copiar dois arquivos. Ressalvas: são 3 execuções,
o tempo variou bastante (de 36 a 96 s) e o orçamento de tempo do agente é de 120 s.

## 4. Limitações conhecidas

- **Poucas execuções.** Nenhum resultado aqui é estatístico; a tabela da seção 3 é evidência de estabilidade, não prova.
- **Protocolo em texto.** A Sandbox não documenta `tools`; por isso o agente usa JSON por turno. Uma resposta
  fora do protocolo ganha uma correção de rota e, na segunda, o agente cai no fallback.
- **Constantes fixas.** O limite inferior `MENOR_THRESHOLD_OBSERVADO` (250) está fixo em `simulador.py` e as
  faixas da rampa em `prep_dados.py`. A v3 lê a rampa, mas com dados novos essas constantes precisariam ser
  derivadas dos dados. Hoje o comportamento só acompanha os dados dentro do que essas constantes já cobrem.
- **Premissa do simulador.** Nos dados, pedido isento mostra frete zero, mas não mostra quem absorve o custo da
  remessa nem se a demanda reage. A margem recuperada é um potencial, condicionado ao Marketplace se
  comportar como os canais próprios.
- **Custo e tempo.** A Sandbox soma cerca de 10 mil tokens de entrada em toda chamada. Execuções reais: v2, US$ 0,0455
  e 35 s; v2.1, US$ 0,0458 e 82 s; v3, média de US$ 0,0498 e 73 s (de 36 a 96 s). O tempo varia com a carga da
  Sandbox (um passo isolado levou 49 s), e o orçamento de tempo do agente é de 120 s: numa demonstração lenta, o
  agente pode cair no fallback, que devolve o mesmo threshold pelo texto-modelo.

## 5. Onde está cada versão no repositório

- `prototipo/src/agente.py` e `prototipo/src/test_agente.py`: a **versão em uso** (hoje, a v3). É o par que o
  `python -m pytest -q` testa e que o front importa.
- `prototipo/versoes/`: **um arquivo de cada versão** (`agente_v2_1.py`, `agente_v3.py` e os testes de cada uma),
  só para consulta. O `conftest.py` da pasta impede o pytest de coletá-los. Para trocar de versão, copie o par
  desejado por cima de `src/agente.py` e `src/test_agente.py`.
- Histórico do git: cada versão adotada tem o seu commit.
- Rode o `pytest` sempre de dentro de `prototipo/src` (o `test_simulador.py` usa um caminho relativo aos dados).
