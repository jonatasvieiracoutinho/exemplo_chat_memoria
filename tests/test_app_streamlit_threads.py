import pytest
from unittest.mock import MagicMock, patch

from persistencia import GerenciadorPersistencia

ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
    "PERSISTENCIA_SQLITE": "true",
}


@pytest.fixture
def db():
    g = GerenciadorPersistencia(":memory:")
    yield g
    g.fechar()


@pytest.fixture
def chat_com_db(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    yield ChatComMemoria(gerenciador=db), db


def test_criar_listar_retomar_excluir_thread_ponta_a_ponta(chat_com_db):
    chat, db = chat_com_db
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                with patch("builtins.print"):
                    from app_streamlit_core import listar_threads, retomar_thread, excluir_thread

                    chat.adicionar_mensagem("user", "Pergunta 1")
                    chat.adicionar_mensagem("assistant", "Resposta 1")
                    thread_id = chat.thread_id

                    threads = listar_threads(db)
                    assert [t["id"] for t in threads] == [thread_id]

                    chat_retomado = retomar_thread(db, thread_id)
                    assert chat_retomado.thread_id == thread_id
                    assert chat_retomado.historico == [
                        {"role": "user", "content": "Pergunta 1"},
                        {"role": "assistant", "content": "Resposta 1"},
                    ]

                    assert excluir_thread(db, thread_id) is True
                    assert listar_threads(db) == []


def test_excluir_thread_inexistente_retorna_false(db):
    from app_streamlit_core import excluir_thread

    assert excluir_thread(db, 999) is False
