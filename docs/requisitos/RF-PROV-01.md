---
id: RF-PROV-01
titulo: Troca de provedor de LLM em runtime pela tela
status: em_execucao
depende_de: []
bloqueia: []
entrega_observavel: "na barra lateral do app Streamlit, escolher outro provedor (Perfil declarado no .env ou valores digitados na hora) e conversar contra ele sem editar arquivo e sem reiniciar o processo, na mesma sessão do navegador; quando o provedor falha, a tela mostra o texto da exceção com a chave mascarada, o que permite distinguir URL errada de chave inválida de modelo inexistente"
criterios: [CA-PROV-01, CA-PROV-02, CA-PROV-03, CA-PROV-04, CA-PROV-05, CA-PROV-06, CA-PROV-07, CA-PROV-08, CA-PROV-09, CA-PROV-10, CA-PROV-11]
esforco: G
fontes:
  - .design/troca-de-provedor-em-runtime.md
  - AGENTS.md#padrão-de-extensão-de-chatcommemoria
  - env.example
  - .specs/features/adicionar-tela-streamlit-659323ea/spec.md
  - .specs/features/fala-do-usu-rio-no-chat-s-aparece-quando-o-assis-a52b11c8/tasks.md
---

# RF-PROV-01 · Troca de provedor de LLM em runtime pela tela

Hoje trocar de provedor compatível com a API OpenAI custa três passos fora do app: editar o `.env`,
matar o processo do Streamlit e subir de novo. O restart não é opcional: `load_dotenv()` não sobrescreve
variável já presente no ambiente do processo, e o cliente da API é construído uma única vez na criação
de `ChatComMemoria`. Efeito colateral de cada troca: a sessão do navegador morre e a conversa de teste
tem de ser refeita do zero.

## ⚠️ `esforco: G` — por que não está dividido

Decisão do dono em 2026-09-27: **o corte fica no `tasks.md`**, não na fila. A `tlc-spec-driven` quebra
este requisito em fases, e o laço abre uma sessão de implementação por marcador `<!-- FASE: N -->`, então
o tamanho da PR é controlado ali, e não pelo número de itens da fila.

Ordem sugerida para as fases, que é a do documento de desenho: Perfil → override no construtor → troca
pela barra lateral → Perfil digitado → erro do provedor na tela. Uma variação defensável: puxar o erro
técnico na tela para a primeira fase, porque sem ele a primeira troca de provedor com URL errada continua
mostrando `Não foi possível obter resposta agora` e não se distingue URL de chave de modelo.

---

## Comportamento (EARS)

### Perfis declarados no ambiente

O SISTEMA DEVE oferecer uma função pura que lê o ambiente e devolve a lista de Perfis, começando sempre
pela entrada `Padrão (.env)`, montada a partir de `OPENAI_API_KEY`, `OPENAI_MODEL` e `OPENAI_BASE_URL`.

QUANDO a variável `PERFIS` lista um nome cujo bloco de três variáveis está completo, O SISTEMA DEVE
incluir esse Perfil na lista como disponível, na ordem em que o nome aparece em `PERFIS`.

SE a variável `PERFIS` estiver ausente ou vazia, ENTÃO O SISTEMA DEVE devolver apenas a entrada
`Padrão (.env)`.

SE um nome listado em `PERFIS` tiver qualquer das três variáveis do bloco ausente ou vazia, ENTÃO O
SISTEMA DEVE incluir esse Perfil marcado como indisponível, com o motivo nomeando o Perfil e a variável
que falta, e NÃO DEVE levantar exceção.

SE a base URL de um Perfil não começar com `http://` nem `https://`, ENTÃO O SISTEMA DEVE incluir esse
Perfil marcado como indisponível, com o motivo nomeando o Perfil e a URL recebida.

SE o mesmo nome aparecer mais de uma vez em `PERFIS`, ENTÃO O SISTEMA DEVE manter apenas a primeira
ocorrência.

### Override de chave, modelo e base URL no construtor

O SISTEMA DEVE aceitar `api_key`, `modelo` e `base_url` como parâmetros opcionais do construtor de
`ChatComMemoria`, e o valor recebido por parâmetro DEVE vencer o valor do ambiente.

ENQUANTO nenhum dos três parâmetros é passado, O SISTEMA DEVE se comportar exatamente como hoje: mesmos
valores lidos do ambiente, mesmas validações e mesmas mensagens de recusa citando o `.env`.

