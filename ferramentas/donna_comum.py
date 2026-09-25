"""Funções comuns da Donna: configuração, credenciais, texto e gravação na caixa de entrada."""

from __future__ import annotations

import hashlib
import html
import os
import re
import tomllib
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from prazo import Calendario, carregar_extras

RAIZ = Path(__file__).resolve().parent.parent
ARQ_CONFIG = RAIZ / "config" / "donna.toml"
ENTRADA = RAIZ / "entrada"
# Credenciais locais ficam FORA do repositório.
ARQ_CREDENCIAIS = Path(os.environ.get("DONNA_CREDENCIAIS", Path.home() / ".donna" / "credenciais.env"))


def carregar_config(caminho: Path = ARQ_CONFIG) -> dict:
    with open(caminho, "rb") as f:
        return tomllib.load(f)


def credencial(nome: str) -> str | None:
    """Lê uma credencial da variável de ambiente ou de ~/.donna/credenciais.env (NOME=valor)."""
    valor = os.environ.get(nome)
    if valor:
        return valor.strip()
    if ARQ_CREDENCIAIS.exists():
        for linha in ARQ_CREDENCIAIS.read_text(encoding="utf-8").splitlines():
            chave, sep, v = linha.partition("=")
            if sep and chave.strip() == nome:
                return v.strip().strip('"').strip("'")
    return None


def normalizar(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


def html_para_texto(conteudo: str) -> str:
    conteudo = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", conteudo)
    conteudo = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>|</h\d>", "\n", conteudo)
    conteudo = re.sub(r"<[^>]+>", " ", conteudo)
    conteudo = html.unescape(conteudo)
    conteudo = re.sub(r"[ \t\xa0]+", " ", conteudo)
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", conteudo).strip()


PADRAO_CNJ = re.compile(r"\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")
PADRAO_CNJ_SEM_MASCARA = re.compile(r"\b(\d{7})(\d{2})(\d{4})(\d)(\d{2})(\d{4})\b")


def numeros_cnj(texto: str) -> list[str]:
    achados = PADRAO_CNJ.findall(texto)
    achados += ["{}-{}.{}.{}.{}.{}".format(*m.groups()) for m in PADRAO_CNJ_SEM_MASCARA.finditer(texto)]
    return list(dict.fromkeys(achados))


def processos_cadastrados(raiz: Path = RAIZ) -> list[str]:
    pasta = raiz / "processos"
    if not pasta.exists():
        return []
    return sorted(p.name for p in pasta.iterdir() if p.is_dir() and PADRAO_CNJ.fullmatch(p.name))


def chave(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def ja_registrado(identificador: str, raiz: Path = RAIZ) -> bool:
    """Evita duplicar: procura o identificador no nome de arquivos da entrada e dos autos."""
    padrao = f"*{identificador}*"
    if any((raiz / "entrada").glob(padrao)):
        return True
    return any((raiz / "processos").glob(f"*/autos/{padrao}"))


def gravar_na_entrada(nome: str, cabecalho: dict[str, str], corpo: str, raiz: Path = RAIZ) -> Path:
    destino = raiz / "entrada" / nome
    destino.parent.mkdir(parents=True, exist_ok=True)
    linhas = [f"{k}: {v}" for k, v in cabecalho.items() if v]
    destino.write_text("\n".join(linhas) + "\n" + "-" * 72 + "\n" + corpo.strip() + "\n", encoding="utf-8")
    return destino


def dia_util_anterior(hoje: date, comarca: str = "salvador") -> date:
    pontuais, anuais = carregar_extras(comarca)
    cal = Calendario(comarca=comarca, extras=pontuais, anuais=anuais, recesso=False)
    d = hoje - timedelta(days=1)
    while not cal.eh_util(d):
        d -= timedelta(days=1)
    return d


def data_inicial(hoje: date, dias: int | None, desde_dia_util_anterior: bool) -> date:
    if desde_dia_util_anterior:
        return dia_util_anterior(hoje)
    return hoje - timedelta(days=max((dias or 1) - 1, 0))
