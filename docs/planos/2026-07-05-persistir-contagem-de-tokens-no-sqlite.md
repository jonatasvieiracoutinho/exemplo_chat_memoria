# Plano de Implementação: Persistir contagem de tokens no SQLite durante interações

> **Modo**: Sem testes manuais (orquestração automática). Toda validação é automatizada; pausas entre fases são preservadas para commits e controle do orquestrador.

## Visão Geral

Passar a **registrar e persistir na base SQLite existente** (`chat_memoria.db`) a
contagem **real** de tokens consumidos em cada turno de conversa, capturada do
campo `usage` da resposta da API OpenAI (`prompt_tokens`, `completion_tokens`,
`total_tokens`). Hoje esse dado é descartado. A persistência ocorrerá dentro do
mesmo fluxo que grava as interações, através de uma **nova entidade de turno**
relacionada a `threads`, com evolução idempotente do schema e tolerância total à
ausência de `usage` (Ollama/LM Studio/Azure, streaming sem `include_usage`).

Base de verdade: o PRD aprovado em
`docs/prds/PRD-2026-07-05-persistir-contagem-de-tokens-no-sqlite-durante-interacoes.md`.

## Análise do Estado Atual

A aplicação é um chat CLI Python integrado à OpenAI, com memória de conversa e
persistência SQLite. A investigação do código confirmou o que o PRD descreve:

### Descobertas Principais:

- **Camada de persistência** (`persistencia.py:7-84`): classe
  `GerenciadorPersistencia` com tabelas `threads` (`persistencia.py:17-22`) e
  `mensagens` (`persistencia.py:23-30`, FK `ON DELETE CASCADE`). O schema é criado
  em `_criar_tabelas()` via `CREATE TABLE IF NOT EXISTS` (`persistencia.py:15-32`),
  que **não** altera bancos já existentes — daí a necessidade de migração
  idempotente. `PRAGMA foreign_keys = ON` é ativado na conexão
  (`persistencia.py:12`).
- **Gravação de mensagens** (`persistencia.py:43-53`): `salvar_mensagem(thread_id,
  role, content, ordem)` insere uma linha e atualiza `atualizado_em`. Assinatura
  coberta por testes — **deve permanecer retrocompatível** (RF5/CA8).
- **Fluxo de gravação** (`chat_openai_memoria.py:424-442`): `adicionar_mensagem`
  cria a thread na primeira mensagem `user` (`:435-438`) e grava cada mensagem via
  `salvar_mensagem` (`:440-442`). É chamado **duas vezes por turno**: `user`
  (`chat_openai_memoria.py:550`, antes da API) e `assistant`
  (`chat_openai_memoria.py:588`, depois da API).
- **Fonte dos tokens reais** (`chat_openai_memoria.py:535-617`): em
  `enviar_mensagem`, o ramo **não-streaming** (`:582-585`) tem acesso a
  `resposta.usage`, que hoje é descartado — só `resposta.choices[0].message.content`
  é usado. O ramo **streaming** (`:571-581`) itera chunks e não coleta `usage`.
- **Estimativa preservada**: `contar_tokens_aproximado()`
  (`chat_openai_memoria.py:653-659`) continua alimentando sliding window
  (`:591`), alertas (`:598`) e comandos `/tokens`, `/debug`, `/grafico`. **Não é
  substituída** pelos tokens reais (fora de escopo).
- **Padrão de extensão** (`AGENTS.md:218-220`): comportamentos opcionais são
  injetados via `__init__` (ex.: `gerenciador`). Quando `gerenciador is None` a
  classe funciona como antes. A persistência de tokens deve respeitar esse padrão.
- **Testes** (`tests/`): 44 testes passando (`pytest -q` → `44 passed`). Fixtures
  usam `GerenciadorPersistencia(":memory:")` e `OpenAI` mockado com `MagicMock`.
  Arquivos: `test_persistencia.py` (camada de dados), `test_integracao_chat.py`
  (fluxo `ChatComMemoria` + DB), `test_cli_persistencia.py` (comandos CLI). Não há
  `pytest.ini`/`conftest.py`; os testes rodam a partir da raiz do projeto.

