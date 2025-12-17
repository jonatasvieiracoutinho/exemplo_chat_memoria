# ⚡ Exemplos Avançados

Técnicas avançadas para aproveitar ao máximo a memória conversacional.

## Índice

- [Como Executar](#como-executar)
- [1. Múltiplas Personalidades](#1-múltiplas-personalidades)
- [2. Controle de Contexto](#2-controle-de-contexto)
- [3. Conversas Longas (Sliding Window)](#3-conversas-longas-sliding-window)
- [4. Análise de Código Multi-turno](#4-análise-de-código-multi-turno)
- [5. Tratamento de Erros](#5-tratamento-de-erros)

---

## Como Executar

O arquivo `exemplos_avancados.py` oferece **duas formas de execução**:

### Via Flags de Linha de Comando

Execute exemplos específicos diretamente:

```bash
# Exemplo 1: Múltiplas personalidades
python exemplos_avancados.py --personalidades

# Exemplo 2: Controle de contexto
python exemplos_avancados.py --contexto

# Exemplo 3: Conversas longas
python exemplos_avancados.py --longa

# Exemplo 4: Tratamento de erros
python exemplos_avancados.py --erros

# Exemplo 5: Análise de código
python exemplos_avancados.py --analise

# Executar TODOS os exemplos em sequência
python exemplos_avancados.py --todos
```

### Via Menu Interativo

Execute sem argumentos para ver o menu:

```bash
python exemplos_avancados.py
```

**Menu:**

```
=== Exemplos Avançados de Chat com Memória ===

1. Múltiplas Personalidades
2. Controle de Contexto
3. Conversas Longas
4. Tratamento de Erros
5. Análise de Código
6. Executar Todos

Escolha uma opção (1-6) ou 'q' para sair: 
```

---

## 1. Múltiplas Personalidades

### Conceito

Criar **instâncias separadas** do chat, cada uma com personalidade diferente, para tarefas especializadas.

### Por que usar?

- Especialização em domínios diferentes
- Contextos isolados (um não interfere no outro)
- Simulação de equipes de especialistas

### Diagrama de Instâncias

```
+-------------------+          +-------------------+
|  Chat Professor   |          |  Chat Revisor     |
|-------------------|          |-------------------|
| System: "Ensine"  |          | System: "Revise"  |
|-------------------|          |-------------------|
| Histórico A       |          | Histórico B       |
| - Msg 1           |          | - Msg X           |
| - Msg 2           |          | - Msg Y           |
+-------------------+          +-------------------+
       |                              |
       v                              v
  Respostas didáticas          Respostas técnicas
```

### Código Exemplo

```python
from chat_openai_memoria import ChatComMemoria

# Instância 1: Professor didático
professor = ChatComMemoria()
professor.definir_system_prompt(
    "Você é um professor de programação experiente. "
    "Explique conceitos de forma clara e didática, "
    "usando analogias e exemplos práticos."
)

# Instância 2: Revisor técnico
revisor = ChatComMemoria()
revisor.definir_system_prompt(
    "Você é um revisor de código sênior. "
    "Analise código de forma crítica, identifique problemas "
    "e sugira melhorias seguindo melhores práticas."
)

# Mesmo assunto, respostas diferentes
assunto = "funções lambda em Python"

resp_professor = professor.enviar_mensagem(f"Explique {assunto}")
print(f"Professor: {resp_professor}\n")
# Resposta didática com exemplos simples

resp_revisor = revisor.enviar_mensagem(
    f"Analise o uso de {assunto} neste código: lambda x: x * 2"
)
print(f"Revisor: {resp_revisor}\n")
# Análise técnica focada em performance e legibilidade
```

### Casos de Uso

1. **Consultoria especializada**: Marketing, Vendas, Técnico
2. **Ensino multi-nível**: Professor, Tutor, Examinador
3. **Análise multifacetada**: Código, Segurança, Performance
4. **Simulação de equipe**: Líder, Desenvolvedor, QA

### Executar

```bash
python exemplos_avancados.py --personalidades
```

---

## 2. Controle de Contexto

### Conceito

**Limpar estrategicamente** o histórico para reduzir custos e focar em tópicos específicos.

### Por que usar?

- Redução de custos em conversas longas
- Mudança de assunto sem interferência
- Manutenção de foco em tópico atual

### Diagrama de Clearing Estratégico

```
Conversa sobre Python:
+------------------+
| User: Python?    |
| Asst: [resposta] |
| User: Decorators?|
| Asst: [resposta] |
+------------------+
       |
       | /limpar (clearing estratégico)
       v
+------------------+
| (memória vazia)  |
+------------------+
       |
       v
Conversa sobre JavaScript:
+------------------+
| User: JavaScript?|
| Asst: [resposta] |
+------------------+

Benefício: Resposta sobre JS sem contexto de Python
Economia: ~50-70% em tokens comparado a manter histórico
```

### Código Exemplo

```python
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria()

# Tópico 1: Python
print("=== Tópico: Python ===")
resp1 = chat.enviar_mensagem("Explique decorators em Python")
print(f"Resposta: {resp1}\n")

resp2 = chat.enviar_mensagem("Dê um exemplo prático")
print(f"Resposta: {resp2}\n")

print(f"Tokens acumulados: {chat.contar_tokens()}\n")

# Limpar antes de mudar de assunto
print("Limpando histórico para mudar de tópico...\n")
chat.limpar_historico()

# Tópico 2: JavaScript (sem contexto do Python)
print("=== Tópico: JavaScript ===")
resp3 = chat.enviar_mensagem("Explique closures em JavaScript")
print(f"Resposta: {resp3}\n")

print(f"Tokens após clearing: {chat.contar_tokens()}")
```

### Quando Limpar

✅ **Limpar quando:**
- Mudar completamente de assunto
- Conversa anterior não é relevante
- Tokens ultrapassaram limite desejado
- Começar sessão nova com cliente/usuário

❌ **NÃO limpar quando:**
- Perguntas relacionadas ao contexto anterior
- Análise multi-turno (código, documento)
- Continuidade é importante
- Referências anteriores são necessárias

### Executar

```bash
python exemplos_avancados.py --contexto
```

---

## 3. Conversas Longas (Sliding Window)

### Conceito

Manter apenas as **N mensagens mais recentes** para controlar custos em conversas extensas.

### Por que usar?

- Conversas muito longas ficam caras
- Contexto antigo pode ser irrelevante
- Limite de tokens do modelo pode ser atingido

### Diagrama de Sliding Window

```
Janela = 4 mensagens (2 interações)

Turno 1-2:
+-------+-------+-------+-------+
| Msg 1 | Msg 2 | Msg 3 | Msg 4 |
+-------+-------+-------+-------+
  [     Janela Completa      ]

Turno 3 (adiciona Msg 5 e 6):
+-------+-------+-------+-------+-------+-------+
| Msg 1 | Msg 2 | Msg 3 | Msg 4 | Msg 5 | Msg 6 |
+-------+-------+-------+-------+-------+-------+
 Remove  Remove          [   Janela Atual   ]

Turno 4 (adiciona Msg 7 e 8):
+-------+-------+-------+-------+-------+-------+
| Msg 3 | Msg 4 | Msg 5 | Msg 6 | Msg 7 | Msg 8 |
+-------+-------+-------+-------+-------+-------+
                        [   Janela Atual   ]
```

### Código Exemplo

```python
from chat_openai_memoria import ChatComMemoria

# Configuração
MAX_TOKENS = 500  # Limite de tokens desejado
TAMANHO_JANELA = 4  # Manter últimas 4 mensagens (2 interações)

chat = ChatComMemoria()

# Simular conversa longa
perguntas = [
    "O que é Python?",
    "Quais são os tipos de dados?",
    "Explique listas",
    "E dicionários?",
    "Como funcionam loops?",
    "O que são funções?",
    "Explique classes",
    "O que é herança?"
]

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n--- Pergunta {i} ---")
    print(f"Você: {pergunta}")
    
    resposta = chat.enviar_mensagem(pergunta)
    print(f"Assistente: {resposta[:100]}...")
    
    tokens = chat.contar_tokens()
    print(f"Tokens: {tokens} | Mensagens: {len(chat.historico)}")
    
    # Aplicar sliding window quando necessário
    if tokens > MAX_TOKENS:
        print(f"⚠️  Limite de {MAX_TOKENS} tokens atingido!")
        print(f"   Aplicando sliding window (mantendo {TAMANHO_JANELA} mensagens)")
        
        # Manter apenas as últimas N mensagens
        chat.historico = chat.historico[-TAMANHO_JANELA:]
        
        print(f"   Tokens após janela: {chat.contar_tokens()}")
```

### Comparação: Com vs Sem Sliding Window

```
Sem Sliding Window (8 interações):
+------------------------------------------+
| Histórico: 16 mensagens                  |
| Tokens: ~2400                            |
| Custo por requisição: Alto e crescente   |
+------------------------------------------+

Com Sliding Window (janela = 4):
+------------------------------------------+
| Histórico: 4 mensagens (sempre)          |
| Tokens: ~300-400 (estável)               |
| Custo por requisição: Baixo e constante  |
+------------------------------------------+

Economia: ~85% em conversas longas
```

### Estratégias de Tamanho

| Tamanho da Janela | Tokens Aprox. | Uso Recomendado |
|-------------------|---------------|-----------------|
| 2 mensagens       | 100-200       | Chat rápido, FAQ simples |
| 4 mensagens       | 200-400       | Conversas curtas |
| 8 mensagens       | 400-800       | Contexto médio (recomendado) |
| 12 mensagens      | 600-1200      | Contexto amplo |

### Limitações

⚠️ **Contexto distante é perdido:**
- Informações além da janela não são lembradas
- Referências antigas não funcionam
- Pode perder coerência em tópicos longos

💡 **Solução:** Use janelas maiores para tópicos que exigem contexto extenso.

### Executar

```bash
python exemplos_avancados.py --longa
```

---

## 4. Análise de Código Multi-turno

### Conceito

Usar a memória para **análise aprofundada** em múltiplas etapas sobre o mesmo código.

### Por que usar?

- Análises complexas exigem múltiplas perguntas
- Contexto do código mantido ao longo da conversa
- Perguntas de acompanhamento naturais

### Diagrama de Análise

```
Turno 1: Envio do Código
+-------------------------+
| User: [código Python]   |
+-------------------------+
         |
         v
+-------------------------+
| Asst: Análise geral     |
| - Estrutura OK          |
| - Falta tratamento erro |
+-------------------------+
         |
         v
Turno 2: Aprofundamento
+-------------------------+
| User: "Quais erros      |
|        você viu?"       |
+-------------------------+
         |
         v
+-------------------------+
| Asst: [detalha erros    |
|        do código        |
|        analisado]       |
+-------------------------+
         |
         v
Turno 3: Melhorias
+-------------------------+
| User: "Como melhorar?"  |
+-------------------------+
         |
         v
+-------------------------+
| Asst: [sugere melhorias |
|        no código        |
|        analisado]       |
+-------------------------+
```

### Código Exemplo

```python
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria()
chat.definir_system_prompt(
    "Você é um revisor de código Python experiente. "
    "Analise código criticamente e forneça feedback detalhado."
)

# Código a ser analisado
codigo = '''
def processar_dados(dados):
    resultado = []
    for item in dados:
        if item > 0:
            resultado.append(item * 2)
    return resultado
'''

# Turno 1: Enviar código
print("=== Análise Inicial ===")
resp1 = chat.enviar_mensagem(
    f"Analise este código Python:\n\n```python\n{codigo}\n```"
)
print(resp1)

# Turno 2: Perguntar sobre problemas (usa contexto do código)
print("\n=== Identificar Problemas ===")
resp2 = chat.enviar_mensagem(
    "Quais problemas ou limitações você identifica no código?"
)
print(resp2)

# Turno 3: Solicitar melhorias (ainda sobre o mesmo código)
print("\n=== Sugerir Melhorias ===")
resp3 = chat.enviar_mensagem(
    "Como posso refatorar esse código para melhorar performance?"
)
print(resp3)

# Turno 4: Código refatorado (assistente lembra do contexto)
print("\n=== Código Refatorado ===")
resp4 = chat.enviar_mensagem(
    "Mostre o código refatorado aplicando suas sugestões"
)
print(resp4)
```

### Benefícios da Memória

✅ **Não precisa reenviar código:** Assistente lembra  
✅ **Perguntas naturais:** "Como melhorar?" em vez de "Como melhorar o código X que enviei?"  
✅ **Continuidade:** Cada resposta considera as anteriores  
✅ **Profundidade:** Análise incremental e detalhada  

### Casos de Uso

1. **Code Review:** Análise → Problemas → Melhorias → Refatoração
2. **Debug:** Código → Erro → Causa → Solução
3. **Otimização:** Código → Benchmarks → Gargalos → Otimizações
4. **Documentação:** Código → Propósito → Exemplos → Testes

### Executar

```bash
python exemplos_avancados.py --analise
```

---

## 5. Tratamento de Erros

### Conceito

Documentação dos **erros comuns** que podem ocorrer e como testá-los.

### Por que importante?

- Entender mensagens de erro
- Validar configuração
- Debug rápido de problemas

### Tipos de Erros

#### 1. Arquivo .env Não Encontrado

**Erro:**
```
FileNotFoundError: Arquivo .env não encontrado.
Crie um arquivo .env na raiz do projeto com as configurações necessárias.
```

**Causa:** Arquivo `.env` não existe ou está em local errado

**Solução:**
```bash
# Criar arquivo .env na raiz do projeto
touch .env  # Linux/macOS
New-Item .env  # Windows PowerShell
```

#### 2. API Key Inválida

**Erro:**
```
ValueError: OPENAI_API_KEY não encontrada no arquivo .env
```

**Causa:** Variável `OPENAI_API_KEY` não está definida

**Solução:**
```env
# Adicionar no .env:
OPENAI_API_KEY=sk-proj-sua_chave_aqui
```

#### 3. Temperature Inválida

**Erro:**
```
ValueError: OPENAI_TEMPERATURE deve estar entre 0.0 e 2.0. Valor atual: 3.5
```

**Causa:** Temperature fora do range 0.0-2.0

**Solução:**
```env
# Corrigir no .env:
OPENAI_TEMPERATURE=0.7  # Valor válido
```

#### 4. Max Tokens Inválido

**Erro:**
```
ValueError: OPENAI_MAX_TOKENS deve ser um número inteiro positivo. Valor atual: -100
```

**Causa:** Max tokens não é inteiro positivo

**Solução:**
```env
# Corrigir no .env:
OPENAI_MAX_TOKENS=1000  # Inteiro positivo
```

#### 5. Erro de Autenticação na API

**Erro (durante envio de mensagem):**
```
openai.AuthenticationError: Invalid API key
```

**Causa:** API key incorreta ou expirada

**Solução:**
1. Verificar key em [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Gerar nova key se necessário
3. Atualizar `.env` com key válida

#### 6. Rate Limit

**Erro:**
```
openai.RateLimitError: Rate limit exceeded
```

**Causa:** Muitas requisições em curto período

**Solução:**
- Aguardar alguns segundos
- Implementar retry com backoff
- Verificar plano da API (limites)

### Como Testar Erros

```python
from chat_openai_memoria import ChatComMemoria

# Teste 1: Sem .env (renomear temporariamente)
try:
    chat = ChatComMemoria()
except FileNotFoundError as e:
    print(f"✅ Erro esperado: {e}")

# Teste 2: Temperature inválida (editar .env com valor 3.0)
try:
    chat = ChatComMemoria()
except ValueError as e:
    print(f"✅ Erro esperado: {e}")

# Teste 3: Max tokens inválido (editar .env com valor -1)
try:
    chat = ChatComMemoria()
except ValueError as e:
    print(f"✅ Erro esperado: {e}")
```

### Executar

```bash
python exemplos_avancados.py --erros
```

**Nota:** Este exemplo apenas **documenta** os erros. Não executa testes reais para não comprometer seu `.env`.

---

## Comparação dos Exemplos

| Exemplo | Foco | Redução de Custo | Complexidade |
|---------|------|------------------|--------------|
| **Múltiplas Personalidades** | Especialização | - | Baixa |
| **Controle de Contexto** | Mudança de tópico | ⭐⭐⭐ Alta | Baixa |
| **Sliding Window** | Conversas longas | ⭐⭐⭐ Alta | Média |
| **Análise Multi-turno** | Profundidade | - | Baixa |
| **Tratamento de Erros** | Configuração | - | Baixa |

---

## Executar Todos os Exemplos

```bash
# Executa os 5 exemplos em sequência
python exemplos_avancados.py --todos
```

---

## Próximos Passos

- 🧠 Aprofunde-se em [GERENCIAMENTO_MEMORIA.md](GERENCIAMENTO_MEMORIA.md) para estratégias avançadas
- 💡 Veja aplicações práticas em [CASOS_DE_USO.md](CASOS_DE_USO.md)
- 🔧 Consulte [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para resolver problemas
