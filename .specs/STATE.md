# STATE

## Decisions

### AD-001
- **Decision**: `GerenciadorPersistencia` executará cada operação pública em uma conexão SQLite aberta e fechada na thread chamadora.
- **Reason**: O Streamlit preserva o gerenciador entre reruns, mas uma `sqlite3.Connection` não pode ser reutilizada por outra thread com a configuração padrão segura.
- **Trade-off**: Cada operação paga o custo pequeno de abrir a conexão e os testes que usam `:memory:` passam a usar um arquivo temporário.
- **Scope**: Camada `persistencia.py`, CLI e interface Streamlit que a reutilizam.
- **Date**: 2026-09-20
- **Status**: active

### AD-002
- **Decision**: Em RF-PROV-01, a Fase 1 é o erro técnico do provedor na tela com mascaramento da chave, e não a carga de Perfis. A superação da decisão da mensagem genérica na documentação entra na mesma fase.
- **Reason**: É a variação que o próprio requisito declara defensável (`docs/requisitos/RF-PROV-01.md`, seção `esforco: G`): sem o texto da exceção, a primeira troca de provedor com URL errada continua mostrando a mensagem fixa e não distingue URL de chave de modelo. `app_streamlit_core.py:sanitizar_erro()` não depende de nenhuma outra parte da entrega.
- **Trade-off**: A entrega observável completa (trocar de provedor pela tela) só aparece na Fase 4. As fases 1 a 3 entregam diagnóstico e contrato, não o gesto de usuário.
- **Scope**: `.specs/features/RF-PROV-01/tasks.md`, ordem das fases.
- **Date**: 2026-09-28
- **Status**: active

### AD-003
- **Decision**: A lógica de Perfis (carga, validação, escolha) fica em `app_streamlit_core.py`, sem módulo novo.
- **Reason**: O requisito autoriza as duas formas ("em `app_streamlit_core.py` (ou em módulo próprio ao lado dele)"). O módulo tem 92 linhas, já não importa `streamlit` e já concentra `construir_sessao_chat()` e `persistencia_ativa()`, que são os pontos de acoplamento da troca.
- **Trade-off**: O módulo passa de ~92 para ~180 linhas. Alternativa descartada: `perfis.py` novo, que acrescentaria um arquivo e um módulo de teste sem ganhar isolamento (nada mais o consome).
- **Scope**: `app_streamlit_core.py`, `tests/test_app_streamlit_core.py`.
- **Date**: 2026-09-28
- **Status**: active

### AD-004
- **Decision**: O comando de gate deste projeto é `.venv/Scripts/python.exe -m pytest tests/`.
- **Reason**: Medido em 2026-09-28: `python -m pytest` devolve `No module named pytest` (é o `C:\Python313` do PATH) e `python3` não existe no Windows. O `.venv` tem pytest 9.1.1 e roda os 112 testes verdes.
- **Trade-off**: O comando é específico da máquina de desenvolvimento. O `tasks.md` da feature anterior cita `python3 -m pytest`, que não executa aqui — divergência registrada, não corrigida retroativamente.
- **Scope**: `Gate Check Commands` de `.specs/features/RF-PROV-01/tasks.md`.
- **Date**: 2026-09-28
- **Status**: active

### AD-005
- **Decision**: Exibir o texto técnico da exceção do provedor na tela é exceção consciente a `[Norma 4.4.1.a, 4.4.1.b]`, que manda erro genérico para o usuário e detalhe só no log interno. A mitigação aceita é o mascaramento obrigatório de toda credencial no texto, coberto por critério de aceite.
- **Reason**: A decisão de desenho de 2026-09-27 supera a mensagem genérica porque o diagnóstico (URL errada x chave inválida x modelo inexistente) é a entrega observável do requisito. A aplicação roda em `localhost`, com um operador único que já possui as credenciais que verá.
- **Trade-off**: Se o app passar a ser servido a mais de um usuário, esta exceção deixa de valer e o texto técnico volta a ser vazamento. Gatilho para reabrir: qualquer bind fora de `localhost`.
- **Scope**: `app_streamlit_core.py:sanitizar_erro()`, critérios PROV-13 a PROV-15.
- **Date**: 2026-09-28
- **Status**: active

### AD-006
- **Decision**: A validação da base URL fica no esquema (`http://` ou `https://`), sem allowlist de domínio nem bloqueio de IP privado.
- **Reason**: Allowlist de domínio contradiz o propósito do requisito, que é apontar para qualquer endpoint compatível com a API OpenAI, inclusive `http://localhost:11434` de Ollama. O esquema é a allowlist mínima que existe e ela bloqueia `file://`, `ftp://` e afins. `[Norma 4.4.13.1.q, 4.4.13.1.u]`
- **Trade-off**: SSRF residual: o operador pode apontar o cliente para um serviço interno da própria rede. Aceito porque a URL vem do operador local, não de terceiro, e o processo já roda com os privilégios dele.
- **Scope**: `ChatComMemoria.__init__()`, carga de Perfis, Perfil digitado.
- **Date**: 2026-09-28
- **Status**: active

### AD-007
- **Decision**: O exit 0 de `checar_rastreabilidade.py` neste projeto não é evidência de rastreabilidade. A conferência da cobertura de `CA-PROV-01` a `CA-PROV-11` no `spec.md` foi feita por `grep` manual e é essa a evidência válida.
- **Reason**: Medido em 2026-09-28: o script imprime `WARN RF-PROV-01.md: nenhum ID de requisito ou critério encontrado` e depois `PASS: nada a conferir`. A causa é o regex dele, `\b(?:CA|RF|RD|RN|PN|US)-\d+[a-z]?\b`, que exige dígito imediatamente após o prefixo. Os IDs deste projeto têm um segmento no meio (`RF-PROV-01`, `CA-PROV-01`), então nunca casam e o script passa a vazio.
- **Trade-off**: O portão de rastreabilidade deste projeto é manual até o regex do script aceitar o formato `PREFIXO-AREA-NN`. Contagem conferida no `spec.md`: CA-PROV-01 (2), 02 a 09 (1 cada), 10 (3), 11 (3) — os 11 critérios presentes.
- **Scope**: Portão de fechamento de todo estágio deste projeto que invoque `checar_rastreabilidade.py`.
- **Date**: 2026-09-28
- **Status**: active

### AD-008
- **Decision**: Em T11 (`tasks.md`), o critério "valor inválido vindo do ambiente continua produzindo a mensagem que cita o `.env`, como hoje" não se aplica a `OPENAI_BASE_URL`. O teste-guarda usa a presença de `OPENAI_BASE_URL` na mensagem, não a string `.env`.
- **Reason**: Lido em `chat_openai_memoria.py` antes da mudança (T10): a mensagem de `OPENAI_BASE_URL` inválida já era `"OPENAI_BASE_URL inválida: '...'. A URL deve começar com http:// ou https://"`, sem a string `.env`, diferente de `OPENAI_API_KEY`/`OPENAI_MODEL` ausentes, que citam `.env` explicitamente ("Crie o arquivo .env com..."). O `tasks.md` generalizou o padrão dos dois primeiros para o terceiro sem conferir o texto atual.
- **Trade-off**: Nenhum comportamento mudou; é só o teste-guarda de T11 que usa o nome da variável de ambiente como discriminador em vez da string `.env`, porque essa string nunca existiu nesse caminho.
- **Scope**: `.specs/features/RF-PROV-01/tasks.md` T11, `tests/test_integracao_chat.py`.
- **Date**: 2026-09-28
- **Status**: active

## Handoff

