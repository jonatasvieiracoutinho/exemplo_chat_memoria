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
    chat.limpar_historico()
    
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


def exemplo_janela_deslizante():
    """Demonstra o funcionamento do sliding window automático"""
    
    print("\n" + "="*60)
    print("EXEMPLO: SLIDING WINDOW (JANELA DESLIZANTE)")
    print("="*60 + "\n")
    
    # Cria chat com janela pequena para demonstração
    chat = ChatComMemoria(tamanho_janela=3)  # Mantém apenas 3 pares (6 mensagens)
    
    print("Configuração: Janela de 3 pares (máximo 6 mensagens)\n")
    print("-"*60 + "\n")
    
    # Envia várias mensagens para demonstrar a janela
    perguntas = [
        "Qual é a capital da França?",
        "E da Alemanha?",
        "E da Itália?",
        "E da Espanha?",
        "E de Portugal?",
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"[Mensagem {i}] {pergunta}")
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Resposta: {resposta[:80]}...")
        print(f"Total no histórico: {len(chat.historico)} mensagens\n")
    
    print("-"*60)
    print("\nOBSERVAÇÕES:")
    print("• Após a 4ª pergunta, o histórico para de crescer")
    print("• As mensagens mais antigas são automaticamente removidas")
    print("• Apenas as últimas 3 pares (6 mensagens) são mantidas")
    print("• Isso reduz custos e mantém o contexto recente\n")
    
    chat.debug_memoria()


