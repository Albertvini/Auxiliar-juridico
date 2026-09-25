---
name: analisar-intimacao
description: Analisa uma intimação do PROJUDI/TJBA em processo bancário do consumidor — identifica o ato, calcula o prazo em dias úteis e recomenda a providência (embargos, recurso inominado, contrarrazões, impugnação, audiência, cumprimento).
argument-hint: <número do processo> [evento/arquivo da intimação] [data da ciência AAAA-MM-DD]
---

Analise a intimação indicada em `$ARGUMENTS`.

- Se o processo ainda não tiver pasta em `processos/`, execute antes o fluxo de `/novo-processo`.
- Se o usuário colou o texto da intimação na conversa, salve-o em `processos/<n>/autos/` antes de analisar.
- Delegue a análise ao subagente **analista-intimacoes**, passando: número do processo, arquivo(s) da
  intimação e do ato intimado, data de expedição e data de ciência (se informadas).

Ao receber o resultado, apresente ao usuário:
1. **Vencimento do prazo** (em destaque) e a providência;
2. resumo do ato e do resultado para o consumidor;
3. pendências.

Se a providência for uma peça (impugnação, embargos, recurso, contrarrazões), pergunte se o usuário quer que
a minuta seja redigida agora (`/impugnacao` ou `/recurso`).
