# GPT-5 / o-series — contrato de API diferente
> Modelos de reasoning quebram a chamada padrão da OpenAI

Entry: `chat_openai_memoria.py:enviar_mensagem()` → chamada em (L418-432)
Gate: `chat_openai_memoria.py:_usa_parametros_reasoning()` — detecta por prefixo `gpt-5`, `o1`, `o3`, `o4`

Diferenças vs modelos clássicos (gpt-4o, gpt-3.5, gpt-4):
- `max_tokens` → REJEITADO. Usar `max_completion_tokens` (erro 400 `unsupported_parameter`)
- `temperature` ≠ 1 → REJEITADO. Só aceita o padrão (1). App omite o param nesses modelos.
- `max_completion_tokens` inclui tokens de raciocínio internos → valor baixo (ex.: 1000) pode devolver `content` vazio. Subir p/ 2000+.

Construção dos params é condicional no dict `parametros` antes de `client.chat.completions.create(**parametros)`.

Config: `env.example` (L13-33) documenta as 3 notas. Disparado quando `.env` muda `OPENAI_MODEL` p/ gpt-5*.

Fonte: community.openai.com/t/temperature-in-gpt-5-models/1337133

Updated: 2026-06-18
