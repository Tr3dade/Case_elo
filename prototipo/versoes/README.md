# Versões do agente

Uma cópia de cada versão do agente, para consulta. Nada daqui é executado nem testado por esta pasta.

- `agente_v2_1.py` e `test_agente_v2_1.py`: v2.1 (o prompt sugere os extremos 250 e 450)
- `agente_v3.py` e `test_agente_v3.py`: v3 (o modelo deduz os extremos lendo a rampa)

A versão em uso é a que estiver em `../src/agente.py` (com `../src/test_agente.py`). Para trocar de
versão, copie o par desejado por cima desses dois arquivos e rode `python -m pytest -q` em `../src`.
Histórico e resultados de cada versão: `../prompts/versoes_prompts.md`.
