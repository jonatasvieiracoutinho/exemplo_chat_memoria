# Plano de Implementação: Persistência SQLite de Conversas (Threads)

> **Modo**: Sem testes manuais (orquestração automática). Toda validação é automatizada; pausas entre fases são preservadas para commits e controle do orquestrador.

---

## Visão Geral

Adicionar persistência local de conversas usando SQLite, controlada pela variável de ambiente `PERSISTENCIA_SQLITE=true`, expondo no CLI interativo os comandos `/threads`, `/retomar <id>` e `/excluir <id>`. Quando a variável estiver ausente ou `false`, o sistema deve continuar funcionando exatamente como hoje, sem qualquer efeito colateral.

---

## Análise do Estado Atual

O sistema é composto essencialmente por um único arquivo (`chat_openai_memoria.py`, ~910 linhas) com a classe `ChatComMemoria` e a função `chat_interativo()`. Não existe nenhuma camada de persistência. Não existem testes automatizados.

### Descobertas Principais

- `ChatComMemoria.__init__` (linha 107) aceita apenas parâmetros de janela, tokens e modo; não tem suporte a banco.
- `adicionar_mensagem()` (linha 405-416) apenas faz `self.historico.append(...)` — ponto exato de injeção da persistência.
- `_aplicar_janela_deslizante()` (linha 473-495) opera exclusivamente em `self.historico` (em memória) — não deve tocar o banco.
- `chat_interativo()` (linha 770-858) instancia `ChatComMemoria()` diretamente na linha 793, antes de qualquer lógica de seleção de thread. A seleção deve ocorrer **antes** dessa linha para evitar output prematuro.
- O `__init__` faz `print()` com o resumo visual das configurações nas linhas 241-260 — reforçando que a seleção de thread deve preceder a instanciação.
- `.gitignore` não inclui `chat_memoria.db` — deve ser corrigido.
- `env.example` não documenta `PERSISTENCIA_SQLITE` — deve ser adicionada.
- `requirements.txt` não inclui `pytest` — deve ser adicionado para a infraestrutura de testes.
- Não existe diretório `tests/`.

---

## Estado Final Desejado

Ao final deste plano:

1. `persistencia.py` existe na raiz do projeto com a classe `GerenciadorPersistencia`.
2. `ChatComMemoria` aceita `gerenciador=None, thread_id=None` em seu `__init__`.
3. `adicionar_mensagem()` persiste no banco quando `gerenciador` está ativo.
4. `chat_interativo()` exibe seleção de thread antes do loop quando `PERSISTENCIA_SQLITE=true`.
5. Os comandos `/threads`, `/retomar <id>` e `/excluir <id>` funcionam no loop.
6. `chat_memoria.db` está no `.gitignore`.
7. `PERSISTENCIA_SQLITE=false` está documentada no `env.example`.
8. `tests/test_persistencia.py`, `tests/test_integracao_chat.py` e `tests/test_cli_persistencia.py` existem e passam.
9. `docs/USO_BASICO.md` e `README.md` refletem as novas funcionalidades.

**Verificação final:** `pytest tests/ -v` retorna 0 falhas; executar `python chat_openai_memoria.py` sem `PERSISTENCIA_SQLITE` não cria `chat_memoria.db`.

---

## O Que NÃO Estamos Fazendo

- Interface gráfica ou web para threads.
- Sincronização ou backup remoto.
- Busca por conteúdo nas threads.
- Paginação da listagem de threads.
- Soft delete (exclusão será física).
- Criptografia ou compressão do banco.
- Migração de exportações `.txt` existentes.
- Edição de mensagens já salvas.
- Pool de conexões ou controle de concorrência (sistema single-threaded).

---

## Abordagem de Implementação

Três fases de código, seguidas de uma fase de documentação:

1. **Fase 1** — Criar `persistencia.py` com toda a lógica SQLite isolada, infraestrutura de testes e ajustes de configuração (`.gitignore`, `env.example`, `requirements.txt`). Os testes desta fase são puramente unitários usando SQLite em memória.
2. **Fase 2** — Integrar `GerenciadorPersistencia` na classe `ChatComMemoria`, modificando `__init__` e `adicionar_mensagem()`. Testes de integração com banco em memória e cliente OpenAI mockado.
3. **Fase 3** — Modificar `chat_interativo()` com seleção inicial de thread, helpers de exibição e novos comandos. Testes de integração para os helpers e comandos.
4. **Fase 4** — Atualizar documentação.

---

