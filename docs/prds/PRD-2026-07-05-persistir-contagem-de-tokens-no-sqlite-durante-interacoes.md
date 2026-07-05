# PRD — Persistir contagem de tokens no SQLite durante interações

- **Data:** 2026-07-05
- **Sistema:** exemplo_chat_memoria — Chat OpenAI com memória e persistência SQLite
- **Status:** Documento funcional para aprovação (pré-plano técnico)
- **Autor:** Agente de especificação (automação)

---

## 1. Contexto

A aplicação é um chat CLI em Python integrado à API da OpenAI, com memória de
conversa e persistência local em SQLite (`chat_memoria.db`). A camada de
persistência é concentrada em `persistencia.py` (`GerenciadorPersistencia`), que
mantém duas tabelas:

- `threads` (`id`, `titulo`, `criado_em`, `atualizado_em`)
- `mensagens` (`id`, `thread_id`, `role`, `content`, `ordem`), com FK
  `ON DELETE CASCADE` e `PRAGMA foreign_keys = ON`.

A orquestração do chat vive em `chat_openai_memoria.py` (`ChatComMemoria`). O
fluxo de gravação é centralizado em `adicionar_mensagem(role, content)`, que cria
a thread na primeira mensagem `user` e grava cada mensagem (`user` e `assistant`)
como uma linha em `mensagens`. A geração de resposta ocorre em
`enviar_mensagem(mensagem)`, que chama `client.chat.completions.create(...)`.

