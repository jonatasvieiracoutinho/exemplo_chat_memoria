# 🤖 Guidelines para Agentes de IA

Guia de contexto e boas práticas para agentes de IA trabalhando neste projeto.

## 📋 Visão Geral do Projeto

**Nome:** Chat OpenAI com Memória  
**Objetivo:** Projeto educacional demonstrando implementação de chat com memória conversacional  
**Linguagem:** Python 3.11+  
**Público-alvo:** Estudantes de IA Generativa  

## 🎯 Propósito

Sistema de chat que mantém histórico completo de conversação, permitindo:
- Contexto preservado entre mensagens
- Personalização via system prompts
- Gerenciamento de memória e custos
- Exportação de conversas

## 🏗️ Arquitetura

### Componente Principal

```python
class ChatComMemoria:
    - historico: List[Dict]        # Armazena todas as mensagens
    - client: OpenAI               # Cliente da API
    - system_prompt: str           # Personalidade do assistente
    - model, temperature, max_tokens  # Configurações da API
```

### Fluxo de Dados

```
Usuário → enviar_mensagem() → [adiciona ao histórico] 
       → API OpenAI (com histórico completo)
       → Resposta → [adiciona ao histórico] → Retorna ao usuário
```

### Arquivos Principais

| Arquivo | Responsabilidade |
|---------|------------------|
| `chat_openai_memoria.py` | Classe principal e modo interativo |
| `exemplos_avancados.py` | Demonstrações de técnicas avançadas |
| `requirements.txt` | Dependências: openai, python-dotenv |
| `.env` | Configurações (não versionado) |

## 🔧 Padrões de Código

### Estilo

- **PEP 8** para formatação
- **Docstrings** em português para métodos públicos
- **Type hints** onde apropriado
- **Nomenclatura:** snake_case para funções/variáveis, PascalCase para classes

### Validação Obrigatória

Toda inicialização DEVE validar:
```python
# Arquivo .env existe
# API key presente e formato válido (começa com 'sk-')
# Temperature: 0.0 <= valor <= 2.0
# Max tokens: inteiro > 0
```

Mensagens de erro devem ser **claras e acionáveis**.

### Gerenciamento de Histórico

```python
# Estrutura de mensagem
{"role": "user" | "assistant", "content": str}

# System prompt NÃO vai no histórico
# Enviado separadamente em cada requisição
```

## 📚 Documentação

Documentação completa em [`docs/`](docs/):

- **Setup:** [INSTALACAO.md](docs/INSTALACAO.md) - Ambiente e configuração
- **Conceitos:** [CONCEITOS.md](docs/CONCEITOS.md) - Memória, temperature, tokens
- **Uso:** [USO_BASICO.md](docs/USO_BASICO.md) - API da classe e comandos
- **Avançado:** [EXEMPLOS_AVANCADOS.md](docs/EXEMPLOS_AVANCADOS.md) - Técnicas complexas
- **Otimização:** [GERENCIAMENTO_MEMORIA.md](docs/GERENCIAMENTO_MEMORIA.md) - Custos e estratégias
- **Troubleshooting:** [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Resolução de problemas
- **Casos de Uso:** [CASOS_DE_USO.md](docs/CASOS_DE_USO.md) - Exemplos práticos

## ⚡ Quick Reference

### Métodos Principais

```python
chat = ChatComMemoria()  # Inicializa e valida .env
chat.definir_system_prompt(prompt: str)  # Define personalidade
chat.enviar_mensagem(msg: str) -> str    # Envia e recebe resposta
chat.limpar_historico()                  # Zera memória
chat.contar_tokens() -> int              # Estima tokens (~4 chars = 1 token)
chat.exportar_conversa(arquivo: str)     # Salva em TXT
```

### Comandos Interativos

```
/limpar    - Limpa memória
/historico - Exibe conversação
/tokens    - Mostra contagem
/exportar  - Salva conversa
/sair      - Encerra
```

## 🎨 Padrões de Uso

### ✅ Fazer

```python
# Instâncias separadas para contextos diferentes
chat_professor = ChatComMemoria()
chat_revisor = ChatComMemoria()

# Limpar memória ao mudar de tópico
chat.limpar_historico()

# Monitorar tokens periodicamente
if chat.contar_tokens() > 1000:
    chat.limpar_historico()

# Tratamento de erros na inicialização
try:
    chat = ChatComMemoria()
except (FileNotFoundError, ValueError) as e:
    print(f"Erro de configuração: {e}")
```

### ❌ Não Fazer

```python
# Não usar mesma instância para múltiplos contextos
# Não modificar historico diretamente sem entender impacto
# Não assumir valores padrão (todas configs são obrigatórias)
# Não ignorar crescimento de tokens
```

## 🧪 Testes e Validação

### Validar Após Mudanças

```bash
# Teste básico
python chat_openai_memoria.py --exemplo

# Testes avançados
python exemplos_avancados.py --todos

# Verificar imports
python -c "from chat_openai_memoria import ChatComMemoria; print('OK')"
```

### Cenários Críticos

1. **Inicialização sem .env** → Deve falhar com erro claro
2. **Temperature inválida** → Deve validar range 0.0-2.0
3. **Max tokens inválido** → Deve validar inteiro positivo
4. **Memória crescente** → Tokens devem aumentar linearmente

## 🔐 Segurança

- **API keys:** Nunca fazer commit (usar .env, gitignored)
- **Validação:** Sempre validar inputs antes de enviar à API
- **Custos:** Implementar limites de tokens em produção

## 🚀 Extensões Comuns

### Sliding Window

```python
# Manter apenas N mensagens recentes
if len(chat.historico) > MAX_MENSAGENS:
    chat.historico = chat.historico[-MAX_MENSAGENS:]
```

### Monitoramento

```python
# Adicionar logging
import logging
logging.basicConfig(level=logging.INFO)
logging.info(f"Tokens: {chat.contar_tokens()}")
```

### Personalidades Múltiplas

```python
# Criar especializações
class ChatProfessor(ChatComMemoria):
    def __init__(self):
        super().__init__()
        self.definir_system_prompt("Você é um professor...")
```

## 📊 Métricas de Qualidade

- **Validação completa** de configurações
- **Mensagens de erro claras** e acionáveis
- **Código documentado** (docstrings em português)
- **Exemplos funcionais** em `exemplos_avancados.py`
- **Performance:** Inicialização < 1s, resposta depende da API

## 🔍 Debugging

```python
# Ver histórico completo
chat.exibir_historico()

# Estimar tokens
print(chat.contar_tokens())

# Verificar configuração
print(f"Model: {chat.model}")
print(f"Temperature: {chat.temperature}")
print(f"Max tokens: {chat.max_tokens}")
```

## 📝 Convenções de Commit

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Alteração em documentação
- `refactor:` Refatoração sem mudança de comportamento
- `test:` Adição/modificação de testes

## 🤝 Contribuindo

Ao adicionar funcionalidades:

1. ✅ Manter compatibilidade com API existente
2. ✅ Adicionar validação apropriada
3. ✅ Documentar em docstrings
4. ✅ Atualizar documentação em `docs/` se necessário
5. ✅ Testar com `exemplos_avancados.py`
6. ✅ Verificar impacto em custos (tokens)

## 🎓 Contexto Educacional

Este é um **projeto educacional**. Priorize:

- **Clareza** sobre performance
- **Simplicidade** sobre otimização prematura
- **Didática** nas mensagens de erro
- **Exemplos práticos** sobre abstrações complexas

---

**Dúvidas?** Consulte [README.md](README.md) ou documentação em [`docs/`](docs/)
