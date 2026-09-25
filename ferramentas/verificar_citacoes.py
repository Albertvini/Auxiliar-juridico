#!/usr/bin/env python3
"""Verificador de citações — impede jurisprudência e "entendimentos" sem fonte em análises e minutas.

Fontes aceitas (a "base verificada"):
- conhecimento/*.md                      (súmulas, temas, enunciados e precedentes da base do projeto)
- jurisprudencia/indice.md               (decisões conferidas pelo advogado)
- processos/<n>/autos/* e ficha.md       (números e decisões que constam dos próprios autos)

Regras:
- BLOQUEANTE: súmula, tema, enunciado ou precedente (REsp, AREsp, RE, ADI, número CNJ...) que não consta da base
  verificada, ou que consta como CANCELADO/SUPERADO.
- BLOQUEANTE: afirmação de entendimento jurisprudencial ("jurisprudência pacífica", "a Turma tem entendido",
  "o STJ firmou"...) em parágrafo sem nenhuma citação verificada.
- Um parágrafo marcado com [INSERIR ...], [A CONFERIR ...], [VERIFICAR ...] ou [CONFIRMAR ...] é tratado como
  pendência declarada: não bloqueia, mas aparece como AVISO para o advogado resolver.
- AVISO: súmula/tema citado sem indicar o tribunal.

Uso:
    python3 ferramentas/verificar_citacoes.py processos/<n>/minutas/2026-09-25-impugnacao.md
Código de saída: 0 = sem bloqueios; 1 = há bloqueios; 2 = erro de uso.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

TRIBUNAIS = r"STJ|STF|TST|TSE|TNU|TJBA|FONAJE|CJF|FONAJEF"
NUM = r"(?:n[º°o]?\.?\s*)?"
LISTA = r"(\d{1,4}(?:\s*(?:,|e)\s*\d{1,4})*)"
SUFIXO_TRIB = rf"(?:\s*(?:/|do|da|-)\s*({TRIBUNAIS}))?"

PADRAO_SV = re.compile(rf"S[úu]mulas?\s+Vinculantes?\s+{NUM}{LISTA}", re.I)
PADRAO_SUMULA = re.compile(rf"S[úu]mulas?\s+(?!Vinculante){NUM}{LISTA}{SUFIXO_TRIB}", re.I)
PADRAO_TEMA = re.compile(rf"\bTemas?\s+{NUM}{LISTA}{SUFIXO_TRIB}", re.I)
PADRAO_ENUNCIADO = re.compile(rf"\bEnunciados?\s+{NUM}{LISTA}{SUFIXO_TRIB}", re.I)
PADRAO_PRECEDENTE = re.compile(
    r"\b(REsp|AREsp|EAREsp|EREsp|AgInt|AgRg|EDcl|RE|ARE|ADI|ADC|ADPF|RMS|Rcl|IRDR|IAC|IUJ|PUIL|RR)"
    r"\s+(?:n[º°o]?\.?\s*)?(\d{1,3}(?:\.\d{3})+|\d{3,9})"
)
PADRAO_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")

MARCADOR_PENDENCIA = re.compile(r"\[(INSERIR|A CONFERIR|VERIFICAR|CONFIRMAR)\b", re.I)
MARCA_CANCELADA = re.compile(r"cancelad[ao]|superad[ao]|revogad[ao]", re.I)

AFIRMACOES_DE_ENTENDIMENTO = [
    r"jurisprud[êe]ncia\s+(?:\w+\s+)?(?:pac[íi]fica|majorit[áa]ria|dominante|consolidada|firme|remansosa|"
    r"iterativa|uniforme|assente|farta|torrencial|sedimentada)",
    r"entendimento\s+(?:\w+\s+)?(?:pac[íi]fico|majorit[áa]rio|dominante|consolidado|firme|prevalente|"
    r"predominante|corrente|assente|uniforme|sedimentado|remansoso)",
    r"\b(?:é|está|encontra-se)\s+(?:\w+\s+)?pac[íi]fic[oa]",
    r"\b(?:tem|vem|têm|vêm)\s+(?:reiteradamente\s+|firmemente\s+)?(?:entendido|decidido|reconhecido|firmado|"
    r"assentado|admitido|se\s+posicionado|se\s+manifestado)",
    r"\b(?:tribunais|turmas?\s+recursa(?:l|is)|TJBA|TJ-?BA|STJ|STF|Corte\s+Especial|Superior\s+Tribunal|"
    r"Supremo|colendo|egr[ée]gio)\s+(?:j[áa]\s+)?(?:entende|entendem|firmou|firmaram|pacificou|consolidou|"
    r"decidiu|decide|reconhece|reconhecem|admite|admitem|sedimentou|assentou|orienta)",
    r"orienta[çc][ãa]o\s+jurisprudencial",
    r"precedentes?\s+(?:desta|deste|da|do|dessa|desse)\s+(?:Turma|Corte|Tribunal|TJBA|STJ|STF|C[âa]mara)",
    r"\b(?:uníssona|uníssono|unânimes?)\b",
    r"\bEMENTA\b",
]
PADRAO_AFIRMACAO = re.compile("|".join(f"(?:{p})" for p in AFIRMACOES_DE_ENTENDIMENTO), re.I)


@dataclass(frozen=True)
class Citacao:
    tipo: str        # sumula | sv | tema | enunciado | precedente | cnj
    numero: str
    tribunal: str | None
    texto: str
    linha: int


def _numeros(lista: str) -> list[str]:
    return re.findall(r"\d{1,4}", lista)


def extrair_citacoes(texto: str) -> list[Citacao]:
    achadas: list[Citacao] = []
    for n_linha, linha in enumerate(texto.splitlines(), 1):
        ocupado: list[tuple[int, int]] = []
        for m in PADRAO_SV.finditer(linha):
            ocupado.append(m.span())
            for n in _numeros(m.group(1)):
                achadas.append(Citacao("sv", n, "STF", m.group(0).strip(), n_linha))
        for tipo, padrao in (("sumula", PADRAO_SUMULA), ("tema", PADRAO_TEMA), ("enunciado", PADRAO_ENUNCIADO)):
            for m in padrao.finditer(linha):
                if any(a <= m.start() < b for a, b in ocupado):
                    continue
                trib = m.group(2).upper() if m.group(2) else None
                if tipo == "enunciado" and trib is None and re.search(r"FONAJE", linha, re.I):
                    trib = "FONAJE"
                for n in _numeros(m.group(1)):
                    achadas.append(Citacao(tipo, n, trib, m.group(0).strip(), n_linha))
        for m in PADRAO_PRECEDENTE.finditer(linha):
            achadas.append(Citacao("precedente", m.group(2).replace(".", ""), m.group(1).upper(),
                                   m.group(0).strip(), n_linha))
        for m in PADRAO_CNJ.finditer(linha):
            achadas.append(Citacao("cnj", m.group(0), None, m.group(0), n_linha))
    return achadas


@dataclass
class Base:
    validas: set[tuple[str, str, str | None]]
    canceladas: set[tuple[str, str, str | None]]

    def _casa(self, conjunto: set, c: Citacao) -> bool:
        for tipo, numero, trib in conjunto:
            if tipo != c.tipo or numero != c.numero:
                continue
            if c.tipo == "precedente":
                if trib == c.tribunal or {trib, c.tribunal} <= {"RE", "ARE"}:
                    return True
                continue
            if trib is None or c.tribunal is None or trib == c.tribunal:
                return True
        return False

    def valida(self, c: Citacao) -> bool:
        return self._casa(self.validas, c)

    def cancelada(self, c: Citacao) -> bool:
        return self._casa(self.canceladas, c)


def fontes_da_base(arquivo: Path, raiz: Path = RAIZ) -> list[Path]:
    fontes = sorted((raiz / "conhecimento").glob("*.md"))
    indice = raiz / "jurisprudencia" / "indice.md"
    if indice.exists():
        fontes.append(indice)
    try:
        partes = arquivo.resolve().relative_to(raiz.resolve()).parts
    except ValueError:
        partes = ()
    if len(partes) >= 2 and partes[0] == "processos":
        pasta = raiz / "processos" / partes[1]
        fontes += [p for p in (pasta / "autos").rglob("*") if p.suffix.lower() in {".txt", ".md"}]
        if (pasta / "ficha.md").exists():
            fontes.append(pasta / "ficha.md")
    return fontes


def carregar_base(fontes: list[Path], nome_pasta_processo: str | None = None) -> Base:
    validas: set = set()
    canceladas: set = set()
    for fonte in fontes:
        for linha in fonte.read_text(encoding="utf-8", errors="ignore").splitlines():
            destino = canceladas if MARCA_CANCELADA.search(linha) else validas
            for c in extrair_citacoes(linha):
                destino.add((c.tipo, c.numero, c.tribunal))
    if nome_pasta_processo and PADRAO_CNJ.fullmatch(nome_pasta_processo):
        validas.add(("cnj", nome_pasta_processo, None))
    # "Súmula 30" sem tribunal na base não pode liberar "Súmula 30/STF" quando a base sabe que é a 30/STJ.
    for conjunto in (validas, canceladas):
        com_tribunal = {(t, n) for t, n, trib in conjunto if trib is not None}
        conjunto.difference_update({(t, n, None) for t, n in com_tribunal})
    return Base(validas, canceladas)


@dataclass
class Achado:
    nivel: str   # BLOQUEANTE | AVISO
    linha: int
    mensagem: str


def _paragrafos(texto: str) -> list[tuple[int, str]]:
    blocos, atual, inicio = [], [], 1
    for n, linha in enumerate(texto.splitlines(), 1):
        if linha.strip():
            if not atual:
                inicio = n
            atual.append(linha)
        elif atual:
            blocos.append((inicio, "\n".join(atual)))
            atual = []
    if atual:
        blocos.append((inicio, "\n".join(atual)))
    return blocos


def verificar_texto(texto: str, base: Base) -> list[Achado]:
    achados: list[Achado] = []
    for inicio, paragrafo in _paragrafos(texto):
        pendente = bool(MARCADOR_PENDENCIA.search(paragrafo))
        citacoes = extrair_citacoes(paragrafo)
        tem_citacao_valida = False
        for c in citacoes:
            linha = inicio + c.linha - 1
            if base.cancelada(c) and not base.valida(c):
                achados.append(Achado("BLOQUEANTE", linha, f'"{c.texto}" consta como CANCELADA/SUPERADA na base.'))
            elif base.cancelada(c):
                achados.append(Achado("AVISO", linha, f'"{c.texto}": a base registra cancelamento/superação — '
                                                      "confirme a vigência."))
            elif base.valida(c):
                tem_citacao_valida = True
                if c.tipo in {"sumula", "tema"} and c.tribunal is None:
                    achados.append(Achado("AVISO", linha, f'"{c.texto}" sem tribunal indicado (ex.: /STJ).'))
            elif pendente:
                achados.append(Achado("AVISO", linha, f'"{c.texto}" não verificado, marcado como pendência — '
                                                      "conferir antes do protocolo."))
            else:
                achados.append(Achado("BLOQUEANTE", linha, f'"{c.texto}" não consta da base verificada '
                                      "(conhecimento/, jurisprudencia/indice.md ou autos do processo). "
                                      "Remova ou marque [A CONFERIR: fonte/link]."))
        m = PADRAO_AFIRMACAO.search(paragrafo)
        if m:
            linha = inicio + paragrafo[:m.start()].count("\n")
            if pendente:
                achados.append(Achado("AVISO", linha, f'afirmação de entendimento "{m.group(0)}" com fonte '
                                                      "pendente — conferir."))
            elif not tem_citacao_valida:
                achados.append(Achado("BLOQUEANTE", linha, f'afirmação de entendimento "{m.group(0)}" sem fonte '
                                      "verificada no parágrafo. Cite a fonte da base ou marque "
                                      "[INSERIR PRECEDENTE ...]."))
    return achados


def verificar_arquivo(arquivo: Path, raiz: Path = RAIZ) -> list[Achado]:
    try:
        partes = arquivo.resolve().relative_to(raiz.resolve()).parts
        pasta = partes[1] if len(partes) >= 2 and partes[0] == "processos" else None
    except ValueError:
        pasta = None
    base = carregar_base(fontes_da_base(arquivo, raiz), pasta)
    return verificar_texto(arquivo.read_text(encoding="utf-8"), base)


def relatorio(arquivo: Path, achados: list[Achado]) -> str:
    linhas = [f"VERIFICAÇÃO DE CITAÇÕES — {arquivo}"]
    for a in sorted(achados, key=lambda a: (a.nivel != "BLOQUEANTE", a.linha)):
        linhas.append(f"  {a.nivel:<10} linha {a.linha}: {a.mensagem}")
    bloq = sum(a.nivel == "BLOQUEANTE" for a in achados)
    avisos = len(achados) - bloq
    linhas.append(f"Resultado: {bloq} bloqueante(s), {avisos} aviso(s)."
                  + (" Nenhuma citação sem fonte." if not achados else ""))
    return "\n".join(linhas)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    codigo = 0
    for nome in argv:
        arquivo = Path(nome)
        if not arquivo.exists():
            print(f"arquivo não encontrado: {arquivo}")
            return 2
        achados = verificar_arquivo(arquivo)
        print(relatorio(arquivo, achados))
        if any(a.nivel == "BLOQUEANTE" for a in achados):
            codigo = 1
    return codigo


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
