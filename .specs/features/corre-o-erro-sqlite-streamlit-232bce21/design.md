# Continuidade de conversas persistidas na interface web — Design

## Causa raiz

`GerenciadorPersistencia.__init__` abre uma única conexão SQLite (`self.conn`) e a
reutiliza em todas as operações. O Streamlit guarda o gerenciador em
`st.session_state` e o reaproveita entre reruns; um rerun pode rodar em outra
thread da que criou a conexão. O SQLite (padrão `check_same_thread=True`) rejeita
isso com `sqlite3.ProgrammingError: SQLite objects created in a thread can only be
used in that same thread`, bloqueando o primeiro envio após a renderização.

Evidência reproduzida: uma conexão criada na thread principal e usada em outra
thread levanta `ProgrammingError` (`persistencia.py:10`, reuso em cada método).

## Decisão de arquitetura

Trocar a conexão de vida longa por **conexão curta por operação** no modo arquivo.
Um `@contextmanager` privado (`_conexao`) abre uma conexão nova na thread chamadora,
aplica `row_factory = sqlite3.Row` e `PRAGMA foreign_keys = ON`, faz `commit` no
sucesso e fecha no `finally`. Cada método público executa todo o seu trabalho dentro
de um único `with self._conexao() as conn:`, preservando a atomicidade de
`salvar_turno` (SELECT MAX(ordem) + INSERT na mesma conexão).

**Exceção para banco em memória.** Um banco `:memory:` (ou `mode=memory`) só existe
enquanto sua conexão vive; conexões distintas veem bancos vazios diferentes. Esse modo
é usado apenas pela suíte de testes, em thread única. Nele o gerenciador mantém **uma
conexão compartilhada** (`self.conn`), e `_conexao` a reaproveita sem fechar. Assim os
consumidores em `:memory:` seguem inalterados (RF-07).

`fechar()` fecha a conexão em memória e é no-op no modo arquivo (não há conexão retida).
`__init__` cria/migra o schema uma vez (conexão temporária no modo arquivo).

## Componentes afetados

| Componente | Mudança |
| ---------- | ------- |
| `persistencia.py` | Introduz `_conexao`/modo dual; métodos públicos passam a usar conexão por operação. Assinaturas públicas inalteradas. |
| `app_streamlit.py` / `app_streamlit_core.py` | Nenhuma. Já guardam o gerenciador em `st.session_state` e chamam apenas métodos públicos; a correção do lifecycle de conexão basta. |
| `chat_openai_memoria.py` (terminal) | Nenhuma. Roda em thread única; conexão por operação funciona; `fechar()` segue válido. |
| `tests/test_persistencia.py` | Adapta o teste de migração (lê `.conn` em modo arquivo) para consultar via conexão nova; adiciona teste de caracteres especiais. |

## Verificação

- **Data-access** (`tests/test_persistencia.py`): caminhos-chave, migração idempotente
  sobre banco pré-existente, caracteres especiais, e uso da conexão a partir de outra
  thread sem `ProgrammingError`.
- **Continuidade web** (novo `tests/test_streamlit_rerun_persistencia.py`): rerun em
  thread distinta com OpenAI mockado e banco temporário isolado — renderização inicial
  + primeiro envio; retomar/excluir após rerun; persistência desativada sem arquivo.
- **Regressão terminal/CLI**: `tests/test_cli_persistencia.py` e
  `tests/test_integracao_chat.py` permanecem verdes (modo `:memory:` e arquivo).
