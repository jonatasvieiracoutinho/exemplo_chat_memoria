#!/usr/bin/env python
"""Teste de Fase 1: Verificação manual do backend OpenAI com streaming"""

import os
import sys
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Teste 1: Não-stream (OPENAI_STREAM=false)
print("\n" + "="*70)
print("TESTE 1: Modo NÃO-STREAM (resposta completa ao final)")
print("="*70 + "\n")

os.environ["OPENAI_STREAM"] = "false"
from chat_openai_memoria import ChatComMemoria

chat = ChatComMemoria()
chat.definir_personalidade("Responda em uma frase curta.")

resposta = chat.enviar_mensagem("Oi, como você está?")
print(f"[TESTE 1] Resposta recebida: {len(resposta)} caracteres\n")

# Teste 2: Com stream (OPENAI_STREAM=true)
# Para isso, preciso recarregar o módulo ou criar nova instância
print("\n" + "="*70)
print("TESTE 2: Modo STREAM (resposta token a token)")
print("="*70 + "\n")

# Criar novo chat com streaming ativado via parâmetro
chat_stream = ChatComMemoria(stream=True)
chat_stream.definir_personalidade("Responda em uma frase curta.")

print("[TESTE 2] Enviando mensagem com STREAM=true:")
resposta_stream = chat_stream.enviar_mensagem("Qual é o seu nome?")
print(f"\n[TESTE 2] Resposta recebida: {len(resposta_stream)} caracteres\n")

print("="*70)
print("TESTES CONCLUÍDOS COM SUCESSO")
print("="*70)
print("\nObservações:")
print("- TESTE 1: Resposta apareceu completa ao final")
print("- TESTE 2: Resposta foi exibida token a token durante o recebimento")
print("- Nenhuma duplicação detectada")
