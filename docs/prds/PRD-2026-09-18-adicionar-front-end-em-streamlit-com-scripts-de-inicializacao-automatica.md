# PRD — Adicionar front-end em Streamlit com scripts de inicialização automática

- **Data:** 2026-09-18
- **Sistema:** exemplo_chat_memoria — Chat OpenAI com memória e persistência SQLite
- **Status:** Documento funcional para aprovação (pré-plano técnico)
- **Autor:** Agente de especificação (automação)

---

## 1. Contexto

O projeto é uma aplicação educacional em Python que demonstra memória
conversacional com a API OpenAI. Toda a lógica reutilizável está concentrada na
classe `ChatComMemoria` (`chat_openai_memoria.py`), que carrega configuração via
`.env` (`load_dotenv`), valida credenciais/parâmetros (`OPENAI_API_KEY`,
`OPENAI_MODEL`, `OPENAI_TEMPERATURE`, `OPENAI_MAX_TOKENS` e opcionais como
`JANELA_MAX`, `OPENAI_STREAM`, `PERSISTENCIA_SQLITE`) e expõe métodos como
`enviar_mensagem()`, `definir_personalidade()`, `limpar_historico()`,
`exportar_conversa()` e `contar_tokens_aproximado()`. A persistência opcional em
SQLite fica em `GerenciadorPersistencia` (`persistencia.py`), ativada apenas quando
`PERSISTENCIA_SQLITE=true`.

Atualmente a única forma de interação é o terminal: `chat_interativo()` lê
`input()` em laço e trata comandos `/limpar`, `/historico`, `/tokens`, `/debug`,
`/grafico`, `/exportar`, `/threads`, `/retomar<id>`, `/excluir<id>`, `/sair`. Toda
a saída assume terminal (colorama, ANSI, caixas ASCII). A inicialização em Windows
é feita por `iniciar_chat.bat`, que ativa `.venv` e roda o script — sem instalar
dependências e sem equivalente `.sh`.

## 2. Problema

Não existe interface visual. Usuários que preferem uma GUI simples precisam operar
via terminal, o que reduz a acessibilidade da demonstração em contexto de aula. Além
disso, a inicialização só é automatizada em Windows, sem opção para Linux/Mac.

## 3. Objetivo

Disponibilizar uma interface web simples em **Streamlit** como forma **alternativa**
(não substituta) de uso do chat, reaproveitando a lógica já existente em
`ChatComMemoria`/`GerenciadorPersistencia`, e automatizar sua inicialização com
scripts para Windows (`.bat`) e Linux/Mac (`.sh`).

## 4. Escopo

- Nova aplicação Streamlit (novo módulo, ex.: `app_streamlit.py`) que **importa e
  reutiliza** `ChatComMemoria` e, condicionalmente, `GerenciadorPersistencia`, sem
  duplicar regra de negócio.
- Reuso do mesmo `.env` e das mesmas variáveis de configuração já existentes.
- Chat conversacional: campo de entrada, envio de mensagem e exibição do histórico
  da sessão (turnos usuário/assistente) na tela.
- Preservação de estado entre interações via `st.session_state` (instância de
  `ChatComMemoria`, `thread_id` e histórico), dado que o Streamlit reexecuta o
  script a cada evento.
- Ações equivalentes aos comandos essenciais do terminal expostas como controles de
  UI, reaproveitando os métodos existentes: **limpar conversa**, **exibir contagem
  de tokens** (via `contar_tokens_aproximado()`/dados de turno) e **exportar
  conversa**. Quando `PERSISTENCIA_SQLITE=true`, também **listar/retomar/excluir
  threads**.
- Tratamento amigável de erros da API (mensagem clara sem vazar detalhes internos).
- Script `.bat` (Windows) e `.sh` (Linux/Mac) que ativam o `.venv` (padrão do
  `iniciar_chat.bat` atual) e executam `streamlit run` sem comandos manuais
  adicionais.
- Inclusão de `streamlit` em `requirements.txt`.
- Atualização mínima de documentação (`README.md`/`env.example`) indicando a nova
  forma de uso.

## 5. Fora de escopo

- Redesign visual elaborado, temas customizados ou componentes avançados de UI.
- Autenticação, controle de acesso multiusuário ou deploy em servidor/nuvem.
- Alteração da CLI existente ou remoção de qualquer funcionalidade atual.
- Mudanças na modelagem/esquema do SQLite ou na lógica de negócio de
  `ChatComMemoria`.
- Auto-instalação obrigatória de dependências pelos scripts (será apenas ativação do
  ambiente; instalação permanece responsabilidade do usuário/`requirements.txt`).
- Reescrita do modo *streaming* token-a-token para renderização incremental na web
  (ver restrições).

## 6. Requisitos funcionais

- **RF1** — Fornecer uma aplicação Streamlit funcional integrada ao projeto, iniciável
  por `streamlit run`.
- **RF2** — A UI deve permitir enviar uma mensagem e receber a resposta do assistente,
  chamando `ChatComMemoria.enviar_mensagem()` e exibindo o **valor de retorno** (sem
  depender de saída em stdout/ANSI).
- **RF3** — Exibir o histórico da conversa da sessão em ordem, distinguindo mensagens
  do usuário e do assistente.
- **RF4** — Persistir o estado da sessão (instância de `ChatComMemoria`, `thread_id`,
  histórico) em `st.session_state`, mantendo a continuidade entre interações.
- **RF5** — Disponibilizar ação de **limpar conversa** reaproveitando
  `limpar_historico()`.
