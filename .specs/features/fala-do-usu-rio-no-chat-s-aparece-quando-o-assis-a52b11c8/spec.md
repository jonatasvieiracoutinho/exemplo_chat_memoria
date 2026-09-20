# Exibição imediata da mensagem do usuário no chat Streamlit — Specification

## Problem Statement

Na interface Streamlit (`app_streamlit.py::main()`), a mensagem digitada só aparece na tela junto com a resposta do assistente: `enviar_mensagem_seguro` roda de forma síncrona e bloqueante (anexa a fala, chama a API e anexa a resposta) e só então ocorre o `st.rerun()` que redesenha a UI. Durante toda a latência da API a tela fica no estado anterior, sem a fala recém-digitada, dando a impressão de que a mensagem foi perdida. Precisamos pintar a fala do usuário assim que é enviada, mantê-la visível durante o processamento e exibir a resposta em seguida, sem regressões de persistência ou de tratamento de erro.

## Goals

- [ ] A mensagem do usuário é renderizada imediatamente após o envio, antes da geração da resposta.
- [ ] A mensagem do usuário permanece visível durante o processamento, com indicação de que a resposta está sendo gerada.
- [ ] A resposta do assistente aparece após a mensagem do usuário, sem duplicar mensagens no histórico nem gravar duas vezes na persistência, e o erro sanitizado continua exibido mantendo a fala do usuário visível.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
| ------- | ------ |
| Alterar a lógica de geração em `chat_openai_memoria.py` (anexar, chamada à API, contagem de tokens) | Fora de escopo pelo PRD; a correção fica na camada de wiring |
| Streaming da resposta na UI ou processamento assíncrono | Explicitamente fora de escopo; a geração continua síncrona |
| Mudanças em `persistencia.py`, modo terminal ou continuidade/gerência de conversas | Não faz parte deste problema |
| Redesenho visual além do feedback de processamento | Só o necessário para o indicador de carregamento |

---

## Assumptions & Open Questions

Every ambiguity is resolved or recorded here - nothing is left silently unclear.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Manter ou remover o `st.rerun()` no sucesso do envio | Remover o `st.rerun()` no sucesso e renderizar o turno inline na mesma execução (fala do usuário, indicador e resposta) | A renderização inline é o mecanismo que mantém a fala visível durante e após a geração; um rerun no fim descartaria a pintura inline e reintroduziria o bug de "aparecer só com a resposta" | n |
| Mecanismo do indicador de processamento | `st.spinner` com mensagem em português ("Gerando resposta...") em volta da chamada bloqueante | Idiomático no Streamlit, mínimo e aderente ao escopo do feedback de processamento | n |
| Onde exibir o erro sanitizado no novo fluxo | `st.error(erro)` abaixo da fala do usuário já pintada, sem bolha de assistente vazia | Preserva o comportamento sanitizado atual e mantém a fala do usuário visível na falha | n |
| Timing do append em `enviar_mensagem` versus a pintura imediata | A pintura imediata da fala é feita pela camada de wiring via `st.chat_message`, independente do append do núcleo | `enviar_mensagem` anexa o `user` antes da chamada à API e não faz rollback na falha (`chat_openai_memoria.py:564,645-649`); pintar pelo wiring garante CA-01/CA-06 independentemente do append | n |
| Tipo e ambiente dos testes | Testes de integração com `streamlit.testing.v1.AppTest`, pulados com `pytest.importorskip("streamlit")` quando o Streamlit não está instalado | Segue a convenção da suíte atual (`tests/test_app_streamlit_ui.py`) | n |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Fala do usuário aparece na hora ⭐ MVP

**User Story**: As a pessoa usuária do chat web, I want ver minha mensagem na tela assim que a envio so that eu tenha certeza de que ela não se perdeu enquanto a resposta é gerada.

**Why P1**: É a correção central do PRD — sem ela a interação parece quebrada.

**Acceptance Criteria**:

1. WHEN the user submits a message THEN the system SHALL render the user's message in the chat area before response generation begins.
2. WHILE the response is being generated the system SHALL keep the user's message visible in the chat area.
3. WHILE the response is being generated the system SHALL display a processing indicator.
4. WHEN response generation succeeds THEN the system SHALL render the assistant reply after the user's message without overwriting or hiding it.
5. WHEN the user sends messages in consecutive interactions THEN the system SHALL render each turn consistently without duplicating messages in the history or persisting a turn twice.
6. IF response generation fails THEN the system SHALL display the sanitized error message while keeping the user's message visible.

**Independent Test**: Com `AppTest`, enviar uma mensagem com `enviar_mensagem_seguro` simulado e verificar que a bolha do usuário aparece antes da resposta, que o indicador é acionado, que a resposta vem depois sem duplicar, e que na falha o erro sanitizado aparece com a fala do usuário ainda visível.

---

## Edge Cases

- IF `enviar_mensagem_seguro` returns an error THEN the system SHALL keep the already-rendered user message visible and show only the sanitized message.
- WHEN the submitted text is empty or blank THEN the system SHALL NOT render a turn nor call generation (comportamento atual de `enviar_mensagem_seguro`).
- WHEN two messages are sent one after another THEN the system SHALL render four ordered bubbles without any duplicate.

---

## Requirement Traceability

Each requirement gets a unique ID for tracking across design, tasks, and validation.

| Requirement ID | Story | Origem | Phase | Status |
| -------------- | ----- | ------ | ----- | ------ |
| CHAT-01 | P1 | RF-01, CA-01 | Tasks | Implementing |
| CHAT-02 | P1 | RF-02, CA-02 | Tasks | Implementing |
| CHAT-03 | P1 | RF-04 | Tasks | Implementing |
| CHAT-04 | P1 | RF-03, CA-03 | Tasks | Implementing |
| CHAT-05 | P1 | RF-05, CA-04, CA-05 | Tasks | Implementing |
| CHAT-06 | P1 | RF-06, CA-06 | Tasks | Pending |

**ID format:** `[CATEGORY]-[NUMBER]` (e.g., `CHAT-01`)

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 6 total, 6 mapped to tasks, 0 unmapped.

---

## Success Criteria

How we know the feature is successful:

- [ ] Ao enviar, a bolha do usuário aparece antes da resposta e permanece visível durante a geração (com indicador).
- [ ] A resposta aparece após a fala do usuário, sem duplicar mensagens no histórico nem gravar o turno duas vezes.
- [ ] Na falha, o erro sanitizado é exibido mantendo a fala do usuário visível; a suíte `tests/` passa sem regressões.
