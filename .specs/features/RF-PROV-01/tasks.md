# RF-PROV-01 — Troca de provedor de LLM em runtime pela tela — Tasks

## Execution Protocol (MANDATORY -- do not skip)

Implement these tasks with the `tlc-spec-driven-ciclo` skill: **activate it by name and follow its Execute flow and Critical Rules.** Do not search for skill files by filesystem path. The skill is the source of truth for the full flow (per-task cycle, adequacy review, Verifier, discrimination sensor).

**If the skill cannot be activated, STOP and tell the user - do not proceed without it.**

---

**Spec**: `.specs/features/RF-PROV-01/spec.md`
**Design**: `.specs/features/RF-PROV-01/design.md`
**Status**: Draft

---

## Test Coverage Matrix

> Gerada do codebase, das diretrizes do projeto e do spec. Diretrizes encontradas: `AGENTS.md:247-249` (padrão de extensão por parâmetro de construtor). Não há `pyproject.toml`, `pytest.ini`, CI nem linter configurado, então não há limiar de cobertura declarado — strong defaults aplicados. Convenção inferida de `tests/test_app_streamlit_core.py`, `tests/test_app_streamlit_ui.py` e `tests/test_readme_streamlit.py`.

| Code Layer | Required Test Type | Coverage Expectation | Location Pattern | Run Command |
| ---------- | ------------------ | -------------------- | ---------------- | ----------- |
| Núcleo UI-agnóstico (`app_streamlit_core.py`) | unit | Todos os branches; 1:1 com os ACs de PROV-01 a PROV-07 e PROV-10 a PROV-14; todo edge case listado no spec | `tests/test_app_streamlit_core.py` | `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py` |
| Domínio de chat (`chat_openai_memoria.py`) | unit | Todos os branches de precedência e recusa; 1:1 com PROV-08 e PROV-09, caminho com e sem parâmetro | `tests/test_app_streamlit_core.py` | `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py` |
| Wiring Streamlit (`app_streamlit.py`) | integration | Todo fluxo de tela em escopo: troca bem-sucedida, recusa, reseleção, Perfil digitado, erro na tela — happy path, edge e falha | `tests/test_app_streamlit_ui.py` | `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_ui.py` |
| Configuração e documentação (`env.example`, PRD, `.specs/`) | unit | Presença do contrato declarado em arquivo (bloco `PERFIS`, nota de superação) | `tests/test_docs_*.py`, `tests/test_requirements_streamlit.py` | `.venv/Scripts/python.exe -m pytest tests/` |

Os testes de núcleo usam `patch.dict("os.environ", …)` e a fixture `openai_mockado` (`patch("chat_openai_memoria.OpenAI")` + `patch("chat_openai_memoria.load_dotenv")`), ambos já presentes em `tests/test_app_streamlit_core.py`. Os de tela usam `streamlit.testing.v1.AppTest` com `pytest.importorskip("streamlit")` e `patch` em `app_streamlit_core.construir_sessao_chat` e `app_streamlit_core.persistencia_ativa`, como `tests/test_app_streamlit_ui.py` já faz. Os de documentação seguem `tests/test_readme_streamlit.py`: leitura do arquivo com `encoding="utf-8"` explícito e assertiva de substring.

## Gate Check Commands

> Gerada do codebase. O interpretador é o do `.venv` por medição (AD-004): `python -m pytest` devolve `No module named pytest` nesta máquina e `python3` não existe no Windows. O `.venv` tem pytest 9.1.1 e roda 112 testes verdes.

| Gate Level | When to Use | Command |
| ---------- | ----------- | ------- |
| Quick | Após tarefas que tocam só o núcleo UI-agnóstico ou o domínio de chat | `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py` |
| Full | Após tarefas de tela, de configuração, de documentação ou que mexam em contrato compartilhado | `.venv/Scripts/python.exe -m pytest tests/` |
| Build | Ao concluir cada fase | `.venv/Scripts/python.exe -m pytest tests/` |

