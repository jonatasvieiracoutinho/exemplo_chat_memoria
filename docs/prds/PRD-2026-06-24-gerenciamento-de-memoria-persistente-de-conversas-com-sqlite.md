# PRD — Gerenciamento de Memória Persistente de Conversas com SQLite

**Status:** Aprovado  
**Data:** 2026-06-24  
**Repositório:** `jonatasvieiracoutinho/exemplo_chat_memoria`

---

## 1. Contexto

O sistema `exemplo_chat_memoria` é um chat interativo via terminal que utiliza a API da OpenAI com suporte a janela deslizante de contexto. Toda a memória das conversas existe exclusivamente em memória RAM durante a execução — ao encerrar o processo, o histórico é perdido. A única forma de preservar conteúdo hoje é via exportação manual para arquivo de texto (`/exportar`).

O sistema não possui nenhum conceito de "thread" ou "sessão persistente". Cada execução inicia com histórico zerado. O CLI interativo é baseado em comandos slash (ex.: `/limpar`, `/historico`, `/exportar`) reconhecidos dentro de um loop `while True`.

O banco SQLite3 já está disponível na stdlib do Python, sem necessidade de dependências externas adicionais.

---

## 2. Problema

Usuários que utilizam o chat de forma recorrente perdem todo o contexto das conversas anteriores ao encerrar o processo. Não há como retomar uma conversa de onde parou, consultar histórico de sessões passadas, ou organizar conversas por tópico. Isso reduz significativamente a utilidade do sistema para casos de uso contínuos ou de longo prazo.

---

## 3. Objetivo

Adicionar persistência local das conversas utilizando SQLite, com ativação controlada por variável de ambiente, e expor no CLI interativo os comandos para listar, selecionar e excluir threads de chat armazenadas. O uso da funcionalidade deve ser completamente opcional e não deve alterar o comportamento atual quando desabilitado.

---

## 4. Escopo

- Persistência das mensagens de cada conversa em banco SQLite local.
- Controle de ativação/desativação da persistência via variável de ambiente.
- Identificação de cada conversa como uma "thread", com título derivado da primeira mensagem do usuário.
- Comandos no CLI interativo para: listar threads existentes, selecionar (retomar) uma thread, e excluir uma thread.
- Carregamento do histórico completo ao retomar uma thread, com aplicação da janela deslizante em memória sem deletar mensagens do banco.
- Identificação numérica sequencial das threads no CLI (mais amigável que UUID para uso manual).

---

## 5. Fora de Escopo

- Interface gráfica ou web para gerenciamento de threads.
- Sincronização ou backup remoto do banco SQLite.
- Exportação do banco para outros formatos além do existente (`/exportar` continua independente).
- Busca por conteúdo dentro das threads.
- Compartilhamento de threads entre usuários ou processos.
- Paginação da listagem de threads (para v1, exibir todas as threads).
- Migração de dados de exportações de texto existentes para o banco.
- Edição de mensagens já salvas.
- Exclusão lógica (soft delete) — a exclusão será física (hard delete) na v1.
- Compressão ou criptografia do banco SQLite.

---

## 6. Requisitos Funcionais

### RF-01 — Ativação por variável de ambiente

A persistência deve ser controlada pela variável de ambiente `PERSISTENCIA_SQLITE`. Quando definida como `"true"`, o sistema deve utilizar o banco SQLite. Quando ausente ou com qualquer outro valor, o sistema deve operar exatamente como hoje, sem qualquer interação com SQLite.

O padrão de leitura deve seguir a convenção já estabelecida no projeto:
```python
os.getenv("PERSISTENCIA_SQLITE", "false").lower() == "true"
```

### RF-02 — Banco de dados SQLite local

Quando a persistência estiver ativada, o sistema deve criar (ou abrir) um arquivo SQLite no diretório do projeto, com nome padrão `chat_memoria.db`. O banco deve conter ao menos duas tabelas:

- **threads**: armazena metadados de cada conversa (id inteiro autoincrement, título, timestamp de criação, timestamp da última atualização).
- **mensagens**: armazena cada mensagem (id, thread_id como FK, role, content, posição/ordem de inserção).

O banco deve ser criado automaticamente na primeira execução com persistência ativada.

### RF-03 — Seleção de thread antes do loop principal

Quando a persistência estiver ativada, antes de iniciar o loop interativo, o sistema deve:

