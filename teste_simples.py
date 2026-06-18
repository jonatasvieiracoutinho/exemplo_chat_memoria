#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Teste simples sem cores para evitar problemas de encoding no Windows"""

import os
import sys
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Desabilitar colorama antes de importar chat_openai_memoria
os.environ["NO_COLOR"] = "1"

from chat_openai_memoria import ChatComMemoria

print("\n--- TESTE DE FASE 1: Backend OpenAI ---\n")
print("Inicializando ChatComMemoria...")

try:
    chat = ChatComMemoria()
    print("\nCHAT INICIALIZADO COM SUCESSO!")
    print(f"Modelo: {chat.modelo}")
    print(f"Stream: {chat.stream}")
    print(f"Backend: {type(chat.backend).__name__}")

    chat.definir_personalidade("Responda em uma frase curta e concisa.")

    print("\nEnviando primeira mensagem...")
    resposta1 = chat.enviar_mensagem("Qual eh o maior planeta do sistema solar?")
    print(f"\n[Resposta recebida com {len(resposta1)} caracteres]")

    print("\nEnviando segunda mensagem (com contexto)...")
    resposta2 = chat.enviar_mensagem("Qual eh sua distancia do sol?")
    print(f"\n[Resposta recebida com {len(resposta2)} caracteres]")

    print("\nEnviando terceira mensagem (com contexto)...")
    resposta3 = chat.enviar_mensagem("Quantas luas ele tem?")
    print(f"\n[Resposta recebida com {len(resposta3)} caracteres]")

    print("\n--- TESTE CONCLUÍDO COM SUCESSO ---")
    print(f"Total de mensagens no historico: {len(chat.historico)}")
    print(f"Tokens aproximados: {chat.contar_tokens_aproximado()}")

except Exception as e:
    print(f"\nERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
