"""
Helpers UI-agnósticos do front-end Streamlit.

Este módulo não importa `streamlit`: toda a lógica testável fica aqui,
reaproveitando `ChatComMemoria`/`GerenciadorPersistencia` sem duplicar
negócio. `app_streamlit.py` faz apenas o wiring dos widgets.
"""

import os
import re
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


def mascarar_chave(texto: str, chaves) -> str:
    """Substitui cada ocorrência de uma chave não vazia em `texto` por uma
    máscara: 4 primeiros + `***` + 4 últimos quando a chave tem 12
    caracteres ou mais, `***` inteiro quando tem menos."""
    resultado = texto
    for chave in chaves:
        if not chave:
            continue
        if len(chave) >= 12:
            mascara = f"{chave[:4]}***{chave[-4:]}"
        else:
            mascara = "***"
        resultado = resultado.replace(chave, mascara)
    return resultado


def _prefixo_perfil(nome: str) -> str:
    """Normaliza o nome do Perfil no prefixo de variável de ambiente:
    maiúsculas, todo caractere não alfanumérico trocado por `_`
    (`Ollama local` -> `PERFIL_OLLAMA_LOCAL_`)."""
    normalizado = re.sub(r"[^A-Za-z0-9]", "_", nome).upper()
    return f"PERFIL_{normalizado}_"


def carregar_perfis() -> list:
    """Lê `os.environ` e devolve a lista de Perfis de provedor: sempre
    começando por `Padrão (.env)` (montado das variáveis `OPENAI_*`),
    seguida de cada nome declarado em `PERFIS`, na ordem declarada."""
    perfis = [
        {
            "nome": "Padrão (.env)",
            "base_url": os.getenv("OPENAI_BASE_URL"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "modelo": os.getenv("OPENAI_MODEL"),
            "disponivel": True,
            "motivo_indisponivel": None,
        }
    ]
    nomes = [nome.strip() for nome in os.getenv("PERFIS", "").split(",") if nome.strip()]
    for nome in nomes:
        prefixo = _prefixo_perfil(nome)
        base_url = os.getenv(f"{prefixo}BASE_URL")
        api_key = os.getenv(f"{prefixo}API_KEY")
        modelo = os.getenv(f"{prefixo}MODEL")
        variavel_ausente = next(
            (
                f"{prefixo}{sufixo}"
                for sufixo, valor in (("BASE_URL", base_url), ("API_KEY", api_key), ("MODEL", modelo))
                if not valor or not valor.strip()
            ),
            None,
        )
        if variavel_ausente:
            perfis.append(
                {
                    "nome": nome,
                    "base_url": None,
                    "api_key": None,
                    "modelo": None,
                    "disponivel": False,
                    "motivo_indisponivel": f"Perfil {nome}: variável {variavel_ausente} ausente ou vazia",
                }
            )
            continue
        perfis.append(
            {
                "nome": nome,
                "base_url": base_url,
                "api_key": api_key,
                "modelo": modelo,
                "disponivel": True,
                "motivo_indisponivel": None,
            }
        )
    return perfis


def sanitizar_erro(exc: Exception, chat=None) -> str:
    """Converte a exceção no seu texto com a chave ativa mascarada.

    A chave ativa vem de `chat.api_key` (não de `os.environ`, porque um
    override por Perfil pode não estar no ambiente); `OPENAI_API_KEY`
    também é mascarada quando presente."""
    chave_ativa = getattr(chat, "api_key", None) if chat is not None else None
    return mascarar_chave(str(exc), [chave_ativa, os.getenv("OPENAI_API_KEY")])


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
        return None, sanitizar_erro(exc, chat)


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


def listar_threads(gerenciador) -> list:
    """Lista as threads persistidas via `GerenciadorPersistencia`."""
    return gerenciador.listar_threads()


def retomar_thread(gerenciador, thread_id) -> ChatComMemoria:
    """Reconstrói `ChatComMemoria` com o `thread_id` selecionado, carregando
    seu histórico a partir da persistência."""
    return construir_sessao_chat(gerenciador=gerenciador, thread_id=thread_id)


def excluir_thread(gerenciador, thread_id) -> bool:
    """Exclui a thread; `True` quando remove, `False` para id inexistente."""
    return gerenciador.excluir_thread(thread_id)


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
