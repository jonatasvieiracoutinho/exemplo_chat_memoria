# Continuidade de conversas persistidas na interface web Validation

**Date**: 2026-09-20
**Spec**: `.specs/features/corre-o-erro-sqlite-streamlit-232bce21/spec.md`
**Diff range**: `8bdf3ddb885f521bf8fc12896bc0d99493510f5a..HEAD`
**Verifier**: independent pass, round 1 of 3 (author ≠ verifier), no sub-agent dispatched

---

## Task Completion

| Task | Status  | Notes |
| ---- | ------- | ----- |
| T1   | ✅ Done | `_conexao` context manager in `persistencia.py:23-40`; all public methods use it; new tests added |
| T2   | ✅ Done | `tests/test_streamlit_rerun_persistencia.py:30-137` — rerun helper + initial-render/first-send scenario |
| T3   | ✅ Done | `tests/test_streamlit_rerun_persistencia.py:161-204` — resume/delete scenarios |
| T4   | ✅ Done | `tests/test_streamlit_rerun_persistencia.py:209-224` — disabled-persistence scenario |

---

## Spec-Anchored Acceptance Criteria

### P1: Continuidade da conversa após renderização

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| -------------------------- | --------------------- | ------------------------ | ------ |
| AC1: operação solicitada por execução diferente da que criou o gerenciador → conexão compatível, sem erro entre execuções | Nenhuma `ProgrammingError`; operação completa normalmente | `tests/test_persistencia.py:350-373` - `test_operacao_em_thread_diferente_da_criacao_nao_levanta_erro`: `assert "erro" not in resultado` (:369), `assert len(resultado["historico"]) == 1` (:370) | ✅ PASS |
| AC2: rerun com persistência ativa → lista de conversas e campo de mensagem disponíveis, sem erro de conexão de outra execução | Listagem retorna sem lançar, e envio subsequente funciona | `tests/test_streamlit_rerun_persistencia.py:131-132` - `assert threads_disponiveis == []` (executado via `rodar_em_nova_execucao` em thread distinta da criação); confirmado pelo envio bem-sucedido em `:134-137` | ✅ PASS |
| AC3: primeira mensagem não vazia após renderização → cria/reutiliza conversa e registra mensagem da pessoa seguida da resposta, na ordem | `historico[0].role == "user"`, `historico[1].role == "assistant"` | `tests/test_streamlit_rerun_persistencia.py:146-148` - `assert len(historico) == 2`; `assert historico[0]["role"] == "user"`; `assert historico[1]["role"] == "assistant"` | ✅ PASS |
| AC4: provedor informa as três quantidades de uso → registra entrada/saída/total daquela interação | `prompt_tokens==15, completion_tokens==25, total_tokens==40` (valores mockados) | `tests/test_streamlit_rerun_persistencia.py:152-154` - `assert turnos[0]["prompt_tokens"] == 15`; `== 25`; `== 40` | ✅ PASS |
| AC5: preservar conversas/mensagens/usos já gravados; manter create/list/resume/delete/query na web e no terminal | Dados pré-existentes intactos após reabrir com o novo lifecycle; suíte de terminal/CLI permanece verde | `tests/test_persistencia.py:277-325` - `test_migracao_idempotente_sobre_banco_pre_existente`: `assert threads[0]["titulo"] == "Thread antiga"` (:313, :323) após reabertura com conexão por operação; regressão completa (`tests/test_cli_persistencia.py`, `tests/test_integracao_chat.py`) verde no gate (ver Gate Check) | ✅ PASS |
| AC6: conteúdo com aspas/apóstrofos/caracteres especiais → dado literal, sem executar instrução, sem afetar outra conversa | Conteúdo malicioso volta idêntico; outra thread permanece intocada | `tests/test_persistencia.py:330-345` - `test_caracteres_especiais_tratados_como_dado_literal`: `assert historico[0]["content"] == conteudo_malicioso` (:340); `assert g.carregar_historico(tid_outra) == []` (:343) | ✅ PASS |
| AC7: renderização inicial + envio, com uso completo mockado → sem erro entre execuções; exatamente 1 conversa ativa, 2 mensagens ordenadas, 1 registro de uso | `len(threads)==1`, `len(historico)==2` ordenado, `len(turnos)==1` com os 3 campos de tokens | `tests/test_streamlit_rerun_persistencia.py:141-154` - `assert len(threads) == 1` (:142); `assert len(historico) == 2` (:146); `assert len(turnos) == 1` (:151) | ✅ PASS |

