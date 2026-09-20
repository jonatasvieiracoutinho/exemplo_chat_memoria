# Continuidade de conversas persistidas na interface web Specification

## Problem Statement

Na interface web (Streamlit), o `GerenciadorPersistencia` reutiliza uma única conexão SQLite guardada na sessão. Uma nova renderização (rerun) pode rodar em outra thread da que criou a conexão, e o SQLite levanta `ProgrammingError` de conexão entre execuções. Isso bloqueia o primeiro envio após a renderização e impede usar uma funcionalidade apresentada como persistente. A correção precisa manter íntegros os dados e o comportamento compartilhado com o modo de terminal.

## Goals

- [ ] Interface web renderiza novamente com persistência ativa sem erro de conexão entre execuções e permite iniciar/continuar conversas.
- [ ] Mensagens e uso de tokens são gravados na conversa correta, na ordem em que ocorreram.
- [ ] Listar, retomar e excluir conversas funcionam após novas renderizações.
- [ ] Dados e capacidades de persistência existentes preservados na web e no terminal; execução sem persistência não cria armazenamento local.

## Out of Scope

Explicitamente excluído. Documentado para evitar scope creep.

| Feature | Reason |
| ------- | ------ |
| Autenticação e isolamento multiusuário | PRD: defeito ocorre em sessão local; sem modelo de acesso multiusuário |
| Substituir o armazenamento local, adotar ORM ou banco remoto | PRD: corrige continuidade do armazenamento atual; preserva caráter didático |
| Novo desenho visual ou mudança da API pública do chat | PRD: UI e contrato atuais não são a causa |
| Tratar indisponibilidade, corrupção ou contenção externa do banco | PRD: falhas distintas, com política e escopo próprios |
| Coordenação global entre processos ou mudança dos limites de espera | PRD: operações seguem curtas; sem coordenação nova |

---

## Assumptions & Open Questions

Toda ambiguidade é resolvida ou registrada aqui. Sessão headless: nenhuma decisão foi confirmada por humano (Confirmed = n); o HITL do Orion confirma depois.

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Abordagem de conexão | Conexão curta por operação no modo arquivo; conexão única no modo `:memory:` | RF-01 exige compatibilidade com a execução chamadora; `:memory:` não sobrevive entre conexões e é só de teste | n |
| Preservar API pública | Assinaturas de `GerenciadorPersistencia` inalteradas; `fechar()` vira no-op no modo arquivo | RF-07: consumidores não mudam como usam o recurso | n |
| Reprodução do rerun | Simular execução em thread distinta (threading/executor) com OpenAI mockado e banco temporário isolado, sem subir servidor Streamlit | Reproduz a causa real (erro de conexão entre execuções) de forma determinística | n |
| Teste white-box de conexão | Adaptar o teste de migração que lê `.conn` em modo arquivo para consultar via conexão nova | `.conn` deixa de existir no modo arquivo; asserção passa a usar conexão curta | n |
| Sem alteração de schema | Manter tabelas `threads`/`mensagens`/`turnos` e `PRAGMA foreign_keys=ON` por conexão | Fora de escopo; preserva dados existentes | n |
| Sem mudança de UI/CLI | `app_streamlit.py` e `chat_interativo` permanecem; correção concentrada em `persistencia.py` | Fora de escopo: sem redesenho nem nova API | n |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Continuidade da conversa após renderização ⭐ MVP

**User Story**: Como pessoa usuária da interface web com persistência ativa, quero renderizar a página novamente e enviar minha primeira mensagem sem erro de conexão, para iniciar ou continuar uma conversa persistida.

**Why P1**: Núcleo do PRD (RF-01..RF-04, RF-07, RF-09) e valor central da correção.

**Acceptance Criteria** (cada linha é um padrão EARS):

1. WHEN uma operação de persistência é solicitada por uma execução diferente da que criou o gerenciador THEN the system SHALL executá-la em conexão compatível com a execução chamadora, sem levantar erro de conexão entre execuções  <!-- event-driven -->
2. WHEN a interface web é renderizada novamente com persistência ativa THEN the system SHALL disponibilizar a lista de conversas e o campo de mensagem sem erro de conexão pertencente a outra execução  <!-- event-driven -->
3. WHEN a pessoa envia a primeira mensagem não vazia após a renderização inicial THEN the system SHALL criar ou reutilizar a conversa ativa e registrar a mensagem da pessoa seguida da resposta do assistente na ordem em que ocorreram  <!-- event-driven -->
4. WHEN o provedor informa as três quantidades de uso de tokens de uma interação persistida THEN the system SHALL registrar as quantidades de entrada, saída e total correspondentes àquela interação  <!-- event-driven -->
5. The system SHALL preservar as conversas, mensagens e registros de uso já gravados e manter as capacidades de criar, listar, retomar, excluir e consultar conversas na interface web e no terminal  <!-- ubiquitous -->
6. IF o conteúdo de uma mensagem ou identificador contém aspas, apóstrofos ou outros caracteres especiais THEN the system SHALL tratá-lo como dado literal, sem executar instruções não solicitadas nem alterar outra conversa  <!-- unwanted-behavior -->
7. WHEN a interface conclui uma renderização inicial e outra com o envio de mensagem, com resposta simulada do provedor com uso completo THEN the system SHALL concluir sem erro de conexão entre execuções e deixar no armazenamento exatamente uma conversa ativa, duas mensagens ordenadas e um registro de uso associado ao envio  <!-- event-driven -->

