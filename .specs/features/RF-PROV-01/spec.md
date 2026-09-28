# RF-PROV-01 — Troca de provedor de LLM em runtime pela tela — Specification

**Faixa de auto-sizing: Large.** 9 arquivos tocados, 5 fases, 15 requisitos rastreáveis. Os arquivos: `app_streamlit_core.py`, `chat_openai_memoria.py`, `app_streamlit.py`, `env.example`, `tests/test_app_streamlit_core.py`, `tests/test_app_streamlit_ui.py`, os 3 artefatos de `.specs/features/adicionar-tela-streamlit-659323ea/` e o PRD `docs/prds/PRD-2026-09-18-adicionar-front-end-em-streamlit-com-scripts-de-inicializacao-automatica.md`. Contagem feita depois de ler: os chamadores de `ChatComMemoria()` (`chat_openai_memoria.py:904,1044`, `app_streamlit_core.py:24-25`, `exemplos_avancados.py:22-358`) usam só argumentos nomeados, então `exemplos_avancados.py` não entra.

## Problem Statement

Trocar de provedor compatível com a API OpenAI hoje custa três passos fora do app: editar o `.env`, matar o processo do Streamlit e subir de novo. O restart é obrigatório porque `load_dotenv()` não sobrescreve variável já presente no ambiente (`chat_openai_memoria.py:18`) e o cliente é montado uma única vez em `ChatComMemoria.__init__()` (`chat_openai_memoria.py:227-230`). Cada troca mata a sessão do navegador e a conversa de teste tem de ser refeita. Pior: quando o provedor novo falha, `app_streamlit_core.py:sanitizar_erro()` devolve a constante fixa `MENSAGEM_ERRO_AMIGAVEL` (`app_streamlit_core.py:28,34`) e descarta o texto da exceção, então URL errada, chave inválida e modelo inexistente produzem a mesma tela.

## Goals

- [ ] Trocar de provedor pela barra lateral e conversar contra ele na mesma sessão de navegador, sem editar arquivo e sem reiniciar o processo.
- [ ] Distinguir URL errada de chave inválida de modelo inexistente pelo texto que aparece na tela, com toda credencial mascarada.
- [ ] Preservar a conversa em andamento quando a troca falha: validar e construir antes de descartar.

## Out of Scope

| Feature | Reason |
| ------- | ------ |
| Provedor AWS Bedrock nativo | Branch próprio, parado; provedor como backend é outro desenho |
| Troca de provedor na CLI | O `.env` antes de subir já é o fluxo natural lá |
| `temperature` e `max_tokens` no seletor | Continuam vindo do ambiente |
| Gravar o provedor na thread | Sem vínculo thread/provedor; `persistencia.py` e o schema não mudam |
| Persistir Perfil escolhido ou valores digitados | O override é de sessão |
| Dar nome ao Perfil digitado | Exige persistência, que está fora |
| Subir o app sem o ambiente obrigatório completo | `Padrão (.env)` é construído no start |
| Classificar o erro por categoria | A categoria perde o detalhe do diagnóstico |
| Descoberta de Perfis por varredura de prefixo | Nome errado sumiria sem erro |
| Allowlist de domínio na base URL | Contradiz apontar para qualquer endpoint (AD-006) |

---

## Assumptions & Open Questions

| Assumption / decision | Chosen default | Rationale | Confirmed? |
| --------------------- | -------------- | --------- | ---------- |
| Onde mora a lógica de Perfis | `app_streamlit_core.py`, sem módulo novo | O requisito autoriza as duas formas; o módulo já não importa `streamlit` e concentra `construir_sessao_chat()` (AD-003) | y |
| Ordem das fases | Erro mascarado primeiro, Perfis depois | Variação declarada defensável pelo requisito; `sanitizar_erro()` não depende do resto (AD-002) | y |
| Comando de gate | `.venv/Scripts/python.exe -m pytest tests/` | Medido: `python -m pytest` não tem pytest e `python3` não existe no Windows (AD-004) | y |
| Exceção técnica na tela x `[Norma 4.4.1.a, 4.4.1.b]` | Exibir, com mascaramento obrigatório | Diagnóstico é a entrega; app em `localhost`, operador único (AD-005) | y |
| Validação da base URL | Só esquema `http://` / `https://` | Allowlist de domínio impediria `http://localhost:11434`; SSRF residual aceito (AD-006) | y |
| Estrutura de cada Perfil | `dict` com `nome`, `base_url`, `api_key`, `modelo`, `disponivel`, `motivo_indisponivel` | Contrato ditado pelo requisito congelado | y |

**Open questions:** none - all resolved or logged above.

