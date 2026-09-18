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
