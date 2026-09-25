#!/usr/bin/env python3
"""Donna — busca intimações no Gmail, lendo EXCLUSIVAMENTE e-mails dos remetentes autorizados.

Garantias:
- A busca já é filtrada no servidor pelos remetentes de config/donna.toml.
- Antes de baixar qualquer conteúdo, confere o remetente EXATO (cabeçalho From) e, quando configurado, o assunto.
  E-mails reprovados são descartados sem que o corpo seja baixado, e nada deles é gravado ou exibido.
- Somente leitura: IMAP em modo EXAMINE com BODY.PEEK (não marca como lido); a API usa o escopo gmail.readonly.
  Nada é enviado, apagado, movido ou marcado.
- Cada e-mail aprovado vira um .txt em entrada/, para a /triagem.

Métodos:
  imap  (computador) — credencial DONNA_GMAIL_SENHA_APP (senha de app do Google)
  api   (nuvem)      — credenciais DONNA_GMAIL_CLIENT_ID, DONNA_GMAIL_CLIENT_SECRET, DONNA_GMAIL_REFRESH_TOKEN

Uso:
  python3 ferramentas/donna_email.py                       # últimos N dias (config)
  python3 ferramentas/donna_email.py --desde-dia-util-anterior
  python3 ferramentas/donna_email.py --metodo api --dias 2
"""

from __future__ import annotations

import argparse
import base64
import email
import imaplib
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr, parsedate_to_datetime

from donna_comum import (carregar_config, chave, credencial, data_inicial, gravar_na_entrada, html_para_texto,
                         ja_registrado, normalizar, numeros_cnj)

MESES_IMAP = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ------------------------------------------------------------------------------------------------ filtro
@dataclass
class Filtro:
    remetentes: set[str]
    termos_assunto: dict[str, list[str]]

    @classmethod
    def da_config(cls, cfg: dict) -> "Filtro":
        remetentes = {r.strip().lower() for r in cfg["email"]["remetentes"]}
        termos = {k.strip().lower(): [normalizar(t) for t in v]
                  for k, v in cfg["email"].get("filtro_assunto", {}).items()}
        return cls(remetentes, termos)

    def aprova(self, remetente_bruto: str, assunto: str) -> tuple[bool, str]:
        endereco = parseaddr(remetente_bruto)[1].strip().lower()
        if endereco not in self.remetentes:
            return False, "remetente não autorizado"
        termos = self.termos_assunto.get(endereco)
        if termos and not any(t in normalizar(assunto) for t in termos):
            return False, "assunto não trata de intimação"
        return True, endereco


def decodificar(valor: str | None) -> str:
    if not valor:
        return ""
    try:
        return str(make_header(decode_header(valor)))
    except Exception:  # noqa: BLE001 — cabeçalho malformado
        return valor


def texto_do_email(msg: Message) -> str:
    planos, htmls = [], []
    partes = msg.walk() if msg.is_multipart() else [msg]
    for parte in partes:
        if parte.get_content_maintype() == "multipart" or parte.get_filename():
            continue
        carga = parte.get_payload(decode=True)
        if carga is None:
            continue
        texto = carga.decode(parte.get_content_charset() or "utf-8", errors="replace")
        (htmls if parte.get_content_type() == "text/html" else planos).append(texto)
    if planos and any(p.strip() for p in planos):
        return "\n\n".join(planos).strip()
    return html_para_texto("\n".join(htmls))


def anexos(msg: Message) -> list[str]:
    return [decodificar(p.get_filename()) for p in msg.walk() if p.get_filename()]


def registrar(msg: Message, endereco: str, identificador: str) -> str:
    assunto = decodificar(msg.get("Subject"))
    try:
        quando = parsedate_to_datetime(msg.get("Date")).strftime("%Y-%m-%d %H:%M")
    except Exception:  # noqa: BLE001
        quando = decodificar(msg.get("Date"))
    corpo = texto_do_email(msg)
    processos = numeros_cnj(assunto + "\n" + corpo)
    nome = f"email-{quando[:10]}-{identificador}.txt"
    gravar_na_entrada(nome, {
        "Origem": "E-mail (intimação/aviso — NÃO é a intimação oficial; conferir no PROJUDI/DJE)",
        "Remetente": endereco,
        "Assunto": assunto,
        "Recebido em": quando,
        "Processo(s) mencionado(s)": ", ".join(processos) or "[não identificado no e-mail]",
        "Anexos (não baixados)": ", ".join(anexos(msg)),
        "Identificador": identificador,
    }, corpo)
    return nome


# ------------------------------------------------------------------------------------------------ IMAP
def buscar_imap(cfg: dict, filtro: Filtro, desde: date, conexao=None) -> dict:
    conta = cfg["email"]["conta"]
    stats = {"verificados": 0, "descartados": 0, "novos": [], "repetidos": 0}
    if conexao is None:
        senha = credencial("DONNA_GMAIL_SENHA_APP")
        if not senha:
            raise RuntimeError("credencial DONNA_GMAIL_SENHA_APP não configurada (ver README, 'Donna — configuração').")
        conexao = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        conexao.login(conta, senha)
    try:
        conexao.select(f'"{cfg["email"].get("pasta_imap", "INBOX")}"', readonly=True)  # EXAMINE
        data_imap = f"{desde.day:02d}-{MESES_IMAP[desde.month - 1]}-{desde.year}"
        uids: list[bytes] = []
        for remetente in sorted(filtro.remetentes):
            tipo, dados = conexao.uid("SEARCH", None, "SINCE", data_imap, "FROM", f'"{remetente}"')
            if tipo == "OK" and dados and dados[0]:
                uids += dados[0].split()
        for uid in dict.fromkeys(uids):
            stats["verificados"] += 1
            tipo, dados = conexao.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT MESSAGE-ID)])")
            cab = email.message_from_bytes(_bytes_da_resposta(dados))
            ok, endereco = filtro.aprova(decodificar(cab.get("From")), decodificar(cab.get("Subject")))
            if not ok:
                stats["descartados"] += 1
                continue
            identificador = chave(cab.get("Message-ID") or f"{conta}-{uid.decode()}")
            if ja_registrado(identificador):
                stats["repetidos"] += 1
                continue
            tipo, dados = conexao.uid("FETCH", uid, "(BODY.PEEK[])")
            msg = email.message_from_bytes(_bytes_da_resposta(dados))
            stats["novos"].append(registrar(msg, endereco, identificador))
    finally:
        try:
            conexao.logout()
        except Exception:  # noqa: BLE001
            pass
    return stats


