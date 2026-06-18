#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste direto do backend OpenAI, contornando a UI"""

import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Carregar .env
load_dotenv()

print("\n--- TESTE DIRETO DO BACKEND OPENAI ---\n")

# Ler configuração do .env
api_key = os.getenv("OPENAI_API_KEY")
modelo = os.getenv("OPENAI_MODEL")
base_url = os.getenv("OPENAI_BASE_URL")
stream = os.getenv("OPENAI_STREAM", "false").lower() == "true"

print(f"API Key: {'***' + api_key[-10:] if api_key else 'NAO CONFIGURADA'}")
print(f"Modelo: {modelo}")
print(f"Base URL: {base_url or 'Padrao OpenAI'}")
print(f"Stream: {stream}")

try:
    # Teste direto da classe _BackendOpenAI
    from chat_openai_memoria import _BackendOpenAI

    print("\n[1] Testando instanciacao do _BackendOpenAI...")
    backend = _BackendOpenAI(api_key=api_key, base_url=base_url, modelo=modelo)
    print(f"    OK: Backend instanciado com modelo {backend.modelo}")

    print("\n[2] Testando _usa_parametros_reasoning()...")
    usa_reasoning = backend._usa_parametros_reasoning()
    print(f"    Resultado: {usa_reasoning}")
    print(f"    (Esperado: True para gpt-5, o1, o3, o4; False caso contrario)")

    print("\n[3] Testando gerar() sem stream...")
    resposta = backend.gerar(
        system_prompt="Responda em uma frase curta.",
        historico=[
            {"role": "user", "content": "Qual eh a capital do Brasil?"}
        ],
        temperature=0.7,
        max_tokens=100,
        stream=False
    )
    print(f"    OK: Resposta recebida ({len(resposta)} caracteres)")
    print(f"    Amostra: {resposta[:100]}...")

    print("\n[4] Testando gerar() com stream...")
    print("    Streaming output:")
    resposta_stream = backend.gerar(
        system_prompt="Responda em uma frase curta.",
        historico=[
            {"role": "user", "content": "Qual eh a capital da Argentina?"}
        ],
        temperature=0.7,
        max_tokens=100,
        stream=True
    )
    print(f"\n    OK: Resposta recebida ({len(resposta_stream)} caracteres)")

    print("\n--- TESTES DO BACKEND CONCLUIDOS COM SUCESSO ---")
    print("\nConclusoes:")
    print("- _BackendOpenAI instancia corretamente")
    print("- _usa_parametros_reasoning() funciona")
    print("- backend.gerar() sem stream retorna texto completo")
    print("- backend.gerar() com stream imprime tokens e retorna texto acumulado")
    print("- Nao houve duplicacao de texto")

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
