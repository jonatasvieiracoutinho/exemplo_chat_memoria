import pytest

pytest.importorskip("streamlit")

from unittest.mock import MagicMock, patch


def _chat_mock():
    chat = MagicMock()
    chat.historico = []
    chat.thread_id = None
    chat.gerenciador = None
    chat.contar_tokens_aproximado.return_value = 42

    def _exportar(caminho):
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("conteudo exportado")

    chat.exportar_conversa.side_effect = _exportar

    def _limpar():
        chat.historico = []

    chat.limpar_historico.side_effect = _limpar
    return chat


def _chat_mock_com_helpers():
    chat = _chat_mock()
    chat.historico = [
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá"},
    ]
    return chat


def test_app_exibe_historico_e_envia_mensagem():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    def _enviar(c, texto):
        c.historico.append({"role": "user", "content": texto})
        c.historico.append({"role": "assistant", "content": "Resposta simulada"})
        c.thread_id = 1
        return "Resposta simulada", None

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert "Olá" in textos
    assert "Resposta simulada" in textos


def test_app_erro_sanitizado_aparece_amigavel():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()
    chat.api_key = "gsk_abc123XYZ789"
    chat.enviar_mensagem.side_effect = Exception(
        "AuthenticationError: Incorrect API key provided: gsk_abc123XYZ789"
    )

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    assert len(at.error) == 1
    assert "Incorrect API key provided" in at.error[0].value
    assert "gsk_abc123XYZ789" not in at.error[0].value
    assert "gsk_***Z789" in at.error[0].value


def test_app_preserva_estado_entre_reruns():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    def _enviar(c, texto):
        c.historico.append({"role": "user", "content": texto})
        c.historico.append({"role": "assistant", "content": "Resposta simulada"})
        return "Resposta simulada", None

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat) as construir_mock, \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()
        at.run()

    construir_mock.assert_called_once()
    assert len(at.chat_message) == 2
    assert at.session_state["chat"] is chat
    assert "thread_id" in at.session_state
    assert "gerenciador" in at.session_state


def test_sidebar_limpar_esvazia_historico_exibido():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        assert len(at.chat_message) == 2
        at.sidebar.button[0].click().run()

    assert len(at.chat_message) == 0
    chat.limpar_historico.assert_called_once()


def test_sidebar_exibe_metrica_de_tokens():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert at.sidebar.metric[0].value == "42"


def test_sidebar_download_entrega_conteudo_exportado():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    botao = at.sidebar.download_button[0]
    assert botao.label == "Exportar conversa"
    chat.exportar_conversa.assert_called_once()
    caminho_usado = chat.exportar_conversa.call_args.args[0]
    assert caminho_usado.endswith(".txt")


def test_sidebar_painel_threads_ausente_quando_persistencia_desativada():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert not any(h.value == "Threads" for h in at.sidebar.header)


def test_sidebar_painel_threads_aparece_com_persistencia_ativa():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert any(h.value == "Threads" for h in at.sidebar.header)


def test_sidebar_retomar_thread_atualiza_sessao_e_historico():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    chat_retomado = _chat_mock_com_helpers()
    chat_retomado.thread_id = 1
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]), \
         patch("app_streamlit_core.retomar_thread", return_value=chat_retomado) as retomar_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.button[1].click().run()

    retomar_mock.assert_called_once_with(gerenciador, 1)
    assert at.session_state["chat"] is chat_retomado
    assert at.session_state["thread_id"] == 1


def test_bolha_usuario_aparece_imediatamente_com_spinner_mesmo_sem_append():
    """Discrimina o bug: a bolha do usuário deve ser pintada pela camada de
    wiring antes da geração, independente do núcleo anexar ao histórico."""
    from streamlit.testing.v1 import AppTest
    import streamlit as st

    chat = _chat_mock()

    def _enviar_sem_append(c, texto):
        return None, "Não foi possível obter resposta agora. Tente novamente em instantes."

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", side_effect=_enviar_sem_append), \
         patch("app_streamlit.st.spinner", wraps=st.spinner) as spinner_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert "Olá" in textos
    spinner_mock.assert_called_once_with("Gerando resposta...")


