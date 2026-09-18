"""
Helpers UI-agnósticos do front-end Streamlit.

Este módulo não importa `streamlit`: toda a lógica testável fica aqui,
reaproveitando `ChatComMemoria`/`GerenciadorPersistencia` sem duplicar
negócio. `app_streamlit.py` faz apenas o wiring dos widgets.
"""

import os
import tempfile

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


def historico_para_ui(chat) -> list:
    """Devolve pares (role, content) na ordem de `chat.historico`."""
    return [(msg["role"], msg["content"]) for msg in chat.historico]


def resumo_tokens(chat) -> dict:
    """Estimativa aproximada e, sob persistência com thread_id, o total
    persistido. Degrada para aproximado se `total_tokens_thread` vier nulo."""
    resultado = {"aproximado": chat.contar_tokens_aproximado(), "total_persistido": None}
    if chat.gerenciador and chat.thread_id:
        dados = chat.gerenciador.total_tokens_thread(chat.thread_id)
        if dados:
            resultado["total_persistido"] = dados.get("total_tokens")
    return resultado


def exportar_conversa_texto(chat) -> tuple:
    """Exporta a conversa via `exportar_conversa()` em arquivo temporário
    (nunca no repositório) e devolve (nome, conteudo)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
        caminho = tmp.name
    chat.exportar_conversa(caminho)
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()
    os.remove(caminho)
    return os.path.basename(caminho), conteudo