ONDE apenas parte dos três parâmetros é passada, O SISTEMA DEVE ler do ambiente somente os que não
vieram por parâmetro.

QUANDO `api_key` ou `modelo` chega por parâmetro, O SISTEMA DEVE construir com sucesso mesmo que a
variável de ambiente correspondente esteja ausente.

SE `api_key` ou `modelo` chegar por parâmetro vazio ou só com espaços, ENTÃO O SISTEMA DEVE recusar a
construção com mensagem que nomeia o parâmetro e NÃO DEVE instruir a editar o `.env`.

SE `base_url` chegar por parâmetro sem começar com `http://` nem `https://`, ENTÃO O SISTEMA DEVE recusar
a construção nomeando o valor recebido e NÃO DEVE instruir a editar o `.env`.

### Troca de Perfil pela barra lateral

O SISTEMA DEVE exibir na barra lateral um seletor com os Perfis carregados do ambiente, e exibir o Perfil
ativo com seu nome, sua base URL e seu modelo, e nunca a chave.

QUANDO a sessão do navegador é criada, O SISTEMA DEVE construir a sessão de chat a partir do ambiente,
com `Padrão (.env)` selecionado, como hoje.

QUANDO um Perfil disponível diferente do ativo é escolhido e confirmado, O SISTEMA DEVE construir uma
sessão nova de `ChatComMemoria` com os três valores daquele Perfil e só então descartar a conversa em
andamento.

ENQUANTO o Perfil escolhido é o mesmo que já está ativo, O SISTEMA DEVE preservar a sessão e a conversa
em andamento.

SE o Perfil escolhido estiver marcado como indisponível, ENTÃO O SISTEMA DEVE exibir o motivo que nomeia
a variável faltante e NÃO DEVE trocar a sessão.

SE a construção da sessão nova for recusada pela validação de `ChatComMemoria`, ENTÃO O SISTEMA DEVE
exibir a recusa e preservar a sessão anterior e a conversa em andamento.

### Perfil digitado na barra lateral

O SISTEMA DEVE oferecer no seletor uma entrada de Perfil digitado, com três campos de texto para base
URL, chave e modelo.

QUANDO a entrada digitada é confirmada com os três campos preenchidos e a base URL válida, O SISTEMA DEVE
construir uma sessão nova de `ChatComMemoria` com os valores digitados, seguindo a mesma ordem: construir
antes de descartar.

SE qualquer dos três campos estiver vazio ou só com espaços na confirmação, ENTÃO O SISTEMA DEVE sinalizar
o campo obrigatório e NÃO DEVE trocar a sessão.

SE a base URL digitada não começar com `http://` nem `https://`, ENTÃO O SISTEMA DEVE exibir erro nomeando
a URL recebida e NÃO DEVE trocar a sessão.

O SISTEMA DEVE manter o campo da chave digitada com entrada mascarada na tela, e NÃO DEVE exibir, gravar
em disco nem registrar em log o valor digitado.

### Erro do provedor na tela

QUANDO o envio de uma mensagem falha por exceção, O SISTEMA DEVE exibir na tela o texto da exceção,
preservar a conversa, manter a fala do usuário visível e não criar bolha de assistente.

O SISTEMA DEVE substituir por máscara toda ocorrência da chave ativa no texto antes de ele chegar à tela.

SE a chave ativa tiver 12 caracteres ou mais, ENTÃO O SISTEMA DEVE exibi-la como os 4 primeiros
caracteres, seguidos de `***`, seguidos dos 4 últimos.

SE a chave ativa tiver menos de 12 caracteres, ENTÃO O SISTEMA DEVE substituí-la inteira por `***`.

SE a mensagem enviada for vazia ou só espaços, ENTÃO O SISTEMA DEVE não chamar a API e não alterar o
histórico, como hoje.

---

## Contexto necessário

### Decisões fechadas

> ✅ **[DECIDIDO em 2026-09-27 com o usuário]** Os nomes das variáveis são `PERFIS` para a lista e
> `PERFIL_<NOME>_BASE_URL`, `PERFIL_<NOME>_API_KEY`, `PERFIL_<NOME>_MODEL` para o bloco. `<NOME>` é o nome
> do Perfil normalizado: maiúsculas, e todo caractere não alfanumérico virando `_`. Razão: mantém o
> vocabulário "Perfil" do desenho e evita colisão com as variáveis `OPENAI_*` já existentes.

