# Front-end Streamlit com Scripts de Inicialização Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven-ciclo` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Design**: `.specs/features/adicionar-tela-streamlit-659323ea/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Generated from codebase, project guidelines, and spec - confirm before Execute. Guidelines found: none - strong defaults applied (repo has no coverage thresholds, no linter config; test style sampled from `tests/test_integracao_chat.py`).

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Núcleo UI-agnóstico (`app_streamlit_core.py`) | unit | Todas as ramificações; 1:1 com as ACs P1/P2; edge cases (erro sanitizado, mensagem vazia, tokens nulos) | `tests/test_app_streamlit_core.py` | `python -m pytest tests/ -q` |
| Fluxo de threads sob persistência | integration | Ponta a ponta com `GerenciadorPersistencia(":memory:")`: criar, listar, retomar, excluir | `tests/test_app_streamlit_threads.py` | `python -m pytest tests/ -q` |
| App Streamlit (`app_streamlit.py`) | e2e | Fluxo via `AppTest`: enviar/exibir, histórico, estado entre reruns, controles da sidebar, painel condicional | `tests/test_app_streamlit_ui.py` | `python -m pytest tests/ -q` |
| Script `iniciar_streamlit.sh` | integration | CLI: sem `.venv` → erro claro + exit ≠ 0; conteúdo tem `streamlit run` + bind local | `tests/test_iniciar_streamlit_sh.py` | `python -m pytest tests/ -q` |
| Script `iniciar_streamlit.bat` | unit | Conteúdo: checagem de `.venv`, ativação, `streamlit run`, bind local | `tests/test_iniciar_streamlit_bat.py` | `python -m pytest tests/ -q` |
| Empacotamento (`requirements.txt`) | unit | Afirma `streamlit>=1.28.0` listado | `tests/test_requirements_streamlit.py` | `python -m pytest tests/ -q` |
| Documentação (`README.md`) | unit | Afirma menção a `iniciar_streamlit` e nota de bind local | `tests/test_readme_streamlit.py` | `python -m pytest tests/ -q` |

## Gate Check Commands

> Generated from codebase - confirm before Execute. Repo tem uma única suíte `pytest` e nenhum linter configurado.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tasks com testes unitários | `python -m pytest tests/ -q` |
| Full | Após tasks com testes de integração/e2e | `python -m pytest tests/ -q` |
| Build | Após conclusão de fase / tasks de config | `python -m pytest tests/ -q` |

---

## Execution Plan

Fases ordenadas e sequenciais - cada fase termina antes da próxima; tasks dentro de uma fase executam em ordem.

<!-- FASE: 1 -->
### Phase 1: Núcleo UI-agnóstico

Helpers testáveis sem `streamlit`.

```
T1 → T2
T1 → T3
```

<!-- FASE: 2 -->
### Phase 2: Threads sob persistência

Operações de thread reaproveitando `GerenciadorPersistencia`.

```
T1 → T4
T2 → T4
```

<!-- FASE: 3 -->
### Phase 3: App Streamlit

Wiring dos widgets ao núcleo, com estado em `st.session_state`.

```
T2 → T5
T3 → T5
T4 → T6
T5 → T6
```

<!-- FASE: 4 -->
### Phase 4: Scripts, empacotamento e documentação

Inicialização multiplataforma e ajustes de config/docs.

```
T5 → T7
T7 → T8
T8 → T9
T9 → T10
```

---

## Task Breakdown

### T1: Criar fábrica de sessão do chat no núcleo

