"""
App Streamlit: wiring dos widgets ao núcleo (app_streamlit_core).

Toda a lógica testável vive em `app_streamlit_core.py`. Este módulo apenas
conecta os widgets do Streamlit ao núcleo e mantém o estado da sessão.
"""

import streamlit as st

from app_streamlit_core import (
    carregar_perfis,
    construir_sessao_chat,
    enviar_mensagem_seguro,
    exportar_conversa_texto,
    excluir_thread,
    historico_para_ui,
    listar_threads,
    persistencia_ativa,
    resumo_tokens,
    retomar_thread,
    trocar_perfil,
)
from persistencia import GerenciadorPersistencia

PERFIL_PADRAO = "Padrão (.env)"


def inicializar_estado():
    """Inicializa `chat`, `thread_id`, `gerenciador` e `perfil_ativo` em
    st.session_state uma única vez por sessão de navegador."""
    if "chat" not in st.session_state:
        gerenciador = GerenciadorPersistencia() if persistencia_ativa() else None
        st.session_state["gerenciador"] = gerenciador
        st.session_state["chat"] = construir_sessao_chat(gerenciador=gerenciador)
        st.session_state["thread_id"] = st.session_state["chat"].thread_id
        st.session_state["perfil_ativo"] = PERFIL_PADRAO


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

        st.header("Provedor")
        perfil_ativo = st.session_state["perfil_ativo"]
        st.caption(
            f"Ativo: {perfil_ativo} · base URL: {chat.base_url or '(padrão da OpenAI)'} · modelo: {chat.modelo}"
        )
        perfis = carregar_perfis()
        nomes = [perfil["nome"] for perfil in perfis]
        indice_atual = nomes.index(perfil_ativo) if perfil_ativo in nomes else 0
        nome_escolhido = st.selectbox("Trocar Perfil de provedor", options=nomes, index=indice_atual)
        if st.button("Confirmar Perfil"):
            perfil_escolhido = next(perfil for perfil in perfis if perfil["nome"] == nome_escolhido)
            chat_novo, motivo = trocar_perfil(perfil_escolhido, gerenciador=st.session_state["gerenciador"])
            if chat_novo is not None:
                st.session_state["chat"] = chat_novo
                st.session_state["thread_id"] = None
                st.session_state["perfil_ativo"] = nome_escolhido
                st.rerun()
            else:
                st.error(motivo)

    for role, content in historico_para_ui(chat):
        with st.chat_message(role):
            st.write(content)

    entrada = st.chat_input("Digite sua mensagem")
    if entrada:
        with st.chat_message("user"):
            st.write(entrada)
        with st.spinner("Gerando resposta..."):
            resposta, erro = enviar_mensagem_seguro(chat, entrada)
        st.session_state["thread_id"] = chat.thread_id
        if erro:
            st.error(erro)
        elif resposta:
            with st.chat_message("assistant"):
                st.write(resposta)


main()
