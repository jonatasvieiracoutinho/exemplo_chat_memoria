# RF-PROV-01 Validation

**Date**: 2026-09-28
**Spec**: `.specs/features/RF-PROV-01/spec.md`
**Diff range**: `release...HEAD` (base `34dc3c9`, 18 commits, `94c4008`..`a414782`)
**Verifier**: independent sub-agent (author ≠ verifier) — rodada 1

---

## Task Completion

Todas as 18 tasks de `tasks.md` (T1–T18, fases 1–5) estão marcadas `[x]` e têm commit correspondente na branch. Nenhuma bloqueada ou parcial.

| Fase | Tasks | Status |
| ---- | ----- | ------ |
| 1 — Erro do provedor na tela | T1–T5 | ✅ Done |
| 2 — Carga de Perfis no ambiente | T6–T9 | ✅ Done |
| 3 — Override no construtor | T10–T11 | ✅ Done |
| 4 — Troca de Perfil pela barra lateral | T12–T15 | ✅ Done |
| 5 — Perfil digitado | T16–T18 | ✅ Done |

---

## Spec-Anchored Acceptance Criteria

| Critério | Spec-defined outcome | `file:line` + assertion | Resultado |
| -------- | --------------------- | ----------------------- | --------- |
| CA-PROV-01 — bloco completo disponível, incompleto indisponível nomeando variável | `Groq` disponível com os 3 valores; `Ollama local` indisponível citando `PERFIL_OLLAMA_LOCAL_MODEL`; sem exceção | `app_streamlit_core.py:78-97` (`carregar_perfis`); `tests/test_app_streamlit_core.py:456-474` — `assert "PERFIL_OLLAMA_LOCAL_MODEL" in perfis[1]["motivo_indisponivel"]` | ✅ PASS |
| CA-PROV-02 — URL sem esquema recusada, nome duplicado uma vez, `PERFIS` ausente só padrão | 3 comportamentos discriminados por `disponivel`, não por contagem | `app_streamlit_core.py:98-109`; `tests/test_app_streamlit_core.py:492-539` — `assert perfis[1]["disponivel"] is False`; `test_carregar_perfis_nome_repetido_entra_uma_vez`; `test_carregar_perfis_sem_perfis_declarados_devolve_so_padrao` | ✅ PASS |
| CA-PROV-03 — sem parâmetro preserva ambiente; parâmetro vence | atributos == ambiente sem params; atributos == params quando passados; `api_key`/`modelo` ausentes do ambiente não impedem construção com parâmetro | `chat_openai_memoria.py:133-157`; `tests/test_integracao_chat.py:321-357` — `test_parametros_novos_vencem_o_ambiente`, `test_api_key_por_parametro_permite_ambiente_sem_openai_api_key` | ✅ PASS |
| CA-PROV-04 — parâmetro inválido recusado sem citar `.env` | `ValueError` citando o parâmetro, sem a string `.env`; ambiente continua citando `.env` | `chat_openai_memoria.py:141-144,154-157,205-211`; `tests/test_integracao_chat.py:378-407` — `assert ".env" not in str(exc.value)` (3x) e `test_valor_invalido_vindo_do_ambiente_continua_citando_a_variavel_do_env` | ✅ PASS |
| CA-PROV-05 — troca constrói contra o Perfil e limpa a conversa | chamada recebe os 3 valores de `Groq`; tela vazia; ativo mostrado sem chave | `app_streamlit.py:114-120`; `tests/test_app_streamlit_ui.py:284-311` — `kwargs["api_key"] == "gsk_exemplo"`; `len(at.chat_message) == 0`; `tests/test_app_streamlit_ui.py:355-372` — `"gsk_super_secreta_123" not in textos` | ✅ PASS |
| CA-PROV-06 — indisponível/recusado preserva sessão | objeto de sessão idêntico; motivo exibido; conversa visível | `tests/test_app_streamlit_ui.py:419-463` — `at.session_state["chat"] is chat`; `construir_mock.assert_called_once()` (só a chamada inicial) | ✅ PASS |
| CA-PROV-07 — reselecionar ativo não descarta | objeto idêntico; nenhuma chamada extra ao construtor | `app_streamlit.py:113` (`elif ... and nome_escolhido != perfil_ativo`); `tests/test_app_streamlit_ui.py:375-416` — `construir_mock.assert_called_once()` / `call_count == 2` (2 trocas reais, 0 por reseleção) | ✅ PASS |
| CA-PROV-08 — Perfil digitado válido troca, campo vazio não | sessão com exatamente os 3 valores digitados; objeto idêntico na recusa | `tests/test_app_streamlit_ui.py:501-549` — `kwargs["api_key"] == "gsk_digitada"`; `at.session_state["chat"] is chat` no caso de campo vazio | ✅ PASS |
| CA-PROV-09 — URL digitada sem esquema recusada, chave não ecoada | erro contém a URL recebida; texto renderizado não contém a chave | `tests/test_app_streamlit_ui.py:552-573,575-` — `assert "gsk_digitada" not in at.error[0].value` | ✅ PASS |
| CA-PROV-10 — texto da exceção na tela, chave ativa mascarada | `st.error` contém `Incorrect API key provided` e `gsk_***Z789`, não contém a chave crua | `app_streamlit_core.py:170-177` (`sanitizar_erro`); `tests/test_app_streamlit_ui.py:60-78` — as 3 assertivas exatas | ✅ PASS |
| CA-PROV-11 — chave curta opaca, chave do ambiente também mascarada | `***` sem a chave de 6 caracteres; `OPENAI_API_KEY` mascarada quando difere da ativa | `app_streamlit_core.py:38-51` (`mascarar_chave`); `tests/test_app_streamlit_core.py:271-279` — `"sk-real-key-999" not in msg`, chave ativa diferente | ✅ PASS |

