---
name: recurso
description: Avalia o cabimento e redige recurso ou resposta em processo bancário do consumidor nos Juizados do TJBA — recurso inominado, embargos de declaração, contrarrazões ao recurso do banco, embargos contra acórdão da Turma Recursal — com cálculo de prazo, preparo e revisão crítica.
argument-hint: <número do processo> [inominado|embargos|contrarrazoes] [instruções]
---

Trate do recurso no processo `$ARGUMENTS`.

1. **Cabimento e estratégia** (antes de redigir): leia a sentença/acórdão (ou o recurso do banco) e
   `conhecimento/juizados-projudi-ba.md`. Indique:
   - qual medida cabe e por quê (embargos → vícios do art. 48; inominado → reforma; contrarrazões → resposta);
   - prazo e vencimento (`ferramentas/prazo.py`); no inominado, **preparo em 48h** após a interposição ou
     pedido de gratuidade;
   - **custo-benefício**: o que se ganha se provido × risco de honorários de 10-20% se improvido (art. 55),
     para o recurso do consumidor. Se o ganho for pequeno, recomende não recorrer e diga isso.
   - se couber embargos antes do recurso (interrompem o prazo — art. 50), recomende a sequência.
   Se o tipo de recurso não foi informado e houver mais de uma opção razoável, apresente a recomendação ao
   usuário e aguarde a escolha antes de redigir.
2. Delegue a redação ao subagente **redator-pecas** com o modelo correspondente:
   `modelos/recurso-inominado.md`, `modelos/embargos-declaracao.md` ou `modelos/contrarrazoes-recurso-inominado.md`.
3. Envie a minuta ao subagente **revisor-juridico**; aplique as correções CRÍTICO e IMPORTANTE.

Entregue: caminho da minuta, vencimento, preparo/gratuidade, resumo dos fundamentos, pendências.
