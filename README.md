# Donna — Direito Bancário do Consumidor (PROJUDI/TJBA)

**Donna** é uma agente para o **Claude Code** especializada em Direito Bancário na defesa do consumidor. Ela
busca as intimações no Diário de Justiça e no seu e-mail, analisa intimações e contestações de bancos nos
Juizados do TJBA (Salvador e interior) e redige impugnações e recursos, com **travas técnicas contra
jurisprudência inventada e contra ações fora do escopo**.

## Rotina sugerida (para ganhar tempo)

1. **Expediente do dia:** `/intimacoes`. A Donna busca as publicações da OAB 68.210/BA no DJEN e os e-mails de
   intimação (só dos remetentes autorizados), faz a triagem e entrega o painel. Nos dias úteis ela também roda
   sozinha, ao meio-dia, na nuvem (ver "Donna — configuração"). Intimações baixadas à mão vão em `entrada/`,
   com `/triagem`.
2. **Peças:** escolha o que redigir (`/impugnacao`, `/recurso`). O agente redige, pesquisa precedentes em
   paralelo, passa a minuta pelo revisor e pelo verificador de citações, e entrega a minuta com as pendências.
3. **Conferência:** confira os precedentes marcados `[A CONFERIR]` (link e trecho literal já vêm prontos) e
   diga `/conferir-precedente`. Eles passam a ser citáveis em todos os processos futuros.
4. **Qualquer hora:** `/painel` para ver todos os prazos.

| Comando | Para quê |
|---|---|
| `/intimacoes [--dias N]` | DJEN + e-mail → triagem → painel |
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

## Donna — configuração do DJE e do e-mail

Dados não secretos (OAB, conta, remetentes autorizados) ficam em `config/donna.toml`. **Senhas nunca vão para o
repositório nem para a conversa.**

### E-mail: só intimações
A Donna só lê e-mails de `projudi@tjba.jus.br`, `pje@tjba.jus.br` e `responda@jusbrasil.com.br`. Deste
último, só os que têm assunto de intimação, publicação, processo ou prazo, porque o Jusbrasil também manda
propaganda. A busca é filtrada no servidor, o remetente exato é conferido antes de baixar o conteúdo, e os
demais e-mails nunca são abertos. O acesso é **somente leitura**: nada é enviado, apagado, movido ou marcado
como lido. Para incluir um remetente, peça à Donna; a alteração exige a sua aprovação.

### No seu computador (IMAP)
1. Ative a verificação em duas etapas na conta Google e crie uma **senha de app**
   (Conta Google → Segurança → Senhas de app).
2. Crie o arquivo `~/.donna/credenciais.env` (fora do repositório), com a linha
   `DONNA_GMAIL_SENHA_APP=<senha de app>`. A Donna não consegue ler esse arquivo; só o script usa.
3. No Gmail, confirme que o IMAP está ativo (Configurações → Encaminhamento e POP/IMAP).
4. Teste: `python3 ferramentas/donna_email.py --dias 7` e `python3 ferramentas/donna_dje.py --dias 7`.

### Na nuvem (rotina automática de dias úteis ao meio-dia)
O ambiente em nuvem só permite HTTPS, então o Gmail é lido pela **API do Gmail com escopo somente leitura**.
1. No Google Cloud Console: ative a Gmail API, configure a tela de consentimento (publique como
   "Em produção" para o token não expirar em 7 dias) e crie um ID do cliente OAuth do tipo "App para computador".
2. No seu computador: `python3 ferramentas/donna_gmail_autorizar.py <CLIENT_ID> <CLIENT_SECRET>`. O script
   só aceita o escopo somente leitura e mostra três valores.
3. No ambiente da nuvem (claude.ai/code → configurações do ambiente):
   - **Segredos/variáveis:** `DONNA_GMAIL_CLIENT_ID`, `DONNA_GMAIL_CLIENT_SECRET`, `DONNA_GMAIL_REFRESH_TOKEN`.
   - **Acesso à rede:** liberar `comunicaapi.pje.jus.br`, `gmail.googleapis.com` e `oauth2.googleapis.com`
     (e, para a pesquisa de jurisprudência, os sites do STJ, STF, TJBA e Jusbrasil).
4. Na nuvem não existem os dados dos processos (não vão para o GitHub). Por isso a rotina entrega um
   **relatório de triagem e prazos** com base no texto das publicações; análises profundas e minutas são feitas
   no seu computador.

### DJE
A consulta usa o **DJEN (Diário de Justiça Eletrônico Nacional, do CNJ)**, que permite buscar por OAB. Ela
depende de o TJBA publicar as comunicações no DJEN; na primeira execução real, compare com o DJE do TJBA por
alguns dias. Se alguma publicação aparecer só no DJE do TJBA, me avise, e eu adapto a busca ao portal do
tribunal.

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
CLAUDE.md                     # regras da Donna (fontes, escopo, método, estilo)
config/donna.toml             # OAB, conta de e-mail, remetentes autorizados (sem senhas)
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
