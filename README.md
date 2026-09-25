# Auxiliar Jurídico — Direito Bancário do Consumidor (PROJUDI/TJBA)

Agente para o **Claude Code** especializado em Direito Bancário na defesa do consumidor. Ele analisa
intimações e contestações de bancos nos Juizados do TJBA (Salvador e interior) e redige impugnações e recursos,
com **travas técnicas contra jurisprudência inventada e contra ações fora do escopo**.

## Rotina sugerida (para ganhar tempo)

1. **Expediente do dia:** baixe do PROJUDI as intimações novas, coloque em `entrada/` e rode `/triagem`.
   Você recebe o painel de prazos e uma linha por intimação (ato · resultado · providência · vencimento).
2. **Peças:** escolha o que redigir (`/impugnacao`, `/recurso`). O agente redige, pesquisa precedentes em
   paralelo, passa a minuta pelo revisor e pelo verificador de citações, e entrega a minuta com as pendências.
3. **Conferência:** confira os precedentes marcados `[A CONFERIR]` (link e trecho literal já vêm prontos) e
   diga `/conferir-precedente`. Eles passam a ser citáveis em todos os processos futuros.
4. **Qualquer hora:** `/painel` para ver todos os prazos.

| Comando | Para quê |
|---|---|
| `/triagem [data da ciência]` | Lote de intimações de `entrada/` → análises + painel |
| `/painel` | Prazos de todos os processos, por urgência |
| `/novo-processo <nº> [pasta]` | Cadastra um processo |
| `/analisar-intimacao <nº>` | Ato, prazo e providência |
| `/analisar-contestacao <nº>` | Mapa da defesa do banco e rebates |
| `/impugnacao <nº>` | Minuta da réplica (com pesquisa, revisão e verificação) |
| `/recurso <nº> [tipo]` | Cabimento, custo-benefício e minuta |
| `/pesquisar-jurisprudencia <tese>` | Precedentes reais, com link e trecho literal |
| `/conferir-precedente <itens>` | Registra precedentes que você conferiu |
| `/revisar <minuta>` | Parecer crítico antes do protocolo |

## Garantias contra jurisprudência falsa

| Camada | O que faz |
|---|---|
| **Regras** (`CLAUDE.md`, subagentes) | Proíbem criar precedentes ou atribuir entendimentos sem fonte; só vale o que foi conferido |
| **Verificador** (`ferramentas/verificar_citacoes.py`) | Roda **automaticamente** a cada análise ou minuta gravada. Bloqueia súmula, tema, enunciado, REsp/RE/ADI, número CNJ etc. fora da base verificada, súmula cancelada e frases como "jurisprudência pacífica" ou "a Turma tem entendido" sem fonte no parágrafo |
| **Fluxo de conferência** (`jurisprudencia/`) | O que é pesquisado vai para `a-conferir.md` (link + trecho literal) e só vira citável quando você aprova a gravação no `indice.md` |
| **Revisor** | Confere se o **conteúdo** atribuído ao precedente é fiel (o verificador confere o número) |

**Importante:** a base inicial (`conhecimento/sumulas-e-temas.md`) foi redigida pelo assistente. Confira cada
enunciado uma vez no site oficial e marque "✔ conferido". Até lá, trate-a como rascunho.

## Garantias de escopo (guardião)

`ferramentas/hooks/guardiao.py` é executado pelo Claude Code **antes de cada ação** (configurado em
`.claude/settings.json`):

- **Grava livremente só** em `processos/<n>/`, `entrada/` e `jurisprudencia/a-conferir.md`.
- **Base do agente** (conhecimento, modelos, regras, jurisprudência conferida, ferramentas): o Claude Code
  **pede sua aprovação** em cada alteração.
- **Bloqueado:** gravar fora do projeto; acessar PROJUDI/PJe/e-SAJ; sites fora da lista jurídica (`*.jus.br`,
  `*.gov.br`, `*.leg.br`, Jusbrasil, Conjur, Migalhas, OAB); pesquisas com CPF, número de processo ou nome de
  cliente; curl/wget/ssh/e-mail; conectores MCP e publicações; apagar ou mover documentos dos autos;
  `git add -f` (dados de clientes) e push forçado.

**Modo manutenção** (para você mexer livremente na estrutura do agente): abra o Claude Code com
`AUXILIAR_MANUTENCAO=1 claude`. O guardião fica desligado nessa sessão. Use só para manutenção, nunca para
trabalhar em processos.

## Prazos

```
python3 ferramentas/prazo.py ciencia 2026-04-01 10                      # Salvador (padrão)
python3 ferramentas/prazo.py ciencia 2026-04-01 10 --comarca feira-de-santana
python3 ferramentas/prazo.py envio   2026-04-01 5                       # intimação tácita (10 dias corridos)
python3 ferramentas/prazo.py dje     2026-04-01 5
python3 ferramentas/painel_prazos.py                                    # painel de todas as fichas
```

Já considera feriados nacionais, Carnaval, Sexta-feira Santa, Corpus Christi, 2 de Julho, 20 de novembro,
feriados de Salvador e a suspensão de 20/12 a 20/01. **Feriados das comarcas do interior e portarias do TJBA**
são cadastrados em `ferramentas/feriados_extras.txt` (ex.: `MM-DD @vitoria-da-conquista # padroeiro`). Se faltar,
o agente avisa.

## Estrutura

```
CLAUDE.md                     # regras do agente (fontes, escopo, método, estilo)
.claude/settings.json         # guardião (hooks) e permissões
.claude/agents/               # analista-intimacoes, analista-contestacao, redator-pecas, revisor-juridico, pesquisador-jurisprudencia
.claude/skills/               # os comandos da tabela acima
conhecimento/                 # rito dos Juizados, legislação, súmulas/temas, teses, defesas dos bancos
jurisprudencia/               # indice.md (conferida), a-conferir.md (pesquisada), decisoes/ (não versionada)
modelos/                      # impugnação, recurso inominado, embargos, contrarrazões
processos/  entrada/          # dados de clientes (NÃO versionados — sigilo/LGPD)
ferramentas/                  # prazo, painel, verificador, extrator de PDF, guardião + testes
```

Testes: `cd ferramentas && pytest`. Leitura de PDFs: instale `poppler-utils` (`pdftotext`) ou `pip install pypdf`.

## Limites

- O agente **não acessa o PROJUDI** e **não protocola**: você baixa os documentos e protocola as peças.
- Tudo o que ele produz é **minuta para revisão** do advogado responsável.
- O verificador detecta citações e frases de "entendimento" por padrões de texto. Uma formulação muito
  incomum pode escapar, e por isso existe a revisão. A leitura final é sempre sua.
