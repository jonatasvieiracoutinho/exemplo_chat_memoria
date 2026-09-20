# Fala do usuário aparece na hora — Validation

**Date**: 2026-09-20
**Spec**: `.specs/features/fala-do-usu-rio-no-chat-s-aparece-quando-o-assis-a52b11c8/spec.md`
**Diff range**: `118fb28c2059ad4a36b737cbaa3f90dc6616b426..HEAD`
**Verifier**: independent pass (author ≠ verifier), round 1 of 3

---

## Task Completion

| Task | Status  | Notes                                                                             |
| ---- | ------- | ---------------------------------------------------------------------------------- |
| T1   | ✅ Done | Commit `021a385` matches task; user bubble + spinner added at `app_streamlit.py:80-82` |
| T2   | ✅ Done | Commit `42c3bb5` matches task; `st.rerun()` removed from success path, assistant bubble inline |
| T3   | ✅ Done | Commit `db3246f` matches task; `st.error` on failure keeps user bubble, no assistant bubble |

---

## Spec-Anchored Acceptance Criteria (P1)

| Criterion (WHEN X THEN Y) | Spec-defined outcome | `file:line` + assertion | Result |
| -------------------------- | --------------------- | ------------------------ | ------ |
| AC1: WHEN the user submits a message THEN render the user's message before response generation begins | User bubble appears even when the core does NOT append to `historico` (proves it is painted by wiring, independent of and prior to the generation call) | `app_streamlit.py:80-83` (paint precedes the `enviar_mensagem_seguro` call) — `tests/test_app_streamlit_ui.py:212-221` — mocks `enviar_mensagem_seguro` to return an error without appending, then `assert "Olá" in textos` | ✅ PASS |
| AC2: WHILE the response is being generated, keep the user's message visible | Message stays in the render tree through the blocking call (no clear/rerun between paint and the call) | `app_streamlit.py:80-84` — same synchronous script run, no intervening `st.rerun()` or history clear between the paint and the `st.spinner` block | ✅ PASS — note: `AppTest` executes the script to completion, so no test literally samples the mid-spinner instant; visibility during generation is guaranteed by code ordering (single execution, no clear call between paint and call), not by a distinct assertion. Flagged for transparency, not counted as a gap. |
| AC3: WHILE the response is being generated, display a processing indicator | Spinner is invoked with a friendly PT-BR message, wrapping the blocking call | `app_streamlit.py:82` `st.spinner("Gerando resposta...")` — `tests/test_app_streamlit_ui.py:215,222` `patch(... wraps=st.spinner)` then `spinner_mock.assert_called_once_with("Gerando resposta...")` | ✅ PASS |
| AC4: WHEN generation succeeds THEN render the assistant reply after the user's message without overwriting/hiding it | Assistant bubble renders after the user bubble in the same run; both remain in the ordered bubble list | `app_streamlit.py:87-89` — `tests/test_app_streamlit_ui.py:247-253` `assert textos == ["Primeira", "Resposta para: Primeira", "Segunda", "Resposta para: Segunda"]` | ✅ PASS |
| AC5: WHEN messages are sent in consecutive interactions THEN render each turn consistently without duplicating in history nor persisting twice | Two submissions → exactly 4 ordered bubbles, no duplicates; `enviar_mensagem_seguro` called exactly once per submission; no `st.rerun()` on the success path | `app_streamlit.py:83-89` (no `st.rerun()` in success branch) — `tests/test_app_streamlit_ui.py:225-255` `assert textos == [...]` (4 items, no dup), `enviar_mock.call_count == 2` (line 254), `rerun_mock.assert_not_called()` (line 255) | ✅ PASS — note: double-write to persistence itself happens inside `chat_openai_memoria.py`/`persistencia.py`, explicitly out of scope for this feature (spec.md Out of Scope). The UI-level cause of double-processing (`st.rerun()` on success) is what's tested and removed. |
| AC6: IF response generation fails THEN display the sanitized error message while keeping the user's message visible | Exactly one `st.error` with the sanitized message, no assistant bubble, user bubble still present | `app_streamlit.py:84-86` — `tests/test_app_streamlit_ui.py:258-278` `assert textos == ["Olá"]` (line 276), `assert len(at.error) == 1` (line 277), message content matches sanitized string (line 278) | ✅ PASS |

