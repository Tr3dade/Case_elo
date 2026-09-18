"""Gerador de relatório executivo via LLM. Único arquivo que chama
uma API de IA generativa — tudo antes disso é cálculo determinístico."""
import os

def gerar_relatorio(resultado: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return ("*(ANTHROPIC_API_KEY não configurada — configure no .env)*\n\n"
                f"Recomenda-se frete grátis acima de R${resultado['threshold']:.0f}, "
                f"recuperando R${resultado['margem_recuperada']:,.2f} em margem.")

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    prompt = (
        "Você é um analista financeiro. Escreva um parágrafo curto (3-4 frases) "
        "recomendando a decisão abaixo para a diretoria da Vértice Retail, "
        "em português, tom executivo, sem inventar números além dos fornecidos.\n\n"
        f"Threshold de frete grátis simulado: R$ {resultado['threshold']:.0f}\n"
        f"Margem recuperada projetada: R$ {resultado['margem_recuperada']:,.2f}\n"
        f"Pedidos que passam a ter frete grátis: {resultado['pct_pedidos_isentos']}%\n"
        f"Frete restante como % da receita do canal: {resultado['frete_pct_receita_nova']}%\n"
    )

    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "prompts_log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n---\n**Prompt:**\n{prompt}\n")

    resposta = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = resposta.content[0].text
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n**Resposta:**\n{texto}\n")
    return texto
