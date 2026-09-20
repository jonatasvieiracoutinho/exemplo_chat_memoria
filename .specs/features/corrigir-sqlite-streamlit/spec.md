# Conexão SQLite compatível com reruns do Streamlit Specification

## Problem Statement

Com `PERSISTENCIA_SQLITE=true`, a aplicação conserva um `GerenciadorPersistencia` em `st.session_state`. O Streamlit reexecuta o script a cada interação e pode fazê-lo em outra thread; a conexão `sqlite3.Connection` criada na primeira execução então falha na leitura da sidebar antes do envio da mensagem. A correção deve permitir iniciar e continuar uma conversa persistida sem compartilhar uma conexão SQLite entre threads.

## Goals

- [ ] Remover o erro `sqlite3.ProgrammingError` causado pelo reuso de uma conexão entre reruns do Streamlit.
- [ ] Preservar o comportamento público do gerenciador, o schema existente e as conversas já gravadas.
- [ ] Cobrir a regressão com uma interação realista de duas renderizações da UI Streamlit.

## Out of Scope

Explicitamente excluído para manter a correção focada.

| Feature | Reason |
| ------- | ------ |
| Autenticação, isolamento de dados entre usuários ou deploy multiusuário | Não fazem parte do defeito de afinidade de thread atual. |
| Alteração do schema SQLite, migração de dados ou exclusão de threads | A correção é de ciclo de vida da conexão; os dados existentes devem permanecer intactos. |
| Substituir SQLite por outro banco ou adicionar ORM/pool de conexões | A solução deve preservar o propósito educacional e a dependência padrão da biblioteca. |
| Resolver indisponibilidade física do arquivo, corrupção ou todos os cenários de lock externos | São falhas distintas do `ProgrammingError` reproduzido. |
| Redesenho da UI ou mudança do contrato público de `ChatComMemoria` | Não é necessário para permitir a conversa persistida. |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Estratégia de ciclo de vida | O gerenciador abrirá e fechará uma conexão por operação pública, em vez de guardar `sqlite3.Connection` no estado da sessão. | Cada operação executará na thread que a chamou; evita desligar a proteção `check_same_thread` e não exige lock manual compartilhado. | y |
| Concorrência entre sessões | Manter transações curtas e o timeout padrão do SQLite; não introduzir lock global em memória. | O fluxo atual já faz commits por operação; um lock global não coordenaria outros processos que possam abrir o mesmo arquivo. | y |
| Banco existente | Reutilizar `chat_memoria.db` e executar a inicialização/migração idempotente a cada conexão aberta. | O schema atual já usa `CREATE TABLE IF NOT EXISTS`; não há motivo para alterar ou recriar dados. | y |
| Erro de banco fora da causa reproduzida | Não alterar a política de mensagens além de garantir que a regressão não levante exceção. | O problema confirmado é a afinidade de thread, não erro de lock, permissões ou corrupção. | y |

**Open questions:** none - all gray areas are recorded as assumptions pending approval.

---

## User Stories

### P1: Conversar com persistência após um rerun ⭐ MVP

**User Story**: Como usuário com persistência SQLite ativa, quero enviar a primeira mensagem pela tela Streamlit após a página renderizar novamente, para iniciar uma conversa sem o erro de thread do SQLite.

**Why P1**: É o bloqueio que impede o uso básico do chat persistido.

**Acceptance Criteria**:

1. WHERE `PERSISTENCIA_SQLITE=true` the system SHALL execute every public persistence operation using a SQLite connection created in the calling thread.  <!-- optional-feature -->
2. WHEN a user interaction causes Streamlit to rerun the page THEN the system SHALL render the thread sidebar and the chat input without raising `sqlite3.ProgrammingError` about a connection created in another thread.  <!-- event-driven -->
3. WHEN the user submits the first nonblank message after the initial render THEN the system SHALL create or reuse the active thread and persist the user and assistant messages in their existing order.  <!-- event-driven -->
4. WHEN the model usage is available for that submitted message THEN the system SHALL persist its prompt, completion, and total token counts in the existing `turnos` table.  <!-- event-driven -->

**Independent Test**: Via `streamlit.testing.v1.AppTest`, habilitar a persistência com um banco temporário, executar a renderização inicial e uma segunda renderização com envio simulado da API; verificar ausência de exceção e os registros de thread, mensagens e turno.

---

### P2: Preservar o contrato e os dados da persistência

**User Story**: Como usuário que já possui conversas salvas, quero que a correção mantenha o banco e a API de persistência existentes, para não perder dados nem quebrar o CLI.

**Why P2**: A persistência é compartilhada pelo Streamlit e pelo chat de terminal.

**Acceptance Criteria**:

1. WHEN `GerenciadorPersistencia` opens an existing database THEN the system SHALL preserve the existing `threads`, `mensagens`, and `turnos` records and run the schema initialization idempotently.  <!-- event-driven -->
2. The system SHALL keep the public methods `criar_thread`, `salvar_mensagem`, `listar_threads`, `carregar_historico`, `excluir_thread`, `thread_existe`, `salvar_turno`, `carregar_turnos`, `total_tokens_thread`, and `fechar` callable with their current signatures.  <!-- ubiquitous -->
3. WHILE `PERSISTENCIA_SQLITE` is disabled the system SHALL avoid creating or opening a SQLite database from the Streamlit flow.  <!-- state-driven -->
4. The system SHALL continue to bind every value originating from a message or thread identifier as a SQL parameter.  <!-- ubiquitous; Norma 4.4.2.5.a, 4.4.2.5.b, 4.4.2.5.d, 4.4.13.1.b; ASVS V5 -->

**Independent Test**: Executar a suíte de persistência existente contra banco temporário, a regressão Streamlit em duas renderizações e o teste de persistência desativada; confirmar que os métodos e dados esperados continuam disponíveis.

## Edge Cases

- IF a thread existente é retomada antes de um rerun THEN the system SHALL carregar seu histórico usando uma conexão pertencente à thread da renderização atual.  <!-- unwanted-behavior -->
- WHEN the user excludes a thread via sidebar THEN the system SHALL executar a exclusão e o rerun subsequente sem reusar uma conexão criada por outra thread.  <!-- event-driven -->
- IF a SQLite operation fails for a reason different from the afinidade de thread THEN the system SHALL preserve the existing exception semantics outside the fluxo de envio seguro.  <!-- unwanted-behavior -->

## Requirement Traceability

| Requirement ID | Story | Phase | Status |
| -------------- | ----- | ----- | ------ |
| SQLSTRM-01 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-02 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-03 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-04 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-05 | P2: Preservar o contrato e os dados da persistência | Design | Pending |
| SQLSTRM-06 | P2: Preservar o contrato e os dados da persistência | Design | Pending |
| SQLSTRM-07 | P2: Preservar o contrato e os dados da persistência | Design | Pending |
| SQLSTRM-08 | P2: Preservar o contrato e os dados da persistência | Design | Pending |
| SQLSTRM-09 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-10 | P1: Conversar com persistência após um rerun | Design | Pending |
| SQLSTRM-11 | P2: Preservar o contrato e os dados da persistência | Design | Pending |

**Coverage:** 11 total, 0 mapped to tasks, 11 pending.

## Success Criteria

- [ ] Uma interação após a renderização inicial com `PERSISTENCIA_SQLITE=true` não produz `sqlite3.ProgrammingError`.
- [ ] A primeira conversa salva inclui thread, duas mensagens e, quando disponível, um turno com uso de tokens.
- [ ] As conversas existentes e a suíte de persistência continuam válidas.
