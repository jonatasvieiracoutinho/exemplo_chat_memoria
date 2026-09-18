# Front-end Streamlit com Scripts de Inicialização Specification

## Problem Statement

O `exemplo_chat_memoria` só é operável pelo terminal (`chat_interativo()`), reduzindo a acessibilidade da demonstração em aula. A inicialização automatizada só existe no Windows (`iniciar_chat.bat`), sem equivalente Linux/Mac. É preciso uma interface web alternativa em Streamlit que reaproveite `ChatComMemoria`/`GerenciadorPersistencia` sem duplicar negócio, e scripts de inicialização para os dois SOs.

## Goals

- [ ] Interface Streamlit funcional que sobe via `streamlit run` e conversa com o assistente reutilizando `ChatComMemoria` (sem duplicar lógica).
- [ ] Paridade com os comandos essenciais do terminal: enviar/receber, histórico, limpar, tokens, exportar e, sob persistência, listar/retomar/excluir threads.
- [ ] Scripts `iniciar_streamlit.bat` e `iniciar_streamlit.sh` que ativam o `.venv`, tratam ausência do `.venv` com erro claro e sobem a app com bind local.
- [ ] CLI e API pública de `ChatComMemoria` inalteradas; testes atuais continuam válidos.

## Out of Scope

Explicitamente excluído. Documentado para evitar scope creep.

| Feature | Reason |
| ------- | ------ |
| Redesign visual, temas custom, componentes avançados | PRD 5: foco em UI simples |
| Autenticação, multiusuário, deploy em nuvem | PRD 5: mitigação é bind local, não auth |
| Alteração/remoção da CLI existente | PRD 5/CA-08: CLI inalterada |
| Mudança de schema SQLite ou lógica de `ChatComMemoria` | PRD 5: reuso sem refatorar negócio |
| Auto-instalação de dependências pelos scripts | PRD 5: scripts só ativam ambiente |
| Streaming token-a-token na web | PRD 5/8: `OPENAI_STREAM` desligado |

---

## Assumptions & Open Questions

Toda ambiguidade é resolvida ou registrada aqui — nada fica silenciosamente indefinido. Sessão headless: nenhuma decisão foi confirmada por humano (Confirmed = n); o HITL do Orion confirma depois.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| PRD usava IDs `RF1`/`CA1` | Normalizados para `RF-01`..`CA-08` (só notação) | Gate `checar_rastreabilidade.py` exige `RF-nn`/`CA-nn` | n |
| Lógica testável sem servidor Streamlit | Helpers UI-agnósticos em `app_streamlit_core.py`; `app_streamlit.py` só faz wiring | Testar sem importar `streamlit`; app fina | n |
| Exibição de tokens | Métrica da sessão via `contar_tokens_aproximado()`; sob persistência somar `total_tokens_thread()` | Reusa métodos, sem tocar terminal | n |
| Exportação na web | `exportar_conversa()` em arquivo temporário + `st.download_button` | Reusa método sem depender de stdout | n |
| Streaming na UI | `OPENAI_STREAM` desligado; usa valor de retorno | PRD 5/8: evitar refatorar chunks | n |
| Bind de rede | `streamlit run ... --server.address=localhost` | PRD 9: reduzir exposição da chave | n |
| Seleção de thread | Sidebar com selectbox + retomar/excluir, só sob `PERSISTENCIA_SQLITE=true` | RF-08 pede ocultar quando desativada | n |
| Verificação e2e | `streamlit.testing.v1.AppTest` com helpers injetados via patch | Roda app headless; evita servidor/API real | n |
| Versão do Streamlit | `streamlit>=1.28.0` | Garante `AppTest` disponível | n |
| Documentação | Atualizar `README.md`; `env.example` já cobre as variáveis | PRD 4: atualização mínima, sem novas variáveis | n |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Conversar pela interface Streamlit ⭐ MVP

**User Story**: Como aluno/usuário, quero conversar com o assistente por uma tela web simples, para não depender do terminal.

**Why P1**: Núcleo do PRD (RF-01..RF-04) e valor central da feature.

**Acceptance Criteria** (cada linha é um padrão EARS):

1. WHEN o usuário abre a aplicação via `streamlit run` THEN the system SHALL apresentar campo de entrada de mensagem e área de histórico da conversa  <!-- event-driven -->
2. WHEN o usuário envia uma mensagem THEN the system SHALL chamar `ChatComMemoria.enviar_mensagem()` e exibir o valor de retorno como resposta do assistente sem depender de stdout/ANSI  <!-- event-driven -->
3. The system SHALL exibir o histórico da sessão em ordem, distinguindo visualmente mensagens do usuário e do assistente  <!-- ubiquitous -->
4. WHILE a mesma sessão do navegador permanece ativa the system SHALL preservar em `st.session_state` a instância de `ChatComMemoria`, o `thread_id` e o histórico entre interações  <!-- state-driven -->
5. IF `enviar_mensagem()` levanta exceção THEN the system SHALL exibir mensagem de erro amigável sem expor chave, stack trace ou detalhes internos  <!-- unwanted-behavior -->

**Independent Test**: Via `AppTest`, enviar uma mensagem com `enviar_mensagem` mockado e ver a resposta e o histórico renderizados; reexecutar e confirmar que o estado persiste.

---

### P2: Ações essenciais da conversa na UI

**User Story**: Como usuário, quero limpar a conversa, ver tokens e exportar, para ter paridade com os comandos essenciais do terminal.

**Why P2**: Complementa o MVP com as ações de gestão da conversa (RF-05..RF-07), mas o chat já é útil sem elas.

**Acceptance Criteria**:

