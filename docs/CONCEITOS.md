# 📚 Conceitos Fundamentais

Entenda como funciona a memória conversacional e os parâmetros que controlam o comportamento do chat.

## Índice

- [Memória Conversacional](#memória-conversacional)
- [Temperature (Temperatura)](#temperature-temperatura)
- [Max Tokens](#max-tokens)
- [Fluxo de uma Conversa](#fluxo-de-uma-conversa)
- [Impacto em Custos](#impacto-em-custos)

---

## Memória Conversacional

### O que é?

Memória conversacional é a capacidade do assistente de **lembrar** o que foi dito anteriormente na conversa. Isso permite:

- Referências a mensagens anteriores
- Continuidade de contexto
- Respostas mais relevantes e personalizadas

### Como funciona?

O chat mantém uma **lista de mensagens** que cresce a cada interação:

```
+------------------+
|  Histórico       |
|  (lista vazia)   |
+------------------+
```

Após a primeira interação:

```
+------------------+
|  Histórico       |
|------------------|
| User: "Olá"      |
| Asst: "Oi!"      |
+------------------+
```

Após a segunda interação:

```
+------------------+
|  Histórico       |
|------------------|
| User: "Olá"      |
| Asst: "Oi!"      |
| User: "Python?"  |
| Asst: "Sim..."   |
+------------------+
```

### Estrutura Técnica

Cada mensagem é armazenada como um dicionário:

```python
{
    "role": "user",        # ou "assistant"
    "content": "mensagem"  # texto da mensagem
}
```

### Contexto Completo na API

**Importante:** A cada requisição, o histórico COMPLETO é enviado para a API:

```
Requisição 1:
  Sistema: "Você é um assistente útil"
  User: "Olá"
  --> API processa e responde

Requisição 2:
  Sistema: "Você é um assistente útil"
  User: "Olá"              <- Enviado novamente
  Asst: "Oi!"              <- Enviado novamente
  User: "Como vai?"        <- Nova mensagem
  --> API processa TUDO e responde
```

### Diagrama do Crescimento da Memória

```
Interação 1          Interação 2          Interação 3
+-----------+        +-----------+        +-----------+
| Msg 1     |        | Msg 1     |        | Msg 1     |
| Msg 2     |        | Msg 2     |        | Msg 2     |
+-----------+        | Msg 3     |        | Msg 3     |
 2 mensagens         | Msg 4     |        | Msg 4     |
                     +-----------+        | Msg 5     |
                      4 mensagens         | Msg 6     |
                                          +-----------+
                                           6 mensagens
                                          
Tokens: ~50          Tokens: ~100         Tokens: ~150
Custo: $ baixo       Custo: $ médio       Custo: $ alto
```

### Vantagens da Memória

✅ Conversas naturais e coerentes  
✅ Não precisa repetir informações  
✅ Assistente entende referências ("isso", "aquele código", "a função anterior")  
✅ Contexto acumulado melhora respostas  

### Desvantagens da Memória

❌ Custos aumentam com histórico longo  
❌ Processamento fica mais lento  
❌ Limite de tokens pode ser atingido  
❌ Memória perdida ao encerrar o programa  

---

## Temperature (Temperatura)

### O que é?

Temperature controla o grau de **aleatoriedade** e **criatividade** nas respostas do modelo.

### Escala de Valores

```
0.0                    1.0                    2.0
|----------------------|----------------------|
Determinístico      Balanceado          Criativo
Preciso             Versátil            Imprevisível
Repetitivo          Variado             Aleatório
```

### Comportamento por Faixa

#### Temperature = 0.0

**Características:**
- Sempre escolhe a palavra mais provável
- Respostas idênticas para mesma pergunta
- Máxima precisão e consistência

**Quando usar:**
- Análise de código
- Respostas técnicas exatas
- Tarefas que exigem determinismo

**Exemplo:**

```
Pergunta: "Quanto é 2 + 2?"

Resposta (sempre): "2 + 2 é igual a 4."
```

#### Temperature = 0.7 (Recomendado)

**Características:**
- Equilíbrio entre precisão e variedade
- Respostas naturais e ligeiramente diferentes
- Bom para uso geral

**Quando usar:**
- Conversas normais
- Explicações didáticas
- Assistente geral

**Exemplo:**

```
Pergunta: "Explique Python"

Resposta 1: "Python é uma linguagem de programação..."
Resposta 2: "Python é uma linguagem versátil e fácil..."
Resposta 3: "Python destaca-se por sua sintaxe clara..."
```

#### Temperature = 1.5 - 2.0

**Características:**
- Alta criatividade e variação
- Respostas imprevisíveis
- Pode gerar informações incorretas

**Quando usar:**
- Brainstorming criativo
- Geração de ideias
- Escrita criativa

**Exemplo:**

```
Pergunta: "Crie um nome para app"

Resposta 1: "CodeWhisperer"
Resposta 2: "Synthronix"
Resposta 3: "NeuralBloom"
```

### Diagrama Visual do Impacto

```
Temperature: 0.0          Temperature: 0.7          Temperature: 2.0

     [A]                       [A]                       [A]
      |                      /  |  \                   / | | \ \
      v                     v   v   v                v  v v  v  v
    Sempre A            A, B ou C            A, B, C, D, E, ...
    (100%)              (variado)            (altamente variado)
```

### Configuração no Projeto

No arquivo `.env`:

```env
OPENAI_TEMPERATURE=0.7  # Valor entre 0.0 e 2.0
```

---

## Max Tokens

### O que é?

Max tokens define o **tamanho máximo da resposta** que o modelo pode gerar.

### Entendendo Tokens

- 1 token ≈ 4 caracteres (aproximação)
- 1 token ≈ 0.75 palavras
- Exemplos:
  - "Olá" = 1 token
  - "Python é legal" = 3 tokens
  - "inteligência" = 3-4 tokens

### Valores Comuns

| Max Tokens | Tamanho da Resposta | Uso Recomendado |
|------------|---------------------|-----------------|
| 100-300    | Respostas curtas    | Perguntas simples, chatbots rápidos |
| 500-1000   | Respostas médias    | Uso geral (recomendado) |
| 1500-2000  | Respostas longas    | Explicações detalhadas, tutoriais |
| 3000+      | Respostas muito longas | Análises extensas, geração de código |

### Comportamento do Limite

Quando o limite é atingido, a resposta é **cortada abruptamente**:

```
Max Tokens = 50

Pergunta: "Explique Python em detalhes"

Resposta:
"Python é uma linguagem de programação de alto nível,
conhecida por sua sintaxe clara e legível. É amplamente
usada em ciência de dados, desenvolvimento web e..."
[CORTADO - limite atingido]
```

### Impacto em Custos

**Importante:** Você paga por tokens **enviados + recebidos**:

```
Custo Total = (Tokens de Entrada + Tokens de Saída) × Preço por Token

Exemplo:
  Histórico: 500 tokens
  Pergunta: 20 tokens
  Resposta: 150 tokens
  -------------------------
  Total: 670 tokens cobrados
```

### Diagrama de Uso de Tokens

```
Requisição para API
+----------------------------------------+
|  System Prompt:  50 tokens             |
|  Histórico:      500 tokens            |
|  Nova Pergunta:  20 tokens             |
|  --------------------------------      |
|  Total Entrada:  570 tokens  (pago)    |
+----------------------------------------+
                  |
                  v
            API Processa
                  |
                  v
+----------------------------------------+
|  Resposta:  150 tokens (pago)          |
|  [limitado por MAX_TOKENS=1000]        |
+----------------------------------------+

Custo = 570 (entrada) + 150 (saída) = 720 tokens
```

### Configuração no Projeto

No arquivo `.env`:

```env
OPENAI_MAX_TOKENS=1000  # Número inteiro positivo
```

---

## Fluxo de uma Conversa

### Diagrama Completo

```
+----------------+
|  Usuário       |
|  "Olá!"        |
+-------+--------+
        |
        v
+-------+------------------+
|  Chat adiciona à memória |
|  [user: "Olá!"]          |
+-------+------------------+
        |
        v
+-------+--------------------+
|  Monta requisição:         |
|  - System prompt           |
|  - Todo histórico          |
|  - Nova mensagem           |
+-------+--------------------+
        |
        v
+-------+------------+
|  Envia para API    |
|  OpenAI            |
+-------+------------+
        |
        v
+-------+-------------------+
|  API processa com:        |
|  - Model: gpt-4o-mini     |
|  - Temperature: 0.7       |
|  - Max tokens: 1000       |
+-------+-------------------+
        |
        v
+-------+--------------------+
|  Resposta recebida         |
|  "Olá! Como posso ajudar?" |
+-------+--------------------+
        |
        v
+-------+------------------+
|  Adiciona à memória      |
|  [assistant: "Olá!..."]  |
+-------+------------------+
        |
        v
+-------+--------+
|  Exibe para    |
|  usuário       |
+----------------+
```

### Ciclo de Vida da Memória

```
Início do Chat
     |
     v
[Memória Vazia]
     |
     +---> Usuário pergunta
     |        |
     |        v
     |    [Adiciona user]
     |        |
     |        v
     |    Chama API
     |        |
     |        v
     |    [Adiciona assistant]
     |        |
     +--------+
     |
     v
Comando /limpar
     |
     v
[Memória Vazia]
     |
     v
   Reinicia
```

---

## Impacto em Custos

### Fatores que Afetam o Custo

1. **Tamanho do Histórico** (principal fator)
2. **Frequência de mensagens**
3. **Modelo escolhido** (gpt-4o vs gpt-4o-mini)
4. **Max tokens configurado**

### Comparação de Cenários

```
Cenário 1: Conversa Curta (5 interações)
+----------------------------------+
| Histórico: 200 tokens            |
| Pergunta: 30 tokens              |
| Resposta: 100 tokens             |
| Total por requisição: ~330 tokens|
+----------------------------------+
Custo: $ baixo

Cenário 2: Conversa Longa (50 interações)
+----------------------------------+
| Histórico: 3000 tokens           |
| Pergunta: 30 tokens              |
| Resposta: 100 tokens             |
| Total por requisição: ~3130 tokens|
+----------------------------------+
Custo: $ alto (9x mais caro que Cenário 1)
```

### Estratégias de Redução de Custos

1. **Limpar memória periodicamente** (`/limpar`)
2. **Usar sliding window** (manter apenas N mensagens recentes)
3. **Monitorar tokens** (`/tokens`)
4. **Escolher modelo adequado** (gpt-4o-mini é mais barato)
5. **Ajustar max_tokens** (não usar valores excessivos)

Ver [GERENCIAMENTO_MEMORIA.md](GERENCIAMENTO_MEMORIA.md) para técnicas detalhadas.

---

## Resumo dos Conceitos

| Conceito | O que controla | Impacto em Custos |
|----------|----------------|-------------------|
| **Memória** | Contexto e continuidade | ⬆️ Alto (cresce com conversa) |
| **Temperature** | Criatividade das respostas | ➡️ Nenhum |
| **Max Tokens** | Tamanho máximo da resposta | ⬆️ Médio (limita saída) |

**Próximo passo:** Aprenda a usar o chat na prática em [USO_BASICO.md](USO_BASICO.md)