Hoje o objeto `usage` retornado pela API (`prompt_tokens`, `completion_tokens`,
`total_tokens`) é **descartado**. A única métrica de tokens existente é
`contar_tokens_aproximado()` — uma **estimativa** (soma de caracteres // 4) usada
apenas para sliding window, alertas visuais e comandos de exibição (`/tokens`,
`/debug`, `/grafico`).

## 2. Problema

A aplicação não registra nem persiste a contagem **real** de tokens consumidos em
cada interação/turno. Sem esse dado persistido, não é possível auditar consumo,
analisar histórico de custo/uso por conversa ou consultar posteriormente quantos
tokens foram gastos em cada turno. A informação real está disponível no momento da
resposta da API (`resposta.usage`), mas é perdida por não ser propagada até a
camada de persistência.

## 3. Objetivo

Garantir que a aplicação **registre e persista na base SQLite existente** a
contagem de tokens consumidos em interações/turnos de conversa, sempre que esses
eventos forem salvos, permitindo consulta posterior por turno e por interação, sem
perda do comportamento atual de registro de mensagens.

## 4. Escopo

- Capturar os tokens **reais** a partir do campo `usage` da resposta da API
  (`prompt_tokens` = entrada, `completion_tokens` = saída, `total_tokens` = total)
  dentro de `enviar_mensagem`.
- Propagar esses valores desde `enviar_mensagem` até a camada de persistência
  (`persistencia.py`).
- Persistir, no mesmo fluxo de gravação das interações/turnos, a contagem de
  tokens de entrada, saída e total associada a cada turno de conversa.
- Evoluir o schema SQLite existente (via migração idempotente, ex.: `ALTER TABLE`
  ou nova tabela/entidade de turno) de forma que bancos já existentes continuem
  funcionando e recebam a nova estrutura.
- Disponibilizar os dados persistidos para **consulta posterior** dos tokens por
  interação e por turno.
- Tratar de forma defensiva cenários em que `usage` esteja ausente ou incompleto
  (ex.: `base_url` alternativa — Ollama/LM Studio/Azure — ou streaming sem
  `include_usage`), gravando `NULL`/valor ausente sem quebrar o fluxo.

## 5. Fora de escopo

- **Migração de dados históricos**: registros de mensagens já existentes **não**
  serão retroalimentados com tokens; a contagem passa a ser registrada apenas a
  partir da implementação. Colunas/valores de tokens aceitam `NULL` para registros
  antigos.
- Substituição ou remoção de `contar_tokens_aproximado()` — a estimativa é
  **preservada** (sliding window e alertas dependem dela). Os tokens reais são um
  dado adicional, não um substituto.
- Cobrança, faturamento, cálculo de custo monetário ou dashboards/relatórios de
  consumo.
- Novos comandos de UI/CLI de exibição de tokens reais (podem ser tema de demanda
  futura; não é requisito aqui).
- Alteração da lógica de negócio da conversa ou do modelo de memória.

## 6. Requisitos funcionais

- **RF1 — Captura de tokens reais:** ao gerar uma resposta em `enviar_mensagem`
  (modo não-streaming), a aplicação deve extrair `prompt_tokens`,
  `completion_tokens` e `total_tokens` de `resposta.usage`.
- **RF2 — Persistência no fluxo de gravação:** a contagem de tokens deve ser
  gravada no SQLite dentro do mesmo fluxo que registra a interação/turno, sem
  fluxo de escrita paralelo desacoplado.
- **RF3 — Associação por turno:** os tokens devem ficar associados ao turno de
  conversa correspondente (entrada + saída + total do turno), vinculado à thread e,
  quando aplicável, às mensagens do turno.
- **RF4 — Consulta posterior:** o modelo de dados deve permitir consultar a
  contagem de tokens por turno de conversa e por interação registrada.
- **RF5 — Preservação do registro atual:** o registro das mensagens (`user` e
  `assistant`) e a criação de threads devem continuar funcionando exatamente como
  hoje; a introdução de tokens não pode impedir ou alterar esse comportamento.
- **RF6 — Evolução idempotente do schema:** a criação/alteração de estrutura deve
  ser idempotente e compatível com bancos `chat_memoria.db` já existentes
  (não recriar, não apagar dados).
- **RF7 — Tolerância a ausência de `usage`:** quando `usage` não estiver presente
  ou vier incompleto (base_url alternativa, streaming sem `include_usage`, erro
  parcial), o registro deve ocorrer com tokens ausentes/`NULL`, sem interromper a
  gravação da interação.
- **RF8 — Persistência durável:** os valores de tokens gravados devem permanecer
  disponíveis após reinicialização da aplicação.

## 7. Critérios de aceite

- **CA1:** Ao registrar uma interação na base SQLite, a contagem de tokens
  correspondente também é salva.
- **CA2:** Ao registrar um turno de conversa, a contagem de tokens associada ao
  turno (entrada, saída e total) também é persistida.
- **CA3:** Os dados persistidos permitem consultar tokens por interação e por
  turno de conversa.
- **CA4:** A persistência de tokens não impede o registro normal das interações
  existentes (mensagens `user`/`assistant` continuam sendo gravadas como hoje).
- **CA5:** Os valores de tokens salvos permanecem disponíveis após reinicialização
  da aplicação.
- **CA6:** Bancos `chat_memoria.db` pré-existentes continuam abrindo e operando
  normalmente após a evolução de schema (sem perda de dados, sem erro de abertura).
- **CA7:** Em cenários sem `usage` disponível, a interação/turno é registrada com
  tokens ausentes/`NULL` e a aplicação não falha.
- **CA8:** A assinatura e o comportamento atuais cobertos pelos testes existentes
  (`test_persistencia.py`, `test_integracao_chat.py`) permanecem compatíveis.

## 8. Impactos e restrições técnicas relevantes

- **Fonte de verdade dos tokens:** o campo `resposta.usage` só existe dentro de
  `enviar_mensagem`, no ramo **não-streaming**. Será necessário propagar esse dado
  até `persistencia.py`.
- **Ponto de escrita atual:** `adicionar_mensagem` → `salvar_mensagem` **não**
  recebe nem propaga tokens e é chamado **duas vezes por turno** (uma para o
  `user`, antes da chamada à API; outra para o `assistant`, depois). A linha
  `user` é gravada **antes** de `usage` existir — associar entrada/saída a
  mensagens individuais exigiria `UPDATE` posterior ou adiar a gravação. O modelo
  conceitual mais aderente ao requisito ("entrada e saída a cada turno") é um
  **registro por turno** com `prompt_tokens`, `completion_tokens` e `total`.
- **Restrição de base:** usar o SQLite já existente (`chat_memoria.db`); não migrar
  para outra tecnologia de armazenamento.
- **Migração de schema obrigatória:** `_criar_tabelas()` usa
  `CREATE TABLE IF NOT EXISTS`, portanto bancos existentes **não** ganham
  colunas/tabelas novas automaticamente — exige lógica de migração idempotente
  (`ALTER TABLE` e/ou nova tabela). Colunas de tokens devem aceitar `NULL`.
- **Preservação de compatibilidade:** `salvar_mensagem` é coberto por testes que
  validam assinatura e comportamento; mudanças devem manter compatibilidade
  retroativa.
- **`contar_tokens_aproximado()` preservado:** continua sendo usado para sliding
  window, alertas e comandos visuais; os tokens reais não o substituem.

## 9. Riscos e pontos de atenção

- **R1 — Streaming sem `usage`:** quando `self.stream=True` (env `OPENAI_STREAM`),
  `enviar_mensagem` itera sobre chunks e não tem acesso a `usage` por padrão. A API
  só envia usage em streaming se for passado `stream_options={'include_usage':
  True}`. Principal risco para garantir tokens reais em todos os modos — decidir
  entre habilitar `include_usage` ou aceitar tokens ausentes no modo streaming.
- **R2 — `base_url` alternativa:** sob Ollama/LM Studio/Azure, `usage` pode estar
  ausente ou incompleto; exige tratamento defensivo (RF7).
- **R3 — Ordem de gravação por turno:** como o `user` é gravado antes de a API
  responder, associar tokens de entrada/saída a mensagens individuais requer
  `UPDATE` posterior ou reestruturação do momento de gravação; o modelo por turno
  mitiga esse risco.
- **R4 — Migração idempotente:** falha na migração pode impedir a abertura de
  bancos existentes; a rotina deve detectar estrutura já presente e não recriar.
- **R5 — Regressão em testes existentes:** alterações em `salvar_mensagem`/schema
  podem quebrar `test_persistencia.py` e `test_integracao_chat.py`; manter
  compatibilidade de assinatura é obrigatório.
- **R6 — Não regressão do registro de mensagens:** garantir que a introdução de
  tokens não altere `ordem`, criação de thread ou o registro das linhas em
  `mensagens`.

## 10. Perguntas em aberto (para validação antes do plano técnico)

Estas questões surgiram na investigação e devem ser confirmadas na aprovação do
PRD; onde há premissa adotada, ela está indicada:

1. **Métricas a persistir:** confirmar entrada (`prompt_tokens`), saída
   (`completion_tokens`) e total (`total_tokens`). *(Premissa: persistir os três.)*
2. **Granularidade:** registro **por turno** (premissa adotada) vs. por mensagem
   individual — confirmar o modelo por turno.
3. **Origem da contagem:** tokens reais vêm do `usage` da API (não estimados pela
   aplicação). *(Premissa: usar `usage`; estimativa permanece só para UI/janela.)*
4. **Streaming:** habilitar `stream_options={'include_usage': True}` para capturar
   tokens no modo streaming, ou aceitar tokens ausentes/`NULL` nesse modo?
5. **Modelo de dados:** novas colunas em `mensagens` vs. nova entidade de "turno"
   relacionada a `threads`/`mensagens` — confirmar preferência estrutural.
6. **Migração de dados históricos:** confirmado que **não** há retroalimentação de
   registros antigos (colunas aceitam `NULL`).
