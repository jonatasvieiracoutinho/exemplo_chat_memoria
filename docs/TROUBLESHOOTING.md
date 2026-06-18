# 🔧 Troubleshooting

Soluções para problemas comuns ao usar o chat com memória.

## Índice

- [Erros de Configuração](#erros-de-configuração)
- [Erros de API](#erros-de-api)
- [Erros de Execução](#erros-de-execução)
- [Problemas de Performance](#problemas-de-performance)
- [Diagnóstico Rápido](#diagnóstico-rápido)

---

## Erros de Configuração

### 1. Arquivo .env Não Encontrado

#### Erro

```
FileNotFoundError: Arquivo .env não encontrado.
Crie um arquivo .env na raiz do projeto com as configurações necessárias.
```

#### Causa

O arquivo `.env` não existe ou está no local errado.

#### Solução

**Passo 1:** Verificar localização do projeto

```bash
# Confirme que está na pasta correta
pwd  # Linux/macOS
cd    # Windows

# Saída esperada:
# c:\python_projects\exemplo_chat_memoria (ou similar)
```

**Passo 2:** Criar arquivo .env

```bash
# Windows PowerShell
New-Item .env -ItemType File

# Linux/macOS
touch .env
```

**Passo 3:** Adicionar configurações mínimas

```env
OPENAI_API_KEY=sk-proj-sua_chave_aqui
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=1000
```

**Passo 4:** Verificar

```bash
# Listar arquivos
ls -a  # Linux/macOS
dir    # Windows

# Deve aparecer .env na lista
```

#### Verificação

```python
import os
print(os.path.exists('.env'))  # Deve retornar True
```

---

### 2. API Key Não Encontrada

#### Erro

```
ValueError: OPENAI_API_KEY não encontrada no arquivo .env
```

#### Causa

A variável `OPENAI_API_KEY` não está definida no `.env`.

#### Solução

**Passo 1:** Abrir arquivo .env

```bash
# Windows
notepad .env

# Linux/macOS
nano .env
# ou
vim .env
```

**Passo 2:** Adicionar linha

```env
OPENAI_API_KEY=sk-proj-sua_chave_real_aqui
```

⚠️ **Importante:**
- Não use aspas ao redor da chave
- Não deixe espaços antes/depois do `=`
- Substitua `sua_chave_real_aqui` pela key real

**Passo 3:** Obter API key

1. Acesse: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Login na sua conta OpenAI
3. Clique em "Create new secret key"
4. Copie a chave (começa com `sk-proj-` ou `sk-`)
5. Cole no arquivo .env

#### Verificação

```python
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv('OPENAI_API_KEY')
print(f"Key encontrada: {key is not None}")
print(f"Key válida: {key.startswith('sk-') if key else False}")
```

---

### 3. API Key com Formato Inválido

#### Erro

```
ValueError: OPENAI_API_KEY deve começar com 'sk-'. Valor atual: 'minha_chave_123'
```

#### Causa

A API key não está no formato correto da OpenAI.

#### Solução

**Formato correto:**
- Sempre começa com `sk-` ou `sk-proj-`
- Tem aproximadamente 40-50 caracteres
- Contém apenas letras, números e hífens

**Exemplos válidos:**
```
sk-abc123def456ghi789jkl012mno345pqr678
sk-proj-xyz789abc456def123ghi890jkl567mno
```

**Exemplo inválido:**
```
minha_chave_123          ❌ Não começa com sk-
openai_api_key           ❌ Formato errado
sk-abc                   ❌ Muito curta
```

**Ação:** Obtenha uma key válida em [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

### 4. Modelo Não Encontrado

#### Erro

```
ValueError: OPENAI_MODEL não encontrada no arquivo .env
```

#### Causa

Variável `OPENAI_MODEL` não está definida.

#### Solução

Adicionar ao `.env`:

```env
OPENAI_MODEL=gpt-4o-mini
```

**Modelos disponíveis:**
- `gpt-4o-mini` - Rápido e econômico (recomendado)
- `gpt-4o` - Mais poderoso
- `gpt-4-turbo` - GPT-4 otimizado
- `gpt-3.5-turbo` - Mais antigo e barato

---

### 5. Temperature Inválida

#### Erro

```
ValueError: OPENAI_TEMPERATURE deve estar entre 0.0 e 2.0. Valor atual: 3.5
```

#### Causa

Temperature fora do range permitido (0.0 a 2.0).

#### Solução

Corrigir no `.env`:

```env
# ❌ Errado
OPENAI_TEMPERATURE=3.5
OPENAI_TEMPERATURE=-1.0

# ✅ Correto
OPENAI_TEMPERATURE=0.7
OPENAI_TEMPERATURE=0.0
OPENAI_TEMPERATURE=2.0
```

**Valores recomendados:**
- `0.0` - Determinístico
- `0.7` - Balanceado (padrão)
- `1.5` - Criativo

#### Verificação

```python
temp = float(os.getenv('OPENAI_TEMPERATURE'))
assert 0.0 <= temp <= 2.0, "Temperature inválida"
print(f"Temperature válida: {temp}")
```

---

### 6. Max Tokens Inválido

#### Erro

```
ValueError: OPENAI_MAX_TOKENS deve ser um número inteiro positivo. Valor atual: -100
```

ou

```
ValueError: OPENAI_MAX_TOKENS deve ser um número inteiro positivo. Valor atual: abc
```

#### Causa

Max tokens não é um inteiro positivo.

#### Solução

Corrigir no `.env`:

```env
# ❌ Errado
OPENAI_MAX_TOKENS=-100    # Negativo
OPENAI_MAX_TOKENS=0       # Zero
OPENAI_MAX_TOKENS=abc     # Não é número
OPENAI_MAX_TOKENS=1000.5  # Não é inteiro

# ✅ Correto
OPENAI_MAX_TOKENS=1000
OPENAI_MAX_TOKENS=500
OPENAI_MAX_TOKENS=2000
```

**Valores comuns:**
- `500` - Respostas curtas
- `1000` - Respostas médias (recomendado)
- `2000` - Respostas longas

#### Verificação

```python
tokens = int(os.getenv('OPENAI_MAX_TOKENS'))
assert tokens > 0, "Max tokens deve ser positivo"
print(f"Max tokens válido: {tokens}")
```

---

## Erros de API

### 7. Erro de Autenticação

#### Erro

```
openai.AuthenticationError: Incorrect API key provided: sk-proj-abc***
```

ou

```
openai.AuthenticationError: Invalid API key
```

#### Causa

API key incorreta, expirada ou sem créditos.

#### Solução

**Passo 1:** Verificar key no dashboard

1. Acesse: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Verifique se a key ainda existe e está ativa
3. Se não aparece, foi deletada ou expirou

**Passo 2:** Criar nova key

1. Clique "Create new secret key"
2. Dê um nome descritivo
3. Copie a key (só aparece uma vez!)
4. Atualize o `.env`

**Passo 3:** Verificar créditos

1. Acesse: [https://platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
2. Verifique se há créditos disponíveis
3. Adicione forma de pagamento se necessário

#### Teste de Autenticação

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

try:
    # Teste simples
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=10
    )
    print("✅ Autenticação OK!")
except Exception as e:
    print(f"❌ Erro: {e}")
```

---

### 8. Rate Limit Excedido

#### Erro

```
openai.RateLimitError: Rate limit exceeded
```

ou

```
openai.RateLimitError: You exceeded your current quota
```

#### Causa

**Tipo 1:** Muitas requisições por minuto (RPM)  
**Tipo 2:** Sem créditos ou quota esgotada  

#### Solução para Tipo 1 (RPM)

Aguardar e implementar retry:

```python
import time
from openai import OpenAI

def enviar_com_retry(chat, mensagem, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            return chat.enviar_mensagem(mensagem)
        except Exception as e:
            if "rate limit" in str(e).lower():
                if tentativa < max_tentativas - 1:
                    tempo_espera = (tentativa + 1) * 5
                    print(f"Rate limit. Aguardando {tempo_espera}s...")
                    time.sleep(tempo_espera)
                else:
                    raise
            else:
                raise
```

#### Solução para Tipo 2 (Quota)

1. Acesse: [https://platform.openai.com/account/billing/overview](https://platform.openai.com/account/billing/overview)
2. Adicione créditos ou configure faturamento
3. Verifique limites de uso

#### Limites Comuns

| Plano | RPM (Requests/min) | TPM (Tokens/min) |
|-------|-------------------|------------------|
| Free Trial | 3 | 40,000 |
| Pay-as-you-go (inicial) | 60 | 90,000 |
| Pay-as-you-go (tier 2) | 3,500 | 5,000,000 |

---

### 9. Modelo Não Existe

#### Erro

```
openai.NotFoundError: The model 'gpt-5' does not exist
```

#### Causa

Nome do modelo está incorreto ou modelo não existe.

#### Solução

Usar modelos válidos no `.env`:

```env
# ✅ Modelos válidos (Dez 2024)
OPENAI_MODEL=gpt-4o-mini
OPENAI_MODEL=gpt-4o
OPENAI_MODEL=gpt-4-turbo
OPENAI_MODEL=gpt-3.5-turbo

# ❌ Modelos inválidos
OPENAI_MODEL=gpt-5           # Não existe
OPENAI_MODEL=gpt4            # Formato errado
OPENAI_MODEL=chatgpt         # Nome incorreto
```

#### Verificar Modelos Disponíveis

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

models = client.models.list()
gpt_models = [m.id for m in models if 'gpt' in m.id.lower()]

print("Modelos GPT disponíveis:")
for model in sorted(gpt_models):
    print(f"  - {model}")
```

---

## Erros de Execução

### 10. Import Error

#### Erro

```
ModuleNotFoundError: No module named 'openai'
```

ou

```
ModuleNotFoundError: No module named 'dotenv'
```

#### Causa

Dependências não instaladas ou ambiente errado.

#### Solução

**Passo 1:** Ativar o ambiente virtual do projeto

```bash
# Windows (CMD/PowerShell)
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

**Passo 2:** Instalar dependências

```bash
pip install -r requirements.txt
```

**Passo 3:** Verificar instalação

```bash
pip list | grep openai
pip list | grep python-dotenv
```

**Saída esperada:**
```
openai                1.12.0
python-dotenv         1.0.0
```

---

### 11. Encoding Error (Windows)

#### Erro

```
UnicodeDecodeError: 'charmap' codec can't decode byte...
```

#### Causa

Problema de encoding no Windows ao ler/escrever arquivos.

#### Solução

**Opção 1:** Definir encoding UTF-8

```python
# Ao exportar conversa
with open('conversa.txt', 'w', encoding='utf-8') as f:
    f.write(conteudo)
```

**Opção 2:** Configurar terminal

```bash
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# CMD
chcp 65001
```

---

### 12. Timeout na API

#### Erro

```
openai.APITimeoutError: Request timed out
```

#### Causa

Requisição demorou muito (rede lenta ou histórico grande).

#### Solução

Aumentar timeout:

```python
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    timeout=60.0  # 60 segundos (padrão: 30)
)
```

Ou reduzir tamanho do histórico:

```python
chat = ChatComMemoria()

# Limpar se muito grande
if chat.contar_tokens() > 2000:
    chat.limpar_historico()
```

---

## Problemas de Performance

### 13. Respostas Lentas

#### Sintoma

Chat demora muito para responder.

#### Causas Possíveis

1. **Histórico muito grande** - Muitos tokens para processar
2. **Modelo pesado** - GPT-4o é mais lento que gpt-4o-mini
3. **Rede lenta** - Conexão instável

#### Soluções

**1. Reduzir histórico:**

```python
# Aplicar sliding window
if len(chat.historico) > 10:
    chat.historico = chat.historico[-10:]
```

**2. Usar modelo mais rápido:**

```env
# Trocar no .env
OPENAI_MODEL=gpt-4o-mini  # Mais rápido
```

**3. Limitar max_tokens:**

```env
# Respostas mais curtas = mais rápidas
OPENAI_MAX_TOKENS=500
```

**4. Medir performance:**

```python
import time

inicio = time.time()
resposta = chat.enviar_mensagem("Sua pergunta")
duracao = time.time() - inicio

print(f"Tempo de resposta: {duracao:.2f}s")
```

---

### 14. Custos Altos

#### Sintoma

Conta da OpenAI crescendo rapidamente.

#### Diagnóstico

```python
# Monitorar tokens
chat = ChatComMemoria()

# Após várias interações
tokens = chat.contar_tokens()
estimativa_custo = tokens * 0.00001  # Exemplo: $0.00001/token

print(f"Tokens: {tokens}")
print(f"Custo estimado: ${estimativa_custo:.4f}")
```

#### Soluções

**1. Limpar histórico regularmente:**

```python
if chat.contar_tokens() > 1000:
    chat.limpar_historico()
```

**2. Usar sliding window:**

Ver [GERENCIAMENTO_MEMORIA.md](GERENCIAMENTO_MEMORIA.md)

**3. Usar modelo mais barato:**

```env
OPENAI_MODEL=gpt-4o-mini  # 60x mais barato que GPT-4
```

**4. Monitorar no dashboard:**

[https://platform.openai.com/usage](https://platform.openai.com/usage)

---

### 15. Memória Cheia (Sistema)

#### Sintoma

```
MemoryError: Unable to allocate...
```

#### Causa

Histórico muito grande consumindo RAM.

#### Solução

```python
# Limitar tamanho máximo
MAX_MENSAGENS = 100

if len(chat.historico) > MAX_MENSAGENS:
    # Manter apenas as mais recentes
    chat.historico = chat.historico[-MAX_MENSAGENS:]
```

---

## Diagnóstico Rápido

### Script de Verificação Completa

```python
import os
from dotenv import load_dotenv

def diagnostico_completo():
    print("=== DIAGNÓSTICO DO SISTEMA ===\n")
    
    # 1. Verificar .env
    print("1. Arquivo .env:")
    if os.path.exists('.env'):
        print("   ✅ Encontrado")
    else:
        print("   ❌ NÃO ENCONTRADO")
        return
    
    # 2. Carregar variáveis
    load_dotenv()
    print("\n2. Variáveis de Ambiente:")
    
    # API Key
    key = os.getenv('OPENAI_API_KEY')
    if key:
        print(f"   ✅ OPENAI_API_KEY: {key[:7]}***")
        if not key.startswith('sk-'):
            print("      ⚠️  Formato suspeito (deve começar com 'sk-')")
    else:
        print("   ❌ OPENAI_API_KEY: NÃO ENCONTRADA")
    
    # Model
    model = os.getenv('OPENAI_MODEL')
    if model:
        print(f"   ✅ OPENAI_MODEL: {model}")
    else:
        print("   ❌ OPENAI_MODEL: NÃO ENCONTRADA")
    
    # Temperature
    temp = os.getenv('OPENAI_TEMPERATURE')
    if temp:
        try:
            temp_float = float(temp)
            if 0.0 <= temp_float <= 2.0:
                print(f"   ✅ OPENAI_TEMPERATURE: {temp}")
            else:
                print(f"   ❌ OPENAI_TEMPERATURE: {temp} (fora do range 0.0-2.0)")
        except ValueError:
            print(f"   ❌ OPENAI_TEMPERATURE: {temp} (não é número)")
    else:
        print("   ❌ OPENAI_TEMPERATURE: NÃO ENCONTRADA")
    
    # Max Tokens
    tokens = os.getenv('OPENAI_MAX_TOKENS')
    if tokens:
        try:
            tokens_int = int(tokens)
            if tokens_int > 0:
                print(f"   ✅ OPENAI_MAX_TOKENS: {tokens}")
            else:
                print(f"   ❌ OPENAI_MAX_TOKENS: {tokens} (deve ser > 0)")
        except ValueError:
            print(f"   ❌ OPENAI_MAX_TOKENS: {tokens} (não é inteiro)")
    else:
        print("   ❌ OPENAI_MAX_TOKENS: NÃO ENCONTRADA")
    
    # 3. Testar importações
    print("\n3. Dependências:")
    try:
        import openai
        print(f"   ✅ openai (versão {openai.__version__})")
    except ImportError:
        print("   ❌ openai: NÃO INSTALADA")
    
    try:
        import dotenv
        print(f"   ✅ python-dotenv")
    except ImportError:
        print("   ❌ python-dotenv: NÃO INSTALADA")
    
    # 4. Testar API (se tudo OK)
    if key and key.startswith('sk-'):
        print("\n4. Teste de API:")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "teste"}],
                max_tokens=5
            )
            print("   ✅ Conexão com API: OK")
        except Exception as e:
            print(f"   ❌ Erro na API: {e}")
    
    print("\n=== FIM DO DIAGNÓSTICO ===")

if __name__ == "__main__":
    diagnostico_completo()
```

**Executar:**

```bash
python diagnostico.py
```

---

## Checklist de Resolução

Ao encontrar um erro, siga esta ordem:

- [ ] 1. Arquivo `.env` existe na pasta correta?
- [ ] 2. Todas as 4 variáveis estão definidas?
- [ ] 3. `OPENAI_API_KEY` começa com `sk-`?
- [ ] 4. `OPENAI_TEMPERATURE` está entre 0.0 e 2.0?
- [ ] 5. `OPENAI_MAX_TOKENS` é inteiro positivo?
- [ ] 6. Dependências instaladas? (`pip list`)
- [ ] 7. Ambiente virtual (.venv) ativo?
- [ ] 8. API key válida no dashboard OpenAI?
- [ ] 9. Créditos disponíveis na conta?
- [ ] 10. Internet funcionando?

---

## Suporte Adicional

### Recursos Oficiais

- **Documentação OpenAI:** [https://platform.openai.com/docs](https://platform.openai.com/docs)
- **Status da API:** [https://status.openai.com/](https://status.openai.com/)
- **Fórum da Comunidade:** [https://community.openai.com/](https://community.openai.com/)

### Logs de Debug

Habilitar logs detalhados:

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Agora todas as operações mostrarão logs detalhados
chat = ChatComMemoria()
```

---

## Próximos Passos

Se todos os problemas foram resolvidos:

- 🚀 Volte para [USO_BASICO.md](USO_BASICO.md) para usar o chat
- ⚡ Explore [EXEMPLOS_AVANCADOS.md](EXEMPLOS_AVANCADOS.md) para técnicas avançadas
- 💡 Veja [CASOS_DE_USO.md](CASOS_DE_USO.md) para aplicações práticas
