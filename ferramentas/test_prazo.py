from datetime import date

import pytest

from prazo import Calendario, calcular, carregar_extras, pascoa


@pytest.fixture
def cal():
    return Calendario(extras={})


@pytest.mark.parametrize("ano, esperado", [
    (2024, date(2024, 3, 31)),
    (2025, date(2025, 4, 20)),
    (2026, date(2026, 4, 5)),
    (2027, date(2027, 3, 28)),
])
def test_pascoa(ano, esperado):
    assert pascoa(ano) == esperado


def test_ciencia_em_dia_util(cal):
    r = calcular("ciencia", date(2026, 3, 2), 10, cal)
    assert r.inicio == date(2026, 3, 3)
    assert r.vencimento == date(2026, 3, 16)


def test_ciencia_no_sabado_vale_para_segunda(cal):
    r = calcular("ciencia", date(2026, 3, 7), 5, cal)
    assert r.intimacao == date(2026, 3, 9)
    assert r.vencimento == date(2026, 3, 16)


def test_intimacao_tacita_dez_dias_corridos(cal):
    r = calcular("envio", date(2026, 3, 2), 5, cal)
    assert r.intimacao == date(2026, 3, 12)
    assert r.vencimento == date(2026, 3, 19)


def test_intimacao_tacita_em_fim_de_semana_prorroga(cal):
    r = calcular("envio", date(2026, 3, 4), 1, cal)  # 10º dia = sábado 14/03
    assert r.intimacao == date(2026, 3, 16)
    assert r.vencimento == date(2026, 3, 17)


def test_dje_publicacao_no_dia_util_seguinte(cal):
    r = calcular("dje", date(2026, 3, 2), 5, cal)
    assert r.intimacao == date(2026, 3, 3)
    assert r.vencimento == date(2026, 3, 10)


def test_pula_sexta_feira_santa(cal):
    r = calcular("ciencia", date(2026, 4, 1), 5, cal)
    assert r.vencimento == date(2026, 4, 9)
    assert (date(2026, 4, 3), "Sexta-feira Santa") in r.dias_pulados


def test_pula_dois_de_julho(cal):
    r = calcular("ciencia", date(2026, 6, 30), 3, cal)
    assert r.vencimento == date(2026, 7, 6)


def test_feriado_de_salvador_so_na_comarca_de_salvador():
    salvador = calcular("ciencia", date(2026, 6, 22), 2, Calendario(extras={}))
    outro = calcular("ciencia", date(2026, 6, 22), 2, Calendario(comarca="feira-de-santana", extras={}))
    assert salvador.vencimento == date(2026, 6, 25)
    assert outro.vencimento == date(2026, 6, 24)


def test_suspensao_de_fim_de_ano(cal):
    r = calcular("ciencia", date(2025, 12, 18), 5, cal)
    assert r.vencimento == date(2026, 1, 26)


def test_sem_recesso_pula_apenas_natal():
    r = calcular("ciencia", date(2025, 12, 18), 5, Calendario(recesso=False, extras={}))
    assert r.vencimento == date(2025, 12, 26)


def test_datas_extras_sao_respeitadas():
    cal = Calendario(extras={date(2026, 3, 4): "portaria"})
    r = calcular("ciencia", date(2026, 3, 2), 2, cal)
    assert r.vencimento == date(2026, 3, 5)


def test_prazo_invalido(cal):
    with pytest.raises(ValueError):
        calcular("ciencia", date(2026, 3, 2), 0, cal)


def test_feriados_extras_por_comarca_e_anuais(tmp_path):
    arquivo = tmp_path / "extras.txt"
    arquivo.write_text(
        "2026-03-04  # portaria geral\n"
        "08-15 @Feira-de-Santana  # feriado municipal anual\n"
        "08-16 @ilheus  # outra comarca\n"
        "data-ruim\n",
        encoding="utf-8",
    )
    pontuais, anuais = carregar_extras("feira-de-santana", arquivo)
    assert pontuais == {date(2026, 3, 4): "portaria geral"}
    assert anuais == {(8, 15): "feriado municipal anual"}
    cal = Calendario(comarca="feira-de-santana", extras=pontuais, anuais=anuais)
    assert not cal.eh_util(date(2028, 8, 15))  # terça-feira, feriado anual da comarca
    assert cal.eh_util(date(2026, 6, 24))  # São João de Salvador não se aplica