---

## Execution Plan

Phases are ordered and run sequentially - each phase completes before the next begins, and tasks within a phase execute in order.

<!-- FASE: 1 -->
### Phase 1: Erro do provedor na tela com a chave mascarada

Primeira fase por AD-002: sem o texto da exceção, a primeira troca com URL errada não se distingue de chave inválida. `sanitizar_erro()` não depende de nenhuma outra parte da entrega. A superação da decisão da mensagem genérica na documentação entra aqui porque é a mesma mudança.

```
T1 → T2 → T3 → T4 → T5
```

<!-- FASE: 2 -->
### Phase 2: Carga de Perfis declarados no ambiente

Função pura sobre `os.environ`, sem tocar em tela nem em construtor. É a fonte de dados do seletor.

```
T6 → T7 → T8 → T9
```

<!-- FASE: 3 -->
### Phase 3: Override de chave, modelo e base URL no construtor

A porta que a troca pela tela usa. Injeção por parâmetro, nunca mutação de `os.environ`.

```
T10 → T11
```

<!-- FASE: 4 -->
### Phase 4: Troca de Perfil pela barra lateral

Junta a Fase 2 com a Fase 3 e entrega o gesto observável. A ordem valida, constrói e só então descarta.

```
T12 → T13 → T14 → T15
```

<!-- FASE: 5 -->
### Phase 5: Perfil digitado na barra lateral

Reusa o mecanismo de troca da Fase 4 com valores vindos de três campos de texto.

```
T16 → T17 → T18
```

---

## Task Breakdown

### T1: Criar `mascarar_chave()` no núcleo

