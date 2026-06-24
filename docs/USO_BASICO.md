# 🚀 Uso Básico

Aprenda a usar o chat com memória nos três modos disponíveis.

## Índice

- [Modo Interativo](#modo-interativo)
- [Persistência de Conversas (Threads)](#persistência-de-conversas-threads)
- [Modo Programático](#modo-programático)
- [Uso como Biblioteca](#uso-como-biblioteca)
- [Referência dos Métodos](#referência-dos-métodos)

---

## Modo Interativo

O modo interativo permite conversar diretamente pelo terminal.

### Iniciar o Chat

```bash
python chat_openai_memoria.py
```

### Interface

```
=== Configuração do Chat ===
Modelo: gpt-4o-mini
Temperatura: 0.7
Max Tokens: 1000
============================

Chat com Memória - Digite 'sair' para encerrar
Você: 
```

### Comandos Especiais

O chat possui comandos que começam com `/` para funções especiais:

#### `/limpar` - Limpar Memória

Apaga todo o histórico da conversa.

```
Você: /limpar
Histórico limpo!

Você: 
```

**Quando usar:**
- Mudar completamente de assunto
- Reduzir custos em conversas longas
- Recomeçar sem contexto anterior

**Diagrama:**

```
Antes:                   Depois:
+-------------+          +-------------+
| Msg 1       |          |             |
| Msg 2       |   /limpar   |  (vazio)    |
| Msg 3       |   ----->    |             |
| Msg 4       |          |             |
+-------------+          +-------------+
```

#### `/historico` - Ver Histórico

Exibe todas as mensagens da conversa atual.

```
Você: /historico

=== Histórico da Conversa ===

[user]: Olá, como você funciona?

[assistant]: Olá! Sou um assistente de IA com memória conversacional...

[user]: Você lembra da primeira pergunta?

[assistant]: Sim! Você perguntou como eu funciono...

=============================
```

**Quando usar:**
- Revisar o que foi discutido
- Verificar se o contexto está correto
- Debug de problemas de memória

#### `/tokens` - Contar Tokens

Mostra estimativa de tokens usados na conversa.

```
Você: /tokens
Tokens estimados no histórico: 342
```

**Quando usar:**
- Monitorar custos
- Decidir quando limpar memória
- Planejar conversas longas

**Nota:** A estimativa usa a regra **~4 caracteres = 1 token**. O valor real pode variar.

#### `/exportar` - Exportar Conversa

Salva a conversa em um arquivo de texto.

```
Você: /exportar
Conversa exportada para: conversa_20241217_143022.txt

# Ou especificar nome:
Você: /exportar minha_analise.txt
Conversa exportada para: minha_analise.txt
```

**Formato do arquivo:**

```
=== Conversa exportada em 17/12/2024 14:30:22 ===
Modelo: gpt-4o-mini

[user]: Explique decorators em Python

[assistant]: Decorators são funções que modificam...

[user]: Dê um exemplo prático

[assistant]: Aqui está um exemplo...
```

**Quando usar:**
- Documentar análises ou revisões
- Compartilhar conversas
- Backup de sessões importantes

#### `/sair` - Encerrar Chat

Encerra o programa.

```
Você: /sair
Encerrando chat...
```

**Alternativas:**
- `sair` (sem barra)
- `Ctrl+C` (interrompe o programa)

### Exemplo de Sessão Completa

```
=== Configuração do Chat ===
Modelo: gpt-4o-mini
Temperatura: 0.7
Max Tokens: 1000
============================

Chat com Memória - Digite 'sair' para encerrar

Você: Olá! Meu nome é João
Assistente: Olá, João! É um prazer conhecê-lo. Como posso ajudá-lo hoje?

Você: Qual é o meu nome?
Assistente: Seu nome é João, conforme você me disse há pouco.

Você: /tokens
Tokens estimados no histórico: 87

Você: /exportar conversa_joao.txt
Conversa exportada para: conversa_joao.txt

Você: /limpar
Histórico limpo!

Você: Você sabe meu nome?
Assistente: Não, você ainda não me disse seu nome. Como você se chama?

Você: /sair
Encerrando chat...
```

---

## Persistência de Conversas (Threads)

O chat suporta persistência local de conversas usando SQLite. Quando ativada, cada conversa é salva automaticamente e pode ser retomada em sessões futuras.

### Ativar a Persistência

No arquivo `.env`, defina:

```env
PERSISTENCIA_SQLITE=true
```

O banco de dados `chat_memoria.db` será criado automaticamente na raiz do projeto. Ele **não é versionado** pelo git.

### Tela de Seleção de Thread

Ao iniciar o chat com persistência ativa, o sistema exibe a lista de conversas salvas e solicita uma escolha antes de entrar no loop:

```
  SELECIONAR CONVERSA

  Conversas armazenadas
  ──────────────────────────────────────────────────────────────
    1  Dúvidas sobre Python decorators          2026-06-24 10:30  (4 msg)
    2  Revisão de código do projeto X           2026-06-24 11:15  (12 msg)
  ──────────────────────────────────────────────────────────────
    0  Nova conversa

  Selecione o ID (ou 0 para nova): 
```

- Digite `0` para iniciar uma nova conversa
- Digite o ID de uma conversa existente para retomá-la

### Comandos de Thread

Dentro do chat interativo, três comandos adicionais ficam disponíveis quando a persistência está ativa:

#### `/threads` — Listar Conversas

Exibe a lista de todas as conversas salvas no banco.

```
Você: /threads

  Conversas armazenadas
  ──────────────────────────────────────────────────────────────
    1  Dúvidas sobre Python decorators          2026-06-24 10:30  (4 msg)
    2  Revisão de código do projeto X           2026-06-24 11:15  (12 msg)
  ──────────────────────────────────────────────────────────────
```

#### `/retomar <id>` — Retomar uma Conversa

Carrega o histórico de uma conversa salva e a torna a conversa ativa.

```
Você: /retomar 1
  ✔ Thread #1 carregada (4 mensagens).
```

O histórico carregado respeita a janela deslizante configurada (`JANELA_MAX`). As mensagens anteriores continuam intactas no banco.

#### `/excluir <id>` — Excluir uma Conversa

Remove permanentemente uma conversa e todas as suas mensagens do banco. A exclusão é irreversível.

```
Você: /excluir 2
  Excluir thread #2? Esta ação é irreversível. (s/n): s
  Thread #2 excluída.
```

Se a thread excluída for a conversa ativa, o histórico em memória é limpo e uma nova conversa é iniciada automaticamente.

### Comportamento do `/limpar` com Persistência Ativa

O comando `/limpar` apaga apenas o histórico **em memória**. As mensagens já salvas no banco SQLite são preservadas:

```
Você: /limpar
  ℹ  Histórico em memória limpo. Mensagens no banco SQLite foram preservadas.
```

Para remover permanentemente uma conversa, use `/excluir <id>`.

### Títulos das Conversas

O título de uma nova thread é gerado automaticamente a partir dos primeiros 60 caracteres da primeira mensagem do usuário. Se a mensagem estiver em branco, o título será `"Conversa sem título"`. O título não é alterado ao retomar uma thread existente.

### Banco de Dados

- **Localização:** `chat_memoria.db` na raiz do projeto
- **Formato:** SQLite 3 (arquivo único, sem servidor)
- **Backup:** Copie o arquivo `chat_memoria.db` para fazer backup de todas as conversas
- **Segurança:** O arquivo não é versionado pelo git (`.gitignore`)

---

## Modo Programático

Execute um exemplo demonstrativo que mostra o uso da memória.

### Executar

```bash
python chat_openai_memoria.py --exemplo
```

### O que faz?

O exemplo demonstra:

1. **Contexto acumulado** - Perguntas sequenciais que dependem de respostas anteriores
2. **Preservação de memória** - Referências a informações mencionadas antes
3. **Estatísticas** - Contagem de mensagens e tokens
4. **Exportação automática** - Salva a conversa ao final

### Código do Exemplo

```python
def exemplo_uso():
    chat = ChatComMemoria()
    
    # Pergunta 1: Estabelece contexto
    resposta = chat.enviar_mensagem("Olá! Vou te fazer algumas perguntas sobre Python.")
    print(f"Assistente: {resposta}\n")
    
    # Pergunta 2: Usa contexto
    resposta = chat.enviar_mensagem("O que são decorators?")
    print(f"Assistente: {resposta}\n")
    
    # Pergunta 3: Referencia resposta anterior
    resposta = chat.enviar_mensagem("Pode dar um exemplo do que você acabou de explicar?")
    print(f"Assistente: {resposta}\n")
    
    # Estatísticas
    print(f"Total de mensagens: {len(chat.historico)}")
    print(f"Tokens estimados: {chat.contar_tokens()}")
    
    # Exporta conversa
    chat.exportar_conversa("exemplo_automatico.txt")
```

### Saída Esperada

```
Assistente: Olá! Fico feliz em responder suas perguntas sobre Python...

Assistente: Decorators em Python são funções que modificam o comportamento...

Assistente: Claro! Aqui está um exemplo de decorator:
[código exemplo]

Total de mensagens no histórico: 6
Tokens estimados: 523
Conversa exportada para: exemplo_automatico.txt
```

---

## Uso como Biblioteca

Integre o chat em seus próprios scripts Python.

### Importar e Inicializar

```python
from chat_openai_memoria import ChatComMemoria

# Inicializa (carrega .env automaticamente)
chat = ChatComMemoria()
```

### Tratamento de Erros

**Importante:** A inicialização valida todas as configurações. Use `try/except`:

```python
from chat_openai_memoria import ChatComMemoria

try:
    chat = ChatComMemoria()
    print("Chat inicializado com sucesso!")
except FileNotFoundError as e:
    print(f"Erro: {e}")
    print("Crie um arquivo .env com as configurações necessárias")
except ValueError as e:
    print(f"Erro de configuração: {e}")
    print("Verifique os valores no arquivo .env")
except Exception as e:
    print(f"Erro inesperado: {e}")
```

### Exemplo: Bot de Suporte

```python
from chat_openai_memoria import ChatComMemoria

def bot_suporte():
    chat = ChatComMemoria()
    chat.definir_system_prompt(
        "Você é um assistente de suporte técnico. "
        "Seja educado, claro e resolva problemas passo a passo."
    )
    
    print("Bot de Suporte - Digite 'sair' para encerrar\n")
    
    while True:
        pergunta = input("Cliente: ")
        if pergunta.lower() == 'sair':
            break
        
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Suporte: {resposta}\n")
        
        # Monitorar tokens
        if chat.contar_tokens() > 2000:
            print("[Sistema: Conversa longa detectada. Considere limpar histórico]")

if __name__ == "__main__":
    bot_suporte()
```

### Exemplo: Análise de Código

```python
from chat_openai_memoria import ChatComMemoria

def analisar_codigo(codigo):
    chat = ChatComMemoria()
    chat.definir_system_prompt(
        "Você é um revisor de código expert. "
        "Analise código Python e forneça feedback construtivo."
    )
    
    # Enviar código para análise
    resposta1 = chat.enviar_mensagem(
        f"Analise este código Python:\n\n```python\n{codigo}\n```"
    )
    print("Análise inicial:", resposta1)
    
    # Perguntas de acompanhamento (usa memória)
    resposta2 = chat.enviar_mensagem(
        "Quais são os principais problemas que você identificou?"
    )
    print("\nProblemas:", resposta2)
    
    resposta3 = chat.enviar_mensagem(
        "Como posso melhorar o código que você analisou?"
    )
    print("\nMelhorias:", resposta3)
    
    # Exportar análise completa
    chat.exportar_conversa("analise_codigo.txt")

# Uso
codigo_exemplo = '''
def calcular(a, b):
    return a + b
'''

analisar_codigo(codigo_exemplo)
```

### Exemplo: Sistema de Perguntas e Respostas

```python
from chat_openai_memoria import ChatComMemoria

def qa_system(perguntas_lista):
    chat = ChatComMemoria()
    respostas = []
    
    for i, pergunta in enumerate(perguntas_lista, 1):
        print(f"\nPergunta {i}: {pergunta}")
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Resposta: {resposta}")
        respostas.append({"pergunta": pergunta, "resposta": resposta})
    
    # Estatísticas finais
    print(f"\n--- Estatísticas ---")
    print(f"Perguntas processadas: {len(perguntas_lista)}")
    print(f"Mensagens no histórico: {len(chat.historico)}")
    print(f"Tokens estimados: {chat.contar_tokens()}")
    
    return respostas

# Uso
perguntas = [
    "O que é Python?",
    "Quais são as principais características da linguagem que você mencionou?",
    "Dê exemplos de aplicações práticas"
]

resultados = qa_system(perguntas)
```

---

## Referência dos Métodos

### Construtor

```python
ChatComMemoria()
```

**Descrição:** Inicializa o chat carregando configurações do `.env`.

**Validações:**
- Verifica existência do arquivo `.env`
- Valida `OPENAI_API_KEY` (deve começar com `sk-`)
- Valida `OPENAI_MODEL` (obrigatório)
- Valida `OPENAI_TEMPERATURE` (0.0 a 2.0)
- Valida `OPENAI_MAX_TOKENS` (inteiro positivo)

**Exceções:**
- `FileNotFoundError` - Arquivo `.env` não encontrado
- `ValueError` - Configurações inválidas

**Exemplo:**
```python
try:
    chat = ChatComMemoria()
except FileNotFoundError:
    print("Crie o arquivo .env")
except ValueError as e:
    print(f"Configuração inválida: {e}")
```

---

### definir_system_prompt()

```python
definir_system_prompt(prompt: str)
```

**Descrição:** Define a personalidade e comportamento do assistente.

**Parâmetros:**
- `prompt` (str) - Instrução de sistema para o assistente

**Retorno:** None

**Exemplo:**
```python
chat = ChatComMemoria()

# Assistente técnico
chat.definir_system_prompt(
    "Você é um engenheiro de software sênior. "
    "Forneça explicações técnicas precisas e exemplos de código."
)

# Professor
chat.definir_system_prompt(
    "Você é um professor paciente de programação. "
    "Explique conceitos de forma didática e use analogias."
)
```

---

### enviar_mensagem()

```python
enviar_mensagem(mensagem: str) -> str
```

**Descrição:** Envia uma mensagem e recebe resposta, mantendo contexto.

**Parâmetros:**
- `mensagem` (str) - Mensagem do usuário

**Retorno:** Resposta do assistente (str)

**Comportamento:**
1. Adiciona mensagem ao histórico
2. Envia todo histórico + system prompt para API
3. Recebe resposta
4. Adiciona resposta ao histórico
5. Retorna resposta

**Exemplo:**
```python
chat = ChatComMemoria()

# Primeira mensagem
resp1 = chat.enviar_mensagem("Olá!")
print(resp1)  # "Olá! Como posso ajudar?"

# Segunda mensagem (com contexto)
resp2 = chat.enviar_mensagem("Qual foi minha primeira mensagem?")
print(resp2)  # "Sua primeira mensagem foi 'Olá!'"
```

---

### limpar_historico()

```python
limpar_historico()
```

**Descrição:** Remove todas as mensagens do histórico.

**Retorno:** None

**Exemplo:**
```python
chat = ChatComMemoria()
chat.enviar_mensagem("Mensagem 1")
chat.enviar_mensagem("Mensagem 2")

print(len(chat.historico))  # 4 (2 user + 2 assistant)

chat.limpar_historico()

print(len(chat.historico))  # 0
```

---

### exibir_historico()

```python
exibir_historico()
```

**Descrição:** Imprime todas as mensagens formatadas no console.

**Retorno:** None

**Formato:**
```
=== Histórico da Conversa ===

[user]: Mensagem do usuário

[assistant]: Resposta do assistente

=============================
```

**Exemplo:**
```python
chat = ChatComMemoria()
chat.enviar_mensagem("Olá")
chat.enviar_mensagem("Tudo bem?")
chat.exibir_historico()
```

---

### contar_tokens()

```python
contar_tokens() -> int
```

**Descrição:** Estima quantidade de tokens no histórico.

**Método:** Usa aproximação de **4 caracteres = 1 token**

**Retorno:** Número estimado de tokens (int)

**Exemplo:**
```python
chat = ChatComMemoria()
chat.enviar_mensagem("Mensagem curta")

tokens = chat.contar_tokens()
print(f"Tokens: {tokens}")  # Ex: Tokens: 45

if tokens > 1000:
    print("Histórico grande, considere limpar")
    chat.limpar_historico()
```

---

### exportar_conversa()

```python
exportar_conversa(nome_arquivo: str = None)
```

**Descrição:** Salva histórico em arquivo de texto.

**Parâmetros:**
- `nome_arquivo` (str, opcional) - Nome do arquivo. Se omitido, gera automaticamente

**Nome automático:** `conversa_YYYYMMDD_HHMMSS.txt`

**Formato do arquivo:**
```
=== Conversa exportada em DD/MM/YYYY HH:MM:SS ===
Modelo: gpt-4o-mini

[user]: Mensagem 1

[assistant]: Resposta 1

[user]: Mensagem 2

[assistant]: Resposta 2
```

**Exemplo:**
```python
chat = ChatComMemoria()
chat.enviar_mensagem("Olá")
chat.enviar_mensagem("Como vai?")

# Nome automático
chat.exportar_conversa()
# Cria: conversa_20241217_143022.txt

# Nome específico
chat.exportar_conversa("sessao_cliente_01.txt")
# Cria: sessao_cliente_01.txt
```

---

## Próximos Passos

- ⚡ Explore técnicas avançadas em [EXEMPLOS_AVANCADOS.md](EXEMPLOS_AVANCADOS.md)
- 🧠 Aprenda a gerenciar memória eficientemente em [GERENCIAMENTO_MEMORIA.md](GERENCIAMENTO_MEMORIA.md)
- 💡 Veja aplicações práticas em [CASOS_DE_USO.md](CASOS_DE_USO.md)
