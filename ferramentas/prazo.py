#!/usr/bin/env python3
"""Calculadora de prazos processuais em dias úteis — Juizados Especiais / PROJUDI-TJBA.

Regras implementadas:
- Contagem em dias úteis (Lei 9.099/95, art. 12-A; CPC, art. 219).
- Exclui o dia do começo e inclui o do vencimento (CPC, art. 224).
- Intimação eletrônica (Lei 11.419/2006, art. 5º): ciência no dia da consulta; consulta em dia não útil vale
  para o primeiro dia útil seguinte; sem consulta, intimação tácita 10 dias corridos após o envio.
- Publicação no DJe (Lei 11.419/2006, art. 4º, §§3º e 4º): publicação no primeiro dia útil seguinte à
  disponibilização; prazo começa no primeiro dia útil seguinte à publicação.
- Suspensão de 20/12 a 20/01 (CPC, art. 220) — ativada por padrão, desativável.
- Feriados nacionais, feriados forenses móveis (Carnaval, Sexta-feira Santa, Corpus Christi), 2 de Julho
  (Independência da Bahia), feriados municipais de Salvador (só com --comarca salvador) e as datas de
  feriados_extras.txt — gerais ou por comarca, pontuais (AAAA-MM-DD) ou anuais (MM-DD).

É uma ferramenta de apoio: suspensões de expediente, indisponibilidade do sistema e portarias do TJBA precisam
ser conferidas no calendário oficial.

Uso:
    python3 ferramentas/prazo.py ciencia 2026-03-02 10
    python3 ferramentas/prazo.py envio 2026-03-02 10        # intimação tácita (sem leitura)
    python3 ferramentas/prazo.py dje 2026-03-02 5
    python3 ferramentas/prazo.py ciencia 2026-03-02 10 --comarca feira-de-santana
    python3 ferramentas/prazo.py ciencia 2026-03-02 10 --sem-recesso
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

ARQUIVO_EXTRAS = Path(__file__).with_name("feriados_extras.txt")

DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def pascoa(ano: int) -> date:
    """Domingo de Páscoa (algoritmo gregoriano anônimo / Meeus-Jones-Butcher)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


def normalizar_comarca(nome: str) -> str:
    import unicodedata
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", nome) if unicodedata.category(c) != "Mn")
    return "-".join(sem_acento.lower().replace("_", " ").split())


def feriados_do_ano(ano: int, comarca: str = "salvador") -> dict[date, str]:
    p = pascoa(ano)
    feriados = {
        date(ano, 1, 1): "Confraternização Universal",
        date(ano, 4, 21): "Tiradentes",
        date(ano, 5, 1): "Dia do Trabalho",
        date(ano, 7, 2): "Independência da Bahia",
        date(ano, 9, 7): "Independência do Brasil",
        date(ano, 10, 12): "Nossa Senhora Aparecida",
        date(ano, 11, 2): "Finados",
        date(ano, 11, 15): "Proclamação da República",
        date(ano, 12, 25): "Natal",
        p - timedelta(days=48): "Carnaval (segunda-feira)",
        p - timedelta(days=47): "Carnaval (terça-feira)",
        p - timedelta(days=2): "Sexta-feira Santa",
        p + timedelta(days=60): "Corpus Christi",
    }
    if ano >= 2024:  # Lei 14.759/2023
        feriados[date(ano, 11, 20)] = "Dia Nacional de Zumbi e da Consciência Negra"
    if normalizar_comarca(comarca) == "salvador":
        feriados[date(ano, 6, 24)] = "São João (Salvador)"
        feriados[date(ano, 12, 8)] = "Nossa Senhora da Conceição da Praia (Salvador)"
    return feriados


def carregar_extras(comarca: str = "salvador", caminho: Path = ARQUIVO_EXTRAS
                    ) -> tuple[dict[date, str], dict[tuple[int, int], str]]:
    """Lê feriados_extras.txt e devolve (datas pontuais, datas anuais) válidas para a comarca.

    Formato de cada linha:  <AAAA-MM-DD | MM-DD> [@comarca] [# descrição]
    Sem @comarca, a data vale para todas as comarcas.
    """
    pontuais: dict[date, str] = {}
    anuais: dict[tuple[int, int], str] = {}
    if not caminho.exists():
        return pontuais, anuais
    alvo = normalizar_comarca(comarca)
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        conteudo, _, descricao = linha.partition("#")
        partes = conteudo.split()
        if not partes:
            continue
        descricao = descricao.strip() or "dia sem expediente (extra)"
        restrita = [normalizar_comarca(p[1:]) for p in partes[1:] if p.startswith("@")]
        if restrita and alvo not in restrita:
            continue
        try:
            if len(partes[0]) == 5:
                mes, dia = (int(x) for x in partes[0].split("-"))
                date(2000, mes, dia)  # valida
                anuais[(mes, dia)] = descricao
            else:
                pontuais[date.fromisoformat(partes[0])] = descricao
        except ValueError:
            print(f"aviso: {caminho.name}:{n} ignorada (data inválida: {partes[0]!r})", file=sys.stderr)
    return pontuais, anuais