**What**: Função pura que recebe um texto e um iterável de chaves e devolve o texto com cada chave não vazia substituída pela máscara: 4 primeiros caracteres + `***` + 4 últimos quando a chave tem 12 caracteres ou mais, `***` inteiro quando tem menos.
**Where**: `app_streamlit_core.py`
**Depends on**: None
**Reuses**: nada; função nova sem dependência
**Requirement**: PROV-02, PROV-03

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Chave de 12 caracteres ou mais vira 4 + `***` + 4 (`gsk_abc123XYZ789` → `gsk_***Z789`)
- [x] Chave com menos de 12 caracteres vira `***` inteiro (`ollama` → `***`)
- [x] Chave `None` ou vazia é ignorada sem erro; texto sem ocorrência volta intacto
- [x] Testes novos em `tests/test_app_streamlit_core.py` cobrem o piso de 12 caracteres nas duas direções, inclusive o limite exato
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [x] Test count: os testes atuais do arquivo continuam passando e ao menos 3 novos passam (sem deleções silenciosas)

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): adiciona mascaramento parcial de chave de API`

---

### T2: Fazer `sanitizar_erro()` devolver o texto da exceção mascarado

**What**: Trocar o retorno fixo de `sanitizar_erro()` pelo `str(exc)` com as chaves mascaradas, aceitando o objeto de chat para obter a chave ativa; `enviar_mensagem_seguro()` passa o chat adiante; a constante `MENSAGEM_ERRO_AMIGAVEL` é removida.
**Where**: `app_streamlit_core.py`
**Depends on**: T1
**Reuses**: `mascarar_chave()` de T1, `enviar_mensagem_seguro()` existente
**Requirement**: PROV-01, PROV-02, PROV-04, PROV-15

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O texto devolvido contém o conteúdo da exceção (`Incorrect API key provided`) e não a chave crua
- [x] A chave **ativa** vem do atributo `api_key` do objeto de chat, não de `os.environ`
- [x] `OPENAI_API_KEY` também é mascarada quando existe e difere da ativa
- [x] Texto vazio ou só espaços continua não chamando a API e não alterando o histórico
- [x] `MENSAGEM_ERRO_AMIGAVEL` não existe mais no módulo
- [x] Os três testes de `tests/test_app_streamlit_core.py` que travavam o texto fixo passam a travar a mascaração, sem serem apagados
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: 112 testes atuais menos as assertivas reescritas, mais ao menos 3 novos, todos passando

**Tests**: unit
**Gate**: full

**Commit**: `feat(core): exibe o texto da excecao do provedor com a chave mascarada`

---

### T3: Ajustar os testes de tela que travavam a mensagem fixa

**What**: Reescrever `test_app_erro_sanitizado_aparece_amigavel()` e `test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append()` para assertar o texto técnico mascarado no `st.error`, mantendo a assertiva de fala do usuário visível sem bolha de assistente.
**Where**: `tests/test_app_streamlit_ui.py`
**Depends on**: T2
**Reuses**: padrão `AppTest` + `patch` já usado no arquivo
**Requirement**: PROV-01, PROV-15

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O `st.error` da tela contém o texto da exceção e não contém a chave crua
- [x] A fala do usuário continua visível na falha, sem bolha de assistente
- [x] Os mocks que usavam o texto fixo apenas como retorno, sem assertiva, seguem válidos
- [x] Nenhum teste é apagado ou marcado como `skip`
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: a suíte inteira passa, contagem igual ou maior que 112

**Tests**: integration
**Gate**: full

**Commit**: `test(ui): trava o texto tecnico mascarado no erro da tela`

---

### T4: Registrar a superação nos artefatos da feature da tela Streamlit

**What**: Acrescentar nota de superação por RF-PROV-01 nos três artefatos de `.specs/features/adicionar-tela-streamlit-659323ea/` que declaram a mensagem genérica como requisito, sem apagar o histórico.
**Where**: `.specs/features/adicionar-tela-streamlit-659323ea/`
**Depends on**: T3
**Reuses**: padrão de assertiva de documento de `tests/test_readme_streamlit.py`
**Requirement**: PROV-01

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O AC da mensagem amigável no `spec.md` daquela feature traz a nota citando RF-PROV-01, com o texto original preservado
- [x] A descrição de `sanitizar_erro` no `design.md` daquela feature traz a nota
- [x] A linha de evidência do `validation.md` daquela feature traz a nota
- [x] Teste novo em `tests/test_docs_superacao_rf_prov_01.py` confirma a presença da nota nos três arquivos
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: ao menos 3 testes novos passam e a suíte inteira segue verde

**Tests**: unit
**Gate**: full

**Commit**: `docs(specs): registra superacao da mensagem generica por RF-PROV-01`

---

### T5: Registrar a superação no PRD da tela Streamlit

**What**: Acrescentar nota de superação por RF-PROV-01 nos pontos do PRD que declaram o erro amigável sem detalhes como critério (CA-07 e as menções de tratamento de erro), sem apagar o texto original.
**Where**: `docs/prds/PRD-2026-09-18-adicionar-front-end-em-streamlit-com-scripts-de-inicializacao-automatica.md`
**Depends on**: T4
**Reuses**: teste criado em T4
**Requirement**: PROV-01

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O critério CA-07 do PRD traz a nota citando RF-PROV-01 e a mitigação por mascaramento
- [x] O texto original do PRD não é apagado
- [x] `tests/test_docs_superacao_rf_prov_01.py` ganha a assertiva do PRD
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: ao menos 1 teste novo passa e a suíte inteira segue verde

**Tests**: unit
**Gate**: full

**Commit**: `docs(prd): registra superacao do erro generico por RF-PROV-01`

---

### T6: Criar `carregar_perfis()` com a entrada `Padrão (.env)` e os Perfis completos

**What**: Função pura que lê `os.environ` e devolve a lista de Perfis como dicionários, sempre começando por `Padrão (.env)` (montado de `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`) e seguindo com cada nome de `PERFIS` cujo bloco de três variáveis está completo, na ordem declarada.
**Where**: `app_streamlit_core.py`
**Depends on**: None
**Reuses**: `os.getenv`, padrão de leitura de ambiente de `persistencia_ativa()`
**Requirement**: PROV-05

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] A primeira entrada é sempre `Padrão (.env)`, com `disponivel` verdadeiro e `base_url` igual a `None` quando `OPENAI_BASE_URL` não está definida
- [x] Cada Perfil é um `dict` com `nome`, `base_url`, `api_key`, `modelo`, `disponivel`, `motivo_indisponivel`
- [x] O nome vira prefixo com maiúsculas e todo caractere não alfanumérico trocado por `_` (`Ollama local` → `PERFIL_OLLAMA_LOCAL_`)
- [x] A ordem da lista segue a ordem dos nomes em `PERFIS`
- [x] Testes novos com `patch.dict("os.environ", …)` cobrem bloco completo, ordem e normalização do nome
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [x] Test count: ao menos 3 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): carrega perfis de provedor declarados no ambiente`