def _bytes_da_resposta(dados) -> bytes:
    for item in dados or []:
        if isinstance(item, tuple) and len(item) >= 2:
            return item[1]
    return b""


# ------------------------------------------------------------------------------------------------ API
class GmailAPI:
    BASE = "https://gmail.googleapis.com/gmail/v1/users/me"

    def __init__(self):
        faltam = [n for n in ("DONNA_GMAIL_CLIENT_ID", "DONNA_GMAIL_CLIENT_SECRET", "DONNA_GMAIL_REFRESH_TOKEN")
                  if not credencial(n)]
        if faltam:
            raise RuntimeError(f"credenciais não configuradas: {', '.join(faltam)} (ver README, 'Donna — configuração').")
        corpo = urllib.parse.urlencode({
            "client_id": credencial("DONNA_GMAIL_CLIENT_ID"),
            "client_secret": credencial("DONNA_GMAIL_CLIENT_SECRET"),
            "refresh_token": credencial("DONNA_GMAIL_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        }).encode()
        with urllib.request.urlopen("https://oauth2.googleapis.com/token", data=corpo, timeout=30) as r:
            resposta = json.load(r)
        if "gmail.readonly" not in resposta.get("scope", "") or "gmail.modify" in resposta.get("scope", ""):
            raise RuntimeError("o token não é somente leitura (escopo gmail.readonly). Gere-o novamente com "
                               "ferramentas/donna_gmail_autorizar.py.")
        self.token = resposta["access_token"]

    def get(self, caminho: str, **params) -> dict:
        consulta = urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(f"{self.BASE}/{caminho}?{consulta}",
                                     headers={"Authorization": f"Bearer {self.token}"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)


def buscar_api(cfg: dict, filtro: Filtro, desde: date, api=None) -> dict:
    api = api or GmailAPI()
    stats = {"verificados": 0, "descartados": 0, "novos": [], "repetidos": 0}
    consulta = f"from:({' OR '.join(sorted(filtro.remetentes))}) after:{desde:%Y/%m/%d}"
    ids, pagina = [], None
    while True:
        params = {"q": consulta, "maxResults": 100, **({"pageToken": pagina} if pagina else {})}
        resp = api.get("messages", **params)
        ids += [m["id"] for m in resp.get("messages", [])]
        pagina = resp.get("nextPageToken")
        if not pagina:
            break
    for mid in ids:
        stats["verificados"] += 1
        meta = api.get(f"messages/{mid}", format="metadata", metadataHeaders=["From", "Subject", "Message-ID"])
        cab = {h["name"].lower(): h["value"] for h in meta.get("payload", {}).get("headers", [])}
        ok, endereco = filtro.aprova(cab.get("from", ""), cab.get("subject", ""))
        if not ok:
            stats["descartados"] += 1
            continue
        identificador = chave(cab.get("message-id") or mid)
        if ja_registrado(identificador):
            stats["repetidos"] += 1
            continue
        bruto = api.get(f"messages/{mid}", format="raw")["raw"]
        msg = email.message_from_bytes(base64.urlsafe_b64decode(bruto + "=" * (-len(bruto) % 4)))
        stats["novos"].append(registrar(msg, endereco, identificador))
    return stats


# ------------------------------------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    cfg = carregar_config()
    ap = argparse.ArgumentParser(description="Donna — intimações por e-mail (somente remetentes autorizados)")
    ap.add_argument("--metodo", choices=["imap", "api"], default=cfg["email"].get("metodo", "imap"))
    ap.add_argument("--dias", type=int, default=cfg["email"].get("dias", 3))
    ap.add_argument("--desde-dia-util-anterior", action="store_true")
    args = ap.parse_args(argv)

    desde = data_inicial(date.today(), args.dias, args.desde_dia_util_anterior)
    filtro = Filtro.da_config(cfg)
    try:
        stats = (buscar_api if args.metodo == "api" else buscar_imap)(cfg, filtro, desde)
    except Exception as erro:  # noqa: BLE001 — relatar de forma legível, sem expor credenciais
        print(f"E-MAIL: não foi possível consultar ({type(erro).__name__}: {erro})")
        return 1
    print(f"E-MAIL ({args.metodo}) desde {desde:%d/%m/%Y} — remetentes autorizados: "
          f"{', '.join(sorted(filtro.remetentes))}")
    print(f"  mensagens desses remetentes: {stats['verificados']} | descartadas pelo filtro de assunto: "
          f"{stats['descartados']} | já registradas: {stats['repetidos']} | novas: {len(stats['novos'])}")
    for nome in stats["novos"]:
        print(f"  + entrada/{nome}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
