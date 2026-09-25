---
name: painel
description: Mostra o painel consolidado de prazos de todos os processos (vencidos, hoje, urgentes, atenção), calculado em dias úteis pela comarca de cada processo.
argument-hint: [data de referência AAAA-MM-DD]
---

Rode `python3 ferramentas/painel_prazos.py $ARGUMENTS` e apresente o painel, começando por VENCIDO, HOJE e
URGENTE. Para cada prazo urgente, indique a providência e se já existe minuta em `processos/<n>/minutas/`.
Aponte fichas com prazo sem data (`SEM DATA`) e comarcas do interior sem feriado municipal cadastrado em
`ferramentas/feriados_extras.txt`. Não altere fichas neste comando.
