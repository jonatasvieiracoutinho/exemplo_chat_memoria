"""
App Streamlit: wiring dos widgets ao núcleo (app_streamlit_core).

Toda a lógica testável vive em `app_streamlit_core.py`. Este módulo apenas
conecta os widgets do Streamlit ao núcleo e mantém o estado da sessão.
"""

import streamlit as st

from app_streamlit_core import (
    construir_sessao_chat,
    enviar_mensagem_seguro,
    exportar_conversa_texto,
    excluir_thread,
    historico_para_ui,
    listar_threads,
    persistencia_ativa,
    resumo_tokens,
    retomar_thread,
)
from persistencia import GerenciadorPersistencia


def inicializar_estado():
    """Inicializa `chat`, `thread_id` e `gerenciador` em st.session_state
    uma única vez por sessão de navegador."""
    if "chat" not in st.session_state:
        gerenciador = GerenciadorPersistencia() if persistencia_ativa() else None
        st.session_state["gerenciador"] = gerenciador
        st.session_state["chat"] = construir_sessao_chat(gerenciador=gerenciador)
        st.session_state["thread_id"] = st.session_state["chat"].thread_id


def main():
    st.set_page_config(page_title="Chat com Memória", page_icon="💬")
    st.title("Chat com Memória")

    inicializar_estado()
    chat = st.session_state["chat"]

    with st.sidebar:
        if st.button("Limpar conversa"):
            chat.limpar_historico()
            st.rerun()

        tokens = resumo_tokens(chat)
        if tokens["total_persistido"] is not None:
            st.metric("Tokens (persistidos)", tokens["total_persistido"])
        else:
            st.metric("Tokens (aproximado)", tokens["aproximado"])

        nome, conteudo = exportar_conversa_texto(chat)
        st.download_button("Exportar conversa", data=conteudo, file_name=nome)

        gerenciador = st.session_state["gerenciador"]
        if persistencia_ativa() and gerenciador is not None:
            st.header("Threads")
            threads = listar_threads(gerenciador)
            if threads:
                opcoes = {t["id"]: t["titulo"] for t in threads}
                thread_escolhida = st.selectbox(
                    "Selecionar thread",
                    options=list(opcoes.keys()),
                    format_func=lambda tid: opcoes[tid],
                )
                if st.button("Retomar thread"):
                    st.session_state["chat"] = retomar_thread(gerenciador, thread_escolhida)
                    st.session_state["thread_id"] = thread_escolhida
                    st.rerun()
                if st.button("Excluir thread"):
                    excluir_thread(gerenciador, thread_escolhida)
                    st.rerun()

    for role, content in historico_para_ui(chat):
        with st.chat_message(role):
            st.write(content)

    entrada = st.chat_input("Digite sua mensagem")
    if entrada:
        resposta, erro = enviar_mensagem_seguro(chat, entrada)
        st.session_state["thread_id"] = chat.thread_id
        if erro:
            st.error(erro)
        elif resposta:
            st.rerun()


main()
