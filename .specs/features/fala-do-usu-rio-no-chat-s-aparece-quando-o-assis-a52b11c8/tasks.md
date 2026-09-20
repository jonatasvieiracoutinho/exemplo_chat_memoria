# Exibição imediata da mensagem do usuário no chat Streamlit — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven-ciclo` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Spec**: `.specs/features/fala-do-usu-rio-no-chat-s-aparece-quando-o-assis-a52b11c8/spec.md`
**Status**: Draft

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec. Guidelines found: none formais (sem `pyproject.toml`, `pytest.ini`, CI ou linter configurado); convenção inferida de `tests/test_app_streamlit_ui.py` e `requirements.txt` (pytest, streamlit). Strong defaults applied.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Wiring Streamlit (`app_streamlit.py::main`) | integration | Todos os ACs da P1: pintura imediata da fala, indicador, resposta ordenada, interações consecutivas sem duplicar e erro sanitizado mantendo a fala | `tests/test_app_streamlit_ui.py` | `python3 -m pytest tests/test_app_streamlit_ui.py` |

Os testes usam `streamlit.testing.v1.AppTest` com `pytest.importorskip("streamlit")` e mockam `app_streamlit_core.enviar_mensagem_seguro`/`construir_sessao_chat`, como a suíte atual. São testes de integração (fluxo ponta a ponta da página); não há camada de domínio nova para testes unitários adicionais.

## Gate Check Commands

> Generated from codebase.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tarefas que tocam só a UI Streamlit | `python3 -m pytest tests/test_app_streamlit_ui.py` |
| Full | Após tarefas que podem afetar o fluxo compartilhado | `python3 -m pytest tests/` |
| Build | Ao concluir a fase | `python3 -m pytest tests/` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

<!-- FASE: 1 -->
### Phase 1: Novo fluxo de envio na UI

Reescrita incremental e coesa do ramo de envio de `main()`, cada passo com seus testes de integração.

```
T1 → T2 → T3
```

---

## Task Breakdown

### T1: Pintar a fala do usuário imediatamente com indicador de processamento

**What**: No ramo `if entrada:` de `main()`, renderizar a mensagem do usuário via `st.chat_message("user")` antes de chamar a geração e envolver `enviar_mensagem_seguro` em um `st.spinner("Gerando resposta...")`, mantendo a fala visível durante o processamento.
**Where**: `app_streamlit.py`
**Depends on**: None
**Reuses**: `app_streamlit_core.enviar_mensagem_seguro`, `st.chat_message`, `st.spinner`
**Requirement**: CHAT-01, CHAT-02, CHAT-03

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] A fala do usuário é pintada pela camada de wiring antes da chamada de geração (independente do append do núcleo)
- [x] A chamada de geração ocorre dentro de um indicador de processamento (`st.spinner`)
- [x] Novo teste em `tests/test_app_streamlit_ui.py`: mock de `enviar_mensagem_seguro` que NÃO anexa ao histórico faz a bolha do usuário aparecer mesmo assim (discrimina o bug atual), e o indicador é acionado com mensagem amigável
- [x] Gate check passes: `python3 -m pytest tests/`
- [x] Test count: suíte atual (11 arquivos) continua passando e ao menos 1 teste novo passa (sem deleções silenciosas)

**Tests**: integration
**Gate**: full

---

### T2: Exibir a resposta após a fala do usuário sem duplicar o turno

**What**: Após o sucesso da geração, renderizar a resposta via `st.chat_message("assistant")` abaixo da fala do usuário na mesma execução e remover o `st.rerun()` do caminho de sucesso, garantindo que o histórico e a persistência não recebam o turno duas vezes em interações consecutivas.
**Where**: `app_streamlit.py`
**Depends on**: T1
**Reuses**: `app_streamlit_core.historico_para_ui`, `st.chat_message`
**Requirement**: CHAT-04, CHAT-05

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] No sucesso, a resposta é renderizada depois da fala do usuário, na ordem correta, sem sobrescrevê-la
- [ ] Não há `st.rerun()` no caminho de sucesso; o turno não é repintado nem reprocessado em execuções seguintes
- [ ] Novo teste em `tests/test_app_streamlit_ui.py`: dois envios consecutivos produzem exatamente 4 bolhas ordenadas sem conteúdo duplicado e `enviar_mensagem_seguro` é chamado uma vez por envio
- [ ] Gate check passes: `python3 -m pytest tests/`
- [ ] Test count: suíte atual continua passando e ao menos 1 teste novo passa (sem deleções silenciosas)

**Tests**: integration
**Gate**: full

---

### T3: Preservar o erro sanitizado mantendo a fala do usuário visível

**What**: No caminho de erro do novo fluxo, exibir `st.error(erro)` abaixo da fala do usuário já pintada, sem bolha de assistente, mantendo o comportamento sanitizado atual e a fala do usuário visível na falha.
**Where**: `app_streamlit.py`
**Depends on**: T2
**Reuses**: `app_streamlit_core.enviar_mensagem_seguro` (retorno `(None, msg)`), `st.error`
**Requirement**: CHAT-06

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Na falha, a fala do usuário continua visível e apenas a mensagem sanitizada é exibida via `st.error`
- [ ] Teste em `tests/test_app_streamlit_ui.py`: mock de erro que NÃO anexa ao histórico mostra a bolha do usuário e exatamente um `st.error` sanitizado (discrimina o bug atual)
- [ ] Gate check passes: `python3 -m pytest tests/`
- [ ] Test count: suíte atual continua passando e ao menos 1 teste novo passa (sem deleções silenciosas)

**Tests**: integration
**Gate**: full

**Commit**: `fix(streamlit): exibe erro sanitizado mantendo a fala do usuario visivel`

---

## Phase Execution Map

Visual representation of task ordering. Phases run in sequence, and tasks within a phase run in order:

```
Phase 1:  T1 ------→ T2 ------→ T3
```

Execution is strictly sequential - there is no intra-phase parallelism. A single agent works one task at a time, in order.
