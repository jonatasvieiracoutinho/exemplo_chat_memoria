# 🧠 Gerenciamento de Memória

Estratégias para controlar custos e otimizar o uso de memória conversacional.

## Índice

- [Por que Gerenciar Memória?](#por-que-gerenciar-memória)
- [Estratégia 1: Limpeza Manual](#estratégia-1-limpeza-manual)
- [Estratégia 2: Sliding Window](#estratégia-2-sliding-window)
- [Estratégia 3: Monitoramento de Tokens](#estratégia-3-monitoramento-de-tokens)
- [Sistema Completo (Recomendado)](#sistema-completo-recomendado)
- [Modo Debug](#modo-debug)
- [Comparação de Estratégias](#comparação-de-estratégias)
- [Ferramentas de Diagnóstico](#ferramentas-de-diagnóstico)

---

## Por que Gerenciar Memória?

### O Problema do Crescimento

```
Requisição 1:
+-----------+
| 100 tokens|  Custo: $0.001
+-----------+

Requisição 5:
+-----------+
| 500 tokens|  Custo: $0.005
+-----------+

Requisição 10:
+------------+
| 1000 tokens|  Custo: $0.010
+------------+

Requisição 20:
+------------+
| 2000 tokens|  Custo: $0.020
+------------+

Sem gerenciamento: Custo cresce linearmente!
```

### Impacto em Custos

**Exemplo de conversa longa (30 interações sem gerenciamento):**

```
Interação 1:  100 tokens  →  $0.001
Interação 5:  500 tokens  →  $0.005
Interação 10: 1000 tokens →  $0.010
Interação 15: 1500 tokens →  $0.015
Interação 20: 2000 tokens →  $0.020
Interação 25: 2500 tokens →  $0.025
Interação 30: 3000 tokens →  $0.030

Custo total: ~$0.35 para 30 mensagens
```

**Com gerenciamento (sliding window de 8 pares):**

```
Interação 1:  100 tokens  →  $0.001
Interação 5:  400 tokens  →  $0.004
Interação 10: 400 tokens  →  $0.004
Interação 15: 400 tokens  →  $0.004
Interação 20: 400 tokens  →  $0.004
Interação 25: 400 tokens  →  $0.004
Interação 30: 400 tokens  →  $0.004

Custo total: ~$0.12 para 30 mensagens

Economia: 66% de redução!
```

### Outros Problemas

❌ **Lentidão:** Mais tokens = mais tempo de processamento  
❌ **Limite de modelo:** Modelos têm limite máximo de tokens  
❌ **Contexto irrelevante:** Informações antigas podem confundir  
❌ **Perda de foco:** Tópicos distantes diluem atenção do modelo  

---

## Estratégia 1: Limpeza Manual

### O que é?

Usar o comando `/limpar` ou método `limpar_historico()` para **zerar a memória** quando apropriado.

### Diagrama

```
Estado Inicial:
+------------------+
| Msg 1            |
| Msg 2            |
| Msg 3            |
| Msg 4            |
+------------------+
   4000 tokens
        |
        | /limpar
        v
+------------------+
|    (vazio)       |
+------------------+
     0 tokens
        |
        | Nova conversa
        v
+------------------+
| Msg 5            |
| Msg 6            |
+------------------+
   300 tokens
```

### Quando Usar

✅ **Limpar quando:**
- Mudar completamente de assunto
- Cliente/sessão diferente
- Atingir limite de custos desejado
- Contexto anterior não é mais necessário
- Começar análise de novo documento/código

❌ **NÃO limpar quando:**
- Perguntas relacionadas ao contexto
- Análise incremental em andamento
- Continuidade é importante

### Código Exemplo

```python
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria()

# Sessão 1
chat.enviar_mensagem("Analise este código Python: ...")
chat.enviar_mensagem("Quais são os problemas?")
chat.enviar_mensagem("Como melhorar?")

print(f"Tokens sessão 1: {chat.contar_tokens_aproximado()}")

# Finalizar sessão 1, começar sessão 2
chat.limpar_historico()

# Sessão 2 (independente)
chat.enviar_mensagem("Explique JavaScript closures")
print(f"Tokens sessão 2: {chat.contar_tokens_aproximado()}")
```

### Modo Interativo

```bash
$ python chat_openai_memoria.py

Você: Explique Python
Assistente: Python é uma linguagem...

Você: /limpar
Histórico limpo - memória apagada

Você: Agora explique JavaScript
Assistente: JavaScript é uma linguagem...
```

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Simples de implementar | ❌ Perde TODO o contexto |
| ✅ Redução máxima de custos | ❌ Decisão manual |
| ✅ Controle total | ❌ Pode limpar cedo demais |

---

## Estratégia 2: Sliding Window

### O que é?

Manter apenas as **N pares de mensagens mais recentes** (user + assistant), descartando automaticamente as antigas. Esta estratégia está **implementada nativamente** na classe `ChatComMemoria`.

### Diagrama Detalhado

```
Janela de 3 pares (6 mensagens):

Passo 1: Conversa normal (dentro da janela)
+-----+-----+-----+-----+-----+-----+
| U1  | A1  | U2  | A2  | U3  | A3  |
+-----+-----+-----+-----+-----+-----+
[          Janela Atual          ]
Tokens: 400

Passo 2: Adiciona U4 e A4 (excede janela)
+-----+-----+-----+-----+-----+-----+-----+-----+
| U1  | A1  | U2  | A2  | U3  | A3  | U4  | A4  |
+-----+-----+-----+-----+-----+-----+-----+-----+
 [XX]  [XX]        [    Janela Atual     ]
Remove U1 e A1
Tokens: 400 (estável)

Passo 3: Adiciona U5 e A5
+-----+-----+-----+-----+-----+-----+-----+-----+
| U2  | A2  | U3  | A3  | U4  | A4  | U5  | A5  |
+-----+-----+-----+-----+-----+-----+-----+-----+
 [XX]  [XX]        [    Janela Atual       ]
Remove U2 e A2
Tokens: 400 (estável)
```

### Configuração

**Opção 1: Via `.env` (Recomendado)**

```env
# No arquivo .env
JANELA_MAX=8  # Mantém 8 pares (16 mensagens)
```

**Opção 2: Via Construtor**

```python
from chat_openai_memoria import ChatComMemoria

# Janela de 6 pares (12 mensagens)
chat = ChatComMemoria(tamanho_janela=6)

# Conversa longa - janela aplicada automaticamente
for i in range(20):
    resposta = chat.enviar_mensagem(f"Pergunta {i+1}")
    print(f"Mensagens mantidas: {len(chat.historico)}")
```

**Opção 3: Ambas (`.env` como padrão)**

```python
# .env tem JANELA_MAX=10
chat1 = ChatComMemoria()  # Usa 10 do .env

# Sobrescreve com parâmetro
chat2 = ChatComMemoria(tamanho_janela=5)  # Usa 5
```

### Escolhendo o Tamanho da Janela

```
Janela Pequena (2-4 pares):
+------------------+
| Contexto: Mínimo |
| Mensagens: 4-8   |
| Tokens: 100-300  |
| Custo: Muito baixo|
+------------------+
Uso: FAQ, respostas rápidas

Janela Média (6-8 pares):
+------------------+
| Contexto: Adequado|
| Mensagens: 12-16 |
| Tokens: 300-600  |
| Custo: Baixo     |
+------------------+
Uso: Conversas gerais (recomendado)

Janela Grande (10-16 pares):
+------------------+
| Contexto: Amplo  |
| Mensagens: 20-32 |
| Tokens: 600-1200 |
| Custo: Médio     |
+------------------+
Uso: Análises complexas, tutoriais
```

### Exemplo Prático

```python
from chat_openai_memoria import ChatComMemoria

# Configurar janela de 3 pares
chat = ChatComMemoria(tamanho_janela=3)

# Enviar 5 perguntas
perguntas = [
    "Qual é a capital da França?",
    "E da Alemanha?",
    "E da Itália?",
    "E da Espanha?",
    "E de Portugal?",
]

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n[Pergunta {i}] {pergunta}")
    chat.enviar_mensagem(pergunta)
    print(f"Mensagens no histórico: {len(chat.historico)}")

# Resultado:
# Pergunta 1: 2 mensagens (U1, A1)
# Pergunta 2: 4 mensagens (U1, A1, U2, A2)
# Pergunta 3: 6 mensagens (U1, A1, U2, A2, U3, A3)
# Pergunta 4: 6 mensagens (U2, A2, U3, A3, U4, A4) <- U1,A1 removidos
# Pergunta 5: 6 mensagens (U3, A3, U4, A4, U5, A5) <- U2,A2 removidos
```

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Custos previsíveis e estáveis | ❌ Perde contexto antigo |
| ✅ Completamente automático | ❌ Pode cortar no meio de análise |
| ✅ Escala bem para conversas longas | ❌ Configuração do tamanho é crítica |
| ✅ Fácil de configurar | ❌ Não diferencia contexto importante |

---

## Estratégia 3: Monitoramento de Tokens

### O que é?

**Monitorar ativamente** o número de tokens e **alertar** quando atingir níveis críticos. Os níveis são calculados automaticamente baseado no limite máximo configurado. Esta estratégia está **implementada nativamente** na classe `ChatComMemoria`.

### Diagrama de Níveis

```
Níveis Automáticos (baseado em LIMITE_MAXIMO):

🟢 Verde (0-33%):
+------------------+
| Uso normal       |
| Sem ação         |
+------------------+

🟡 Amarelo (33-66%):
+------------------+
| Atenção          |
| Começando alto   |
+------------------+

🟠 Laranja (66-99%):
+------------------+
| Alerta elevado   |
| Próximo do limite|
+------------------+

🔴 Vermelho (≥100%):
+------------------+
| CRÍTICO          |
| Ação recomendada |
+------------------+
```

### Configuração

**Opção 1: Via `.env` (Recomendado)**

```env
# No arquivo .env
LIMITE_MAXIMO=1000  # Os níveis serão calculados automaticamente:
                    # 🟢 0-333 tokens
                    # 🟡 333-666 tokens
                    # 🟠 666-999 tokens
                    # 🔴 ≥1000 tokens
```

**Opção 2: Via Construtor**

```python
from chat_openai_memoria import ChatComMemoria

# Limite de 500 tokens
chat = ChatComMemoria(limite_maximo=500)

# Níveis calculados automaticamente:
# 🟢 0-166 tokens (0-33%)
# 🟡 166-333 tokens (33-66%)
# 🟠 333-500 tokens (66-99%)
# 🔴 ≥500 tokens (≥100%)
```

### Como Funciona

Ao atingir cada nível, o sistema exibe alertas **automaticamente** após cada `enviar_mensagem()`:

```python
chat = ChatComMemoria(limite_maximo=300)

# Primeiras mensagens - nível verde
chat.enviar_mensagem("Pergunta curta")
# Saída: (nenhum alerta)

# Conversando mais - nível amarelo
chat.enviar_mensagem("Outra pergunta")
# Saída: ⚠️  🟡 AMARELO: 150 tokens (50.0% do limite)

# Mais mensagens - nível laranja
chat.enviar_mensagem("Mais uma pergunta longa...")
# Saída: ⚠️  🟠 LARANJA: 240 tokens (80.0% do limite)
#        ⚠️     Atenção: Aproximando do limite máximo

# Atingiu o limite - nível vermelho
chat.enviar_mensagem("Última pergunta bem longa...")
# Saída: ⚠️  🔴 CRÍTICO: 320 tokens (106.7% do limite)
#        ⚠️     Ação recomendada: Execute limpar_historico() ou ajuste JANELA_MAX no .env
```

### Ação no Nível Vermelho

Quando o limite é atingido, o sistema **recomenda** (mas não força) ações:

```
🔴 CRÍTICO: Você tem 3 opções:

1. Limpeza Manual:
   chat.limpar_historico()
   
2. Ajustar Sliding Window:
   # No .env
   JANELA_MAX=6  # Reduzir janela
   
3. Aumentar Limite:
   # No .env
   LIMITE_MAXIMO=1500  # Se apropriado
```

### Exemplo Prático

```python
from chat_openai_memoria import ChatComMemoria

# Limite baixo para demonstração
chat = ChatComMemoria(limite_maximo=300, modo_debug=False)

perguntas = [
    "Me explique o que é Python em poucas palavras.",
    "Quais são os principais tipos de dados em Python?",
    "Como funcionam as listas em Python?",
    "Explique o conceito de dicionários em Python.",
]

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n{'='*60}")
    print(f"PERGUNTA {i}")
    print('='*60)
    print(pergunta)
    chat.enviar_mensagem(pergunta)
    # Alertas aparecem automaticamente aqui
```

**Saída:**

```
============================================================
PERGUNTA 1
============================================================
Me explique o que é Python em poucas palavras.
Assistente: Python é uma linguagem...
(sem alerta - nível verde)

============================================================
PERGUNTA 2
============================================================
Quais são os principais tipos de dados em Python?
Assistente: Os principais tipos...

⚠️  🟡 AMARELO: 145 tokens (48.3% do limite)

============================================================
PERGUNTA 3
============================================================
Como funcionam as listas em Python?
Assistente: Listas são estruturas...

⚠️  🟠 LARANJA: 230 tokens (76.7% do limite)
⚠️     Atenção: Aproximando do limite máximo

============================================================
PERGUNTA 4
============================================================
Explique o conceito de dicionários em Python.
Assistente: Dicionários são...

⚠️  🔴 CRÍTICO: 315 tokens (105.0% do limite)
⚠️     Ação recomendada: Execute limpar_historico() ou ajuste JANELA_MAX no .env
```

### Valores Sugeridos

```
Conversas Curtas/Econômicas:
LIMITE_MAXIMO=500-800
Uso: FAQ, suporte rápido

Uso Geral (Recomendado):
LIMITE_MAXIMO=1000-1500
Uso: Conversas normais, tutoriais

Conversas Longas/Complexas:
LIMITE_MAXIMO=2000+
Uso: Análises profundas, sessões extensas
```

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Visibilidade clara de custos | ❌ Alertas podem interromper UX |
| ✅ Níveis calculados automaticamente | ❌ Não toma ação automática |
| ✅ Previne custos excessivos | ❌ Usuário deve decidir ação |
| ✅ Fácil de configurar | ❌ Requer configuração de limite |

---

## Sistema Completo (Recomendado)

### Combinando Sliding Window + Monitoramento

A **melhor prática** é usar ambas estratégias juntas para controle automático e visibilidade:

```python
from chat_openai_memoria import ChatComMemoria

# Sistema completo configurado
chat = ChatComMemoria(
    tamanho_janela=8,     # Mantém 8 pares (16 mensagens)
    limite_maximo=1000    # Alerta ao aproximar de 1000 tokens
)

# Benefícios:
# ✅ Sliding window mantém memória controlada automaticamente
# ✅ Monitoramento alerta sobre uso mesmo dentro da janela
# ✅ Custos previsíveis
# ✅ Contexto relevante sempre disponível
```

### Configuração via `.env` (Recomendado)

```env
# arquivo .env
OPENAI_API_KEY=sua-chave-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# Gerenciamento de memória
JANELA_MAX=8
LIMITE_MAXIMO=1000
```

```python
# Código Python
from chat_openai_memoria import ChatComMemoria

# Carrega tudo do .env automaticamente
chat = ChatComMemoria()

# Pronto para uso com gerenciamento completo!
```

### Como as Estratégias Trabalham Juntas

```
Fluxo de uma Mensagem:

1. Usuário envia mensagem
2. API processa e retorna resposta
3. Resposta adicionada ao histórico
4. 
   ↓
5. SLIDING WINDOW verifica:
   - Histórico > janela_max?
   - Se SIM: Remove mensagens antigas
   - Se NÃO: Mantém todas
   ↓
6. MONITORAMENTO verifica:
   - Calcula tokens atuais
   - Calcula percentual do limite
   - Exibe alerta apropriado (🟢🟡🟠🔴)
   ↓
7. Retorna resposta ao usuário
```

### Exemplo Prático Completo

```python
from chat_openai_memoria import ChatComMemoria

# Configuração otimizada para uso geral
chat = ChatComMemoria(
    tamanho_janela=6,
    limite_maximo=600
)

print("Sistema completo ativo:")
print(f"  • Janela: {chat.tamanho_janela} pares")
print(f"  • Limite: {chat.limite_maximo} tokens\n")

# Simula conversa longa
perguntas = [
    "O que é aprendizado de máquina?",
    "Quais são os tipos principais?",
    "Explique aprendizado supervisionado",
    "E o não supervisionado?",
    "O que é deep learning?",
    "Como funciona uma rede neural?",
    "Quais são as aplicações?",
    "Explique overfitting",
]

for i, pergunta in enumerate(perguntas, 1):
    print(f"\n{'='*60}")
    print(f"INTERAÇÃO {i}")
    print('='*60)
    print(f"Você: {pergunta}\n")
    
    resposta = chat.enviar_mensagem(pergunta)
    print(f"Assistente: {resposta[:100]}...\n")
    
    # Estatísticas
    print(f"📊 Status: {len(chat.historico)} mensagens, "
          f"{chat.contar_tokens_aproximado()} tokens")
```

**Comportamento Esperado:**

```
INTERAÇÃO 1:
Você: O que é aprendizado de máquina?
Assistente: Aprendizado de máquina é...
📊 Status: 2 mensagens, 85 tokens

INTERAÇÃO 4:
Você: E o não supervisionado?
Assistente: Aprendizado não supervisionado...
📊 Status: 8 mensagens, 340 tokens

INTERAÇÃO 7:
Você: Quais são as aplicações?
Assistente: As aplicações incluem...
📊 Status: 12 mensagens, 510 tokens

⚠️  🟠 LARANJA: 510 tokens (85.0% do limite)
⚠️     Atenção: Aproximando do limite máximo
```

### Cenários de Uso Recomendados

| Cenário | Janela | Limite | Justificativa |
|---------|--------|--------|---------------|
| **Chatbot FAQ** | 3-4 | 400-600 | Perguntas independentes, contexto mínimo |
| **Tutor Interativo** | 6-8 | 800-1200 | Equilíbrio contexto/custo |
| **Análise de Código** | 8-12 | 1500-2000 | Contexto amplo necessário |
| **Suporte Técnico** | 5-7 | 1000-1500 | Sessões médias variáveis |

### Ajuste Fino

Se os alertas estão aparecendo muito:

```env
# Opção 1: Reduzir janela (menos contexto, menos tokens)
JANELA_MAX=5

# Opção 2: Aumentar limite (mais tolerância)
LIMITE_MAXIMO=1500

# Opção 3: Ambos (balance customizado)
JANELA_MAX=7
LIMITE_MAXIMO=1200
```

---

## Modo Debug

### O que é?

Modo que gera **logs detalhados** de cada interação em arquivos timestampados na pasta `logs/`. Essencial para desenvolvimento, auditoria e aprendizado.

### Ativando

**Opção 1: Via `.env`**

```env
MODO_DEBUG=true
```

**Opção 2: Via Construtor**

```python
chat = ChatComMemoria(modo_debug=True)
```

### O que é Registrado

Cada arquivo de log (`logs/chat_debug_YYYYMMDD_HHMMSS.log`) contém:

```
╔════════════════════════════════════════════════════════════════════╗
║                        CHAT DEBUG LOG                              ║
║                   Chat OpenAI com Memória                          ║
╚════════════════════════════════════════════════════════════════════╝

Sessão iniciada em: 17/12/2025 14:30:45
══════════════════════════════════════════════════════════════════

CONFIGURAÇÕES DA SESSÃO:
  • Modelo: gpt-4o-mini
  • Temperature: 0.7
  • Max Tokens: 1000
  • System Prompt: Você é um assistente útil e amigável.
  • Sliding Window: 8 pares de mensagens
  • Monitoramento: 1000 tokens (máximo)
    - 🟢 Verde: 0-333 tokens (0-33%)
    - 🟡 Amarelo: 333-666 tokens (33-66%)
    - 🟠 Laranja: 666-1000 tokens (66-99%)
    - 🔴 Vermelho: ≥1000 tokens (≥100% - CRÍTICO)

══════════════════════════════════════════════════════════════════

╔════════════════════════════════════════════════════════════════════╗
║  INTERAÇÃO #1                                                      ║
║  17/12/2025 14:31:02                                               ║
╚════════════════════════════════════════════════════════════════════╝

──────────────────────────────────────────────────────────────────
[MENSAGEM DO USUÁRIO]
──────────────────────────────────────────────────────────────────
O que é Python?

──────────────────────────────────────────────────────────────────
[SYSTEM PROMPT]
──────────────────────────────────────────────────────────────────
Você é um assistente útil e amigável.

──────────────────────────────────────────────────────────────────
[PARÂMETROS DO MODELO]
──────────────────────────────────────────────────────────────────
  Modelo: gpt-4o-mini
  Temperature: 0.7
  Max Tokens: 1000

──────────────────────────────────────────────────────────────────
[HISTÓRICO (antes da nova mensagem)]
──────────────────────────────────────────────────────────────────
  Total de mensagens: 0
  Tokens aproximados: 0

──────────────────────────────────────────────────────────────────
[RESPOSTA DO ASSISTENTE]
──────────────────────────────────────────────────────────────────
Python é uma linguagem de programação de alto nível...

──────────────────────────────────────────────────────────────────
[STATUS DE MEMÓRIA]
──────────────────────────────────────────────────────────────────
  Total de mensagens: 2
  Tokens aproximados: 65
  Janela máxima: 16 mensagens (8 pares)
  Limite máximo: 1000 tokens
  Uso atual: 6.5% 🟢

══════════════════════════════════════════════════════════════════
```

### Quando o Sliding Window Atua

```
──────────────────────────────────────────────────────────────────
[AÇÕES EXECUTADAS]
──────────────────────────────────────────────────────────────────
  ⚠️  Sliding window aplicado: mantendo 8 pares de mensagens
```

### Quando Atinge Nível de Alerta

```
──────────────────────────────────────────────────────────────────
[AÇÕES EXECUTADAS]
──────────────────────────────────────────────────────────────────
  ⚠️  🟠 LARANJA: 720 tokens (72.0% do limite)
  ⚠️     Atenção: Aproximando do limite máximo
```

### Limpeza de Histórico Registrada

```
══════════════════════════════════════════════════════════════════
[LIMPEZA DE HISTÓRICO]
══════════════════════════════════════════════════════════════════
Removidas 12 mensagens do histórico
Timestamp: 17/12/2025 14:35:22
══════════════════════════════════════════════════════════════════
```

### Exemplo de Uso

```python
from chat_openai_memoria import ChatComMemoria

# Ativar debug
chat = ChatComMemoria(
    tamanho_janela=4,
    limite_maximo=400,
    modo_debug=True
)

print(f"Log sendo gravado em: {chat.arquivo_log}\n")

# Conversar normalmente
chat.enviar_mensagem("Explique Python")
chat.enviar_mensagem("E suas vantagens?")
chat.limpar_historico()
chat.enviar_mensagem("Agora explique JavaScript")

# Ao final, verificar o arquivo de log
print(f"\n✅ Sessão finalizada!")
print(f"📄 Log completo salvo em: {chat.arquivo_log}")
```

### Análise dos Logs

Os logs são úteis para:

```
✅ Debugging:
   - Identificar por que o modelo respondeu de certa forma
   - Ver exatamente qual contexto foi enviado
   - Rastrear quando sliding window atuou

✅ Auditoria:
   - Registro completo de conversas
   - Timestamps precisos
   - Parâmetros utilizados

✅ Otimização:
   - Analisar crescimento de tokens
   - Identificar quando alertas aparecem
   - Ajustar janela e limites

✅ Aprendizado:
   - Entender como memória funciona
   - Ver impacto de diferentes configurações
   - Estudar padrões de uso
```

### Desempenho

- **Overhead:** Mínimo (~5-10ms por interação)
- **Tamanho:** ~2-5KB por interação registrada
- **Arquivo:** Novo arquivo por sessão (não acumula)

### Desativando

```python
# Opção 1: Não configurar
chat = ChatComMemoria()  # Debug desativado por padrão

# Opção 2: Explicitamente desativar
chat = ChatComMemoria(modo_debug=False)

# Opção 3: No .env
MODO_DEBUG=false
```

---

## Comparação de Estratégias

### Tabela Resumida

| Estratégia | Automação | Economia | Complexidade | Perda de Contexto |
|------------|-----------|----------|--------------|-------------------|
| **Limpeza Manual** | ❌ Nenhuma | ⭐⭐⭐ Alta | ⭐ Baixa | ⚠️ Total (quando limpa) |
| **Sliding Window** | ✅ Total | ⭐⭐⭐ Alta | ⭐ Baixa | ⚠️ Gradual |
| **Monitoramento** | ⚠️ Alertas | ⭐ Baixa | ⭐ Baixa | ⚠️ Nenhuma (só alerta) |
| **Sistema Completo** | ✅ Total | ⭐⭐⭐ Alta | ⭐⭐ Média | ⚠️ Gradual + Visibilidade |

### Quando Usar Cada Uma

```
Limpeza Manual:
+------------------+
| Cenário:         |
| - Múltiplos      |
|   clientes       |
| - Mudança total  |
|   de assunto     |
+------------------+

Sliding Window:
+------------------+
| Cenário:         |
| - Conversas      |
|   longas         |
| - FAQ contínuo   |
| - Tutoriais      |
+------------------+

Monitoramento:
+------------------+
| Cenário:         |
| - Visibilidade   |
|   de custos      |
| - Alertas para   |
|   usuário        |
+------------------+

Sistema Completo (RECOMENDADO):
+------------------+
| Cenário:         |
| - Uso geral      |
| - Produção       |
| - Controle total |
+------------------+
```

---

## Ferramentas de Diagnóstico

### Comando `/debug`

Exibe status detalhado da memória no chat interativo:

```bash
Você: /debug

╔════════════════════════════════════════════════════════════════════╗
║                      DEBUG DE MEMÓRIA                              ║
╚════════════════════════════════════════════════════════════════════╝

📊 Status Geral:
   • Total de mensagens: 12
   • Pares (user+assistant): 6
   • Tokens aproximados: 480

🪟 Sliding Window:
   • Limite: 8 pares (16 mensagens)
   • Uso atual: 6 pares (12 mensagens)
   • Percentual: 75.0%

📈 Monitoramento:
   • Limite máximo: 1000 tokens
   • Uso atual: 480 tokens (48.0%)
   • Nível: 🟡
   • Progresso: [████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░]

🐛 Modo Debug: Ativo
   • Arquivo de log: logs/chat_debug_20251217_143045.log
   • Interações registradas: 6

══════════════════════════════════════════════════════════════════
```

### Comando `/grafico`

Mostra evolução visual dos tokens:

```bash
Você: /grafico

╔════════════════════════════════════════════════════════════════════╗
║                      GRÁFICO DE TOKENS                             ║
╚════════════════════════════════════════════════════════════════════╝

Evolução de tokens ao longo de 12 mensagens

Max: 480 tokens
 480 |█████████████
     |█████████████
     |█████████████
     |████████████
     |███████████
     |██████████
     |█████████
 240 |████████
     |███████
     |██████
     |█████
     |████
     |███
     |██
   0 |█
     └─────────────
      Mensagens: 1            12

🟡 Uso máximo: 480/1000 tokens (48.0%)

══════════════════════════════════════════════════════════════════
```

### Método `debug_memoria()`

Uso programático:

```python
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria(tamanho_janela=6, limite_maximo=800)

# Conversar
chat.enviar_mensagem("Primeira pergunta")
chat.enviar_mensagem("Segunda pergunta")

# Verificar status
chat.debug_memoria()

# Mais conversa
chat.enviar_mensagem("Terceira pergunta")

# Verificar novamente
chat.debug_memoria()
```

### Método `grafico_tokens()`

Gera gráfico ASCII:

```python
chat = ChatComMemoria(tamanho_janela=8, limite_maximo=1000)

# Simular conversa
for i in range(15):
    chat.enviar_mensagem(f"Pergunta número {i+1}")

# Mostrar evolução
chat.grafico_tokens()
```

---

## Resumo das Melhores Práticas

### ✅ Faça

1. **Use o sistema completo** - Combine sliding window + monitoramento
2. **Configure via `.env`** - Facilita ajustes sem mudar código
3. **Monitore tokens** - Use `/debug` ou `debug_memoria()` periodicamente
4. **Ajuste conforme necessário** - Cada caso de uso é diferente
5. **Use modo debug** - Durante desenvolvimento e troubleshooting
6. **Documente escolhas** - Explique por que escolheu valores específicos

### ❌ Não Faça

1. **Não ignore alertas** - Custos podem crescer inesperadamente
2. **Não use janela muito pequena** - Perde contexto útil
3. **Não desabilite tudo** - Sem gerenciamento, custos explodem
4. **Não use valores fixos** - Adapte ao caso de uso
5. **Não esqueça de testar** - Valide configurações com dados reais

### Configuração Inicial Recomendada

```env
# .env - Configuração segura para começar
OPENAI_API_KEY=sua-chave-aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000

# Gerenciamento de memória (valores conservadores)
JANELA_MAX=6
LIMITE_MAXIMO=800
MODO_DEBUG=false  # true durante desenvolvimento
```

---

## Próximos Passos

- 💡 Veja aplicações práticas em [CASOS_DE_USO.md](CASOS_DE_USO.md)
- 🔧 Resolva problemas em [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📚 Revise conceitos em [CONCEITOS.md](CONCEITOS.md)
- 🎓 Experimente os exemplos: `python exemplos_avancados.py`
