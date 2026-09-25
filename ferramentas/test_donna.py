import base64
import io
import json
from datetime import date
from email.message import EmailMessage
from functools import partial

import pytest

import donna_comum
import donna_dje
import donna_email
from donna_email import Filtro

CFG = {
    "advogado": {"oab": "68210", "uf": "BA"},
    "dje": {"tribunais": ["TJBA"], "conferir_processos_cadastrados": False},
    "email": {
        "conta": "adv@gmail.com",
        "remetentes": ["projudi@tjba.jus.br", "pje@tjba.jus.br", "responda@jusbrasil.com.br"],
        "filtro_assunto": {"responda@jusbrasil.com.br": ["intima", "publica", "processo"]},
    },
}


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    for modulo in (donna_email, donna_dje):
        monkeypatch.setattr(modulo, "gravar_na_entrada", partial(donna_comum.gravar_na_entrada, raiz=tmp_path))
        monkeypatch.setattr(modulo, "ja_registrado", partial(donna_comum.ja_registrado, raiz=tmp_path))
    return tmp_path


def mensagem(remetente, assunto, corpo, mid):
    m = EmailMessage()
    m["From"], m["Subject"], m["Message-ID"], m["Date"] = remetente, assunto, mid, "Fri, 25 Sep 2026 10:00:00 -0300"
    m.set_content(corpo)
    return m


CAIXA = {
    b"1": mensagem("PROJUDI <projudi@tjba.jus.br>", "Intimação — processo 0001234-56.2026.8.05.0001",
                   "Fica V. Sa. intimado da sentença no processo 0001234-56.2026.8.05.0001.", "<a@tjba>"),
    b"2": mensagem("Jusbrasil <responda@jusbrasil.com.br>", "Oferta imperdível: assine já",
                   "PROPAGANDA SIGILOSA", "<b@jus>"),
    b"3": mensagem("Jusbrasil <responda@jusbrasil.com.br>", "Nova publicação no Diário",
                   "Publicação no processo 00012345620268050001.", "<c@jus>"),
    b"4": mensagem("Golpista <projudi@tjba.jus.br.golpe.com>", "Intimação urgente", "CONTEUDO PESSOAL", "<d@x>"),
}


class FakeIMAP:
    def __init__(self):
        self.corpos_baixados, self.somente_leitura = [], None

    def select(self, pasta, readonly=False):
        self.somente_leitura = readonly
        return "OK", [b"4"]

    def uid(self, comando, *args):
        if comando == "SEARCH":
            remetente = args[-1].strip('"')
            achados = [u for u, m in CAIXA.items() if remetente in m["From"]]  # servidor faz busca por substring
            return "OK", [b" ".join(achados)]
        uid, partes = args
        msg = CAIXA[uid]
        if "HEADER.FIELDS" in partes:
            cab = f"From: {msg['From']}\r\nSubject: {msg['Subject']}\r\nMessage-ID: {msg['Message-ID']}\r\n\r\n"
            return "OK", [(b"1 (BODY[HEADER]", cab.encode())]
        assert "PEEK" in partes, "nunca pode marcar como lido"
        self.corpos_baixados.append(uid)
        return "OK", [(b"1 (BODY[]", msg.as_bytes())]

    def logout(self):
        pass


def test_filtro_exige_remetente_exato_e_assunto():
    f = Filtro.da_config(CFG)
    assert f.aprova("PROJUDI <projudi@tjba.jus.br>", "qualquer")[0]
    assert not f.aprova("x <projudi@tjba.jus.br.golpe.com>", "Intimação")[0]
    assert not f.aprova("x <outro@gmail.com>", "Intimação")[0]
    assert not f.aprova("<responda@jusbrasil.com.br>", "Promoção de assinatura")[0]
    assert f.aprova("<responda@jusbrasil.com.br>", "Nova PUBLICAÇÃO no diário")[0]


