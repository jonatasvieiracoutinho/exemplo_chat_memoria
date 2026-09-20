import sqlite3
from contextlib import contextmanager
from datetime import datetime

BANCO_CAMINHO_PADRAO = "chat_memoria.db"


def _e_modo_memoria(caminho: str) -> bool:
    return caminho == ":memory:" or "mode=memory" in caminho


class GerenciadorPersistencia:
    def __init__(self, caminho: str = BANCO_CAMINHO_PADRAO):
        self.caminho = caminho
        self._memoria = _e_modo_memoria(caminho)
        self.conn = None
        if self._memoria:
            self.conn = sqlite3.connect(caminho, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON")
        self._criar_tabelas()

    @contextmanager
    def _conexao(self):
        """Conexão curta por operação no modo arquivo (compatível com reruns
        do Streamlit, que podem chamar em execuções diferentes); conexão
        única compartilhada no modo `:memory:`, que não sobrevive entre
        conexões distintas."""
        if self._memoria:
            conexao = self.conn
        else:
            conexao = sqlite3.connect(self.caminho)
            conexao.row_factory = sqlite3.Row
            conexao.execute("PRAGMA foreign_keys = ON")
        try:
            yield conexao
            conexao.commit()
        finally:
            if not self._memoria:
                conexao.close()

    def _criar_tabelas(self):
        with self._conexao() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS threads (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo        TEXT    NOT NULL,
                    criado_em     TEXT    NOT NULL,
                    atualizado_em TEXT    NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mensagens (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id INTEGER NOT NULL,
                    role      TEXT    NOT NULL,
                    content   TEXT    NOT NULL,
                    ordem     INTEGER NOT NULL,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
                );
            """)
        self._migrar_schema()

    def _migrar_schema(self):
        """Evolução idempotente do schema: cria a entidade de turno em bancos
        novos e pré-existentes sem recriar nem apagar dados. Colunas de tokens
        aceitam NULL (registros antigos e cenários sem `usage`)."""
        with self._conexao() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS turnos (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id         INTEGER NOT NULL,
                    ordem             INTEGER NOT NULL,
                    prompt_tokens     INTEGER,
                    completion_tokens INTEGER,
                    total_tokens      INTEGER,
                    criado_em         TEXT    NOT NULL,
                    FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
                );
            """)

    def criar_thread(self, titulo: str) -> int:
        agora = datetime.now().isoformat()
        with self._conexao() as conn:
            cursor = conn.execute(
                "INSERT INTO threads (titulo, criado_em, atualizado_em) VALUES (?, ?, ?)",
                (titulo, agora, agora),
            )
            return cursor.lastrowid

    def salvar_mensagem(self, thread_id: int, role: str, content: str, ordem: int):
        agora = datetime.now().isoformat()
        with self._conexao() as conn:
            conn.execute(
                "INSERT INTO mensagens (thread_id, role, content, ordem) VALUES (?, ?, ?, ?)",
                (thread_id, role, content, ordem),
            )
            conn.execute(
                "UPDATE threads SET atualizado_em = ? WHERE id = ?",
                (agora, thread_id),
            )

    def listar_threads(self) -> list:
        with self._conexao() as conn:
            cursor = conn.execute("""
                SELECT t.id, t.titulo, t.criado_em, t.atualizado_em,
                       COUNT(m.id) AS total_mensagens
                  FROM threads t
                  LEFT JOIN mensagens m ON m.thread_id = t.id
                 GROUP BY t.id
                 ORDER BY t.atualizado_em DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def carregar_historico(self, thread_id: int) -> list:
        with self._conexao() as conn:
            cursor = conn.execute(
                "SELECT role, content FROM mensagens WHERE thread_id = ? ORDER BY ordem ASC",
                (thread_id,),
            )
            return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

    def excluir_thread(self, thread_id: int) -> bool:
        with self._conexao() as conn:
            cursor = conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
            return cursor.rowcount > 0

    def thread_existe(self, thread_id: int) -> bool:
        with self._conexao() as conn:
            cursor = conn.execute("SELECT 1 FROM threads WHERE id = ?", (thread_id,))
            return cursor.fetchone() is not None

    def salvar_turno(self, thread_id: int, prompt_tokens=None,
                     completion_tokens=None, total_tokens=None) -> int:
        """Registra um turno de conversa com a contagem real de tokens.
        Valores de tokens podem ser None (usage ausente/incompleto)."""
        agora = datetime.now().isoformat()
        with self._conexao() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(ordem), 0) + 1 AS proxima FROM turnos WHERE thread_id = ?",
                (thread_id,),
            )
            ordem = cursor.fetchone()["proxima"]
            cursor = conn.execute(
                """INSERT INTO turnos
                       (thread_id, ordem, prompt_tokens, completion_tokens, total_tokens, criado_em)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (thread_id, ordem, prompt_tokens, completion_tokens, total_tokens, agora),
            )
            conn.execute(
                "UPDATE threads SET atualizado_em = ? WHERE id = ?", (agora, thread_id)
            )
            return cursor.lastrowid

    def carregar_turnos(self, thread_id: int) -> list:
        """Lista os turnos de uma thread com tokens por turno, em ordem."""
        with self._conexao() as conn:
            cursor = conn.execute(
                """SELECT ordem, prompt_tokens, completion_tokens, total_tokens, criado_em
                     FROM turnos WHERE thread_id = ? ORDER BY ordem ASC""",
                (thread_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def total_tokens_thread(self, thread_id: int) -> dict:
        """Soma os tokens de todos os turnos de uma thread (ignora NULL)."""
        with self._conexao() as conn:
            cursor = conn.execute(
                """SELECT COALESCE(SUM(prompt_tokens), 0)     AS prompt_tokens,
                          COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                          COALESCE(SUM(total_tokens), 0)      AS total_tokens
                     FROM turnos WHERE thread_id = ?""",
                (thread_id,),
            )
            return dict(cursor.fetchone())

    def fechar(self):
        if self._memoria and self.conn:
            self.conn.close()
