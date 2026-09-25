#!/usr/bin/env python3
"""Donna — busca publicações no Diário de Justiça Eletrônico Nacional (DJEN/CNJ).

Consulta pública e somente leitura (API Comunica PJe do CNJ), por:
- número de OAB e UF do advogado (config/donna.toml);
- números dos processos cadastrados em processos/ (quando existirem).
Filtra pelos tribunais configurados (padrão: TJBA) e grava cada publicação nova como .txt em entrada/.

Prazo de publicação em diário eletrônico: considera-se publicada no primeiro dia útil seguinte à
disponibilização, e o prazo começa no primeiro dia útil seguinte (Lei 11.419/2006, art. 4º, §§3º e 4º) —
use `prazo.py dje <data de disponibilização> <dias>`.

Uso:
  python3 ferramentas/donna_dje.py
  python3 ferramentas/donna_dje.py --desde-dia-util-anterior
  python3 ferramentas/donna_dje.py --dias 7
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import date

from donna_comum import (carregar_config, chave, data_inicial, gravar_na_entrada, html_para_texto, ja_registrado,
                         numeros_cnj, processos_cadastrados)

API = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"
ITENS_POR_PAGINA = 100
MAX_PAGINAS = 20


def _campo(item: dict, *nomes: str, padrao: str = "") -> str:
    for nome in nomes:
        valor = item.get(nome)
        if valor not in (None, ""):
            return str(valor)
    return padrao


def consultar(params: dict, abrir=urllib.request.urlopen) -> list[dict]:
    itens: list[dict] = []
    for pagina in range(1, MAX_PAGINAS + 1):
        consulta = urllib.parse.urlencode({**params, "pagina": pagina, "itensPorPagina": ITENS_POR_PAGINA})
        req = urllib.request.Request(f"{API}?{consulta}", headers={"User-Agent": "Donna/1.0 (consulta DJEN)"})
        with abrir(req, timeout=40) as r:
            dados = json.load(r)
        lote = dados.get("items") or dados.get("itens") or []
        itens += lote
        if len(lote) < ITENS_POR_PAGINA:
            break
        time.sleep(0.5)
    return itens


def normalizar_item(item: dict) -> dict:
    processo = _campo(item, "numeroprocessocommascara", "numero_processo", "numeroProcesso")
    cnjs = numeros_cnj(processo)
    advogados = []
    for d in item.get("destinatarioadvogados") or []:
        adv = d.get("advogado", d) if isinstance(d, dict) else {}
        if adv:
            advogados.append(f"{adv.get('nome', '')} (OAB {adv.get('numero_oab', '')}/{adv.get('uf_oab', '')})")
    return {
        "id": _campo(item, "id", "hash", "numeroComunicacao"),
        "tribunal": _campo(item, "siglaTribunal", "sigla_tribunal").upper(),
        "processo": cnjs[0] if cnjs else processo,
        "disponibilizacao": _campo(item, "data_disponibilizacao", "datadisponibilizacao", "dataDisponibilizacao")[:10],
        "orgao": _campo(item, "nomeOrgao", "nome_orgao"),
        "tipo": _campo(item, "tipoComunicacao", "tipo_comunicacao"),
        "documento": _campo(item, "tipoDocumento", "tipo_documento"),
        "classe": _campo(item, "nomeClasse", "nome_classe"),
        "link": _campo(item, "link"),
        "advogados": "; ".join(advogados),
        "texto": html_para_texto(_campo(item, "texto")),
    }


def buscar(cfg: dict, desde: date, ate: date, abrir=urllib.request.urlopen) -> dict:
    periodo = {"dataDisponibilizacaoInicio": f"{desde:%Y-%m-%d}", "dataDisponibilizacaoFim": f"{ate:%Y-%m-%d}"}
    tribunais = {t.upper() for t in cfg["dje"].get("tribunais", [])}
    brutos: list[dict] = []
    oab = str(cfg["advogado"].get("oab", "")).replace(".", "").strip()
    if oab:
        brutos += consultar({**periodo, "numeroOab": oab, "ufOab": cfg["advogado"].get("uf", "BA")}, abrir)
    cadastrados = processos_cadastrados() if cfg["dje"].get("conferir_processos_cadastrados") else []
    for numero in cadastrados:
        brutos += consultar({**periodo, "numeroProcesso": numero.replace("-", "").replace(".", "")}, abrir)

    stats = {"encontradas": 0, "outros_tribunais": 0, "repetidas": 0, "novas": [], "nao_cadastrados": set()}
    vistos: set[str] = set()
    for bruto in brutos:
        item = normalizar_item(bruto)
        identificador = chave(f"djen-{item['id']}-{item['processo']}-{item['disponibilizacao']}")
        if identificador in vistos:
            continue
        vistos.add(identificador)
        stats["encontradas"] += 1
        if tribunais and item["tribunal"] not in tribunais:
            stats["outros_tribunais"] += 1
            continue
        if ja_registrado(identificador):
            stats["repetidas"] += 1
            continue
        if cadastrados and item["processo"] not in cadastrados:
            stats["nao_cadastrados"].add(item["processo"])
        nome = f"djen-{item['disponibilizacao']}-{identificador}.txt"
        gravar_na_entrada(nome, {
            "Origem": "DJEN — Diário de Justiça Eletrônico Nacional (CNJ)",
            "Tribunal": item["tribunal"],
            "Órgão": item["orgao"],
            "Processo": item["processo"],
            "Classe": item["classe"],
            "Tipo de comunicação": item["tipo"],
            "Documento": item["documento"],
            "Data de disponibilização": item["disponibilizacao"],
            "Prazo": f"calcular com: prazo.py dje {item['disponibilizacao']} <dias> --comarca <comarca>",
            "Advogados intimados": item["advogados"],
            "Link": item["link"],
            "Identificador": identificador,
        }, item["texto"])
        stats["novas"].append(nome)
    return stats


def main(argv: list[str] | None = None) -> int:
    cfg = carregar_config()
    ap = argparse.ArgumentParser(description="Donna — publicações no DJEN por OAB e processos cadastrados")
    ap.add_argument("--dias", type=int, default=cfg["dje"].get("dias", 3))
    ap.add_argument("--desde-dia-util-anterior", action="store_true")
    args = ap.parse_args(argv)
    hoje = date.today()
    desde = data_inicial(hoje, args.dias, args.desde_dia_util_anterior)
    try:
        stats = buscar(cfg, desde, hoje)
    except Exception as erro:  # noqa: BLE001
        print(f"DJEN: não foi possível consultar ({type(erro).__name__}: {erro}). Confira manualmente em "
              "https://comunica.pje.jus.br e no DJE do TJBA.")
        return 1
    print(f"DJEN de {desde:%d/%m/%Y} a {hoje:%d/%m/%Y} — OAB {cfg['advogado'].get('oab')}/{cfg['advogado'].get('uf')}"
          f" + {len(processos_cadastrados())} processo(s) cadastrado(s)")
    print(f"  publicações: {stats['encontradas']} | de outros tribunais: {stats['outros_tribunais']} | "
          f"já registradas: {stats['repetidas']} | novas: {len(stats['novas'])}")
    for nome in stats["novas"]:
        print(f"  + entrada/{nome}")
    if stats["nao_cadastrados"]:
        print("  ATENÇÃO — processos com publicação que ainda não estão cadastrados: "
              + ", ".join(sorted(stats["nao_cadastrados"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