> ✅ **[DECIDIDO em 2026-09-27 com o usuário]** A máscara da chave é parcial: 4 primeiros caracteres +
> `***` + 4 últimos, por exemplo `gsk_***Z789`. Razão: permite confirmar qual chave foi usada quando há
> vários Perfis. Chave com menos de 12 caracteres cai na máscara opaca `***`, senão 4+4 exporia a chave
> inteira ou quase inteira.

> ✅ **[DECIDIDO em 2026-09-27 com o usuário]** Escolher no seletor o Perfil que já está ativo **não**
> descarta a conversa. Razão: só uma troca real reconstrói a sessão, então rerun do Streamlit ou interação
> acidental com o widget não causa perda de conversa.

> ✅ **[DECIDIDO no desenho, 2026-09-27]** A carga inicial continua exigindo o ambiente obrigatório
> completo: o app não sobe sem `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_TEMPERATURE` e
> `OPENAI_MAX_TOKENS` válidos, porque o `Padrão (.env)` é construído no start. Rodar só contra um provedor
> local sem nenhuma chave OpenAI declarada fica fora desta entrega.

> ✅ **[DECIDIDO no desenho, 2026-09-27]** A exibição do texto técnico da exceção **supera** a decisão de
> setembro que fixou a mensagem genérica. Sem o texto da exceção não há como distinguir URL errada de
> chave inválida de modelo inexistente, que é o diagnóstico que um teste de provedor precisa.

### Declaração no ambiente

```
PERFIS=Groq,Ollama local
PERFIL_GROQ_BASE_URL=https://api.groq.com/openai/v1
PERFIL_GROQ_API_KEY=gsk_exemplo
PERFIL_GROQ_MODEL=llama-3.3-70b-versatile
```

O nome `Ollama local` vira o prefixo `PERFIL_OLLAMA_LOCAL_`. Um provedor local que não exige chave
(Ollama, LM Studio) ainda declara `PERFIL_<NOME>_API_KEY` com um valor qualquer, porque o bloco de três é
obrigatório por desenho. A chave não é opcional em Perfil algum.

### Contrato interno entre as partes

Cada Perfil é um dicionário com as chaves `nome`, `base_url`, `api_key`, `modelo`, `disponivel` (bool) e
`motivo_indisponivel` (str ou None). Em Perfil indisponível, os três valores podem vir `None`, e
`motivo_indisponivel` é o texto exibido na tela. A entrada `Padrão (.env)` tem `base_url` igual a `None`
quando `OPENAI_BASE_URL` não está definida, porque o endpoint padrão da OpenAI é o comportamento atual de
`ChatComMemoria.__init__()` nesse caso, e é sempre `disponivel: True`.

### A porta: assinatura de `ChatComMemoria`

A assinatura de `ChatComMemoria.__init__()` em `chat_openai_memoria.py` é consumida por três chamadores:
o modo interativo da CLI no próprio módulo, `app_streamlit_core.py:construir_sessao_chat()` e
`exemplos_avancados.py`. Os três parâmetros novos entram **no fim** da assinatura, depois de `thread_id`,
para não deslocar nenhum argumento posicional existente. Nomeie-os `api_key`, `modelo` e `base_url`,
iguais aos atributos que o construtor já grava (`self.api_key`, `self.modelo`, `self.base_url`).

O padrão de precedência já existe no mesmo construtor, nos quatro parâmetros opcionais atuais
(`tamanho_janela`, `limite_maximo`, `modo_debug`, `stream`): parâmetro vence ambiente, `None` significa
"leia do ambiente". Copie essa forma; não invente uma terceira.

A regra de recusa de URL sem esquema já existe em `ChatComMemoria.__init__()`, na validação de
`OPENAI_BASE_URL`. Use a mesma regra; não crie uma segunda validação de URL.

O cliente é montado no fim de `ChatComMemoria.__init__()`, com `base_url` quando ela existe e sem ela
caso contrário. Essa bifurcação continua valendo com o valor que vier do parâmetro.

### Injeção, nunca mutação de ambiente

