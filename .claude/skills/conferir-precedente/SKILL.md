---
name: conferir-precedente
description: Registra como verificados, no jurisprudencia/indice.md, os precedentes de a-conferir.md que o advogado conferiu e aprovou. Só executa com a confirmação expressa do advogado.
argument-hint: <itens aprovados — ex.: "REsp 1.234.567 e RI 8000...">
---

O advogado informou que conferiu: `$ARGUMENTS`.

1. Localize cada item em `jurisprudencia/a-conferir.md`. Se algum não for encontrado, ou se a descrição do
   advogado divergir do registro (número, tribunal, tese), **pare e pergunte**.
2. Mostre ao advogado, para cada item, a linha exata que será gravada no `indice.md` (identificação, órgão/relator,
   julgamento, matéria, trecho literal, link, "Conferido em <data de hoje> pelo advogado").
3. Grave no `jurisprudencia/indice.md`. O Claude Code pedirá a aprovação do advogado; se ele recusar, não
   insista e não tente outro caminho.
4. Remova os itens gravados de `a-conferir.md`.
5. Se houver minutas com `[A CONFERIR: <item>]`, ofereça converter o marcador em citação normal e rode
   `python3 ferramentas/verificar_citacoes.py` nelas.

Nunca registre como conferido algo que o advogado não confirmou expressamente nesta conversa.