---

### T7: Marcar como indisponível o Perfil com bloco incompleto

**What**: Em `carregar_perfis()`, incluir na lista o Perfil cujo bloco tem variável ausente ou vazia com `disponivel` falso e `motivo_indisponivel` nomeando o Perfil e a variável que falta, sem levantar exceção.
**Where**: `app_streamlit_core.py`
**Depends on**: T6
**Reuses**: `carregar_perfis()` de T6
**Requirement**: PROV-06

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Apagar `PERFIL_OLLAMA_LOCAL_MODEL` produz `disponivel: False` com `PERFIL_OLLAMA_LOCAL_MODEL` e o nome do Perfil no motivo
- [x] O Perfil indisponível continua **na** lista, e não ausente dela
- [x] Nenhuma exceção é levantada; os três valores podem vir `None`
- [x] Variável presente mas vazia ou só com espaços conta como ausente
- [x] Teste novo discrimina as duas mutações: Perfil ausente da lista e Perfil com modelo `None` marcado disponível
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [x] Test count: ao menos 2 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): marca perfil de bloco incompleto como indisponivel`

---

### T8: Recusar URL sem esquema, deduplicar nome e tratar `PERFIS` ausente

**What**: Em `carregar_perfis()`, marcar como indisponível o Perfil cuja base URL não começa com `http://` nem `https://` (motivo nomeando o Perfil e a URL recebida), manter só a primeira ocorrência de nome repetido, e devolver apenas `Padrão (.env)` quando `PERFIS` está ausente ou vazia.
**Where**: `app_streamlit_core.py`
**Depends on**: T7
**Reuses**: regra de esquema de `chat_openai_memoria.py:187-195`
**Requirement**: PROV-07

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `api.groq.com/openai/v1` produz `disponivel: False` com o nome do Perfil e a URL recebida no motivo
- [x] `PERFIS=Groq,Groq` produz exatamente uma entrada `Groq`
- [x] `PERFIS` ausente ou string vazia produz lista de comprimento 1 com só `Padrão (.env)`
- [x] Testes novos olham `disponivel`, não apenas o comprimento da lista, e discriminam a troca da checagem de esquema por `if base_url:`
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [x] Test count: ao menos 3 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): recusa url sem esquema e deduplica nome de perfil`

---

### T9: Documentar o bloco `PERFIS` no `env.example`

**What**: Acrescentar ao `env.example` o bloco comentado de declaração de Perfis, com `PERFIS` e o trio `PERFIL_<NOME>_BASE_URL`, `PERFIL_<NOME>_API_KEY`, `PERFIL_<NOME>_MODEL`, explicando a normalização do nome e a obrigatoriedade da chave mesmo em provedor local.
**Where**: `env.example`
**Depends on**: T8
**Reuses**: estilo de comentário das seções existentes do arquivo
**Requirement**: PROV-05

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] O arquivo traz `PERFIS=` com o exemplo `Groq,Ollama local` comentado
- [x] O trio de variáveis de `Groq` aparece como exemplo
- [x] O comentário registra que a chave é obrigatória em todo Perfil, inclusive provedor local
- [x] Nenhum valor real de chave entra no arquivo
- [x] Teste novo em `tests/test_docs_superacao_rf_prov_01.py` confirma a presença do bloco no `env.example`
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: ao menos 1 teste novo passa e a suíte inteira segue verde

**Tests**: unit
**Gate**: full

**Commit**: `docs(env): documenta o bloco de perfis de provedor`

---

### T10: Aceitar `api_key`, `modelo` e `base_url` no construtor com parâmetro vencendo o ambiente

**What**: Acrescentar os três parâmetros opcionais no fim da assinatura de `ChatComMemoria.__init__()`, depois de `thread_id`, com a precedência parâmetro vence ambiente e `None` significando "leia do ambiente", na mesma forma dos quatro parâmetros opcionais atuais.
**Where**: `chat_openai_memoria.py`
**Depends on**: None
**Reuses**: padrão de precedência de `chat_openai_memoria.py:200-224`, bifurcação do cliente em `chat_openai_memoria.py:227-230`
**Requirement**: PROV-08

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Sem os três parâmetros, os atributos valem exatamente o que o ambiente declara, com as mesmas validações e mensagens citando o `.env`
- [x] Com os três passados, os atributos valem os valores passados e o ambiente é ignorado para eles
- [x] Passando só `base_url`, `api_key` e `modelo` continuam vindo do ambiente
- [x] Com `OPENAI_API_KEY` ausente e `api_key` por parâmetro, a construção conclui sem exceção; o mesmo para `OPENAI_MODEL` e `modelo`
- [x] `OPENAI_TEMPERATURE` e `OPENAI_MAX_TOKENS` continuam obrigatórios no ambiente e falham como hoje
- [x] Nenhum caminho de código escreve em `os.environ`
- [x] Testes novos cobrem o caminho **sem** parâmetro e discriminam a inversão da precedência
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: ao menos 4 testes novos passam e a suíte inteira segue verde

**Tests**: unit
**Gate**: full

**Commit**: `feat(chat): aceita chave, modelo e base url por parametro do construtor`

---

### T11: Recusar valor inválido por parâmetro sem mandar editar o `.env`

**What**: Em `ChatComMemoria.__init__()`, recusar com `ValueError` a `api_key` ou o `modelo` que chegam por parâmetro vazios ou só com espaços, nomeando o parâmetro, e a `base_url` por parâmetro sem esquema, nomeando o valor recebido — nenhuma dessas mensagens contendo a string `.env`.
**Where**: `chat_openai_memoria.py`
**Depends on**: T10
**Reuses**: a mesma regra de esquema de `chat_openai_memoria.py:187-195`, sem criar uma segunda validação de URL
**Requirement**: PROV-09

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] `ChatComMemoria(api_key="   ")` levanta `ValueError` citando `api_key`, sem a string `.env`
- [x] `ChatComMemoria(modelo="")` idem, citando `modelo`
- [x] `ChatComMemoria(base_url="api.groq.com/openai/v1")` recusa citando o valor recebido, sem a string `.env`
- [x] Valor inválido vindo do **ambiente** continua produzindo a mensagem que cita o `.env`, como hoje (exceto `OPENAI_BASE_URL`, que nunca citou `.env` — AD-008)
- [x] Testes novos discriminam o reaproveitamento da mensagem do ambiente e a checagem `is None` no lugar de valor em branco
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [x] Test count: ao menos 4 testes novos passam e a suíte inteira segue verde

**Tests**: unit
**Gate**: full

**Commit**: `feat(chat): recusa parametro invalido sem instruir a editar o .env`

---

### T12: Repassar chave, modelo e base URL em `construir_sessao_chat()`

**What**: Acrescentar `api_key`, `modelo` e `base_url` a `construir_sessao_chat()` e repassá-los a `ChatComMemoria`, preservando a condição de `persistencia_ativa()` que hoje decide se `gerenciador` e `thread_id` são repassados.
**Where**: `app_streamlit_core.py`
**Depends on**: None
**Reuses**: `construir_sessao_chat()` e `persistencia_ativa()` existentes, construtor de T10
**Requirement**: PROV-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [x] Os três valores chegam a `ChatComMemoria` quando informados
- [x] Sem persistência, `gerenciador` e `thread_id` continuam ignorados
- [x] Chamada sem os três valores mantém o comportamento atual
- [x] `retomar_thread()` continua funcionando e usa o Perfil informado no momento
- [x] Testes novos conferem os argumentos recebidos pelo construtor mockado
- [x] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [x] Test count: ao menos 3 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): repassa perfil ativo para a construcao da sessao`

