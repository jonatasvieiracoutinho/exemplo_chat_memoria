#!/bin/bash
# Ativa o ambiente virtual e executa o app Streamlit.
# Funciona independente da pasta de onde for chamado.

cd "$(dirname "$0")"

if [ ! -f ".venv/bin/activate" ]; then
    echo "[ERRO] Ambiente virtual nao encontrado em .venv"
    echo "Crie com: python -m venv .venv  e instale as dependencias."
    exit 1
fi

source ".venv/bin/activate"

streamlit run app_streamlit.py --server.address=localhost
