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
