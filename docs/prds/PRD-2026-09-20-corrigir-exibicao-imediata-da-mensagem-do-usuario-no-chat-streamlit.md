# PRD — Corrigir exibição imediata da mensagem do usuário no chat Streamlit

**Data:** 2026-09-20  
**Autor(es):** Claude  
**Status:** rascunho

> **TL;DR.** A mensagem digitada pela pessoa usuária deve aparecer na área do chat assim que é enviada, permanecer visível durante a geração da resposta e ser seguida — não substituída — pela fala do assistente, em qualquer interação.

---

## Contexto

O chat com memória possui uma interface web em Streamlit cujo fluxo de renderização e envio vive em `app_streamlit.py::main()`. O histórico é renderizado antes do campo de entrada; a lógica de negócio (anexar mensagens, chamar a API e persistir) está em `chat_openai_memoria.py` e é acionada por `enviar_mensagem_seguro` (`app_streamlit_core.py`). O objeto de conversa é mantido em `st.session_state['chat']` e preservado entre renderizações. O público afetado são estudantes e pessoas que experimentam o chat pela interface web.

## Problema

Ao pressionar Enter, a mensagem do usuário só aparece na tela junto com a resposta do assistente. A causa verificada: `enviar_mensagem_seguro` executa de forma síncrona e bloqueante o turno completo — anexa a fala do usuário ao histórico, faz o round-trip à API OpenAI e anexa a resposta — e só então ocorre o `st.rerun()` que redesenha a interface. Durante toda a latência da API a tela permanece no estado anterior, sem a fala recém-digitada, passando a impressão de que a mensagem foi perdida.

## Objetivo

Renderizar a mensagem do usuário imediatamente após o envio, antes de a resposta ser processada, mantendo-a visível durante o processamento e exibindo a resposta do assistente em seguida, sem regressões de persistência nem de tratamento de erro.

## Escopo

- Ajustar o fluxo de renderização/envio na camada de wiring (`app_streamlit.py`) para pintar a fala do usuário antes da resolução da resposta.
- Sinalizar visualmente o processamento da resposta (ex.: indicador de carregamento) enquanto a mensagem do usuário permanece na tela.
- Preservar o tratamento de erro sanitizado existente (`st.error` com mensagem amigável) e a inserção/persistência única do turno.

## Fora de escopo

- Alterar a lógica de geração de resposta do assistente em `chat_openai_memoria.py` (anexar mensagens, chamada à API, contagem de tokens).
- Introduzir streaming da resposta na UI ou processamento assíncrono.
- Mudanças na persistência (`persistencia.py`), no modo terminal ou no gerenciamento/continuidade de conversas.
- Redesenho visual da interface além do necessário para o feedback de processamento.

## Requisitos funcionais

- **RF-01.** Ao enviar (Enter ou botão de envio), a mensagem do usuário deve ser renderizada imediatamente na área do chat, antes de a resposta começar a ser gerada.
- **RF-02.** A mensagem do usuário deve permanecer visível durante todo o processamento da resposta.
- **RF-03.** A resposta do assistente deve ser exibida após a mensagem do usuário, sem sobrescrevê-la nem ocultá-la.
- **RF-04.** Deve haver indicação de que a resposta está sendo processada enquanto a mensagem do usuário já está na tela.
- **RF-05.** O comportamento deve se repetir de forma consistente em interações consecutivas, sem duplicar mensagens no histórico.
- **RF-06.** Em caso de falha na geração, o erro sanitizado deve ser exibido sem remover a mensagem do usuário já mostrada.

## Critérios de aceite

- **CA-01.** Enviar uma mensagem faz a fala do usuário aparecer imediatamente na área do chat.
- **CA-02.** A fala do usuário permanece visível enquanto a resposta é processada/gerada.
- **CA-03.** A resposta do assistente aparece após a mensagem do usuário, sem sobrescrever ou ocultar a mensagem anterior.
- **CA-04.** O comportamento é consistente em múltiplas interações consecutivas.
- **CA-05.** Nenhuma mensagem é duplicada no histórico nem gravada duas vezes na persistência.
- **CA-06.** Erros de geração continuam exibidos de forma sanitizada, mantendo a mensagem do usuário visível.

## Impactos/restrições técnicas relevantes

- A correção deve ficar na camada de wiring (`app_streamlit.py`), sem tocar na lógica de geração de resposta.
- Não deve introduzir atrasos perceptíveis adicionais.
- `user` e `assistant` são anexados atomicamente por `enviar_mensagem`, e `adicionar_mensagem`/`enviar_mensagem` têm efeitos colaterais de persistência (criação de thread, gravação de mensagens e de tokens do turno). Qualquer pré-renderização da fala do usuário **não** pode duplicar a inserção no histórico nem gravar duas vezes.
- Streamlit `>=1.28.0` (já disponível), com suporte a `st.chat_message`, `st.chat_input`, `st.status`/`st.spinner` e `st.rerun`. O objeto de conversa em `st.session_state` é preservado entre reruns.
- Não há código assíncrono; a geração é síncrona e bloqueante. O modo `stream` de `ChatComMemoria` escreve no stdout do terminal, não na UI web.
- A suíte de testes usa `streamlit.testing.v1.AppTest` mockando `enviar_mensagem_seguro` e verifica `chat_message`/`error`; deve continuar validando exibição da fala do usuário, exibição posterior da resposta, erro sanitizado e chamada única a `construir_sessao_chat`.

## Riscos e pontos de atenção

- **Dupla persistência/duplicação de histórico:** um padrão de "mensagem pendente" com rerun mal implementado pode re-anexar ou re-gravar o turno. Garantir inserção e persistência únicas.
- **Regressão de testes:** mudanças no fluxo de `main()` podem quebrar os testes de UI e de rerun/persistência; ajustá-los conforme o novo fluxo mantendo as garantias atuais.
- **Consistência entre reruns:** assegurar que o estado pendente seja limpo corretamente para não repintar ou reprocessar mensagens em runs subsequentes.
- **Feedback de processamento:** o indicador de carregamento não deve mascarar erros nem permanecer preso caso a geração falhe.
- **Segurança:** superfície baixa; a entrada continua renderizada sem `unsafe_allow_html` e os erros permanecem sanitizados — manter esses comportamentos.
