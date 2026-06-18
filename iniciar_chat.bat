@echo off
REM Ativa o ambiente virtual e executa o chat com memoria.
REM Funciona independente da pasta de onde for chamado.

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado em .venv
    echo Crie com: python -m venv .venv  e instale as dependencias.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

python chat_openai_memoria.py

REM Mantem a janela aberta ao final para ver a saida/erros.
pause
