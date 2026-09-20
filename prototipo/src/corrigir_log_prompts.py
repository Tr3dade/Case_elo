"""Corrige o prompts_log.md que JÁ EXISTE: coloca cada prompt registrado dentro de um bloco de código.

Motivo: no markdown (VS Code e GitHub), textos como <o threshold escolhido> são lidos como tags HTML e
somem da tela, e o prompt aparece quebrado. Dentro de um bloco de código eles aparecem intactos. As
execuções NOVAS já gravam o prompt cercado (ver registrar_log em agente.py e em relatorio.py); este
script existe só para consertar as entradas antigas. É uma correção de uma vez.

Garantias:
  - Só INSERE texto (a cerca de abertura e a de fechamento). Nada é removido nem reescrito.
  - Antes de gravar, confere que desfazendo as inserções o arquivo volta IDÊNTICO ao original.
    Se não voltar, aborta sem gravar nada.
  - É idempotente: se o log já estiver corrigido, não faz nada.
  - O log está no git: qualquer problema se desfaz com  git checkout -- prototipo/prompts/prompts_log.md

Uso (de dentro de src/):  python corrigir_log_prompts.py [caminho_do_log]
Códigos de saída: 0 = corrigido ou já estava corrigido; 1 = a verificação falhou (nada gravado);
                  2 = arquivo não encontrado.
"""
import os
import re
import sys

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOG_PADRAO = os.path.join(PROTOTIPO_DIR, "prompts", "prompts_log.md")

CERCA_ABRE = "```text\n"
CERCA_FECHA = "\n```"

# Onde está cada prompt no log (e o que vem logo depois dele):
#   agente:    **Prompt:**\n<prompt>\n\n**Missão:** ...
#   relatório: **Prompt** (data ou versão e data):\n<prompt>\n\n\n**Resposta...
# O "(?=...)" olha adiante sem consumir: o que vem depois do prompt não é alterado.
PADRAO_AGENTE = re.compile(r"(\*\*Prompt:\*\*\n)(.*?)(\n\n)(?=\*\*Missão:\*\*)", re.DOTALL)
PADRAO_RELATORIO = re.compile(r"(\*\*Prompt\*\* \([^)]*\):\n)(.*?)(\n+)(?=\*\*Resposta)", re.DOTALL)

# Os inversos: encontram exatamente o que foi inserido, para conferir a reversibilidade.
INVERSO_ABRE = re.compile(r"(\*\*Prompt(?::\*\*|\*\* \([^)]*\):)\n)```text\n")
INVERSO_FECHA = re.compile(r"\n```(\n+)(?=\*\*(?:Missão|Resposta))")


def _cercar(m: re.Match) -> str:
    """Devolve a mesma entrada com a cerca de abertura depois do cabeçalho e a de fechamento depois do prompt."""
    return m.group(1) + CERCA_ABRE + m.group(2) + CERCA_FECHA + m.group(3)


def corrigir_texto(texto: str) -> tuple:
    """Devolve (texto_corrigido, prompts_do_agente_cercados, prompts_do_relatorio_cercados)."""
    novo, n_agente = PADRAO_AGENTE.subn(_cercar, texto)
    novo, n_relatorio = PADRAO_RELATORIO.subn(_cercar, novo)
    return novo, n_agente, n_relatorio


def verificar(original: str, novo: str) -> bool:
    """True se, desfazendo as inserções, o texto novo volta idêntico ao original."""
    return INVERSO_FECHA.sub(r"\1", INVERSO_ABRE.sub(r"\1", novo)) == original


def main(caminho: str = LOG_PADRAO) -> int:
    if not os.path.exists(caminho):
        print(f"Arquivo não encontrado: {caminho}")
        return 2
    with open(caminho, encoding="utf-8", newline="") as f:
        original = f.read()

    if CERCA_ABRE in original:
        print("O log já está corrigido (já existe bloco de código nos prompts). Nada a fazer.")
        return 0

    novo, n_agente, n_relatorio = corrigir_texto(original)
    if not verificar(original, novo):
        print("ABORTADO: desfazendo as inserções o arquivo não voltou idêntico ao original. Nada foi gravado.")
        return 1
    if n_agente + n_relatorio == 0:
        print("Nenhum prompt encontrado no formato esperado. Nada a fazer.")
        return 0

    with open(caminho, "w", encoding="utf-8", newline="") as f:
        f.write(novo)
    print(f"Corrigido: {n_agente} prompt(s) do agente e {n_relatorio} do relatório dentro de blocos de código "
          f"({len(novo) - len(original)} caracteres inseridos, nenhum removido).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else LOG_PADRAO))