1. Exibir a lista de threads existentes (ID, título truncado, data/hora, contagem de mensagens).
2. Oferecer ao usuário a opção de selecionar uma thread existente (pelo ID numérico) ou iniciar uma nova conversa.
3. Só então instanciar `ChatComMemoria` — com o histórico carregado da thread selecionada, ou com histórico vazio para nova thread.

### RF-04 — Persistência automática de mensagens

Quando uma thread estiver ativa e a persistência estiver ativada, cada mensagem adicionada via `adicionar_mensagem()` deve ser salva imediatamente no banco SQLite (operação síncrona). O timestamp da thread deve ser atualizado a cada nova mensagem.

### RF-05 — Título automático da thread

O título de uma nova thread deve ser gerado a partir da primeira mensagem do usuário, truncada em 60 caracteres. Se a primeira mensagem for vazia ou não existir, usar `"Conversa sem título"` como fallback.

### RF-06 — Comando `/threads` no CLI

Dentro do loop interativo, o comando `/threads` deve exibir a lista de todas as threads armazenadas. Este comando deve estar disponível apenas quando a persistência estiver ativada; caso contrário, exibir mensagem informando que a persistência está desabilitada.

### RF-07 — Comando `/retomar` no CLI

O comando `/retomar <id>` deve permitir ao usuário trocar para outra thread sem encerrar o processo. O histórico em memória deve ser substituído pelo histórico completo da thread selecionada. A janela deslizante deve ser aplicada em memória após o carregamento.

### RF-08 — Comando `/excluir` no CLI

O comando `/excluir <id>` deve remover permanentemente (exclusão física) a thread especificada e todas as suas mensagens do banco SQLite. Antes de executar, o sistema deve solicitar confirmação do usuário (`s/n`). Se a thread excluída for a thread atualmente ativa, o sistema deve iniciar uma nova conversa automaticamente.

### RF-09 — Carregamento de histórico ao retomar thread

Ao retomar uma thread, o histórico completo armazenado no banco deve ser carregado para `self.historico`. A janela deslizante (`_aplicar_janela_deslizante`) deve ser aplicada sobre o histórico em memória, sem deletar mensagens do banco — a base SQLite preserva o histórico completo; a janela opera apenas sobre o contexto enviado à API.

### RF-10 — Sem efeito colateral quando persistência está desabilitada

Com `PERSISTENCIA_SQLITE` não definida ou diferente de `"true"`, o sistema não deve instanciar nenhuma conexão SQLite, não deve criar arquivo `.db`, e o fluxo de execução deve ser idêntico ao comportamento atual.

---

## 7. Critérios de Aceite

| # | Critério | Verificação |
|---|----------|-------------|
| CA-01 | Com `PERSISTENCIA_SQLITE=true`, ao iniciar o sistema exibe a lista de threads e aguarda seleção antes do loop. | Execução com env var ativa. |
| CA-02 | Com `PERSISTENCIA_SQLITE` ausente ou `false`, o sistema inicia normalmente sem tela de seleção. | Execução sem env var. |
| CA-03 | Ao iniciar nova conversa com persistência ativa, o arquivo `chat_memoria.db` é criado se não existir. | Verificar existência do arquivo após primeira execução. |
| CA-04 | Cada mensagem enviada aparece salva no banco imediatamente após ser adicionada. | Consulta direta ao SQLite após envio de mensagem. |
| CA-05 | O título da thread é gerado a partir dos primeiros 60 caracteres da primeira mensagem do usuário. | Conferir coluna `titulo` na tabela `threads`. |
| CA-06 | `/threads` exibe ID, título, data/hora e contagem de mensagens para cada thread armazenada. | Executar comando e verificar saída. |
| CA-07 | `/retomar <id>` carrega o histórico da thread corretamente e a conversa continua a partir desse contexto. | Retomar thread existente e verificar que o modelo responde com contexto do histórico anterior. |
| CA-08 | `/excluir <id>` solicita confirmação e, após confirmação, remove thread e mensagens do banco. | Verificar que thread e mensagens não existem mais no SQLite após exclusão confirmada. |
| CA-09 | `/excluir <id>` com resposta `n` na confirmação não remove nada. | Verificar que dados permanecem após cancelamento. |
| CA-10 | Ao excluir a thread ativa, o sistema inicia nova conversa automaticamente sem encerrar o processo. | Excluir thread em uso e verificar continuidade do CLI. |
| CA-11 | O histórico completo é preservado no banco mesmo quando a janela deslizante remove mensagens antigas da memória. | Verificar contagem de mensagens no banco versus `self.historico` após atingir limite da janela. |
| CA-12 | Com persistência desabilitada, o arquivo `chat_memoria.db` não é criado. | Verificar ausência do arquivo após execução sem env var. |

