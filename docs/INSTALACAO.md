# 📦 Instalação

Guia completo para configurar o ambiente e executar o chat com memória.

## Índice

- [Pré-requisitos](#pré-requisitos)
- [Passo 1: Instalar o Miniconda](#passo-1-instalar-o-miniconda)
- [Passo 2: Criar Ambiente Conda](#passo-2-criar-ambiente-conda)
- [Passo 3: Instalar Dependências](#passo-3-instalar-dependências)
- [Passo 4: Configurar Variáveis de Ambiente](#passo-4-configurar-variáveis-de-ambiente)
- [Passo 5: Verificar Instalação](#passo-5-verificar-instalação)

---

## Pré-requisitos

- Sistema operacional: Windows, Linux ou macOS
- Conta na OpenAI com API key ativa ([criar conta aqui](https://platform.openai.com/signup))
- Conhecimento básico de linha de comando

---

## Passo 1: Instalar o Miniconda

O Miniconda é uma versão mínima do Anaconda que permite gerenciar ambientes Python isolados.

### Download

Acesse o site oficial e baixe o instalador para seu sistema:

**🔗 [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)**

### Instalação por Sistema Operacional

#### Windows

1. Execute o instalador `.exe` baixado
2. Siga o assistente de instalação
3. ✅ Marque a opção "Add Miniconda3 to PATH" (recomendado)
4. Conclua a instalação
5. Abra o **Anaconda Prompt** ou **CMD/PowerShell**

#### Linux/macOS

```bash
# Após baixar o instalador .sh
chmod +x Miniconda3-latest-Linux-x86_64.sh  # ou macOS equivalente
./Miniconda3-latest-Linux-x86_64.sh

# Siga as instruções no terminal
# Aceite a licença e confirme a localização da instalação
```

### Verificar Instalação

```bash
conda --version
# Saída esperada: conda 24.x.x (ou similar)
```

---

## Passo 2: Criar Ambiente Conda

Crie um ambiente isolado para o projeto:

```bash
# Criar ambiente com Python 3.11
conda create -n chat_memoria python=3.11 -y

# Ativar o ambiente
conda activate chat_memoria
```

**📌 Nota:** Você precisará ativar o ambiente sempre que for usar o projeto:
```bash
conda activate chat_memoria
```

---

## Passo 3: Instalar Dependências

Navegue até a pasta do projeto e instale as bibliotecas necessárias:

```bash
# Navegar para o diretório do projeto
cd c:\python_projects\exemplo_chat_memoria  # Windows
# ou
cd ~/python_projects/exemplo_chat_memoria   # Linux/macOS

# Instalar dependências
pip install -r requirements.txt
```

### Dependências Instaladas

O projeto usa duas bibliotecas principais:

- **openai** (>=1.12.0): Cliente oficial da API OpenAI
- **python-dotenv** (>=1.0.0): Carregamento de variáveis de ambiente

---

## Passo 4: Configurar Variáveis de Ambiente

### 4.1 Criar Arquivo .env

Crie um arquivo chamado `.env` na raiz do projeto:

```bash
# Windows (PowerShell)
New-Item .env -ItemType File

# Linux/macOS
touch .env
```

### 4.2 Adicionar Configurações

Edite o arquivo `.env` e adicione as seguintes variáveis:

```env
# API Key da OpenAI (obrigatório)
OPENAI_API_KEY=sk-proj-sua_chave_aqui

# Modelo a ser usado (obrigatório)
OPENAI_MODEL=gpt-4o-mini

# Temperatura - controla criatividade (obrigatório: 0.0 a 2.0)
OPENAI_TEMPERATURE=0.7

# Máximo de tokens na resposta (obrigatório: inteiro positivo)
OPENAI_MAX_TOKENS=1000
```

### 4.3 Detalhamento das Variáveis

#### OPENAI_API_KEY

- **Obrigatório:** Sim
- **Formato:** String começando com `sk-` ou `sk-proj-`
- **Onde obter:** [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Exemplo:** `sk-proj-abc123def456...`

⚠️ **Segurança:** Nunca compartilhe sua API key ou faça commit dela no Git!

#### OPENAI_MODEL

- **Obrigatório:** Sim
- **Valores comuns:**
  - `gpt-4o-mini` - Rápido e econômico (recomendado)
  - `gpt-4o` - Mais poderoso, mais caro
  - `gpt-3.5-turbo` - Alternativa mais antiga
- **Exemplo:** `gpt-4o-mini`

#### OPENAI_TEMPERATURE

- **Obrigatório:** Sim
- **Formato:** Número decimal entre 0.0 e 2.0
- **Valores:**
  - `0.0` - Respostas determinísticas e focadas
  - `0.7` - Balanceado (recomendado para uso geral)
  - `1.0` - Mais criativo
  - `2.0` - Máxima aleatoriedade
- **Exemplo:** `0.7`

#### OPENAI_MAX_TOKENS

- **Obrigatório:** Sim
- **Formato:** Número inteiro positivo (> 0)
- **Descrição:** Limita o tamanho máximo da resposta
- **Valores sugeridos:**
  - `500` - Respostas curtas
  - `1000` - Respostas médias (recomendado)
  - `2000` - Respostas longas
- **Exemplo:** `1000`

#### OPENAI_BASE_URL

- **Obrigatório:** Não
- **Formato:** URL completa começando com `http://` ou `https://`
- **Descrição:** URL base customizada para conectar a provedores compatíveis com o padrão OpenAI
- **Quando usar:**
  - **Azure OpenAI Service** - Usar endpoint do seu recurso Azure
  - **Ollama** - Executar modelos localmente
  - **LM Studio** - Testar modelos locais
  - **Outros provedores** - Qualquer serviço compatível com API OpenAI
- **Se não configurada:** Usa o endpoint padrão da OpenAI (`https://api.openai.com/v1`)
- **Exemplos:**
  - Azure: `https://seu-recurso.openai.azure.com`
  - Ollama: `http://localhost:11434/v1`
  - LM Studio: `http://localhost:1234/v1`

**Casos de uso comuns:**

1. **Azure OpenAI Service**
   ```env
   OPENAI_BASE_URL=https://seu-recurso.openai.azure.com
   OPENAI_API_KEY=sua-chave-azure
   OPENAI_MODEL=gpt-4o-mini  # ou modelo disponível no Azure
   ```

2. **Ollama (modelos locais)**
   ```env
   OPENAI_BASE_URL=http://localhost:11434/v1
   OPENAI_API_KEY=ollama  # Ollama não valida a key, mas é obrigatória
   OPENAI_MODEL=llama2  # ou outro modelo instalado no Ollama
   ```

3. **LM Studio (desenvolvimento local)**
   ```env
   OPENAI_BASE_URL=http://localhost:1234/v1
   OPENAI_API_KEY=lm-studio  # LM Studio não valida, mas é obrigatória
   OPENAI_MODEL=local-model  # modelo carregado no LM Studio
   ```

⚠️ **Importante:** 
- A URL deve terminar com `/v1` para a maioria dos provedores
- Verifique a documentação do seu provedor para detalhes específicos
- Para serviços locais (Ollama, LM Studio), certifique-se de que o servidor está rodando

### 4.4 Validação Manual

Após criar o `.env`, verifique:

✅ Arquivo está na raiz do projeto (mesmo diretório de `chat_openai_memoria.py`)  
✅ API key está no formato correto  
✅ Temperature está entre 0.0 e 2.0  
✅ Max tokens é um número inteiro positivo  
✅ Base URL (se configurada) começa com http:// ou https://  
✅ Não há espaços antes ou depois do `=`  

---

## Passo 5: Verificar Instalação

### 5.1 Teste Básico

Execute o chat para verificar se tudo está funcionando:

```bash
python chat_openai_memoria.py
```

**Saída esperada:**

```
=== Configuração do Chat ===
Modelo: gpt-4o-mini
Temperatura: 0.7
Max Tokens: 1000
============================

Chat com Memória - Digite 'sair' para encerrar
Você: 
```

### 5.2 Teste de API

Digite uma mensagem simples para testar a conexão com a API:

```
Você: Olá, você está funcionando?
```

Se receber uma resposta do assistente, a instalação está completa! ✅

### 5.3 Solução de Problemas

Se encontrar erros, consulte o [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para soluções.

#### Erros Comuns

| Erro | Causa Provável |
|------|----------------|
| `Arquivo .env não encontrado` | Arquivo .env não existe ou está no local errado |
| `OPENAI_API_KEY não encontrada` | Variável não definida no .env |
| `OPENAI_TEMPERATURE deve estar entre 0.0 e 2.0` | Valor inválido para temperature |
| `OPENAI_MAX_TOKENS deve ser um número inteiro positivo` | Valor inválido para max_tokens |
| `OPENAI_BASE_URL inválida` | URL não começa com http:// ou https:// |
| `AuthenticationError` | API key inválida ou expirada |

---

## Próximos Passos

Após a instalação bem-sucedida:

1. 📚 Leia [CONCEITOS.md](CONCEITOS.md) para entender como funciona a memória conversacional
2. 🚀 Consulte [USO_BASICO.md](USO_BASICO.md) para aprender os comandos e modos de uso
3. ⚡ Explore [EXEMPLOS_AVANCADOS.md](EXEMPLOS_AVANCADOS.md) para técnicas avançadas

---

## Desinstalação

Para remover o ambiente:

```bash
# Desativar ambiente
conda deactivate

# Remover ambiente
conda env remove -n chat_memoria
```
