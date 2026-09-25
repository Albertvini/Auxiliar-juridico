---
name: intimacoes
description: Rotina diária da Donna — busca as intimações/publicações do advogado no DJEN (por OAB e processos cadastrados) e no Gmail (EXCLUSIVAMENTE e-mails dos remetentes autorizados: PROJUDI/PJe do TJBA e avisos do Jusbrasil/JusIA), faz a triagem e entrega o painel de prazos.
argument-hint: [nuvem] [--dias N]
---

Execute a verificação de intimações. Argumentos: `$ARGUMENTS`.

## 1. Coleta (somente leitura)

- Se `$ARGUMENTS` contiver `nuvem`: use `--desde-dia-util-anterior` e, no e-mail, `--metodo api`.
- Caso contrário: use `--dias N` se informado (senão, o padrão da configuração).

Rode, nesta ordem:
```
python3 ferramentas/donna_dje.py   [--desde-dia-util-anterior | --dias N]
python3 ferramentas/donna_email.py [--desde-dia-util-anterior | --dias N] [--metodo api]
```
Se um dos dois falhar (credencial ausente, rede bloqueada), **não tente outro caminho** (nada de WebFetch no
Gmail, curl, scripts avulsos). Registre a falha no relatório, com a mensagem do script e a providência (ver
README, "Donna — configuração"), e siga com a fonte que funcionou.

**Regra do e-mail:** a Donna só conhece os e-mails que o script gravou em `entrada/`. Não peça, não procure e
não comente outros e-mails. O e-mail é **aviso**: a intimação oficial é a do PROJUDI/DJE. O prazo se conta
pela intimação oficial; se só houver o e-mail, marque `[CONFIRMAR DATA DE CIÊNCIA NO PROJUDI]`.

## 2. Triagem

Siga o fluxo de `/triagem` sobre os arquivos novos de `entrada/`, com estes cuidados:
- **Agrupe por processo**: DJEN + e-mail do mesmo processo e ato = uma intimação só (cite as duas fontes).
- **Prazo de publicação no DJEN:** `prazo.py dje <data de disponibilização> <dias> --comarca <comarca>`.
- **Processo não cadastrado** (sem pasta em `processos/`): liste em destaque; no modo local, ofereça
  `/novo-processo`.
- Publicações em que o cliente **não** é consumidor contra banco (outras matérias): liste em "Outras
  publicações", com prazo, sem análise de mérito.

## 3. Modo nuvem (rotina automática)

Na nuvem, `processos/` não existe (dados de clientes não vão para o repositório). Então:
- **não** crie pastas de processo nem minutas;
- faça a análise **apenas com o texto da publicação/e-mail**, deixando claro que os autos não foram consultados;
- entregue o relatório na própria conversa: é ele que o advogado lê no app.

## 4. Relatório (formato fixo)

```
DONNA — Intimações de <data>
Fontes: DJEN ✔/✖ (<n> novas) · E-mail ✔/✖ (<n> novos; <n> descartados pelo filtro)

VENCIDOS / VENCEM HOJE / URGENTES (≤ 2 dias úteis)
| Vencimento | Processo | Comarca | Ato | Providência | Fonte |

DEMAIS PRAZOS
| ... |

PROCESSOS NÃO CADASTRADOS · OUTRAS PUBLICAÇÕES · FALHAS DE COLETA · PENDÊNCIAS
```
Uma linha por intimação. Sem jurisprudência no relatório. Quando o dia não for útil e nada for encontrado,
responda em uma linha.