## Estado Final Desejado

- Existe uma tabela `turnos` no schema SQLite, relacionada a `threads`, com colunas
  `prompt_tokens`, `completion_tokens`, `total_tokens` que aceitam `NULL`.
- Bancos `chat_memoria.db` pré-existentes recebem a nova tabela automaticamente na
  abertura, sem perda de dados e sem erro (migração idempotente).
- A cada turno de conversa em `enviar_mensagem`, os tokens reais extraídos de
  `usage` são persistidos como um registro de turno vinculado à thread. Quando
  `usage` está ausente/incompleto, o turno é gravado com `NULL` (ou não bloqueia o
  fluxo), e o registro das mensagens ocorre normalmente.
- É possível consultar os tokens por turno e por thread através de métodos do
  `GerenciadorPersistencia`.
- Todos os 44 testes existentes continuam passando + novos testes automatizados
  (unitários e de integração) cobrindo schema, migração, captura, propagação,
  fallback defensivo e durabilidade.

**Como verificar:** suíte `pytest` verde (existentes + novos), incluindo teste de
migração sobre um arquivo `.db` gerado com o schema antigo e teste ponta a ponta
com cliente OpenAI mockado retornando `usage`.

## O Que NÃO Estamos Fazendo

- **Sem migração de dados históricos**: mensagens/threads antigas não recebem
  tokens retroativos. Colunas aceitam `NULL`.
- **Sem remover/alterar `contar_tokens_aproximado()`**: a estimativa permanece para
  sliding window, alertas e comandos visuais.
- **Sem** cobrança, cálculo de custo monetário, dashboards ou relatórios.
- **Sem** novos comandos de UI/CLI para exibir tokens reais (`/tokens` continua
  mostrando a estimativa; exibição de tokens reais é demanda futura).
- **Sem** alterar a lógica de negócio da conversa, o modelo de memória, a ordem de
  gravação das mensagens ou a criação de threads.
- **Sem** migrar para outra tecnologia de armazenamento — usa o SQLite existente.

## Abordagem de Implementação

Seguindo o padrão "mudanças de banco de dados" (schema → acesso a dados → lógica de
negócio) e o padrão de extensão do projeto:

1. **Modelo por turno** (não por mensagem individual): é o modelo apontado pelo PRD
   (seção 8, R3) como o mais aderente ao requisito "entrada e saída a cada turno" e
   que evita `UPDATE` posterior — a linha `user` é gravada antes de `usage` existir.
   Uma nova tabela `turnos` referencia `threads(id)` com `ON DELETE CASCADE`,
   mantendo `salvar_mensagem` e o schema de `mensagens` **intactos**
   (retrocompatibilidade, CA8).
2. **Migração via `CREATE TABLE IF NOT EXISTS`** para a nova tabela — inerentemente
   idempotente e seguro para bancos existentes (não recria, não apaga). Uma rotina
   `_migrar_schema()` explícita centraliza a evolução e é chamada na inicialização.
3. **Captura de `usage`** em `enviar_mensagem` via helper defensivo
   `_extrair_uso_tokens(...)` que retorna `(prompt, completion, total)` com `None`
   quando ausente/incompleto. No modo streaming, habilita
   `stream_options={"include_usage": True}` para capturar `usage` no chunk final
   quando o provedor suportar; se não vier, grava `NULL` (RF7).
4. **Persistência no mesmo fluxo**: após gravar a mensagem `assistant`, o turno é
   registrado via `self.gerenciador.salvar_turno(...)`, sem fluxo paralelo
   desacoplado (RF2). Só ocorre quando há `gerenciador` e `thread_id` — respeitando
   o comportamento "sem persistência" quando `gerenciador is None`.

---

<!-- FASE: 1 -->
## Fase 1: Evolução do schema e camada de persistência de turnos

### Visão Geral

Introduzir a entidade `turnos` no SQLite com migração idempotente e os métodos de
escrita/consulta no `GerenciadorPersistencia`, sem tocar em `mensagens` nem alterar
a assinatura de `salvar_mensagem`.

