import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "iniciar_streamlit.sh"


def test_conteudo_tem_streamlit_run_e_bind_local():
    conteudo = SCRIPT.read_text()
    assert "streamlit run app_streamlit.py" in conteudo
    assert "--server.address=localhost" in conteudo


def test_sem_venv_erro_claro_e_exit_diferente_de_zero():
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "iniciar_streamlit.sh"
        shutil.copy(SCRIPT, destino)
        destino.chmod(0o755)

        resultado = subprocess.run(
            ["bash", str(destino)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )

        assert resultado.returncode != 0
        assert "ERRO" in resultado.stdout
        assert ".venv" in resultado.stdout
