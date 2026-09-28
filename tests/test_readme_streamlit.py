from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"

# O encoding e EXPLICITO de proposito: `read_text()` sem argumento usa o encoding
# padrao da plataforma, que no Windows e cp1252 e nao decodifica os emojis do README.
ENCODING = "utf-8"


def test_menciona_iniciar_streamlit_e_streamlit_run():
    conteudo = README.read_text(encoding=ENCODING)
    assert "iniciar_streamlit" in conteudo
    assert "streamlit run app_streamlit.py" in conteudo


def test_menciona_nota_de_bind_local():
    conteudo = README.read_text(encoding=ENCODING)
    assert "--server.address=localhost" in conteudo