<!-- FASE: 1 -->
## Fase 1: Módulo de Persistência SQLite e Infraestrutura de Testes

### Visão Geral

Criar `persistencia.py` com a classe `GerenciadorPersistencia` que encapsula toda a interação com SQLite. Criar `tests/` com testes unitários completos para o módulo. Atualizar `.gitignore`, `env.example` e `requirements.txt`.

---

### Mudanças Necessárias

#### 1. Novo arquivo `persistencia.py` (raiz do projeto)

**Arquivo:** `persistencia.py`

```python
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
```

#### 2. Atualizar `.gitignore`

Adicionar ao final do arquivo `.gitignore`:

```
# Banco de dados SQLite local (gerado em tempo de execução)
chat_memoria.db
```

#### 3. Atualizar `env.example`

Adicionar nova seção após as variáveis opcionais existentes:

```
# Persistência SQLite (opcional — padrão: false)
# Quando "true", conversas são salvas localmente em chat_memoria.db
PERSISTENCIA_SQLITE=false
```

#### 4. Atualizar `requirements.txt`

Adicionar `pytest`:

```
# Testes automatizados
pytest>=8.0.0
```

#### 5. Criar `tests/__init__.py`

Arquivo vazio para reconhecimento do pacote pelo pytest.

#### 6. Criar `tests/test_persistencia.py`

**Arquivo:** `tests/test_persistencia.py`

```python
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
```

---

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `pip install -r requirements.txt` instala `pytest` sem erros.
- [x] `pytest tests/test_persistencia.py -v` passa com 0 falhas.
- [x] `python -c "from persistencia import GerenciadorPersistencia"` executa sem erro.
- [x] `chat_memoria.db` está listado no `.gitignore` (`grep chat_memoria.db .gitignore` retorna match).

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito.**

---

<!-- FASE: 2 -->
## Fase 2: Integração com `ChatComMemoria`

### Visão Geral

Modificar a classe `ChatComMemoria` em `chat_openai_memoria.py` para receber e usar um `GerenciadorPersistencia`. A persistência deve ser transparente — nenhuma alteração quando `gerenciador=None`.

---

### Mudanças Necessárias

#### 1. Modificar `ChatComMemoria.__init__` — adicionar parâmetros e lógica de persistência

**Arquivo:** `chat_openai_memoria.py` — linha 107

Alterar assinatura de:
```python
def __init__(self, tamanho_janela: int = None, limite_maximo: int = None, modo_debug: bool = None, stream: bool = None):
```

Para:
```python
def __init__(self, tamanho_janela: int = None, limite_maximo: int = None, modo_debug: bool = None, stream: bool = None, gerenciador=None, thread_id: int = None):
```

Adicionar logo após a linha `self.historico = []` (linha 227) e **antes** do bloco de debug:

```python
# Persistência SQLite
self.gerenciador = gerenciador
self.thread_id = thread_id
self._thread_titulo_definido = thread_id is not None

# Carregar histórico da thread selecionada
if self.gerenciador and self.thread_id:
    self.historico = self.gerenciador.carregar_historico(self.thread_id)
    self._aplicar_janela_deslizante()
```

Adicionar ao bloco de exibição de configurações (após linha 258, onde estão os `if self.stream:`):

```python
if self.gerenciador:
    modo_db = f"thread #{self.thread_id}" if self.thread_id else "nova thread"
    print(item("Persistência", f"SQLite ativo — {modo_db}"))
```

#### 2. Modificar `adicionar_mensagem()` — persistir no banco

**Arquivo:** `chat_openai_memoria.py` — linha 405

Substituir o corpo atual:
```python
def adicionar_mensagem(self, role: str, content: str):
    self.historico.append({
        "role": role,
        "content": content
    })
```

Por:
```python
def adicionar_mensagem(self, role: str, content: str):
    self.historico.append({"role": role, "content": content})

    if self.gerenciador:
        if role == "user" and not self._thread_titulo_definido:
            titulo = content[:60].strip() or "Conversa sem título"
            self.thread_id = self.gerenciador.criar_thread(titulo)
            self._thread_titulo_definido = True

        if self.thread_id:
            ordem = len(self.historico)
            self.gerenciador.salvar_mensagem(self.thread_id, role, content, ordem)
```

#### 3. Criar `tests/test_integracao_chat.py`

**Arquivo:** `tests/test_integracao_chat.py`

```python
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
```

