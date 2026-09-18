import pytest
from unittest.mock import MagicMock, patch

ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


@pytest.fixture
def openai_mockado():
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                with patch("builtins.print"):
                    yield


# ---------- persistencia_ativa ----------

def test_persistencia_ativa_true_quando_env_true():
    with patch.dict("os.environ", {"PERSISTENCIA_SQLITE": "true"}):
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is True


def test_persistencia_ativa_false_quando_env_ausente():
    import os
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("PERSISTENCIA_SQLITE", None)
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is False


def test_persistencia_ativa_false_quando_env_outro_valor():
    with patch.dict("os.environ", {"PERSISTENCIA_SQLITE": "yes"}):
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is False


# ---------- construir_sessao_chat ----------

def test_construir_sessao_chat_sem_persistencia_ignora_gerenciador(openai_mockado):
    with patch.dict("os.environ", {**ENV_VARS, "PERSISTENCIA_SQLITE": "false"}):
        from app_streamlit_core import construir_sessao_chat
        gerenciador = MagicMock()
        chat = construir_sessao_chat(gerenciador=gerenciador, thread_id=42)
        assert chat.gerenciador is None
        assert chat.thread_id is None


def test_construir_sessao_chat_com_persistencia_usa_gerenciador_e_thread_id(openai_mockado):
    with patch.dict("os.environ", {**ENV_VARS, "PERSISTENCIA_SQLITE": "true"}):
        from app_streamlit_core import construir_sessao_chat
        gerenciador = MagicMock()
        gerenciador.carregar_historico.return_value = []
        chat = construir_sessao_chat(gerenciador=gerenciador, thread_id=42)
        assert chat.gerenciador is gerenciador
        assert chat.thread_id == 42


# ---------- sanitizar_erro ----------

def test_sanitizar_erro_nao_contem_texto_bruto_da_excecao():
    from app_streamlit_core import sanitizar_erro
    exc = Exception("Erro ao chamar API OpenAI: chave sk-segredo-123 inválida")
    msg = sanitizar_erro(exc)
    assert "sk-segredo-123" not in msg
    assert "Erro ao chamar API OpenAI" not in msg


def test_sanitizar_erro_nao_contem_api_key_do_ambiente():
    from app_streamlit_core import sanitizar_erro
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-real-key-999"}):
        msg = sanitizar_erro(Exception("Traceback: falha em algum_modulo.py linha 10"))
        assert "sk-real-key-999" not in msg
        assert "Traceback" not in msg


# ---------- enviar_mensagem_seguro ----------

def test_enviar_mensagem_seguro_sucesso_retorna_resposta_sem_erro():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.enviar_mensagem.return_value = "Resposta do assistente"
    resposta, erro = enviar_mensagem_seguro(chat, "Olá")
    assert resposta == "Resposta do assistente"
    assert erro is None
    chat.enviar_mensagem.assert_called_once_with("Olá")


def test_enviar_mensagem_seguro_excecao_retorna_mensagem_sanitizada():
    from app_streamlit_core import enviar_mensagem_seguro, MENSAGEM_ERRO_AMIGAVEL
    chat = MagicMock()
    chat.enviar_mensagem.side_effect = Exception("Erro ao chamar API OpenAI: sk-segredo")
    resposta, erro = enviar_mensagem_seguro(chat, "Olá")
    assert resposta is None
    assert erro == MENSAGEM_ERRO_AMIGAVEL
    assert "sk-segredo" not in erro


def test_enviar_mensagem_seguro_texto_vazio_nao_chama_api():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.historico = []
    resposta, erro = enviar_mensagem_seguro(chat, "")
    assert resposta is None
    assert erro is None
    chat.enviar_mensagem.assert_not_called()
    assert chat.historico == []


def test_enviar_mensagem_seguro_texto_em_branco_nao_chama_api():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.historico = []
    resposta, erro = enviar_mensagem_seguro(chat, "   \n\t  ")
    assert resposta is None
    assert erro is None
    chat.enviar_mensagem.assert_not_called()
    assert chat.historico == []
