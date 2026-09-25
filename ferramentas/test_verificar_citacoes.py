from pathlib import Path

from verificar_citacoes import RAIZ, carregar_base, extrair_citacoes, fontes_da_base, verificar_arquivo, verificar_texto

BASE = carregar_base(fontes_da_base(RAIZ / "qualquer.md"))


def niveis(texto):
    return [a.nivel for a in verificar_texto(texto, BASE)]


def test_extrai_lista_de_sumulas():
    nums = [(c.tipo, c.numero, c.tribunal) for c in extrair_citacoes("Súmulas 539 e 541/STJ")]
    assert nums == [("sumula", "539", "STJ"), ("sumula", "541", "STJ")]


def test_extrai_precedente_com_pontos():
    c = extrair_citacoes("EAREsp 676.608/RS")[0]
    assert (c.tipo, c.numero, c.tribunal) == ("precedente", "676608", "EARESP")


def test_citacoes_da_base_passam():
    assert niveis("Aplica-se a Súmula 479/STJ e o Tema 1061/STJ (REsp 1.846.649/MA).") == []


def test_sumula_inexistente_bloqueia():
    assert niveis("Conforme a Súmula 999/STJ, o banco responde.") == ["BLOQUEANTE"]


def test_tribunal_errado_bloqueia():
    assert niveis("Súmula 479/STF.") == ["BLOQUEANTE"]


def test_precedente_inventado_bloqueia():
    assert niveis("Nesse sentido: REsp 1.999.999/BA, Rel. Min. Fulano.") == ["BLOQUEANTE"]


def test_numero_cnj_de_outro_processo_bloqueia():
    assert niveis("Veja-se o Recurso Inominado 8000123-45.2025.8.05.0001.") == ["BLOQUEANTE"]


def test_sumula_cancelada_bloqueia():
    assert niveis("A Súmula 603/STJ veda a retenção.") == ["BLOQUEANTE"]


def test_entendimento_sem_fonte_bloqueia():
    assert niveis("A jurisprudência pacífica reconhece o dano moral.") == ["BLOQUEANTE"]
    assert niveis("A Turma Recursal tem entendido que o dano é presumido.") == ["BLOQUEANTE"]
    assert niveis("O TJBA entende que o valor deve ser majorado.") == ["BLOQUEANTE"]


def test_entendimento_com_fonte_verificada_passa():
    assert niveis("O STJ firmou, no Tema 1061/STJ, que o ônus é do banco.") == []


def test_pendencia_marcada_vira_aviso():
    texto = "A Turma tem entendido pela majoração [INSERIR PRECEDENTE DA TURMA RECURSAL SOBRE valor]."
    assert niveis(texto) == ["AVISO"]
    assert niveis("REsp 1.999.999/BA [A CONFERIR: link do STJ]") == ["AVISO"]


def test_sumula_sem_tribunal_gera_aviso():
    assert niveis("Súmula 479.") == ["AVISO"]


def test_processo_aceita_numeros_dos_proprios_autos(tmp_path: Path):
    n = "0001234-56.2026.8.05.0001"
    pasta = tmp_path / "processos" / n
    (pasta / "autos").mkdir(parents=True)
    (pasta / "autos" / "evento-10-sentenca.txt").write_text("Acórdão no processo 8000999-11.2024.8.05.0001")
    (tmp_path / "conhecimento").mkdir()
    minuta = pasta / "minutas" / "m.md"
    minuta.parent.mkdir()
    minuta.write_text(f"Processo {n}. Citado na sentença: 8000999-11.2024.8.05.0001.")
    assert verificar_arquivo(minuta, raiz=tmp_path) == []
