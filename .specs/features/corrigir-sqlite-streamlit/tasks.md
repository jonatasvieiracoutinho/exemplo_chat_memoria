# Conexão SQLite compatível com reruns do Streamlit Tasks

## Execution Protocol

Implementar estas tarefas com `tlc-spec-driven`, seguindo o ciclo por tarefa, testes derivados da especificação, gate verde e um commit Conventional Commits atômico por tarefa. A execução local não autoriza push, deploy ou alteração remota.

**Design**: `.specs/features/corrigir-sqlite-streamlit/design.md`
**Status**: Approved

## Test Coverage Matrix

> Gerada a partir de `AGENTS.md`, da suíte existente e da especificação. `AGENTS.md` exige `pytest` e cita cenários críticos de persistência; não há configuração de lint, formatter, CI ou cobertura no repositório. A cobertura forte se aplica aos critérios desta feature.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Gerenciador SQLite | integration | Todos os métodos públicos mantêm schema, dados, cascatas, ordenação e tokens com arquivo temporário, sem depender de conexão persistente. | `tests/test_persistencia.py` | `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_persistencia.py` |
| Integração de chat e CLI com persistência | integration | Os fluxos existentes de criar, retomar, excluir e gravar turnos continuam funcionais com banco temporário. | `tests/test_integracao_chat.py`, `tests/test_cli_persistencia.py`, `tests/test_app_streamlit_threads.py` | `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_integracao_chat.py tests/test_cli_persistencia.py tests/test_app_streamlit_threads.py` |
| Interface Streamlit | e2e (AppTest) | Renderização inicial e envio em rerun subsequente, sem `ProgrammingError`, com thread, mensagens e tokens persistidos. | `tests/test_app_streamlit_ui.py` | `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_app_streamlit_ui.py` |
| Demais código/configuração | none | Regressão completa da suíte. | `tests/` | `.\\.venv\\Scripts\\python.exe -m pytest -q` |

## Gate Check Commands

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após T1 | `.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_persistencia.py` |
| Focused | Após T2 a T5 | Executar o comando da linha correspondente da matriz de cobertura. |
| Full / Build | Ao concluir a fase | `.\\.venv\\Scripts\\python.exe -m pytest -q` |

## Execution Plan

### Phase 1: Persistência sem conexão compartilhada

```
T1
```

### Phase 2: Compatibilidade das integrações e regressão UI

```
T1 → T2 → T3 → T4 → T5
```

## Task Breakdown

### T1: Refatorar o gerenciador para conexão por operação

**What**: Substituir `self.conn` por um helper privado que abre, configura, inicializa e fecha uma conexão na thread chamadora; adaptar os testes de persistência para banco temporário e efeitos observáveis.
**Where**: `persistencia.py`
**Depends on**: None
**Reuses**: DDL, `_migrar_schema`, queries parametrizadas e retornos atuais de `GerenciadorPersistencia`.
**Requirement**: SQLSTRM-01, SQLSTRM-05, SQLSTRM-06, SQLSTRM-08

**Tools**:

- MCP: NONE
- Skill: `dev-sec-ops`

**Done when**:

- [ ] Cada método público usa uma conexão criada e fechada no próprio escopo da chamada.
- [ ] Cada conexão aplica `sqlite3.Row`, `PRAGMA foreign_keys = ON` e a inicialização/migração idempotente.
- [ ] Escritas confirmam a transação; leituras preservam os retornos atuais.
- [ ] `fechar()` mantém a assinatura e é seguro sem conexão persistente.
- [ ] `tests/test_persistencia.py` usa arquivo temporário em vez de `:memory:` e não acessa `db.conn` como detalhe do gerenciador.
- [ ] O SQL continua com parâmetros ligados, sem interpolar mensagens ou IDs [Norma 4.4.2.5.a, 4.4.13.1.b].
- [ ] Gate quick passa com ao menos os 34 testes atuais de persistência.

**Tests**: integration, em `tests/test_persistencia.py`
**Gate**: Quick
**Commit**: `fix(persistencia): abre conexao sqlite por operacao`

---

### T2: Migrar o fixture de integração do chat para arquivo temporário

**What**: Trocar o fixture SQLite em memória por banco em arquivo temporário, preservando os cenários existentes de histórico, janela deslizante e tokens.
**Where**: `tests/test_integracao_chat.py`
**Depends on**: T1
**Reuses**: Fixture `db`, mocks de OpenAI e `tmp_path` já usado no arquivo.
**Requirement**: SQLSTRM-03, SQLSTRM-04, SQLSTRM-05

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O fixture cria um arquivo SQLite único em `tmp_path` para cada teste.
- [ ] Os 20 testes existentes do arquivo continuam passando sem relaxar asserts.
- [ ] Gate focused passa.

