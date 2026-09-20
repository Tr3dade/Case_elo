# Versões do agente

Uma cópia de cada versão do agente, para consulta. Nada daqui é executado nem testado por esta pasta (o
`conftest.py` daqui impede o pytest de coletar os arquivos).

- `agente_v2_1.py` e `test_agente_v2_1.py`: v2.1 (o prompt sugere os extremos 250 e 450)
- `agente_v3.py` e `test_agente_v3.py`: v3 (o modelo deduz os extremos lendo a rampa)

A versão em uso é a que estiver em `../src/agente.py` (com `../src/test_agente.py`). Para trocar de versão,
copie o par desejado por cima desses dois arquivos e rode `python -m pytest -q` em `../src`.
Histórico e resultados de cada versão: `../prompts/versoes_prompts.md`.

## Uma diferença entre `../src/agente.py` e `agente_v3.py`

O `../src/agente.py` (a v3 em uso) difere do `agente_v3.py` desta pasta **só na formatação do log**: o prompt
passou a ser gravado em bloco de código e o threshold recomendado sai como `R$ 275` em vez de `R$ 275.0`.
O prompt, o protocolo e o comportamento são idênticos, e por isso o resultado do experimento de estabilidade
(3 execuções de 3, todas com R$ 275) continua valendo. Os arquivos desta pasta ficam exatamente como foram
avaliados no experimento, sem alteração.
