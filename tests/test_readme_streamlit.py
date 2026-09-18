from pathlib import Path

README = Path(__file__).resolve().parent.parent / "README.md"


def test_menciona_iniciar_streamlit_e_streamlit_run():
    conteudo = README.read_text()
    assert "iniciar_streamlit" in conteudo
    assert "streamlit run app_streamlit.py" in conteudo


def test_menciona_nota_de_bind_local():
    conteudo = README.read_text()
    assert "--server.address=localhost" in conteudo
