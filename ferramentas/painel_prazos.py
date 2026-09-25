#!/usr/bin/env python3
"""Painel de prazos: reúne a tabela "Prazos em aberto" de todas as fichas em processos/*/ficha.md.

Ordena por vencimento, calcula quantos dias úteis faltam (pela comarca da ficha) e grava
processos/painel-prazos.md. Linhas com status "cumprido", "protocolado", "encerrado" ou "cancelado" são omitidas.

Uso:
    python3 ferramentas/painel_prazos.py            # hoje como referência
    python3 ferramentas/painel_prazos.py 2026-10-01 # outra data de referência
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from prazo import Calendario, carregar_extras, fmt, normalizar_comarca

RAIZ = Path(__file__).resolve().parent.parent
ENCERRADOS = re.compile(r"cumprid|protocolad|encerrad|cancelad|conclu", re.I)
DATA_BR = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


@dataclass
class Prazo:
    processo: str
    comarca: str
    providencia: str
    vencimento: date | None
    status: str
    dias_uteis_restantes: int | None = None


def comarca_da_ficha(texto: str) -> str:
    m = re.search(r"\|\s*Comarca \(para prazos\)\s*\|\s*([^|\[\]]+?)\s*\|", texto)
    if m:
        return normalizar_comarca(m.group(1))
    m = re.search(r"Comarca de ([A-ZÀ-Úa-zà-ú ]+?)\s*(?:\||$)", texto, re.M)
    return normalizar_comarca(m.group(1)) if m else "salvador"


def ler_prazos(ficha: Path) -> list[Prazo]:
    texto = ficha.read_text(encoding="utf-8")
    comarca = comarca_da_ficha(texto)
    secao = re.search(r"^## Prazos em aberto\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not secao:
        return []
    prazos = []
    for linha in secao.group(1).splitlines():
        celulas = [c.strip() for c in linha.strip().strip("|").split("|")]
        if len(celulas) < 4 or set(celulas[0]) <= {"-", " ", ":"} or celulas[0].lower().startswith("provid"):
            continue
        providencia, _ciencia, vencimento, status = celulas[:4]
        if not providencia or ENCERRADOS.search(status):
            continue
        m = DATA_BR.search(vencimento)
        venc = date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None
        prazos.append(Prazo(ficha.parent.name, comarca, providencia, venc, status))
    return prazos


def dias_uteis_entre(hoje: date, fim: date, cal: Calendario) -> int:
    """Dias úteis de amanhã até o vencimento (inclusive); negativo se já venceu."""
    if fim < hoje:
        return -sum(1 for i in range(1, (hoje - fim).days + 1) if cal.eh_util(hoje - timedelta(days=i - 1)))
    return sum(1 for i in range(1, (fim - hoje).days + 1) if cal.eh_util(hoje + timedelta(days=i)))


def montar_painel(hoje: date, raiz: Path = RAIZ) -> tuple[str, list[Prazo]]:
    prazos: list[Prazo] = []
    for ficha in sorted((raiz / "processos").glob("*/ficha.md")):
        if ficha.parent.name.startswith("_"):
            continue
        prazos += ler_prazos(ficha)
    calendarios: dict[str, Calendario] = {}
    for p in prazos:
        if p.vencimento:
            if p.comarca not in calendarios:
                pontuais, anuais = carregar_extras(p.comarca)
                calendarios[p.comarca] = Calendario(comarca=p.comarca, extras=pontuais, anuais=anuais)
            p.dias_uteis_restantes = dias_uteis_entre(hoje, p.vencimento, calendarios[p.comarca])
    prazos.sort(key=lambda p: (p.vencimento is None, p.vencimento or date.max))

    linhas = [f"# Painel de prazos — referência {fmt(hoje)}", "",
              "| Alerta | Vencimento | Dias úteis | Processo | Comarca | Providência | Status |",
              "|---|---|---|---|---|---|---|"]
    for p in prazos:
        if p.vencimento is None:
            alerta, venc, restam = "SEM DATA", "[CONFIRMAR]", "—"
        else:
            d = p.dias_uteis_restantes
            alerta = "VENCIDO" if p.vencimento < hoje else "HOJE" if p.vencimento == hoje else \
                "URGENTE" if d <= 2 else "ATENÇÃO" if d <= 5 else "ok"
            venc, restam = fmt(p.vencimento), str(d)
        linhas.append(f"| {alerta} | {venc} | {restam} | {p.processo} | {p.comarca} | {p.providencia} | {p.status} |")
    if not prazos:
        linhas.append("| — | — | — | nenhum prazo em aberto nas fichas | — | — | — |")
    linhas += ["", "Gerado a partir das fichas. Confira cada prazo no PROJUDI e no calendário do TJBA."]
    return "\n".join(linhas) + "\n", prazos


def main(argv: list[str]) -> int:
    hoje = date.fromisoformat(argv[0]) if argv else date.today()
    texto, _ = montar_painel(hoje)
    destino = RAIZ / "processos" / "painel-prazos.md"
    destino.write_text(texto, encoding="utf-8")
    print(texto)
    print(f"(gravado em {destino.relative_to(RAIZ)})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
