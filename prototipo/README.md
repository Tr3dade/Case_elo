# Protótipo: frete grátis no Marketplace (simulador, relatório e agente)

Backend do protótipo do case Vértice Retail. Ele responde a uma pergunta: **a partir de qual valor de pedido
o Marketplace deveria dar frete grátis?** A resposta vem de três peças que se encaixam:

1. **Um motor de simulação** (`simulador.py`), determinístico: dado um threshold, calcula quantos pedidos ficam
   isentos, quanto de frete some da conta e quanta margem é recuperada. Não usa IA.
2. **Um agente** (`agente.py`) que usa o motor como ferramenta: decide quais thresholds testar, observa os
   resultados e conclui com uma recomendação e um memo. Fala com a Sandbox da Elo (um LLM).
3. **Um relatório final** (`relatorio_final.py`), montado pelo código a partir do resultado do agente, sem
   nenhuma chamada extra à API.

Os números vêm sempre do motor. O modelo escolhe o que testar e redige o texto, e o código confere o que dá.

## Estrutura

```
prototipo/
├── README.md
├── app.py                        front Streamlit (Painel do Gestor e Simulador de frete)
├── ui/                           blocos do Simulador que dependem do backend: dados em cache, agente com
│                                 progresso ao vivo, relatório final (o app.py só os chama); e os cálculos do
│                                 Painel (painel_calculos.py: mensal e categorias na base dos KPIs)
├── .env                          local, NÃO vai pro git: a chave da Sandbox
├── data/
│   ├── vendas.csv ...            bases do case
│   ├── marketplace_pedidos.csv   gerado por prep_dados.py
│   ├── rampa_canais_proprios.csv gerado por prep_dados.py
│   └── perfil_canais_proprios.csv gerado por prep_dados.py
├── prompts/
│   ├── prompts_log.md            cada prompt e resposta, gravado automaticamente
│   ├── uso_api.csv               tokens, custo e tempo de cada chamada à API
│   └── versoes_prompts.md        histórico das versões dos prompts e resultados dos testes
├── src/                          o código e os testes
└── versoes/                      um arquivo de cada versão do agente, só para consulta
```

## Preparo do ambiente

```bash
cd ~/BootCamp/Case_elo
source venv/bin/activate              # o venv do projeto (crie com: python -m venv venv)
pip install -r requirements.txt
```

Crie o arquivo `prototipo/.env` com uma linha (a chave da Sandbox de quem for rodar; ele nunca vai pro git):

```
API_KEY=sua_chave_da_sandbox
```

Os testes e o motor **não precisam de chave**. Só o relatório rápido e o agente chamam a API.

## Como rodar

Sempre de dentro de `prototipo/src` (o `test_simulador.py` usa um caminho relativo aos dados):

```bash
cd prototipo/src
python -m pytest -q          # 217 testes, sem rede e sem chave (inclui o front no AppTest)
python prep_dados.py         # só se os dados mudarem: regenera os 3 CSVs derivados
python relatorio.py          # relatório rápido: 1 chamada real (cerca de US$ 0,008)
python agente.py             # agente: 5 a 6 chamadas reais (cerca de US$ 0,05, de 36 a 96 s)
python agente.py --n 3       # 3 execuções seguidas e uma tabela de estabilidade (cerca de US$ 0,15)
python uso_api.py            # tokens e custo acumulados (JSON)
```

Não interrompa o `agente.py` com Ctrl+C: cada execução termina sozinha em no máximo cerca de 3 minutos.

## O que cada arquivo de `src/` faz

| Arquivo | Papel | Chama a API? |
|---|---|---|
| `prep_dados.py` | Lê `vendas.csv` e gera os 3 CSVs derivados. Roda offline, uma vez. | não |
| `simulador.py` | O motor: `simular`, `curva_completa`, `simular_politica_observada`. | não |
| `uso_api.py` | Registra tokens, custo e tempo de cada chamada em `prompts/uso_api.csv`. | não |
| `relatorio.py` | Conexão com a Sandbox e o relatório rápido (1 parágrafo, 1 chamada). | sim |
| `agente.py` | O agente: decide o que testar, conclui e devolve o caminho percorrido. | sim |
| `relatorio_final.py` | Monta o relatório completo a partir do resultado do agente. | não |
| `corrigir_log_prompts.py` | Uso único: coloca os prompts do log antigo em blocos de código. | não |

