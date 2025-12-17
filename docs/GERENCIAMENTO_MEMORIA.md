# 🧠 Gerenciamento de Memória

Estratégias para controlar custos e otimizar o uso de memória conversacional.

## Índice

- [Por que Gerenciar Memória?](#por-que-gerenciar-memória)
- [Estratégia 1: Limpeza Manual](#estratégia-1-limpeza-manual)
- [Estratégia 2: Sliding Window](#estratégia-2-sliding-window)
- [Estratégia 3: Monitoramento de Tokens](#estratégia-3-monitoramento-de-tokens)
- [Estratégia 4: Clearing Estratégico](#estratégia-4-clearing-estratégico)
- [Comparação de Estratégias](#comparação-de-estratégias)
- [Implementação Prática](#implementação-prática)

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

**Com gerenciamento (sliding window de 8 mensagens):**

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

print(f"Tokens sessão 1: {chat.contar_tokens()}")

# Finalizar sessão 1, começar sessão 2
chat.limpar_historico()

# Sessão 2 (independente)
chat.enviar_mensagem("Explique JavaScript closures")
print(f"Tokens sessão 2: {chat.contar_tokens()}")
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

Manter apenas as **N mensagens mais recentes**, descartando automaticamente as antigas.

### Diagrama Detalhado

```
Janela de 6 mensagens (3 interações):

Passo 1: Conversa normal (dentro da janela)
+-----+-----+-----+-----+-----+-----+
| M1  | M2  | M3  | M4  | M5  | M6  |
+-----+-----+-----+-----+-----+-----+
[          Janela Atual          ]
Tokens: 500

Passo 2: Adiciona M7 e M8 (excede janela)
+-----+-----+-----+-----+-----+-----+-----+-----+
| M1  | M2  | M3  | M4  | M5  | M6  | M7  | M8  |
+-----+-----+-----+-----+-----+-----+-----+-----+
 [XX]  [XX]        [    Janela Atual     ]
Remove M1 e M2
Tokens: 500 (estável)

Passo 3: Adiciona M9 e M10
+-----+-----+-----+-----+-----+-----+-----+-----+
| M3  | M4  | M5  | M6  | M7  | M8  | M9  | M10 |
+-----+-----+-----+-----+-----+-----+-----+-----+
 [XX]  [XX]        [    Janela Atual       ]
Remove M3 e M4
Tokens: 500 (estável)
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria

class ChatComJanela(ChatComMemoria):
    def __init__(self, tamanho_janela=8):
        super().__init__()
        self.tamanho_janela = tamanho_janela
    
    def enviar_mensagem(self, mensagem):
        # Enviar normalmente
        resposta = super().enviar_mensagem(mensagem)
        
        # Aplicar janela se exceder
        if len(self.historico) > self.tamanho_janela:
            # Manter apenas as últimas N mensagens
            self.historico = self.historico[-self.tamanho_janela:]
            print(f"[Janela aplicada: {len(self.historico)} mensagens mantidas]")
        
        return resposta

# Uso
chat = ChatComJanela(tamanho_janela=6)

for i in range(10):
    resp = chat.enviar_mensagem(f"Pergunta {i+1}")
    print(f"Mensagens: {len(chat.historico)} | Tokens: {chat.contar_tokens()}")
```

### Escolhendo o Tamanho da Janela

```
Janela Pequena (2-4 mensagens):
+------------------+
| Contexto: Mínimo |
| Tokens: 100-300  |
| Custo: Muito baixo|
+------------------+
Uso: FAQ, respostas rápidas

Janela Média (6-8 mensagens):
+------------------+
| Contexto: Adequado|
| Tokens: 300-600  |
| Custo: Baixo     |
+------------------+
Uso: Conversas gerais (recomendado)

Janela Grande (10-16 mensagens):
+------------------+
| Contexto: Amplo  |
| Tokens: 600-1200 |
| Custo: Médio     |
+------------------+
Uso: Análises complexas, tutoriais
```

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Custos previsíveis | ❌ Perde contexto antigo |
| ✅ Automático | ❌ Pode cortar no meio de análise |
| ✅ Escala bem | ❌ Configuração do tamanho é crítica |

---

## Estratégia 3: Monitoramento de Tokens

### O que é?

**Monitorar ativamente** o número de tokens e alertar/agir quando atingir limites.

### Diagrama de Monitoramento

```
Fluxo com Monitoramento:

Enviar Mensagem
      |
      v
+------------------+
| Processa resposta|
+------------------+
      |
      v
+------------------+
| Conta tokens     |
+------------------+
      |
      v
  Tokens < 500?
   /         \
  Sim        Não
   |          |
   v          v
Continua   +------------------+
           | Alerta: Tokens   |
           | alto! Considere  |
           | limpar histórico |
           +------------------+
                  |
                  v
          Tokens > 1000?
           /         \
          Sim        Não
           |          |
           v          v
      +----------+  Continua
      | FORÇA    |
      | limpeza  |
      | automática|
      +----------+
```

### Implementação com Alertas

```python
from chat_openai_memoria import ChatComMemoria

class ChatComMonitoramento(ChatComMemoria):
    def __init__(self, limite_alerta=500, limite_maximo=1000):
        super().__init__()
        self.limite_alerta = limite_alerta
        self.limite_maximo = limite_maximo
    
    def enviar_mensagem(self, mensagem):
        resposta = super().enviar_mensagem(mensagem)
        tokens = self.contar_tokens()
        
        # Alertas
        if tokens > self.limite_maximo:
            print(f"⚠️  CRÍTICO: {tokens} tokens! Limpando automaticamente...")
            self.limpar_historico()
        elif tokens > self.limite_alerta:
            print(f"⚠️  Aviso: {tokens} tokens. Considere limpar histórico.")
        else:
            print(f"✅ Tokens OK: {tokens}")
        
        return resposta

# Uso
chat = ChatComMonitoramento(limite_alerta=300, limite_maximo=500)

perguntas = [
    "Explique Python",
    "E listas?",
    "E dicionários?",
    "E funções?",
    "E classes?"
]

for p in perguntas:
    chat.enviar_mensagem(p)
```

### Níveis de Monitoramento

```
+----------------------+
| Verde: 0-300 tokens  |
| ✅ Sem ação          |
+----------------------+
         |
+----------------------+
| Amarelo: 300-600     |
| ⚠️  Alerta visual    |
+----------------------+
         |
+----------------------+
| Laranja: 600-1000    |
| ⚠️  Sugestão limpar  |
+----------------------+
         |
+----------------------+
| Vermelho: 1000+      |
| 🛑 Limpeza forçada   |
+----------------------+
```

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Visibilidade de custos | ❌ Requer configuração de limites |
| ✅ Previne custos excessivos | ❌ Alertas podem interromper UX |
| ✅ Flexível (alerta ou ação) | ❌ Limpeza forçada pode ser abrupta |

---

## Estratégia 4: Clearing Estratégico

### O que é?

Limpar memória em **pontos estratégicos** da conversa baseado em lógica de negócio.

### Momentos Estratégicos

```
1. Mudança de Sessão:
   Cliente A  -->  /limpar  -->  Cliente B

2. Mudança de Tópico:
   Python  -->  /limpar  -->  JavaScript

3. Finalização de Tarefa:
   Análise completa  -->  /limpar  -->  Nova análise

4. Comando Explícito:
   Usuário digita: "mude de assunto"  -->  /limpar

5. Tempo Limite:
   5 minutos inativo  -->  /limpar  -->  Nova sessão
```

### Diagrama de Transições

```
+------------------+
|   Sessão A       |
|   (Cliente 1)    |
+--------+---------+
         |
         | Detecta fim da sessão
         v
+------------------+
|   /limpar        |
+--------+---------+
         |
         v
+------------------+
|   Sessão B       |
|   (Cliente 2)    |
+------------------+
```

### Implementação com Detecção de Contexto

```python
from chat_openai_memoria import ChatComMemoria
import time

class ChatInteligente(ChatComMemoria):
    def __init__(self):
        super().__init__()
        self.topico_atual = None
        self.ultima_interacao = time.time()
    
    def enviar_mensagem(self, mensagem):
        # Detectar timeout (5 minutos)
        if time.time() - self.ultima_interacao > 300:
            print("🕐 Timeout detectado. Limpando sessão antiga...")
            self.limpar_historico()
            self.topico_atual = None
        
        # Detectar mudança de tópico explícita
        palavras_mudanca = ["novo assunto", "mude de tema", "outra coisa"]
        if any(palavra in mensagem.lower() for palavra in palavras_mudanca):
            print("🔄 Mudança de tópico detectada. Limpando contexto...")
            self.limpar_historico()
            self.topico_atual = None
        
        # Processar mensagem
        resposta = super().enviar_mensagem(mensagem)
        self.ultima_interacao = time.time()
        
        return resposta

# Uso
chat = ChatInteligente()

chat.enviar_mensagem("Explique Python")
chat.enviar_mensagem("Dê exemplos")

# Usuário solicita mudança
chat.enviar_mensagem("Novo assunto: explique JavaScript")
# -> Limpa automaticamente antes de processar
```

### Regras de Negócio Comuns

| Cenário | Regra de Clearing |
|---------|-------------------|
| **Chatbot de Suporte** | Limpar ao fechar ticket |
| **Assistente de Código** | Limpar ao mudar de arquivo |
| **Tutor Educacional** | Limpar ao mudar de matéria |
| **Consultor Virtual** | Limpar ao finalizar consulta |

### Vantagens e Desvantagens

| Vantagens | Desvantagens |
|-----------|--------------|
| ✅ Contextualmente relevante | ❌ Complexo de implementar |
| ✅ UX natural | ❌ Requer lógica de detecção |
| ✅ Equilibra contexto e custo | ❌ Pode errar detecção |

---

## Comparação de Estratégias

### Tabela Resumida

| Estratégia | Automação | Economia | Complexidade | Perda de Contexto |
|------------|-----------|----------|--------------|-------------------|
| **Limpeza Manual** | ❌ Nenhuma | ⭐⭐⭐ Alta | ⭐ Baixa | ⚠️ Total (quando limpa) |
| **Sliding Window** | ✅ Total | ⭐⭐⭐ Alta | ⭐⭐ Média | ⚠️ Gradual |
| **Monitoramento** | ⚠️ Parcial | ⭐⭐ Média | ⭐⭐ Média | ⚠️ Total (quando força) |
| **Clearing Estratégico** | ✅ Contextual | ⭐⭐ Média | ⭐⭐⭐ Alta | ⚠️ Mínima |

### Cenários Recomendados

```
Chatbot FAQ:
+------------------+
| Sliding Window   |
| (janela: 4)      |
+------------------+
Motivo: Perguntas independentes

Análise de Código:
+------------------+
| Clearing         |
| Estratégico      |
+------------------+
Motivo: Limpar ao mudar arquivo

Tutor Interativo:
+------------------+
| Monitoramento +  |
| Sliding Window   |
+------------------+
Motivo: Equilíbrio contexto/custo

Suporte Técnico:
+------------------+
| Monitoramento +  |
| Limpeza Manual   |
+------------------+
Motivo: Sessões variáveis
```

---

## Implementação Prática

### Sistema Híbrido (Recomendado)

Combinar múltiplas estratégias para melhor resultado:

```python
from chat_openai_memoria import ChatComMemoria
import time

class ChatOtimizado(ChatComMemoria):
    def __init__(
        self,
        janela_max=10,
        limite_tokens=800,
        timeout_segundos=300
    ):
        super().__init__()
        self.janela_max = janela_max
        self.limite_tokens = limite_tokens
        self.timeout_segundos = timeout_segundos
        self.ultima_interacao = time.time()
    
    def enviar_mensagem(self, mensagem):
        # Estratégia 1: Timeout (Clearing Estratégico)
        if time.time() - self.ultima_interacao > self.timeout_segundos:
            print("⏰ Sessão expirada. Nova sessão iniciada.")
            self.limpar_historico()
        
        # Processar mensagem
        resposta = super().enviar_mensagem(mensagem)
        tokens = self.contar_tokens()
        
        # Estratégia 2: Monitoramento
        if tokens > self.limite_tokens:
            print(f"⚠️  {tokens} tokens excede limite ({self.limite_tokens})")
            
            # Estratégia 3: Sliding Window
            if len(self.historico) > self.janela_max:
                print(f"   Aplicando janela de {self.janela_max} mensagens...")
                self.historico = self.historico[-self.janela_max:]
                print(f"   ✅ Tokens após janela: {self.contar_tokens()}")
            else:
                print("   ⚠️  Considere limpar histórico manualmente")
        else:
            print(f"✅ Tokens: {tokens}")
        
        self.ultima_interacao = time.time()
        return resposta

# Uso
chat = ChatOtimizado(
    janela_max=8,          # Máximo 8 mensagens
    limite_tokens=600,     # Alerta em 600 tokens
    timeout_segundos=300   # 5 minutos de inatividade
)

# Conversa longa
for i in range(15):
    resposta = chat.enviar_mensagem(f"Pergunta número {i+1} sobre Python")
    print(f"Resposta: {resposta[:50]}...\n")
```

### Resultado do Sistema Híbrido

```
Pergunta 1:
✅ Tokens: 45

Pergunta 5:
✅ Tokens: 320

Pergunta 8:
✅ Tokens: 580

Pergunta 9:
⚠️  620 tokens excede limite (600)
   Aplicando janela de 8 mensagens...
   ✅ Tokens após janela: 480

Pergunta 12:
✅ Tokens: 550

[5 minutos de inatividade]

Pergunta 13:
⏰ Sessão expirada. Nova sessão iniciada.
✅ Tokens: 40
```

---

## Resumo das Melhores Práticas

### ✅ Faça

1. **Monitore tokens regularmente** - Use `contar_tokens()` após cada interação
2. **Escolha estratégia adequada** - Baseado no caso de uso
3. **Combine estratégias** - Híbridos funcionam melhor
4. **Teste limites** - Encontre o balanço ideal contexto/custo
5. **Documente decisões** - Explique por que escolheu X tokens ou Y janela

### ❌ Não Faça

1. **Não ignore crescimento** - Custos podem explodir
2. **Não use janela muito pequena** - Perde contexto útil
3. **Não limpe durante análise** - Espere conclusão de tarefa
4. **Não use valores fixos** - Adapte ao caso de uso
5. **Não confie só em limpeza manual** - Usuários esquecem

---

## Ferramentas de Debug

### Visualizar Memória

```python
def debug_memoria(chat):
    print("=== Debug de Memória ===")
    print(f"Mensagens: {len(chat.historico)}")
    print(f"Tokens: {chat.contar_tokens()}")
    print("\nÚltimas 3 mensagens:")
    for msg in chat.historico[-3:]:
        role = msg['role']
        content = msg['content'][:50]
        print(f"  [{role}]: {content}...")
    print("========================\n")

# Uso
chat = ChatComMemoria()
chat.enviar_mensagem("Mensagem 1")
chat.enviar_mensagem("Mensagem 2")
debug_memoria(chat)
```

### Gráfico ASCII de Crescimento

```python
def grafico_tokens(historico_tokens):
    print("\nGráfico de Tokens:")
    max_tokens = max(historico_tokens)
    
    for i, tokens in enumerate(historico_tokens):
        barras = int((tokens / max_tokens) * 40)
        print(f"Msg {i+1:2d}: {'█' * barras} {tokens}")
    print()

# Uso
tokens_historico = []
chat = ChatComMemoria()

for i in range(10):
    chat.enviar_mensagem(f"Pergunta {i+1}")
    tokens_historico.append(chat.contar_tokens())

grafico_tokens(tokens_historico)
```

**Saída:**
```
Gráfico de Tokens:
Msg  1: ████                                      50
Msg  2: ████████                                 100
Msg  3: ████████████                             150
Msg  4: ████████████████                         200
Msg  5: ████████████████████                     250
Msg  6: ████████████████████████                 300
Msg  7: ████████████████████████████             350
Msg  8: ████████████████████████████████         400
Msg  9: ████████████████████████████████████     450
Msg 10: ████████████████████████████████████████ 500
```

---

## Próximos Passos

- 💡 Veja aplicações práticas em [CASOS_DE_USO.md](CASOS_DE_USO.md)
- 🔧 Resolva problemas em [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📚 Revise conceitos em [CONCEITOS.md](CONCEITOS.md)