**Nenhum caminho de código escreve em `os.environ`.** A injeção é por parâmetro do construtor, que é o
padrão canônico declarado no `AGENTS.md`, com `gerenciador` como caso precedente. Mutar o ambiente
contaminaria o processo inteiro, inclusive uma segunda sessão na mesma execução, e faria as mensagens de
validação mandarem corrigir um `.env` que não é a origem do valor.

`temperature` e `max_tokens` continuam obrigatórios no ambiente e **não** ganham parâmetro. Se
`OPENAI_TEMPERATURE` ou `OPENAI_MAX_TOKENS` faltar, a construção falha como hoje, mesmo com os três
parâmetros novos preenchidos.

### Estado da sessão e ordem da troca

**A ordem é o que este requisito garante:** valide o Perfil, construa a sessão nova, e só depois descarte
a antiga. Trocar a ordem transforma uma URL digitada errada em perda da conversa.

`app_streamlit.py:inicializar_estado()` é quem cria `chat`, `gerenciador` e `thread_id` em
`st.session_state` uma vez por sessão de navegador. A troca de Perfil substitui `st.session_state["chat"]`
e zera `st.session_state["thread_id"]`, mantendo o **mesmo** `gerenciador`.

`app_streamlit_core.py:construir_sessao_chat()` passa a repassar os três valores do Perfil para
`ChatComMemoria`. Ela hoje só repassa `gerenciador` e `thread_id`, e só quando `persistencia_ativa()`.
Preserve essa condição: sem persistência, `gerenciador` e `thread_id` continuam ignorados.

**Thread e provedor não têm vínculo.** Nenhuma coluna nova, nenhuma migração. A thread só é criada na
primeira mensagem do usuário (em `ChatComMemoria._adicionar_ao_historico()`, via
`GerenciadorPersistencia.criar_thread()`), então trocar de Perfil sem ter mandado mensagem não deixa
thread órfã no banco. Retomar uma thread antiga por `app_streamlit_core.py:retomar_thread()` usa o Perfil
selecionado no momento, não o que gerou a thread.

⚠️ O Perfil escolhido e os valores digitados vivem em `st.session_state` e morrem no recarregamento da
página do navegador: a sessão volta ao `Padrão (.env)`. Nada é gravado em disco.

### O erro na tela e os testes que mudam

`app_streamlit_core.py:sanitizar_erro()` hoje devolve a constante fixa `MENSAGEM_ERRO_AMIGAVEL` e descarta
o texto da exceção. Essa constante deixa de existir, e `sanitizar_erro()` passa a devolver o texto da
exceção mascarado.

A função precisa da chave **ativa**, não só da do ambiente: com o override, a chave em uso pode não estar
em `os.environ`. `app_streamlit_core.py:enviar_mensagem_seguro()` recebe o objeto de chat e tem acesso ao
atributo `api_key` de `ChatComMemoria`. Masque a chave ativa **e** a de `OPENAI_API_KEY` quando existir.

**Testes existentes que travam o texto fixo e passam a travar a mascaração:**

- `tests/test_app_streamlit_core.py` → `test_sanitizar_erro_nao_contem_texto_bruto_da_excecao()`,
  `test_sanitizar_erro_nao_contem_api_key_do_ambiente()`,
  `test_enviar_mensagem_seguro_excecao_retorna_mensagem_sanitizada()`
- `tests/test_app_streamlit_ui.py` → `test_app_erro_sanitizado_aparece_amigavel()`,
  `test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append()`

Os demais testes de UI que usam o texto fixo apenas como retorno de mock, sem assertiva sobre ele,
continuam válidos.

A propriedade que a mensagem fixa existia para proteger é **só** a de a chave não chegar a disco, log,
export ou tela. Hoje a chave não é impressa nem logada em modo algum, inclusive debug (conferido em
2026-09-27: `api_key` só aparece na leitura do ambiente e na construção do cliente OpenAI), e isso precisa
continuar verdadeiro depois da mudança.

O comportamento de manter a fala do usuário visível na falha, sem bolha de assistente, já existe em
`app_streamlit.py:main()` e é coberto por
`tests/test_app_streamlit_ui.py:test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append()`. Não
reimplemente; preserve.

### Onde o código vai e como se testa

A lógica de carga de Perfis, de escolha e de validação fica em `app_streamlit_core.py` (ou em módulo
próprio ao lado dele), **sem importar `streamlit`**, e `app_streamlit.py` faz só o wiring dos widgets. É a
separação que os dois módulos já mantêm.

