import pytest
from unittest.mock import MagicMock, patch
from persistencia import GerenciadorPersistencia


ENV_VARS = {
    "OPENAI_API_KEY": "sk-test-key",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_TEMPERATURE": "0.7",
    "OPENAI_MAX_TOKENS": "1000",
}


@pytest.fixture
def db():
    g = GerenciadorPersistencia(":memory:")
    yield g
    g.fechar()


@pytest.fixture
def chat_sem_persistencia():
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    yield ChatComMemoria()


@pytest.fixture
def chat_com_db(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    yield ChatComMemoria(gerenciador=db), db


# ---------- sem persistência ----------

def test_adicionar_mensagem_sem_gerenciador_nao_cria_thread(chat_sem_persistencia):
    chat = chat_sem_persistencia
    chat.adicionar_mensagem("user", "Olá")
    assert chat.thread_id is None
    assert len(chat.historico) == 1


def test_adicionar_mensagem_sem_gerenciador_historico_correto(chat_sem_persistencia):
    chat = chat_sem_persistencia
    chat.adicionar_mensagem("user", "Pergunta")
    chat.adicionar_mensagem("assistant", "Resposta")
    assert chat.historico[0]["role"] == "user"
    assert chat.historico[1]["role"] == "assistant"


# ---------- criação de thread ----------

def test_primeira_mensagem_usuario_cria_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Primeira mensagem")
    assert chat.thread_id is not None
    assert db.thread_existe(chat.thread_id)


def test_titulo_gerado_dos_primeiros_60_chars(chat_com_db):
    chat, db = chat_com_db
    mensagem_longa = "A" * 80
    chat.adicionar_mensagem("user", mensagem_longa)
    threads = db.listar_threads()
    assert len(threads[0]["titulo"]) == 60


def test_titulo_fallback_mensagem_vazia(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "   ")
    threads = db.listar_threads()
    assert threads[0]["titulo"] == "Conversa sem título"


def test_mensagem_assistant_antes_de_user_nao_cria_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("assistant", "Oi")
    assert chat.thread_id is None
    assert db.listar_threads() == []


# ---------- persistência sequencial ----------

def test_mensagens_subsequentes_salvas_na_mesma_thread(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Pergunta 1")
    chat.adicionar_mensagem("assistant", "Resposta 1")
    chat.adicionar_mensagem("user", "Pergunta 2")
    historico = db.carregar_historico(chat.thread_id)
    assert len(historico) == 3


def test_historico_em_memoria_igual_ao_banco(chat_com_db):
    chat, db = chat_com_db
    chat.adicionar_mensagem("user", "Teste")
    chat.adicionar_mensagem("assistant", "Ok")
    historico_db = db.carregar_historico(chat.thread_id)
    assert len(chat.historico) == len(historico_db)
    for mem, banco in zip(chat.historico, historico_db):
        assert mem["role"] == banco["role"]
        assert mem["content"] == banco["content"]


# ---------- janela deslizante não altera banco ----------

def test_janela_deslizante_nao_apaga_mensagens_do_banco(db):
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, tamanho_janela=2)
    chat.adicionar_mensagem("user", "msg 1")
    chat.adicionar_mensagem("assistant", "resp 1")
    chat.adicionar_mensagem("user", "msg 2")
    chat.adicionar_mensagem("assistant", "resp 2")
    chat.adicionar_mensagem("user", "msg 3")
    chat._aplicar_janela_deslizante()
    historico_banco = db.carregar_historico(chat.thread_id)
    assert len(historico_banco) == 5
    assert len(chat.historico) <= 4


# ---------- retomar thread existente ----------

def test_historico_carregado_ao_retomar_thread(db):
    tid = db.criar_thread("Thread existente")
    db.salvar_mensagem(tid, "user", "Pergunta anterior", 1)
    db.salvar_mensagem(tid, "assistant", "Resposta anterior", 2)
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, thread_id=tid)
    assert len(chat.historico) == 2
    assert chat.historico[0]["content"] == "Pergunta anterior"


def test_titulo_nao_sobrescrito_ao_retomar_thread(db):
    tid = db.criar_thread("Título original")
    db.salvar_mensagem(tid, "user", "Primeira msg", 1)
    with patch.dict("os.environ", ENV_VARS):
        with patch("chat_openai_memoria.load_dotenv"):
            with patch("chat_openai_memoria.OpenAI") as mock_openai:
                mock_openai.return_value = MagicMock()
                from chat_openai_memoria import ChatComMemoria
                with patch("builtins.print"):
                    chat = ChatComMemoria(gerenciador=db, thread_id=tid)
    chat.adicionar_mensagem("user", "Nova mensagem após retomar")
    threads = db.listar_threads()
    assert threads[0]["titulo"] == "Título original"


# ---------- _extrair_uso_tokens ----------

def _fake_usage(prompt_tokens=None, completion_tokens=None, total_tokens=None):
    usage = MagicMock(spec=["prompt_tokens", "completion_tokens", "total_tokens"])
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = total_tokens
    return usage