@dataclass
class Calendario:
    comarca: str = "salvador"
    recesso: bool = True
    extras: dict[date, str] = field(default_factory=dict)
    anuais: dict[tuple[int, int], str] = field(default_factory=dict)
    _cache: dict[int, dict[date, str]] = field(default_factory=dict, repr=False)

    def motivo_nao_util(self, d: date) -> str | None:
        if d.weekday() >= 5:
            return DIAS_SEMANA[d.weekday()]
        if d in self.extras:
            return self.extras[d]
        if (d.month, d.day) in self.anuais:
            return self.anuais[(d.month, d.day)]
        if d.year not in self._cache:
            self._cache[d.year] = feriados_do_ano(d.year, self.comarca)
        if d in self._cache[d.year]:
            return self._cache[d.year][d]
        if self.recesso and ((d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)):
            return "suspensão de prazos (CPC, art. 220)"
        return None

    def eh_util(self, d: date) -> bool:
        return self.motivo_nao_util(d) is None

    def proximo_util(self, d: date) -> date:
        """Primeiro dia útil estritamente posterior a d."""
        d += timedelta(days=1)
        while not self.eh_util(d):
            d += timedelta(days=1)
        return d

    def util_ou_proximo(self, d: date) -> date:
        return d if self.eh_util(d) else self.proximo_util(d)


@dataclass
class Resultado:
    intimacao: date
    inicio: date
    vencimento: date
    dias: int
    passos: list[str]
    dias_pulados: list[tuple[date, str]]


def calcular(modo: str, data_base: date, dias: int, cal: Calendario) -> Resultado:
    if dias < 1:
        raise ValueError("o prazo deve ter ao menos 1 dia")
    passos: list[str] = []

    if modo == "ciencia":
        intimacao = cal.util_ou_proximo(data_base)
        passos.append(f"Ciência (leitura) em {fmt(data_base)}.")
        if intimacao != data_base:
            passos.append(f"Dia não útil ({cal.motivo_nao_util(data_base)}): intimação considerada em "
                          f"{fmt(intimacao)} (Lei 11.419/2006, art. 5º, §2º).")
    elif modo == "envio":
        tacita = data_base + timedelta(days=10)
        intimacao = cal.util_ou_proximo(tacita)
        passos.append(f"Envio/disponibilização em {fmt(data_base)}; sem leitura, intimação tácita no 10º dia "
                      f"corrido: {fmt(tacita)} (Lei 11.419/2006, art. 5º, §3º).")
        if intimacao != tacita:
            passos.append(f"10º dia não útil ({cal.motivo_nao_util(tacita)}): prorrogado para {fmt(intimacao)}.")
        passos.append("Se o advogado leu antes do 10º dia, use o modo 'ciencia' com a data da leitura.")
    elif modo == "dje":
        intimacao = cal.proximo_util(data_base)
        passos.append(f"Disponibilização no DJe em {fmt(data_base)}; publicação no primeiro dia útil seguinte: "
                      f"{fmt(intimacao)} (Lei 11.419/2006, art. 4º, §3º).")
    else:
        raise ValueError(f"modo desconhecido: {modo}")

    inicio = cal.proximo_util(intimacao)
    passos.append(f"Exclui-se o dia da intimação; 1º dia do prazo: {fmt(inicio)} (CPC, art. 224).")

    pulados: list[tuple[date, str]] = []
    atual, contados = inicio, 1
    while contados < dias:
        atual += timedelta(days=1)
        motivo = cal.motivo_nao_util(atual)
        if motivo is None:
            contados += 1
        elif atual.weekday() < 5:
            pulados.append((atual, motivo))
    passos.append(f"Contados {dias} dias úteis: vencimento em {fmt(atual)}.")
    return Resultado(intimacao, inicio, atual, dias, passos, pulados)


def fmt(d: date) -> str:
    return f"{d.strftime('%d/%m/%Y')} ({DIAS_SEMANA[d.weekday()]})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prazo em dias úteis — Juizados / PROJUDI-TJBA")
    parser.add_argument("modo", choices=["ciencia", "envio", "dje"],
                        help="ciencia = data da leitura; envio = data de envio (tácita); dje = disponibilização")
    parser.add_argument("data", help="data base no formato AAAA-MM-DD")
    parser.add_argument("dias", type=int, help="prazo em dias úteis (ex.: 5 embargos, 10 recurso inominado)")
    parser.add_argument("--comarca", default="salvador",
                        help="comarca do processo (padrão: salvador); define os feriados municipais aplicados")
    parser.add_argument("--sem-recesso", action="store_true",
                        help="não aplica a suspensão de 20/12 a 20/01")
    args = parser.parse_args(argv)

    try:
        data_base = date.fromisoformat(args.data)
    except ValueError:
        parser.error("data inválida; use AAAA-MM-DD")

    pontuais, anuais = carregar_extras(args.comarca)
    cal = Calendario(comarca=args.comarca, recesso=not args.sem_recesso, extras=pontuais, anuais=anuais)
    locais = [d for d in anuais] + [d for d in pontuais if d.year >= data_base.year]
    if normalizar_comarca(args.comarca) != "salvador" and not locais:
        print(f"ATENÇÃO: nenhum feriado municipal cadastrado para a comarca '{args.comarca}' em "
              f"ferramentas/feriados_extras.txt. Cadastre-os (formato: MM-DD @{normalizar_comarca(args.comarca)} "
              f"# descrição) ou confira manualmente.\n")
    r = calcular(args.modo, data_base, args.dias, cal)

    print(f"PRAZO DE {r.dias} DIAS ÚTEIS — comarca: {args.comarca}")
    for i, passo in enumerate(r.passos, 1):
        print(f"  {i}. {passo}")
    if r.dias_pulados:
        print("  Dias úteis da semana desconsiderados:")
        for d, motivo in r.dias_pulados:
            print(f"     - {fmt(d)}: {motivo}")
    print(f"\n>>> VENCIMENTO: {fmt(r.vencimento)}")
    print("\nConfira no calendário oficial do TJBA: portarias de suspensão, indisponibilidade do PROJUDI, "
          "feriados municipais da comarca e ponto facultativo (ex.: Quarta-feira de Cinzas).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