---

## User Stories

### P1: Erro do provedor legível na tela, com credencial mascarada ⭐ MVP

**User Story**: Como operador testando um provedor, quero ver o texto do erro que o provedor devolveu, para distinguir URL errada de chave inválida de modelo inexistente sem vazar a chave.

**Why P1**: Sem ele, toda troca que falhar produz a mesma tela e o diagnóstico é impossível. É pré-requisito de uso das demais histórias.

**Acceptance Criteria**:

1. WHEN sending a message raises an exception THEN the system SHALL display the exception text on screen, keep the conversation, keep the user's message visible and create no assistant bubble.
2. The system SHALL replace every occurrence of the active API key in that text with a mask before the text reaches the screen.
3. IF the active key has 12 characters or more THEN the system SHALL render it as its first 4 characters, then `***`, then its last 4 characters.
4. IF the active key has fewer than 12 characters THEN the system SHALL replace it entirely with `***`.
5. WHERE `OPENAI_API_KEY` is present in the environment and differs from the active key, the system SHALL mask it in the displayed text as well.
6. IF the submitted message is empty or whitespace-only THEN the system SHALL neither call the API nor change the history.
7. The system SHALL never write the displayed error text, the active key or a typed key to a log file, to the conversation export or to disk.

**Independent Test**: `enviar_mensagem_seguro()` com chat cuja `api_key` é `gsk_abc123XYZ789` e cujo `enviar_mensagem` levanta `AuthenticationError: Incorrect API key provided: gsk_abc123XYZ789` devolve texto com `Incorrect API key provided` e `gsk_***Z789`, sem a chave crua. Com `AppTest`, o `st.error` traz o mesmo texto e a fala do usuário continua visível sem bolha de assistente.

---

### P1: Perfis declarados no ambiente ⭐ MVP

**User Story**: Como operador, quero que o app leia do ambiente a lista de provedores alternativos, para escolher um deles sem digitar nada.

**Why P1**: É a fonte de dados do seletor. Sem ela não há o que escolher.

**Acceptance Criteria**:

1. The system SHALL offer a pure function that reads the environment and returns the list of Perfis, always starting with the `Padrão (.env)` entry built from `OPENAI_API_KEY`, `OPENAI_MODEL` and `OPENAI_BASE_URL`.
2. WHEN the `PERFIS` variable lists a name whose three-variable block is complete THEN the system SHALL include that Perfil as available, in the order the name appears in `PERFIS`.
3. IF the `PERFIS` variable is absent or empty THEN the system SHALL return only the `Padrão (.env)` entry.
4. IF a name listed in `PERFIS` has any of its three block variables absent or empty THEN the system SHALL include that Perfil marked unavailable, with a reason naming the Perfil and the missing variable, and SHALL NOT raise an exception.
5. IF a Perfil's base URL starts with neither `http://` nor `https://` THEN the system SHALL include that Perfil marked unavailable, with a reason naming the Perfil and the received URL.
6. IF the same name appears more than once in `PERFIS` THEN the system SHALL keep only the first occurrence.

**Independent Test**: Com `patch.dict("os.environ", …)`, `PERFIS=Groq,Ollama local`, bloco completo de `Groq` e bloco de `Ollama local` sem `PERFIL_OLLAMA_LOCAL_MODEL`: a lista tem 3 entradas, a primeira é `Padrão (.env)`, `Groq` vem `disponivel: True` e `Ollama local` vem `disponivel: False` com `PERFIL_OLLAMA_LOCAL_MODEL` no motivo.

---

### P1: Override de chave, modelo e base URL no construtor ⭐ MVP

**User Story**: Como desenvolvedor, quero injetar chave, modelo e base URL por parâmetro em `ChatComMemoria`, para construir uma sessão contra outro provedor sem mutar `os.environ`.

**Why P1**: É a porta que a troca pela tela usa. Sem ela a troca só seria possível mutando o ambiente, o que contaminaria o processo inteiro.

**Acceptance Criteria**:

1. The system SHALL accept `api_key`, `modelo` and `base_url` as optional parameters at the end of `ChatComMemoria.__init__()`, after `thread_id`, and the value received by parameter SHALL win over the environment value.
2. WHILE none of the three parameters is passed, the system SHALL behave exactly as today: same values read from the environment, same validations and same refusal messages citing the `.env`.
3. WHERE only part of the three parameters is passed, the system SHALL read from the environment only those not received by parameter.
4. WHEN `api_key` or `modelo` arrives by parameter THEN the system SHALL construct successfully even if the matching environment variable is absent.
5. IF `api_key` or `modelo` arrives by parameter empty or whitespace-only THEN the system SHALL refuse construction with a `ValueError` naming the parameter, and the message SHALL NOT contain the string `.env`.
6. IF `base_url` arrives by parameter starting with neither `http://` nor `https://` THEN the system SHALL refuse construction naming the received value, and the message SHALL NOT contain the string `.env`.
7. The system SHALL keep `OPENAI_TEMPERATURE` and `OPENAI_MAX_TOKENS` mandatory in the environment, with no parameter added for them.
8. The system SHALL write to `os.environ` in no code path.