A dependência vai num sentido só: `simulador` e `uso_api` não importam nada do projeto; `relatorio` usa o
`uso_api`; `agente` usa os três; `relatorio_final` usa o `agente`, o `relatorio` e o `simulador`.

## Funções que o front usa

| Função | Recebe | Devolve | API? |
|---|---|---|---|
| `simular(threshold, pedidos)` | um valor e o DataFrame de pedidos | `dict` com `threshold`, `pct_pedidos_isentos`, `margem_recuperada`, `frete_restante`, `frete_pct_receita_nova`, `zona_com_evidencia`, `aviso` | não (poucos ms) |
| `curva_completa(lista, pedidos)` | lista de valores | `DataFrame`, uma linha de `simular` por valor (use `.to_dict("records")` para JSON) | não |
| `simular_politica_observada(pedidos, rampa)` | os pedidos e a rampa | `dict` com o **alvo**: `margem_recuperada`, `pct_pedidos_isentos`, `frete_restante`, `frete_pct_receita_nova`, `threshold_equivalente` | não (cerca de 100 ms: guarde o resultado) |
| `gerar_relatorio(resultado)` | o `dict` de `simular` | `str`: um parágrafo. Em falha da API, um texto-modelo (começa com `*(Texto-modelo`) | sim, 1 chamada |
| `gerar_relatorio_detalhado(resultado)` | o mesmo | `dict` com `texto`, `fallback`, `motivo_fallback` (só o tipo do erro) e `run_id` (para casar o custo em `uso_api`) | sim, 1 chamada |
| `prep_dados.preparar_tudo(vendas)` | o DataFrame de `vendas.csv` | `(pedidos do Marketplace, rampa, perfil)` em memória, iguais aos 3 CSVs derivados | não |
| `rodar_agente(missao, ao_passo=None, dados=None)` | nada (ou uma missão); `ao_passo(evento)` recebe `{"tipo", "passo", ...}` a cada evento (`inicio`, `chamada_modelo`, `acao`, `observacao`, `resposta_invalida`, `memo_recusado`, `fallback`, `fim`) e nunca derruba o agente; `dados=(pedidos, rampa, perfil)` evita ler os CSVs | `dict`, veja abaixo | sim, 5 a 6 chamadas |
| `montar_relatorio_final(resultado, pedidos, rampa, alvo=None)` | o resultado do agente e os dados | `dict`, veja abaixo | não |
| `uso_api.resumo_uso(run_id=None)` | um `run_id` (opcional) | `dict` com chamadas, tokens e custo em US$ | não |

**Resultado de `rodar_agente()`** (tudo serializável em JSON): `memo` (o texto final), `threshold_recomendado`,
`fallback` e `motivo_fallback`, `cenarios_testados` (números, no formato de `simular`: use para gráficos),
`caminho` (passos já formatados em português, com o `raciocinio`: use para a linha do tempo), `caminho_texto`,
`trilha` (registro bruto de auditoria; o campo `observacao` dela é um JSON dentro de uma string),
`passos`, `chamadas_tool`, `segundos`, `run_id` e `versao_prompt`.

**Resultado de `montar_relatorio_final(...)`**: `titulo`, `fallback`, `motivo_fallback`, `aviso`,
`threshold_recomendado`, `secoes` (lista de `id`, `titulo` e `markdown`: para abas ou blocos), `tabela` (linhas
numéricas, uma por cenário mais a linha do alvo), `verificacoes` (4 checagens automáticas) e `markdown` (o
relatório inteiro). As seções são: Recomendação, Ponto de partida, Evidência, Análise do agente, Alternativas
descartadas, Premissas e limites, Como chegamos aqui e Verificações. O relatório sai completo mesmo quando o
agente cai em fallback, com um aviso no topo.

## Como o agente funciona

A Sandbox documenta só `model`, `messages`, `temperature` e `max_tokens` em `POST /api/chat/completions`.
Chamadas com `tools` foram respondidas com as ferramentas da própria plataforma, então o agente **não usa
function calling**. Ele usa um protocolo em texto (o ReAct original):

1. o modelo recebe a missão e as ações possíveis;
2. a cada turno responde com **um objeto JSON**: `perfil_canais_proprios`, `simular_threshold` ou `concluir`;
3. o código valida o JSON, executa a ação no motor e devolve o resultado como a próxima mensagem;
4. o modelo decide de novo, até concluir com `threshold_recomendado` e o memo.