Padrões de teste que a suíte já usa e que servem aqui:

- ambiente: `patch.dict("os.environ", …)`, como em
  `tests/test_app_streamlit_core.py:test_persistencia_ativa_true_quando_env_true()`
- construção: fixture `openai_mockado` de `tests/test_app_streamlit_core.py`, com
  `patch("chat_openai_memoria.OpenAI")` + `patch("chat_openai_memoria.load_dotenv")`
- tela: `streamlit.testing.v1.AppTest` com `patch` em `app_streamlit_core.construir_sessao_chat` e
  `app_streamlit_core.persistencia_ativa`, como em
  `tests/test_app_streamlit_ui.py:test_sidebar_retomar_thread_atualiza_sessao_e_historico()`

A suíte atual tem 112 testes verdes (medido em 2026-09-27). Lint e tipos não existem no projeto, então o
gate mede por pytest.

⚠️ Documentação a atualizar junto, porque hoje ela declara a mensagem genérica como requisito:
`.specs/features/adicionar-tela-streamlit-659323ea/` (spec, design e validation) e o PRD
`docs/prds/PRD-2026-09-18-adicionar-front-end-em-streamlit-com-scripts-de-inicializacao-automatica.md`.
Registre a superação; não apague o histórico. O `env.example` ganha o bloco de `PERFIS`.

---

## Critérios de aceite

### CA-PROV-01 — Perfil completo entra disponível, bloco incompleto entra indisponível nomeando a variável

DADO `PERFIS=Groq,Ollama local` no ambiente
E o bloco completo das três variáveis de `Groq`
E o bloco de `Ollama local` sem a variável de modelo
QUANDO a lista de Perfis é carregada
ENTÃO a primeira entrada é `Padrão (.env)` com os valores das variáveis obrigatórias
E `Groq` aparece com `disponivel` verdadeiro e os três valores declarados
E `Ollama local` aparece com `disponivel` falso e `motivo_indisponivel` contendo o nome do Perfil e
`PERFIL_OLLAMA_LOCAL_MODEL`
E nenhuma exceção é levantada

**Teste-guarda (a mutação que o derruba):** apagar a variável de modelo de um Perfil **tem** de produzir
`disponivel: False` com o nome da variável no motivo, e não um Perfil ausente da lista nem um Perfil com
modelo `None` marcado como disponível. Fazer a função levantar exceção no bloco incompleto **tem** de
reprovar.

### CA-PROV-02 — URL sem esquema é recusada, nome duplicado entra uma vez, lista ausente dá só o padrão

DADO um Perfil cuja base URL declarada é `api.groq.com/openai/v1`, sem esquema
QUANDO a lista de Perfis é carregada
ENTÃO esse Perfil aparece com `disponivel` falso e o motivo contém o nome do Perfil e a URL recebida
E quando `PERFIS=Groq,Groq`, a lista traz `Groq` exatamente uma vez
E quando `PERFIS` está ausente ou é string vazia, a lista tem comprimento 1 e contém só `Padrão (.env)`

**Teste-guarda (a mutação que o derruba):** trocar a checagem de esquema por um `if base_url:` **tem** de
deixar o teste vermelho; e remover a deduplicação **tem** de produzir duas entradas `Groq`. Um teste que
só conte os itens da lista sem olhar `disponivel` passaria satisfeito por cima da recusa e não serve.

### CA-PROV-03 — ausência de parâmetro preserva o comportamento atual, e parâmetro vence ambiente

DADO um ambiente com as quatro variáveis obrigatórias preenchidas
QUANDO `ChatComMemoria()` é construído sem os três parâmetros novos
ENTÃO `api_key`, `modelo` e `base_url` valem exatamente o que o ambiente declara
E quando os três são passados por parâmetro, os três atributos valem os valores passados e o ambiente é
ignorado para eles
E quando só `base_url` é passada, `api_key` e `modelo` continuam vindo do ambiente
E quando `OPENAI_API_KEY` está ausente do ambiente e `api_key` é passada por parâmetro, a construção
conclui sem exceção

