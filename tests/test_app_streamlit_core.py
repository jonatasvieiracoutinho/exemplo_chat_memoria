import tempfile

import pytest
from unittest.mock import MagicMock, patch

ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


@pytest.fixture
def openai_mockado():
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                with patch("builtins.print"):
                    yield


# ---------- persistencia_ativa ----------

def test_persistencia_ativa_true_quando_env_true():
    with patch.dict("os.environ", {"PERSISTENCIA_SQLITE": "true"}):
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is True


def test_persistencia_ativa_false_quando_env_ausente():
    import os
    with patch.dict("os.environ", {}, clear=False):
        os.environ.pop("PERSISTENCIA_SQLITE", None)
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is False


def test_persistencia_ativa_false_quando_env_outro_valor():
    with patch.dict("os.environ", {"PERSISTENCIA_SQLITE": "yes"}):
        from app_streamlit_core import persistencia_ativa
        assert persistencia_ativa() is False


# ---------- construir_sessao_chat ----------

def test_construir_sessao_chat_sem_persistencia_ignora_gerenciador(openai_mockado):
    with patch.dict("os.environ", {**ENV_VARS, "PERSISTENCIA_SQLITE": "false"}):
        from app_streamlit_core import construir_sessao_chat
        gerenciador = MagicMock()
        chat = construir_sessao_chat(gerenciador=gerenciador, thread_id=42)
        assert chat.gerenciador is None
        assert chat.thread_id is None


def test_construir_sessao_chat_com_persistencia_usa_gerenciador_e_thread_id(openai_mockado):
    with patch.dict("os.environ", {**ENV_VARS, "PERSISTENCIA_SQLITE": "true"}):
        from app_streamlit_core import construir_sessao_chat
        gerenciador = MagicMock()
        gerenciador.carregar_historico.return_value = []
        chat = construir_sessao_chat(gerenciador=gerenciador, thread_id=42)
        assert chat.gerenciador is gerenciador
        assert chat.thread_id == 42


# ---------- mascarar_chave ----------

def test_mascarar_chave_doze_ou_mais_caracteres_vira_parcial():
    from app_streamlit_core import mascarar_chave
    texto = "chave gsk_abc123XYZ789 invalida"
    resultado = mascarar_chave(texto, ["gsk_abc123XYZ789"])
    assert "gsk_***Z789" in resultado
    assert "gsk_abc123XYZ789" not in resultado


def test_mascarar_chave_menos_de_doze_vira_opaca():
    from app_streamlit_core import mascarar_chave
    texto = "provedor ollama sem chave"
    resultado = mascarar_chave(texto, ["ollama"])
    assert "***" in resultado
    assert "ollama" not in resultado


def test_mascarar_chave_none_ou_vazia_e_ignorada_sem_erro():
    from app_streamlit_core import mascarar_chave
    texto = "texto sem nenhuma chave"
    resultado = mascarar_chave(texto, [None, ""])
    assert resultado == texto


def test_mascarar_chave_limite_exato_doze_caracteres():
    from app_streamlit_core import mascarar_chave
    chave = "123456789012"  # exatamente 12 caracteres
    texto = f"chave {chave} usada"
    resultado = mascarar_chave(texto, [chave])
    assert "1234***9012" in resultado
    assert chave not in resultado


def test_mascarar_chave_onze_caracteres_fica_opaca():
    from app_streamlit_core import mascarar_chave
    chave = "12345678901"  # 11 caracteres
    texto = f"chave {chave} usada"
    resultado = mascarar_chave(texto, [chave])
    assert "***" in resultado
    assert chave not in resultado


# ---------- sanitizar_erro ----------

def test_sanitizar_erro_nao_contem_texto_bruto_da_excecao():
    from app_streamlit_core import sanitizar_erro
    chat = MagicMock()
    chat.api_key = "sk-segredo-123456"
    exc = Exception(f"Erro ao chamar API OpenAI: chave {chat.api_key} inválida")
    msg = sanitizar_erro(exc, chat)
    assert chat.api_key not in msg
    assert "Erro ao chamar API OpenAI" in msg


def test_sanitizar_erro_nao_contem_api_key_do_ambiente():
    from app_streamlit_core import sanitizar_erro
    chat = MagicMock()
    chat.api_key = "outra-chave-ativa-em-uso"
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-real-key-999"}):
        exc = Exception("Traceback: falha em algum_modulo.py, chave sk-real-key-999")
        msg = sanitizar_erro(exc, chat)
        assert "sk-real-key-999" not in msg
        assert "Traceback" in msg


