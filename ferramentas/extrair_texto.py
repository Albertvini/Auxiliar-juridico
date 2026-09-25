#!/usr/bin/env python3
"""Extrai o texto dos PDFs baixados do PROJUDI, gravando um .txt ao lado de cada PDF.

Tenta, nesta ordem: `pdftotext` (poppler-utils), a biblioteca `pypdf`. PDFs digitalizados (imagem) não têm
texto — o script avisa, e o arquivo deve ser lido como imagem ou passar por OCR (ex.: `ocrmypdf`).

Uso:
    python3 ferramentas/extrair_texto.py processos/0001234-56.2026.8.05.0001/autos
    python3 ferramentas/extrair_texto.py arquivo.pdf
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

MINIMO_CARACTERES = 200  # abaixo disso, provavelmente é PDF digitalizado


def extrair(pdf: Path) -> str:
    if shutil.which("pdftotext"):
        saida = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True)
        if saida.returncode == 0:
            return saida.stdout
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("instale o poppler-utils (pdftotext) ou `pip install pypdf`") from None
    leitor = PdfReader(str(pdf))
    return "\n\f".join(pagina.extract_text() or "" for pagina in leitor.pages)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    alvo = Path(argv[0])
    pdfs = sorted(alvo.rglob("*.pdf")) if alvo.is_dir() else [alvo]
    if not pdfs:
        print(f"nenhum PDF encontrado em {alvo}")
        return 1
    falhas = 0
    for pdf in pdfs:
        destino = pdf.with_suffix(".txt")
        try:
            texto = extrair(pdf)
        except Exception as erro:  # noqa: BLE001 — relatar e seguir para o próximo arquivo
            print(f"ERRO   {pdf}: {erro}")
            falhas += 1
            continue
        destino.write_text(texto, encoding="utf-8")
        aviso = "  <- pouco texto: provável digitalização, ler como imagem/OCR" \
            if len(texto.strip()) < MINIMO_CARACTERES else ""
        print(f"ok     {destino} ({len(texto.strip())} caracteres){aviso}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