**Status**: ✅ All ACs covered (one transparency note on AC2, not a gap; see Discrimination Sensor confirming AC2 is regression-proof through AC1/AC3's tests).

---

## Discrimination Sensor

Isolated in a temporary git worktree (`git worktree add --detach <mktemp -d>/sensor HEAD`), never touching the real tree. Baseline `git status --porcelain` before sensor work: empty. Ran `python3 -m pytest tests/test_app_streamlit_ui.py` in the scratch after each mutation, reverted with `git checkout -- app_streamlit.py` between mutations, then `git worktree remove --force` at the end. Post-cleanup `git status --porcelain` on the real tree: empty — matches baseline.

| Mutation | File:line | Description | Killed? |
| -------- | --------- | ------------ | ------- |
| 1 | `app_streamlit.py:80-81` | Removed the immediate `with st.chat_message("user"): st.write(entrada)` paint (reintroduces the original bug: bubble only from history) | ✅ Killed — 4 tests failed (`test_app_exibe_historico_e_envia_mensagem`, `test_bolha_usuario_aparece_imediatamente_com_spinner_mesmo_sem_append`, `test_dois_envios_consecutivos_nao_duplicam_bolhas`, `test_erro_sanitizado_mantem_fala_do_usuario_visivel_sem_append`) |
| 2 | `app_streamlit.py:87-89` | Reintroduced `st.rerun()` right after rendering the assistant bubble on success (reverts the T2 fix) | ✅ Killed — `test_dois_envios_consecutivos_nao_duplicam_bolhas` failed on `rerun_mock.assert_not_called()` (called 2 times) |
| 3 | `app_streamlit.py:82` | Changed spinner text `"Gerando resposta..."` → `"Processando..."` | ✅ Killed — `test_bolha_usuario_aparece_imediatamente_com_spinner_mesmo_sem_append` failed on `spinner_mock.assert_called_once_with("Gerando resposta...")` |

**Sensor depth**: lightweight (3 targeted behavior-level mutations on the new code — default tier; feature is not P0/critical-path).
**Result**: 3/3 killed — ✅ PASS

---

## Code Quality

| Principle                                                                     | Status |
| ------------------------------------------------------------------------------ | ------ |
| Minimum code                                                                    | ✅     |
| Surgical changes                                                                | ✅     |
| No scope creep                                                                  | ✅     |
| Matches patterns                                                                | ✅     |
| Spec-anchored outcome check (asserted values match spec)                       | ✅     |
| Per-layer Coverage Expectation met (integration tests cover happy+edge+error)  | ✅     |
| Every test maps to a spec requirement - no unclaimed tests                     | ✅     |
| Documented guidelines followed: none formais — strong defaults applied (per tasks.md Test Coverage Matrix, following `tests/test_app_streamlit_ui.py` existing convention) | ✅     |

Diff touches only `app_streamlit.py` (8 lines, code) plus `tests/test_app_streamlit_ui.py` (+80 lines) and planning artifacts (`spec.md`, `tasks.md`, PRD). No changes to `app_streamlit_core.py`, `chat_openai_memoria.py`, or `persistencia.py` — matches the Out of Scope table in spec.md.

---

## Edge Cases

- [x] IF `enviar_mensagem_seguro` returns an error → keep rendered user message visible, show only sanitized message: covered by AC6 (`tests/test_app_streamlit_ui.py:258-278`).
- [ ] WHEN submitted text is empty/blank → SHALL NOT render a turn nor call generation: NOT covered by a new or existing test. Verified only by code inspection — the `if entrada:` guard at `app_streamlit.py:79` is unchanged by this diff and predates it (present at `118fb28c`). No regression introduced by this feature; flagged as a pre-existing coverage gap, out of this diff's blast radius.
- [x] WHEN two messages are sent one after another → four ordered bubbles, no duplicate: covered by `tests/test_app_streamlit_ui.py:225-255` (`test_dois_envios_consecutivos_nao_duplicam_bolhas`).

---

## Gate Check

- **Gate command**: `python3 -m pytest tests/`
- **Result**: 112 passed, 0 failed, 0 skipped
- **Test count before feature** (at `118fb28c`): 109
- **Test count after feature** (at `HEAD`): 112
- **Delta**: +3 new tests (matches `tests/test_app_streamlit_ui.py` growing from 10 to 13 test functions)
- **Skipped tests**: none
- **Failures**: none

---

## Fix Plans

None. No gap survived verification; the one edge case left uncovered (empty/blank input) is pre-existing behavior outside this diff's scope, not a regression introduced by this feature.

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status  |
| ----------- | ---------------- | ------------ |
| CHAT-01     | Implementing      | ✅ Verified |
| CHAT-02     | Implementing      | ✅ Verified |
| CHAT-03     | Implementing      | ✅ Verified |
| CHAT-04     | Implementing      | ✅ Verified |
| CHAT-05     | Implementing      | ✅ Verified |
| CHAT-06     | Implementing      | ✅ Verified |

---

## Conditional Skills Check

- `dev-sec-ops-ciclo`: not triggered — diff touches only Streamlit UI wiring (chat bubble rendering, spinner, error display); no auth, credential, untrusted-input parsing, SQL, subprocess, filesystem, HTTP route, or LLM prompt code.
- `revisao-de-impacto-ciclo`: not triggered — no change to SQL/schema shape, API/event contract, auth model, or runtime topology. `app_streamlit_core.py`, `chat_openai_memoria.py`, and `persistencia.py` are untouched.

---

## Summary

**Overall**: ✅ Ready

**Spec-anchored check**: 6/6 ACs matched spec outcome (1 transparency note on AC2's mid-spinner instant, not scored as a gap)
**Sensor**: 3/3 mutations killed
**Gate**: 112 passed, 0 failed

**What works**: User message paints immediately via wiring-level `st.chat_message("user")` before the blocking `enviar_mensagem_seguro` call, independent of core history append; `st.spinner("Gerando resposta...")` wraps the call; on success the assistant reply renders inline after the user bubble with no `st.rerun()`, so consecutive turns don't duplicate; on failure `st.error` shows the sanitized message while the user bubble stays visible. All three sensor mutations (removing the immediate paint, reintroducing `st.rerun()`, changing the spinner text) were caught by the new tests.

**Issues found**: none blocking. Pre-existing edge case (empty/blank input skip) has no dedicated test, but it predates this diff and isn't part of this feature's blast radius.

**Next steps**: none required for this round. Round 1 verdict: PRONTO / aprovado.
