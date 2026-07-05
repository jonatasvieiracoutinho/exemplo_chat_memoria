import sqlite3

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


def test_tabela_turnos_criada(db):
    cursor = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas = {row[0] for row in cursor.fetchall()}
    assert "turnos" in tabelas


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


# ---------- salvar_turno ----------

def test_salvar_turno_retorna_id_inteiro(db):
    tid = db.criar_thread("Turnos")
    turno_id = db.salvar_turno(tid, 10, 20, 30)
    assert isinstance(turno_id, int)
    assert turno_id > 0


def test_salvar_turno_persiste_valores_corretos(db):
    tid = db.criar_thread("Turnos")
    db.salvar_turno(tid, 10, 20, 30)
    turnos = db.carregar_turnos(tid)
    assert turnos[0]["prompt_tokens"] == 10
    assert turnos[0]["completion_tokens"] == 20
    assert turnos[0]["total_tokens"] == 30


def test_salvar_turno_com_none_grava_null_sem_erro(db):
    tid = db.criar_thread("Turnos")
    db.salvar_turno(tid, None, None, None)
    turnos = db.carregar_turnos(tid)
    assert turnos[0]["prompt_tokens"] is None
    assert turnos[0]["completion_tokens"] is None
    assert turnos[0]["total_tokens"] is None


def test_salvar_turno_ordem_sequencial_por_thread(db):
    tid = db.criar_thread("Turnos")
    db.salvar_turno(tid, 1, 1, 2)
    db.salvar_turno(tid, 2, 2, 4)
    turnos = db.carregar_turnos(tid)
    assert [t["ordem"] for t in turnos] == [1, 2]


def test_salvar_turno_ordem_independente_por_thread(db):
    tid1 = db.criar_thread("Thread 1")
    tid2 = db.criar_thread("Thread 2")
    db.salvar_turno(tid1, 1, 1, 2)
    db.salvar_turno(tid2, 5, 5, 10)
    turnos_tid2 = db.carregar_turnos(tid2)
    assert turnos_tid2[0]["ordem"] == 1


# ---------- carregar_turnos ----------

def test_carregar_turnos_thread_sem_turnos_retorna_vazio(db):
    tid = db.criar_thread("Sem turnos")
    assert db.carregar_turnos(tid) == []


def test_carregar_turnos_ordem_crescente(db):
    tid = db.criar_thread("Vários turnos")
    db.salvar_turno(tid, 1, 1, 2)
    db.salvar_turno(tid, 2, 2, 4)
    db.salvar_turno(tid, 3, 3, 6)
    turnos = db.carregar_turnos(tid)
    assert [t["ordem"] for t in turnos] == [1, 2, 3]


# ---------- total_tokens_thread ----------

def test_total_tokens_thread_soma_corretamente(db):
    tid = db.criar_thread("Soma")
    db.salvar_turno(tid, 10, 20, 30)
    db.salvar_turno(tid, 5, 15, 20)
    total = db.total_tokens_thread(tid)
    assert total["prompt_tokens"] == 15
    assert total["completion_tokens"] == 35
    assert total["total_tokens"] == 50


def test_total_tokens_thread_ignora_null(db):
    tid = db.criar_thread("Com nulos")
    db.salvar_turno(tid, 10, 20, 30)
    db.salvar_turno(tid, None, None, None)
    total = db.total_tokens_thread(tid)
    assert total["prompt_tokens"] == 10
    assert total["completion_tokens"] == 20
    assert total["total_tokens"] == 30


def test_total_tokens_thread_sem_turnos_retorna_zero(db):
    tid = db.criar_thread("Vazia")
    total = db.total_tokens_thread(tid)
    assert total == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


# ---------- cascade de turnos ----------

def test_excluir_thread_remove_turnos_em_cascata(db):
    tid = db.criar_thread("Com turnos")
    db.salvar_turno(tid, 1, 1, 2)
    db.excluir_thread(tid)
    assert db.carregar_turnos(tid) == []


# ---------- migração idempotente sobre banco pré-existente ----------

def test_migracao_idempotente_sobre_banco_pre_existente(tmp_path):
    caminho_db = str(tmp_path / "antigo.db")

    conexao_antiga = sqlite3.connect(caminho_db)
    conexao_antiga.executescript("""
        CREATE TABLE threads (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo        TEXT    NOT NULL,
            criado_em     TEXT    NOT NULL,
            atualizado_em TEXT    NOT NULL
        );
        CREATE TABLE mensagens (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            role      TEXT    NOT NULL,
            content   TEXT    NOT NULL,
            ordem     INTEGER NOT NULL,
            FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
        );
    """)
    conexao_antiga.execute(
        "INSERT INTO threads (titulo, criado_em, atualizado_em) VALUES (?, ?, ?)",
        ("Thread antiga", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    conexao_antiga.commit()
    conexao_antiga.close()

    g1 = GerenciadorPersistencia(caminho_db)
    cursor = g1.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tabelas = {row[0] for row in cursor.fetchall()}
    assert "turnos" in tabelas
    threads = g1.listar_threads()
    assert len(threads) == 1
    assert threads[0]["titulo"] == "Thread antiga"
    g1.fechar()

    # abrir novamente não deve gerar erro nem duplicar estrutura
    g2 = GerenciadorPersistencia(caminho_db)
    cursor = g2.conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='turnos'"
    )
    assert cursor.fetchone()[0] == 1
    threads = g2.listar_threads()
    assert len(threads) == 1
    g2.fechar()