**Independent Test**: Com a fixture `openai_mockado` de `tests/test_app_streamlit_core.py`, construir `ChatComMemoria()` e conferir os três atributos contra o ambiente; construir com os três parâmetros e conferir que vencem; construir com `api_key="   "` e conferir `ValueError` sem a string `.env`.

---

### P1: Troca de Perfil pela barra lateral ⭐ MVP

**User Story**: Como operador, quero escolher um Perfil na barra lateral e conversar contra ele, para testar outro provedor sem reiniciar o app.

**Why P1**: É a entrega observável do requisito.

**Acceptance Criteria**:

1. The system SHALL show a selector in the sidebar with the Perfis loaded from the environment, and SHALL show the active Perfil with its name, its base URL and its model, and never its key.
2. WHEN a browser session is created THEN the system SHALL build the chat session from the environment with `Padrão (.env)` selected.
3. WHEN an available Perfil different from the active one is chosen and confirmed THEN the system SHALL build a new `ChatComMemoria` with that Perfil's three values and only then discard the ongoing conversation.
4. WHILE the chosen Perfil is the one already active, the system SHALL preserve the session object and the ongoing conversation, and SHALL build no `ChatComMemoria`.
5. IF the chosen Perfil is marked unavailable THEN the system SHALL display the reason naming the missing variable and SHALL NOT swap the session.
6. IF building the new session is refused by `ChatComMemoria` validation THEN the system SHALL display the refusal and preserve the previous session object and the ongoing conversation.
7. WHEN a Perfil swap succeeds THEN the system SHALL replace `st.session_state["chat"]`, reset `st.session_state["thread_id"]` and keep the same `gerenciador`.

**Independent Test**: Com `AppTest` e `patch` em `app_streamlit_core.construir_sessao_chat`, escolher `Groq` e confirmar: a chamada recebe base URL, chave e modelo de `Groq`, a área de conversa esvazia, a barra lateral mostra `Groq` com base URL e modelo, e nenhum texto renderizado contém a chave.

---

### P2: Perfil digitado na barra lateral

**User Story**: Como operador, quero digitar base URL, chave e modelo na hora, para testar um provedor que não está declarado no `.env`.

**Why P2**: O caminho declarado no ambiente já cobre o uso repetido; o digitado atende o teste pontual e depende do mesmo mecanismo de troca da P1.

**Acceptance Criteria**:

1. The system SHALL offer a typed-Perfil entry in the selector, with three text fields for base URL, key and model.
2. WHEN the typed entry is confirmed with all three fields filled and a valid base URL THEN the system SHALL build a new `ChatComMemoria` with the typed values, building before discarding.
3. IF any of the three fields is empty or whitespace-only on confirmation THEN the system SHALL flag the required field and SHALL NOT swap the session.
4. IF the typed base URL starts with neither `http://` nor `https://` THEN the system SHALL display an error naming the received URL and SHALL NOT swap the session.
5. The system SHALL render the key field as masked input and SHALL NOT display, echo, persist to disk or log the typed value.

**Independent Test**: Com `AppTest`, confirmar a entrada digitada com `https://api.groq.com/openai/v1`, chave e modelo: `construir_sessao_chat` recebe exatamente esses três valores e a conversa esvazia. Repetir com um campo em branco e com `api.groq.com/openai/v1`: o objeto de sessão é o mesmo de antes e nenhum texto renderizado contém a chave digitada.

---

## Edge Cases

- IF a `PERFIS` name has non-alphanumeric characters THEN the system SHALL normalize it to the prefix `PERFIL_<NOME>_`, uppercase, every non-alphanumeric character becoming `_` (`Ollama local` becomes `PERFIL_OLLAMA_LOCAL_`).
- WHEN `OPENAI_BASE_URL` is undefined THEN the system SHALL build the `Padrão (.env)` entry with `base_url` equal to `None` and `disponivel` true, preserving today's default OpenAI endpoint behaviour.
- IF a Perfil is unavailable THEN the system SHALL tolerate `None` in its `base_url`, `api_key` and `modelo`.
- WHEN the browser page is reloaded THEN the system SHALL return to `Padrão (.env)`, since the chosen Perfil lives only in `st.session_state`.
- WHEN a Perfil is swapped before any message is sent THEN the system SHALL leave no orphan thread, because the thread is created on the first user message in `ChatComMemoria._adicionar_ao_historico()`.
- WHEN a thread is resumed by `app_streamlit_core.py:retomar_thread()` THEN the system SHALL use the Perfil selected at that moment, not the one that generated the thread.
- WHILE persistence is off, the system SHALL keep ignoring `gerenciador` and `thread_id` in `construir_sessao_chat()`, as today.