**Independent Test**: Com banco em arquivo temporário e OpenAI mockado, criar o gerenciador em uma thread e executar operações de persistência em outra thread; confirmar ausência de `ProgrammingError` e o armazenamento com uma conversa, duas mensagens ordenadas e um turno com uso.

---

### P2: Gestão de conversas após rerun e persistência opcional

**User Story**: Como pessoa usuária, quero retomar e excluir conversas após novas renderizações e, quando a persistência está desativada, não gerar armazenamento local, para administrar conversas com previsibilidade.

**Why P2**: Complementa o MVP (RF-05, RF-06, RF-08); depende da correção do lifecycle de conexão.

**Acceptance Criteria**:

1. WHEN a pessoa seleciona na lista uma conversa salva antes de uma nova renderização THEN the system SHALL apresentar o histórico daquela conversa na ordem original  <!-- event-driven -->
2. WHEN a pessoa exclui uma conversa e a página é renderizada novamente THEN the system SHALL removê-la da lista e impedir sua retomada  <!-- event-driven -->
3. WHILE a persistência local está desativada the system SHALL não criar nem acessar arquivo de armazenamento local de conversas no fluxo da interface web  <!-- state-driven -->

**Independent Test**: Reutilizar a simulação de rerun; retomar uma conversa e conferir o histórico ordenado, excluir e conferir que some da lista; com persistência desativada, confirmar que nenhum arquivo de banco é criado.

---

## Edge Cases

- IF a mesma operação é solicitada por várias execuções em sequência THEN the system SHALL abrir e encerrar uma conexão curta por operação, sem reter conexão de execução anterior  <!-- unwanted-behavior -->
- IF o objeto de uso de tokens vier ausente ou incompleto THEN the system SHALL persistir o turno com quantidades nulas sem levantar erro  <!-- unwanted-behavior -->
- WHEN o banco é um armazenamento em memória (`:memory:`) usado em testes THEN the system SHALL manter uma única conexão compartilhada, pois um banco em memória não sobrevive entre conexões distintas  <!-- event-driven -->

---

## Requirement Traceability

Cada requisito recebe um ID rastreável. A coluna **Origem** liga ao ID congelado do PRD.

| Requirement ID | Origem | Story | Phase | Status |
| -------------- | ------ | ----- | ----- | ------ |
| SQLR-01 | RF-01, CA-01 | P1 | Tasks | Implementing |
| SQLR-02 | RF-02, CA-01 | P1 | Tasks | In Tasks |
| SQLR-03 | RF-03, CA-02 | P1 | Tasks | In Tasks |
| SQLR-04 | RF-04, CA-03 | P1 | Tasks | In Tasks |
| SQLR-05 | RF-05, CA-04 | P2 | Tasks | In Tasks |
| SQLR-06 | RF-06, CA-05 | P2 | Tasks | In Tasks |
| SQLR-07 | RF-07, CA-06 | P1 | Tasks | Implementing |
| SQLR-08 | RF-08, CA-07 | P2 | Tasks | In Tasks |
| SQLR-09 | RF-09, CA-08 | P1 | Tasks | Implementing |
| SQLR-10 | RF-01, RF-03, RF-04, CA-09 | P1 | Tasks | In Tasks |

**ID format:** `[CATEGORY]-[NUMBER]` (ex.: `SQLR-01`)

**Status values:** Pending → In Design → In Tasks → Implementing → Verified

**Coverage:** 10 total, 10 mapped to tasks, 0 unmapped.

---

## Success Criteria

- [ ] Rerun com persistência ativa não gera erro de conexão entre execuções; lista e campo de mensagem seguem disponíveis (CA-01).
- [ ] Primeiro envio cria/reutiliza a conversa com mensagem da pessoa e resposta do assistente ordenadas; uso de tokens persistido (CA-02, CA-03).
- [ ] Retomar apresenta o histórico ordenado; excluir remove da lista e impede retomada (CA-04, CA-05).
- [ ] Dados e capacidades preservados na web e no terminal; sem persistência, nenhum arquivo local é criado (CA-06, CA-07).
- [ ] Caracteres especiais tratados como dado literal (CA-08).
- [ ] Cenário ponta a ponta: uma conversa ativa, duas mensagens ordenadas e um registro de uso, sem erro entre execuções (CA-09).
