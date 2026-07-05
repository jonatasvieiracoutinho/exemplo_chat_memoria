# Persistência SQLite (threads)
> Opcional via `.env`; CUIDADO com a ordem do load_dotenv()

Flag: `PERSISTENCIA_SQLITE` no `.env` (padrão false). Lida em `chat_openai_memoria.py:chat_interativo()` (L831).
Módulo: `persistencia.py:GerenciadorPersistencia` — abre/cria o banco `chat_memoria.db` no `__init__` (tabelas `threads` + `mensagens`, FK ON DELETE CASCADE). Ignorado no `.gitignore` (L29).
Comandos extras só aparecem quando ativa: `/threads`, `/retomar <id>`, `/excluir <id>` (L854-859). Carga do histórico inicial via `_selecionar_thread()`; salvamento em `enviar_mensagem` (L429-436), título da thread = 1ª msg do user.

GOTCHA (corrigido 2026-06-25): `chat_interativo()` lê `PERSISTENCIA_SQLITE` em L831 ANTES de instanciar `ChatComMemoria`. O `load_dotenv()` original morava só dentro de `ChatComMemoria.__init__` (L125), que roda só em L866 — depois da leitura. Resultado: a flag caía no default "false", banco nunca criado e comandos de thread sumiam, mesmo com `.env` correto. Demais vars (JANELA_MAX, OPENAI_STREAM…) não sofriam por serem lidas dentro do `__init__`, pós load_dotenv.
Fix: `load_dotenv()` adicionado no NÍVEL DE MÓDULO logo após os imports (idempotente, não sobrescreve ambiente; o do `__init__` ficou redundante mas inofensivo). Regra geral: qualquer `os.getenv()` fora de `__init__` depende desse load no topo.

## Contagem real de tokens por turno (`turnos`)

Desde 2026-07-05, `GerenciadorPersistencia` também persiste a contagem **real** de
tokens (vinda do campo `usage` da resposta da OpenAI) em uma tabela `turnos`,
separada de `mensagens`:

- Schema (`persistencia.py:_migrar_schema`): `turnos(id, thread_id, ordem,
  prompt_tokens, completion_tokens, total_tokens, criado_em)`, FK para
  `threads(id)` com `ON DELETE CASCADE`. Colunas de tokens aceitam `NULL`.
- Migração idempotente: `_migrar_schema()` roda sempre após `_criar_tabelas()`
  (via `CREATE TABLE IF NOT EXISTS`), então bancos `chat_memoria.db` antigos
  (só com `threads`/`mensagens`) ganham a tabela `turnos` automaticamente na
  próxima abertura, sem perder dados.
- API: `salvar_turno(thread_id, prompt_tokens=None, completion_tokens=None,
  total_tokens=None)` grava um turno com `ordem` sequencial por thread;
  `carregar_turnos(thread_id)` lista os turnos em ordem; `total_tokens_thread(thread_id)`
  soma os tokens da thread (ignora `NULL` via `COALESCE`).
- Captura em `chat_openai_memoria.py:enviar_mensagem`: `_extrair_uso_tokens(usage)`
  normaliza o objeto `usage` da API em `(prompt, completion, total)`, retornando
  `None` em qualquer campo ausente/não-inteiro — nunca lança exceção. Cobre tanto
  o ramo não-streaming (`resposta.usage`) quanto o streaming, que precisa de
  `stream_options={"include_usage": True}` para receber um chunk final com `usage`
  (chunk sem `choices`, tratado pelo `continue` existente).
- O turno é gravado logo depois de `adicionar_mensagem("assistant", ...)`, dentro
  do mesmo fluxo — só quando há `gerenciador` e `thread_id`. Qualquer exceção em
  `salvar_turno` é capturada e apenas logada em modo debug; nunca interrompe a
  conversa (tolerância a Ollama/LM Studio/Azure sem `usage`, ou streaming sem
  `include_usage`).
- A estimativa `contar_tokens_aproximado()` (sliding window, alertas, `/tokens`)
  não foi alterada — os tokens reais são um dado adicional, não um substituto.

Updated: 2026-07-05