**Status**: ✅ Todos os 11 ACs do requisito cobertos com evidência `file:line`, sem spec-precision gap.

---

## Discrimination Sensor

Scratch usado: cópia de arquivos em `.agent-loop/execucoes/2026-09-28T07-55-02/RF-PROV-01/3-verificar#rodada-1/scratch` (nunca `git worktree`, nunca `git stash`). Baseline `git status --porcelain` da árvore real: vazio antes e depois — isolamento confirmado.

| # | Arquivo:linha | Mutação | Testes usados | Killed? |
| - | -------------- | ------- | -------------- | ------- |
| 1 | `app_streamlit_core.py` (`mascarar_chave`) | `len(chave) >= 12` → `len(chave) > 12` | `tests/test_app_streamlit_core.py -k mascarar` | ✅ Killed — `test_mascarar_chave_limite_exato_doze_caracteres` |
| 2 | `app_streamlit_core.py` (`carregar_perfis`) | checagem de esquema `startswith("http://"/"https://")` → `if not base_url:` | `tests/test_app_streamlit_core.py -k carregar_perfis` | ✅ Killed — `test_carregar_perfis_url_sem_esquema_fica_indisponivel_com_url_no_motivo` |
| 3 | `app_streamlit_core.py` (`trocar_perfil`) | inversão de ordem: construir antes de checar `disponivel` | `tests/test_app_streamlit_core.py -k trocar_perfil` | ✅ Killed — `test_trocar_perfil_indisponivel_devolve_motivo_sem_chamar_construtor`, `test_trocar_perfil_disponivel_constroi_antes_de_qualquer_descarte` |
| 4 | `chat_openai_memoria.py` (`__init__`, validação de `api_key`) | precedência invertida: `if os.getenv("OPENAI_API_KEY"):` no lugar de `if api_key is None:` | `tests/test_integracao_chat.py -k "parametro or vence"` | ✅ Killed — `test_parametros_novos_vencem_o_ambiente`, `test_api_key_por_parametro_vazio_recusa_citando_o_parametro`, `test_sem_parametros_novos_atributos_vem_do_ambiente_como_hoje` |

**Sensor depth**: lightweight (feature não é P0 payment/auth/data-integrity — é credencial de LLM em app localhost, operador único, conforme AD-005/AD-006 do spec).
**Result**: 4/4 killed — PASS ✅

---

