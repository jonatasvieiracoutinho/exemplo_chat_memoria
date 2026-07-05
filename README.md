# 💬 Chat OpenAI com Memória

Projeto educacional demonstrando implementação de chat com memória conversacional usando a API da OpenAI.

## 🎯 Público-Alvo

Este projeto é voltado para **estudantes de IA Generativa** que desejam entender na prática como funciona memória conversacional, gerenciamento de contexto e integração com APIs de LLMs.

## 📚 Documentação

### Primeiros Passos

| Documento | Descrição |
|-----------|-----------|
| 📦 [INSTALACAO.md](docs/INSTALACAO.md) | Guia completo de instalação com venv e configuração do ambiente |
| 📚 [CONCEITOS.md](docs/CONCEITOS.md) | Fundamentos de memória conversacional, temperature e max tokens |

### Uso e Desenvolvimento

| Documento | Descrição |
|-----------|-----------|
| 🚀 [USO_BASICO.md](docs/USO_BASICO.md) | Modos de uso (interativo, programático, biblioteca) e referência de métodos |
| ⚡ [EXEMPLOS_AVANCADOS.md](docs/EXEMPLOS_AVANCADOS.md) | Técnicas avançadas: múltiplas personalidades, sliding window, análise multi-turno |

### Otimização e Resolução de Problemas

| Documento | Descrição |
|-----------|-----------|
| 🧠 [GERENCIAMENTO_MEMORIA.md](docs/GERENCIAMENTO_MEMORIA.md) | Estratégias para controlar custos e otimizar memória |
| 🔧 [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Soluções para erros comuns de configuração, API e execução |

### Aplicações Práticas

| Documento | Descrição |
|-----------|-----------|
| 💡 [CASOS_DE_USO.md](docs/CASOS_DE_USO.md) | Exemplos práticos: assistente de estudos, revisor de código, suporte técnico |

---

## ⚡ Quick Start

### 1. Instalar

```bash
# Criar e ativar ambiente virtual (venv)
python -m venv .venv
# Windows (CMD/PowerShell): .venv\Scripts\activate
# Linux/macOS:              source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar

Crie arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-proj-sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

### 3. Executar

```bash
# Modo interativo
python chat_openai_memoria.py

# Exemplo demonstrativo
python chat_openai_memoria.py --exemplo

# Exemplos avançados
python exemplos_avancados.py
```

📖 Para instalação detalhada, consulte [INSTALACAO.md](docs/INSTALACAO.md)

---

## 🎨 Funcionalidades

### Chat Interativo

- ✅ Memória completa de conversação
- ✅ Comandos especiais (`/limpar`, `/historico`, `/tokens`, `/exportar`)
- ✅ Personalização via system prompt
- ✅ Exportação de conversas
- ✅ Persistência SQLite de conversas (threads) — ativada por `PERSISTENCIA_SQLITE=true` no `.env`
- ✅ Contagem real de tokens por turno (via `usage` da API), persistida junto com as threads

### Uso Programático

- ✅ Biblioteca Python reutilizável
- ✅ Múltiplas instâncias independentes
- ✅ Gerenciamento flexível de contexto
- ✅ Monitoramento de tokens

### Exemplos Avançados

- ✅ Múltiplas personalidades especializadas
- ✅ Controle estratégico de contexto
- ✅ Sliding window para conversas longas
- ✅ Análise de código multi-turno

---

## 📁 Estrutura do Projeto

```
exemplo_chat_memoria/
├── chat_openai_memoria.py    # Script principal com classe ChatComMemoria
├── exemplos_avancados.py     # Demonstrações de técnicas avançadas
├── requirements.txt          # Dependências do projeto
├── env.example               # Template de configuração
│
└── docs/                      # Documentação completa
    ├── INSTALACAO.md         # Guia de instalação
    ├── CONCEITOS.md          # Fundamentos teóricos
    ├── USO_BASICO.md         # Manual de uso
    ├── EXEMPLOS_AVANCADOS.md # Técnicas avançadas
    ├── GERENCIAMENTO_MEMORIA.md  # Otimização de custos
    ├── TROUBLESHOOTING.md    # Resolução de problemas
    └── CASOS_DE_USO.md       # Aplicações práticas
```

---

## 🚀 Exemplos de Uso

### Chat Básico

```python
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria()
resposta = chat.enviar_mensagem("Olá! Me explique sobre Python")
print(resposta)
```

### Múltiplas Personalidades

```python
professor = ChatComMemoria()
professor.definir_system_prompt("Você é um professor didático")

revisor = ChatComMemoria()
revisor.definir_system_prompt("Você é um revisor de código técnico")

# Cada instância mantém contexto independente
```

### Gerenciamento de Contexto

```python
chat = ChatComMemoria()

# Conversa sobre Python
chat.enviar_mensagem("Explique decorators")
chat.enviar_mensagem("Dê um exemplo")

# Limpar antes de mudar de assunto
chat.limpar_historico()

# Nova conversa sobre JavaScript
chat.enviar_mensagem("Explique closures")
```

📖 Mais exemplos em [USO_BASICO.md](docs/USO_BASICO.md) e [EXEMPLOS_AVANCADOS.md](docs/EXEMPLOS_AVANCADOS.md)

---

## 💰 Sobre Custos

- Você paga por **tokens de entrada + tokens de saída**
- Histórico completo é enviado a cada requisição
- Conversas longas custam progressivamente mais
- Use estratégias de gerenciamento para controlar custos

📖 Veja estratégias detalhadas em [GERENCIAMENTO_MEMORIA.md](docs/GERENCIAMENTO_MEMORIA.md)

---

## ⚠️ Limitações

- **Persistência opcional:** Por padrão, a memória é perdida ao fechar o programa; ative `PERSISTENCIA_SQLITE=true` para salvar conversas localmente
- **Crescimento linear:** Custos aumentam com tamanho do histórico
- **Gerenciamento manual:** Usuário deve controlar limpeza de contexto
- **Single-user:** O banco SQLite local não suporta múltiplos usuários simultâneos

---

## 🎓 Aprendizado

Este projeto é ideal para entender:

- Como APIs de chat com LLMs funcionam
- Importância e custo da memória conversacional
- Estratégias de otimização de contexto
- Integração com OpenAI API
- Boas práticas de desenvolvimento com IA

---

## 📖 Documentação Completa

Comece pela ordem sugerida ou navegue livremente:

1. 📦 [INSTALACAO.md](docs/INSTALACAO.md) - Configure o ambiente
2. 📚 [CONCEITOS.md](docs/CONCEITOS.md) - Entenda os fundamentos
3. 🚀 [USO_BASICO.md](docs/USO_BASICO.md) - Aprenda a usar
4. ⚡ [EXEMPLOS_AVANCADOS.md](docs/EXEMPLOS_AVANCADOS.md) - Explore técnicas avançadas
5. 🧠 [GERENCIAMENTO_MEMORIA.md](docs/GERENCIAMENTO_MEMORIA.md) - Otimize custos
6. 💡 [CASOS_DE_USO.md](docs/CASOS_DE_USO.md) - Veja aplicações práticas
7. 🔧 [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Resolva problemas

---

## 🔗 Recursos Externos

- [Documentação OpenAI](https://platform.openai.com/docs)
- [Python dotenv](https://pypi.org/project/python-dotenv/)
- [OpenAI Python SDK](https://github.com/openai/openai-python)

---

## 📝 Licença

Projeto educacional de código aberto.