def test_dois_envios_consecutivos_nao_duplicam_bolhas():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()
    enviar_mock = MagicMock()

    def _enviar(c, texto):
        c.historico.append({"role": "user", "content": texto})
        c.historico.append({"role": "assistant", "content": f"Resposta para: {texto}"})
        return f"Resposta para: {texto}", None

    enviar_mock.side_effect = _enviar

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.enviar_mensagem_seguro", enviar_mock), \
         patch("app_streamlit.st.rerun") as rerun_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Primeira").run()
        at.chat_input[0].set_value("Segunda").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert textos == [
        "Primeira",
        "Resposta para: Primeira",
        "Segunda",
        "Resposta para: Segunda",
    ]
    assert enviar_mock.call_count == 2
    rerun_mock.assert_not_called()


def test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append():
    """Discrimina o bug: na falha, a fala do usuário deve permanecer visível
    e apenas um st.error sanitizado deve aparecer, sem bolha de assistente."""
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()
    chat.api_key = "gsk_abc123XYZ789"
    chat.enviar_mensagem.side_effect = Exception(
        "AuthenticationError: Incorrect API key provided: gsk_abc123XYZ789"
    )

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.chat_input[0].set_value("Olá").run()

    textos = [m.markdown[0].value for m in at.chat_message]
    assert textos == ["Olá"]
    assert len(at.error) == 1
    assert "Incorrect API key provided" in at.error[0].value
    assert "gsk_abc123XYZ789" not in at.error[0].value


def test_provedor_seletor_troca_perfil_repassa_tres_valores_e_esvazia_conversa():
    from streamlit.testing.v1 import AppTest

    chat_inicial = _chat_mock_com_helpers()
    chat_groq = _chat_mock()

    env = {
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env), \
         patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", side_effect=[chat_inicial, chat_groq]) as construir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.selectbox[-1].set_value("Groq").run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat_groq
    assert at.session_state["thread_id"] is None
    assert at.session_state["perfil_ativo"] == "Groq"
    assert len(at.chat_message) == 0
    _, kwargs = construir_mock.call_args
    assert kwargs["api_key"] == "gsk_exemplo"
    assert kwargs["modelo"] == "llama-3.3-70b-versatile"
    assert kwargs["base_url"] == "https://api.groq.com/openai/v1"


def test_provedor_seletor_mantem_mesmo_gerenciador_apos_troca():
    from streamlit.testing.v1 import AppTest

    chat_inicial = _chat_mock_com_helpers()
    chat_groq = _chat_mock()
    gerenciador = MagicMock()

    env = {
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env), \
         patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.listar_threads", return_value=[]), \
         patch("app_streamlit_core.construir_sessao_chat", side_effect=[chat_inicial, chat_groq]):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        gerenciador_antes = at.session_state["gerenciador"]
        at.sidebar.selectbox[-1].set_value("Groq").run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["gerenciador"] is gerenciador_antes


def test_provedor_criacao_da_sessao_inicia_com_padrao_env():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert at.session_state["perfil_ativo"] == "Padrão (.env)"
    assert at.sidebar.selectbox[-1].value == "Padrão (.env)"


def test_provedor_resumo_mostra_perfil_ativo_sem_a_chave():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()
    chat.base_url = "https://api.groq.com/openai/v1"
    chat.modelo = "llama-3.3-70b-versatile"
    chat.api_key = "gsk_super_secreta_123"

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    textos = " ".join(c.value for c in at.sidebar.caption)
    assert "Padrão (.env)" in textos
    assert "llama-3.3-70b-versatile" in textos
    assert "https://api.groq.com/openai/v1" in textos
    assert "gsk_super_secreta_123" not in textos


def test_provedor_reselecionar_perfil_ativo_preserva_sessao_sem_chamar_construtor_de_novo():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat) as construir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat
    assert len(at.chat_message) == 2
    construir_mock.assert_called_once()


