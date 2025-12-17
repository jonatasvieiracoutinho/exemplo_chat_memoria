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

    def __init__(self, tamanho_janela: int = None, limite_maximo: int = None, modo_debug: bool = None):
        """
        Inicializa o chat com memória.

        Todas as configurações básicas são carregadas do arquivo .env
        O sistema falhará se qualquer variável obrigatória estiver faltando ou inválida.
        
        Args:
            tamanho_janela: Número máximo de pares de mensagens (user+assistant) a manter.
                          Se None, carrega de JANELA_MAX no .env. Se ainda None, desabilita sliding window.
            limite_maximo: Limite de tokens para alerta crítico e sugestão de limpeza.
                          Se None, carrega de LIMITE_MAXIMO no .env. Se ainda None, desabilita monitoramento.
            modo_debug: Se True, gera logs detalhados em logs/chat_debug_TIMESTAMP.log.
                       Se None, carrega de MODO_DEBUG no .env. Padrão: False.
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

        # Configurações opcionais de gerenciamento de memória
        # Prioridade: parâmetro do construtor > .env > None (desabilitado)
        
        # Sliding Window
        if tamanho_janela is None:
            janela_env = os.getenv("JANELA_MAX")
            self.tamanho_janela = int(janela_env) if janela_env else None
        else:
            self.tamanho_janela = tamanho_janela
        
        # Monitoramento de tokens
        if limite_maximo is None:
            limite_env = os.getenv("LIMITE_MAXIMO")
            self.limite_maximo = int(limite_env) if limite_env else None
        else:
            self.limite_maximo = limite_maximo
        
        # Modo debug
        if modo_debug is None:
            debug_env = os.getenv("MODO_DEBUG", "false").lower()
            self.modo_debug = debug_env == "true"
        else:
            self.modo_debug = modo_debug
        
        # Inicializar cliente
        self.client = OpenAI(api_key=self.api_key)
        self.historico = []
        self.system_prompt = "Você é um assistente útil e amigável."
        
        # Controle de logging
        self.arquivo_log = None
        self.contador_interacoes = 0
        
        # Inicializar arquivo de log se modo debug ativo
        if self.modo_debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.arquivo_log = f"logs/chat_debug_{timestamp}.log"
            self._inicializar_log()

        # Mensagem com configurações REAIS do .env
        print(f"Chat inicializado com modelo: {self.modelo}")
        print(f"Temperature: {self.temperature}")
        print(f"Max Tokens: {self.max_tokens}")
        print(f"Memoria ativa: histórico será mantido durante a sessão")
        
        # Informar configurações de gerenciamento
        if self.tamanho_janela:
            print(f"Sliding Window: {self.tamanho_janela} pares de mensagens")
        if self.limite_maximo:
            print(f"Monitoramento: limite de {self.limite_maximo} tokens")
        if self.modo_debug:
            print(f"Modo Debug: logs em {self.arquivo_log}")
        print()
    
    def definir_personalidade(self, prompt: str):
        """
        Define a personalidade do assistente através do system prompt.
        
        Args:
            prompt: Instrução de sistema para definir comportamento do assistente
        """
        self.system_prompt = prompt
        print(f"Personalidade definida: {prompt[:50]}...\n")
        
        if self.modo_debug:
            self._registrar_log(f"\n{'─'*70}\n[SYSTEM PROMPT ATUALIZADO]\n{'─'*70}\n{prompt}\n")
    
    def _inicializar_log(self):
        """Inicializa o arquivo de log com cabeçalho visual"""
        with open(self.arquivo_log, "w", encoding="utf-8") as f:
            f.write("╔" + "═"*68 + "╗\n")
            f.write("║" + " "*20 + "CHAT DEBUG LOG" + " "*34 + "║\n")
            f.write("║" + " "*15 + "Chat OpenAI com Memória" + " "*30 + "║\n")
            f.write("╚" + "═"*68 + "╝\n\n")
            f.write(f"Sessão iniciada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"{'═'*70}\n\n")
            f.write("CONFIGURAÇÕES DA SESSÃO:\n")
            f.write(f"  • Modelo: {self.modelo}\n")
            f.write(f"  • Temperature: {self.temperature}\n")
            f.write(f"  • Max Tokens: {self.max_tokens}\n")
            f.write(f"  • System Prompt: {self.system_prompt}\n")
            
            if self.tamanho_janela:
                f.write(f"  • Sliding Window: {self.tamanho_janela} pares de mensagens\n")
            else:
                f.write(f"  • Sliding Window: Desabilitado\n")
            
            if self.limite_maximo:
                f.write(f"  • Monitoramento: {self.limite_maximo} tokens (máximo)\n")
                f.write(f"    - 🟢 Verde: 0-{self.limite_maximo//3} tokens (0-33%)\n")
                f.write(f"    - 🟡 Amarelo: {self.limite_maximo//3}-{(self.limite_maximo*2)//3} tokens (33-66%)\n")
                f.write(f"    - 🟠 Laranja: {(self.limite_maximo*2)//3}-{self.limite_maximo} tokens (66-99%)\n")
                f.write(f"    - 🔴 Vermelho: ≥{self.limite_maximo} tokens (≥100% - CRÍTICO)\n")
            else:
                f.write(f"  • Monitoramento: Desabilitado\n")
            
            f.write(f"\n{'═'*70}\n\n")
    
    def _registrar_log(self, mensagem: str):
        """Registra mensagem no arquivo de log se modo debug ativo"""
        if self.modo_debug and self.arquivo_log:
            with open(self.arquivo_log, "a", encoding="utf-8") as f:
                f.write(mensagem)
    
    def _registrar_interacao(self, mensagem_usuario: str, resposta_assistente: str, tokens_antes: int, tokens_depois: int, acoes: list = None):
        """
        Registra uma interação completa no log de debug.
        
        Args:
            mensagem_usuario: Mensagem enviada pelo usuário
            resposta_assistente: Resposta gerada pelo assistente
            tokens_antes: Contagem de tokens antes da interação
            tokens_depois: Contagem de tokens depois da interação
            acoes: Lista de ações executadas (ex: ["Sliding window aplicado", "Alerta laranja"])
        """
        if not self.modo_debug:
            return
        
        self.contador_interacoes += 1
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        log = f"\n{'╔' + '═'*68 + '╗'}\n"
        log += f"║  INTERAÇÃO #{self.contador_interacoes:<55} ║\n"
        log += f"║  {timestamp:<66} ║\n"
        log += f"{'╚' + '═'*68 + '╝'}\n\n"
        
        # Mensagem do usuário
        log += f"{'─'*70}\n"
        log += f"[MENSAGEM DO USUÁRIO]\n"
        log += f"{'─'*70}\n"
        log += f"{mensagem_usuario}\n\n"
        
        # System prompt atual
        log += f"{'─'*70}\n"
        log += f"[SYSTEM PROMPT]\n"
        log += f"{'─'*70}\n"
        log += f"{self.system_prompt}\n\n"
        
        # Parâmetros do modelo
        log += f"{'─'*70}\n"
        log += f"[PARÂMETROS DO MODELO]\n"
        log += f"{'─'*70}\n"
        log += f"  Modelo: {self.modelo}\n"
        log += f"  Temperature: {self.temperature}\n"
        log += f"  Max Tokens: {self.max_tokens}\n\n"
        
        # Histórico antes da mensagem
        log += f"{'─'*70}\n"
        log += f"[HISTÓRICO (antes da nova mensagem)]\n"
        log += f"{'─'*70}\n"
        log += f"  Total de mensagens: {len(self.historico) - 2}\n"  # -2 pois já adicionou user+assistant
        log += f"  Tokens aproximados: {tokens_antes}\n\n"
        
        for i, msg in enumerate(self.historico[:-2] if len(self.historico) > 2 else [], 1):
            role = "USUÁRIO" if msg["role"] == "user" else "ASSISTENTE"
            log += f"  [{i}] {role}:\n"
            conteudo = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            log += f"      {conteudo}\n\n"
        
        # Resposta do assistente
        log += f"{'─'*70}\n"
        log += f"[RESPOSTA DO ASSISTENTE]\n"
        log += f"{'─'*70}\n"
        log += f"{resposta_assistente}\n\n"
        
        # Status de memória
        log += f"{'─'*70}\n"
        log += f"[STATUS DE MEMÓRIA]\n"
        log += f"{'─'*70}\n"
        log += f"  Total de mensagens: {len(self.historico)}\n"
        log += f"  Tokens aproximados: {tokens_depois}\n"
        
        if self.tamanho_janela:
            log += f"  Janela máxima: {self.tamanho_janela * 2} mensagens ({self.tamanho_janela} pares)\n"
        
        if self.limite_maximo:
            percentual = (tokens_depois / self.limite_maximo) * 100
            nivel = self._calcular_nivel_alerta(tokens_depois)
            log += f"  Limite máximo: {self.limite_maximo} tokens\n"
            log += f"  Uso atual: {percentual:.1f}% {nivel}\n"
        
        log += "\n"
        
        # Ações executadas
        if acoes:
            log += f"{'─'*70}\n"
            log += f"[AÇÕES EXECUTADAS]\n"
            log += f"{'─'*70}\n"
            for acao in acoes:
                log += f"  ⚠️  {acao}\n"
            log += "\n"
        
        log += f"{'═'*70}\n\n"
        
        self._registrar_log(log)
    
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
    
    def _calcular_nivel_alerta(self, tokens: int) -> str:
        """
        Calcula o nível de alerta baseado na quantidade de tokens.
        
        Args:
            tokens: Quantidade atual de tokens
            
        Returns:
            String com emoji representando o nível
        """
        if not self.limite_maximo:
            return ""
        
        percentual = (tokens / self.limite_maximo) * 100
        
        if percentual >= 100:
            return "🔴"
        elif percentual >= 66:
            return "🟠"
        elif percentual >= 33:
            return "🟡"
        else:
            return "🟢"
    
    def _verificar_tokens(self, tokens: int) -> list:
        """
        Verifica o nível de tokens e retorna alertas apropriados.
        
        Args:
            tokens: Quantidade atual de tokens
            
        Returns:
            Lista de mensagens de alerta
        """
        if not self.limite_maximo:
            return []
        
        alertas = []
        percentual = (tokens / self.limite_maximo) * 100
        nivel = self._calcular_nivel_alerta(tokens)
        
        if percentual >= 100:
            alertas.append(f"{nivel} CRÍTICO: {tokens} tokens ({percentual:.1f}% do limite)")
            alertas.append(f"   Ação recomendada: Execute limpar_historico() ou ajuste JANELA_MAX no .env")
        elif percentual >= 66:
            alertas.append(f"{nivel} LARANJA: {tokens} tokens ({percentual:.1f}% do limite)")
            alertas.append(f"   Atenção: Aproximando do limite máximo")
        elif percentual >= 33:
            alertas.append(f"{nivel} AMARELO: {tokens} tokens ({percentual:.1f}% do limite)")
        else:
            if self.modo_debug:
                alertas.append(f"{nivel} VERDE: {tokens} tokens ({percentual:.1f}% do limite)")
        
        return alertas
    
    def _aplicar_janela_deslizante(self) -> bool:
        """
        Aplica sliding window mantendo apenas as últimas N pares de mensagens.
        
        Returns:
            True se a janela foi aplicada, False caso contrário
        """
        if not self.tamanho_janela:
            return False
        
        max_mensagens = self.tamanho_janela * 2  # user + assistant = 1 par
        
        if len(self.historico) > max_mensagens:
            mensagens_removidas = len(self.historico) - max_mensagens
            self.historico = self.historico[-max_mensagens:]
            
            if self.modo_debug:
                self._registrar_log(f"[SLIDING WINDOW] Removidas {mensagens_removidas} mensagens antigas. "
                                   f"Mantendo {len(self.historico)} mensagens.\n")
            
            return True
        
        return False
    
    def enviar_mensagem(self, mensagem: str) -> str:
        """
        Envia mensagem para a API mantendo o contexto completo.
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            Resposta do assistente
        """
        # Contagem de tokens antes
        tokens_antes = self.contar_tokens_aproximado()
        acoes_executadas = []
        
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
            
            # Aplica sliding window se configurado
            if self._aplicar_janela_deslizante():
                acoes_executadas.append(f"Sliding window aplicado: mantendo {self.tamanho_janela} pares de mensagens")
            
            # Contagem de tokens depois
            tokens_depois = self.contar_tokens_aproximado()
            
            # Verifica alertas de tokens
            alertas = self._verificar_tokens(tokens_depois)
            if alertas:
                for alerta in alertas:
                    print(f"\n⚠️  {alerta}")
                    acoes_executadas.append(alerta)
                print()
            
            # Registra interação completa no log
            if self.modo_debug:
                self._registrar_interacao(mensagem, resposta_texto, tokens_antes, tokens_depois, acoes_executadas if acoes_executadas else None)
            
            return resposta_texto
            
        except Exception as e:
            erro = f"Erro ao chamar API OpenAI: {e}"
            if self.modo_debug:
                self._registrar_log(f"\n[ERRO] {erro}\n")
            raise Exception(erro)
    
    def limpar_historico(self):
        """Limpa todo o histórico de conversação"""
        mensagens_removidas = len(self.historico)
        self.historico = []
        print("Histórico limpo - memória apagada\n")
        
        if self.modo_debug:
            self._registrar_log(f"\n{'═'*70}\n")
            self._registrar_log(f"[LIMPEZA DE HISTÓRICO]\n")
            self._registrar_log(f"{'═'*70}\n")
            self._registrar_log(f"Removidas {mensagens_removidas} mensagens do histórico\n")
            self._registrar_log(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            self._registrar_log(f"{'═'*70}\n\n")
    
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
    
    def debug_memoria(self):
        """Exibe informações detalhadas sobre o estado atual da memória"""
        tokens = self.contar_tokens_aproximado()
        
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*22 + "DEBUG DE MEMÓRIA" + " "*30 + "║")
        print("╚" + "═"*68 + "╝\n")
        
        print(f"📊 Status Geral:")
        print(f"   • Total de mensagens: {len(self.historico)}")
        print(f"   • Pares (user+assistant): {len(self.historico) // 2}")
        print(f"   • Tokens aproximados: {tokens}\n")
        
        if self.tamanho_janela:
            print(f"🪟 Sliding Window:")
            print(f"   • Limite: {self.tamanho_janela} pares ({self.tamanho_janela * 2} mensagens)")
            print(f"   • Uso atual: {len(self.historico) // 2} pares ({len(self.historico)} mensagens)")
            uso_percentual = (len(self.historico) / (self.tamanho_janela * 2)) * 100
            print(f"   • Percentual: {uso_percentual:.1f}%\n")
        else:
            print(f"🪟 Sliding Window: Desabilitado\n")
        
        if self.limite_maximo:
            nivel = self._calcular_nivel_alerta(tokens)
            percentual = (tokens / self.limite_maximo) * 100
            print(f"📈 Monitoramento:")
            print(f"   • Limite máximo: {self.limite_maximo} tokens")
            print(f"   • Uso atual: {tokens} tokens ({percentual:.1f}%)")
            print(f"   • Nível: {nivel}")
            
            # Barra de progresso ASCII
            barra_total = 50
            barra_preenchida = int((tokens / self.limite_maximo) * barra_total)
            barra_preenchida = min(barra_preenchida, barra_total)
            barra = "█" * barra_preenchida + "░" * (barra_total - barra_preenchida)
            print(f"   • Progresso: [{barra}]\n")
        else:
            print(f"📈 Monitoramento: Desabilitado\n")
        
        if self.modo_debug:
            print(f"🐛 Modo Debug: Ativo")
            print(f"   • Arquivo de log: {self.arquivo_log}")
            print(f"   • Interações registradas: {self.contador_interacoes}\n")
        else:
            print(f"🐛 Modo Debug: Desabilitado\n")
        
        print("═"*70 + "\n")
    
    def grafico_tokens(self):
        """Gera um gráfico ASCII da evolução de tokens no histórico"""
        if len(self.historico) == 0:
            print("\n⚠️  Nenhum histórico disponível para gerar gráfico\n")
            return
        
        print("\n" + "╔" + "═"*68 + "╗")
        print("║" + " "*20 + "GRÁFICO DE TOKENS" + " "*31 + "║")
        print("╚" + "═"*68 + "╝\n")
        
        # Calcula tokens acumulados a cada mensagem
        tokens_acumulados = []
        total_chars = 0
        
        for msg in self.historico:
            total_chars += len(msg["content"])
            tokens_acumulados.append(total_chars // 4)
        
        if not tokens_acumulados:
            print("⚠️  Nenhum dado para exibir\n")
            return
        
        max_tokens = max(tokens_acumulados)
        altura_grafico = 15
        largura_grafico = len(tokens_acumulados)
        
        print(f"Evolução de tokens ao longo de {len(self.historico)} mensagens\n")
        print(f"Max: {max_tokens} tokens")
        
        # Desenha o gráfico de cima para baixo
        for nivel in range(altura_grafico, -1, -1):
            linha = ""
            threshold = (nivel / altura_grafico) * max_tokens
            
            for tokens in tokens_acumulados:
                if tokens >= threshold:
                    linha += "█"
                else:
                    linha += " "
            
            # Adiciona escala no lado esquerdo
            if nivel == altura_grafico:
                print(f"{max_tokens:>4} |{linha}")
            elif nivel == altura_grafico // 2:
                print(f"{max_tokens//2:>4} |{linha}")
            elif nivel == 0:
                print(f"   0 |{linha}")
            else:
                print(f"     |{linha}")
        
        # Linha de base
        print(f"     └" + "─" * largura_grafico)
        print(f"      Mensagens: 1" + " " * (largura_grafico - 13) + f"{len(self.historico)}")
        
        if self.limite_maximo:
            percentual = (max_tokens / self.limite_maximo) * 100
            nivel = self._calcular_nivel_alerta(max_tokens)
            print(f"\n{nivel} Uso máximo: {max_tokens}/{self.limite_maximo} tokens ({percentual:.1f}%)")
        
        print("\n" + "═"*70 + "\n")
    
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
    print("  /debug     - Exibe informações detalhadas de memória")
    print("  /grafico   - Mostra gráfico de evolução de tokens")
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
                chat.limpar_historico()
                continue
            
            elif mensagem.lower() == "/historico":
                chat.mostrar_historico()
                continue
            
            elif mensagem.lower() == "/tokens":
                tokens = chat.contar_tokens_aproximado()
                print(f"\nTokens aproximados no histórico: {tokens}\n")
                continue
            
            elif mensagem.lower() == "/debug":
                chat.debug_memoria()
                continue
            
            elif mensagem.lower() == "/grafico":
                chat.grafico_tokens()
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

