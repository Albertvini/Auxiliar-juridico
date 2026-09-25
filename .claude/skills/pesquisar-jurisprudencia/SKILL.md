---
name: pesquisar-jurisprudencia
description: Pesquisa jurisprudência real (STJ, STF, TJBA, Turmas Recursais, outros TJs) sobre uma tese bancária do consumidor, em fontes oficiais e confiáveis, registrando cada precedente com link e trecho literal para conferência do advogado. Nunca cria jurisprudência.
argument-hint: <tese a pesquisar> [número do processo onde será usada]
---

Pesquise precedentes para: `$ARGUMENTS`.

1. Reformule o pedido em 1 a 3 **teses objetivas** (ex.: "cartão RMC — ausência de informação — conversão em
   consignado comum — Turma Recursal TJBA"). Não inclua dados do cliente nas buscas.
2. Veja antes se `jurisprudencia/indice.md` ou `jurisprudencia/a-conferir.md` já têm algo sobre a tese e
   informe, para evitar retrabalho.
3. Acione o subagente **pesquisador-jurisprudencia** (uma chamada por tese; teses independentes em paralelo).
4. Apresente ao advogado a tabela de achados (favoráveis e contrários) e peça a conferência: "Quando conferir,
   diga `/conferir-precedente` com os itens aprovados."

Lembre ao advogado: nada do que foi pesquisado pode ser citado como verificado antes da conferência.
