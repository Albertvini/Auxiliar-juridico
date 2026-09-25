#!/usr/bin/env python3
"""Autoriza a Donna a LER o Gmail (somente leitura) — rode UMA VEZ, no seu computador.

Gera o "refresh token" usado pela rotina na nuvem (método "api"). Escopo solicitado: gmail.readonly
(ler apenas; o Google impede enviar, apagar, mover ou marcar mensagens com esse escopo).

Pré-requisitos (uma vez, no Google Cloud Console, com a sua conta Google):
  1. Crie um projeto e ative a "Gmail API".
  2. Tela de consentimento OAuth: tipo "Externo", adicione seu e-mail como usuário de teste e depois
     publique o app ("Em produção") — em modo "Teste", o token expira em 7 dias.
  3. Credenciais → Criar ID do cliente OAuth → tipo "App para computador". Anote o ID e a chave secreta.

Uso:
  python3 ferramentas/donna_gmail_autorizar.py <CLIENT_ID> <CLIENT_SECRET>

O navegador abre, você autoriza, e o script mostra os três valores para cadastrar como SEGREDOS do ambiente
na nuvem (DONNA_GMAIL_CLIENT_ID, DONNA_GMAIL_CLIENT_SECRET, DONNA_GMAIL_REFRESH_TOKEN). Não cole esses
valores em conversas nem em arquivos do repositório.
"""

from __future__ import annotations

import http.server
import json
import secrets
import sys
import urllib.parse
import urllib.request
import webbrowser

ESCOPO = "https://www.googleapis.com/auth/gmail.readonly"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    client_id, client_secret = argv
    estado = secrets.token_urlsafe(16)
    recebido: dict = {}

    class Receptor(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            recebido.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Autorização recebida. Pode fechar esta janela.".encode())

        def log_message(self, *args):
            pass

    servidor = http.server.HTTPServer(("127.0.0.1", 0), Receptor)
    redirect = f"http://127.0.0.1:{servidor.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code", "scope": ESCOPO,
        "access_type": "offline", "prompt": "consent", "state": estado,
    })
    print("Abrindo o navegador para autorizar (somente leitura). Se não abrir, acesse:\n" + url)
    webbrowser.open(url)
    servidor.handle_request()

    if recebido.get("state", [""])[0] != estado or "code" not in recebido:
        print("Autorização não concluída:", recebido.get("error", ["resposta inválida"])[0])
        return 1
    dados = urllib.parse.urlencode({
        "code": recebido["code"][0], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen("https://oauth2.googleapis.com/token", data=dados, timeout=30) as r:
        token = json.load(r)
    if token.get("scope", "").strip() != ESCOPO:
        print(f"Escopo inesperado ({token.get('scope')}). Por segurança, nada foi gerado.")
        return 1
    print("\nCadastre estes três valores como SEGREDOS do ambiente na nuvem:\n")
    print(f"DONNA_GMAIL_CLIENT_ID={client_id}")
    print(f"DONNA_GMAIL_CLIENT_SECRET={client_secret}")
    print(f"DONNA_GMAIL_REFRESH_TOKEN={token['refresh_token']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