**Tests**: integration, em `tests/test_integracao_chat.py`
**Gate**: Focused
**Commit**: `test(chat): usa banco temporario nas integracoes`

---

### T3: Migrar o fixture de persistência da CLI para arquivo temporário

**What**: Atualizar o fixture da CLI para usar um arquivo SQLite temporário sem alterar os cenários de listar, retomar e excluir threads.
**Where**: `tests/test_cli_persistencia.py`
**Depends on**: T2
**Reuses**: Fixture `db` e mocks de entrada/saída existentes.
**Requirement**: SQLSTRM-05, SQLSTRM-06, SQLSTRM-09, SQLSTRM-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O fixture cria um arquivo SQLite isolado por teste.
- [ ] Os 12 testes atuais de CLI continuam passando sem relaxar asserts.
- [ ] Gate focused passa.

**Tests**: integration, em `tests/test_cli_persistencia.py`
**Gate**: Focused
**Commit**: `test(cli): usa banco temporario na persistencia`

---

### T4: Migrar a integração de threads Streamlit para arquivo temporário

**What**: Adaptar os fixtures de threads do núcleo Streamlit para banco temporário, preservando criar, listar, retomar e excluir.
**Where**: `tests/test_app_streamlit_threads.py`
**Depends on**: T3
**Reuses**: Fixture `db`, `chat_com_db` e mocks de OpenAI existentes.
**Requirement**: SQLSTRM-05, SQLSTRM-06, SQLSTRM-09, SQLSTRM-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O fixture cria um arquivo SQLite isolado em `tmp_path`.
- [ ] Os 2 testes atuais de threads continuam passando sem relaxar asserts.
- [ ] Gate focused passa.

**Tests**: integration, em `tests/test_app_streamlit_threads.py`
**Gate**: Focused
**Commit**: `test(streamlit): usa banco temporario nas threads`

---

### T5: Cobrir a primeira conversa persistida após rerun

**What**: Adicionar um `AppTest` que habilita a persistência, executa renderização inicial e envio na renderização seguinte, e verifica dados persistidos com resposta OpenAI simulada.
**Where**: `tests/test_app_streamlit_ui.py`
**Depends on**: T4
**Reuses**: `AppTest.from_file`, `patch`, `tmp_path` e os elementos Streamlit já testados.
**Requirement**: SQLSTRM-02, SQLSTRM-03, SQLSTRM-04, SQLSTRM-07

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O teste usa ambiente e banco temporários, sem abrir `chat_memoria.db` do repositório.
- [ ] A resposta simulada contém `usage` completo e não chama a rede.
- [ ] Após duas renderizações, não há exceção `sqlite3.ProgrammingError`.
- [ ] O banco contém a thread, as mensagens de usuário e assistente na ordem esperada e um registro de turno com os três totais.
- [ ] O stdout é silenciado somente durante a execução do teste para isolar a regressão SQLite do problema de codificação documentado.
- [ ] Gate focused passa com ao menos os 10 testes atuais da UI mais a nova regressão.

**Tests**: e2e (AppTest), em `tests/test_app_streamlit_ui.py`
**Gate**: Focused, seguido de Full
**Commit**: `test(streamlit): cobre conversa sqlite apos rerun`

## Phase Execution Map

```
Phase 1: T1
Phase 2: T1 → T2 → T3 → T4 → T5
```

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1 | Gerenciador e seus testes de integração co-localizados | ✅ Granular |
| T2 | Um fixture e seus cenários de integração do chat | ✅ Granular |
| T3 | Um fixture e seus cenários de CLI | ✅ Granular |
| T4 | Um fixture e seus cenários de threads | ✅ Granular |
| T5 | Uma regressão AppTest da UI | ✅ Granular |

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| ---- | ---------------------- | ------------- | ------ |
| T1 | None | início da Phase 1 | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | T2 | T2 → T3 | ✅ Match |
| T4 | T3 | T3 → T4 | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Gerenciador SQLite | integration | integration | ✅ OK |
| T2 | Integração de chat | integration | integration | ✅ OK |
| T3 | Integração CLI | integration | integration | ✅ OK |
| T4 | Integração de threads Streamlit | integration | integration | ✅ OK |
| T5 | Interface Streamlit | e2e (AppTest) | e2e (AppTest) | ✅ OK |
