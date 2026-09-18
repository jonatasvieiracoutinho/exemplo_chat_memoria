"""
Helpers UI-agnósticos do front-end Streamlit.

Este módulo não importa `streamlit`: toda a lógica testável fica aqui,
reaproveitando `ChatComMemoria`/`GerenciadorPersistencia` sem duplicar
negócio. `app_streamlit.py` faz apenas o wiring dos widgets.
"""

import os

from chat_openai_memoria import ChatComMemoria


def persistencia_ativa() -> bool:
    """Lê PERSISTENCIA_SQLITE do ambiente (true/false), padrão false."""
    return os.getenv("PERSISTENCIA_SQLITE", "false").lower() == "true"


def construir_sessao_chat(gerenciador=None, thread_id=None) -> ChatComMemoria:
    """Instancia ChatComMemoria, repassando gerenciador/thread_id somente
    quando a persistência está ativa."""
    if persistencia_ativa():
        return ChatComMemoria(gerenciador=gerenciador, thread_id=thread_id)
    return ChatComMemoria()


MENSAGEM_ERRO_AMIGAVEL = "Não foi possível obter resposta agora. Tente novamente em instantes."


def sanitizar_erro(exc: Exception) -> str:
    """Converte qualquer exceção em mensagem amigável fixa, sem expor
    chave, stack trace ou texto bruto da exceção."""
    return MENSAGEM_ERRO_AMIGAVEL


def enviar_mensagem_seguro(chat, texto: str):
    """Envia `texto` via `chat.enviar_mensagem`, capturando exceções.

    Retorna `(resposta, None)` no sucesso e `(None, msg_sanitizada)` na
    exceção. Texto vazio/branco não chama a API e não altera o histórico.
    """
    if not texto or not texto.strip():
        return None, None
    try:
        return chat.enviar_mensagem(texto), None
    except Exception as exc:
        return None, sanitizar_erro(exc)
