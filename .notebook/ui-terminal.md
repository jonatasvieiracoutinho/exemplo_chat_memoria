# Camada visual do terminal (cores e caixas)

> Helpers de UI no topo de `chat_openai_memoria.py` — reusar, não recriar

Entry: `chat_openai_memoria.py` (L15-105) — bloco antes de `class ChatComMemoria`.

Componentes:
- `_Paleta`/`_C` — paleta semântica (USUARIO=ciano, ASSISTENTE=verde, SISTEMA=magenta, ERRO=vermelho, etc.) e `LARGURA=70`.
- `pintar(texto, cor)` — envolve com ANSI e SEMPRE faz reset (`colorama.init(autoreset=False)`, reset manual).
- `cabecalho(titulo)` — caixa de título 3 linhas centralizada; padding medido no texto SEM cor → bordas sempre com 70 colunas.
- `regua()`, `item(rotulo, valor)`, `cor_por_nivel(emoji)` — separador, linha "• rótulo: valor", e mapa emoji→cor dos alertas de token.

colorama (>=0.4.6, agora em `requirements.txt`) traduz ANSI no Windows. Import com **degradação graciosa**: ausente → `Fore=Style=_SemCor()` e toda cor vira `""` (chat roda sem cor, nada quebra).

GOTCHA (acoplamento) — cor vai SÓ para o terminal:
- Os gravadores de ARQUIVO continuam texto puro, sem `pintar`/`_C.`: `_inicializar_log()`, `_registrar_log()`, `_registrar_interacao()` (log de debug) e o `f.write` de `exportar_conversa()`. Colorir esses poluiria os arquivos com escapes ANSI.
- Corpo das respostas NÃO é colorido — só rótulos/molduras/alertas. Evita acoplar cor ao streaming token a token. Ver [[streaming-output]].

Render correto depende de stdout UTF-8 (caixas/emoji). Console interativo do Windows usa WindowsConsoleIO (UTF-8) — ok; stdout REDIRECIONADO cai p/ cp1252 e quebra box-drawing (artefato de teste em pipe, não no uso real).

Updated: 2026-06-18