---

### T13: Criar `trocar_perfil()` que valida e constrói antes de qualquer descarte

**What**: Função no núcleo que recebe o Perfil escolhido, recusa o indisponível devolvendo o motivo, tenta construir a sessão nova e devolve `(chat_novo, None)` no sucesso ou `(None, motivo)` na recusa, sem nunca tocar em estado de sessão.
**Where**: `app_streamlit_core.py`
**Depends on**: T12
**Reuses**: `construir_sessao_chat()` de T12, `carregar_perfis()` da Fase 2
**Requirement**: PROV-10, PROV-11

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Perfil indisponível devolve `(None, motivo)` com a variável faltante no motivo, sem chamar o construtor
- [ ] `ValueError` do construtor é capturada e devolvida como motivo, sem propagar
- [ ] Sucesso devolve o objeto novo; a função não lê nem escreve `st.session_state`
- [ ] A função não importa `streamlit`
- [ ] Testes novos discriminam a inversão de ordem: construção antes da validação
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [ ] Test count: ao menos 3 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): valida e constroi a sessao nova antes de qualquer descarte`

---

### T14: Ligar o seletor de Perfis e o resumo do Perfil ativo na barra lateral

**What**: No wiring, exibir o seletor com os Perfis carregados do ambiente, o resumo do Perfil ativo (nome, base URL, modelo, nunca a chave) e o botão de confirmar que, no sucesso, substitui `st.session_state["chat"]`, zera `["thread_id"]` e mantém o mesmo `gerenciador`.
**Where**: `app_streamlit.py`
**Depends on**: T13
**Reuses**: `inicializar_estado()`, padrão de `st.selectbox` + botão já usado no bloco de threads
**Requirement**: PROV-10

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] A sessão nova recebe base URL, chave e modelo do Perfil escolhido
- [ ] A área de conversa esvazia após a troca bem-sucedida
- [ ] A barra lateral mostra o Perfil ativo com nome, base URL e modelo
- [ ] Nenhum texto renderizado na tela contém a chave do Perfil
- [ ] Na criação da sessão do navegador, `Padrão (.env)` está selecionado e a sessão vem do ambiente
- [ ] O `gerenciador` é o mesmo objeto antes e depois da troca
- [ ] Testes novos com `AppTest` discriminam a sessão construída sem repassar os três valores e a impressão da chave no resumo
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [ ] Test count: ao menos 4 testes novos passam e a suíte inteira segue verde

**Tests**: integration
**Gate**: full

**Commit**: `feat(ui): adiciona seletor de perfil de provedor na barra lateral`

---

### T15: Preservar a sessão na reseleção e na recusa

**What**: No wiring, retornar antes de qualquer reconstrução quando o Perfil escolhido é o já ativo, e exibir o motivo devolvido por `trocar_perfil()` preservando a sessão anterior e a conversa quando a troca é recusada.
**Where**: `app_streamlit.py`
**Depends on**: T14
**Reuses**: `trocar_perfil()` de T13, `st.error` já usado no caminho de falha de envio
**Requirement**: PROV-11, PROV-12

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Reselecionar o Perfil ativo deixa o objeto de sessão idêntico e não chama o construtor nenhuma vez
- [ ] Perfil indisponível exibe o motivo nomeando a variável faltante e não troca a sessão
- [ ] Recusa da validação de `ChatComMemoria` aparece na tela e a sessão anterior é preservada
- [ ] A conversa em andamento continua visível nos dois casos de recusa
- [ ] Testes novos assertam identidade do objeto de sessão e contagem de chamadas do construtor, não só a presença da mensagem
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [ ] Test count: ao menos 4 testes novos passam e a suíte inteira segue verde

**Tests**: integration
**Gate**: full

**Commit**: `feat(ui): preserva a sessao na reselecao e na recusa de perfil`

---

### T16: Validar os três campos do Perfil digitado no núcleo

**What**: Função no núcleo que recebe base URL, chave e modelo digitados e devolve o Perfil montado ou o motivo da recusa: campo vazio ou só com espaços nomeia o campo obrigatório, e base URL sem `http://` nem `https://` nomeia a URL recebida.
**Where**: `app_streamlit_core.py`
**Depends on**: None
**Reuses**: regra de esquema de T8, contrato de Perfil da Fase 2
**Requirement**: PROV-13, PROV-14

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Três campos preenchidos com URL válida devolvem o Perfil com exatamente esses valores
- [ ] Qualquer campo vazio ou só com espaços devolve recusa nomeando o campo
- [ ] `api.groq.com/openai/v1` devolve recusa contendo a URL recebida
- [ ] A função não registra em log nem grava em disco o valor digitado
- [ ] Testes novos discriminam a checagem de `None` no lugar de valor em branco e a troca do esquema por um truthy da string
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/test_app_streamlit_core.py`
- [ ] Test count: ao menos 4 testes novos passam

**Tests**: unit
**Gate**: quick

**Commit**: `feat(core): valida os campos do perfil digitado`

---

### T17: Ligar a entrada de Perfil digitado na barra lateral

**What**: No wiring, acrescentar ao seletor a entrada de Perfil digitado com três campos de texto — o da chave com entrada mascarada — e, na confirmação válida, construir a sessão nova pelos valores digitados antes de descartar a anterior.
**Where**: `app_streamlit.py`
**Depends on**: T16
**Reuses**: `trocar_perfil()` de T13, validação de T16, `st.text_input(type="password")`
**Requirement**: PROV-13, PROV-14

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] O seletor oferece a entrada digitada com os três campos
- [ ] O campo da chave usa entrada mascarada na tela
- [ ] Confirmação válida constrói a sessão com exatamente os três valores digitados e a conversa esvazia
- [ ] Os valores digitados vivem só em `st.session_state`, sem gravação em disco
- [ ] Testes novos com `AppTest` conferem os argumentos recebidos pelo construtor mockado
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [ ] Test count: ao menos 3 testes novos passam e a suíte inteira segue verde

**Tests**: integration
**Gate**: full

**Commit**: `feat(ui): adiciona entrada de perfil digitado na barra lateral`

---

### T18: Não trocar a sessão na recusa do Perfil digitado e nunca ecoar a chave

**What**: No wiring, sinalizar o campo obrigatório e exibir o erro de URL sem esquema sem trocar a sessão, garantindo que nenhum texto renderizado — inclusive resumo de confirmação — contenha a chave digitada.
**Where**: `app_streamlit.py`
**Depends on**: T17
**Reuses**: retorno de recusa de T16, `st.error` do caminho de falha
**Requirement**: PROV-14

**Tools**:

- MCP: NONE
- Skill: NONE

**Done when**:

- [ ] Campo vazio ou só com espaços sinaliza o obrigatório, o objeto de sessão é o mesmo de antes e a conversa continua visível
- [ ] URL digitada sem esquema exibe erro contendo a URL recebida e não troca a sessão
- [ ] Nenhum texto renderizado na tela contém a chave digitada, em nenhum dos caminhos
- [ ] Testes novos assertam identidade do objeto de sessão e ausência da chave no conteúdo renderizado, discriminando o eco em resumo de confirmação
- [ ] Gate check passes: `.venv/Scripts/python.exe -m pytest tests/`
- [ ] Test count: ao menos 4 testes novos passam e a suíte inteira segue verde

**Tests**: integration
**Gate**: full

**Commit**: `feat(ui): recusa perfil digitado invalido sem trocar a sessao`

---

## Phase Execution Map

```
Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5
```

Execução estritamente sequencial: um agente por vez, uma task por vez, na ordem. As fases 2 e 3 são independentes entre si em conteúdo, mas rodam em sequência porque a Fase 4 depende das duas e o laço abre uma sessão por marcador de fase.

---

## Task Granularity Check

| Task | Scope | Status |
| ---- | ----- | ------ |
| T1 | 1 função nova | ✅ Granular |
| T2 | 2 funções coesas no mesmo arquivo | ✅ Granular |
| T3 | 1 arquivo de teste | ✅ Granular |
| T4 | 1 diretório de artefatos de uma feature | ✅ Granular |
| T5 | 1 arquivo de PRD | ✅ Granular |
| T6 | 1 função nova | ✅ Granular |
| T7 | 1 branch da função de T6 | ✅ Granular |
| T8 | 3 regras coesas da mesma função | ✅ Granular |
| T9 | 1 arquivo de configuração | ✅ Granular |
| T10 | 1 assinatura + precedência | ✅ Granular |
| T11 | 1 bloco de validação | ✅ Granular |
| T12 | 1 função | ✅ Granular |
| T13 | 1 função nova | ✅ Granular |
| T14 | 1 bloco de widgets | ✅ Granular |
| T15 | 2 guardas no mesmo bloco | ✅ Granular |
| T16 | 1 função nova | ✅ Granular |
| T17 | 1 bloco de widgets | ✅ Granular |
| T18 | 2 guardas no mesmo bloco | ✅ Granular |

---

## Diagram-Definition Cross-Check

| Task | Depends On (task body) | Diagram Shows | Status |
| ---- | ---------------------- | ------------- | ------ |
| T1 | None | - | ✅ Match |
| T2 | T1 | T1 → T2 | ✅ Match |
| T3 | T2 | T2 → T3 | ✅ Match |
| T4 | T3 | T3 → T4 | ✅ Match |
| T5 | T4 | T4 → T5 | ✅ Match |
| T6 | None | - | ✅ Match |
| T7 | T6 | T6 → T7 | ✅ Match |
| T8 | T7 | T7 → T8 | ✅ Match |
| T9 | T8 | T8 → T9 | ✅ Match |
| T10 | None | - | ✅ Match |
| T11 | T10 | T10 → T11 | ✅ Match |
| T12 | None | - | ✅ Match |
| T13 | T12 | T12 → T13 | ✅ Match |
| T14 | T13 | T13 → T14 | ✅ Match |
| T15 | T14 | T14 → T15 | ✅ Match |
| T16 | None | - | ✅ Match |
| T17 | T16 | T16 → T17 | ✅ Match |
| T18 | T17 | T17 → T18 | ✅ Match |

Nenhuma dependência aponta para fase posterior.

---

## Test Co-location Validation

| Task | Code Layer Created/Modified | Matrix Requires | Task Says | Status |
| ---- | --------------------------- | --------------- | --------- | ------ |
| T1 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T2 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T3 | Wiring Streamlit (testes) | integration | integration | ✅ OK |
| T4 | Documentação | unit | unit | ✅ OK |
| T5 | Documentação | unit | unit | ✅ OK |
| T6 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T7 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T8 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T9 | Configuração | unit | unit | ✅ OK |
| T10 | Domínio de chat | unit | unit | ✅ OK |
| T11 | Domínio de chat | unit | unit | ✅ OK |
| T12 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T13 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T14 | Wiring Streamlit | integration | integration | ✅ OK |
| T15 | Wiring Streamlit | integration | integration | ✅ OK |
| T16 | Núcleo UI-agnóstico | unit | unit | ✅ OK |
| T17 | Wiring Streamlit | integration | integration | ✅ OK |
| T18 | Wiring Streamlit | integration | integration | ✅ OK |

Nenhuma task usa `Tests: none`.
