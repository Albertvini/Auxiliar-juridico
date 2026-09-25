from datetime import date

from painel_prazos import montar_painel

FICHA = """# Ficha

| Campo | Valor |
|---|---|
| Juízo | 3º Juizado Especial Cível — Comarca de {comarca} |
| Comarca (para prazos) | {comarca} |

## Prazos em aberto

| Providência | Ciência | Vencimento | Status |
|---|---|---|---|
| Recurso inominado | 01/10/2026 | 15/10/2026 | a fazer |
| Impugnação | 20/09/2026 | 28/09/2026 | protocolado |
| Embargos | 29/09/2026 | 02/10/2026 | a fazer |
| Manifestação | [CONFIRMAR] | [CONFIRMAR] | a fazer |

## Estratégia
"""


def criar(tmp_path, numero, comarca):
    pasta = tmp_path / "processos" / numero
    pasta.mkdir(parents=True)
    (pasta / "ficha.md").write_text(FICHA.format(comarca=comarca), encoding="utf-8")


def test_painel_ordena_filtra_e_alerta(tmp_path):
    criar(tmp_path, "0000001-00.2026.8.05.0001", "Salvador")
    criar(tmp_path, "0000002-00.2026.8.05.0080", "Feira de Santana")
    texto, prazos = montar_painel(date(2026, 10, 1), raiz=tmp_path)
    assert all(p.providencia != "Impugnação" for p in prazos)          # protocolado sai do painel
    assert [p.providencia for p in prazos[:2]] == ["Embargos", "Embargos"]
    assert prazos[0].dias_uteis_restantes == 1                          # quinta 01/10 -> sexta 02/10
    assert prazos[-1].vencimento is None
    assert "URGENTE" in texto and "SEM DATA" in texto
    assert {p.comarca for p in prazos} == {"salvador", "feira-de-santana"}


def test_prazo_vencido(tmp_path):
    criar(tmp_path, "0000003-00.2026.8.05.0001", "Salvador")
    texto, _ = montar_painel(date(2026, 10, 5), raiz=tmp_path)
    assert "VENCIDO" in texto
