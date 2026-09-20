# Continuidade de conversas persistidas na interface web Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, sub-agent delegation, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/corre-o-erro-sqlite-streamlit-232bce21/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none (sem `pyproject.toml`, `Makefile`, CI ou config de lint/coverage; `requirements.txt` lista `pytest>=8.0.0`; testes existentes usam `pytest`). Strong defaults applied.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Persistência / data-access (`persistencia.py`) | integration | Caminhos-chave + migração idempotente + caracteres especiais + uso a partir de outra thread sem erro; 1:1 às ACs de dados | `tests/test_persistencia.py` | `python3 -m pytest tests/test_persistencia.py -q` |
| Continuidade web / rerun (ponta a ponta) | integration | Renderização inicial + primeiro envio, retomar, excluir e persistência desativada; happy + edge + erro de conexão entre execuções | `tests/test_streamlit_rerun_persistencia.py` | `python3 -m pytest tests/test_streamlit_rerun_persistencia.py -q` |
| Terminal / CLI (regressão) | integration | Suíte atual permanece verde (modo `:memory:` e arquivo) | `tests/test_cli_persistencia.py`, `tests/test_integracao_chat.py` | `python3 -m pytest -q` |
| Helpers UI-agnósticos (`app_streamlit_core.py`) | none | Sem mudança de código nesta feature (build gate only) | - | build gate only |

## Gate Check Commands

> Generated from codebase - confirm before Execute.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tasks com testes unitários/data-access apenas | `python3 -m pytest tests/test_persistencia.py -q` |
| Full | Após tasks com testes de integração de rerun | `python3 -m pytest tests/test_persistencia.py tests/test_streamlit_rerun_persistencia.py -q` |
| Build | Após conclusão de fase / regressão completa | `python3 -m pytest -q` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

<!-- FASE: 1 -->
### Phase 1: Correção do núcleo de persistência

Refatora o lifecycle de conexão na camada de dados.

```
T1
```

<!-- FASE: 2 -->
### Phase 2: Verificação de continuidade na interface web

Testes de integração que provam os fluxos web após a correção. Reusam o helper de simulação de rerun.

```
T2 → T3
T2 → T4
```

---

## Task Breakdown

### T1: Conexão por operação em `GerenciadorPersistencia`

**What**: Substituir a conexão de vida longa por conexão curta por operação (modo arquivo), mantendo uma conexão única no modo `:memory:`; preservar assinaturas públicas.
**Where**: `persistencia.py`
**Depends on**: None
**Reuses**: `persistencia.py` (schema `threads`/`mensagens`/`turnos`, `PRAGMA foreign_keys=ON`)
**Requirement**: SQLR-01, SQLR-07, SQLR-09

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `_conexao` (context manager) abre conexão nova por operação no modo arquivo, aplica `row_factory` e `PRAGMA foreign_keys=ON`, faz commit no sucesso e fecha no `finally`
- [x] Modo `:memory:`/`mode=memory` mantém conexão única compartilhada; `fechar()` fecha em memória e é no-op no modo arquivo
- [x] Todos os métodos públicos usam `_conexao`; `salvar_turno` mantém SELECT MAX(ordem)+INSERT na mesma conexão; assinaturas inalteradas
- [x] `tests/test_persistencia.py`: teste de migração em modo arquivo lê via conexão nova (sem `.conn`); novo teste de caracteres especiais (aspas/apóstrofos como dado literal, sem afetar outra conversa); novo teste de uso a partir de outra thread sem `ProgrammingError`
- [x] Gate check passes: `python3 -m pytest -q`
- [x] Test count: suíte completa passa (nenhum teste silenciosamente removido)

**Tests**: integration
**Gate**: build

**Commit**: `fix(sqlite): conexão por operação para compatibilidade com reruns do Streamlit`

---

### T2: Cenário de rerun — renderização inicial + primeiro envio

