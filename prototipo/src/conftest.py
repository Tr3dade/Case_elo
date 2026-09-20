"""Configuração compartilhada dos testes (o pytest carrega este arquivo sozinho).

A fixture abaixo roda antes de TODO teste (autouse) e garante duas coisas:
  1. nenhum teste escreve no prompts_log.md nem no uso_api.csv de verdade (vão para uma pasta temporária);
  2. nenhum teste faz chamada real à API: as variáveis da chave são removidas, então qualquer teste
     que esquecer de usar um LLM falso recebe RuntimeError em vez de gastar tokens.
"""
import pytest

import relatorio
import uso_api


@pytest.fixture(autouse=True)
def isolar_ambiente(tmp_path, monkeypatch):
    monkeypatch.setattr(relatorio, "LOG_PATH", str(tmp_path / "prompts_log.md"))
    monkeypatch.setattr(uso_api, "USO_PATH", str(tmp_path / "uso_api.csv"))
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API-KEY", raising=False)
