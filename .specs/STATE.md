# STATE

## Decisions

### AD-001
- **Decision**: `GerenciadorPersistencia` executará cada operação pública em uma conexão SQLite aberta e fechada na thread chamadora.
- **Reason**: O Streamlit preserva o gerenciador entre reruns, mas uma `sqlite3.Connection` não pode ser reutilizada por outra thread com a configuração padrão segura.
- **Trade-off**: Cada operação paga o custo pequeno de abrir a conexão e os testes que usam `:memory:` passam a usar um arquivo temporário.
- **Scope**: Camada `persistencia.py`, CLI e interface Streamlit que a reutilizam.
- **Date**: 2026-09-20
- **Status**: active

## Handoff

