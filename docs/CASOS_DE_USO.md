# 💡 Casos de Uso

Aplicações práticas do chat com memória em cenários reais.

## Índice

- [1. Assistente de Estudos](#1-assistente-de-estudos)
- [2. Revisor de Código](#2-revisor-de-código)
- [3. Suporte Técnico](#3-suporte-técnico)
- [4. Tutor Personalizado](#4-tutor-personalizado)
- [5. Analisador de Documentos](#5-analisador-de-documentos)

---

## 1. Assistente de Estudos

### Cenário

Estudante precisa de ajuda para entender um tópico específico, fazer perguntas de acompanhamento e revisar o que aprendeu.

### Por que memória é importante?

- Perguntas subsequentes referenciam explicações anteriores
- Não precisa repetir contexto a cada pergunta
- Assistente pode construir progressivamente o conhecimento

### Estratégia de Memória

```
+----------------------+
| Estratégia:          |
| - Manter contexto    |
|   completo durante   |
|   sessão de estudo   |
| - Limpar ao mudar    |
|   de matéria         |
| - Janela: 12-16 msgs |
+----------------------+
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria

class AssistenteEstudos:
    def __init__(self, materia):
        self.chat = ChatComMemoria()
        self.materia = materia
        self.chat.definir_system_prompt(
            f"Você é um tutor de {materia}. "
            "Explique conceitos de forma clara e didática. "
            "Use exemplos práticos e verifique a compreensão do aluno."
        )
    
    def estudar_topico(self, topico):
        """Inicia estudo de um novo tópico"""
        print(f"\n=== Estudando: {topico} ===\n")
        resposta = self.chat.enviar_mensagem(
            f"Explique {topico} de forma didática"
        )
        print(f"Tutor: {resposta}\n")
        return resposta
    
    def perguntar(self, pergunta):
        """Faz pergunta sobre o tópico atual"""
        resposta = self.chat.enviar_mensagem(pergunta)
        print(f"Tutor: {resposta}\n")
        return resposta
    
    def revisar(self):
        """Pede revisão do que foi estudado"""
        resposta = self.chat.enviar_mensagem(
            "Faça um resumo do que estudamos até agora"
        )
        print(f"Tutor: {resposta}\n")
        return resposta
    
    def mudar_materia(self, nova_materia):
        """Muda de matéria (limpa contexto)"""
        print(f"\n🔄 Mudando para {nova_materia}...\n")
        self.chat.limpar_historico()
        self.materia = nova_materia
        self.chat.definir_system_prompt(
            f"Você é um tutor de {nova_materia}. "
            "Explique conceitos de forma clara e didática."
        )

# Uso
assistente = AssistenteEstudos("Python")

# Estudar tópico
assistente.estudar_topico("decorators em Python")

# Perguntas de acompanhamento (usa contexto)
assistente.perguntar("Pode dar um exemplo mais simples?")
assistente.perguntar("Quando devo usar decorators?")
assistente.perguntar("Qual a diferença para herança?")

# Revisar
assistente.revisar()

# Mudar de matéria (limpa contexto)
assistente.mudar_materia("JavaScript")
assistente.estudar_topico("Promises")
```

### Fluxo de Memória

```
Sessão de Python:
+------------------+
| Q: Decorators?   |
| A: São funções...| <-- Contexto base
| Q: Exemplo?      |
| A: [código]      | <-- Usa contexto
| Q: Quando usar?  |
| A: [casos]       | <-- Usa ambos
+------------------+
        |
        | mudar_materia("JavaScript")
        v
+------------------+
| (memória limpa)  |
+------------------+
        |
        v
Sessão de JavaScript:
+------------------+
| Q: Promises?     |
| A: São objetos...| <-- Novo contexto
+------------------+
```

### Benefícios

✅ Conversas naturais e fluidas  
✅ Progressão lógica do aprendizado  
✅ Revisões consideram toda a sessão  
✅ Economia ao trocar de matéria  

---

## 2. Revisor de Código

### Cenário

Desenvolvedor precisa revisar código, identificar problemas, sugerir melhorias e ver exemplos refatorados.

### Por que memória é importante?

- Código enviado uma vez serve para múltiplas análises
- Perguntas específicas referenciam o código já analisado
- Evolução incremental das sugestões

### Estratégia de Memória

```
+----------------------+
| Estratégia:          |
| - Manter durante     |
|   revisão completa   |
| - Limpar ao mudar    |
|   de arquivo         |
| - Exportar análise   |
| - Janela: 8-10 msgs  |
+----------------------+
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria

class RevisorCodigo:
    def __init__(self):
        self.chat = ChatComMemoria()
        self.chat.definir_system_prompt(
            "Você é um revisor de código Python sênior. "
            "Analise código criticamente identificando: "
            "bugs, problemas de performance, más práticas, "
            "e sugira melhorias seguindo PEP 8 e melhores práticas."
        )
        self.arquivo_atual = None
    
    def revisar_arquivo(self, caminho, codigo):
        """Inicia revisão de novo arquivo"""
        # Limpar contexto do arquivo anterior
        if self.arquivo_atual:
            print(f"💾 Salvando análise de {self.arquivo_atual}...")
            self.chat.exportar_conversa(
                f"revisao_{self.arquivo_atual.replace('.', '_')}.txt"
            )
            self.chat.limpar_historico()
        
        self.arquivo_atual = caminho
        print(f"\n=== Revisando: {caminho} ===\n")
        
        resposta = self.chat.enviar_mensagem(
            f"Analise este código de {caminho}:\n\n"
            f"```python\n{codigo}\n```"
        )
        print(f"Revisor: {resposta}\n")
        return resposta
    
    def perguntar_problemas(self):
        """Pede lista de problemas específicos"""
        resposta = self.chat.enviar_mensagem(
            "Liste os 3 principais problemas do código "
            "em ordem de prioridade"
        )
        print(f"Revisor: {resposta}\n")
        return resposta
    
    def pedir_refatoracao(self):
        """Solicita código refatorado"""
        resposta = self.chat.enviar_mensagem(
            "Mostre o código refatorado aplicando as melhorias sugeridas"
        )
        print(f"Revisor: {resposta}\n")
        return resposta
    
    def perguntar_performance(self):
        """Analisa performance especificamente"""
        resposta = self.chat.enviar_mensagem(
            "Analise a performance do código. "
            "Há gargalos ou otimizações possíveis?"
        )
        print(f"Revisor: {resposta}\n")
        return resposta

# Uso
revisor = RevisorCodigo()

# Código a revisar
codigo1 = '''
def processar_dados(dados):
    resultado = []
    for item in dados:
        if item > 0:
            resultado.append(item * 2)
    return resultado
'''

# Revisar arquivo
revisor.revisar_arquivo("processar.py", codigo1)

# Análises incrementais (todas referenciam o código enviado)
revisor.perguntar_problemas()
revisor.perguntar_performance()
revisor.pedir_refatoracao()

# Novo arquivo (salva análise anterior e limpa)
codigo2 = '''
class Usuario:
    def __init__(self, nome):
        self.nome = nome
'''

revisor.revisar_arquivo("usuario.py", codigo2)
```

### Fluxo de Memória

```
Arquivo 1:
+----------------------+
| Código: processar.py |
| Análise geral        |
| Problemas            |
| Performance          |
| Refatoração          |
+----------------------+
        |
        | Exporta + Limpa
        v
+----------------------+
| (salvo em arquivo)   |
+----------------------+
        |
        v
Arquivo 2:
+----------------------+
| Código: usuario.py   |
| Nova análise         |
+----------------------+
```

### Benefícios

✅ Não repete código a cada pergunta  
✅ Análises progressivas e detalhadas  
✅ Exportação automática das revisões  
✅ Isolamento entre arquivos  

---

## 3. Suporte Técnico

### Cenário

Sistema de atendimento onde agente precisa entender problema, coletar informações e resolver passo a passo.

### Por que memória é importante?

- Histórico completo do problema do cliente
- Evita repetir perguntas já respondidas
- Soluções consideram todo o contexto

### Estratégia de Memória

```
+----------------------+
| Estratégia:          |
| - Manter durante     |
|   atendimento        |
| - Limpar entre       |
|   clientes           |
| - Exportar ticket    |
| - Monitorar tokens   |
+----------------------+
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria
from datetime import datetime

class SistemaSuporteATM:
    def __init__(self):
        self.chat = ChatComMemoria()
        self.chat.definir_system_prompt(
            "Você é um agente de suporte técnico. "
            "Seja educado, empático e resolva problemas passo a passo. "
            "Colete informações necessárias antes de sugerir soluções."
        )
        self.ticket_id = None
        self.cliente = None
    
    def iniciar_atendimento(self, ticket_id, cliente):
        """Inicia novo atendimento"""
        # Finalizar atendimento anterior se houver
        if self.ticket_id:
            self.finalizar_atendimento()
        
        self.ticket_id = ticket_id
        self.cliente = cliente
        print(f"\n{'='*50}")
        print(f"Ticket #{ticket_id} | Cliente: {cliente}")
        print(f"Início: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}\n")
        
        # Saudação inicial
        saudacao = self.chat.enviar_mensagem(
            f"O cliente {cliente} abriu um ticket. "
            "Cumprimente e pergunte como pode ajudar."
        )
        print(f"Suporte: {saudacao}\n")
        return saudacao
    
    def processar_mensagem(self, mensagem_cliente):
        """Processa mensagem do cliente"""
        print(f"Cliente: {mensagem_cliente}")
        
        # Monitorar tokens
        tokens = self.chat.contar_tokens()
        if tokens > 1000:
            print("[Sistema: Conversa longa, considere resumir]")
        
        resposta = self.chat.enviar_mensagem(mensagem_cliente)
        print(f"Suporte: {resposta}\n")
        return resposta
    
    def finalizar_atendimento(self):
        """Finaliza atendimento e salva histórico"""
        if not self.ticket_id:
            return
        
        print(f"\n🎫 Finalizando Ticket #{self.ticket_id}...")
        
        # Exportar histórico
        nome_arquivo = f"ticket_{self.ticket_id}_{self.cliente}.txt"
        self.chat.exportar_conversa(nome_arquivo)
        print(f"✅ Histórico salvo: {nome_arquivo}")
        
        # Limpar para próximo atendimento
        self.chat.limpar_historico()
        self.ticket_id = None
        self.cliente = None
        print("🔄 Sistema pronto para próximo atendimento\n")

# Uso
suporte = SistemaSuporteATM()

# Atendimento 1
suporte.iniciar_atendimento("2024-001", "João Silva")
suporte.processar_mensagem("Não consigo fazer login no sistema")
suporte.processar_mensagem("Aparece 'credenciais inválidas'")
suporte.processar_mensagem("Já tentei recuperar senha")
suporte.processar_mensagem("Obrigado, funcionou!")
suporte.finalizar_atendimento()

# Atendimento 2 (contexto independente)
suporte.iniciar_atendimento("2024-002", "Maria Santos")
suporte.processar_mensagem("O relatório não está gerando")
```

### Fluxo de Memória

```
Ticket #001:
+------------------------+
| Cliente: João          |
| Problema: Login        |
| Info 1: Cred inválidas |
| Info 2: Senha já reset |
| Solução: [...]         |
+------------------------+
        |
        | Finalizar + Exportar
        v
+------------------------+
| ticket_001_joao.txt    |
+------------------------+
        |
        | Limpar contexto
        v
+------------------------+
| (memória vazia)        |
+------------------------+
        |
        v
Ticket #002:
+------------------------+
| Cliente: Maria         |
| Problema: Relatório    |
| [...]                  |
+------------------------+
```

### Benefícios

✅ Contexto completo do problema  
✅ Histórico salvo para auditoria  
✅ Isolamento entre atendimentos  
✅ Respostas contextualizadas  

---

## 4. Tutor Personalizado

### Cenário

Plataforma educacional com múltiplos tutores especializados, cada um com personalidade própria.

### Por que memória é importante?

- Cada tutor mantém histórico independente
- Personalização por matéria/estilo
- Contexto preservado dentro da sessão

### Estratégia de Memória

```
+----------------------+
| Estratégia:          |
| - Instância por tutor|
| - Memórias isoladas  |
| - Limpar por sessão  |
| - Janela: 10-12 msgs |
+----------------------+
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria

class PlataformaTutores:
    def __init__(self):
        self.tutores = {}
    
    def criar_tutor(self, nome, materia, estilo):
        """Cria novo tutor especializado"""
        chat = ChatComMemoria()
        
        # Personalizar prompt por estilo
        prompts = {
            "professor": (
                f"Você é um professor de {materia}. "
                "Seja formal, detalhado e use exemplos acadêmicos."
            ),
            "amigavel": (
                f"Você é um tutor amigável de {materia}. "
                "Use linguagem casual, analogias e incentive o aluno."
            ),
            "socrático": (
                f"Você é um tutor socrático de {materia}. "
                "Faça perguntas para guiar o aluno a descobrir as respostas."
            )
        }
        
        chat.definir_system_prompt(prompts[estilo])
        
        self.tutores[nome] = {
            'chat': chat,
            'materia': materia,
            'estilo': estilo
        }
        
        print(f"✅ Tutor '{nome}' criado ({materia} - {estilo})")
    
    def perguntar(self, tutor_nome, pergunta):
        """Faz pergunta para tutor específico"""
        if tutor_nome not in self.tutores:
            print(f"❌ Tutor '{tutor_nome}' não encontrado")
            return
        
        tutor = self.tutores[tutor_nome]
        print(f"\n[{tutor_nome} - {tutor['materia']}]")
        print(f"Você: {pergunta}")
        
        resposta = tutor['chat'].enviar_mensagem(pergunta)
        print(f"{tutor_nome}: {resposta}\n")
        return resposta
    
    def nova_sessao(self, tutor_nome):
        """Limpa histórico do tutor para nova sessão"""
        if tutor_nome in self.tutores:
            self.tutores[tutor_nome]['chat'].limpar_historico()
            print(f"🔄 Nova sessão iniciada com {tutor_nome}")

# Uso
plataforma = PlataformaTutores()

# Criar tutores diferentes
plataforma.criar_tutor("Prof. Silva", "Matemática", "professor")
plataforma.criar_tutor("Ana", "Python", "amigavel")
plataforma.criar_tutor("Sócrates", "Filosofia", "socrático")

# Perguntas simultâneas (contextos isolados)
plataforma.perguntar("Ana", "O que são listas em Python?")
plataforma.perguntar("Ana", "Como adiciono elementos?")  # Usa contexto

plataforma.perguntar("Prof. Silva", "O que são derivadas?")
plataforma.perguntar("Prof. Silva", "Dê um exemplo")  # Usa contexto

plataforma.perguntar("Sócrates", "O que é conhecimento?")
plataforma.perguntar("Sócrates", "Como saber se sei algo?")  # Usa contexto
```

### Diagrama de Instâncias

```
Plataforma:
+------------------+    +------------------+    +------------------+
| Tutor: Ana       |    | Tutor: Silva     |    | Tutor: Sócrates  |
| Matéria: Python  |    | Matéria: Mate    |    | Matéria: Filo    |
|------------------|    |------------------|    |------------------|
| Memória A:       |    | Memória B:       |    | Memória C:       |
| - Listas?        |    | - Derivadas?     |    | - Conhecimento?  |
| - Adicionar?     |    | - Exemplo        |    | - Como saber?    |
+------------------+    +------------------+    +------------------+
     ↕ Isoladas          ↕ Isoladas            ↕ Isoladas
```

### Benefícios

✅ Especialização por matéria  
✅ Personalidades diferentes  
✅ Contextos independentes  
✅ Escalável para muitos tutores  

---

## 5. Analisador de Documentos

### Cenário

Sistema que analisa documentos longos em múltiplas etapas: resumo, análise crítica, extração de informações.

### Por que memória é importante?

- Documento enviado uma vez
- Múltiplas análises sobre mesmo conteúdo
- Perguntas específicas referenciam o documento

### Estratégia de Memória

```
+----------------------+
| Estratégia:          |
| - Documento no início|
| - Limpar entre docs  |
| - Sliding window para|
|   docs muito longos  |
| - Exportar análise   |
+----------------------+
```

### Implementação

```python
from chat_openai_memoria import ChatComMemoria

class AnalisadorDocumentos:
    def __init__(self):
        self.chat = ChatComMemoria()
        self.chat.definir_system_prompt(
            "Você é um analista de documentos. "
            "Forneça análises precisas, objetivas e bem estruturadas."
        )
        self.documento_atual = None
    
    def carregar_documento(self, titulo, conteudo):
        """Carrega novo documento para análise"""
        # Salvar análise anterior
        if self.documento_atual:
            self.chat.exportar_conversa(
                f"analise_{self.documento_atual}.txt"
            )
            self.chat.limpar_historico()
        
        self.documento_atual = titulo
        print(f"\n📄 Analisando: {titulo}\n")
        
        # Enviar documento
        resposta = self.chat.enviar_mensagem(
            f"Analise este documento intitulado '{titulo}':\n\n"
            f"{conteudo}\n\n"
            "Confirme que recebeu e está pronto para análises."
        )
        print(f"Analista: {resposta}\n")
        return resposta
    
    def resumir(self):
        """Gera resumo executivo"""
        resposta = self.chat.enviar_mensagem(
            "Faça um resumo executivo do documento em 3-5 pontos principais"
        )
        print(f"Resumo:\n{resposta}\n")
        return resposta
    
    def extrair_informacoes(self, tipo):
        """Extrai informações específicas"""
        resposta = self.chat.enviar_mensagem(
            f"Extraia do documento: {tipo}"
        )
        print(f"{tipo}:\n{resposta}\n")
        return resposta
    
    def analise_critica(self):
        """Análise crítica do conteúdo"""
        resposta = self.chat.enviar_mensagem(
            "Faça uma análise crítica identificando: "
            "pontos fortes, pontos fracos e sugestões de melhoria"
        )
        print(f"Análise Crítica:\n{resposta}\n")
        return resposta

# Uso
analisador = AnalisadorDocumentos()

# Documento exemplo
documento = """
Projeto de Migração de Sistema

Objetivo: Migrar sistema legado para arquitetura moderna

Prazo: 6 meses
Orçamento: R$ 500.000
Equipe: 5 desenvolvedores

Riscos identificados:
- Perda de dados durante migração
- Resistência dos usuários
- Dependências de sistemas externos

Próximos passos:
1. Análise detalhada do sistema atual
2. Prototipação da nova arquitetura
3. Testes piloto
"""

# Análises incrementais
analisador.carregar_documento("Projeto_Migracao", documento)
analisador.resumir()
analisador.extrair_informacoes("riscos e ações mitigatórias")
analisador.extrair_informacoes("requisitos de recursos")
analisador.analise_critica()
```

### Fluxo de Memória

```
Documento 1:
+-------------------------+
| Texto completo enviado  |
| ↓                       |
| Resumo (referencia doc) |
| ↓                       |
| Extração (ref. doc)     |
| ↓                       |
| Crítica (ref. tudo)     |
+-------------------------+
        |
        | Exporta + Limpa
        v
Documento 2:
+-------------------------+
| Novo texto enviado      |
| ↓                       |
| [novas análises]        |
+-------------------------+
```

### Benefícios

✅ Documento enviado uma vez  
✅ Múltiplas perspectivas de análise  
✅ Análises referenciam o contexto  
✅ Histórico completo exportado  

---

## Comparação dos Casos de Uso

| Caso de Uso | Tamanho Contexto | Freq. Limpeza | Complexidade |
|-------------|------------------|---------------|--------------|
| **Assistente Estudos** | Médio-Alto | Por matéria | ⭐⭐ |
| **Revisor Código** | Médio | Por arquivo | ⭐⭐⭐ |
| **Suporte Técnico** | Variável | Por ticket | ⭐⭐ |
| **Tutor Personalizado** | Médio | Por sessão | ⭐⭐⭐ |
| **Analisador Docs** | Alto | Por documento | ⭐⭐ |

---

## Dicas de Implementação

### 1. Sempre exportar antes de limpar

```python
# ✅ Correto
chat.exportar_conversa("sessao.txt")
chat.limpar_historico()

# ❌ Errado (perde histórico)
chat.limpar_historico()
```

### 2. Monitorar tokens em produção

```python
if chat.contar_tokens() > LIMITE:
    logging.warning(f"Tokens alto: {chat.contar_tokens()}")
    # Tomar ação (limpar, janela, etc)
```

### 3. Isolar contextos com instâncias

```python
# ✅ Correto (contextos isolados)
chat_cliente1 = ChatComMemoria()
chat_cliente2 = ChatComMemoria()

# ❌ Errado (contextos misturados)
chat = ChatComMemoria()
# Cliente 1
# Cliente 2  <- Memória do cliente 1 ainda presente
```

### 4. Personalizar por caso de uso

```python
# System prompt específico para cada caso
chat.definir_system_prompt(
    "Prompt adaptado ao caso de uso específico..."
)
```

---

## Próximos Passos

- 🧠 Refine estratégias em [GERENCIAMENTO_MEMORIA.md](GERENCIAMENTO_MEMORIA.md)
- 🔧 Resolva problemas em [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 📚 Revise fundamentos em [CONCEITOS.md](CONCEITOS.md)
