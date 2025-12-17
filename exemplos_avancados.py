"""
Exemplos Avançados - Chat OpenAI com Memória

Demonstra casos de uso mais complexos e técnicas avançadas.

IMPORTANTE: Todas as configurações são carregadas do arquivo .env
O sistema falhará se qualquer variável obrigatória estiver faltando.
"""

from chat_openai_memoria import ChatComMemoria
import time


def exemplo_multiplas_personalidades():
    """Demonstra como usar diferentes personalidades em chats separados"""
    
    print("\n" + "="*60)
    print("EXEMPLO: MÚLTIPLAS PERSONALIDADES")
    print("="*60 + "\n")
    
    # Chat 1: Professor de Python
    professor = ChatComMemoria()
    professor.definir_personalidade(
        "Você é um professor de Python experiente. "
        "Responda de forma didática e use exemplos práticos."
    )
    
    # Chat 2: Code Reviewer
    reviewer = ChatComMemoria()
    reviewer.definir_personalidade(
        "Você é um code reviewer experiente. "
        "Analise código criticamente e sugira melhorias."
    )
    
    # Pergunta ao professor
    print("PERGUNTANDO AO PROFESSOR:")
    codigo_exemplo = """
def calcular(a, b):
    return a + b
"""
    pergunta = f"Como posso melhorar esta função?\n{codigo_exemplo}"
    resposta_prof = professor.enviar_mensagem(pergunta)
    print(f"Professor: {resposta_prof}\n")
    
    # Mesma pergunta ao reviewer
    print("-"*60)
    print("\nPERGUNTANDO AO REVIEWER:")
    resposta_review = reviewer.enviar_mensagem(pergunta)
    print(f"Reviewer: {resposta_review}\n")
    
    print("="*60)
    print("Nota: Respostas diferentes devido a personalidades distintas")
    print("="*60 + "\n")


def exemplo_controle_contexto():
    """Demonstra controle de contexto e limpeza estratégica de memória"""
    
    print("\n" + "="*60)
    print("EXEMPLO: CONTROLE DE CONTEXTO")
    print("="*60 + "\n")
    
    chat = ChatComMemoria()
    
    # Primeira conversa sobre Python
    print("TÓPICO 1: Python")
    chat.enviar_mensagem("Vamos falar sobre Python. O que são decorators?")
    chat.enviar_mensagem("Pode dar um exemplo de decorator?")
    
    print(f"Mensagens no histórico: {len(chat.historico)}")
    print(f"Tokens aproximados: {chat.contar_tokens_aproximado()}\n")
    
    # Muda de tópico - limpa contexto
    print("-"*60)
    print("\nMudando de tópico - limpando contexto anterior\n")
    chat.limpar_memoria()
    
    # Segunda conversa sobre JavaScript
    print("TÓPICO 2: JavaScript")
    resposta = chat.enviar_mensagem("Vamos falar sobre JavaScript. O que são Promises?")
    print(f"Resposta: {resposta[:100]}...\n")
    
    print(f"Mensagens no histórico: {len(chat.historico)}")
    print(f"Tokens aproximados: {chat.contar_tokens_aproximado()}\n")
    
    print("="*60)
    print("Nota: Limpar memória ajuda a reduzir custos e manter foco")
    print("="*60 + "\n")


def exemplo_conversa_longa():
    """Demonstra como gerenciar conversas longas com controle de tokens"""
    
    print("\n" + "="*60)
    print("EXEMPLO: GERENCIAMENTO DE CONVERSA LONGA")
    print("="*60 + "\n")
    
    chat = ChatComMemoria()
    
    # Simula várias perguntas
    perguntas = [
        "O que é Python?",
        "Quais são os tipos de dados básicos?",
        "Como funcionam as listas?",
        "E os dicionários?",
        "O que são funções?",
        "Como usar classes?",
        "O que são módulos?",
        "Como fazer tratamento de erros?"
    ]
    
    MAX_TOKENS = 500  # Limite arbitrário para exemplo
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n[{i}] Você: {pergunta}")
        
        # Verifica tokens antes de enviar
        tokens_atuais = chat.contar_tokens_aproximado()
        print(f"Tokens no histórico: {tokens_atuais}")
        
        if tokens_atuais > MAX_TOKENS:
            print("ATENÇÃO: Limite de tokens atingido - limpando histórico antigo")
            
            # Estratégia: mantém apenas as últimas 2 mensagens
            if len(chat.historico) > 4:
                historico_recente = chat.historico[-4:]
                chat.historico = historico_recente
                print(f"Histórico reduzido para {len(chat.historico)} mensagens")
        
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Assistente: {resposta[:100]}...")
    
    print("\n" + "="*60)
    print(f"Total de mensagens processadas: {i}")
    print(f"Mensagens mantidas em memória: {len(chat.historico)}")
    print("="*60 + "\n")


