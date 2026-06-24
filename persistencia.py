import sqlite3
from datetime import datetime

BANCO_CAMINHO_PADRAO = "chat_memoria.db"


class GerenciadorPersistencia:
    def __init__(self, caminho: str = BANCO_CAMINHO_PADRAO):
        self.caminho = caminho
        self.conn = sqlite3.connect(caminho)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._criar_tabelas()

    def _criar_tabelas(self):
        self.conn.executescript("""
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
        self.conn.commit()

    def criar_thread(self, titulo: str) -> int:
        agora = datetime.now().isoformat()
        cursor = self.conn.execute(
            "INSERT INTO threads (titulo, criado_em, atualizado_em) VALUES (?, ?, ?)",
            (titulo, agora, agora),
        )
        self.conn.commit()
        return cursor.lastrowid

    def salvar_mensagem(self, thread_id: int, role: str, content: str, ordem: int):
        agora = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO mensagens (thread_id, role, content, ordem) VALUES (?, ?, ?, ?)",
            (thread_id, role, content, ordem),
        )
        self.conn.execute(
            "UPDATE threads SET atualizado_em = ? WHERE id = ?",
            (agora, thread_id),
        )
        self.conn.commit()

    def listar_threads(self) -> list:
        cursor = self.conn.execute("""
            SELECT t.id, t.titulo, t.criado_em, t.atualizado_em,
                   COUNT(m.id) AS total_mensagens
              FROM threads t
              LEFT JOIN mensagens m ON m.thread_id = t.id
             GROUP BY t.id
             ORDER BY t.atualizado_em DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def carregar_historico(self, thread_id: int) -> list:
        cursor = self.conn.execute(
            "SELECT role, content FROM mensagens WHERE thread_id = ? ORDER BY ordem ASC",
            (thread_id,),
        )
        return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

    def excluir_thread(self, thread_id: int) -> bool:
        cursor = self.conn.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def thread_existe(self, thread_id: int) -> bool:
        cursor = self.conn.execute("SELECT 1 FROM threads WHERE id = ?", (thread_id,))
        return cursor.fetchone() is not None

    def fechar(self):
        if self.conn:
            self.conn.close()
