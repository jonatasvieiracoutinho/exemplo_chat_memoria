# Contexto — Conexão SQLite compatível com reruns do Streamlit

**Coletado:** 2026-09-20
**Spec:** `.specs/features/corrigir-sqlite-streamlit/spec.md`
**Status:** Aprovado para desenho

---

## Feature Boundary

Eliminar o reuso de uma conexão SQLite entre threads de renderizações do Streamlit, mantendo a persistência atual de threads, mensagens e tokens. A correção não muda o schema, a CLI, o contrato público dos métodos do gerenciador ou a política de tratamento para falhas SQLite que não sejam a afinidade de thread.

---

## Implementation Decisions

### Ciclo de vida da conexão

- Cada operação pública do `GerenciadorPersistencia` abrirá uma conexão SQLite pertencente à thread que executa a operação e a fechará ao terminar.
- O gerenciador não manterá uma `sqlite3.Connection` viva em `st.session_state`.
- `fechar()` continuará disponível para compatibilidade e não precisará encerrar uma conexão persistente.

### Concorrência e integridade

- As transações continuarão curtas e serão confirmadas no escopo de cada operação de escrita.
- Não haverá lock global em memória; ele não coordenaria outro processo que também acessasse o mesmo arquivo SQLite.
- O timeout padrão do SQLite permanece inalterado nesta feature.

### Compatibilidade e limites de erro

- `chat_memoria.db`, as tabelas atuais e a migração idempotente serão preservados.
- As assinaturas dos métodos públicos do gerenciador não mudarão.
- `conn` é detalhe interno; os testes de caixa branca que o acessam serão substituídos por testes observáveis do banco e da API pública.
- Falhas SQLite que não sejam a regressão de thread não receberão nova política de captura ou mensagem na sidebar nesta feature.

### Verificação da regressão

- Um teste `AppTest` usará banco temporário e resposta da OpenAI simulada.
- Ele executará renderização inicial e envio de mensagem em renderização subsequente, depois verificará a ausência do `ProgrammingError` e a persistência de thread, mensagens e tokens.

### Agent's Discretion

- Escolher o helper privado mais didático para abrir/configurar a conexão e executar a migração, desde que cada chamada pública preserve o contrato especificado.
- Manter ou reorganizar os testes unitários de persistência conforme necessário para que eles verifiquem resultados observáveis, não detalhes de conexão.

### Declined / Undiscussed Gray Areas → Assumptions

- Nenhuma. Todas as áreas identificadas foram aprovadas pelo usuário em 2026-09-20.

---

## Specific References

- A reprodução mostra que o gerenciador é criado na inicialização da sessão e guardado em `st.session_state` em `app_streamlit.py:24-31`; a segunda renderização o usa para listar threads em `app_streamlit.py:55-58`.
- `GerenciadorPersistencia` mantém hoje a conexão em `self.conn` desde `persistencia.py:8-13`.
- A documentação do Python informa que `check_same_thread=True` é padrão e levanta `ProgrammingError` entre threads; desabilitá-lo exige serializar escritas: [sqlite3](https://docs.python.org/3/library/sqlite3.html).
- A documentação do Streamlit confirma que o script é reexecutado de cima a baixo a cada interação e que `Session State` preserva valores entre reruns: [Session State](https://docs.streamlit.io/develop/concepts/architecture/session-state).

## Deferred Ideas

- Política de UX para `database is locked`, erro de permissão, corrupção e indisponibilidade do arquivo.
- Estratégia de acesso concorrente a um banco compartilhado por múltiplos processos ou usuários.