**Teste-guarda (a mutação que o derruba):** inverter a precedência, fazendo o ambiente vencer o parâmetro,
**tem** de deixar o teste vermelho; e manter a ausência de `OPENAI_API_KEY` como fatal mesmo com `api_key`
por parâmetro **tem** de reprovar. Um teste que só verifique o caso dos três parâmetros passados não
discrimina a regressão do caminho sem parâmetro, que é o risco real aqui.

### CA-PROV-04 — valor inválido por parâmetro é recusado sem mandar editar o `.env`

DADO um ambiente com as quatro variáveis obrigatórias preenchidas
QUANDO `ChatComMemoria(api_key="   ")` é construído
ENTÃO a construção levanta `ValueError` cuja mensagem cita o parâmetro `api_key` e **não** contém a string
`.env`
E o mesmo vale para `modelo=""`
E quando `base_url="api.groq.com/openai/v1"` é passada, a recusa cita o valor recebido e **não** contém a
string `.env`
E quando o valor inválido vem do ambiente, e não de parâmetro, a mensagem continua citando o `.env` como
hoje

**Teste-guarda (a mutação que o derruba):** reaproveitar a mensagem de erro do ambiente para o caminho de
parâmetro **tem** de deixar o teste vermelho, porque a string `.env` reapareceria. E aceitar
`api_key="   "` como válida (checagem `is None` em vez de valor em branco) **tem** de reprovar.

### CA-PROV-05 — trocar de Perfil constrói a sessão contra ele e limpa a conversa

DADO um ambiente com `Padrão (.env)` e um Perfil disponível `Groq`
E uma conversa em andamento com mensagens na tela
QUANDO `Groq` é escolhido e confirmado na barra lateral
ENTÃO a sessão nova é construída com a base URL, a chave e o modelo de `Groq`
E a tela de conversa fica vazia
E a barra lateral mostra `Groq` como Perfil ativo, com sua base URL e seu modelo
E nenhum texto da tela contém a chave do Perfil

**Teste-guarda (a mutação que o derruba):** construir a sessão nova sem repassar os três valores (ficando
no ambiente) **tem** de deixar o teste vermelho; e imprimir a chave junto da base URL no resumo do Perfil
ativo **tem** de reprovar. Um teste que só confira "a conversa esvaziou" passa satisfeito por cima de uma
sessão que continua no provedor antigo, e não serve.

### CA-PROV-06 — Perfil indisponível ou construção recusada preservam a sessão atual

DADO uma conversa em andamento e um Perfil marcado como indisponível por variável faltante
QUANDO esse Perfil é escolhido e confirmado
ENTÃO a tela exibe o motivo nomeando a variável que falta
E a sessão de chat é o mesmo objeto de antes
E a conversa em andamento continua visível
E quando o Perfil está disponível mas `ChatComMemoria` recusa a construção, a recusa aparece na tela e a
sessão anterior também é preservada

**Teste-guarda (a mutação que o derruba):** descartar a conversa antes de construir a sessão nova **tem**
de deixar este teste vermelho. É exatamente a inversão de ordem que o requisito existe para impedir, e um
teste que só verifique a mensagem de erro não a detecta.

### CA-PROV-07 — reselecionar o Perfil ativo não descarta a conversa

DADO `Groq` como Perfil ativo e uma conversa em andamento
QUANDO `Groq` é escolhido e confirmado de novo
ENTÃO a sessão de chat é o mesmo objeto de antes
E a conversa em andamento continua visível
E nenhuma construção de `ChatComMemoria` é feita

**Teste-guarda (a mutação que o derruba):** reconstruir a sessão a cada confirmação, sem comparar com o
Perfil ativo, **tem** de deixar o teste vermelho pela assertiva de identidade do objeto e da contagem de
chamadas do construtor.

### CA-PROV-08 — Perfil digitado válido troca a sessão, campo vazio não troca

DADO uma conversa em andamento no `Padrão (.env)`
QUANDO a entrada digitada é confirmada com base URL `https://api.groq.com/openai/v1`, chave e modelo
preenchidos
ENTÃO a sessão nova é construída com exatamente esses três valores
E a tela de conversa fica vazia
E quando a confirmação acontece com qualquer dos três campos vazio ou só com espaços, a tela sinaliza o
campo obrigatório, a sessão de chat é o mesmo objeto de antes e a conversa continua visível