- **RF6** — Exibir informação de **tokens** da conversa (estimativa e/ou tokens reais de
  turno já disponíveis), reaproveitando os métodos existentes.
- **RF7** — Disponibilizar ação de **exportar conversa** reaproveitando
  `exportar_conversa()`.
- **RF8** — Quando `PERSISTENCIA_SQLITE=true`, permitir **listar**, **retomar** e
  **excluir** threads, reaproveitando `GerenciadorPersistencia`; quando desativada,
  ocultar/desabilitar essas ações.
- **RF9** — Capturar exceções levantadas por `enviar_mensagem()` e exibir mensagem de
  erro amigável na tela, sem expor detalhes sensíveis (ex.: chave, stack trace).
- **RF10** — Reutilizar o mesmo `.env`/variáveis já validadas por `ChatComMemoria`, sem
  novo mecanismo de configuração; a `OPENAI_API_KEY` permanece exclusivamente no
  servidor, nunca no browser.
- **RF11** — Fornecer `iniciar_streamlit.bat` (Windows) que ativa `.venv` e roda
  `streamlit run <app>`, tratando ausência do `.venv` com mensagem clara (padrão do
  `iniciar_chat.bat`).
- **RF12** — Fornecer `iniciar_streamlit.sh` (Linux/Mac) equivalente, com permissão de
  execução e ativação de `.venv`.
- **RF13** — Adicionar `streamlit` ao `requirements.txt`.

## 7. Critérios de aceite

- **CA1** — Existe uma aplicação Streamlit funcional integrada ao projeto que sobe via
  `streamlit run` e permite conversar com o assistente.
- **CA2** — A interface permite usar as funcionalidades principais: enviar/receber
  mensagens, ver histórico, limpar conversa, ver tokens e exportar; e, com persistência
  ativada, listar/retomar/excluir threads.
- **CA3** — Existe `iniciar_streamlit.bat` que inicia o front-end no Windows sem
  comandos manuais adicionais.
- **CA4** — Existe `iniciar_streamlit.sh` que inicia o front-end no Linux/Mac sem
  comandos manuais adicionais.
- **CA5** — Ambos os scripts ativam o `.venv` e executam corretamente a aplicação
  Streamlit; na ausência do `.venv`, exibem mensagem de erro clara em vez de falhar
  silenciosamente.
- **CA6** — O estado da conversa persiste entre interações da mesma sessão (não é
  reiniciado a cada mensagem).
- **CA7** — Erros da API são exibidos de forma amigável, sem vazar chave nem detalhes
  internos.
- **CA8** — A CLI existente e a API pública de `ChatComMemoria` permanecem inalteradas
  (os testes atuais, incl. `tests/test_integracao_chat.py`, continuam válidos).

## 8. Impactos / restrições técnicas relevantes

- **Estado por sessão:** o Streamlit reexecuta o script a cada evento; `ChatComMemoria`
  e `GerenciadorPersistencia` devem viver em `st.session_state` para não perder
  histórico/`thread_id`.
- **Streaming incompatível com stdout:** `enviar_mensagem()` no modo *stream* imprime
  token-a-token via `print`, o que não renderiza na web. Recomenda-se operar com
  `OPENAI_STREAM` desligado no front-end (consumindo o valor de retorno) e tratar o
  streaming incremental como melhoria futura, evitando refatorar o laço de *chunks*.
- **Saída acoplada a terminal:** métodos como `mostrar_historico()`, `debug_memoria()`
  e `grafico_tokens()` escrevem no terminal com ANSI/colorama; a UI **não** deve
  reutilizá-los diretamente — deve montar a visualização a partir dos dados
  (histórico/tokens) já mantidos pela classe.
- **Compatibilidade da API interna:** manter a assinatura de instanciação de
  `ChatComMemoria` (incl. parâmetro `gerenciador=...`) para não quebrar testes/uso
  programático existentes.
- **Configuração:** nova dependência `streamlit` em `requirements.txt`; reuso integral
  do `.env` (que está no `.gitignore`).
- **Scripts:** seguir o padrão do `iniciar_chat.bat` (ativar `.venv`, `cd` para o
  diretório do script); apenas iniciar a aplicação — sem auto-instalação obrigatória de
  dependências (decisão default; pode-se opcionalmente validar presença do `.venv`).

## 9. Riscos e pontos de atenção

- **Exposição em rede / custo:** `streamlit run` por padrão faz *bind* acessível na
  rede e não tem autenticação; em rede compartilhada de sala, terceiros poderiam
  consumir a `OPENAI_API_KEY` e gerar custo. **Mitigação:** iniciar com bind local
  (`--server.address=localhost`) por padrão nos scripts e/ou alertar no README. A chave
  permanece server-side (não vai ao browser).
- **Vazamento de erros:** respostas de exceção da API contêm detalhes; a UI deve
  sanitizar antes de exibir.
- **Divergência de comportamento CLI × UI:** por reaproveitar os métodos, comportamentos
  específicos do terminal (comandos `/...`, ANSI) não têm paridade automática; a UI
  reimplementa apenas os equivalentes essenciais definidos no escopo.
- **Dependência do ambiente:** ausência de `.venv` ou de dependências instaladas fará os
  scripts falharem; tratar com mensagem clara.
- **Decisões de implementação com defaults sensatos** (não bloqueiam aprovação): porta
  padrão do Streamlit, nome do módulo/scripts e granularidade da exibição de tokens
  ficam a cargo do plano técnico.
