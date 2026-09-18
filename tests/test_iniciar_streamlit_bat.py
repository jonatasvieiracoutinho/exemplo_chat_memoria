from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "iniciar_streamlit.bat"


def test_conteudo_tem_checagem_do_venv():
    conteudo = SCRIPT.read_text()
    assert 'if not exist ".venv\\Scripts\\activate.bat"' in conteudo
    assert "exit /b 1" in conteudo


def test_conteudo_tem_ativacao_e_streamlit_run_com_bind_local():
    conteudo = SCRIPT.read_text()
    assert 'call ".venv\\Scripts\\activate.bat"' in conteudo
    assert "streamlit run app_streamlit.py" in conteudo
    assert "--server.address=localhost" in conteudo