# ---------- enviar_mensagem_seguro ----------

def test_enviar_mensagem_seguro_sucesso_retorna_resposta_sem_erro():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.enviar_mensagem.return_value = "Resposta do assistente"
    resposta, erro = enviar_mensagem_seguro(chat, "Olá")
    assert resposta == "Resposta do assistente"
    assert erro is None
    chat.enviar_mensagem.assert_called_once_with("Olá")


def test_enviar_mensagem_seguro_excecao_retorna_mensagem_sanitizada():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.api_key = "sk-segredo-longa-123"
    chat.enviar_mensagem.side_effect = Exception(f"Erro ao chamar API OpenAI: {chat.api_key}")
    resposta, erro = enviar_mensagem_seguro(chat, "Olá")
    assert resposta is None
    assert chat.api_key not in erro
    assert "Erro ao chamar API OpenAI" in erro


def test_enviar_mensagem_seguro_texto_vazio_nao_chama_api():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.historico = []
    resposta, erro = enviar_mensagem_seguro(chat, "")
    assert resposta is None
    assert erro is None
    chat.enviar_mensagem.assert_not_called()
    assert chat.historico == []


def test_enviar_mensagem_seguro_texto_em_branco_nao_chama_api():
    from app_streamlit_core import enviar_mensagem_seguro
    chat = MagicMock()
    chat.historico = []
    resposta, erro = enviar_mensagem_seguro(chat, "   \n\t  ")
    assert resposta is None
    assert erro is None
    chat.enviar_mensagem.assert_not_called()
    assert chat.historico == []


# ---------- historico_para_ui ----------

def test_historico_para_ui_devolve_pares_na_ordem():
    from app_streamlit_core import historico_para_ui
    chat = MagicMock()
    chat.historico = [
        {"role": "user", "content": "Pergunta"},
        {"role": "assistant", "content": "Resposta"},
    ]
    pares = historico_para_ui(chat)
    assert pares == [("user", "Pergunta"), ("assistant", "Resposta")]


def test_historico_para_ui_vazio_devolve_lista_vazia():
    from app_streamlit_core import historico_para_ui
    chat = MagicMock()
    chat.historico = []
    assert historico_para_ui(chat) == []


# ---------- resumo_tokens ----------

def test_resumo_tokens_sem_persistencia_traz_so_aproximado():
    from app_streamlit_core import resumo_tokens
    chat = MagicMock()
    chat.contar_tokens_aproximado.return_value = 42
    chat.gerenciador = None
    chat.thread_id = None
    resultado = resumo_tokens(chat)
    assert resultado == {"aproximado": 42, "total_persistido": None}


def test_resumo_tokens_com_persistencia_soma_total_persistido():
    from app_streamlit_core import resumo_tokens
    chat = MagicMock()
    chat.contar_tokens_aproximado.return_value = 42
    chat.gerenciador = MagicMock()
    chat.gerenciador.total_tokens_thread.return_value = {"total_tokens": 500}
    chat.thread_id = 7
    resultado = resumo_tokens(chat)
    assert resultado == {"aproximado": 42, "total_persistido": 500}
    chat.gerenciador.total_tokens_thread.assert_called_once_with(7)


def test_resumo_tokens_degrada_para_aproximado_quando_total_nulo():
    from app_streamlit_core import resumo_tokens
    chat = MagicMock()
    chat.contar_tokens_aproximado.return_value = 42
    chat.gerenciador = MagicMock()
    chat.gerenciador.total_tokens_thread.return_value = None
    chat.thread_id = 7
    resultado = resumo_tokens(chat)
    assert resultado == {"aproximado": 42, "total_persistido": None}


# ---------- exportar_conversa_texto ----------

def test_exportar_conversa_texto_usa_arquivo_temporario_e_devolve_conteudo():
    import os
    from app_streamlit_core import exportar_conversa_texto
    chat = MagicMock()
    caminho_usado = {}

    def _gravar(caminho):
        caminho_usado["valor"] = caminho
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("VOCÊ:\nOlá\n\nASSISTENTE:\nOi\n\n")

    chat.exportar_conversa.side_effect = _gravar
    nome, conteudo = exportar_conversa_texto(chat)
    assert "Olá" in conteudo and "Oi" in conteudo
    assert nome.endswith(".txt")
    assert caminho_usado["valor"].startswith(tempfile.gettempdir())
    assert not os.path.exists(caminho_usado["valor"])


# ---------- carregar_perfis ----------