### P2: Gestão de conversas após rerun e persistência opcional

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| -------------------------- | --------------------- | ------------------------ | ------ |
| AC1: seleciona conversa salva antes do rerun → histórico na ordem original | `historico == [{"role":"user",...}, {"role":"assistant",...}]` na ordem de envio | `tests/test_streamlit_rerun_persistencia.py:177-181` - `assert sessao["chat"].thread_id == thread_id`; `assert sessao["chat"].historico == [{"role": "user", "content": "Primeira mensagem"}, {"role": "assistant", "content": "Resposta 1"}]` | ✅ PASS |
| AC2: exclui conversa e renderiza novamente → removida da lista e impede retomada | Lista pós-exclusão vazia; retomada não recupera histórico | `tests/test_streamlit_rerun_persistencia.py:197-204` - `assert excluida is True` (:197); `assert threads_apos_exclusao == []` (:201); `assert sessao["chat"].historico == []` (:204) | ✅ PASS |
| AC3: persistência desativada → não cria nem acessa arquivo de armazenamento local no fluxo web | Arquivo do caminho configurado nunca existe após o fluxo | `tests/test_streamlit_rerun_persistencia.py:222-224` - `assert sessao["gerenciador"] is None`; `assert sessao["chat"].gerenciador is None`; `assert not os.path.exists(caminho_db)` | ✅ PASS |

**Status**: ✅ All ACs covered (10/10)

---

## Edge Cases

| Edge case (spec.md) | Spec-defined outcome | `file:line` + evidence | Result |
| -------------------- | --------------------- | ------------------------ | ------ |
| Mesma operação solicitada por várias execuções em sequência → abre/encerra conexão curta por operação, sem reter conexão anterior | Nova conexão criada e fechada em cada chamada no modo arquivo | `persistencia.py:31-40` - `conexao = sqlite3.connect(self.caminho)` a cada entrada no context manager; `conexao.close()` no `finally` quando `not self._memoria`; exercitado por chamadas sequenciais em `tests/test_streamlit_rerun_persistencia.py:119-156` (3+ operações em execuções distintas, sem erro) | ✅ Handled |
| Objeto de uso ausente/incompleto → persiste turno com quantidades nulas sem erro | `prompt_tokens/completion_tokens/total_tokens` gravados como `NULL`, sem exceção | `tests/test_persistencia.py:196-202` - `test_salvar_turno_com_none_grava_null_sem_erro`: `assert turnos[0]["prompt_tokens"] is None`; `is None`; `is None` | ✅ Handled |
| Banco `:memory:` usado em testes → mantém conexão única compartilhada | `self.conn` criado uma vez em `__init__` e reaproveitado, nunca fechado por operação | `persistencia.py:17-21` (conexão única na criação) e `persistencia.py:29-30` (`if self._memoria: conexao = self.conn`, sem novo `connect`/`close`); exercitado por toda a suíte que usa a fixture `db` em modo `:memory:` (`tests/test_persistencia.py:8-12`), incluindo acesso direto a `db.conn` em `tests/test_persistencia.py:18` | ✅ Handled |

---

## Discrimination Sensor

Executado em worktree isolado (`git worktree add --detach <tmp>/sensor HEAD`), nunca na árvore real. Baseline `git status --porcelain` vazio antes e depois (confirmado).

| Mutation | File:line | Description | Killed? |
| -------- | --------- | ------------ | ------- |
| 1 | `persistencia.py:37` | Removido o `conexao.commit()` do sucesso do context manager (side effect obrigatório) | ✅ Killed — 5 testes falharam (`test_caracteres_especiais_tratados_como_dado_literal`, `test_operacao_em_thread_diferente_da_criacao_nao_levanta_erro`, e os 3 cenários de rerun T2/T3 com conteúdo persistido) |
| 2 | `persistencia.py:29` | Invertida a condição `if self._memoria:` → `if not self._memoria:` no `_conexao` (troca de ramo memória/arquivo) | ✅ Killed — 39 testes falharam (quase toda a suíte de `test_persistencia.py` em modo `:memory:` mais os cenários de rerun) |
| 3 | `persistencia.py:138` | Removido o `+ 1` de `COALESCE(MAX(ordem), 0) + 1` em `salvar_turno` (off-by-one na ordenação) | ✅ Killed — 3 testes falharam (`test_salvar_turno_ordem_sequencial_por_thread`, `test_salvar_turno_ordem_independente_por_thread`, `test_carregar_turnos_ordem_crescente`) |

**Sensor depth**: lightweight (3 mutações, código de maior risco desta feature)
**Result**: 3/3 killed - PASS ✅
**Isolation check**: `git status --porcelain` da árvore real idêntico antes/depois do sensor (vazio nos dois momentos); worktree removido com `git worktree remove --force`

---

## Interactive UAT Results

Não aplicável — sessão headless sem humano disponível para UAT interativo (feature backend/integração; cobertura automatizada é suficiente).