---

## Requirement Traceability

| Requirement ID | Origem | Story | Phase | Status |
| -------------- | ------ | ----- | ----- | ------ |
| PROV-01 | RF-PROV-01 / CA-PROV-10 | P1: Erro do provedor legível | 1 | Pending |
| PROV-02 | CA-PROV-10 / CA-PROV-11 | P1: Erro do provedor legível | 1 | Pending |
| PROV-03 | CA-PROV-11 | P1: Erro do provedor legível | 1 | Pending |
| PROV-04 | CA-PROV-10 | P1: Erro do provedor legível | 1 | Pending |
| PROV-05 | CA-PROV-01 | P1: Perfis no ambiente | 2 | Pending |
| PROV-06 | CA-PROV-01 | P1: Perfis no ambiente | 2 | Pending |
| PROV-07 | CA-PROV-02 | P1: Perfis no ambiente | 2 | Pending |
| PROV-08 | CA-PROV-03 | P1: Override no construtor | 3 | Done |
| PROV-09 | CA-PROV-04 | P1: Override no construtor | 3 | Done |
| PROV-10 | CA-PROV-05 | P1: Troca pela barra lateral | 4 | Pending |
| PROV-11 | CA-PROV-06 | P1: Troca pela barra lateral | 4 | Pending |
| PROV-12 | CA-PROV-07 | P1: Troca pela barra lateral | 4 | Pending |
| PROV-13 | CA-PROV-08 | P2: Perfil digitado | 5 | Pending |
| PROV-14 | CA-PROV-09 | P2: Perfil digitado | 5 | Pending |
| PROV-15 | CA-PROV-11 | P1: Erro do provedor legível | 1 | Pending |

**ID format:** `PROV-[NUMBER]`. A coluna `Origem` liga ao requisito congelado `docs/requisitos/RF-PROV-01.md`.

**Coverage:** 15 total, 15 mapeados para fases, 0 sem mapeamento.

---

## Security Requirements

Derivados com `dev-sec-ops-ciclo`, modo R. Categoria: integração com API externa e segredo em memória. Exposição: `localhost`, operador único. Dado tratado: credencial de provedor de LLM e conteúdo da conversa.

1. The system SHALL keep every API key out of the screen, the `logs/` files, the conversation export and any file on disk, in every mode including debug. `[Norma 4.4.1.f, 4.4.1.o, 4.4.2.1.d]` `[ASVS V14.6]`
2. The system SHALL mask every API key occurrence in any error text before it reaches the screen, 4 + `***` + 4 above 12 characters and full `***` below it. `[Norma 4.4.1.a, 4.4.1.f]`
3. The system SHALL render the typed key field as masked input and SHALL NOT echo the typed value. `[Norma 4.4.2.1.e]`
4. The system SHALL validate the base URL against the `http://` / `https://` allowlist before building the client, on the environment path and on the typed path. `[Norma 4.4.13.1.a, 4.4.13.1.q, 4.4.13.1.u]`
5. The system SHALL carry credentials by constructor parameter only and SHALL write to `os.environ` in no code path. `[Norma 4.4.2.1.d]` `[ASVS V14.6]`
6. The system SHALL display the active Perfil's name, base URL and model, so the operator knows which external endpoint receives the conversation. `[sem cláusula direta na norma — referencial: OWASP LLM02]`

Exceção consciente em AD-005: exibir o texto técnico contraria `[Norma 4.4.1.a, 4.4.1.b]`. Mitigação: mascaramento obrigatório (item 2) e uso restrito a `localhost`.

---

## Success Criteria

- [ ] Trocar de `Padrão (.env)` para um Perfil declarado e conversar contra ele sem editar arquivo e sem reiniciar o processo, na mesma sessão do navegador.
- [ ] URL errada, chave inválida e modelo inexistente produzem três textos distintos na tela, nenhum com credencial crua.
- [ ] Toda troca recusada deixa a conversa anterior intacta.
- [ ] A suíte vai de 112 testes verdes para 112 mais os novos, sem deleção silenciosa.
