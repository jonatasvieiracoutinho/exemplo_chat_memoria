# Persistência SQLite (threads)
> Opcional via `.env`; CUIDADO com a ordem do load_dotenv()

Flag: `PERSISTENCIA_SQLITE` no `.env` (padrão false). Lida em `chat_openai_memoria.py:chat_interativo()` (L831).
Módulo: `persistencia.py:GerenciadorPersistencia` — abre/cria o banco `chat_memoria.db` no `__init__` (tabelas `threads` + `mensagens`, FK ON DELETE CASCADE). Ignorado no `.gitignore` (L29).
Comandos extras só aparecem quando ativa: `/threads`, `/retomar <id>`, `/excluir <id>` (L854-859). Carga do histórico inicial via `_selecionar_thread()`; salvamento em `enviar_mensagem` (L429-436), título da thread = 1ª msg do user.

GOTCHA (corrigido 2026-06-25): `chat_interativo()` lê `PERSISTENCIA_SQLITE` em L831 ANTES de instanciar `ChatComMemoria`. O `load_dotenv()` original morava só dentro de `ChatComMemoria.__init__` (L125), que roda só em L866 — depois da leitura. Resultado: a flag caía no default "false", banco nunca criado e comandos de thread sumiam, mesmo com `.env` correto. Demais vars (JANELA_MAX, OPENAI_STREAM…) não sofriam por serem lidas dentro do `__init__`, pós load_dotenv.
Fix: `load_dotenv()` adicionado no NÍVEL DE MÓDULO logo após os imports (idempotente, não sobrescreve ambiente; o do `__init__` ficou redundante mas inofensivo). Regra geral: qualquer `os.getenv()` fora de `__init__` depende desse load no topo.

Updated: 2026-06-25