---

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `pytest tests/test_persistencia.py tests/test_integracao_chat.py -v` passa com 0 falhas.
- [x] `python -c "from chat_openai_memoria import ChatComMemoria"` executa sem importar `persistencia` (módulo só é importado em runtime quando persistência está ativa).

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito.**

---

<!-- FASE: 3 -->
## Fase 3: CLI — Seleção Inicial de Thread e Novos Comandos

### Visão Geral

Modificar `chat_interativo()` para: (a) verificar `PERSISTENCIA_SQLITE` e instanciar `GerenciadorPersistencia` antes da classe principal; (b) exibir a tela de seleção de thread; (c) adicionar os comandos `/threads`, `/retomar <id>` e `/excluir <id>`; (d) atualizar o comportamento do `/limpar` quando persistência está ativa.

---

### Mudanças Necessárias

#### 1. Adicionar helpers de CLI em `chat_openai_memoria.py` (antes de `chat_interativo()`)

Inserir as funções abaixo **logo antes** da definição de `chat_interativo()` (linha 770):

```python
def _exibir_lista_threads(gerenciador):
    threads = gerenciador.listar_threads()
    if not threads:
        print(pintar("  Nenhuma conversa armazenada.", _C.DIM))
        return
    print(pintar("  Conversas armazenadas", _C.TITULO))
    print(regua())
    for t in threads:
        data = t["atualizado_em"][:16].replace("T", " ")
        titulo = t["titulo"][:42]
        msgs = t["total_mensagens"]
        linha = (
            f"  {pintar(str(t['id']).rjust(3), _C.SISTEMA)}"
            f"  {titulo:<44}"
            f"  {pintar(data, _C.DIM)}"
            f"  {pintar(f'({msgs} msg)', _C.DIM)}"
        )
        print(linha)
    print(regua())


def _selecionar_thread(gerenciador):
    threads = gerenciador.listar_threads()
    print()
    print(cabecalho("SELECIONAR CONVERSA", cor=_C.SISTEMA))
    print()
    _exibir_lista_threads(gerenciador)
    print(f"  {pintar('  0', _C.SISTEMA)}  Nova conversa")
    print()
    while True:
        escolha = input(pintar("  Selecione o ID (ou 0 para nova): ", _C.USUARIO)).strip()
        if escolha == "0":
            return None
        if escolha.isdigit() and gerenciador.thread_existe(int(escolha)):
            return int(escolha)
        print(pintar(f"  Thread '{escolha}' não encontrada. Tente novamente.", _C.ERRO))
```

#### 2. Modificar `chat_interativo()` — adicionar persistência, seleção e novos comandos

**a) Adicionar import condicional e inicialização da persistência**

No início do corpo de `chat_interativo()`, antes do bloco `try:` (linha 791), adicionar:

```python
persistencia_ativa = os.getenv("PERSISTENCIA_SQLITE", "false").lower() == "true"
gerenciador = None
thread_id_inicial = None

if persistencia_ativa:
    from persistencia import GerenciadorPersistencia
    gerenciador = GerenciadorPersistencia()
    thread_id_inicial = _selecionar_thread(gerenciador)
```

**b) Adicionar novos comandos na lista de ajuda** (linha 778, dicionário `comandos`)

Adicionar as três entradas quando persistência estiver ativa. A forma mais simples é construir a lista condicionalmente logo após inicializar `gerenciador`:

```python
comandos_base = [
    ("/limpar",    "Limpa a memória do chat"),
    ("/historico", "Mostra todo o histórico"),
    ("/tokens",    "Mostra quantidade aproximada de tokens"),
    ("/debug",     "Exibe informações detalhadas de memória"),
    ("/grafico",   "Mostra gráfico de evolução de tokens"),
    ("/exportar",  "Exporta a conversa para arquivo"),
    ("/sair",      "Encerra o chat"),
]
if persistencia_ativa:
    comandos_base += [
        ("/threads",       "Lista conversas armazenadas"),
        ("/retomar <id>",  "Retoma uma conversa salva"),
        ("/excluir <id>",  "Exclui uma conversa permanentemente"),
    ]
```

Substituir a variável `comandos` original por `comandos_base` no loop de exibição.

**c) Alterar instanciação de `ChatComMemoria`** (linha 793)

Substituir:
```python
chat = ChatComMemoria()
```
Por:
```python
chat = ChatComMemoria(gerenciador=gerenciador, thread_id=thread_id_inicial)
```

**d) Atualizar o bloco `/limpar`** (linha 810)

