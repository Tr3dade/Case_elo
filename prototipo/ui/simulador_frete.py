"""Blocos novos da página "Simulador de frete": aviso de zona sem evidência, agente com progresso ao vivo,
botão "Aplicar no simulador" e relatório final. O app.py só chama as funções públicas daqui.

Estado (st.session_state), tudo em chaves que NÃO são de widget, por isso sobrevive à troca de página:
    resultado_agente   o dict devolvido por agente.rodar_agente
    relatorio_final    o dict devolvido por relatorio_final.montar_relatorio_final (do mesmo resultado)
    threshold_frete    o valor do slider (é a key dele: some ao sair da página)
    threshold_frete_salvo  cópia do valor do slider, que não some (ver inicializar_threshold)

Dois cuidados de tela que valem para tudo que vem daqui:
  * Cifrão: o markdown do Streamlit lê "$...$" como fórmula, então "R$ 250 ... R$ 159.556,45" numa linha
    sairia como matemática. escapar_cifrao troca "$" por "\\$" SÓ na hora de exibir; o texto do download
    e os dados ficam intactos.
  * Interação durante o agente: o Streamlit interrompe o script no próximo st.* levantando RerunException
    (BaseException). Deixar isso passar mataria o agente no meio (tokens já gastos, log pela metade), então
    o callback de progresso segura essa exceção, para de escrever na tela e deixa o agente terminar.
"""
import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, StopException

CHAVE_AGENTE = "resultado_agente"
CHAVE_RELATORIO = "relatorio_final"
CHAVE_THRESHOLD = "threshold_frete"                  # a key do slider
CHAVE_THRESHOLD_SALVO = "threshold_frete_salvo"       # cópia que sobrevive à troca de página

AVISO_CUSTO = "estimado: tarifa não confirmada pelo mentor"
SEPARADOR_JUSTIFICATIVA = "\n   Justificativa do agente: "     # como agente.formatar_caminho separa a justificativa


def escapar_cifrao(texto) -> str:
    """'R$ 250' -> 'R\\$ 250', para o markdown não ler o cifrão como início de fórmula. Só para exibir."""
    return (texto or "").replace("$", "\\$")


def inicializar_threshold(padrao: int) -> None:
    """Antes do slider: garante o valor inicial dele em session_state["threshold_frete"].

    O slider tem key, e o Streamlit APAGA o estado de um widget quando a página não o renderiza (é o que
    acontece na ida ao Painel). Por isso o valor também fica numa cópia (chave que não é de widget, ver
    guardar_threshold) e é restaurado aqui na volta. Na primeira visita vale o padrão.
    """
    st.session_state.setdefault(CHAVE_THRESHOLD, st.session_state.get(CHAVE_THRESHOLD_SALVO, padrao))


def guardar_threshold(valor) -> None:
    """Depois do slider: guarda a cópia do valor que sobrevive à troca de página."""
    st.session_state[CHAVE_THRESHOLD_SALVO] = int(valor)


def aplicar_threshold(valor) -> None:
    """Callback do botão "Aplicar no simulador". Roda ANTES do rerun, então quando o slider é criado de
    novo já encontra o valor (o slider não tem key: o valor entra pelo session_state)."""
    st.session_state[CHAVE_THRESHOLD] = int(valor)


def mostrar_aviso_zona(resultado: dict) -> None:
    """Avisa quando o threshold está abaixo do menor observado nos canais próprios (extrapolação)."""
    if not resultado.get("zona_com_evidencia", True):
        st.warning(escapar_cifrao(resultado["aviso"]))


# ----------------------------------------------------------------------------------------------
# Progresso ao vivo
# ----------------------------------------------------------------------------------------------
def _linha_do_passo(detalhe: dict) -> str:
    """Um passo do caminho (o "detalhe" do evento observacao) como item de lista markdown, com a
    justificativa do agente embaixo. O texto vem de agente.formatar_caminho: mesma formatação do log."""
    from agente import formatar_caminho

    principal, _, justificativa = formatar_caminho([detalhe]).partition(SEPARADOR_JUSTIFICATIVA)
    item = f"- {principal}"
    if justificativa:
        item += f"\n  - _Justificativa do agente: {justificativa}_"
    return escapar_cifrao(item)


class ProgressoNaTela:
    """Callback ao_passo do agente: escreve cada evento num st.status enquanto o agente roda.

    Se o Streamlit mandar interromper o script (o usuário mexeu na página), a exceção de controle é
    capturada aqui, `interrompido` vira True e o callback fica mudo até o fim. Só RerunException e
    StopException são seguradas, nunca um BaseException genérico (Ctrl+C e SystemExit passam).
    """

    def __init__(self, status):
        self.status = status
        self.interrompido = False

    def __call__(self, evento: dict) -> None:
        if self.interrompido:
            return
        try:
            self._mostrar(evento)
        except (RerunException, StopException):
            self.interrompido = True

    def _mostrar(self, evento: dict) -> None:
        tipo, passo = evento["tipo"], evento["passo"]
        if tipo == "chamada_modelo":
            self.status.update(label=f"Passo {passo} (de até {evento['max_passos']}): consultando o modelo…")
        elif tipo == "acao":
            if evento["acao"] == "concluir":
                self.status.update(label=f"Passo {passo}: o agente concluiu; validando o memo…")
            else:
                alvo = f" com R$ {evento['threshold']}" if evento.get("threshold") is not None else ""
                self.status.update(label=escapar_cifrao(f"Passo {passo}: executando {evento['acao']}{alvo}…"))
        elif tipo == "observacao":
            self.status.write(_linha_do_passo(evento["detalhe"]))
        elif tipo == "resposta_invalida":
            self.status.write(f"⚠️ Passo {passo}: resposta fora do protocolo ({evento['motivo']}). Pedindo correção.")
        elif tipo == "memo_recusado":
            self.status.write(f"⚠️ Passo {passo}: memo recusado pela validação ({evento['motivo']}). Pedindo correção.")
        elif tipo == "fallback":
            self.status.write(escapar_cifrao(
                f"⚠️ Fallback: {evento['motivo']}. Usando o threshold equivalente à política dos canais próprios "
                f"(R$ {evento['threshold']})."))
        # "inicio" e "fim" não escrevem nada: o rótulo inicial e o final do status já dizem isso


