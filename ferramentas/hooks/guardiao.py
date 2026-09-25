#!/usr/bin/env python3
"""Guardião de escopo do agente — hook do Claude Code (PreToolUse e PostToolUse).

PreToolUse
- Write/Edit: livre em processos/<n>/, entrada/ e jurisprudencia/a-conferir.md. Na base do agente (conhecimento/,
  modelos/, .claude/, ferramentas/, CLAUDE.md, jurisprudencia/indice.md...) o Claude Code PEDE CONFIRMAÇÃO ao
  advogado. Fora do projeto: bloqueado.
- Bash: bloqueia rede fora das ferramentas de pesquisa (curl, wget, ssh...), envio de e-mail, git push forçado,
  git add -f (versionar dados de clientes), apagar documentos dos autos e gravar na base do agente pelo shell.
- Bash: só executa python dos scripts de ferramentas/ (e pytest); bloqueia código avulso (python -c, node,
  perl...), e exibir variáveis de ambiente ou credenciais.
- Read/Grep/Glob: bloqueia a leitura de credenciais (~/.donna/, *.env).
- WebFetch: só domínios jurídicos/oficiais da lista abaixo; nunca PROJUDI/PJe (exceto o diário público DJEN)
  nem URL com CPF.
- WebSearch: bloqueia consultas com CPF, número de processo CNJ ou nome de cliente cadastrado nas fichas.
- Ferramentas MCP e publicação de artefatos: bloqueadas (fora do escopo); exceções: leitura da documentação do
  ambiente (livre) e rotinas agendadas (exigem confirmação do advogado).

PostToolUse
- Após gravar análise ou minuta em processos/<n>/(analises|minutas)/, roda o verificador de citações; havendo
  citação sem fonte, devolve o relatório ao agente para correção imediata.

Modo manutenção: com a variável de ambiente AUXILIAR_MANUTENCAO=1 (definida por você ao abrir o Claude Code),
o guardião não interfere.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2]).resolve()

DOMINIOS_PERMITIDOS = (
    "jus.br",            # STF, STJ, TST, TJBA e todos os tribunais, CNJ, CJF
    "gov.br",            # Planalto, BACEN, INSS, Consumidor.gov, Senacon
    "leg.br",            # Câmara, Senado
    "jusbrasil.com.br",
    "conjur.com.br",
    "migalhas.com.br",
    "oab.org.br",
    "fonaje.org.br",
    "lexml.gov.br",
)
BLOQUEIO_URL = re.compile(r"projudi|pje\d?[a-z]*\.|esaj|eproc|\d{3}\.?\d{3}\.?\d{3}-?\d{2}", re.I)
CPF = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
CNJ = re.compile(r"\b\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}\b")

COMANDOS_DE_REDE = {"curl", "wget", "ssh", "scp", "sftp", "rsync", "nc", "ncat", "netcat", "telnet", "ftp",
                    "mail", "mailx", "sendmail", "mutt", "aws", "gsutil", "rclone"}
INTERPRETADORES = {"node", "nodejs", "deno", "bun", "perl", "ruby", "php", "lua", "osascript", "powershell", "pwsh"}
MODULOS_PYTHON_PERMITIDOS = {"pytest", "json.tool", "py_compile"}
# Diários públicos que o agente pode consultar mesmo estando em domínio do PJe.
DIARIOS_PUBLICOS = {"comunicaapi.pje.jus.br", "comunica.pje.jus.br"}
SEGREDOS = re.compile(r"DONNA_GMAIL_(?:SENHA|CLIENT_SECRET|REFRESH)|\.donna(?:/|\b|$)|credenciais\.env", re.I)
# Ferramentas MCP de leitura inofensiva / que exigem a confirmação do advogado.
MCP_LIVRES = {"mcp__Claude_Code_Remote__read_documentation"}
MCP_COM_CONFIRMACAO = {f"mcp__Claude_Code_Remote__{n}" for n in
                       ("create_trigger", "update_trigger", "delete_trigger", "get_trigger", "list_triggers",
                        "fire_trigger", "send_later")}
COMANDOS_QUE_GRAVAM = {"rm", "rmdir", "touch", "truncate", "chmod", "chown", "ln", "unlink", "shred"}


# ---------------------------------------------------------------------------------------------- respostas
def decidir(decisao: str, motivo: str) -> int:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decisao,
                                             "permissionDecisionReason": motivo}}, ensure_ascii=False))
    return 0


def negar(motivo: str) -> int:
    return decidir("deny", f"[Guardião de escopo] {motivo}")


def perguntar(motivo: str) -> int:
    return decidir("ask", f"[Guardião de escopo] {motivo}")


# ---------------------------------------------------------------------------------------------- caminhos
def resolver(caminho: str, cwd: str) -> Path:
    p = Path(os.path.expanduser(caminho))
    return (p if p.is_absolute() else Path(cwd) / p).resolve()


def relativo(p: Path) -> tuple[str, ...] | None:
    try:
        return p.relative_to(RAIZ).parts
    except ValueError:
        return None


def area_livre(p: Path) -> bool:
    partes = relativo(p)
    if not partes:
        return False
    if partes[0] == "processos":
        return len(partes) >= 2 and not partes[1].startswith("_")
    if partes[0] == "entrada":
        return True
    return partes == ("jurisprudencia", "a-conferir.md") or partes[:2] == ("jurisprudencia", "decisoes")


def eh_autos(p: Path) -> bool:
    partes = relativo(p) or ()
    return len(partes) >= 4 and partes[0] == "processos" and partes[2] == "autos"


def classificar_gravacao(p: Path) -> str:
    """livre | base | fora"""
    if relativo(p) is None:
        return "fora"
    return "livre" if area_livre(p) else "base"


# ---------------------------------------------------------------------------------------------- ferramentas
def checar_escrita(caminho: str, cwd: str) -> int:
    p = resolver(caminho, cwd)
    tipo = classificar_gravacao(p)
    if tipo == "livre":
        return 0
    if tipo == "fora":
        return negar(f"gravação fora do projeto ({p}) não faz parte do escopo do agente.")
    return perguntar(f"alteração na BASE do agente ({p.relative_to(RAIZ)}). Só aprove se você pediu esta "
                     "mudança e conferiu o conteúdo (súmulas, teses, jurisprudência verificada, modelos, regras).")


def segmentos(comando: str) -> list[list[str]]:
    partes = re.split(r"\|\||&&|;|\||\n", comando)
    tokens = []
    for parte in partes:
        try:
            tokens.append(shlex.split(parte, posix=True))
        except ValueError:
            tokens.append(parte.split())
    return [t for t in tokens if t]


def alvos_de_redirecionamento(comando: str) -> list[str]:
    sem_aspas = re.sub(r"'[^']*'|\"(?:\\.|[^\"\\])*\"", "''", comando)
    return re.findall(r"(?<![<\d&>=-])>{1,2}\s*([^\s;&|<>]+)", sem_aspas)


def sem_heredocs(comando: str) -> str:
    """Remove o corpo de heredocs (texto de mensagens/arquivos), mantendo a linha do comando."""
    return re.sub(r"(<<-?\s*['\"]?(\w+)['\"]?[^\n]*)\n.*?\n\s*\2[ \t]*(?=\n|$)", r"\1", comando, flags=re.S)


def checar_bash(comando: str, cwd: str) -> int:
    comando = sem_heredocs(comando)
    for alvo in alvos_de_redirecionamento(comando):
        if alvo.startswith("&") or alvo == "/dev/null":
            continue
        motivo = checar_destino_shell(alvo, cwd)
        if motivo:
            return negar(motivo)
    for tokens in segmentos(comando):
        if tokens[0] == "printenv" or (tokens[0] == "env" and all("=" in t or t.startswith("-")
                                                                   for t in tokens[1:])):
            return negar("exibir variáveis de ambiente ou credenciais não é permitido.")
        while tokens and ("=" in tokens[0] and not tokens[0].startswith("-") or tokens[0] in {"sudo", "env",
                                                                                               "nohup", "time"}):
            tokens = tokens[1:]
        if not tokens:
            continue
        prog = os.path.basename(tokens[0])
        args = [a for a in tokens[1:] if not a.startswith("-")]
        if prog in COMANDOS_DE_REDE:
            return negar(f"'{prog}' faz acesso externo fora das ferramentas de pesquisa jurídica. Para pesquisar "
                         "jurisprudência, use WebSearch/WebFetch nos sites permitidos.")
        if prog == "git":
            sub = tokens[1] if len(tokens) > 1 else ""
            if sub == "add" and any(t in {"-f", "--force"} for t in tokens):
                return negar("'git add -f' poderia versionar documentos de clientes (sigilo/LGPD).")
            if sub == "push" and any(t in {"-f", "--force", "--force-with-lease"} or t.startswith("+")
                                     for t in tokens):
                return negar("push forçado reescreve o histórico do repositório; fora do escopo.")
            continue
        if prog in {"sh", "bash", "zsh"} and "-c" in tokens:
            interno = tokens[tokens.index("-c") + 1] if tokens.index("-c") + 1 < len(tokens) else ""
            resultado = checar_bash(interno, cwd)
            if resultado or interno == "":
                return resultado
            continue
        if prog in INTERPRETADORES:
            return negar(f"execução de código avulso ('{prog}') não é permitida; o agente só roda as ferramentas "
                         "de ferramentas/.")
        if prog in {"python", "python3"} or re.fullmatch(r"python3\.\d+", prog):
            motivo = checar_python(tokens[1:], cwd)
            if motivo:
                return negar(motivo)
        if (prog in {"env", "printenv"} and len(tokens) <= 2) or (prog in {"set", "export", "declare"}
                                                                   and len(tokens) == 1) or \
                SEGREDOS.search(" ".join(tokens)):
            return negar("exibir variáveis de ambiente ou credenciais não é permitido.")
        destinos: list[str] = []
        if prog in COMANDOS_QUE_GRAVAM:
            destinos = args
        elif prog in {"mv", "cp", "install"} and args:
            destinos = [args[-1]] + (args[:-1] if prog == "mv" else [])
        elif prog == "tee":
            destinos = args
        elif prog in {"sed", "perl"} and any(t == "-i" or t.startswith("-i") or t == "--in-place" for t in tokens):
            destinos = args[1:] if args else []
        removidos = args if prog in {"rm", "rmdir", "unlink", "shred", "truncate"} else \
            args[:-1] if prog == "mv" else []
        if any(eh_autos(resolver(a, cwd)) for a in removidos):
            return negar("os documentos em autos/ são cópias dos autos e não podem ser apagados, movidos ou "
                         "alterados pelo agente. Peça ao advogado.")
        for destino in destinos:
            motivo = checar_destino_shell(destino, cwd)
            if motivo:
                return negar(motivo)
    return 0


def checar_python(args: list[str], cwd: str) -> str | None:
    """Permite só os scripts de ferramentas/ e alguns módulos (pytest). Código avulso é bloqueado."""
    i = 0
    while i < len(args) and args[i].startswith("-") and args[i] not in {"-c", "-m", "-"}:
        i += 1
    if i >= len(args):
        return "python interativo não é permitido."
    if args[i] == "-m":
        modulo = args[i + 1] if i + 1 < len(args) else ""
        return None if modulo in MODULOS_PYTHON_PERMITIDOS else f"módulo python '{modulo}' não permitido."
    if args[i] in {"-c", "-"}:
        return ("execução de código python avulso não é permitida; o agente só roda os scripts de ferramentas/ "
                "(para manutenção, use AUXILIAR_MANUTENCAO=1).")
    script = resolver(args[i], cwd)
    if relativo(script) is None or relativo(script)[0] != "ferramentas":
        return f"só os scripts de ferramentas/ podem ser executados (pedido: {args[i]})."
    return None


def checar_destino_shell(destino: str, cwd: str) -> str | None:
    if any(c in destino for c in "*?$`"):
        destino_base = re.split(r"[*?$`]", destino)[0] or "."
    else:
        destino_base = destino
    tipo = classificar_gravacao(resolver(destino_base, cwd))
    if tipo == "livre":
        return None
    if tipo == "fora" and resolver(destino_base, cwd).is_relative_to(Path("/tmp")):
        return None
    if tipo == "fora":
        return f"o comando grava fora do projeto ({destino}); fora do escopo do agente."
    return (f"o comando altera a base do agente ({destino}) pelo shell. Use Write/Edit, para que o advogado "
            "aprove a alteração.")


def checar_webfetch(url: str) -> int:
    host = (urlparse(url).hostname or "").lower()
    if not any(host == d or host.endswith("." + d) for d in DOMINIOS_PERMITIDOS):
        return negar(f"domínio '{host}' fora da lista de fontes jurídicas permitidas "
                     f"({', '.join(DOMINIOS_PERMITIDOS)}).")
    alvo = url.replace(host, "") if host in DIARIOS_PUBLICOS else url
    if BLOQUEIO_URL.search(alvo):
        return negar("acesso a sistemas processuais (PROJUDI/PJe/e-SAJ) ou URL com dados pessoais está fora do "
                     "escopo. O advogado baixa os documentos.")
    return 0


def nomes_de_clientes() -> list[str]:
    nomes = []
    for ficha in (RAIZ / "processos").glob("*/ficha.md"):
        if ficha.parent.name.startswith("_"):
            continue
        m = re.search(r"\|\s*Autor \(cliente\)\s*\|\s*([^|\[—-]+)", ficha.read_text(encoding="utf-8", errors="ignore"))
        if m and len(m.group(1).split()) >= 2:
            nomes.append(m.group(1).strip().lower())
    return nomes


def checar_websearch(consulta: str) -> int:
    if CPF.search(consulta) or CNJ.search(consulta):
        return negar("a pesquisa contém CPF ou número de processo. Pesquise pela TESE (ex.: 'consignado não "
                     "contratado dano moral turma recursal bahia'), nunca por dados do cliente.")
    baixa = consulta.lower()
    for nome in nomes_de_clientes():
        if nome in baixa:
            return negar("a pesquisa contém o nome de um cliente. Pesquise pela tese, sem dados pessoais.")
    return 0


def pre(dados: dict) -> int:
    ferramenta = dados.get("tool_name", "")
    entrada = dados.get("tool_input", {}) or {}
    cwd = dados.get("cwd") or str(RAIZ)
    if ferramenta in {"Write", "Edit", "MultiEdit"}:
        return checar_escrita(entrada.get("file_path", ""), cwd)
    if ferramenta == "NotebookEdit":
        return checar_escrita(entrada.get("notebook_path", ""), cwd)
    if ferramenta == "Bash":
        return checar_bash(entrada.get("command", ""), cwd)
    if ferramenta == "WebFetch":
        return checar_webfetch(entrada.get("url", ""))
    if ferramenta == "WebSearch":
        return checar_websearch(entrada.get("query", ""))
    if ferramenta in {"Read", "Grep", "Glob"}:
        alvo = entrada.get("file_path") or entrada.get("path") or ""
        if SEGREDOS.search(alvo) or alvo.endswith(".env"):
            return negar("leitura de credenciais não é permitida; elas são usadas só pelos scripts.")
        return 0
    if ferramenta in MCP_LIVRES:
        return 0
    if ferramenta in MCP_COM_CONFIRMACAO:
        return perguntar(f"'{ferramenta}' cria ou altera uma rotina agendada. Aprove só se você pediu.")
    if ferramenta.startswith("mcp__") or ferramenta in {"Artifact", "ArtifactData", "ArtifactComments"}:
        return negar(f"'{ferramenta}' envia ou publica conteúdo em serviço externo; fora do escopo do agente.")
    return 0


def pos(dados: dict) -> int:
    if dados.get("tool_name") not in {"Write", "Edit", "MultiEdit"}:
        return 0
    caminho = resolver((dados.get("tool_input") or {}).get("file_path", ""), dados.get("cwd") or str(RAIZ))
    partes = relativo(caminho) or ()
    if not (len(partes) == 4 and partes[0] == "processos" and partes[2] in {"analises", "minutas"}
            and caminho.suffix == ".md"):
        return 0
    verificador = RAIZ / "ferramentas" / "verificar_citacoes.py"
    r = subprocess.run([sys.executable, str(verificador), str(caminho)], capture_output=True, text=True)
    if r.returncode == 1:
        print(r.stdout + "\nCORRIJA AGORA: remova cada citação/afirmação BLOQUEANTE ou transforme-a em pendência "
              "([INSERIR PRECEDENTE ...] / [A CONFERIR: link]). Não crie nem 'ajuste' citações para passar no "
              "verificador, e não altere a base para incluí-las.", file=sys.stderr)
        return 2
    return 0


def main() -> int:
    if os.environ.get("AUXILIAR_MANUTENCAO") == "1":
        return 0
    modo = sys.argv[1] if len(sys.argv) > 1 else "pre"
    try:
        dados = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    return pos(dados) if modo == "pos" else pre(dados)


if __name__ == "__main__":
    sys.exit(main())