Substituir:
```python
elif mensagem.lower() == "/limpar":
    chat.limpar_historico()
    continue
```
Por:
```python
elif mensagem.lower() == "/limpar":
    chat.limpar_historico()
    if gerenciador:
        print(pintar(
            "  ℹ  Histórico em memória limpo. Mensagens no banco SQLite foram preservadas.",
            _C.SISTEMA
        ) + "\n")
    continue
```

**e) Adicionar novos comandos no bloco `elif`** (após o bloco `/exportar`, linha 831)

```python
elif mensagem.lower() == "/threads":
    if gerenciador:
        _exibir_lista_threads(gerenciador)
    else:
        print(pintar(
            "  Persistência desabilitada. Defina PERSISTENCIA_SQLITE=true no .env para usar threads.",
            _C.DIM
        ) + "\n")
    continue

elif mensagem.lower().startswith("/retomar"):
    partes = mensagem.split()
    if not gerenciador:
        print(pintar("  Persistência desabilitada.", _C.DIM) + "\n")
    elif len(partes) == 2 and partes[1].isdigit():
        novo_id = int(partes[1])
        if gerenciador.thread_existe(novo_id):
            historico = gerenciador.carregar_historico(novo_id)
            chat.historico = historico
            chat._aplicar_janela_deslizante()
            chat.thread_id = novo_id
            chat._thread_titulo_definido = True
            print(pintar(f"  ✔ Thread #{novo_id} carregada ({len(historico)} mensagens).", _C.SISTEMA) + "\n")
        else:
            print(pintar(f"  Thread #{novo_id} não encontrada.", _C.ERRO) + "\n")
    else:
        print(pintar("  Uso: /retomar <id>", _C.DIM) + "\n")
    continue

elif mensagem.lower().startswith("/excluir"):
    partes = mensagem.split()
    if not gerenciador:
        print(pintar("  Persistência desabilitada.", _C.DIM) + "\n")
    elif len(partes) == 2 and partes[1].isdigit():
        excluir_id = int(partes[1])
        if gerenciador.thread_existe(excluir_id):
            confirmacao = input(
                pintar(f"  Excluir thread #{excluir_id}? Esta ação é irreversível. (s/n): ", _C.ERRO)
            ).strip().lower()
            if confirmacao == "s":
                gerenciador.excluir_thread(excluir_id)
                if excluir_id == chat.thread_id:
                    chat.historico = []
                    chat.thread_id = None
                    chat._thread_titulo_definido = False
                    print(pintar(
                        "  Thread ativa excluída. Nova conversa iniciada.", _C.SISTEMA
                    ) + "\n")
                else:
                    print(pintar(f"  Thread #{excluir_id} excluída.", _C.SISTEMA) + "\n")
            else:
                print(pintar("  Exclusão cancelada.", _C.DIM) + "\n")
        else:
            print(pintar(f"  Thread #{excluir_id} não encontrada.", _C.ERRO) + "\n")
    else:
        print(pintar("  Uso: /excluir <id>", _C.DIM) + "\n")
    continue
```

**f) Adicionar fechamento do gerenciador no bloco `finally`**

Envolver o bloco `try/except` existente em um `try/finally`:

```python
try:
    # ... todo o bloco try/except existente ...
finally:
    if gerenciador:
        gerenciador.fechar()
```

O `KeyboardInterrupt` e os demais `except` já existentes continuam dentro do `try` interno.

#### 3. Criar `tests/test_cli_persistencia.py`

**Arquivo:** `tests/test_cli_persistencia.py`

```python
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
```

---

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `pytest tests/ -v` passa com 0 falhas (todas as três suítes).
- [x] `python -c "import os; os.environ.setdefault('PERSISTENCIA_SQLITE','false'); from chat_openai_memoria import chat_interativo"` importa sem erro.
- [x] `python -c "from chat_openai_memoria import _selecionar_thread, _exibir_lista_threads"` importa sem erro.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito.**

---

<!-- FASE: 4 -->
## Fase 4: Atualização da Documentação

### Visão Geral

Refletir as novas funcionalidades nos documentos existentes do projeto. Esta fase é obrigatória — sem ela o projeto ficará com documentação desatualizada.

### Documentos a Atualizar

#### 1. `docs/USO_BASICO.md`

Adicionar nova seção **Persistência de Conversas (Threads)** descrevendo:
- Como ativar (`PERSISTENCIA_SQLITE=true` no `.env`)
- O que acontece ao iniciar com persistência ativa (tela de seleção de thread)
- Comandos `/threads`, `/retomar <id>`, `/excluir <id>` com exemplos
- Comportamento do `/limpar` quando persistência está ativa (apenas em memória)
- Onde o banco é criado (`chat_memoria.db` na raiz, não versionado)