### Mudanças Necessárias:

#### 1. Schema e migração idempotente
**Arquivo**: `persistencia.py`
**Mudanças**: adicionar a tabela `turnos` (colunas de tokens `NULL`) e uma rotina de
migração idempotente chamada na inicialização, logo após `_criar_tabelas()`.

```python
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
    self._migrar_schema()

def _migrar_schema(self):
    """Evolução idempotente do schema: cria a entidade de turno em bancos
    novos e pré-existentes sem recriar nem apagar dados. Colunas de tokens
    aceitam NULL (registros antigos e cenários sem `usage`)."""
    self.conn.execute("""
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
    self.conn.commit()
```

#### 2. Escrita de turno
**Arquivo**: `persistencia.py`
**Mudanças**: novo método `salvar_turno`, tolerante a `None`.

```python
def salvar_turno(self, thread_id: int, prompt_tokens=None,
                 completion_tokens=None, total_tokens=None) -> int:
    """Registra um turno de conversa com a contagem real de tokens.
    Valores de tokens podem ser None (usage ausente/incompleto)."""
    agora = datetime.now().isoformat()
    cursor = self.conn.execute(
        "SELECT COALESCE(MAX(ordem), 0) + 1 AS proxima FROM turnos WHERE thread_id = ?",
        (thread_id,),
    )
    ordem = cursor.fetchone()["proxima"]
    cursor = self.conn.execute(
        """INSERT INTO turnos
               (thread_id, ordem, prompt_tokens, completion_tokens, total_tokens, criado_em)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (thread_id, ordem, prompt_tokens, completion_tokens, total_tokens, agora),
    )
    self.conn.execute(
        "UPDATE threads SET atualizado_em = ? WHERE id = ?", (agora, thread_id)
    )
    self.conn.commit()
    return cursor.lastrowid
```

#### 3. Consulta posterior (RF4/CA3)
**Arquivo**: `persistencia.py`
**Mudanças**: métodos de leitura por turno e agregado por thread.

```python
def carregar_turnos(self, thread_id: int) -> list:
    """Lista os turnos de uma thread com tokens por turno, em ordem."""
    cursor = self.conn.execute(
        """SELECT ordem, prompt_tokens, completion_tokens, total_tokens, criado_em
             FROM turnos WHERE thread_id = ? ORDER BY ordem ASC""",
        (thread_id,),
    )
    return [dict(row) for row in cursor.fetchall()]

def total_tokens_thread(self, thread_id: int) -> dict:
    """Soma os tokens de todos os turnos de uma thread (ignora NULL)."""
    cursor = self.conn.execute(
        """SELECT COALESCE(SUM(prompt_tokens), 0)     AS prompt_tokens,
                  COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                  COALESCE(SUM(total_tokens), 0)      AS total_tokens
             FROM turnos WHERE thread_id = ?""",
        (thread_id,),
    )
    return dict(cursor.fetchone())
```

### Critérios de Sucesso:

#### Verificação Automatizada:
- [ ] Novos testes unitários da camada de persistência passam:
      `python -m pytest tests/test_persistencia.py -q`
- [ ] Suíte completa continua verde (nenhuma regressão em `mensagens`/`threads`):
      `python -m pytest -q`
- [ ] Import sem erro: `python -c "from persistencia import GerenciadorPersistencia; print('OK')"`

**Testes a criar nesta fase** (em `tests/test_persistencia.py`):
- **Unitários** — tabela `turnos` criada (checar `sqlite_master`); `salvar_turno`
  retorna id inteiro > 0; `salvar_turno` com os três tokens persiste os valores
  corretos (via `carregar_turnos`); `salvar_turno` com `None` grava `NULL` sem
  erro; `ordem` é sequencial por thread; `carregar_turnos` retorna lista vazia para
  thread sem turnos e em ordem crescente quando há vários; `total_tokens_thread`
  soma corretamente e ignora `NULL`; cascade `ON DELETE` remove turnos ao excluir a
  thread; `salvar_mensagem` mantém assinatura/comportamento (testes existentes).