1. WHEN o usuário aciona "limpar conversa" THEN the system SHALL chamar `limpar_historico()` e esvaziar o histórico exibido  <!-- event-driven -->
2. The system SHALL exibir a contagem de tokens da conversa reaproveitando `contar_tokens_aproximado()` (e, sob persistência, `total_tokens_thread()`)  <!-- ubiquitous -->
3. WHEN o usuário aciona "exportar conversa" THEN the system SHALL gerar o conteúdo via `exportar_conversa()` e oferecê-lo para download  <!-- event-driven -->

**Independent Test**: Via `AppTest`, acionar limpar e ver histórico vazio; verificar a métrica de tokens exibida; acionar exportar e ver o botão de download com conteúdo.

---

### P3: Gestão de threads sob persistência

**User Story**: Como usuário com `PERSISTENCIA_SQLITE=true`, quero listar, retomar e excluir threads na UI, para continuar conversas anteriores.

**Why P3**: Só aplicável quando a persistência opcional está ativa (RF-08); é um recurso condicional.

**Acceptance Criteria**:

1. WHERE `PERSISTENCIA_SQLITE=true` the system SHALL permitir listar, retomar e excluir threads reaproveitando `GerenciadorPersistencia`  <!-- optional-feature -->
2. WHERE a persistência está desativada the system SHALL ocultar ou desabilitar as ações de threads  <!-- optional-feature -->
3. WHEN o usuário retoma uma thread THEN the system SHALL reconstruir `ChatComMemoria` com o `thread_id` selecionado e carregar seu histórico em `st.session_state`  <!-- event-driven -->

**Independent Test**: Com `GerenciadorPersistencia(":memory:")`, criar threads via chat, listar, retomar (histórico carregado) e excluir (thread some).

---

### P4: Inicialização automática multiplataforma

**User Story**: Como usuário, quero subir o front-end com um único script no meu SO, para não digitar comandos manuais.

**Why P4**: Automação de inicialização (RF-11..RF-13); depende da app existir.

**Acceptance Criteria**:

1. WHEN o usuário executa `iniciar_streamlit.bat` (Windows) THEN the system SHALL ativar o `.venv` e rodar `streamlit run app_streamlit.py` com bind local  <!-- event-driven -->
2. WHEN o usuário executa `iniciar_streamlit.sh` (Linux/Mac) THEN the system SHALL ativar o `.venv` e rodar `streamlit run app_streamlit.py` com bind local  <!-- event-driven -->
3. IF o `.venv` não existe THEN the system SHALL exibir mensagem de erro clara e encerrar com código diferente de zero em vez de falhar silenciosamente  <!-- unwanted-behavior -->
4. The system SHALL listar `streamlit>=1.28.0` em `requirements.txt` e documentar a nova forma de uso no `README.md`  <!-- ubiquitous -->

**Independent Test**: Executar `iniciar_streamlit.sh` num diretório temporário sem `.venv` e ver saída de erro clara com código de saída ≠ 0; inspecionar o conteúdo dos scripts e do `requirements.txt`/`README.md`.

---

## Edge Cases

- IF a API retorna erro (rede, cota, chave inválida) THEN the system SHALL exibir texto amigável e manter a UI utilizável  <!-- unwanted-behavior -->
- IF o usuário envia mensagem vazia THEN the system SHALL não chamar a API e manter o estado inalterado  <!-- unwanted-behavior -->
- IF `total_tokens_thread()` retorna nulos/ausentes THEN the system SHALL exibir a estimativa aproximada sem quebrar  <!-- unwanted-behavior -->

---

## Requirement Traceability

Cada requisito recebe um ID rastreável. A coluna **Origem** liga ao ID congelado do PRD.

| Requirement ID | Origem | Story | Phase | Status |
| -------------- | ------ | ----- | ----- | ------ |
| STRM-01 | RF-01, CA-01 | P1 | Tasks | Pending |
| STRM-02 | RF-02 | P1 | Tasks | Pending |
| STRM-03 | RF-03 | P1 | Tasks | Pending |
| STRM-04 | RF-04, CA-06 | P1 | Tasks | Pending |
| STRM-05 | RF-09, CA-07 | P1 | Tasks | Pending |
| STRM-06 | RF-05 | P2 | Tasks | Pending |
| STRM-07 | RF-06 | P2 | Tasks | Pending |
| STRM-08 | RF-07 | P2 | Tasks | Pending |
| STRM-09 | RF-08, CA-02 | P3 | Tasks | Pending |
| STRM-10 | RF-10 | P1 | Tasks | Pending |
| STRM-11 | RF-11, CA-03, CA-05 | P4 | Tasks | Pending |
| STRM-12 | RF-12, CA-04, CA-05 | P4 | Tasks | Pending |
| STRM-13 | RF-13 | P4 | Tasks | Pending |
| STRM-14 | CA-08 | P1 | Tasks | Pending |

**ID format:** `[CATEGORY]-[NUMBER]` (ex.: `STRM-01`)

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 14 total, 14 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] `streamlit run app_streamlit.py` sobe a app e permite conversar (CA-01).
- [ ] Enviar/receber, histórico, limpar, tokens, exportar; sob persistência, listar/retomar/excluir threads (CA-02).
- [ ] Estado persiste entre interações da mesma sessão (CA-06).
- [ ] Erros da API aparecem amigáveis, sem vazar chave nem detalhes (CA-07).
- [ ] Scripts sobem a app sem passos manuais; sem `.venv`, erro claro (CA-03/CA-04/CA-05).
- [ ] Suíte atual (incl. `tests/test_integracao_chat.py`) segue passando (CA-08).
