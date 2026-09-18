import re
from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parent.parent / "requirements.txt"


def test_lista_streamlit_com_versao_minima():
    conteudo = REQUIREMENTS.read_text()
    assert re.search(r"^streamlit>=1\.28\.0$", conteudo, re.MULTILINE)


def test_dependencias_preexistentes_permanecem():
    conteudo = REQUIREMENTS.read_text()
    assert "openai>=1.12.0" in conteudo
    assert "python-dotenv>=1.0.0" in conteudo
    assert "colorama>=0.4.6" in conteudo
    assert "pytest>=8.0.0" in conteudo