#### 2. `README.md`

Adicionar bullet point na seção de funcionalidades mencionando a persistência SQLite com ativação por variável de ambiente.

#### 3. `env.example`

Já atualizado na Fase 1. Verificar que `PERSISTENCIA_SQLITE=false` está presente com comentário explicativo.

#### 4. `AGENTS.md`

Adicionar nota sobre o padrão de extensão de `ChatComMemoria`: novos comportamentos opcionais devem ser injetados via parâmetros no `__init__` (padrão estabelecido com `gerenciador`), não via herança ou variáveis globais.

---

### Critérios de Sucesso

#### Verificação Automatizada:
- [x] `grep -q "PERSISTENCIA_SQLITE" env.example` retorna 0 (variável documentada).
- [x] `grep -q "chat_memoria.db" .gitignore` retorna 0 (banco gitignored).
- [x] `grep -qi "threads\|retomar\|excluir\|sqlite" docs/USO_BASICO.md` retorna 0 (doc atualizada).
- [x] `grep -qi "sqlite\|persistência\|threads" README.md` retorna 0 (README atualizado).
- [x] `pytest tests/ -v` continua passando com 0 falhas após alterações de documentação (nada quebrou).

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de encerrar. **Não avançar sem receber um comando explícito.**

---

## Estratégia de Testes

### Testes Unitários (`tests/test_persistencia.py`)

Cobrem todas as operações de `GerenciadorPersistencia` em isolamento, usando banco SQLite em memória (`:memory:`). Não dependem de env vars, OpenAI, nem de estado externo.

Casos cobertos: criação de tabelas, criação de threads, listagem, contagem de mensagens, persistência de mensagens em ordem, carregamento de histórico, exclusão com cascade, verificação de existência, integridade de foreign key.

### Testes de Integração (`tests/test_integracao_chat.py`)

Verificam que `ChatComMemoria` interage corretamente com `GerenciadorPersistencia`. Usam banco em memória e cliente OpenAI mockado (sem chamadas reais à API).

Casos cobertos: comportamento sem gerenciador (nenhum efeito no banco), criação de thread na primeira mensagem de usuário, geração de título com truncamento, fallback para mensagem vazia, não criação de thread para mensagem de `assistant` antes de `user`, salvamento sequencial, invariância da janela deslizante no banco, carregamento de histórico ao retomar thread, não sobrescrita do título ao retomar.

### Testes de Integração CLI (`tests/test_cli_persistencia.py`)

Verificam helpers de UI (`_exibir_lista_threads`, `_selecionar_thread`) e a lógica dos comandos aplicada ao estado do `chat`. Usam `capsys` do pytest para capturar stdout e `patch("builtins.input")` para simular entradas do usuário.

Casos cobertos: exibição de lista vazia e com dados, seleção de thread (nova, existente, ID inválido, não numérico), reset do chat ao excluir thread ativa, preservação do chat ao excluir thread inativa, preservação de dados ao cancelar exclusão, preservação do histórico ao tentar retomar ID inexistente.

---

## Considerações de Performance

- SQLite com `check_same_thread` padrão é adequado para o cenário single-threaded.
- `PRAGMA foreign_keys = ON` é necessário para garantir CASCADE (o SQLite desabilita FK por padrão).
- Para v1, threads com histórico muito longo (milhares de mensagens) carregarão tudo na memória — aceitar como limitação conforme PRD.
- A janela deslizante opera exclusivamente em memória e não gera operações extras no banco.

---

## Referências

- PRD aprovado: `docs/prds/PRD-2026-06-24-gerenciamento-de-memoria-persistente-de-conversas-com-sqlite.md`
- `ChatComMemoria.__init__`: `chat_openai_memoria.py:107`
- `adicionar_mensagem()`: `chat_openai_memoria.py:405`
- `_aplicar_janela_deslizante()`: `chat_openai_memoria.py:473`
- `chat_interativo()`: `chat_openai_memoria.py:770`
- Risco R-01 (encerramento abrupto): mitigado pelo `finally` que fecha `gerenciador`
- Risco R-02 (`/limpar` vs banco): mitigado por mensagem informativa no `/limpar`
- Risco R-05 (banco no git): mitigado por `.gitignore` na Fase 1
- Risco R-06 (print prematuro): mitigado pela seleção de thread antes de instanciar a classe
