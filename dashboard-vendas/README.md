# dashboard-vendas

Pipeline de agregação de dados de e-commerce e painel para acompanhamento das metas
comerciais. Lê os CSVs brutos de `data/`, grava agregações em `outputs/` e as exibe
num painel HTML.

## Uso

```bash
uv run python data_pipeline/pipeline.py     # gera outputs/
python3 -m http.server 8000                 # serve o painel
```

Painel em `http://localhost:8000/ui/painel-gestor-dados.html` — ele lê os CSVs de
`outputs/` a cada carregamento. Abrir por `file://` não funciona: o navegador bloqueia
o `fetch` por CORS.

## Estrutura

| Caminho | O que é |
|---|---|
| `data/` | CSVs brutos: vendas, clientes, estoque, marketing, atendimento |
| `data_pipeline/pipeline.py` | O pipeline |
| `data_pipeline/pipeline_bruto.py` | Histórico original do IPython, mantido como referência |
| `outputs/` | Agregações geradas (regeneráveis — não edite à mão) |
| `ui/painel-gestor-dados.html` | Painel que lê os CSVs |
| `ui/painel-gestor.html` | Versão anterior, com os valores cravados no HTML |

## Saídas

`kpis.csv` traz os 4 indicadores de topo — receita líquida, margem %, taxa de devolução
e ticket médio — com uma coluna `meta` em branco para preencher com o alvo do período.
As demais: `receita_bruta`, `receita_liquida`, `margem_mensal` (séries mensais),
`canal_count`, `eficiencia_canal`, `atendimento_custo`, `receita_por_categoria`.
