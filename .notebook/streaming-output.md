# Streaming da saída
> Resposta token a token, opcional via .env

Entry: `chat_openai_memoria.py:enviar_mensagem()` — branch `if self.stream:`
Flag: `self.stream` carregada de `OPENAI_STREAM` no `.env` (padrão false), mesmo padrão de `MODO_DEBUG`. Construtor aceita `stream=` como override.

Contrato de impressão (CUIDADO — acoplamento):
- Em streaming, `enviar_mensagem()` IMPRIME a resposta (print delta a delta) E retorna o texto acumulado.
- Os chamadores NÃO podem reimprimir o retorno nesse modo, senão duplica.
- Chamadores tratam isso: `chat_interativo()` (L707+) e `exemplo_programatico()` (L749+) imprimem o prefixo ("Assistente: "), chamam, e só dão `print("\n")` quando `chat.stream`.

Iteração: `for chunk in client.chat.completions.create(..., stream=True)` → `chunk.choices[0].delta.content` (guard p/ `choices` vazio e delta None). Padrão SDK openai v1.

Pós-processamento (histórico, sliding window, alertas, log) roda igual com o texto acumulado.

Nota reasoning (gpt-5*/o-series): só os tokens finais saem no stream, não o raciocínio interno. Ver [[gpt5-reasoning-api]].

Updated: 2026-06-18
