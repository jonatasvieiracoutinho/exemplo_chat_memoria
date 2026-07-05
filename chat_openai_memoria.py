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

# Carrega o .env já na importação do módulo, garantindo que qualquer
# leitura de os.getenv() (inclusive antes de instanciar ChatComMemoria,
# como a checagem de PERSISTENCIA_SQLITE em chat_interativo) enxergue as
# variáveis. load_dotenv() é idempotente e não sobrescreve o ambiente.
load_dotenv()


# ============================================================
#  Camada visual (UI) — cores e caixas para o terminal
# ------------------------------------------------------------
#  Usa colorama para traduzir códigos ANSI também no Windows.
#  Se a biblioteca não estiver instalada, o chat continua
#  funcionando normalmente, apenas sem cores (degradação graciosa).
# ============================================================
try:
    from colorama import init as _iniciar_cores, Fore, Style
    _iniciar_cores(autoreset=False)  # o reset é feito manualmente por pintar()
except ImportError:  # colorama ausente: cada cor vira string vazia
    class _SemCor:
        def __getattr__(self, _nome):
            return ""
    Fore = Style = _SemCor()


class _Paleta:
    """Paleta semântica de cores e medidas usada em todo o chat."""

    LARGURA = 70                            # largura padrão das caixas

    USUARIO = Fore.CYAN + Style.BRIGHT      # rótulo do usuário
    ASSISTENTE = Fore.GREEN + Style.BRIGHT  # rótulo do assistente
    SISTEMA = Fore.MAGENTA + Style.BRIGHT   # mensagens do sistema

    TITULO = Fore.WHITE + Style.BRIGHT      # títulos de caixas/seções
    VALOR = Fore.CYAN                       # valores destacados
    MOLDURA = Fore.BLUE                     # bordas das caixas
    INFO = Fore.BLUE + Style.BRIGHT         # marcadores / ícones
    DIM = Style.DIM                         # texto secundário

    OK = Fore.GREEN
    AVISO = Fore.YELLOW + Style.BRIGHT
    ERRO = Fore.RED + Style.BRIGHT
    RESET = Style.RESET_ALL


_C = _Paleta()


def pintar(texto: str, cor: str) -> str:
    """Envolve um texto com uma cor ANSI e garante o reset ao final."""
    return f"{cor}{texto}{_C.RESET}"


def regua(largura: int = None, cor: str = None, char: str = "─") -> str:
    """Devolve uma linha horizontal (régua) para separar seções."""
    return pintar(char * (largura or _C.LARGURA), cor or _C.DIM)


def cabecalho(titulo: str, cor: str = None, largura: int = None) -> str:
    """Monta uma caixa de título centralizada (3 linhas), já colorida.

    O padding é calculado sobre o texto sem cor, garantindo o alinhamento
    das bordas mesmo com os códigos ANSI embutidos.
    """
    cor = cor or _C.MOLDURA
    largura = largura or _C.LARGURA
    interno = largura - 2
    texto = f" {titulo.strip()} "[:interno]
    espaco = interno - len(texto)
    esq = espaco // 2
    dirr = espaco - esq
    topo = pintar("╔" + "═" * interno + "╗", cor)
    meio = (pintar("║", cor) + " " * esq + pintar(texto, _C.TITULO)
            + " " * dirr + pintar("║", cor))
    base = pintar("╚" + "═" * interno + "╝", cor)
    return f"{topo}\n{meio}\n{base}"


def item(rotulo: str, valor, cor_valor: str = None) -> str:
    """Formata uma linha 'marcador rótulo: valor' com cores."""
    marcador = pintar("•", _C.INFO)
    return (f"  {marcador} {pintar(str(rotulo) + ':', _C.DIM)} "
            f"{pintar(str(valor), cor_valor or _C.VALOR)}")


def cor_por_nivel(emoji: str) -> str:
    """Mapeia o emoji de nível de tokens para a cor ANSI correspondente."""
    return {
        "🔴": _C.ERRO,
        "🟠": Fore.RED,
        "🟡": _C.AVISO,
        "🟢": _C.OK,
    }.get(emoji, "")


