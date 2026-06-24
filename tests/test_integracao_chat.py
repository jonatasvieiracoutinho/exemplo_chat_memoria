import pytest
from unittest.mock import MagicMock, patch
from persistencia import GerenciadorPersistencia


ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


@pytest.fixture
def db():
    g = GerenciadorPersistencia(":memory:")
    yield g
    g.fechar()


@pytest.fixture
def chat_sem_persistencia():
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    yield ChatComMemoria()


@pytest.fixture
def chat_com_db(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    yield ChatComMemoria(gerenciador=db), db


# ---------- sem persistência ----------

def test_adicionar_mensagem_sem_gerenciador_nao_cria_thread(chat_sem_persistencia):
    chat = chat_sem_persistencia
    chat.adicionar_mensagem("user", "Olá")
    assert chat.thread_id is None
    assert len(chat.historico) == 1


def test_adicionar_mensagem_sem_gerenciador_historico_correto(chat_sem_persistencia):
    chat = chat_sem_persistencia
    chat.adicionar_mensagem("user", "Pergunta")
    chat.adicionar_mensagem("assistant", "Resposta")
    assert chat.historico[0]["role"] == "user"
    assert chat.historico[1]["role"] == "assistant"


# ---------- criação de thread ----------

def test_primeira_mensagem_usuario_cria_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Primeira mensagem")
    assert chat.thread_id is not None
    assert db.thread_existe(chat.thread_id)


def test_titulo_gerado_dos_primeiros_60_chars(chat_com_db):
    chat, db = chat_com_db
    mensagem_longa = "A" * 80
    chat.adicionar_mensagem("user", mensagem_longa)
    threads = db.listar_threads()
    assert len(threads[0]["titulo"]) == 60


def test_titulo_fallback_mensagem_vazia(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "   ")
    threads = db.listar_threads()
    assert threads[0]["titulo"] == "Conversa sem título"


def test_mensagem_assistant_antes_de_user_nao_cria_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("assistant", "Oi")
    assert chat.thread_id is None
    assert db.listar_threads() == []


# ---------- persistência sequencial ----------

def test_mensagens_subsequentes_salvas_na_mesma_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Pergunta 1")
    chat.adicionar_mensagem("assistant", "Resposta 1")
    chat.adicionar_mensagem("user", "Pergunta 2")
    historico = db.carregar_historico(chat.thread_id)
    assert len(historico) == 3


def test_historico_em_memoria_igual_ao_banco(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Teste")
    chat.adicionar_mensagem("assistant", "Ok")
    historico_db = db.carregar_historico(chat.thread_id)
    assert len(chat.historico) == len(historico_db)
    for mem, banco in zip(chat.historico, historico_db):
        assert mem["role"] == banco["role"]
        assert mem["content"] == banco["content"]


# ---------- janela deslizante não altera banco ----------

def test_janela_deslizante_nao_apaga_mensagens_do_banco(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, tamanho_janela=2)
    chat.adicionar_mensagem("user", "msg 1")
    chat.adicionar_mensagem("assistant", "resp 1")
    chat.adicionar_mensagem("user", "msg 2")
    chat.adicionar_mensagem("assistant", "resp 2")
    chat.adicionar_mensagem("user", "msg 3")
    chat._aplicar_janela_deslizante()
    historico_banco = db.carregar_historico(chat.thread_id)
    assert len(historico_banco) == 5
    assert len(chat.historico) <= 4


# ---------- retomar thread existente ----------

def test_historico_carregado_ao_retomar_thread(db):
    tid = db.criar_thread("Thread existente")
    db.salvar_mensagem(tid, "user", "Pergunta anterior", 1)
    db.salvar_mensagem(tid, "assistant", "Resposta anterior", 2)
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, thread_id=tid)
    assert len(chat.historico) == 2
    assert chat.historico[0]["content"] == "Pergunta anterior"


def test_titulo_nao_sobrescrito_ao_retomar_thread(db):
    tid = db.criar_thread("Título original")
    db.salvar_mensagem(tid, "user", "Primeira msg", 1)
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, thread_id=tid)
    chat.adicionar_mensagem("user", "Nova mensagem após retomar")
    threads = db.listar_threads()
    assert threads[0]["titulo"] == "Título original"