## Code Quality

| Principle | Status |
| --------- | ------ |
| Sem funcionalidade além do pedido | ✅ — nada de Bedrock, nome de Perfil digitado, allowlist de domínio, persistência de Perfil (todos em *Fora deste requisito*) |
| Sem abstração para código de uso único | ✅ — `mascarar_chave`, `carregar_perfis`, `trocar_perfil`, `validar_perfil_digitado` são funções diretas, sem classe/factory desnecessária |
| Sem flexibilidade especulativa | ✅ |
| Só arquivos exigidos pela task | ✅ — `app_streamlit_core.py`, `chat_openai_memoria.py`, `app_streamlit.py`, `env.example`, testes, e os artefatos de `.specs`/PRD citados pelo requisito |
| Não "melhorou" código não relacionado | ✅ |
| Segue padrões existentes | ✅ — precedência parâmetro-vence-ambiente copia a forma dos 4 parâmetros opcionais já existentes; regra de esquema de URL reaproveitada, não duplicada |
| Testes mapeiam para ACs e não são superficiais | ✅ — spot-check em CA-PROV-06/07 confirma assertiva de identidade de objeto e contagem de chamadas, não só presença de mensagem |
| Spec-anchored outcome check | ✅ — ver tabela acima |
| Cobertura por camada (domínio 1:1, rotas happy+edge+erro) | ✅ — núcleo com testes unitários por branch; `app_streamlit.py` com `AppTest` cobrindo sucesso, recusa, reseleção e Perfil digitado |
| Todo teste mapeia para um AC (sem teste órfão) | ✅ — nomes dos testes novos citam a intenção do AC |
| Diretrizes documentadas seguidas | `tasks.md` — "strong defaults aplicados", sem `pyproject.toml`/CI/linter declarado |

---

## Edge Cases

- [x] Nome de Perfil com caractere não alfanumérico normaliza para `PERFIL_<NOME>_` — `tests/test_app_streamlit_core.py:439-454`
- [x] `OPENAI_BASE_URL` indefinida → `Padrão (.env)` com `base_url: None`, `disponivel: True` — `tests/test_app_streamlit_core.py:405-414`
- [x] Perfil indisponível tolera `None` nos três valores — implementado em `carregar_perfis`
- [x] Reload do navegador volta a `Padrão (.env)` — decorre de `st.session_state` não persistido; não testável fora de um browser real, mas a inicialização (`inicializar_estado()`) sempre parte de `Padrão (.env)`, coberto por `test_provedor_criacao_da_sessao_inicia_com_padrao_env`
- [x] Troca de Perfil sem enviar mensagem não deixa thread órfã — não há mudança em `_adicionar_ao_historico()`/`criar_thread()` no diff; comportamento herdado, não regredido (confirmado por leitura: nenhuma dessas funções aparece no diff)
- [x] `retomar_thread()` usa o Perfil do momento — `app_streamlit_core.py:222-228`; `tests/test_app_streamlit_core.py:110-127` (`test_retomar_thread_repassa_perfil_informado_no_momento`)
- [x] Sem persistência, `gerenciador`/`thread_id` continuam ignorados em `construir_sessao_chat` — `tests/test_app_streamlit_core.py:48-56,100-108`

---

## Gate Check

- **Gate command**: `.venv/Scripts/python.exe -m pytest tests/`
- **Result**: 168 passed, 0 failed, 0 skipped
- **Test count before feature**: 112 (declarado em `docs/requisitos/RF-PROV-01.md` e `tasks.md`)
- **Test count after feature**: 168
- **Delta**: +56 novos, nenhuma deleção silenciosa (os 5 testes que travavam a mensagem fixa foram reescritos, não apagados — `T3`)
- **Skipped tests**: nenhum
- **Failures**: nenhuma

---

## Condicionais de superfície

**Segurança (dev-sec-ops-ciclo)** — aplicável, diff toca API externa, segredo em memória, validação de input, headers implícitos de URL. Os 6 requisitos de segurança do `spec.md` (linhas 189-194) foram conferidos contra o código:

1. `[Norma 4.4.1.f, 4.4.1.o, 4.4.2.1.d]` `[ASVS V14.6]` — chave nunca em tela/log/export/disco: `mascarar_chave` aplicado em `sanitizar_erro`; nenhuma escrita em `os.environ` (`grep -n "os.environ\["` vazio nos 3 arquivos); erro nunca entra em `chat.historico` (`grep -n "st.error\|historico.append"` em `app_streamlit.py` confirma que nenhum `st.error` é seguido de append). Caminho de log de debug (`chat_openai_memoria.py:262-` em diante) não foi tocado pelo diff — sem regressão. ✅ Conforme
2. `[Norma 4.4.1.a, 4.4.1.f]` — máscara 4+***+4 acima de 12, `***` abaixo: confirmado pelo sensor (mutação 1 morta no limite exato). ✅ Conforme
3. `[Norma 4.4.2.1.e]` — campo da chave digitada mascarado, sem eco: `app_streamlit.py:96` (`type="password"`); `tests/test_app_streamlit_ui.py:575-` confirma ausência da chave no conteúdo renderizado. ✅ Conforme
4. `[Norma 4.4.13.1.a, 4.4.13.1.q, 4.4.13.1.u]` — allowlist de esquema nos dois caminhos: confirmado pelo sensor (mutação 2 morta). ✅ Conforme
5. `[Norma 4.4.2.1.d]` `[ASVS V14.6]` — credenciais só por parâmetro do construtor: confirmado por grep e pelo sensor (mutação 4 morta). ✅ Conforme
6. Exibição do Perfil ativo (nome/URL/modelo): `app_streamlit.py:82-84`. ✅ Conforme

SSRF residual (aceitar qualquer `http://`/`https://`, incluindo `localhost`) é exceção consciente já registrada em AD-006 do `spec.md`, com justificativa (provedor local como Ollama exige apontar para `localhost`); não é achado novo desta verificação.

**Invariante transversal (revisao-de-impacto-ciclo)** — **não aplicável**. A mudança altera a assinatura de `ChatComMemoria.__init__()` (3 parâmetros novos, opcionais, no fim), mas isso não é o tipo de invariante que o gatilho cobre: não há split de topologia de runtime, nenhuma migração ou mudança de forma de SQL (`persistencia.py` e o schema `threads`/`turnos` não aparecem no diff), nenhuma mudança de modelo de auth (mesmo mecanismo de Bearer key contra endpoint OpenAI-compatível) e o contrato de API/evento não muda porque a adição é aditiva e todos os chamadores existentes (`chat_openai_memoria.py:920,1060`, `exemplos_avancados.py` — 8 ocorrências) usam apenas kwargs já nomeados ou nenhum argumento novo, confirmado por `grep -rn "ChatComMemoria(" --include="*.py" .` e por leitura de cada ocorrência. Nenhum arquivo fora do diff foi verificado como violando um invariante porque não há invariante transversal em jogo.

---

## Fix Plans

Nenhum — PASS limpo, sem gaps.

---

## Requirement Traceability Update

| Requirement | Previous Status | New Status |
| ----------- | ---------------- | ---------- |
| PROV-01 a PROV-15 | Pending / Done (PROV-08, PROV-09) | ✅ Verified (todos) |

---

## Summary

**Overall**: ✅ Ready
**Result**: PASS ✅ — 11/11 ACs, 4/4 mutações mortas, 168/168 testes verdes

**Spec-anchored check**: 11/11 ACs do requisito (CA-PROV-01 a CA-PROV-11) e 15/15 requisitos rastreáveis do spec (PROV-01 a PROV-15) com evidência `file:line`, 0 spec-precision gaps
**Sensor**: 4/4 mutações mortas
**Gate**: 168 passed, 0 failed

**What works**: as 5 fases completas — máscara e exibição do erro técnico, carga de Perfis do ambiente com validação, override por parâmetro no construtor sem mutar `os.environ`, troca pela barra lateral com ordem validar→construir→descartar, e Perfil digitado com os mesmos invariantes.

**Issues found**: nenhum.

**Next steps**: nenhum — feature pronta para push e comentário na PR.