class ChatComMemoria:
    """Classe para gerenciar chat com memória usando OpenAI API
       Todas as configurações são carregadas do arquivo .env"""

    def __init__(self, tamanho_janela: int = None, limite_maximo: int = None, modo_debug: bool = None, stream: bool = None, gerenciador=None, thread_id: int = None):
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
            stream: Se True, imprime a resposta token a token conforme chega da API.
                       Se None, carrega de OPENAI_STREAM no .env. Padrão: False.
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

        # Validar Base URL (opcional)
        self.base_url = os.getenv("OPENAI_BASE_URL")
        if self.base_url:
            # Validar formato básico de URL
            if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
                raise ValueError(
                    f"OPENAI_BASE_URL inválida: '{self.base_url}'. "
                    f"A URL deve começar com http:// ou https://"
                )

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

        # Streaming de saída
        if stream is None:
            stream_env = os.getenv("OPENAI_STREAM", "false").lower()
            self.stream = stream_env == "true"
        else:
            self.stream = stream

        # Inicializar cliente
        if self.base_url:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = OpenAI(api_key=self.api_key)
        self.historico = []
        self.system_prompt = "Você é um assistente confiável. Se não tiver certeza das fontes de seus dados, diga que não sabe. É melhor não responder do que responder errado."

        # Persistência SQLite
        self.gerenciador = gerenciador
        self.thread_id = thread_id
        self._thread_titulo_definido = thread_id is not None

        # Carregar histórico da thread selecionada
        if self.gerenciador and self.thread_id:
            self.historico = self.gerenciador.carregar_historico(self.thread_id)
            self._aplicar_janela_deslizante()

        # Controle de logging
        self.arquivo_log = None
        self.contador_interacoes = 0
        
        # Inicializar arquivo de log se modo debug ativo
        if self.modo_debug:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.arquivo_log = f"logs/chat_debug_{timestamp}.log"
            self._inicializar_log()

        # Resumo visual com as configurações REAIS do .env
        print(pintar("  Configuração ativa", _C.TITULO))
        print(regua())
        print(item("Modelo", self.modelo))
        print(item("Temperature", self.temperature))
        print(item("Max tokens", self.max_tokens))
        print(item("Memória", "histórico mantido durante a sessão"))

        # Configurações opcionais de gerenciamento
        if self.base_url:
            print(item("Base URL", self.base_url))
        if self.tamanho_janela:
            print(item("Sliding window", f"{self.tamanho_janela} pares de mensagens"))
        if self.limite_maximo:
            print(item("Monitoramento", f"limite de {self.limite_maximo} tokens"))
        if self.modo_debug:
            print(item("Modo debug", f"logs em {self.arquivo_log}"))
        if self.stream:
            print(item("Streaming", "resposta exibida token a token"))
        if self.gerenciador:
            modo_db = f"thread #{self.thread_id}" if self.thread_id else "nova thread"
            print(item("Persistência", f"SQLite ativo — {modo_db}"))
        print(regua())
        print()
    
    def definir_personalidade(self, prompt: str):
        """
        Define a personalidade do assistente através do system prompt.
        
        Args:
            prompt: Instrução de sistema para definir comportamento do assistente
        """
        self.system_prompt = prompt
        print(pintar("  ✦ Personalidade definida", _C.SISTEMA)
              + pintar(f" — {prompt[:50]}...", _C.DIM) + "\n")
        
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
        self.historico.append({"role": role, "content": content})

        if self.gerenciador:
            if role == "user" and not self._thread_titulo_definido:
                titulo = content[:60].strip() or "Conversa sem título"
                self.thread_id = self.gerenciador.criar_thread(titulo)
                self._thread_titulo_definido = True

            if self.thread_id:
                ordem = len(self.historico)
                self.gerenciador.salvar_mensagem(self.thread_id, role, content, ordem)

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

    def _usa_parametros_reasoning(self) -> bool:
        """
        Indica se o modelo configurado pertence à família de reasoning da OpenAI
        (gpt-5*, o1*, o3*, o4*).

        Esses modelos mudaram o contrato da API: exigem 'max_completion_tokens'
        no lugar de 'max_tokens' e só aceitam o valor padrão de temperature (1),
        rejeitando qualquer outro com erro 400.
        """
        modelo = self.modelo.lower()
        return modelo.startswith(("gpt-5", "o1", "o3", "o4"))

    def _extrair_uso_tokens(self, usage):
        """Extrai (prompt, completion, total) de um objeto `usage` da API.
        Retorna (None, None, None) quando `usage` é ausente/incompleto —
        ex.: base_url alternativa (Ollama/LM Studio/Azure) ou streaming sem
        include_usage. Nunca lança exceção."""
        if usage is None:
            return None, None, None

        def _get(campo):
            valor = getattr(usage, campo, None)
            return valor if isinstance(valor, int) else None

        return _get("prompt_tokens"), _get("completion_tokens"), _get("total_tokens")

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
            # Monta os parâmetros conforme o contrato da API do modelo.
            # Modelos de reasoning (gpt-5*, o-series) usam 'max_completion_tokens'
            # e não aceitam 'temperature' customizada (somente o padrão 1).
            parametros = {
                "model": self.modelo,
                "messages": mensagens,
            }
            if self._usa_parametros_reasoning():
                parametros["max_completion_tokens"] = self.max_tokens
            else:
                parametros["temperature"] = self.temperature
                parametros["max_tokens"] = self.max_tokens

            usage_bruto = None
            if self.stream:
                # Streaming: imprime a resposta token a token conforme chega.
                parametros["stream"] = True
                parametros["stream_options"] = {"include_usage": True}
                resposta_texto = ""
                for chunk in self.client.chat.completions.create(**parametros):
                    # O chunk final de usage chega sem choices; capturamos quando presente.
                    if getattr(chunk, "usage", None) is not None:
                        usage_bruto = chunk.usage
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta.content
                    if delta:
                        print(delta, end="", flush=True)
                        resposta_texto += delta
            else:
                # Chama a API e extrai a resposta completa de uma vez
                resposta = self.client.chat.completions.create(**parametros)
                resposta_texto = resposta.choices[0].message.content
                usage_bruto = getattr(resposta, "usage", None)

            # Adiciona resposta ao histórico
            self.adicionar_mensagem("assistant", resposta_texto)

            # Persiste os tokens reais do turno no mesmo fluxo de gravação (RF2/RF3).
            # Tolerante a ausência de usage e a falhas de escrita (RF7/CA7).
            if self.gerenciador and self.thread_id:
                prompt_tokens, completion_tokens, total_tokens = self._extrair_uso_tokens(usage_bruto)
                try:
                    self.gerenciador.salvar_turno(
                        self.thread_id, prompt_tokens, completion_tokens, total_tokens
                    )
                except Exception as e:
                    if self.modo_debug:
                        self._registrar_log(f"\n[AVISO] Falha ao persistir tokens do turno: {e}\n")

            # Aplica sliding window se configurado
            if self._aplicar_janela_deslizante():
                acoes_executadas.append(f"Sliding window aplicado: mantendo {self.tamanho_janela} pares de mensagens")
            
            # Contagem de tokens depois
            tokens_depois = self.contar_tokens_aproximado()
            
            # Verifica alertas de tokens (cor conforme o nível de uso)
            alertas = self._verificar_tokens(tokens_depois)
            if alertas:
                cor_alerta = cor_por_nivel(self._calcular_nivel_alerta(tokens_depois))
                print()
                for alerta in alertas:
                    print(pintar(f"  ⚠  {alerta}", cor_alerta))
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
        print(pintar("  ✓ Histórico limpo — memória apagada", _C.OK) + "\n")
        
        if self.modo_debug:
            self._registrar_log(f"\n{'═'*70}\n")
            self._registrar_log(f"[LIMPEZA DE HISTÓRICO]\n")
            self._registrar_log(f"{'═'*70}\n")
            self._registrar_log(f"Removidas {mensagens_removidas} mensagens do histórico\n")
            self._registrar_log(f"Timestamp: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            self._registrar_log(f"{'═'*70}\n\n")
    
    def mostrar_historico(self):
        """Exibe todo o histórico de conversação"""
        print("\n" + cabecalho("HISTÓRICO DA CONVERSAÇÃO"))

        if not self.historico:
            print(pintar("\n  (histórico vazio)\n", _C.DIM))
            return

        for i, msg in enumerate(self.historico, 1):
            usuario = msg["role"] == "user"
            rotulo = "Você" if usuario else "Assistente"
            cor = _C.USUARIO if usuario else _C.ASSISTENTE
            print()
            print(pintar(f"  ┃ [{i}] {rotulo}", cor))
            # Barra vertical colorida em cada linha do conteúdo
            for linha in msg["content"].splitlines() or [""]:
                print(pintar("  ┃ ", cor) + linha)

        print("\n" + regua() + "\n")
    
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
        
        print("\n" + cabecalho("DEBUG DE MEMÓRIA") + "\n")

        print(pintar("📊 Status Geral", _C.TITULO))
        print(item("Total de mensagens", len(self.historico)))
        print(item("Pares (user+assistant)", len(self.historico) // 2))
        print(item("Tokens aproximados", tokens) + "\n")

        if self.tamanho_janela:
            uso_percentual = (len(self.historico) / (self.tamanho_janela * 2)) * 100
            print(pintar("🪟 Sliding Window", _C.TITULO))
            print(item("Limite", f"{self.tamanho_janela} pares ({self.tamanho_janela * 2} mensagens)"))
            print(item("Uso atual", f"{len(self.historico) // 2} pares ({len(self.historico)} mensagens)"))
            print(item("Percentual", f"{uso_percentual:.1f}%") + "\n")
        else:
            print(pintar("🪟 Sliding Window", _C.TITULO) + pintar("  Desabilitado", _C.DIM) + "\n")

        if self.limite_maximo:
            nivel = self._calcular_nivel_alerta(tokens)
            percentual = (tokens / self.limite_maximo) * 100
            print(pintar("📈 Monitoramento", _C.TITULO))
            print(item("Limite máximo", f"{self.limite_maximo} tokens"))
            print(item("Uso atual", f"{tokens} tokens ({percentual:.1f}%)"))
            print(item("Nível", nivel))

            # Barra de progresso colorida conforme o nível de uso
            barra_total = 50
            barra_preenchida = int((tokens / self.limite_maximo) * barra_total)
            barra_preenchida = min(barra_preenchida, barra_total)
            barra = (pintar("█" * barra_preenchida, cor_por_nivel(nivel))
                     + pintar("░" * (barra_total - barra_preenchida), _C.DIM))
            print(f"   {pintar('•', _C.INFO)} Progresso: {pintar('▕', _C.DIM)}{barra}{pintar('▏', _C.DIM)}\n")
        else:
            print(pintar("📈 Monitoramento", _C.TITULO) + pintar("  Desabilitado", _C.DIM) + "\n")

        if self.modo_debug:
            print(pintar("🐛 Modo Debug", _C.TITULO) + pintar("  Ativo", _C.OK))
            print(item("Arquivo de log", self.arquivo_log))
            print(item("Interações registradas", self.contador_interacoes) + "\n")
        else:
            print(pintar("🐛 Modo Debug", _C.TITULO) + pintar("  Desabilitado", _C.DIM) + "\n")

        print(regua() + "\n")
    
    def grafico_tokens(self):
        """Gera um gráfico ASCII da evolução de tokens no histórico"""
        if len(self.historico) == 0:
            print("\n⚠️  Nenhum histórico disponível para gerar gráfico\n")
            return
        
        print("\n" + cabecalho("GRÁFICO DE TOKENS") + "\n")

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
        
        print(pintar(f"Evolução de tokens ao longo de {len(self.historico)} mensagens", _C.DIM) + "\n")
        print(item("Máximo", f"{max_tokens} tokens"))

        # Cor das barras: pelo nível de uso (se houver limite) ou cor neutra
        cor_graf = cor_por_nivel(self._calcular_nivel_alerta(max_tokens)) if self.limite_maximo else _C.VALOR

        # Desenha o gráfico de cima para baixo
        for nivel in range(altura_grafico, -1, -1):
            linha = ""
            threshold = (nivel / altura_grafico) * max_tokens

            for tokens in tokens_acumulados:
                if tokens >= threshold:
                    linha += "█"
                else:
                    linha += " "

            barra = pintar(linha, cor_graf)
            eixo = pintar("│", _C.MOLDURA)
            # Adiciona escala no lado esquerdo
            if nivel == altura_grafico:
                print(pintar(f"{max_tokens:>4} ", _C.DIM) + eixo + barra)
            elif nivel == altura_grafico // 2:
                print(pintar(f"{max_tokens//2:>4} ", _C.DIM) + eixo + barra)
            elif nivel == 0:
                print(pintar("   0 ", _C.DIM) + eixo + barra)
            else:
                print(pintar("     ", _C.DIM) + eixo + barra)

        # Linha de base
        print(pintar("     └" + "─" * largura_grafico, _C.MOLDURA))
        print(pintar(f"      Mensagens: 1" + " " * (largura_grafico - 13) + f"{len(self.historico)}", _C.DIM))
        
        if self.limite_maximo:
            percentual = (max_tokens / self.limite_maximo) * 100
            nivel = self._calcular_nivel_alerta(max_tokens)
            print(pintar(f"\n{nivel} Uso máximo: {max_tokens}/{self.limite_maximo} tokens ({percentual:.1f}%)",
                         cor_por_nivel(nivel)))

        print("\n" + regua() + "\n")
    
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
        
        print(pintar(f"  ✓ Conversa exportada para: {arquivo}", _C.OK) + "\n")


def _exibir_lista_threads(gerenciador):
    threads = gerenciador.listar_threads()
    if not threads:
        print(pintar("  Nenhuma conversa armazenada.", _C.DIM))
        return
    print(pintar("  Conversas armazenadas", _C.TITULO))
    print(regua())
    for t in threads:
        data = t["atualizado_em"][:16].replace("T", " ")
        titulo = t["titulo"][:42]
        msgs = t["total_mensagens"]
        linha = (
            f"  {pintar(str(t['id']).rjust(3), _C.SISTEMA)}"
            f"  {titulo:<44}"
            f"  {pintar(data, _C.DIM)}"
            f"  {pintar(f'({msgs} msg)', _C.DIM)}"
        )
        print(linha)
    print(regua())


def _selecionar_thread(gerenciador):
    threads = gerenciador.listar_threads()
    print()
    print(cabecalho("SELECIONAR CONVERSA", cor=_C.SISTEMA))
    print()
    _exibir_lista_threads(gerenciador)
    print(f"  {pintar('  0', _C.SISTEMA)}  Nova conversa")
    print()
    while True:
        escolha = input(pintar("  Selecione o ID (ou 0 para nova): ", _C.USUARIO)).strip()
        if escolha == "0":
            return None
        if escolha.isdigit() and gerenciador.thread_existe(int(escolha)):
            return int(escolha)
        print(pintar(f"  Thread '{escolha}' não encontrada. Tente novamente.", _C.ERRO))


def chat_interativo():
    """Função principal para chat interativo no terminal"""

    persistencia_ativa = os.getenv("PERSISTENCIA_SQLITE", "false").lower() == "true"
    gerenciador = None
    thread_id_inicial = None

    if persistencia_ativa:
        from persistencia import GerenciadorPersistencia
        gerenciador = GerenciadorPersistencia()
        thread_id_inicial = _selecionar_thread(gerenciador)

    print()
    print(cabecalho("CHAT OPENAI · MEMÓRIA DE CONVERSAÇÃO", cor=_C.USUARIO))
    print()
    print(pintar("  Comandos especiais", _C.TITULO))
    print(regua())
    comandos_base = [
        ("/limpar",    "Limpa a memória do chat"),
        ("/historico", "Mostra todo o histórico"),
        ("/tokens",    "Mostra quantidade aproximada de tokens"),
        ("/debug",     "Exibe informações detalhadas de memória"),
        ("/grafico",   "Mostra gráfico de evolução de tokens"),
        ("/exportar",  "Exporta a conversa para arquivo"),
        ("/sair",      "Encerra o chat"),
    ]
    if persistencia_ativa:
        comandos_base += [
            ("/threads",       "Lista conversas armazenadas"),
            ("/retomar <id>",  "Retoma uma conversa salva"),
            ("/excluir <id>",  "Exclui uma conversa permanentemente"),
        ]
    for cmd, desc in comandos_base:
        print(f"  {pintar(cmd.ljust(11), _C.SISTEMA)} {pintar(desc, _C.DIM)}")
    print(regua() + "\n")
    
    try:
        # Inicializa o chat
        chat = ChatComMemoria(gerenciador=gerenciador, thread_id=thread_id_inicial)
        
        # Opcional: definir personalidade customizada
        # chat.definir_personalidade("Você é um especialista em Python que responde de forma concisa.")
        
        while True:
            # Recebe mensagem do usuário
            mensagem = input(pintar("  Você ▸ ", _C.USUARIO)).strip()
            
            if not mensagem:
                continue
            
            # Processa comandos especiais
            if mensagem.lower() == "/sair":
                print(pintar("\n  Encerrando chat. Até logo! 👋", _C.SISTEMA) + "\n")
                break
            
            elif mensagem.lower() == "/limpar":
                chat.limpar_historico()
                if gerenciador:
                    print(pintar(
                        "  ℹ  Histórico em memória limpo. Mensagens no banco SQLite foram preservadas.",
                        _C.SISTEMA
                    ) + "\n")
                continue
            
            elif mensagem.lower() == "/historico":
                chat.mostrar_historico()
                continue
            
            elif mensagem.lower() == "/tokens":
                tokens = chat.contar_tokens_aproximado()
                print("\n" + item("Tokens aproximados no histórico", tokens) + "\n")
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

            elif mensagem.lower() == "/threads":
                if gerenciador:
                    _exibir_lista_threads(gerenciador)
                else:
                    print(pintar(
                        "  Persistência desabilitada. Defina PERSISTENCIA_SQLITE=true no .env para usar threads.",
                        _C.DIM
                    ) + "\n")
                continue

            elif mensagem.lower().startswith("/retomar"):
                partes = mensagem.split()
                if not gerenciador:
                    print(pintar("  Persistência desabilitada.", _C.DIM) + "\n")
                elif len(partes) == 2 and partes[1].isdigit():
                    novo_id = int(partes[1])
                    if gerenciador.thread_existe(novo_id):
                        historico = gerenciador.carregar_historico(novo_id)
                        chat.historico = historico
                        chat._aplicar_janela_deslizante()
                        chat.thread_id = novo_id
                        chat._thread_titulo_definido = True
                        print(pintar(f"  ✔ Thread #{novo_id} carregada ({len(historico)} mensagens).", _C.SISTEMA) + "\n")
                    else:
                        print(pintar(f"  Thread #{novo_id} não encontrada.", _C.ERRO) + "\n")
                else:
                    print(pintar("  Uso: /retomar <id>", _C.DIM) + "\n")
                continue

            elif mensagem.lower().startswith("/excluir"):
                partes = mensagem.split()
                if not gerenciador:
                    print(pintar("  Persistência desabilitada.", _C.DIM) + "\n")
                elif len(partes) == 2 and partes[1].isdigit():
                    excluir_id = int(partes[1])
                    if gerenciador.thread_existe(excluir_id):
                        confirmacao = input(
                            pintar(f"  Excluir thread #{excluir_id}? Esta ação é irreversível. (s/n): ", _C.ERRO)
                        ).strip().lower()
                        if confirmacao == "s":
                            gerenciador.excluir_thread(excluir_id)
                            if excluir_id == chat.thread_id:
                                chat.historico = []
                                chat.thread_id = None
                                chat._thread_titulo_definido = False
                                print(pintar(
                                    "  Thread ativa excluída. Nova conversa iniciada.", _C.SISTEMA
                                ) + "\n")
                            else:
                                print(pintar(f"  Thread #{excluir_id} excluída.", _C.SISTEMA) + "\n")
                        else:
                            print(pintar("  Exclusão cancelada.", _C.DIM) + "\n")
                    else:
                        print(pintar(f"  Thread #{excluir_id} não encontrada.", _C.ERRO) + "\n")
                else:
                    print(pintar("  Uso: /excluir <id>", _C.DIM) + "\n")
                continue

            # Envia mensagem e recebe resposta
            try:
                print(pintar("\n  Assistente ▸ ", _C.ASSISTENTE), end="", flush=True)
                resposta = chat.enviar_mensagem(mensagem)
                # No modo streaming a resposta já foi impressa token a token
                if chat.stream:
                    print("\n")
                else:
                    print(resposta + "\n")
                print(regua())

            except Exception as e:
                print(pintar(f"\n  ✖ Erro: {e}", _C.ERRO) + "\n")
                break
    
    except ValueError as e:
        print(pintar(f"\n  ✖ Erro de configuração: {e}", _C.ERRO))
        print(pintar("  Configure a variável OPENAI_API_KEY no arquivo .env.\n", _C.DIM))

    except KeyboardInterrupt:
        print(pintar("\n\n  Chat interrompido pelo usuário. Até logo! 👋", _C.SISTEMA))

    except Exception as e:
        print(pintar(f"\n  ✖ Erro inesperado: {e}", _C.ERRO))
    finally:
        if gerenciador:
            gerenciador.fechar()


def exemplo_programatico():
    """Exemplo de uso programático (não interativo)"""
    
    print("\n" + cabecalho("EXEMPLO DE USO PROGRAMÁTICO", cor=_C.SISTEMA) + "\n")
    
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
        print(pintar("  Você ▸ ", _C.USUARIO) + pergunta)
        print(pintar("  Assistente ▸ ", _C.ASSISTENTE), end="", flush=True)
        resposta = chat.enviar_mensagem(pergunta)
        # No modo streaming a resposta já foi impressa token a token
        if chat.stream:
            print("\n")
        else:
            print(f"{resposta}\n")
        print(regua() + "\n")

    # Mostra estatísticas
    print(item("Total de mensagens no histórico", len(chat.historico)))
    print(item("Tokens aproximados", chat.contar_tokens_aproximado()))
    
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