- **Integração (banco)** — **migração idempotente sobre banco pré-existente**:
  criar um arquivo `.db` temporário (via `tmp_path`) contendo apenas o schema
  antigo (`threads` + `mensagens`, sem `turnos`) com dados; abrir com
  `GerenciadorPersistencia(<arquivo>)`; verificar que a tabela `turnos` passou a
  existir, que os dados antigos permanecem intactos (CA6) e que abrir **duas vezes**
  o mesmo banco não gera erro nem duplica estrutura (idempotência, RF6/R4).

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito. Esta pausa só pode ser omitida se o usuário ou orquestrador tiver solicitado explicitamente execução contínua sem pausas (ex.: "execute todas as fases sem parar", "modo contínuo", "sem pausas"). Ausência de instrução contrária NÃO é permissão para avançar.**

---

<!-- FASE: 2 -->
## Fase 2: Captura de tokens reais e persistência no fluxo do turno

### Visão Geral

Capturar `usage` em `enviar_mensagem` (não-streaming e streaming com
`include_usage`), de forma defensiva, e persistir o turno via `salvar_turno` dentro
do mesmo fluxo de gravação — sem alterar a ordem de gravação das mensagens nem o
comportamento quando `gerenciador is None`.

### Mudanças Necessárias:

#### 1. Helper defensivo de extração de `usage`
**Arquivo**: `chat_openai_memoria.py`
**Mudanças**: método utilitário que normaliza `usage` em `(prompt, completion,
total)`, retornando `None` em qualquer campo ausente/incompleto (RF7/R2).

```python
def _extrair_uso_tokens(self, usage):
    """Extrai (prompt, completion, total) de um objeto `usage` da API.
    Retorna (None, None, None) quando `usage` é ausente/incompleto —
    ex.: base_url alternativa (Ollama/LM Studio/Azure) ou streaming sem
    include_usage. Nunca lança exceção."""
    if usage is None:
        return None, None, None
    def _get(campo):
        valor = getattr(usage, campo, None)
        return valor if isinstance(valor, int) else None
    return _get("prompt_tokens"), _get("completion_tokens"), _get("total_tokens")
```

#### 2. Captura no ramo não-streaming e no streaming
**Arquivo**: `chat_openai_memoria.py` (dentro de `enviar_mensagem`, `:571-585`)
**Mudanças**: coletar `usage` nos dois ramos; no streaming, habilitar
`stream_options={"include_usage": True}` e ler `usage` do chunk final quando
presente (o chunk de usage vem sem `choices`, já tratado pelo `continue` existente).

```python
usage_bruto = None
if self.stream:
    parametros["stream"] = True
    parametros["stream_options"] = {"include_usage": True}
    resposta_texto = ""
    for chunk in self.client.chat.completions.create(**parametros):
        # O chunk final de usage chega sem choices; capturamos quando presente.
        if getattr(chunk, "usage", None) is not None:
            usage_bruto = chunk.usage
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            print(delta, end="", flush=True)
            resposta_texto += delta
else:
    resposta = self.client.chat.completions.create(**parametros)
    resposta_texto = resposta.choices[0].message.content
    usage_bruto = getattr(resposta, "usage", None)
```

#### 3. Persistência do turno no mesmo fluxo
**Arquivo**: `chat_openai_memoria.py` (dentro de `enviar_mensagem`, após
`self.adicionar_mensagem("assistant", resposta_texto)` em `:588`)
**Mudanças**: registrar o turno com os tokens reais. A gravação nunca pode
interromper o fluxo da conversa (RF7/CA7).

```python
self.adicionar_mensagem("assistant", resposta_texto)

# Persiste os tokens reais do turno no mesmo fluxo de gravação (RF2/RF3).
# Tolerante a ausência de usage e a falhas de escrita (RF7/CA7).
if self.gerenciador and self.thread_id:
    prompt_tokens, completion_tokens, total_tokens = self._extrair_uso_tokens(usage_bruto)
    try:
        self.gerenciador.salvar_turno(
            self.thread_id, prompt_tokens, completion_tokens, total_tokens
        )
    except Exception as e:
        if self.modo_debug:
            self._registrar_log(f"\n[AVISO] Falha ao persistir tokens do turno: {e}\n")
```

