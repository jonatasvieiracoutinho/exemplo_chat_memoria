# RF-PROV-01 — Troca de provedor de LLM em runtime pela tela — Design

**Spec**: `.specs/features/RF-PROV-01/spec.md`
**Faixa**: Large

## Decisão de arquitetura

A injeção acontece por **parâmetro de construtor**, não por mutação de ambiente. `ChatComMemoria.__init__()` ganha `api_key`, `modelo` e `base_url` no fim da assinatura, depois de `thread_id`, seguindo o padrão de precedência que os quatro parâmetros opcionais atuais já usam (`chat_openai_memoria.py:200-224`: parâmetro vence ambiente, `None` significa "leia do ambiente"). É o padrão canônico declarado em `AGENTS.md:247-249`, com `gerenciador` como caso precedente.

Efeito: uma segunda sessão na mesma execução do processo não é contaminada, e a mensagem de validação pode citar o parâmetro em vez de mandar corrigir um `.env` que não é a origem do valor.

A lógica de Perfis (carga, validação, escolha) fica em `app_streamlit_core.py`, sem importar `streamlit` (AD-003). `app_streamlit.py` só faz o wiring dos widgets, como já faz hoje.

## Componentes

| Componente | Arquivo | O que muda |
| ---------- | ------- | ---------- |
| `mascarar_chave(texto, chaves)` | `app_streamlit_core.py` (novo) | Função pura: troca cada chave não vazia pela máscara. 4+`***`+4 com 12 caracteres ou mais, `***` inteiro abaixo disso |
| `sanitizar_erro(exc, chat=None)` | `app_streamlit_core.py:31-34` | Passa a devolver `str(exc)` mascarado. `MENSAGEM_ERRO_AMIGAVEL` deixa de existir |
| `enviar_mensagem_seguro(chat, texto)` | `app_streamlit_core.py:37-48` | Passa `chat` para `sanitizar_erro`, de onde sai `chat.api_key` (a chave **ativa**, que com override pode não estar em `os.environ`) |
| `carregar_perfis()` | `app_streamlit_core.py` (novo) | Função pura sobre `os.environ`; devolve `list[dict]` |
| `construir_sessao_chat(...)` | `app_streamlit_core.py:20-25` | Ganha `api_key`, `modelo`, `base_url` e os repassa. A condição `persistencia_ativa()` para `gerenciador`/`thread_id` é preservada |
| `trocar_perfil(...)` | `app_streamlit_core.py` (novo) | Valida o Perfil, constrói a sessão nova e devolve `(chat_novo, erro)`. Nunca descarta nada |
| `ChatComMemoria.__init__()` | `chat_openai_memoria.py:114` | Três parâmetros novos no fim da assinatura |
| Barra lateral de Perfis | `app_streamlit.py:41-72` | Seletor, resumo do Perfil ativo, três campos do Perfil digitado, botão de confirmar |
| Bloco `PERFIS` | `env.example` | Documenta a declaração das variáveis |

## Contratos

### Perfil

`dict` com `nome`, `base_url`, `api_key`, `modelo`, `disponivel` (bool), `motivo_indisponivel` (str ou `None`). Em Perfil indisponível os três valores podem vir `None`. A entrada `Padrão (.env)` tem `base_url` igual a `None` quando `OPENAI_BASE_URL` não está definida, e é sempre `disponivel: True`, porque o endpoint padrão da OpenAI é o comportamento atual de `chat_openai_memoria.py:227-230` nesse caso.

### Variáveis de ambiente

`PERFIS` lista os nomes separados por vírgula. Cada nome vira o prefixo `PERFIL_<NOME>_`, onde `<NOME>` é o nome em maiúsculas com todo caractere não alfanumérico trocado por `_`. O bloco é `PERFIL_<NOME>_BASE_URL`, `PERFIL_<NOME>_API_KEY`, `PERFIL_<NOME>_MODEL`, e os três são obrigatórios — provedor local que não exige chave declara um valor qualquer.

### `trocar_perfil` — a ordem é o contrato

```
valida o Perfil (disponível? URL com esquema? campos preenchidos?)
  └─ recusa → devolve (None, motivo); o chamador não toca em st.session_state
constrói ChatComMemoria(api_key=…, modelo=…, base_url=…)
  └─ ValueError → devolve (None, str(erro)); o chamador não toca em st.session_state
sucesso → devolve (chat_novo, None)
  └─ só então o chamador substitui st.session_state["chat"] e zera ["thread_id"]
```

Inverter essa ordem transforma uma URL digitada errada em perda da conversa. A função nunca recebe `st.session_state`: quem escreve nele é `app_streamlit.py`, depois de ver `erro is None`.

Reselecionar o Perfil ativo não chama `trocar_perfil`: `app_streamlit.py` compara o nome escolhido com `st.session_state["perfil_ativo"]` e retorna antes. É o que garante que rerun do Streamlit ou interação acidental com o widget não reconstrói a sessão (CA-PROV-07).

