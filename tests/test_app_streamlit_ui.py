import pytest

pytest.importorskip("streamlit")

from unittest.mock import MagicMock, patch


def _chat_mock():
    chat = MagicMock()
    chat.historico = []
    chat.thread_id = None
    chat.gerenciador = None
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