---

## Conditional Skills Gate

O diff altera `persistencia.py` (camada SQLite) e adiciona testes que gravam entrada não confiável (conteúdo de mensagem com tentativa de injeção). Gatilho de `dev-sec-ops-ciclo` acionado; Modo P executado sobre o diff:

- Todas as queries que incorporam dado variável usam parâmetros `?` (nenhuma concatenação/interpolação de string em SQL) — `persistencia.py:83-171`.
- `PRAGMA foreign_keys = ON` aplicado em toda conexão nova (`persistencia.py:20,34`), preservando o invariante de integridade referencial que existia antes.
- Conteúdo do usuário (incluindo tentativa de `DROP TABLE`) é tratado como dado literal e não afeta outras conversas — confirmado por `tests/test_persistencia.py:330-345`.
- Nenhum secret, comando de SO, upload, rota HTTP ou lógica de auth introduzidos neste diff.

**Resultado**: nenhum bloqueador. Nenhum item para o `validation.md`.

`revisao-de-impacto-ciclo` não foi acionada: o diff não altera a forma das queries/schema (mesmas tabelas e SQL, apenas o lifecycle de conexão), não altera contrato de API/evento nem modelo de auth, e não altera topologia de runtime (processo único, mesmo binário).

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Minimum code | ✅ — mudança concentrada no lifecycle de conexão (`persistencia.py`) e nos testes que o cobrem |
| Surgical changes | ✅ — `app_streamlit_core.py`/`app_streamlit.py`/`chat_openai_memoria.py` não tocados, conforme design.md |
| No scope creep | ✅ — sem mudança de schema, API pública ou UI |
| Matches patterns | ✅ — mantém `sqlite3.Row`, `PRAGMA foreign_keys`, assinaturas públicas |
| Spec-anchored outcome check (asserted values match spec) | ✅ — ver tabela de ACs acima |
| Per-layer Coverage Expectation met (domain 1:1 ACs; rerun happy+edge+error) | ✅ — `persistencia.py` 1:1 com ACs de dados; cenários de rerun cobrem inicial+envio, retomar, excluir, persistência desativada |
| Every test maps to a spec requirement — no unclaimed tests | ✅ — os 6 testes novos mapeiam a SQLR-01/02/03/04/08/09/10 |
| Documented guidelines followed | ✅ — nenhuma (Test Coverage Matrix em `tasks.md`: "Guidelines found: none... Strong defaults applied") |

---

## Gate Check

- **Gate command**: `python3 -m pytest -q` (Build gate, `tasks.md` Gate Check Commands)
- **Result**: 109 passed, 0 failed, 0 skipped
- **Test count before feature** (commit `8bdf3ddb885f521bf8fc12896bc0d99493510f5a`): 103
- **Test count after feature** (HEAD, commit `e4515ec`): 109
- **Delta**: +6 new tests (2 em `tests/test_persistencia.py`: caracteres especiais, operação em thread diferente; 4 em `tests/test_streamlit_rerun_persistencia.py`: T2, T3×2, T4). Nenhum teste removido.
- **Skipped tests**: nenhum
- **Failures**: nenhuma

---

## Fix Plans

Nenhum gap encontrado. Sem Fix Plans nesta rodada.

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status  |
| ------------ | ---------------- | ------------ |
| SQLR-01 | Implementing | ✅ Verified |
| SQLR-02 | Implementing | ✅ Verified |
| SQLR-03 | Implementing | ✅ Verified |
| SQLR-04 | Implementing | ✅ Verified |
| SQLR-05 | Implementing | ✅ Verified |
| SQLR-06 | Implementing | ✅ Verified |
| SQLR-07 | Implementing | ✅ Verified |
| SQLR-08 | Implementing | ✅ Verified |
| SQLR-09 | Implementing | ✅ Verified |
| SQLR-10 | Implementing | ✅ Verified |

(Atualização registrada aqui pelo Verifier; `spec.md` não é editado nesta rodada por protocolo de rodada 1.)

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 10/10 ACs matched spec outcome, 0 spec-precision gaps
**Sensor**: 3/3 mutations killed
**Gate**: 109 passed, 0 failed, 0 skipped

**What works**: Conexão por operação elimina o `ProgrammingError` entre execuções (T1); os quatro cenários de rerun (inicial+envio, retomar, excluir, persistência desativada) passam com asserções precisas de spec; modo `:memory:` inalterado; regressão completa (terminal/CLI) verde; entrada não confiável tratada como dado literal via SQL parametrizado.

**Issues found**: nenhum.

**Next steps**: Nenhuma correção pendente. Sidecar de veredito: PRONTO / aprovado.
