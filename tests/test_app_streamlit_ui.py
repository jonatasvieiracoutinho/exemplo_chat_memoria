import pytest

pytest.importorskip("streamlit")

from unittest.mock import MagicMock, patch


def _chat_mock():
    chat = MagicMock()
    chat.historico = []
    chat.thread_id = None
    chat.gerenciador = None
    chat.contar_tokens_aproximado.return_value = 42

    def _exportar(caminho):
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("conteudo exportado")

    chat.exportar_conversa.side_effect = _exportar

    def _limpar():
        chat.historico = []

    chat.limpar_historico.side_effect = _limpar
    return chat


def _chat_mock_com_helpers():
    chat = _chat_mock()
    chat.historico = [
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá"},
    ]
    return chat


def test_app_exibe_historico_e_envia_mensagem():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    def _enviar(c, texto):
        c.historico.append({"role": "user", "content": texto})
        c.historico.append({"role": "assistant", "content": "Resposta simulada"})
        c.thread_id = 1
        return "Resposta simulada", None

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert "Olá" in textos
    assert "Resposta simulada" in textos


def test_app_erro_sanitizado_aparece_amigavel():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    def _enviar_com_erro(c, texto):
        return None, "Não foi possível obter resposta agora. Tente novamente em instantes."

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar_com_erro):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    assert len(at.error) == 1
    assert "Não foi possível obter resposta" in at.error[0].value


def test_app_preserva_estado_entre_reruns():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    def _enviar(c, texto):
        c.historico.append({"role": "user", "content": texto})
        c.historico.append({"role": "assistant", "content": "Resposta simulada"})
        return "Resposta simulada", None

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat) as construir_mock, \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()
        at.run()

    construir_mock.assert_called_once()
    assert len(at.chat_message) == 2
    assert at.session_state["chat"] is chat
    assert "thread_id" in at.session_state
    assert "gerenciador" in at.session_state


def test_sidebar_limpar_esvazia_historico_exibido():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        assert len(at.chat_message) == 2
        at.sidebar.button[0].click().run()

    assert len(at.chat_message) == 0
    chat.limpar_historico.assert_called_once()


def test_sidebar_exibe_metrica_de_tokens():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert at.sidebar.metric[0].value == "42"


def test_sidebar_download_entrega_conteudo_exportado():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    botao = at.sidebar.download_button[0]
    assert botao.label == "Exportar conversa"
    chat.exportar_conversa.assert_called_once()
    caminho_usado = chat.exportar_conversa.call_args.args[0]
    assert caminho_usado.endswith(".txt")


def test_sidebar_painel_threads_ausente_quando_persistencia_desativada():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert not any(h.value == "Threads" for h in at.sidebar.header)


def test_sidebar_painel_threads_aparece_com_persistencia_ativa():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert any(h.value == "Threads" for h in at.sidebar.header)


def test_sidebar_retomar_thread_atualiza_sessao_e_historico():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    chat_retomado = _chat_mock_com_helpers()
    chat_retomado.thread_id = 1
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]), \
         patch("app_streamlit_core.retomar_thread", return_value=chat_retomado) as retomar_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.button[1].click().run()

    retomar_mock.assert_called_once_with(gerenciador, 1)
    assert at.session_state["chat"] is chat_retomado
    assert at.session_state["thread_id"] == 1


def test_bolha_usuario_aparece_imediatamente_com_spinner_mesmo_sem_append():
    """Discrimina o bug: a bolha do usuário deve ser pintada pela camada de
    wiring antes da geração, independente do núcleo anexar ao histórico."""
    from streamlit.testing.v1 import AppTest
    import streamlit as st

    chat = _chat_mock()

    def _enviar_sem_append(c, texto):
        return None, "Não foi possível obter resposta agora. Tente novamente em instantes."

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar_sem_append), \
         patch("app_streamlit.st.spinner", wraps=st.spinner) as spinner_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert "Olá" in textos
    spinner_mock.assert_called_once_with("Gerando resposta...")


def test_sidebar_excluir_thread_chama_helper_do_nucleo():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]), \
         patch("app_streamlit_core.excluir_thread") as excluir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.button[2].click().run()

    excluir_mock.assert_called_once_with(gerenciador, 1)
