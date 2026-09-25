import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GUARDIAO = RAIZ / "ferramentas" / "hooks" / "guardiao.py"
PROC = "9999999-99.2099.8.05.0001"


def rodar(ferramenta, entrada, modo="pre", env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "AUXILIAR_MANUTENCAO"}
    env.update({"CLAUDE_PROJECT_DIR": str(RAIZ), **(env_extra or {})})
    dados = {"tool_name": ferramenta, "tool_input": entrada, "cwd": str(RAIZ)}
    r = subprocess.run([sys.executable, str(GUARDIAO), modo], input=json.dumps(dados),
                       capture_output=True, text=True, env=env)
    decisao = json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "livre"
    return decisao, r.returncode, r.stderr


@pytest.fixture
def processo_teste():
    pasta = RAIZ / "processos" / PROC
    (pasta / "minutas").mkdir(parents=True, exist_ok=True)
    (pasta / "autos").mkdir(exist_ok=True)
    (pasta / "ficha.md").write_text("| Autor (cliente) | Maria das Dores Teste |\n", encoding="utf-8")
    yield pasta
    shutil.rmtree(pasta)


@pytest.mark.parametrize("caminho, esperado", [
    (f"processos/{PROC}/minutas/2026-09-25-impugnacao.md", "livre"),
    ("entrada/intimacao.txt", "livre"),
    ("jurisprudencia/a-conferir.md", "livre"),
    ("jurisprudencia/indice.md", "ask"),
    ("conhecimento/sumulas-e-temas.md", "ask"),
    (".claude/settings.json", "ask"),
    ("CLAUDE.md", "ask"),
    ("processos/_modelo/ficha.md", "ask"),
    ("/etc/passwd", "deny"),
    ("../fora-do-projeto.md", "deny"),
])
def test_gravacao_por_area(caminho, esperado):
    assert rodar("Write", {"file_path": caminho, "content": "x"})[0] == esperado


@pytest.mark.parametrize("comando, esperado", [
    ("python3 ferramentas/prazo.py ciencia 2026-09-25 10", "livre"),
    ("python3 ferramentas/prazo.py ciencia 2026-09-25 10 | grep '>>> VENC'", "livre"),
    (f"mkdir -p processos/{PROC}/autos && cp -r processos/_modelo/. processos/{PROC}/", "livre"),
    (f"mv entrada/intimacao.pdf processos/{PROC}/autos/", "livre"),
    ("ls conhecimento && cat conhecimento/sumulas-e-temas.md 2>&1", "livre"),
    ("git status && git push -u origin minha-branch", "livre"),
    ("curl https://exemplo.com", "deny"),
    ("wget http://x", "deny"),
    ("git push --force origin main", "deny"),
    ("git add -f processos/", "deny"),
    ("echo 'Súmula 999/STJ' >> conhecimento/sumulas-e-temas.md", "deny"),
    ("sed -i 's/a/b/' modelos/recurso-inominado.md", "deny"),
    (f"rm processos/{PROC}/autos/evento-10-sentenca.pdf", "deny"),
    (f"mv processos/{PROC}/autos/evento-10.pdf /tmp/", "deny"),
    ("python3 -c \"open('CLAUDE.md','w').write('')\"", "deny"),
    ("cp arquivo.txt ~/Documentos/", "deny"),
    ("git commit -F - <<'EOF'\nfluxo pesquisa -> a-conferir.md\nrm processos/x/autos/y.pdf\nEOF", "livre"),
    ("cat > conhecimento/nova.md <<'EOF'\nSúmula 999/STJ\nEOF", "deny"),
])
def test_bash(comando, esperado):
    assert rodar("Bash", {"command": comando})[0] == esperado


@pytest.mark.parametrize("url, esperado", [
    ("https://scon.stj.jus.br/SCON/pesquisar.jsp?b=SUMU", "livre"),
    ("https://www.tjba.jus.br/jurisprudencia/", "livre"),
    ("https://www.jusbrasil.com.br/jurisprudencia/busca?q=rmc", "livre"),
    ("https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm", "livre"),
    ("https://projudi.tjba.jus.br/projudi/", "deny"),
    ("https://pje.tjba.jus.br/pje/login.seam", "deny"),
    ("https://blog-qualquer.com/artigo", "deny"),
    ("https://jus.br.golpe.com/", "deny"),
])
def test_webfetch(url, esperado):
    assert rodar("WebFetch", {"url": url, "prompt": "x"})[0] == esperado


def test_websearch_sem_dados_pessoais(processo_teste):
    assert rodar("WebSearch", {"query": "cartão RMC dano moral turma recursal Bahia"})[0] == "livre"
    assert rodar("WebSearch", {"query": "processo 0001234-56.2026.8.05.0001"})[0] == "deny"
    assert rodar("WebSearch", {"query": "cpf 123.456.789-09 banco"})[0] == "deny"
    assert rodar("WebSearch", {"query": "maria das dores teste banco"})[0] == "deny"


def test_mcp_e_publicacao_bloqueados():
    assert rodar("mcp__github__create_issue", {})[0] == "deny"
    assert rodar("Artifact", {"file_path": "x.html"})[0] == "deny"


def test_modo_manutencao_libera():
    assert rodar("Write", {"file_path": "CLAUDE.md"}, env_extra={"AUXILIAR_MANUTENCAO": "1"})[0] == "livre"


def test_pos_bloqueia_minuta_com_citacao_inventada(processo_teste):
    minuta = processo_teste / "minutas" / "m.md"
    minuta.write_text("Nesse sentido, REsp 1.999.999/BA.\n", encoding="utf-8")
    _, codigo, erro = rodar("Write", {"file_path": str(minuta)}, modo="pos")
    assert codigo == 2 and "BLOQUEANTE" in erro
    minuta.write_text("Aplica-se a Súmula 479/STJ.\n", encoding="utf-8")
    assert rodar("Write", {"file_path": str(minuta)}, modo="pos")[1] == 0