> Observação: a estimativa `contar_tokens_aproximado()` e os alertas visuais
> permanecem exatamente como estão (`:591-609`). Os tokens reais são um dado
> adicional, gravado em paralelo à lógica existente, não um substituto.

### Critérios de Sucesso:

#### Verificação Automatizada:
- [ ] Novos testes de integração/unitários passam:
      `python -m pytest tests/test_integracao_chat.py -q`
- [ ] Suíte completa verde (sem regressão nos 44 testes existentes):
      `python -m pytest -q`
- [ ] Import sem erro: `python -c "from chat_openai_memoria import ChatComMemoria; print('OK')"`

**Testes a criar nesta fase** (em `tests/test_integracao_chat.py`, com `OpenAI`
mockado):
- **Unitários** — `_extrair_uso_tokens` com `usage` completo retorna a tupla
  correta; com `usage=None` retorna `(None, None, None)`; com objeto sem os campos /
  campos não-inteiros retorna `None` nos ausentes (defensivo).
- **Integração (fluxo ponta a ponta com mock)** —
  - Não-streaming: mock de `chat.completions.create` retorna objeto com
    `choices[0].message.content` e `usage` (`prompt_tokens`, `completion_tokens`,
    `total_tokens`); após `enviar_mensagem`, `carregar_turnos(thread_id)` contém um
    turno com os valores esperados (**CA1/CA2**) e o histórico de `mensagens`
    continua gravado como hoje (**CA4**).
  - Streaming: `chat.stream=True`; mock retorna iterável de chunks de conteúdo +
    chunk final com `usage` e `choices=[]`; verificar que o turno é persistido com
    os tokens do chunk final e `include_usage` foi enviado nos parâmetros.
  - Streaming sem usage / base_url alternativa: mock sem chunk de `usage` (ou
    `usage=None`) → turno gravado com `NULL` e nenhuma exceção (**CA7**); mensagens
    gravadas normalmente.
  - Sem `gerenciador`: `enviar_mensagem` não tenta persistir turno e não falha
    (comportamento inalterado).
  - Falha em `salvar_turno`: gerenciador que lança exceção em `salvar_turno` não
    interrompe `enviar_mensagem` (resposta retornada normalmente) (**CA7**).
  - **Durabilidade (CA5/RF8)**: usando arquivo `.db` em `tmp_path`, gravar um turno,
    fechar o gerenciador, reabrir com nova instância e confirmar via
    `carregar_turnos`/`total_tokens_thread` que os tokens persistem.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito. Esta pausa só pode ser omitida se o usuário ou orquestrador tiver solicitado explicitamente execução contínua sem pausas (ex.: "execute todas as fases sem parar", "modo contínuo", "sem pausas"). Ausência de instrução contrária NÃO é permissão para avançar.**

---

## Estratégia de Testes

### Testes Unitários:
- `salvar_turno`: retorno de id, gravação dos três tokens, tolerância a `None`,
  `ordem` sequencial por thread.
- `carregar_turnos` / `total_tokens_thread`: ordenação, agregação, tratamento de
  `NULL` e thread sem turnos.
- `_migrar_schema`: criação idempotente da tabela `turnos`.
- `_extrair_uso_tokens`: normalização defensiva de `usage` (completo, ausente,
  incompleto, tipos inválidos).

### Testes de Integração:
- **Banco**: migração idempotente sobre `.db` pré-existente com schema antigo +
  dados; preservação dos dados; abertura repetida sem erro; cascade `ON DELETE`.
- **Fluxo ponta a ponta (mock OpenAI)**: `enviar_mensagem` persistindo turno nos
  modos não-streaming e streaming (`include_usage`); fallback `NULL` sem `usage`;
  ausência de `gerenciador`; falha isolada de `salvar_turno` não quebra o fluxo.
