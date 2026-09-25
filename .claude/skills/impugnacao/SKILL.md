---
name: impugnacao
description: Redige a impugnação/réplica à contestação do banco (ou manifestação sobre documentos) em favor do consumidor, no rito dos Juizados Especiais do TJBA, e a submete a revisão crítica.
argument-hint: <número do processo> [instruções específicas]
---

Redija a impugnação à contestação do processo `$ARGUMENTS`.

1. Verifique se existe `processos/<n>/analises/*analise-contestacao*.md`. Se não existir, execute primeiro o
   fluxo de `/analisar-contestacao` (subagente **analista-contestacao**).
2. Verifique o prazo da manifestação na ficha; se não estiver calculado, calcule com `ferramentas/prazo.py`.
3. Delegue a redação ao subagente **redator-pecas**, indicando: peça = impugnação à contestação; modelo =
   `modelos/impugnacao-contestacao.md`; análise a seguir; instruções adicionais do usuário.
   Para os pontos que dependem de precedente, acione **em paralelo** o subagente **pesquisador-jurisprudencia**
   (uma tese por chamada) e passe os marcadores `[A CONFERIR: ...]` ao redator.
4. Em seguida, envie a minuta ao subagente **revisor-juridico**. Aplique você mesmo as correções classificadas
   como CRÍTICO e IMPORTANTE e registre as SUGESTÕES não aplicadas.

Entregue ao usuário: caminho da minuta, vencimento do prazo, resumo das teses, resultado do verificador de
citações (0 bloqueantes) e lista de pendências `[CONFIRMAR]`/`[INSERIR]`/`[A CONFERIR]`.