---

## 8. Impactos e Restrições Técnicas

### 8.1 Integração com a classe `ChatComMemoria`

A classe recebe parâmetro adicional `thread_id=None` no `__init__`. Quando fornecido, o histórico é carregado do banco antes de qualquer interação. O método `adicionar_mensagem()` passa a ter efeito colateral de escrita no SQLite quando persistência está ativa. A inicialização (`__init__`) já imprime informações na tela — a lógica de seleção de thread deve ocorrer **antes** da instanciação da classe para evitar output prematuro.

### 8.2 Janela deslizante e banco de dados

A janela deslizante (`_aplicar_janela_deslizante`) opera **exclusivamente em memória** e não deve modificar o banco SQLite. O banco é a fonte de verdade do histórico completo. Ao retomar uma thread, o histórico completo é carregado e a janela é aplicada em memória para montar o contexto da API.

### 8.3 Conexão com SQLite

A conexão deve ser aberta uma vez durante a sessão e fechada ao encerrar. Dado que o sistema é single-threaded, não há necessidade de pool de conexões ou controle de concorrência. Usar `sqlite3.connect()` da stdlib com `check_same_thread=False` não é necessário neste cenário.

### 8.4 CLI sem framework de parsing

O sistema usa reconhecimento manual de comandos via `if/elif` sobre a string de entrada. Os novos comandos (`/threads`, `/retomar <id>`, `/excluir <id>`) devem seguir o mesmo padrão. Para comandos com argumento (`/retomar 3`), usar `mensagem.split()` para extrair o ID e validar se é inteiro.

### 8.5 Compatibilidade com funcionalidades existentes

Os comandos existentes (`/exportar`, `/historico`, `/limpar`, etc.) não devem ser alterados em comportamento. O `/limpar` zera `self.historico` em memória mas **não deve deletar dados do banco** — essa ação continua a gravar novas mensagens na thread ativa. O `/exportar` continua exportando o histórico em memória para arquivo de texto independentemente do SQLite.

### 8.6 Variável de ambiente e `.env`

A nova variável `PERSISTENCIA_SQLITE` deve ser documentada no arquivo `env.example` existente, seguindo o padrão das demais variáveis opcionais.

---

## 9. Riscos e Pontos de Atenção

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|---------------|---------|-----------|
| R-01 | Corrupção do banco SQLite por encerramento abrupto (Ctrl+C sem `finally`) | Média | Alto | Garantir fechamento da conexão em bloco `finally` ou via `atexit`. |
| R-02 | `/limpar` em sessão com persistência ativa apaga histórico em memória mas usuário espera apagar também do banco | Alta | Médio | Definir claramente no comportamento: `/limpar` opera só em memória; `/excluir` remove do banco. Exibir mensagem explicativa ao usar `/limpar` com persistência ativa. |
| R-03 | Thread com histórico muito longo (milhares de mensagens) pode tornar o carregamento lento | Baixa | Médio | Para v1, aceitar a limitação. Paginação ou carregamento parcial são fora de escopo. |
| R-04 | ID numérico de thread pode conflitar com expectativa do usuário após exclusões (IDs não sequenciais) | Baixa | Baixo | Usar autoincrement do SQLite e exibir sempre o ID real. Documentar que IDs não são reordenados após exclusões. |
| R-05 | Arquivo `chat_memoria.db` acidentalmente comitado no repositório | Alta | Médio | Adicionar `chat_memoria.db` ao `.gitignore` como parte desta entrega. |
| R-06 | O `__init__` de `ChatComMemoria` faz print antes da seleção de thread estar definida | Alta | Baixo | Separar a lógica de seleção de thread em função chamada antes de instanciar a classe. |
| R-07 | Exclusão física de thread sem undo pode causar perda de dados acidental | Média | Alto | Solicitar confirmação explícita antes de executar; mensagem clara de que a ação é irreversível. |
| R-08 | `/retomar` com ID inválido ou inexistente deve ser tratado graciosamente | Alta | Baixo | Validar existência do ID antes de carregar histórico; exibir mensagem de erro sem encerrar o processo. |