O prompt (versão `agente-v3`) não traz nenhum dos números da resposta: o modelo lê a rampa de isenção dos canais
próprios, identifica o limite inferior e o superior e testa esses dois antes de refinar. A meta não é maximizar
a isenção: é reproduzir o perfil dos canais próprios (o "alvo").

Proteções: máximo de 8 chamadas ao modelo, 5 ações de ferramenta, 2 respostas fora do protocolo e 120 s por
execução (timeout de 40 s por chamada, sem retentativa); o memo só é aceito se citar um threshold simulado, com
evidência nos dados, e a margem de um cenário simulado (com uma chance de correção). Se algo falhar, o resultado
vem do caminho determinístico: o threshold equivalente à política dos canais próprios.

## Exemplo de uso num front Streamlit

Este código foi executado com o agente e o relatório finais (com um Streamlit e um LLM de mentira):

```python
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from agente import rodar_agente
from relatorio_final import montar_relatorio_final
from simulador import simular_politica_observada

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@st.cache_data
def carregar():
    pedidos = pd.read_csv(os.path.join(DATA, "marketplace_pedidos.csv"))
    rampa = pd.read_csv(os.path.join(DATA, "rampa_canais_proprios.csv"))
    return pedidos, rampa, simular_politica_observada(pedidos, rampa)


pedidos, rampa, alvo = carregar()

if st.button("Rodar o agente"):
    with st.spinner("O agente está analisando (de 30 a 90 s)..."):
        resultado = rodar_agente()
    relatorio = montar_relatorio_final(resultado, pedidos, rampa, alvo)
    st.markdown(relatorio["markdown"])
    st.dataframe(pd.DataFrame(relatorio["tabela"]))
```

## Registros

- `prompts/prompts_log.md`: o prompt e a resposta de cada execução, e o caminho percorrido do agente. O prompt é
  gravado dentro de um bloco de código, porque fora dele o markdown esconde trechos entre sinais de menor e maior.
- `prompts/uso_api.csv`: uma linha por chamada (execução, origem, passo, tokens, custo em US$, segundos, status).
  A tarifa usada (US$ 0,50 por milhão de tokens de entrada e US$ 3,00 por milhão de saída) foi deduzida do painel
  da Sandbox. Para ver o custo em reais, preencha `COTACAO_USD_BRL` em `src/uso_api.py`.
- **Esses dois arquivos são versionados e mudam a cada execução real.** Antes de commitar, quem só rodou o agente
  para testar deve descartá-los: `git restore prototipo/prompts/prompts_log.md prototipo/prompts/uso_api.csv`.
  Assim não há conflito entre pessoas diferentes.

## Limitações e próximos passos

- O agente é síncrono (de 36 a 96 s). O front mostra cada passo pelo parâmetro `ao_passo`, mas se o usuário mexer na
  página durante a execução o Streamlit só atende o novo pedido depois que o agente termina.
- `gerar_relatorio` devolve só texto; para saber se veio da IA ou do texto-modelo use `gerar_relatorio_detalhado`.
- O menor threshold observado (R$ 250), as faixas da rampa e o teto de 1500 são constantes no código. Com dados
  novos, precisariam ser derivados dos dados.
- A "zona com evidência" só tem limite inferior: um threshold bem acima de R$ 450 passa como "com evidência",
  embora seja mais rígido que qualquer canal próprio.
- A simulação é estática: a margem recuperada é um potencial e não mede efeito na demanda nem quem absorve o
  custo da remessa. A base cobre cerca de um ano de vendas.
- Nenhuma função aqui cobre margem real (margem fantasma), cliente ou atendimento: só o frete do Marketplace.

## Solução de problemas

- **`RuntimeError: API_KEY (ou API-KEY) não encontrada`**: crie `prototipo/.env` com `API_KEY=sua_chave`.
- **`Connection error` da Sandbox**: o LiteLLM esconde o erro real. O terminal mostra a causa raiz em
  "Causa raiz". Já vimos `API_BASE` sem `https://` e chave inválida.
- **`pytest` com "import file mismatch"**: há duas cópias dos mesmos arquivos de teste (por exemplo, um zip
  descompactado dentro de `src/`). Apague a pasta duplicada.
- **Testes do `test_simulador.py` falham**: rode o `pytest` de dentro de `prototipo/src`.
- **O agente cai em fallback**: veja `motivo_fallback` no resultado e o fim da entrada dele em `prompts_log.md`.