## Precedência no construtor

Um único ponto de leitura por valor, na forma que o módulo já usa:

| Valor | Regra |
| ----- | ----- |
| `api_key` | parâmetro se não `None`; senão `os.getenv("OPENAI_API_KEY")`. Vazio ou só espaços por parâmetro ⇒ `ValueError` nomeando `api_key`, sem a string `.env` |
| `modelo` | idem, com `OPENAI_MODEL` |
| `base_url` | parâmetro se não `None`; senão `os.getenv("OPENAI_BASE_URL")`. A validação de esquema é a **mesma** de `chat_openai_memoria.py:187-195`, com a mensagem trocada quando a origem é parâmetro |
| `temperature`, `max_tokens` | só ambiente, obrigatórios, falham como hoje mesmo com os três parâmetros novos preenchidos |

A bifurcação do cliente (`OpenAI(api_key=…, base_url=…)` x `OpenAI(api_key=…)`, `chat_openai_memoria.py:227-230`) continua valendo com o valor que vier do parâmetro.

## Estado da sessão

`app_streamlit.py:inicializar_estado()` passa a criar também `perfil_ativo` (nome do Perfil) e os campos do Perfil digitado. Numa troca bem-sucedida, `st.session_state["chat"]` é substituído, `["thread_id"]` zera e o **mesmo** `gerenciador` é mantido — sem ele a persistência perderia a conexão configurada na sessão.

Nada disso é gravado em disco. Recarregar a página volta ao `Padrão (.env)`.

## Thread e provedor não têm vínculo

Nenhuma coluna nova, nenhuma migração em `persistencia.py`. A thread só nasce na primeira mensagem do usuário, em `ChatComMemoria._adicionar_ao_historico()` via `GerenciadorPersistencia.criar_thread()`, então trocar de Perfil sem ter mandado mensagem não deixa thread órfã. Retomar thread antiga por `app_streamlit_core.py:retomar_thread()` usa o Perfil selecionado no momento.

## Mascaramento e o que ele protege

`sanitizar_erro` masca **duas** chaves: a ativa (`chat.api_key`) e `os.getenv("OPENAI_API_KEY")` quando existe e difere. Com override, a chave em uso pode não estar no ambiente, e a do ambiente pode aparecer no texto de uma exceção anterior.

A propriedade que a constante fixa protegia era só a de a chave não chegar a disco, log, export ou tela. Hoje `api_key` só aparece na leitura do ambiente e na construção do cliente OpenAI, sem impressão nem log em modo algum, inclusive debug (conferido em `chat_openai_memoria.py:134-139,227-230,255-277`) — e isso continua verdadeiro. O trade-off de exibir o texto técnico está registrado em AD-005.

## Compatibilidade dos chamadores

Os três parâmetros entram **no fim** da assinatura, depois de `thread_id`, para não deslocar argumento posicional. Conferido: todos os chamadores usam argumentos nomeados ou nenhum — `chat_openai_memoria.py:904,1044`, `app_streamlit_core.py:24-25`, `exemplos_avancados.py:22,29,63,98,173,226,264,308,358`. `exemplos_avancados.py` não precisa de alteração.

## Testes existentes que mudam

Cinco travam o texto fixo e passam a travar a mascaração:

- `tests/test_app_streamlit_core.py`: `test_sanitizar_erro_nao_contem_texto_bruto_da_excecao()`, `test_sanitizar_erro_nao_contem_api_key_do_ambiente()`, `test_enviar_mensagem_seguro_excecao_retorna_mensagem_sanitizada()`
- `tests/test_app_streamlit_ui.py`: `test_app_erro_sanitizado_aparece_amigavel()`, `test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append()`

Os demais que usam o texto fixo apenas como retorno de mock, sem assertiva sobre ele (`tests/test_app_streamlit_ui.py:210,266`), continuam válidos.

O comportamento de manter a fala do usuário visível na falha, sem bolha de assistente, já existe em `app_streamlit.py:79-89` e é coberto por `test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append()`. Preservar, não reimplementar.

## Alternativas descartadas

| Alternativa | Por que não |
| ----------- | ----------- |
| Mutar `os.environ` e reconstruir | Contamina o processo inteiro, inclusive uma segunda sessão na mesma execução, e faz a validação mandar corrigir um `.env` que não é a origem do valor |
| Módulo `perfis.py` novo | Acrescenta arquivo e módulo de teste sem ganhar isolamento: nada além de `app_streamlit_core.py` o consumiria (AD-003) |
| Classificar o erro por categoria | A categoria perde o detalhe, que é o conteúdo do diagnóstico. Fora de escopo por decisão do requisito |
| Descartar a conversa e construir depois | É a inversão de ordem que o requisito existe para impedir |
| Allowlist de domínio na base URL | Impediria `http://localhost:11434`, que é o caso de uso principal de provedor local (AD-006) |
