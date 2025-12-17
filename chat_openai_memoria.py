"""
Chat com OpenAI API - Com Memória de Conversação

Este script demonstra como criar um chat interativo com a API da OpenAI
mantendo o histórico completo de conversas (memória).
"""

import os
from openai import OpenAI
from typing import List, Dict
from datetime import datetime
from dotenv import load_dotenv


class ChatComMemoria:
    """Classe para gerenciar chat com memória usando OpenAI API
       Todas as configurações são carregadas do arquivo .env"""

    def __init__(self):
        """
        Inicializa o chat com memória.

        Todas as configurações são carregadas do arquivo .env
        O sistema falhará se qualquer variável estiver faltando ou inválida.
        """
        # Carregar .env OBRIGATORIAMENTE
        load_dotenv()

        # Validar API Key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Crie o arquivo .env com: OPENAI_API_KEY=sua-chave-aqui"
            )

        # Validar Modelo
        self.modelo = os.getenv("OPENAI_MODEL")
        if not self.modelo:
            raise ValueError(
                "OPENAI_MODEL não configurada. "
                "Adicione no arquivo .env: OPENAI_MODEL=gpt-4o-mini"
            )

        # Validar Temperature
        temp_str = os.getenv("OPENAI_TEMPERATURE")
        if not temp_str:
            raise ValueError(
                "OPENAI_TEMPERATURE não configurada. "
                "Adicione no arquivo .env: OPENAI_TEMPERATURE=0.7"
            )
        try:
            self.temperature = float(temp_str)
            if not 0.0 <= self.temperature <= 2.0:
                raise ValueError(f"OPENAI_TEMPERATURE deve estar entre 0.0 e 2.0, recebido: {self.temperature}")
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(
                    f"OPENAI_TEMPERATURE inválida: '{temp_str}'. "
                    f"Use um número entre 0.0 e 2.0"
                ) from e
            raise

        # Validar Max Tokens
        tokens_str = os.getenv("OPENAI_MAX_TOKENS")
        if not tokens_str:
            raise ValueError(
                "OPENAI_MAX_TOKENS não configurada. "
                "Adicione no arquivo .env: OPENAI_MAX_TOKENS=1000"
            )
        try:
            self.max_tokens = int(tokens_str)
            if self.max_tokens <= 0:
                raise ValueError(f"OPENAI_MAX_TOKENS deve ser maior que 0, recebido: {self.max_tokens}")
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"OPENAI_MAX_TOKENS inválida: '{tokens_str}'. "
                    f"Use um número inteiro positivo"
                ) from e
            raise

        # Inicializar cliente
        self.client = OpenAI(api_key=self.api_key)
        self.historico = []
        self.system_prompt = "Você é um assistente útil e amigável."

        # Mensagem com configurações REAIS do .env
        print(f"Chat inicializado com modelo: {self.modelo}")
        print(f"Temperature: {self.temperature}")
        print(f"Max Tokens: {self.max_tokens}")
        print(f"Memoria ativa: histórico será mantido durante a sessão\n")
    
    def definir_personalidade(self, prompt: str):
        """
        Define a personalidade do assistente através do system prompt.
        
        Args:
            prompt: Instrução de sistema para definir comportamento do assistente
        """
        self.system_prompt = prompt
        print(f"Personalidade definida: {prompt[:50]}...\n")
    
    def adicionar_mensagem(self, role: str, content: str):
        """
        Adiciona mensagem ao histórico.
        
        Args:
            role: 'user' ou 'assistant'
            content: Conteúdo da mensagem
        """
        self.historico.append({
            "role": role,
            "content": content
        })
    
    def enviar_mensagem(self, mensagem: str) -> str:
        """
        Envia mensagem para a API mantendo o contexto completo.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            Resposta do assistente
        """
        # Adiciona mensagem do usuário ao histórico
        self.adicionar_mensagem("user", mensagem)
        
        # Prepara mensagens com system prompt + histórico completo
        mensagens = [
            {"role": "system", "content": self.system_prompt}
        ] + self.historico
        
        try:
            # Chama a API
            resposta = self.client.chat.completions.create(
                model=self.modelo,
                messages=mensagens,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Extrai resposta
            resposta_texto = resposta.choices[0].message.content
            
            # Adiciona resposta ao histórico
            self.adicionar_mensagem("assistant", resposta_texto)
            
            return resposta_texto
            
        except Exception as e:
            raise Exception(f"Erro ao chamar API OpenAI: {e}")
    
    def limpar_memoria(self):
        """Limpa todo o histórico de conversação"""
        self.historico = []
        print("Memória limpa - histórico apagado\n")
    
    def mostrar_historico(self):
        """Exibe todo o histórico de conversação"""
        print("\n" + "="*60)
        print("HISTÓRICO DA CONVERSAÇÃO")
        print("="*60)
        
        for i, msg in enumerate(self.historico, 1):
            role = "VOCÊ" if msg["role"] == "user" else "ASSISTENTE"
            print(f"\n[{i}] {role}:")
            print(f"{msg['content']}")
        
        print("\n" + "="*60 + "\n")
    
    def contar_tokens_aproximado(self) -> int:
        """
        Conta aproximadamente quantos tokens estão no histórico.
        Estimativa simples: ~4 caracteres por token
        """
        total_chars = sum(len(msg["content"]) for msg in self.historico)
        return total_chars // 4
    
    def exportar_conversa(self, arquivo: str = None):
        """
        Exporta a conversa para um arquivo de texto.
        
        Args:
            arquivo: Nome do arquivo (se None, usa timestamp)
        """
        if not arquivo:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = f"conversa_{timestamp}.txt"
        
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(f"Conversa exportada em: {datetime.now()}\n")
            f.write(f"Modelo: {self.modelo}\n")
            f.write("="*60 + "\n\n")
            
            for msg in self.historico:
                role = "VOCÊ" if msg["role"] == "user" else "ASSISTENTE"
                f.write(f"{role}:\n{msg['content']}\n\n")
        
        print(f"Conversa exportada para: {arquivo}\n")


def chat_interativo():
    """Função principal para chat interativo no terminal"""
    
    print("="*60)
    print("CHAT COM OPENAI - COM MEMÓRIA")
    print("="*60)
    print("\nComandos especiais:")
    print("  /limpar    - Limpa a memória do chat")
    print("  /historico - Mostra todo o histórico")
    print("  /tokens    - Mostra quantidade aproximada de tokens")
    print("  /exportar  - Exporta a conversa para arquivo")
    print("  /sair      - Encerra o chat")
    print("="*60 + "\n")
    
    try:
        # Inicializa o chat
        chat = ChatComMemoria()
        
        # Opcional: definir personalidade customizada
        # chat.definir_personalidade("Você é um especialista em Python que responde de forma concisa.")
        
        while True:
            # Recebe mensagem do usuário
            mensagem = input("Você: ").strip()
            
            if not mensagem:
                continue
            
            # Processa comandos especiais
            if mensagem.lower() == "/sair":
                print("\nEncerrando chat. Até logo")
                break
            
            elif mensagem.lower() == "/limpar":
                chat.limpar_memoria()
                continue
            
            elif mensagem.lower() == "/historico":
                chat.mostrar_historico()
                continue
            
            elif mensagem.lower() == "/tokens":
                tokens = chat.contar_tokens_aproximado()
                print(f"\nTokens aproximados no histórico: {tokens}\n")
                continue
            
            elif mensagem.lower() == "/exportar":
                chat.exportar_conversa()
                continue
            
            # Envia mensagem e recebe resposta
            try:
                print("\nAssistente: ", end="", flush=True)
                resposta = chat.enviar_mensagem(mensagem)
                print(resposta + "\n")
                
            except Exception as e:
                print(f"\nErro: {e}\n")
                break
    
    except ValueError as e:
        print(f"\nErro de configuração: {e}")
        print("Configure a variável de ambiente OPENAI_API_KEY com sua chave da API.\n")
    
    except KeyboardInterrupt:
        print("\n\nChat interrompido pelo usuário. Até logo")
    
    except Exception as e:
        print(f"\nErro inesperado: {e}")


def exemplo_programatico():
    """Exemplo de uso programático (não interativo)"""
    
    print("\n" + "="*60)
    print("EXEMPLO DE USO PROGRAMÁTICO")
    print("="*60 + "\n")
    
    # Inicializa o chat
    chat = ChatComMemoria()
    
    # Define personalidade
    chat.definir_personalidade(
        "Você é um professor de Python que explica conceitos de forma simples e objetiva."
    )
    
    # Sequência de perguntas relacionadas (memória será mantida)
    perguntas = [
        "O que é uma lista em Python?",
        "E como eu adiciono elementos nela?",  # Contexto da pergunta anterior
        "Pode me dar um exemplo prático?"       # Mantém contexto
    ]
    
    for pergunta in perguntas:
        print(f"VOCÊ: {pergunta}")
        resposta = chat.enviar_mensagem(pergunta)
        print(f"ASSISTENTE: {resposta}\n")
        print("-"*60 + "\n")
    
    # Mostra estatísticas
    print(f"Total de mensagens no histórico: {len(chat.historico)}")
    print(f"Tokens aproximados: {chat.contar_tokens_aproximado()}")
    
    # Exporta conversa
    chat.exportar_conversa("exemplo_conversa.txt")


if __name__ == "__main__":
    import sys
    
    # Se receber argumento --exemplo, roda exemplo programático
    if len(sys.argv) > 1 and sys.argv[1] == "--exemplo":
        exemplo_programatico()
    else:
        # Senão, inicia chat interativo
        chat_interativo()

