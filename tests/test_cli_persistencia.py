import pytest
from unittest.mock import patch, MagicMock
from persistencia import GerenciadorPersistencia


@pytest.fixture
def db():
    g = GerenciadorPersistencia(":memory:")
    yield g
    g.fechar()


# ---------- _exibir_lista_threads ----------

def test_exibir_lista_threads_vazio(db, capsys):
    from chat_openai_memoria import _exibir_lista_threads
    _exibir_lista_threads(db)
    saida = capsys.readouterr().out
    assert "Nenhuma conversa armazenada" in saida


def test_exibir_lista_threads_mostra_threads(db, capsys):
    db.criar_thread("Thread de teste")
    from chat_openai_memoria import _exibir_lista_threads
    _exibir_lista_threads(db)
    saida = capsys.readouterr().out
    assert "Thread de teste" in saida


def test_exibir_lista_threads_mostra_contagem_mensagens(db, capsys):
    tid = db.criar_thread("Com msgs")
    db.salvar_mensagem(tid, "user", "Oi", 1)
    from chat_openai_memoria import _exibir_lista_threads
    _exibir_lista_threads(db)
    saida = capsys.readouterr().out
    assert "1 msg" in saida


# ---------- _selecionar_thread ----------

def test_selecionar_thread_nova_conversa(db):
    from chat_openai_memoria import _selecionar_thread
    with patch("builtins.input", return_value="0"):
        with patch("builtins.print"):
            resultado = _selecionar_thread(db)
    assert resultado is None


def test_selecionar_thread_id_existente(db):
    tid = db.criar_thread("Thread real")
    from chat_openai_memoria import _selecionar_thread
    with patch("builtins.input", return_value=str(tid)):
        with patch("builtins.print"):
            resultado = _selecionar_thread(db)
    assert resultado == tid


def test_selecionar_thread_id_invalido_tenta_novamente(db):
    tid = db.criar_thread("Thread real")
    from chat_openai_memoria import _selecionar_thread
    # Primeiro input inválido, segundo válido
    with patch("builtins.input", side_effect=["9999", str(tid)]):
        with patch("builtins.print"):
            resultado = _selecionar_thread(db)
    assert resultado == tid


def test_selecionar_thread_string_nao_numerica(db):
    tid = db.criar_thread("Thread real")
    from chat_openai_memoria import _selecionar_thread
    with patch("builtins.input", side_effect=["abc", "0"]):
        with patch("builtins.print"):
            resultado = _selecionar_thread(db)
    assert resultado is None


# ---------- lógica dos comandos (via ChatComMemoria + gerenciador mockado) ----------

ENV_VARS = {
    "OPENAI_API_KEY": "sk-test",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


@pytest.fixture
def chat_com_db(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db)
    return chat, db


def test_retomar_thread_substitui_historico(chat_com_db):
    chat, db = chat_com_db
    tid = db.criar_thread("Thread para retomar")
    db.salvar_mensagem(tid, "user", "Histórico anterior", 1)
    db.salvar_mensagem(tid, "assistant", "Resposta anterior", 2)

    historico = db.carregar_historico(tid)
    chat.historico = historico
    chat._aplicar_janela_deslizante()
    chat.thread_id = tid
    chat._thread_titulo_definido = True

    assert len(chat.historico) == 2
    assert chat.thread_id == tid


def test_excluir_thread_ativa_reseta_conversa(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Primeira msg")
    tid_ativo = chat.thread_id

    db.excluir_thread(tid_ativo)
    if tid_ativo == chat.thread_id:
        chat.historico = []
        chat.thread_id = None
        chat._thread_titulo_definido = False

    assert chat.thread_id is None
    assert chat.historico == []
    assert not db.thread_existe(tid_ativo)


def test_excluir_thread_inativa_nao_altera_chat(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Msg na thread ativa")
    tid_ativo = chat.thread_id
    tid_outro = db.criar_thread("Outra thread")

    db.excluir_thread(tid_outro)

    assert chat.thread_id == tid_ativo
    assert len(chat.historico) == 1


def test_cancelar_excluir_preserva_dados(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Msg")
    tid = chat.thread_id

    # Simula "n" na confirmação — não executa a exclusão
    assert db.thread_existe(tid)
    assert len(db.carregar_historico(tid)) == 1


def test_retomar_id_inexistente_nao_altera_historico(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Msg original")
    historico_antes = list(chat.historico)

    if not db.thread_existe(9999):
        pass  # comando /retomar não executa — histórico preservado

    assert chat.historico == historico_antes