def exemplo_tratamento_erros():
    """Demonstra tratamento de erros comuns"""
    
    print("\n" + "="*60)
    print("EXEMPLO: TRATAMENTO DE ERROS")
    print("="*60 + "\n")
    
    # Erro 1: API Key inválida
    print("1. Testando com API Key inválida:")
    print("Nota: Agora todas as configurações vêm do .env")
    print("Para testar erro de API Key, modifique OPENAI_API_KEY no .env\n")
    
    # Erro 2: API Key não configurada
    print("2. Testando sem API Key:")
    print("Nota: Agora o sistema falha imediatamente se OPENAI_API_KEY não estiver no .env")
    print("Para testar, remova ou comente OPENAI_API_KEY no .env\n")
    
    # Erro 3: Modelo inválido
    print("3. Testando com modelo inválido:")
    print("Nota: Agora o modelo vem do .env (OPENAI_MODEL)")
    print("Para testar erro de modelo, configure um modelo inválido no .env\n")
    
    print("="*60)
    print("Nota: Sempre implemente try/except ao trabalhar com APIs")
    print("="*60 + "\n")


def exemplo_analise_codigo():
    """Exemplo prático: análise de código com contexto"""
    
    print("\n" + "="*60)
    print("EXEMPLO PRÁTICO: ANÁLISE DE CÓDIGO")
    print("="*60 + "\n")
    
    chat = ChatComMemoria()
    chat.definir_personalidade(
        "Você é um especialista em Python. "
        "Analise código e sugira melhorias de forma objetiva."
    )
    
    # Envia código para análise
    codigo = """
def processar_dados(dados):
    resultado = []
    for i in range(len(dados)):
        if dados[i] > 0:
            resultado.append(dados[i] * 2)
    return resultado

numeros = [1, -2, 3, -4, 5]
print(processar_dados(numeros))
"""
    
    print("CÓDIGO ORIGINAL:")
    print(codigo)
    print("-"*60)
    
    # Pergunta 1: Análise geral
    print("\n1. Análise geral:")
    resposta1 = chat.enviar_mensagem(f"Analise este código:\n{codigo}")
    print(resposta1[:200] + "...\n")
    
    # Pergunta 2: Aproveita contexto
    print("-"*60)
    print("\n2. Pergunta de acompanhamento (usa contexto):")
    resposta2 = chat.enviar_mensagem("Como posso torná-lo mais pythonico?")
    print(resposta2[:200] + "...\n")
    
    # Pergunta 3: Continua no mesmo contexto
    print("-"*60)
    print("\n3. Outra pergunta de acompanhamento:")
    resposta3 = chat.enviar_mensagem("E quanto a performance?")
    print(resposta3[:200] + "...\n")
    
    print("="*60)
    print("Nota: Cada pergunta mantém o contexto das anteriores")
    print("="*60 + "\n")


def menu_exemplos():
    """Menu interativo para escolher exemplos"""
    
    exemplos = {
        "1": ("Múltiplas Personalidades", exemplo_multiplas_personalidades),
        "2": ("Controle de Contexto", exemplo_controle_contexto),
        "3": ("Conversa Longa", exemplo_conversa_longa),
        "4": ("Tratamento de Erros", exemplo_tratamento_erros),
        "5": ("Análise de Código", exemplo_analise_codigo),
        "6": ("Executar Todos", lambda: None)
    }
    
    print("\n" + "="*60)
    print("EXEMPLOS AVANÇADOS - CHAT OPENAI")
    print("="*60)
    
    for key, (nome, _) in exemplos.items():
        print(f"{key}. {nome}")
    
    print("0. Sair")
    print("="*60)
    
    while True:
        escolha = input("\nEscolha um exemplo: ").strip()
        
        if escolha == "0":
            print("Encerrando...")
            break
        
        if escolha == "6":
            print("\nExecutando todos os exemplos...\n")
            for key in ["1", "2", "3", "4", "5"]:
                exemplos[key][1]()
                time.sleep(2)
            print("\nTodos os exemplos executados")
            break
        
        if escolha in exemplos and escolha != "6":
            try:
                exemplos[escolha][1]()
                input("\nPressione Enter para continuar...")
            except Exception as e:
                print(f"\nErro ao executar exemplo: {e}")
        else:
            print("Opção inválida")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Executa exemplo específico via argumento
        exemplo_map = {
            "--personalidades": exemplo_multiplas_personalidades,
            "--contexto": exemplo_controle_contexto,
            "--longa": exemplo_conversa_longa,
            "--erros": exemplo_tratamento_erros,
            "--analise": exemplo_analise_codigo,
            "--todos": lambda: [
                exemplo_multiplas_personalidades(),
                exemplo_controle_contexto(),
                exemplo_conversa_longa(),
                exemplo_tratamento_erros(),
                exemplo_analise_codigo()
            ]
        }
        
        arg = sys.argv[1]
        if arg in exemplo_map:
            exemplo_map[arg]()
        else:
            print(f"Argumento inválido: {arg}")
            print("Argumentos disponíveis:", ", ".join(exemplo_map.keys()))
    else:
        # Modo interativo
        menu_exemplos()