**What**: Criar o módulo de integração com helper de simulação de rerun (gerenciador criado em uma thread; operações em outra) e o cenário ponta a ponta de renderização inicial seguida do primeiro envio, com OpenAI mockado e banco temporário isolado.
**Where**: `tests/test_streamlit_rerun_persistencia.py`
**Depends on**: T1
**Reuses**: `app_streamlit_core.py`, `chat_openai_memoria.ChatComMemoria`, `persistencia.GerenciadorPersistencia`
**Requirement**: SQLR-02, SQLR-03, SQLR-04, SQLR-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Helper simula rerun executando operações de persistência em thread distinta da que criou o gerenciador
- [x] Cenário: após renderização inicial e primeiro envio, não ocorre erro de conexão entre execuções; lista de conversas e histórico ficam disponíveis
- [x] Asserção: armazenamento com exatamente uma conversa ativa, duas mensagens ordenadas (pessoa depois assistente) e um registro de uso com entrada/saída/total do provedor mockado
- [x] Gate check passes: `python3 -m pytest tests/test_persistencia.py tests/test_streamlit_rerun_persistencia.py -q`
- [x] Test count: novos testes de integração passam (nenhum teste silenciosamente removido)

**Tests**: integration
**Gate**: full

---

### T3: Cenário de rerun — retomar e excluir conversa

**What**: Adicionar ao módulo de integração os cenários de retomar (histórico ordenado) e excluir (some da lista e não é retomável) após nova renderização, reusando o helper de rerun.
**Where**: `tests/test_streamlit_rerun_persistencia.py`
**Depends on**: T2
**Reuses**: helper de simulação de rerun do T2; `app_streamlit_core.listar_threads`/`retomar_thread`/`excluir_thread`
**Requirement**: SQLR-05, SQLR-06

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Cenário: conversa salva antes do rerun é retomada com histórico na ordem original
- [x] Cenário: conversa excluída deixa de aparecer na lista e não pode ser retomada após nova renderização
- [x] Gate check passes: `python3 -m pytest tests/test_persistencia.py tests/test_streamlit_rerun_persistencia.py -q`
- [x] Test count: novos testes de integração passam (nenhum teste silenciosamente removido)

**Tests**: integration
**Gate**: full

---

### T4: Cenário de rerun — persistência desativada sem armazenamento

**What**: Adicionar ao módulo de integração o cenário em que, com persistência desativada, o fluxo da interface web não cria nem acessa arquivo de armazenamento local mesmo após renderização e envio, reusando o helper de rerun.
**Where**: `tests/test_streamlit_rerun_persistencia.py`
**Depends on**: T2
**Reuses**: helper de simulação de rerun do T2; `app_streamlit_core.persistencia_ativa`/`construir_sessao_chat`
**Requirement**: SQLR-08

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Cenário: com `PERSISTENCIA_SQLITE` desativada, renderização inicial e envio não criam gerenciador nem arquivo de banco em diretório temporário isolado
- [x] Asserção: nenhum arquivo de armazenamento local é criado ou acessado no fluxo
- [x] Gate check passes: `python3 -m pytest -q`
- [x] Test count: suíte completa passa (nenhum teste silenciosamente removido)

**Tests**: integration
**Gate**: build

---

## Phase Execution Map

Visual representation of task ordering. Phases run in sequence, and tasks within a phase run in order:

```
Phase 1 → Phase 2

Phase 1:  T1
Phase 2:  T1 → T2 → T3
          T2 → T4
```

Execution is strictly sequential - there is no intra-phase parallelism. A single agent (or batch worker) works one task at a time, in order.

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| ---- | ---------------------- | ------------- | ------ |
| T1 | None | (nenhuma) | ✅ Match |
| T2 | T1 | T1 → T2 (cross-phase, backward) | ✅ Match |
| T3 | T2 | T2 → T3 | ✅ Match |
| T4 | T2 | T2 → T4 | ✅ Match |

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Persistência / data-access (`persistencia.py`) | integration | integration | ✅ OK |
| T2 | Continuidade web / rerun | integration | integration | ✅ OK |
| T3 | Continuidade web / rerun | integration | integration | ✅ OK |
| T4 | Continuidade web / rerun | integration | integration | ✅ OK |
