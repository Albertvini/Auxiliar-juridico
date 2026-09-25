# Auxiliar Jurídico — Direito Bancário do Consumidor (PROJUDI/TJBA)

Agente para o **Claude Code** especializado em Direito Bancário na defesa do consumidor, voltado à análise de
processos nos Juizados Especiais do TJBA (PROJUDI): análise de intimações, análise de contestações de bancos,
redação de impugnações e recursos.

## Como usar

1. Abra esta pasta no Claude Code (terminal, app desktop ou claude.ai/code).
2. Baixe do PROJUDI os documentos do processo (PDF) e cadastre:
   ```
   /novo-processo 0001234-56.2026.8.05.0001 ~/Downloads/processo
   ```
3. Use os comandos:

| Comando | Para quê |
|---|---|
| `/analisar-intimacao <processo> [evento] [data da ciência]` | O que foi decidido, prazo e providência |
| `/analisar-contestacao <processo>` | Mapa da defesa do banco, rebates e provas |
| `/impugnacao <processo>` | Minuta da impugnação à contestação (com revisão) |
| `/recurso <processo> [inominado\|embargos\|contrarrazoes]` | Cabimento, custo-benefício e minuta (com revisão) |
| `/revisar <minuta>` | Revisão crítica antes do protocolo |

Também é possível conversar livremente ("o banco juntou um contrato com selfie, como impugno?"). O agente
consulta a base em `conhecimento/`.

## Estrutura

```
CLAUDE.md                  # instruções do agente (persona, regras, método, estilo)
.claude/agents/            # subagentes: analista-intimacoes, analista-contestacao, redator-pecas, revisor-juridico
.claude/skills/            # comandos /novo-processo, /analisar-intimacao, /analisar-contestacao, /impugnacao, /recurso, /revisar
conhecimento/              # rito dos Juizados, legislação, súmulas/temas, teses por matéria, defesas dos bancos
modelos/                   # impugnação, recurso inominado, embargos, contrarrazões
processos/                 # um diretório por processo (NÃO versionado — sigilo/LGPD)
ferramentas/prazo.py       # prazo em dias úteis (Lei 9.099/95, art. 12-A; Lei 11.419/2006, art. 5º)
ferramentas/extrair_texto.py  # texto dos PDFs do PROJUDI
```

### Calculadora de prazos

```
python3 ferramentas/prazo.py ciencia 2026-04-01 10   # leitura da intimação em 01/04, prazo de 10 dias úteis
python3 ferramentas/prazo.py envio   2026-04-01 5    # sem leitura: intimação tácita após 10 dias corridos
python3 ferramentas/prazo.py dje     2026-04-01 5    # disponibilização no DJe
```

Considera feriados nacionais, Carnaval, Sexta-feira Santa, Corpus Christi, 2 de Julho, feriados de Salvador
(`--municipio outro` para outras comarcas) e a suspensão de 20/12 a 20/01 (`--sem-recesso` para desligar).
Portarias do TJBA e feriados locais vão em `ferramentas/feriados_extras.txt`. Testes: `cd ferramentas && pytest`.

Para ler PDFs, instale o `poppler-utils` (`pdftotext`) ou `pip install pypdf`.

## Limites — leia

- O agente **não acessa o PROJUDI**: você baixa os documentos e protocola as peças.
- Tudo que ele produz é **minuta para revisão** do advogado responsável.
- Ele é instruído a **não inventar jurisprudência**: precedentes locais aparecem como `[INSERIR PRECEDENTE ...]`
  com sugestão de busca. Súmulas e temas vêm da base em `conhecimento/sumulas-e-temas.md` — mantenha-a
  atualizada (súmulas são canceladas, teses revistas, normas do INSS/BACEN mudam).
- Confira sempre os prazos no calendário oficial do TJBA.
