---
# A fila que o `code_agent_loop` executa, na ordem. Copie para `itens` no `.agent-loop.toml`.
fila: [RF-PROV-01]
gerado_em: 2026-09-27
---

# Fila de execução

Um item só. Não há dependência a ordenar, então não há desempate a declarar.

| # | ID | Título | Depende de | Critérios | Status |
|---|---|---|---|---|---|
| 1 | RF-PROV-01 | Troca de provedor de LLM em runtime pela tela | — | CA-PROV-01 a CA-PROV-11 | pendente |

**Decisão de granularidade (dono, 2026-09-27):** a feature inteira é um requisito, e o corte em unidades
de trabalho fica no `tasks.md` da `tlc-spec-driven`, não na fila. O laço abre uma sessão de implementação
por marcador `<!-- FASE: N -->`, então é ali que o tamanho de cada PR é controlado. Consequência aceita:
o gate `verificar` roda uma vez, sobre os 11 critérios de aceite de uma vez, com teto de 3 rodadas.

Entrega observável declarada no requisito: trocar de provedor pela barra lateral e conversar contra ele na
mesma sessão do navegador, com o erro do provedor diagnosticável na tela.

## Fora da fila (e por quê)

| Escopo | Motivo |
|---|---|
| Provedor AWS Bedrock nativo | Tem plano e branch próprios, parados, e depende de um backend que não existe no `main`. Não virou requisito. |
| Troca de provedor na CLI | O `.env` antes de subir já é o fluxo natural lá, e não paga restart de sessão de navegador. |
| `temperature` e `max_tokens` no seletor | Continuam vindo do ambiente, onde as ressalvas de modelo de reasoning já estão documentadas. |
| Gravar o provedor na thread | Sem vínculo entre thread e provedor por decisão do desenho, logo sem coluna nova e sem migração. |
| Persistir em disco o Perfil escolhido ou os valores digitados | O override é de sessão. |
| Subir o app sem o ambiente obrigatório completo | Default do desenho é manter a exigência, porque o `Padrão (.env)` é construído no start. |

## Ciclos detectados

Nenhum. Grafo de um nó, sem aresta.
