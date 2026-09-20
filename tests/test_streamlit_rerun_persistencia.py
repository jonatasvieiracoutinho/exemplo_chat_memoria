"""
Testes de integração: continuidade da conversa na interface web através de
reruns do Streamlit.

Um rerun pode despachar a execução seguinte em uma thread diferente da que
criou o gerenciador de persistência armazenado em `st.session_state`. O
helper `rodar_em_nova_execucao` reproduz essa condição (gerenciador criado em
uma thread, operações executadas em outra) sem precisar de um servidor
Streamlit real, reusando `app_streamlit_core`, `chat_openai_memoria` e
`persistencia` como o app real faz.
"""

import os
import threading
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

import pytest

from persistencia import GerenciadorPersistencia

ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


def rodar_em_nova_execucao(func, *args, **kwargs):
    """Executa `func` em uma thread nova, simulando um rerun que despacha a
    execução seguinte em thread diferente da que criou o gerenciador/conexão.
    Propaga exceções levantadas dentro da thread para a thread chamadora."""
    resultado = {}

    def alvo():
        try:
            resultado["valor"] = func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - propagada abaixo
            resultado["erro"] = exc

    execucao = threading.Thread(target=alvo)
    execucao.start()
    execucao.join()
    if "erro" in resultado:
        raise resultado["erro"]
    return resultado.get("valor")


def _resposta_openai(texto, prompt_tokens, completion_tokens, total_tokens):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=texto))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        ),
    )


def renderizar_inicial(sessao, caminho_db):
    """Reproduz `inicializar_estado()` de app_streamlit.py: cria o
    gerenciador (se a persistência está ativa) e a sessão de chat, guardando
    ambos em `sessao` como `st.session_state` guardaria entre reruns."""
    from app_streamlit_core import construir_sessao_chat, persistencia_ativa

    gerenciador = GerenciadorPersistencia(caminho_db) if persistencia_ativa() else None
    sessao["gerenciador"] = gerenciador
    sessao["chat"] = construir_sessao_chat(gerenciador=gerenciador)
    sessao["thread_id"] = sessao["chat"].thread_id
    return sessao


def renderizar_envio(sessao, texto):
    """Reproduz o envio de mensagem pelo `st.chat_input` em app_streamlit.py."""
    from app_streamlit_core import enviar_mensagem_seguro

    resposta, erro = enviar_mensagem_seguro(sessao["chat"], texto)
    sessao["thread_id"] = sessao["chat"].thread_id
    return resposta, erro


def renderizar_listar(sessao):
    """Reproduz a listagem de threads exibida na barra lateral."""
    from app_streamlit_core import listar_threads

    return listar_threads(sessao["gerenciador"])


@pytest.fixture
def openai_mockado():
    with patch.dict("os.environ", ENV_VARS, clear=False):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai_cls:
                cliente = MagicMock()
                mock_openai_cls.return_value = cliente
                with patch("builtins.print"):
                    yield cliente


# ---------- T2: renderização inicial + primeiro envio ----------

def test_rerun_renderizacao_inicial_e_primeiro_envio_sem_erro_de_conexao(tmp_path, openai_mockado):
    caminho_db = str(tmp_path / "rerun.db")
    openai_mockado.chat.completions.create.return_value = _resposta_openai(
        "Oi! Como posso ajudar?", 15, 25, 40
    )

    with patch.dict("os.environ", {**ENV_VARS, "PERSISTENCIA_SQLITE": "true"}):
        sessao = {}
        rodar_em_nova_execucao(renderizar_inicial, sessao, caminho_db)

        # após a renderização inicial, a lista de conversas deve estar
        # disponível sem erro de conexão pertencente a outra execução
        threads_disponiveis = rodar_em_nova_execucao(renderizar_listar, sessao)
        assert threads_disponiveis == []

        resposta, erro = rodar_em_nova_execucao(renderizar_envio, sessao, "Olá, tudo bem?")

        assert erro is None
        assert resposta == "Oi! Como posso ajudar?"

        gerenciador_verificacao = GerenciadorPersistencia(caminho_db)
        try:
            threads = gerenciador_verificacao.listar_threads()
            assert len(threads) == 1
            thread_id = threads[0]["id"]

            historico = gerenciador_verificacao.carregar_historico(thread_id)
            assert len(historico) == 2
            assert historico[0]["role"] == "user"
            assert historico[1]["role"] == "assistant"

            turnos = gerenciador_verificacao.carregar_turnos(thread_id)
            assert len(turnos) == 1
            assert turnos[0]["prompt_tokens"] == 15
            assert turnos[0]["completion_tokens"] == 25
            assert turnos[0]["total_tokens"] == 40
        finally:
            gerenciador_verificacao.fechar()