def test_extrair_uso_tokens_usage_completo(chat_sem_persistencia):
    chat = chat_sem_persistencia
    usage = _fake_usage(10, 20, 30)
    assert chat._extrair_uso_tokens(usage) == (10, 20, 30)


def test_extrair_uso_tokens_usage_none(chat_sem_persistencia):
    chat = chat_sem_persistencia
    assert chat._extrair_uso_tokens(None) == (None, None, None)


def test_extrair_uso_tokens_campos_ausentes_ou_invalidos(chat_sem_persistencia):
    chat = chat_sem_persistencia
    usage = _fake_usage(prompt_tokens=10, completion_tokens="não-inteiro", total_tokens=None)
    assert chat._extrair_uso_tokens(usage) == (10, None, None)


# ---------- persistência de turno no fluxo (mock OpenAI) ----------

def _mock_resposta_nao_streaming(conteudo, usage=None):
    resposta = MagicMock()
    resposta.choices = [MagicMock(message=MagicMock(content=conteudo))]
    resposta.usage = usage
    return resposta


def _mock_chunk(delta_content=None, usage=None, sem_choices=False):
    chunk = MagicMock()
    chunk.usage = usage
    if sem_choices:
        chunk.choices = []
    else:
        chunk.choices = [MagicMock(delta=MagicMock(content=delta_content))]
    return chunk


def test_turno_persistido_nao_streaming_com_usage(chat_com_db):
    chat, db = chat_com_db
    usage = _fake_usage(10, 20, 30)
    chat.client.chat.completions.create.return_value = _mock_resposta_nao_streaming(
        "Resposta da API", usage
    )
    with patch("builtins.print"):
        resposta = chat.enviar_mensagem("Pergunta")

    assert resposta == "Resposta da API"
    turnos = db.carregar_turnos(chat.thread_id)
    assert len(turnos) == 1
    assert turnos[0]["prompt_tokens"] == 10
    assert turnos[0]["completion_tokens"] == 20
    assert turnos[0]["total_tokens"] == 30
    historico = db.carregar_historico(chat.thread_id)
    assert len(historico) == 2


def test_turno_persistido_streaming_com_usage_no_chunk_final(chat_com_db):
    chat, db = chat_com_db
    chat.stream = True
    usage = _fake_usage(5, 15, 20)
    chunks = [
        _mock_chunk(delta_content="Olá"),
        _mock_chunk(delta_content=" mundo"),
        _mock_chunk(usage=usage, sem_choices=True),
    ]
    chat.client.chat.completions.create.return_value = iter(chunks)
    with patch("builtins.print"):
        resposta = chat.enviar_mensagem("Pergunta")

    assert resposta == "Olá mundo"
    turnos = db.carregar_turnos(chat.thread_id)
    assert len(turnos) == 1
    assert turnos[0]["total_tokens"] == 20
    _, kwargs = chat.client.chat.completions.create.call_args
    assert kwargs["stream_options"] == {"include_usage": True}


def test_turno_persistido_com_null_quando_usage_ausente(chat_com_db):
    chat, db = chat_com_db
    chat.stream = True
    chunks = [_mock_chunk(delta_content="Sem usage")]
    chat.client.chat.completions.create.return_value = iter(chunks)
    with patch("builtins.print"):
        chat.enviar_mensagem("Pergunta")

    turnos = db.carregar_turnos(chat.thread_id)
    assert len(turnos) == 1
    assert turnos[0]["prompt_tokens"] is None
    assert turnos[0]["completion_tokens"] is None
    assert turnos[0]["total_tokens"] is None
    historico = db.carregar_historico(chat.thread_id)
    assert len(historico) == 2


def test_sem_gerenciador_nao_persiste_turno_nem_falha(chat_sem_persistencia):
    chat = chat_sem_persistencia
    chat.client.chat.completions.create.return_value = _mock_resposta_nao_streaming(
        "Ok", _fake_usage(1, 2, 3)
    )
    with patch("builtins.print"):
        resposta = chat.enviar_mensagem("Pergunta")
    assert resposta == "Ok"


def test_falha_em_salvar_turno_nao_interrompe_fluxo(chat_com_db):
    chat, db = chat_com_db
    chat.client.chat.completions.create.return_value = _mock_resposta_nao_streaming(
        "Ok", _fake_usage(1, 2, 3)
    )
    with patch.object(db, "salvar_turno", side_effect=Exception("falha simulada")):
        with patch("builtins.print"):
            resposta = chat.enviar_mensagem("Pergunta")
    assert resposta == "Ok"
    historico = db.carregar_historico(chat.thread_id)
    assert len(historico) == 2


def test_durabilidade_tokens_apos_reabrir_banco(tmp_path):
    caminho_db = str(tmp_path / "durabilidade.db")

    g1 = GerenciadorPersistencia(caminho_db)
    tid = g1.criar_thread("Thread durável")
    g1.salvar_turno(tid, 10, 20, 30)
    g1.fechar()

    g2 = GerenciadorPersistencia(caminho_db)
    turnos = g2.carregar_turnos(tid)
    total = g2.total_tokens_thread(tid)
    g2.fechar()

    assert len(turnos) == 1
    assert turnos[0]["prompt_tokens"] == 10
    assert total["total_tokens"] == 30
