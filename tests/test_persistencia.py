import pytest
from persistencia import GerenciadorPersistencia


@pytest.fixture
def db():
    g = GerenciadorPersistencia(":memory:")
    yield g
    g.fechar()


# ---------- tabelas ----------

def test_tabelas_criadas(db):
    cursor = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas = {row[0] for row in cursor.fetchall()}
    assert "threads" in tabelas
    assert "mensagens" in tabelas


# ---------- criar_thread ----------

def test_criar_thread_retorna_id_inteiro(db):
    tid = db.criar_thread("Primeira conversa")
    assert isinstance(tid, int)
    assert tid > 0


def test_criar_duas_threads_ids_distintos(db):
    id1 = db.criar_thread("Thread A")
    id2 = db.criar_thread("Thread B")
    assert id1 != id2


def test_criar_thread_titulo_salvo(db):
    db.criar_thread("Título da thread")
    threads = db.listar_threads()
    assert threads[0]["titulo"] == "Título da thread"


# ---------- listar_threads ----------

def test_listar_threads_vazio(db):
    assert db.listar_threads() == []


def test_listar_threads_retorna_todas(db):
    db.criar_thread("Thread 1")
    db.criar_thread("Thread 2")
    threads = db.listar_threads()
    assert len(threads) == 2


def test_listar_threads_contagem_mensagens(db):
    tid = db.criar_thread("Com mensagens")
    db.salvar_mensagem(tid, "user", "Olá", 1)
    db.salvar_mensagem(tid, "assistant", "Oi!", 2)
    threads = db.listar_threads()
    assert threads[0]["total_mensagens"] == 2


def test_listar_threads_sem_mensagens_conta_zero(db):
    db.criar_thread("Vazia")
    threads = db.listar_threads()
    assert threads[0]["total_mensagens"] == 0


# ---------- salvar_mensagem ----------

def test_salvar_mensagem_user(db):
    tid = db.criar_thread("Teste")
    db.salvar_mensagem(tid, "user", "Olá mundo", 1)
    historico = db.carregar_historico(tid)
    assert len(historico) == 1
    assert historico[0]["role"] == "user"
    assert historico[0]["content"] == "Olá mundo"


def test_salvar_mensagem_assistant(db):
    tid = db.criar_thread("Teste")
    db.salvar_mensagem(tid, "assistant", "Resposta", 1)
    historico = db.carregar_historico(tid)
    assert historico[0]["role"] == "assistant"


# ---------- carregar_historico ----------

def test_carregar_historico_ordem_correta(db):
    tid = db.criar_thread("Ordem")
    db.salvar_mensagem(tid, "user",      "Msg 1", 1)
    db.salvar_mensagem(tid, "assistant", "Resp 1", 2)
    db.salvar_mensagem(tid, "user",      "Msg 2", 3)
    historico = db.carregar_historico(tid)
    assert len(historico) == 3
    assert historico[0]["content"] == "Msg 1"
    assert historico[1]["content"] == "Resp 1"
    assert historico[2]["content"] == "Msg 2"


def test_carregar_historico_thread_inexistente_retorna_vazio(db):
    assert db.carregar_historico(9999) == []


def test_historico_contem_apenas_role_e_content(db):
    tid = db.criar_thread("Campos")
    db.salvar_mensagem(tid, "user", "Teste", 1)
    historico = db.carregar_historico(tid)
    assert set(historico[0].keys()) == {"role", "content"}


# ---------- excluir_thread ----------

def test_excluir_thread_remove_registro(db):
    tid = db.criar_thread("Para excluir")
    db.excluir_thread(tid)
    assert not db.thread_existe(tid)


def test_excluir_thread_retorna_true_quando_existe(db):
    tid = db.criar_thread("Existe")
    assert db.excluir_thread(tid) is True


def test_excluir_thread_retorna_false_quando_inexistente(db):
    assert db.excluir_thread(9999) is False


def test_excluir_thread_remove_mensagens_em_cascata(db):
    tid = db.criar_thread("Com msgs")
    db.salvar_mensagem(tid, "user", "msg", 1)
    db.excluir_thread(tid)
    assert db.carregar_historico(tid) == []


def test_excluir_thread_nao_afeta_outras_threads(db):
    tid1 = db.criar_thread("Fica")
    tid2 = db.criar_thread("Vai")
    db.salvar_mensagem(tid1, "user", "msg da thread 1", 1)
    db.excluir_thread(tid2)
    assert db.thread_existe(tid1)
    assert len(db.carregar_historico(tid1)) == 1


# ---------- thread_existe ----------

def test_thread_existe_retorna_true(db):
    tid = db.criar_thread("Existe")
    assert db.thread_existe(tid) is True


def test_thread_existe_retorna_false(db):
    assert db.thread_existe(9999) is False


# ---------- foreign key cascade com PRAGMA ----------

def test_foreign_key_cascade_ativo(db):
    tid = db.criar_thread("FK Test")
    db.salvar_mensagem(tid, "user", "msg", 1)
    db.conn.execute("DELETE FROM threads WHERE id = ?", (tid,))
    db.conn.commit()
    assert db.carregar_historico(tid) == []