def exemplo_monitoramento_automatico():
    """Demonstra o sistema de monitoramento de tokens"""
    
    print("\n" + "="*60)
    print("EXEMPLO: MONITORAMENTO AUTOMÁTICO DE TOKENS")
    print("="*60 + "\n")
    
    # Cria chat com limite baixo para demonstração
    chat = ChatComMemoria(limite_maximo=300)
    
    print("Configuração: Limite de 300 tokens\n")
    print("Níveis de alerta:")
    print("  🟢 Verde: 0-100 tokens (0-33%)")
    print("  🟡 Amarelo: 100-200 tokens (33-66%)")
    print("  🟠 Laranja: 200-300 tokens (66-99%)")
    print("  🔴 Vermelho: ≥300 tokens (≥100% - CRÍTICO)\n")
    print("-"*60 + "\n")
    
    # Envia mensagens gradualmente
    perguntas = [
        "Me explique o que é Python em poucas palavras.",
        "Quais são os principais tipos de dados em Python?",
        "Como funcionam as listas em Python?",
        "Explique o conceito de dicionários em Python.",
        "O que são funções em Python e como criá-las?",
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n[Pergunta {i}] {pergunta}")
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Resposta recebida: {len(resposta)} caracteres")
        
        # O alerta será exibido automaticamente por enviar_mensagem()
    
    print("\n" + "-"*60)
    print("\nStatus final:")
    chat.debug_memoria()
    
    print("OBSERVAÇÕES:")
    print("• Os alertas aparecem automaticamente conforme tokens aumentam")
    print("• No nível vermelho, o sistema recomenda ação (limpar ou ajustar janela)")
    print("• Combine com sliding window para gerenciamento automático\n")


def exemplo_sistema_completo():
    """Demonstra uso de sliding window + monitoramento juntos"""
    
    print("\n" + "="*60)
    print("EXEMPLO: SISTEMA COMPLETO (SLIDING WINDOW + MONITORAMENTO)")
    print("="*60 + "\n")
    
    # Cria chat com ambas funcionalidades
    chat = ChatComMemoria(tamanho_janela=4, limite_maximo=400)
    
    print("Configuração otimizada:")
    print("  • Sliding Window: 4 pares (8 mensagens)")
    print("  • Monitoramento: 400 tokens")
    print("\nEsta é a configuração recomendada para uso geral!\n")
    print("-"*60 + "\n")
    
    # Simula conversa longa
    perguntas = [
        "O que é aprendizado de máquina?",
        "Quais são os tipos principais?",
        "Explique aprendizado supervisionado",
        "E o não supervisionado?",
        "O que é deep learning?",
        "Como funciona uma rede neural?",
    ]
    
    for i, pergunta in enumerate(perguntas, 1):
        print(f"\n{'='*60}")
        print(f"INTERAÇÃO {i}")
        print('='*60)
        print(f"Você: {pergunta}\n")
        
        resposta = chat.enviar_mensagem(pergunta)
        print(f"Assistente: {resposta[:150]}...\n")
    
    print("\n" + "="*60)
    print("RESULTADO FINAL:")
    print("="*60 + "\n")
    
    chat.debug_memoria()
    chat.grafico_tokens()
    
    print("BENEFÍCIOS DO SISTEMA COMPLETO:")
    print("  ✓ Sliding window mantém memória controlada")
    print("  ✓ Monitoramento alerta sobre uso de tokens")
    print("  ✓ Custos previsíveis e controlados")
    print("  ✓ Contexto relevante sempre disponível")
    print("  ✓ Sem necessidade de intervenção manual\n")


def exemplo_modo_debug():
    """Demonstra o modo debug com logging detalhado"""
    
    print("\n" + "="*60)
    print("EXEMPLO: MODO DEBUG COM LOGGING")
    print("="*60 + "\n")
    
    # Cria chat com modo debug ativo
    chat = ChatComMemoria(
        tamanho_janela=3,
        limite_maximo=300,
        modo_debug=True
    )
    
    print("Modo Debug ATIVO")
    print(f"Arquivo de log: {chat.arquivo_log}\n")
    print("-"*60 + "\n")
    
    # Envia algumas mensagens
    print("Enviando mensagens para gerar log...\n")
    
    chat.enviar_mensagem("Olá! Como você está?")
    chat.enviar_mensagem("Me explique o que é uma lista em Python")
    chat.enviar_mensagem("E um dicionário?")
    
    print("\n" + "-"*60)
    print("\nConversação concluída!")
    print(f"\nVerifique o arquivo de log para ver detalhes completos:")
    print(f"  📄 {chat.arquivo_log}\n")
    
    chat.debug_memoria()
    
    print("O QUE O LOG CONTÉM:")
    print("  • Timestamp de cada interação")
    print("  • Mensagem do usuário")
    print("  • System prompt utilizado")
    print("  • Parâmetros do modelo (temperature, max_tokens, etc)")
    print("  • Histórico completo antes da nova mensagem")
    print("  • Resposta do assistente")
    print("  • Status de memória (tokens, janela, alertas)")
    print("  • Ações executadas (sliding window, limpeza, etc)")
    print("\nÚTIL PARA:")
    print("  • Debugging de problemas")
    print("  • Auditoria de conversas")
    print("  • Aprendizado sobre gerenciamento de memória")
    print("  • Análise de custos e uso de tokens\n")


def exemplo_base_url_customizada():
    """Demonstra uso de URL customizada para provedores alternativos"""
    
    print("\n" + "="*60)
    print("EXEMPLO: URL CUSTOMIZADA (PROVEDORES ALTERNATIVOS)")
    print("="*60 + "\n")
    
    print("Este exemplo demonstra como configurar URLs customizadas")
    print("para usar provedores compatíveis com o padrão OpenAI.\n")
    
    print("CASOS DE USO COMUNS:\n")
    
    print("1. Azure OpenAI Service")
    print("   .env:")
    print("   OPENAI_BASE_URL=https://seu-recurso.openai.azure.com")
    print("   OPENAI_API_KEY=sua-chave-azure")
    print("   OPENAI_MODEL=gpt-4o-mini\n")
    
    print("2. Ollama (modelos locais)")
    print("   .env:")
    print("   OPENAI_BASE_URL=http://localhost:11434/v1")
    print("   OPENAI_API_KEY=ollama")
    print("   OPENAI_MODEL=llama2\n")
    
    print("3. LM Studio (desenvolvimento local)")
    print("   .env:")
    print("   OPENAI_BASE_URL=http://localhost:1234/v1")
    print("   OPENAI_API_KEY=lm-studio")
    print("   OPENAI_MODEL=local-model\n")
    
    print("-"*60)
    print("\nCOMO FUNCIONA:")
    print("- Se OPENAI_BASE_URL não estiver configurada → OpenAI padrão")
    print("- Se OPENAI_BASE_URL estiver configurada → Provedor customizado")
    print("- A URL deve começar com http:// ou https://")
    print("- A maioria dos provedores requer /v1 no final da URL\n")
    
    print("-"*60)
    print("\nVANTAGENS:")
    print("✓ Testar modelos locais sem custo")
    print("✓ Usar Azure OpenAI em ambientes corporativos")
    print("✓ Compatibilidade com múltiplos provedores")
    print("✓ Mesma interface de código para diferentes backends\n")
    
    print("-"*60)
    print("\nPASSOS PARA USAR:")
    print("1. Configure o provedor desejado (Ollama, LM Studio, etc)")
    print("2. Adicione OPENAI_BASE_URL no arquivo .env")
    print("3. Ajuste OPENAI_MODEL para o modelo disponível")
    print("4. Execute normalmente - o código se adapta automaticamente\n")
    
    print("="*60)
    print("Nota: Este exemplo é informativo. Para usar,")
    print("configure as variáveis no .env e execute o chat normalmente.")
    print("="*60 + "\n")


def menu_exemplos():
    """Menu interativo para escolher exemplos"""
    
    exemplos = {
        "1": ("Múltiplas Personalidades", exemplo_multiplas_personalidades),
        "2": ("Controle de Contexto", exemplo_controle_contexto),
        "3": ("Conversa Longa", exemplo_conversa_longa),
        "4": ("Tratamento de Erros", exemplo_tratamento_erros),
        "5": ("Análise de Código", exemplo_analise_codigo),
        "6": ("Sliding Window", exemplo_janela_deslizante),
        "7": ("Monitoramento Automático", exemplo_monitoramento_automatico),
        "8": ("Sistema Completo", exemplo_sistema_completo),
        "9": ("Modo Debug", exemplo_modo_debug),
        "10": ("URL Customizada", exemplo_base_url_customizada),
        "11": ("Executar Todos", lambda: None)
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
        
        if escolha == "11":
            print("\nExecutando todos os exemplos...\n")
            for key in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
                exemplos[key][1]()
                time.sleep(2)
            print("\nTodos os exemplos executados!")
            break
        
        if escolha in exemplos and escolha != "11":
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
            "--janela": exemplo_janela_deslizante,
            "--monitoramento": exemplo_monitoramento_automatico,
            "--completo": exemplo_sistema_completo,
            "--debug": exemplo_modo_debug,
            "--baseurl": exemplo_base_url_customizada,
            "--todos": lambda: [
                exemplo_multiplas_personalidades(),
                exemplo_controle_contexto(),
                exemplo_conversa_longa(),
                exemplo_tratamento_erros(),
                exemplo_analise_codigo(),
                exemplo_janela_deslizante(),
                exemplo_monitoramento_automatico(),
                exemplo_sistema_completo(),
                exemplo_modo_debug(),
                exemplo_base_url_customizada()
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