**Teste-guarda (a mutação que o derruba):** aceitar campo só com espaços como preenchido (checagem de
`None` em vez de valor em branco) **tem** de deixar o teste vermelho; e construir a sessão nova antes de
validar os campos **tem** de reprovar pela assertiva de identidade do objeto de sessão.

### CA-PROV-09 — URL digitada sem esquema é recusada e a chave digitada não aparece na tela

DADO uma conversa em andamento
QUANDO a entrada digitada é confirmada com base URL `api.groq.com/openai/v1`, sem esquema
ENTÃO a tela exibe erro contendo a URL recebida
E a sessão de chat é o mesmo objeto de antes
E nenhum texto renderizado na tela contém a chave digitada

**Teste-guarda (a mutação que o derruba):** ecoar os valores digitados em um resumo de confirmação **tem**
de deixar o teste vermelho pela assertiva da chave; e trocar a checagem de esquema por um truthy da string
**tem** de reprovar.

### CA-PROV-10 — o texto da exceção aparece na tela, e a chave ativa aparece mascarada

DADO uma sessão cuja chave ativa é `gsk_abc123XYZ789`
QUANDO o envio falha com exceção cujo texto é
`AuthenticationError: Incorrect API key provided: gsk_abc123XYZ789`
ENTÃO a tela exibe um erro contendo `Incorrect API key provided`
E o texto exibido contém `gsk_***Z789`
E o texto exibido **não** contém `gsk_abc123XYZ789`
E a fala do usuário continua visível, sem bolha de assistente
E mensagem vazia ou só com espaços continua não chamando a API nem alterando o histórico

**Teste-guarda (a mutação que o derruba):** voltar a devolver uma mensagem fixa **tem** de deixar vermelha
a assertiva de `Incorrect API key provided`; e remover a mascaração **tem** de deixar vermelha a assertiva
de que a chave crua não aparece. Um teste que só confira "existe um `st.error` na tela" passa satisfeito
nas duas mutações e não serve.

### CA-PROV-11 — chave curta é totalmente opaca, e a chave do ambiente também é mascarada

DADO uma chave ativa `ollama`, com menos de 12 caracteres
QUANDO o envio falha com exceção cujo texto contém `ollama`
ENTÃO o texto exibido contém `***` no lugar da chave e **não** contém `ollama`
E quando a chave ativa difere de `OPENAI_API_KEY` e o texto da exceção contém a chave do ambiente, essa
também aparece mascarada
E o texto exibido nunca é gravado em arquivo de log nem no arquivo de export da conversa

**Teste-guarda (a mutação que o derruba):** aplicar a máscara 4+4 sem o piso de 12 caracteres **tem** de
deixar o teste vermelho, porque `olla***lama` conteria a chave inteira. E mascarar só a chave ativa,
ignorando `OPENAI_API_KEY`, **tem** de reprovar na segunda assertiva.

---

## Fora deste requisito

- **Provedor AWS Bedrock nativo.** Tem plano e branch próprios, parados, e depende de um backend que não
  existe no `main`. Provedor como backend é um desenho diferente de provedor como endpoint.
- **Troca de provedor na CLI.** Lá o `.env` antes de subir já é o fluxo natural e não paga restart de
  sessão de navegador.
- **`temperature` e `max_tokens` no seletor.** Continuam vindo do ambiente, onde as ressalvas de modelo de
  reasoning já estão documentadas.
- **Gravar o provedor na thread**, em coluna nova ou no título. Sem vínculo entre thread e provedor, logo
  sem migração. `GerenciadorPersistencia` e o schema, incluindo `threads` e `turnos`, não mudam.
- **Persistir em disco o Perfil escolhido ou os valores digitados.** O override é de sessão.
- **Dar nome ao Perfil digitado** e vê-lo depois como entrada nomeada do seletor.
- **Subir o app sem o ambiente obrigatório completo**, para rodar só contra provedor local sem chave
  OpenAI declarada.
- **Classificar o erro por categoria** em vez de exibir o texto do provedor: a categoria perde o detalhe
  que é o conteúdo do diagnóstico.
- **Descoberta de Perfis por varredura de prefixo**, sem a lista `PERFIS` declarada: nome digitado errado
  sumiria sem erro.
- A estimativa aproximada de tokens, o sliding window e o monitoramento de limite não mudam.
  `exemplos_avancados.py` consome apenas a interface pública e não deve precisar de alteração.