def test_carregar_perfis_primeira_entrada_sempre_padrao_env():
    with patch.dict("os.environ", ENV_VARS, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert perfis[0]["nome"] == "Padrão (.env)"
        assert perfis[0]["disponivel"] is True
        assert perfis[0]["base_url"] is None
        assert perfis[0]["api_key"] == "sk-test-key"
        assert perfis[0]["modelo"] == "gpt-4o-mini"


def test_carregar_perfis_inclui_perfil_com_bloco_completo_na_ordem_declarada():
    env = {
        **ENV_VARS,
        "PERFIS": "Groq,Ollama local",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
        "PERFIL_OLLAMA_LOCAL_BASE_URL": "http://localhost:11434/v1",
        "PERFIL_OLLAMA_LOCAL_API_KEY": "ollama",
        "PERFIL_OLLAMA_LOCAL_MODEL": "llama3",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        nomes = [perfil["nome"] for perfil in perfis]
        assert nomes == ["Padrão (.env)", "Groq", "Ollama local"]
        groq = perfis[1]
        assert groq["disponivel"] is True
        assert groq["base_url"] == "https://api.groq.com/openai/v1"
        assert groq["api_key"] == "gsk_exemplo"
        assert groq["modelo"] == "llama-3.3-70b-versatile"


def test_carregar_perfis_normaliza_nome_com_espaco_para_prefixo():
    env = {
        **ENV_VARS,
        "PERFIS": "Ollama local",
        "PERFIL_OLLAMA_LOCAL_BASE_URL": "http://localhost:11434/v1",
        "PERFIL_OLLAMA_LOCAL_API_KEY": "ollama",
        "PERFIL_OLLAMA_LOCAL_MODEL": "llama3",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert perfis[1]["nome"] == "Ollama local"
        assert perfis[1]["base_url"] == "http://localhost:11434/v1"


# ---------- carregar_perfis: bloco incompleto ----------

def test_carregar_perfis_bloco_incompleto_fica_indisponivel_e_permanece_na_lista():
    env = {
        **ENV_VARS,
        "PERFIS": "Ollama local",
        "PERFIL_OLLAMA_LOCAL_BASE_URL": "http://localhost:11434/v1",
        "PERFIL_OLLAMA_LOCAL_API_KEY": "ollama",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        nomes = [perfil["nome"] for perfil in perfis]
        assert "Ollama local" in nomes
        perfil = perfis[1]
        assert perfil["disponivel"] is False
        assert "PERFIL_OLLAMA_LOCAL_MODEL" in perfil["motivo_indisponivel"]
        assert "Ollama local" in perfil["motivo_indisponivel"]
        assert perfil["modelo"] is None


def test_carregar_perfis_variavel_so_com_espacos_conta_como_ausente():
    env = {
        **ENV_VARS,
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "   ",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert perfis[1]["disponivel"] is False
        assert "PERFIL_GROQ_MODEL" in perfis[1]["motivo_indisponivel"]


# ---------- carregar_perfis: esquema, deduplicação e PERFIS ausente ----------

def test_carregar_perfis_url_sem_esquema_fica_indisponivel_com_url_no_motivo():
    env = {
        **ENV_VARS,
        "PERFIS": "Groq",
        "PERFIL_GROQ_BASE_URL": "api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert perfis[1]["disponivel"] is False
        assert "api.groq.com/openai/v1" in perfis[1]["motivo_indisponivel"]
        assert "Groq" in perfis[1]["motivo_indisponivel"]


def test_carregar_perfis_nome_repetido_entra_uma_vez():
    env = {
        **ENV_VARS,
        "PERFIS": "Groq,Groq",
        "PERFIL_GROQ_BASE_URL": "https://api.groq.com/openai/v1",
        "PERFIL_GROQ_API_KEY": "gsk_exemplo",
        "PERFIL_GROQ_MODEL": "llama-3.3-70b-versatile",
    }
    with patch.dict("os.environ", env, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        nomes = [perfil["nome"] for perfil in perfis]
        assert nomes.count("Groq") == 1


def test_carregar_perfis_sem_perfis_declarados_devolve_so_padrao():
    with patch.dict("os.environ", ENV_VARS, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert len(perfis) == 1
        assert perfis[0]["nome"] == "Padrão (.env)"


def test_carregar_perfis_perfis_vazia_devolve_so_padrao():
    with patch.dict("os.environ", {**ENV_VARS, "PERFIS": ""}, clear=True):
        from app_streamlit_core import carregar_perfis
        perfis = carregar_perfis()
        assert len(perfis) == 1
        assert perfis[0]["nome"] == "Padrão (.env)"