**What**: Criar `app_streamlit_core.py` com `persistencia_ativa()` e `construir_sessao_chat(gerenciador=None, thread_id=None)` que instancia `ChatComMemoria` (com `gerenciador`/`thread_id` quando a persistência está ativa).
**Where**: `app_streamlit_core.py`
**Depends on**: None
**Reuses**: `chat_openai_memoria.ChatComMemoria` (`chat_openai_memoria.py:113`), `persistencia.GerenciadorPersistencia`
**Requirement**: STRM-01, STRM-10, STRM-14

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `persistencia_ativa()` lê `PERSISTENCIA_SQLITE` do ambiente (true/false)
- [x] `construir_sessao_chat` retorna `ChatComMemoria` sem alterar a assinatura pública do ctor
- [x] Testes unitários cobrem persistência ligada/desligada (mock de `OpenAI`, `patch.dict` env como em `tests/test_integracao_chat.py`)
- [x] Gate `python -m pytest tests/ -q` passa; suíte pré-existente intacta (nenhum teste removido)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(streamlit): fabrica de sessao do chat no nucleo`

---

### T2: Adicionar envio seguro e sanitização de erro

**What**: Adicionar `sanitizar_erro(exc)` e `enviar_mensagem_seguro(chat, texto)` que chama `enviar_mensagem()`, captura exceções e ignora texto vazio/branco.
**Where**: `app_streamlit_core.py`
**Depends on**: T1
**Reuses**: `ChatComMemoria.enviar_mensagem` (`chat_openai_memoria.py:549`)
**Requirement**: STRM-02, STRM-05

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Sucesso retorna `(resposta, None)`; exceção retorna `(None, msg_sanitizada)`
- [x] Mensagem sanitizada não contém a `OPENAI_API_KEY`, stack trace nem o texto bruto da exceção
- [x] Texto vazio/branco não chama a API e mantém o histórico inalterado
- [x] Testes unitários cobrem sucesso, exceção e entrada vazia
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: unit
**Gate**: quick

**Commit**: `feat(streamlit): envio seguro e sanitizacao de erro`

---

### T3: Adicionar helpers de histórico, tokens e exportação

**What**: Adicionar `historico_para_ui(chat)`, `resumo_tokens(chat)` e `exportar_conversa_texto(chat)` (grava via `exportar_conversa()` em arquivo `tempfile` e lê o conteúdo).
**Where**: `app_streamlit_core.py`
**Depends on**: T1
**Reuses**: `contar_tokens_aproximado` (`chat_openai_memoria.py:685`), `exportar_conversa` (`:805`), `GerenciadorPersistencia.total_tokens_thread` (`persistencia.py:132`)
**Requirement**: STRM-03, STRM-07, STRM-08

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `historico_para_ui` devolve pares `(role, content)` na ordem de `chat.historico`
- [x] `resumo_tokens` traz estimativa aproximada e, sob persistência com `thread_id`, o total persistido; degrada para aproximado se `total_tokens_thread` vier nulo
- [x] `exportar_conversa_texto` usa arquivo temporário (nunca no repositório) e devolve `(nome, conteudo)`
- [x] Testes unitários cobrem histórico, tokens (com/sem persistência e nulos) e exportação
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: unit
**Gate**: quick

**Commit**: `feat(streamlit): helpers de historico, tokens e exportacao`

---

### T4: Adicionar operações de thread no núcleo

**What**: Adicionar `listar_threads(gerenciador)`, `retomar_thread(gerenciador, thread_id)` (reconstrói `ChatComMemoria` com o `thread_id`) e `excluir_thread(gerenciador, thread_id)`.
**Where**: `app_streamlit_core.py`
**Depends on**: T1, T2
**Reuses**: `GerenciadorPersistencia.listar_threads/carregar_historico/excluir_thread` (`persistencia.py:74`), `construir_sessao_chat`
**Requirement**: STRM-09

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `retomar_thread` retorna chat com histórico carregado da thread
- [x] `excluir_thread` retorna `True` quando remove e `False` para id inexistente
- [x] Teste de integração com `GerenciadorPersistencia(":memory:")` cobre criar→listar→retomar→excluir ponta a ponta
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: integration
**Gate**: full

**Commit**: `feat(streamlit): operacoes de thread no nucleo`

---

### T5: Criar app Streamlit base (chat e estado)

**What**: Criar `app_streamlit.py` com init de `st.session_state` (via `construir_sessao_chat`), exibição do histórico, `st.chat_input` e envio via `enviar_mensagem_seguro`.
**Where**: `app_streamlit.py`
**Depends on**: T2, T3
**Reuses**: `app_streamlit_core` (`construir_sessao_chat`, `enviar_mensagem_seguro`, `historico_para_ui`)
**Requirement**: STRM-01, STRM-02, STRM-03, STRM-04

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `st.session_state` guarda `chat`, `thread_id` e `gerenciador`, inicializados uma vez
- [x] Enviar mensagem exibe a resposta e o histórico; erro sanitizado aparece amigável
- [x] Teste e2e com `AppTest` (patch dos helpers do core) valida envio, histórico e persistência de estado entre reruns; usa `pytest.importorskip("streamlit")`
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: e2e
**Gate**: full

**Commit**: `feat(streamlit): app base de chat e estado`

---

### T6: Adicionar controles da sidebar

**What**: Adicionar à app os controles: limpar (`limpar_historico`), métrica de tokens (`resumo_tokens`), download de exportação (`st.download_button` + `exportar_conversa_texto`) e painel de threads condicional a `persistencia_ativa()`.
**Where**: `app_streamlit.py`
**Depends on**: T4, T5
**Reuses**: `ChatComMemoria.limpar_historico` (`chat_openai_memoria.py:651`), helpers de T3/T4
**Requirement**: STRM-05, STRM-06, STRM-07, STRM-08, STRM-09

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Limpar esvazia o histórico exibido; tokens aparecem como métrica
- [x] Botão de download entrega o conteúdo exportado
- [x] Painel de threads aparece só quando `PERSISTENCIA_SQLITE=true` e some quando desativado
- [x] Teste e2e com `AppTest` cobre limpar, tokens, export e presença/ausência do painel conforme a flag
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: e2e
**Gate**: full

**Commit**: `feat(streamlit): controles da sidebar`

---

### T7: Criar script de inicialização Linux/Mac

**What**: Criar `iniciar_streamlit.sh` que faz `cd` para o diretório do script, ativa `.venv`, e roda `streamlit run app_streamlit.py --server.address=localhost`; se `.venv` ausente, imprime erro claro e sai com código ≠ 0.
**Where**: `iniciar_streamlit.sh`
**Depends on**: T5
**Reuses**: padrão de `iniciar_chat.bat` (ativação de `.venv` + erro claro)
**Requirement**: STRM-12

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Sem `.venv`, o script exibe mensagem de erro clara e `exit` ≠ 0
- [x] Conteúdo contém `streamlit run app_streamlit.py` e `--server.address=localhost`
- [x] Teste de integração roda o script num diretório temporário sem `.venv` (assert exit ≠ 0 + mensagem) e verifica o conteúdo
- [x] Gate `python -m pytest tests/ -q` passa

**Tests**: integration
**Gate**: full

**Commit**: `feat(streamlit): script de inicializacao linux/mac`

---

### T8: Criar script de inicialização Windows

**What**: Criar `iniciar_streamlit.bat` equivalente: `cd /d "%~dp0"`, checa `.venv\Scripts\activate.bat` (erro claro + `exit /b 1` se ausente), ativa e roda `streamlit run app_streamlit.py --server.address=localhost`.
**Where**: `iniciar_streamlit.bat`
**Depends on**: T7
**Reuses**: `iniciar_chat.bat` como base
**Requirement**: STRM-11

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Conteúdo tem a checagem de ausência do `.venv` com mensagem clara e `exit /b 1`
- [ ] Conteúdo tem ativação do `.venv` e `streamlit run app_streamlit.py --server.address=localhost`
- [ ] Teste unitário lê o arquivo e afirma os trechos exigidos
- [ ] Gate `python -m pytest tests/ -q` passa

**Tests**: unit
**Gate**: quick

**Commit**: `feat(streamlit): script de inicializacao windows`

---

### T9: Adicionar streamlit ao requirements

**What**: Adicionar `streamlit>=1.28.0` ao `requirements.txt` (mantendo as dependências existentes).
**Where**: `requirements.txt`
**Depends on**: T8
**Reuses**: `requirements.txt` atual
**Requirement**: STRM-13

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] `requirements.txt` lista `streamlit>=1.28.0`
- [ ] Dependências pré-existentes permanecem
- [ ] Teste unitário afirma a presença de `streamlit` com a versão mínima
- [ ] Gate `python -m pytest tests/ -q` passa

**Tests**: unit
**Gate**: quick

**Commit**: `build(streamlit): adiciona streamlit ao requirements`

---

### T10: Documentar uso no README

**What**: Atualizar `README.md` com a nova forma de uso (scripts `iniciar_streamlit`, `streamlit run app_streamlit.py`) e a nota de segurança de bind local.
**Where**: `README.md`
**Depends on**: T9
**Reuses**: seções de uso e testes do `README.md`
**Requirement**: STRM-11, STRM-12

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] README documenta `iniciar_streamlit` e o `streamlit run`
- [ ] README traz a nota de bind local (`--server.address=localhost`) e chave server-side
- [ ] Teste unitário afirma as menções esperadas no README
- [ ] Gate `python -m pytest tests/ -q` passa

**Tests**: unit
**Gate**: quick

**Commit**: `docs(streamlit): documenta uso do front-end no readme`
