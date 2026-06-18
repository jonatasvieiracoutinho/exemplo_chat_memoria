# Plano de Implementação: Provedor AWS Bedrock (boto3 + Converse)

## Visão Geral

Adicionar o **AWS Bedrock como provedor nativo** ao chat, usando `boto3` com a API
`Converse`/`ConverseStream` e autenticação por **Bedrock API key**. O provedor é
selecionável via `.env` (`PROVEDOR=openai|bedrock`), **mantendo o backend OpenAI
existente 100% funcional**. A escolha arquitetural é uma camada fina de *backend*
(estratégia): tudo que é genérico — memória, sliding window, monitoramento de
tokens, logging, UI e comandos — permanece em `ChatComMemoria` sem alteração de
comportamento; apenas a etapa "chamar o modelo" é delegada a um backend.

## Análise do Estado Atual

O núcleo é a classe `ChatComMemoria` em [chat_openai_memoria.py:103](chat_openai_memoria.py#L103),
configurada inteiramente via `.env`. Pontos relevantes mapeados na recon:

### Descobertas Principais:
- **Já existe suporte a provedores compatíveis** via `OPENAI_BASE_URL`
  ([chat_openai_memoria.py:182-189](chat_openai_memoria.py#L182-L189) e
  [L223-226](chat_openai_memoria.py#L223-L226)) — Azure/Ollama/LM Studio já documentados.
- **A validação da API key NÃO exige prefixo `sk-`** ([chat_openai_memoria.py:128-133](chat_openai_memoria.py#L128-L133)).
- A chamada ao modelo (build de `parametros` + branch de reasoning + branch de
  streaming) está concentrada em [chat_openai_memoria.py:531-559](chat_openai_memoria.py#L531-L559),
  dentro de `enviar_mensagem()`.
- O gate de reasoning é `_usa_parametros_reasoning()` ([chat_openai_memoria.py:497-507](chat_openai_memoria.py#L497-L507)),
  detecta `gpt-5`/`o1`/`o3`/`o4` por prefixo. Documentado em `.notebook/gpt5-reasoning-api.md`.
- O **contrato de impressão do streaming** ([.notebook/streaming-output.md](.notebook/streaming-output.md)):
  em stream, `enviar_mensagem()` IMPRIME os deltas e retorna o texto acumulado; os
  chamadores NÃO reimprimem (só dão `print("\n")` quando `chat.stream`). Esse contrato
  precisa ser preservado ao mover a chamada para o backend.
- `self.modelo`, `self.temperature`, `self.max_tokens` são usados em todo o
  logging/exibição/export ([L286-288](chat_openai_memoria.py#L286-L288),
  [L351-353](chat_openai_memoria.py#L351-L353), [L760](chat_openai_memoria.py#L760)) —
  devem continuar existindo no objeto `ChatComMemoria`.
- `exemplos_avancados.py` consome **apenas a interface pública** (`ChatComMemoria(...)`
  com kwargs `tamanho_janela`/`limite_maximo`/`modo_debug`, `enviar_mensagem`,
  `definir_personalidade`, `debug_memoria`, etc.) — **não toca em internals de provedor**.
  Logo, preservando a interface pública, ele continua funcionando sem mudança.

### Fatos verificados contra a documentação oficial da AWS:
- **boto3 + Bedrock API key**: a chave só é aceita via variável de ambiente
  `AWS_BEARER_TOKEN_BEDROCK`; `boto3.client("bedrock-runtime", region_name=...)`
  a detecta automaticamente. boto3 **não** aceita a chave como parâmetro de `client()`.
- **Converse**: `client.converse(modelId=..., messages=[{"role","content":[{"text"}]}],
  system=[{"text"}], inferenceConfig={"maxTokens","temperature"})`; texto em
  `response["output"]["message"]["content"][0]["text"]`.
- **ConverseStream**: `client.converse_stream(...)`; iterar `response["stream"]`; em
  eventos `contentBlockDelta`, o texto incremental está em
  `event["contentBlockDelta"]["delta"]["text"]`.
- Formato de model id no Bedrock: ex. `us.anthropic.claude-sonnet-4-6`.
- Suporte a `AWS_BEARER_TOKEN_BEDROCK` exige boto3 razoavelmente recente (`>=1.40`).

## Estado Final Desejado

Com `PROVEDOR=bedrock` + `BEDROCK_API_KEY`/`BEDROCK_REGION`/`BEDROCK_MODEL` no `.env`,
o chat conversa com modelos do Bedrock (incluindo Claude) usando a API Converse nativa,
com streaming funcionando igual ao OpenAI e toda a camada de memória/monitoramento/logging
intacta. Com `PROVEDOR=openai` (padrão) ou `.env` legado, o comportamento é idêntico ao atual.

Verificação do estado final:
- `python -m py_compile chat_openai_memoria.py exemplos_avancados.py` sem erros.
- `python -c "from chat_openai_memoria import ChatComMemoria"` sem erros.
- Sessão real OpenAI inalterada; sessão real Bedrock responde (passos manuais).

## O Que NÃO Estamos Fazendo

- **Não** renomear as variáveis compartilhadas — `OPENAI_TEMPERATURE`,
  `OPENAI_MAX_TOKENS` e `OPENAI_STREAM` passam a valer para ambos os provedores
  (decisão do usuário: reutilizar nomes existentes, diff mínimo).
- **Não** usar o endpoint OpenAI-compatível do Bedrock (decisão: backend nativo via boto3).
- **Não** implementar tool use, guardrails, cross-region inference profiles explícitos,
  nem streaming de `usage`/metadata.
- **Não** suportar autenticação SigV4/IAM pura no SDK (auth é por Bedrock API key).
- **Não** alterar a lógica de memória, sliding window, monitoramento de tokens, gráficos
  ou comandos do chat.

## Abordagem de Implementação

Refatoração incremental e retrocompatível em três fases: (1) extrair o comportamento
atual da OpenAI para um backend dedicado, sem mudar nada observável; (2) adicionar o
backend Bedrock, a seleção por `PROVEDOR`, a validação condicional e o polish de UX
ciente do provedor; (3) atualizar a documentação do projeto. As variáveis de geração
permanecem com os nomes `OPENAI_*` (compartilhadas), e as variáveis de conexão do
Bedrock usam o prefixo `BEDROCK_*`.

Interface comum dos backends:

```python
def gerar(self, *, system_prompt: str, historico: list,
          temperature: float, max_tokens: int, stream: bool) -> str:
    """Chama o modelo. Em stream=True, imprime os deltas e retorna o texto acumulado."""
```

---

<!-- FASE: 1 -->
## Fase 1: Extrair `_BackendOpenAI` (refatoração sem mudança de comportamento)

### Visão Geral
Mover a construção de parâmetros e a chamada à API da OpenAI (incluindo o gate de
reasoning e os branches stream/não-stream) de `enviar_mensagem()` para uma classe
`_BackendOpenAI`. `ChatComMemoria` passa a delegar a chamada ao modelo via `self.backend`.
Sem `PROVEDOR` ainda: o backend continua sendo sempre OpenAI, e o comportamento
observável é idêntico ao atual.

### Mudanças Necessárias:

#### 1. Nova classe `_BackendOpenAI`
**Arquivo**: `chat_openai_memoria.py`
**Mudanças**: Adicionar a classe (antes de `ChatComMemoria`). Recebe `api_key`,
`base_url` e `modelo`; cria o cliente; encapsula `_usa_parametros_reasoning()` (movido
de [L497-507](chat_openai_memoria.py#L497-L507)) e a lógica de [L531-559](chat_openai_memoria.py#L531-L559).

```python
class _BackendOpenAI:
    """Backend para a API da OpenAI (e provedores compatíveis via base_url)."""

    def __init__(self, *, api_key, base_url, modelo):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.modelo = modelo

    def _usa_parametros_reasoning(self) -> bool:
        modelo = self.modelo.lower()
        return modelo.startswith(("gpt-5", "o1", "o3", "o4"))

    def gerar(self, *, system_prompt, historico, temperature, max_tokens, stream) -> str:
        mensagens = [{"role": "system", "content": system_prompt}] + historico
        parametros = {"model": self.modelo, "messages": mensagens}
        if self._usa_parametros_reasoning():
            parametros["max_completion_tokens"] = max_tokens
        else:
            parametros["temperature"] = temperature
            parametros["max_tokens"] = max_tokens

        if stream:
            parametros["stream"] = True
            texto = ""
            for chunk in self.client.chat.completions.create(**parametros):
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end="", flush=True)
                    texto += delta
            return texto

        resposta = self.client.chat.completions.create(**parametros)
        return resposta.choices[0].message.content
```

#### 2. Instanciar o backend em `ChatComMemoria.__init__`
**Arquivo**: `chat_openai_memoria.py` (em torno de [L222-226](chat_openai_memoria.py#L222-L226))
**Mudanças**: Substituir a criação direta de `self.client` por:

```python
self.backend = _BackendOpenAI(
    api_key=self.api_key, base_url=self.base_url, modelo=self.modelo
)
```

Remover o método `_usa_parametros_reasoning()` de `ChatComMemoria` (movido para o backend).
Manter `self.modelo`, `self.temperature`, `self.max_tokens` como hoje (uso em log/export).

#### 3. Delegar a chamada em `enviar_mensagem()`
**Arquivo**: `chat_openai_memoria.py` (bloco [L531-559](chat_openai_memoria.py#L531-L559))
**Mudanças**: Trocar todo o build de `parametros` + branches por:

```python
resposta_texto = self.backend.gerar(
    system_prompt=self.system_prompt,
    historico=self.historico,
    temperature=self.temperature,
    max_tokens=self.max_tokens,
    stream=self.stream,
)
```

O restante de `enviar_mensagem()` (tokens antes/depois, sliding window, alertas, log)
permanece inalterado. O contrato de impressão do streaming é preservado (o `print`
delta a delta agora ocorre dentro de `backend.gerar`).

### Critérios de Sucesso:

#### Verificação Automatizada:
- [x] Compila: `python -m py_compile chat_openai_memoria.py exemplos_avancados.py`
- [x] Importa: `python -c "from chat_openai_memoria import ChatComMemoria, _BackendOpenAI; print('OK')"`
- [x] `ChatComMemoria` não tem mais `_usa_parametros_reasoning` e tem `backend`:
      `python -c "from chat_openai_memoria import ChatComMemoria as C; assert not hasattr(C,'_usa_parametros_reasoning'); assert '_BackendOpenAI'"`

#### Verificação Manual:
> Integração com serviço externo (API real da OpenAI) — não capturável por testes locais.
- [ ] Com `.env` apontando para OpenAI, `python chat_openai_memoria.py --exemplo` responde
      normalmente (modo não-stream) e com `OPENAI_STREAM=true` exibe token a token sem duplicar.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito.**

---

<!-- FASE: 2 -->
## Fase 2: Adicionar `_BackendBedrock`, seleção por `PROVEDOR` e UX ciente do provedor

### Visão Geral
Implementar o backend nativo do Bedrock (boto3 + Converse/ConverseStream), introduzir
a variável `PROVEDOR`, tornar a validação de configuração condicional ao provedor ativo,
montar o backend correto via uma pequena fábrica, e deixar o resumo de configuração, o
cabeçalho do log e as dicas de erro cientes do provedor. Adicionar `boto3` às dependências.

### Mudanças Necessárias:

#### 1. Nova classe `_BackendBedrock`
**Arquivo**: `chat_openai_memoria.py`
**Mudanças**: Adicionar a classe. Import de `boto3` **preguiçoso** (só dentro do
`__init__`, com erro amigável se faltar — mesmo padrão de degradação do `colorama`).
A conversão de histórico fica em `@staticmethod` para ser testável offline (sem boto3/rede).

```python
class _BackendBedrock:
    """Backend nativo do Amazon Bedrock via API Converse (boto3)."""

    def __init__(self, *, api_key, region, modelo):
        try:
            import boto3
        except ImportError as e:
            raise ImportError(
                "PROVEDOR=bedrock requer a biblioteca boto3. "
                "Instale com: pip install boto3>=1.40.0"
            ) from e
        # boto3 só aceita a Bedrock API key via variável de ambiente.
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.modelo = modelo

    @staticmethod
    def _para_converse(system_prompt, historico):
        """Converte o histórico interno para o schema da API Converse."""
        system = [{"text": system_prompt}] if system_prompt else []
        mensagens = [
            {"role": m["role"], "content": [{"text": m["content"]}]}
            for m in historico
        ]
        return system, mensagens

    def gerar(self, *, system_prompt, historico, temperature, max_tokens, stream) -> str:
        system, mensagens = self._para_converse(system_prompt, historico)
        inference = {"maxTokens": max_tokens, "temperature": temperature}

        if stream:
            resposta = self.client.converse_stream(
                modelId=self.modelo, messages=mensagens,
                system=system, inferenceConfig=inference,
            )
            texto = ""
            for evento in resposta["stream"]:
                if "contentBlockDelta" in evento:
                    delta = evento["contentBlockDelta"]["delta"].get("text", "")
                    if delta:
                        print(delta, end="", flush=True)
                        texto += delta
            return texto

        resposta = self.client.converse(
            modelId=self.modelo, messages=mensagens,
            system=system, inferenceConfig=inference,
        )
        return resposta["output"]["message"]["content"][0]["text"]
```

#### 2. Ler `PROVEDOR` e validação condicional em `ChatComMemoria.__init__`
**Arquivo**: `chat_openai_memoria.py` (após `load_dotenv()`, [L124-189](chat_openai_memoria.py#L124-L189))
**Mudanças**:
- Ler `PROVEDOR` (padrão `"openai"`), normalizar `lower()`, validar em `{"openai","bedrock"}`
  com erro claro.
- Os parâmetros compartilhados (`OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS`, `OPENAI_STREAM`,
  `MODO_DEBUG`, `JANELA_MAX`, `LIMITE_MAXIMO`) continuam sendo lidos como hoje.
- Mover a validação específica de OpenAI (`OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`)
  para dentro do ramo `provedor == "openai"`.
- Adicionar ramo `provedor == "bedrock"` exigindo `BEDROCK_API_KEY`, `BEDROCK_REGION`,
  `BEDROCK_MODEL` (mensagens de erro claras e acionáveis, no mesmo estilo das existentes).
- Definir `self.modelo` a partir de `OPENAI_MODEL` ou `BEDROCK_MODEL` conforme o provedor.

#### 3. Fábrica de backend
**Arquivo**: `chat_openai_memoria.py` (substitui a instanciação da Fase 1)
**Mudanças**:

```python
if self.provedor == "bedrock":
    self.backend = _BackendBedrock(
        api_key=self.bedrock_api_key, region=self.bedrock_region, modelo=self.modelo
    )
else:
    self.backend = _BackendOpenAI(
        api_key=self.api_key, base_url=self.base_url, modelo=self.modelo
    )
```

#### 4. Resumo de configuração, cabeçalho do log e dicas de erro cientes do provedor
**Arquivo**: `chat_openai_memoria.py`
**Mudanças**:
- Resumo inicial ([L240-260](chat_openai_memoria.py#L240-L260)): exibir `Provedor`
  (openai/bedrock) e, no Bedrock, `Região`; no OpenAI, manter `Base URL` quando houver.
- Cabeçalho do log ([L285-289](chat_openai_memoria.py#L285-L289)): registrar o provedor.
- Dica de erro de configuração ([L850-852](chat_openai_memoria.py#L850-L852)): mensagem
  genérica (mencionar `PROVEDOR` e as vars do provedor ativo), não mais fixa em `OPENAI_API_KEY`.

#### 5. Dependência boto3
**Arquivo**: `requirements.txt`
**Mudanças**: adicionar, com comentário, `boto3>=1.40.0` (necessário para autenticação por
Bedrock API key via `AWS_BEARER_TOKEN_BEDROCK`). Observar que só é necessário para `PROVEDOR=bedrock`.

### Critérios de Sucesso:

#### Verificação Automatizada:
- [ ] Compila: `python -m py_compile chat_openai_memoria.py`
- [ ] Importa as duas classes: `python -c "from chat_openai_memoria import _BackendBedrock; print('OK')"`
- [ ] Conversão Converse correta (offline, sem boto3/rede):
      `python -c "from chat_openai_memoria import _BackendBedrock as B; s,m=B._para_converse('SYS',[{'role':'user','content':'oi'}]); assert s==[{'text':'SYS'}]; assert m==[{'role':'user','content':[{'text':'oi'}]}]; print('OK')"`
- [ ] Validação condicional: com `PROVEDOR=bedrock` e sem `BEDROCK_*`, a inicialização
      falha com `ValueError` claro (teste via `.env` temporário ou variáveis de ambiente).

#### Verificação Manual:
> Integração com serviço externo (Amazon Bedrock real) — exige credenciais e rede.
- [ ] Com `.env` Bedrock válido (`PROVEDOR=bedrock`, `BEDROCK_API_KEY`, `BEDROCK_REGION`,
      `BEDROCK_MODEL=us.anthropic.claude-sonnet-4-6`), `python chat_openai_memoria.py` responde.
- [ ] Com `OPENAI_STREAM=true`, a resposta do Bedrock sai token a token, sem duplicação.
- [ ] O resumo inicial exibe `Provedor: bedrock` e a `Região`.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de iniciar a próxima fase. **Não avançar sem receber um comando explícito.**

---

## Estratégia de Testes

### Testes Unitários (offline, sem credenciais):
- `_BackendBedrock._para_converse`: histórico vazio, com system, multi-turno, mapeamento
  correto de `role`/`content`.
- `_BackendOpenAI._usa_parametros_reasoning`: `gpt-4o-mini` → False; `gpt-5`/`o3` → True.

### Testes de Integração (manuais, exigem credenciais/rede):
- Sessão real OpenAI (não-stream e stream) — regressão.
- Sessão real Bedrock (não-stream e stream) — nova funcionalidade.

### Etapas de Teste Manual:
1. `.env` OpenAI → `python chat_openai_memoria.py --exemplo` (confere regressão).
2. `.env` Bedrock → `python chat_openai_memoria.py`, enviar uma mensagem e validar resposta.
3. Alternar `OPENAI_STREAM=true/false` em cada provedor e confirmar a saída.

---

<!-- FASE: 3 -->
## Fase 3: Atualização da Documentação

**Esta fase é obrigatória e deve ser executada após as fases anteriores estarem concluídas
e validadas.**

Atualizar os documentos do projeto para refletir o suporte a múltiplos provedores e ao Bedrock:

- `env.example` — adicionar a seção `PROVEDOR` (openai|bedrock) e o bloco de variáveis
  `BEDROCK_API_KEY`/`BEDROCK_REGION`/`BEDROCK_MODEL`, com comentários; explicitar que
  `OPENAI_TEMPERATURE`/`OPENAI_MAX_TOKENS`/`OPENAI_STREAM` são compartilhadas pelos dois
  provedores; adicionar exemplo de `.env` Bedrock comentado.
- `README.md` — seção curta "Usando o AWS Bedrock" (pré-requisitos: `boto3`, Bedrock API key,
  região; exemplo de `.env`; nota de que a key é exposta via `AWS_BEARER_TOKEN_BEDROCK`).
- `AGENTS.md` — atualizar a seção de Arquitetura/Componente Principal para citar a camada
  de backend (`_BackendOpenAI`/`_BackendBedrock`) e o seletor `PROVEDOR`; ajustar o fluxo de dados.
- `docs/INSTALACAO.md` — incluir instalação do `boto3` e configuração do provedor Bedrock.
- `docs/TROUBLESHOOTING.md` — erros comuns do Bedrock (boto3 ausente, região inválida,
  modelo sem acesso, key inválida/expirada, faixa de `temperature` por modelo).
- `.notebook/bedrock-converse.md` — **novo**: fluxo do backend Bedrock e gotchas
  (key só via `AWS_BEARER_TOKEN_BEDROCK`; schema Converse; shape do stream
  `contentBlockDelta`; formato de model id; import preguiçoso de boto3). Linkar
  `[[streaming-output]]` e `[[gpt5-reasoning-api]]`.
- `.notebook/streaming-output.md` — atualizar: o `print` delta a delta agora ocorre
  dentro de `backend.gerar` (OpenAI e Bedrock), não mais em `enviar_mensagem`.
- `.notebook/INDEX.md` — adicionar a entrada `bedrock-converse` e atualizar a data.

### Critérios de Sucesso:

#### Verificação Manual:
- [ ] `env.example` permite copiar um `.env` Bedrock funcional sem adivinhação.
- [ ] `README.md`, `AGENTS.md`, `docs/INSTALACAO.md` e `docs/TROUBLESHOOTING.md` descrevem o
      Bedrock como **implementado** (não "planejado").
- [ ] `.notebook/INDEX.md` lista `bedrock-converse` e `.notebook/streaming-output.md` reflete
      a mudança do local de impressão.
- [ ] Nenhuma doc afirma que `OPENAI_API_KEY` é obrigatória quando `PROVEDOR=bedrock`.

#### ⛔ Pausa Obrigatória
- [ ] Aguardar confirmação explícita do usuário ou orquestrador antes de concluir. **Não encerrar sem comando explícito.**

---

## Considerações de Performance

Sem impacto relevante. O `boto3` é importado preguiçosamente apenas quando
`PROVEDOR=bedrock`, então usuários OpenAI não pagam custo de import nem dependência extra.
A latência passa a depender do endpoint/modelo do Bedrock escolhido.

## Referências

- Núcleo atual: [chat_openai_memoria.py:103](chat_openai_memoria.py#L103),
  chamada ao modelo em [L531-559](chat_openai_memoria.py#L531-L559).
- Suporte a base_url existente: [chat_openai_memoria.py:182-226](chat_openai_memoria.py#L182-L226).
- Gate de reasoning: [.notebook/gpt5-reasoning-api.md](.notebook/gpt5-reasoning-api.md).
- Contrato de streaming: [.notebook/streaming-output.md](.notebook/streaming-output.md).
- AWS — Chat Completions/Converse e endpoints do Bedrock (verificado jun/2026):
  docs.aws.amazon.com/bedrock (Converse, ConverseStream, API keys / `AWS_BEARER_TOKEN_BEDROCK`).