def test_imap_so_baixa_emails_autorizados(raiz):
    conexao = FakeIMAP()
    stats = donna_email.buscar_imap(CFG, Filtro.da_config(CFG), date(2026, 9, 24), conexao=conexao)
    assert conexao.somente_leitura is True
    assert sorted(conexao.corpos_baixados) == [b"1", b"3"]          # propaganda e golpe nunca abertos
    assert stats["descartados"] == 2 and len(stats["novos"]) == 2
    conteudo = "".join(p.read_text() for p in (raiz / "entrada").glob("*.txt"))
    assert "PROPAGANDA SIGILOSA" not in conteudo and "CONTEUDO PESSOAL" not in conteudo
    assert "0001234-56.2026.8.05.0001" in conteudo


def test_imap_nao_duplica(raiz):
    donna_email.buscar_imap(CFG, Filtro.da_config(CFG), date(2026, 9, 24), conexao=FakeIMAP())
    stats = donna_email.buscar_imap(CFG, Filtro.da_config(CFG), date(2026, 9, 24), conexao=FakeIMAP())
    assert stats["novos"] == [] and stats["repetidos"] == 2


class FakeAPI:
    def __init__(self):
        self.brutos = []

    def get(self, caminho, **params):
        if caminho == "messages":
            assert params["q"].startswith("from:(") and "after:2026/09/24" in params["q"]
            return {"messages": [{"id": u.decode()} for u in CAIXA]}
        mid = caminho.split("/")[1].encode()
        msg = CAIXA[mid]
        if params["format"] == "metadata":
            return {"payload": {"headers": [{"name": k, "value": msg[k]} for k in ("From", "Subject", "Message-ID")]}}
        self.brutos.append(mid)
        return {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip("=")}


def test_api_so_baixa_emails_autorizados(raiz):
    api = FakeAPI()
    stats = donna_email.buscar_api(CFG, Filtro.da_config(CFG), date(2026, 9, 24), api=api)
    assert sorted(api.brutos) == [b"1", b"3"] and len(stats["novos"]) == 2


ITEM_DJEN = {
    "id": 555, "siglaTribunal": "TJBA", "nomeOrgao": "3ª Vara do Sistema dos Juizados — Salvador",
    "tipoComunicacao": "Intimação", "tipoDocumento": "Sentença", "nomeClasse": "Procedimento do Juizado",
    "numeroprocessocommascara": "0001234-56.2026.8.05.0001", "data_disponibilizacao": "2026-09-24",
    "texto": "<p>Julgo <b>procedente</b> o pedido.</p>", "link": "https://comunica.pje.jus.br/x",
    "destinatarioadvogados": [{"advogado": {"nome": "ADVOGADO", "numero_oab": "68210", "uf_oab": "BA"}}],
}


def abrir_falso(respostas, chamadas):
    def abrir(req, timeout=0):
        chamadas.append(req.full_url)
        return io.BytesIO(json.dumps({"items": respostas.pop(0) if respostas else []}).encode())
    return abrir


def test_djen_filtra_tribunal_e_grava(raiz):
    outro = {**ITEM_DJEN, "id": 556, "siglaTribunal": "TJSP"}
    chamadas = []
    stats = donna_dje.buscar(CFG, date(2026, 9, 24), date(2026, 9, 25), abrir_falso([[ITEM_DJEN, outro]], chamadas))
    assert "numeroOab=68210" in chamadas[0] and "ufOab=BA" in chamadas[0]
    assert stats["outros_tribunais"] == 1 and len(stats["novas"]) == 1
    texto = next((raiz / "entrada").glob("djen-*.txt")).read_text()
    assert "Julgo procedente o pedido." in texto and "prazo.py dje 2026-09-24" in texto
    stats2 = donna_dje.buscar(CFG, date(2026, 9, 24), date(2026, 9, 25), abrir_falso([[ITEM_DJEN]], []))
    assert stats2["repetidas"] == 1 and stats2["novas"] == []


def test_numeros_cnj_com_e_sem_mascara():
    assert donna_comum.numeros_cnj("proc 00012345620268050001 e 0001234-56.2026.8.05.0001") == \
        ["0001234-56.2026.8.05.0001"]


def test_dia_util_anterior_pula_fim_de_semana():
    assert donna_comum.dia_util_anterior(date(2026, 9, 28)) == date(2026, 9, 25)  # segunda -> sexta