- **Durabilidade**: reabertura de arquivo `.db` confirmando persistência dos tokens.

---

<!-- FASE: 3 -->
## Fase 3: Atualização da Documentação

**Esta fase é obrigatória e deve ser executada após as fases anteriores terem sido
concluídas com sucesso.**

Atualizar a documentação do projeto para refletir o estado real pós-implementação.
Este projeto **não possui** `RAIO_X_PROJETO.md`/`RAIO_X_FRONTEND.md` nem manuais MCP;
os documentos efetivamente impactados são:

- `.notebook/persistencia-sqlite.md` — descrever a nova entidade `turnos`, os
  métodos `salvar_turno`, `carregar_turnos`, `total_tokens_thread`, a migração
  idempotente e o comportamento defensivo de `usage`.
- `.notebook/INDEX.md` — atualizar o índice/estado da persistência SQLite.
- `docs/USO_BASICO.md` — documentar a persistência automática de tokens reais por
  turno quando a persistência SQLite está ativa, e como consultar via
  `GerenciadorPersistencia`.
- `AGENTS.md` — registrar o novo schema (`turnos`), o padrão de captura de `usage`
  em `enviar_mensagem` e o gotcha de streaming (`stream_options.include_usage`);
  atualizar o exemplo da seção "Persistência SQLite" se pertinente.
- `README.md` — mencionar, se cabível, a persistência da contagem real de tokens.
- Demais documentos de `docs/` diretamente impactados (ex.: `CONCEITOS.md` /
  `GERENCIAMENTO_MEMORIA.md`) apenas se citarem contagem de tokens e ficarem
  desatualizados.

### Critérios de Sucesso:

#### Verificação Automatizada:
- [ ] Suíte de testes permanece verde após ajustes de documentação:
      `python -m pytest -q`
- [ ] Os arquivos de documentação citados existem e foram atualizados (sem
      referência à feature como "planejada"/"pendente"):
      `grep -riE "planejad|pendente|TODO" .notebook/persistencia-sqlite.md docs/USO_BASICO.md`
      não retorna menções à contagem de tokens como não implementada.
- [ ] A tabela `turnos` e os novos métodos aparecem documentados:
      `grep -rl "turnos\|salvar_turno" .notebook AGENTS.md docs` retorna os arquivos atualizados.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de encerrar. **Não avançar sem receber um comando explícito. Esta pausa só pode ser omitida se o usuário ou orquestrador tiver solicitado explicitamente execução contínua sem pausas (ex.: "execute todas as fases sem parar", "modo contínuo", "sem pausas"). Ausência de instrução contrária NÃO é permissão para avançar.**

---

## Considerações de Performance

- Impacto desprezível: uma inserção adicional por turno (`salvar_turno`) na mesma
  conexão SQLite já aberta, e uma consulta `MAX(ordem)` barata por turno.
- A migração roda uma única vez por abertura de conexão (`CREATE TABLE IF NOT
  EXISTS`), custo irrelevante.
- Nenhuma chamada extra à API OpenAI: `usage` já vem na resposta; no streaming,
  `include_usage` apenas anexa um chunk final de metadados.
- Projeto educacional (`AGENTS.md:264-271`): prioriza clareza e simplicidade —
  o modelo por turno mantém `mensagens`/`salvar_mensagem` inalterados.

## Referências

- Especificação original: `docs/prds/PRD-2026-07-05-persistir-contagem-de-tokens-no-sqlite-durante-interacoes.md`
- Plano anterior de persistência: `docs/planos/2026-06-24-persistencia-sqlite-threads.md`
- Camada de persistência: `persistencia.py:7-84`
- Fluxo de gravação e envio: `chat_openai_memoria.py:424-442`, `chat_openai_memoria.py:535-617`
- Estimativa preservada: `chat_openai_memoria.py:653-659`
- Padrão de extensão via `__init__`: `AGENTS.md:218-220`
- Testes existentes: `tests/test_persistencia.py`, `tests/test_integracao_chat.py`, `tests/test_cli_persistencia.py`