def test_provedor_reselecionar_perfil_nao_padrao_ja_ativo_nao_reconstroi():
    from streamlit.testing.v1 import AppTest

    chat_inicial = _chat_mock_com_helpers()
    chat_groq = _chat_mock_com_helpers()
    env = {
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env), \
         patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch(
             "app_streamlit_core.construir_sessao_chat",
             side_effect=[chat_inicial, chat_groq],
         ) as construir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.selectbox[-1].set_value("Groq").run()
        at.sidebar.button[-1].click().run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat_groq
    assert at.session_state["perfil_ativo"] == "Groq"
    assert construir_mock.call_count == 2


def test_provedor_perfil_indisponivel_exibe_motivo_e_preserva_sessao():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    env = {
        "PERFIS": "Ollama local",
        "PERFIL_OLLAMA_LOCAL_BASE_URL": "http://localhost:11434/v1",
        "PERFIL_OLLAMA_LOCAL_API_KEY": "ollama",
    }
    with patch.dict("os.environ", env), \
         patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat) as construir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.selectbox[-1].set_value("Ollama local").run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat
    assert len(at.error) == 1
    assert "PERFIL_OLLAMA_LOCAL_MODEL" in at.error[0].value
    assert len(at.chat_message) == 2
    construir_mock.assert_called_once()


def test_provedor_recusa_do_construtor_preserva_sessao_anterior():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    env = {
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env), \
         patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch(
             "app_streamlit_core.construir_sessao_chat",
             side_effect=[chat, ValueError("modelo inválido")],
         ):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.selectbox[-1].set_value("Groq").run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat
    assert len(at.error) == 1
    assert "modelo inválido" in at.error[0].value
    assert len(at.chat_message) == 2


def test_sidebar_excluir_thread_chama_helper_do_nucleo():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock_com_helpers()
    gerenciador = MagicMock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=True), \
         patch("persistencia.GerenciadorPersistencia", return_value=gerenciador), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat), \
         patch("app_streamlit_core.listar_threads", return_value=[{"id": 1, "titulo": "Thread 1"}]), \
         patch("app_streamlit_core.excluir_thread") as excluir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.button[2].click().run()

    excluir_mock.assert_called_once_with(gerenciador, 1)


def test_provedor_seletor_oferece_perfil_digitado():
    from streamlit.testing.v1 import AppTest

    chat = _chat_mock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch("app_streamlit_core.construir_sessao_chat", return_value=chat):
        at = AppTest.from_file("../app_streamlit.py")
        at.run()

    assert "Perfil digitado" in at.sidebar.selectbox[-1].options


def test_provedor_perfil_digitado_valido_troca_sessao_com_os_tres_valores():
    from streamlit.testing.v1 import AppTest

    chat_inicial = _chat_mock_com_helpers()
    chat_digitado = _chat_mock()

    with patch("app_streamlit_core.persistencia_ativa", return_value=False), \
         patch(
             "app_streamlit_core.construir_sessao_chat",
             side_effect=[chat_inicial, chat_digitado],
         ) as construir_mock:
        at = AppTest.from_file("../app_streamlit.py")
        at.run()
        at.sidebar.selectbox[-1].set_value("Perfil digitado").run()
        at.sidebar.text_input[-3].set_value("https://api.groq.com/openai/v1").run()
        at.sidebar.text_input[-2].set_value("gsk_digitada").run()
        at.sidebar.text_input[-1].set_value("llama-3.3-70b-versatile").run()
        at.sidebar.button[-1].click().run()

    assert at.session_state["chat"] is chat_digitado
    assert at.session_state["thread_id"] is None
    assert at.session_state["perfil_ativo"] == "Perfil digitado"
    assert len(at.chat_message) == 0
    _, kwargs = construir_mock.call_args
    assert kwargs["api_key"] == "gsk_digitada"
    assert kwargs["modelo"] == "llama-3.3-70b-versatile"
    assert kwargs["base_url"] == "https://api.groq.com/openai/v1"