# ----------------------------------------------------------------------------------------------
# Bloco do agente
# ----------------------------------------------------------------------------------------------
def _executar_agente(dados: tuple) -> None:
    """Roda o agente com progresso ao vivo e guarda o resultado e o relatório final no session_state.

    A ORDEM importa: o session_state é preenchido antes de qualquer st.* pós-execução. Se o usuário
    tiver interagido durante a execução, o próximo st.* levanta o rerun; como o resultado já está
    guardado, a nova rodada da página o mostra em vez de perdê-lo.
    """
    from agente import rodar_agente
    from relatorio_final import montar_relatorio_final

    pedidos, rampa, perfil, alvo = dados
    status = st.status("O agente está começando…", expanded=True)
    resultado = rodar_agente(ao_passo=ProgressoNaTela(status), dados=(pedidos, rampa, perfil))

    st.session_state[CHAVE_AGENTE] = resultado
    st.session_state[CHAVE_RELATORIO] = montar_relatorio_final(resultado, pedidos, rampa, alvo)

    if resultado["fallback"]:
        status.update(label="Concluído com fallback (veja o aviso abaixo)", state="error", expanded=False)
    else:
        status.update(label="Análise concluída", state="complete", expanded=False)


def _custo_da_execucao(run_id: str) -> str:
    """Custo em US$ da execução (soma das chamadas do run_id no uso_api.csv), sempre com o aviso de estimativa."""
    import uso_api

    resumo = uso_api.resumo_uso(run_id)
    if not resumo.get("chamadas"):
        return f"sem registro de uso ({AVISO_CUSTO})"
    return f"US$ {resumo['custo_usd']:.4f}".replace(".", ",") + f" em {resumo['chamadas']} chamadas ({AVISO_CUSTO})"


def _mostrar_resultado_agente(resultado: dict) -> None:
    recomendado = resultado["threshold_recomendado"]
    if resultado["fallback"]:
        st.warning(escapar_cifrao(
            f"Fallback: {resultado['motivo_fallback']}. O texto abaixo NÃO foi escrito pelo agente: é o caminho "
            f"determinístico (o threshold equivalente à política dos canais próprios)."))
    else:
        st.success("Resposta do agente (IA), sem fallback.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Threshold recomendado", f"R$ {recomendado}")
    c2.metric("Tempo e passos", f"{resultado['segundos']:.0f} s · {resultado['passos']} passos")
    c3.metric("Ações de ferramenta", resultado["chamadas_tool"])
    st.caption(f"Custo desta execução: {_custo_da_execucao(resultado['run_id'])}")

    st.markdown("**Memo**")
    st.markdown(escapar_cifrao(resultado["memo"]))
    with st.expander("Caminho percorrido"):
        if resultado["caminho"]:
            st.markdown("\n".join(_linha_do_passo(p) for p in resultado["caminho"]))
        else:
            st.write("O agente não executou nenhuma ação.")

    st.button(f"Aplicar R$ {recomendado} no simulador", key="aplicar_threshold_agente",
              on_click=aplicar_threshold, args=(recomendado,))


def render_bloco_agente(dados: tuple) -> None:
    """O bloco do agente. `dados` = (pedidos, rampa, perfil, alvo), como ui.dados.carregar_dados_frete devolve."""
    with st.container(border=True):
        st.subheader("Agente de recomendação")
        st.caption("O agente escolhe quais thresholds testar no simulador, compara com a política já praticada nos "
                   "canais próprios e conclui com um memo. Os números vêm sempre do motor; a IA escolhe o que testar e redige.")
        st.info("A execução leva de 36 a 96 s e faz chamadas reais à API (custo estimado abaixo). "
                "**Não interaja com a página enquanto ela roda** (slider, botões, menu): interagir interrompe a tela.")
        if st.button("Rodar agente", type="primary", key="rodar_agente"):
            _executar_agente(dados)
        resultado = st.session_state.get(CHAVE_AGENTE)
        if resultado is not None:
            _mostrar_resultado_agente(resultado)


# ----------------------------------------------------------------------------------------------
# Relatório final
# ----------------------------------------------------------------------------------------------
def render_relatorio_final() -> None:
    """O relatório final do último resultado do agente, com download em .md. Não aparece antes da 1ª execução."""
    relatorio = st.session_state.get(CHAVE_RELATORIO)
    if relatorio is None:
        return
    with st.container(border=True):
        st.subheader("Relatório final")
        st.caption("Montado pelo código a partir do resultado do agente: não faz nova chamada à API.")
        if relatorio["aviso"]:
            st.warning(escapar_cifrao(relatorio["aviso"]))
        st.markdown(f"**{escapar_cifrao(relatorio['titulo'])}**")
        for secao in relatorio["secoes"]:
            with st.expander(secao["titulo"], expanded=secao["id"] in ("recomendacao", "evidencia")):
                st.markdown(escapar_cifrao(secao["markdown"]))
        st.download_button("Baixar relatório (.md)", data=relatorio["markdown"],
                           file_name="relatorio_frete_gratis.md", mime="text/markdown",
                           key="baixar_relatorio_final")
