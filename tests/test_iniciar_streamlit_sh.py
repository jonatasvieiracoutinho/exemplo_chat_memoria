import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "iniciar_streamlit.sh"

# O encoding e EXPLICITO de proposito: `read_text()` sem argumento usa o encoding
# padrao da plataforma, que no Windows e cp1252.
ENCODING = "utf-8"


def _bash_utilizavel():
    """Devolve o caminho de um bash que de fato executa, ou None.

    No Windows, `shutil.which("bash")` costuma achar primeiro o bash do WSL, que
    falha com `execvpe(/bin/bash) failed` quando nao ha distro instalada. Por isso
    cada candidato e testado de verdade antes de ser aceito, e o bash do Git for
    Windows vem antes na ordem de preferencia.
    """
    candidatos = [
        os.environ.get("BASH_PARA_TESTES"),
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        shutil.which("bash"),
    ]
    for candidato in candidatos:
        if not candidato or not Path(candidato).is_file():
            continue
        try:
            sonda = subprocess.run(
                [candidato, "-c", "exit 0"],
                capture_output=True,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if sonda.returncode == 0:
            return candidato
    return None


BASH = _bash_utilizavel()


def test_conteudo_tem_streamlit_run_e_bind_local():
    conteudo = SCRIPT.read_text(encoding=ENCODING)
    assert "streamlit run app_streamlit.py" in conteudo
    assert "--server.address=localhost" in conteudo


@pytest.mark.skipif(
    BASH is None,
    reason="nenhum bash executavel encontrado (defina BASH_PARA_TESTES para apontar um)",
)
def test_sem_venv_erro_claro_e_exit_diferente_de_zero():
    with tempfile.TemporaryDirectory() as tmp:
        destino = Path(tmp) / "iniciar_streamlit.sh"
        shutil.copy(SCRIPT, destino)
        destino.chmod(0o755)

        resultado = subprocess.run(
            [BASH, str(destino)],
            cwd=tmp,
            capture_output=True,
            text=True,
        )

        assert resultado.returncode != 0
        assert "ERRO" in resultado.stdout
        assert ".venv" in resultado.stdout
