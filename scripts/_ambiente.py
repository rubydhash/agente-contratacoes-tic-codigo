#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ambiente comum dos scripts Python: o .venv do repositório e a fonte dos PDFs.

As dependências Python ficam no .venv/ (requirements.txt), e não no Python do sistema. Para que
os comandos documentados (`python3 scripts/<script>.py`) continuem valendo, o script que precisa
de biblioteca chama, antes de importá-la:

    import _ambiente; _ambiente.usar_venv(__file__)

Se existir .venv/bin/python e o script não estiver rodando nele, o processo é reexecutado com o
Python do .venv, com os mesmos argumentos. Sem .venv, segue com o Python atual. Se faltar alguma
biblioteca, o erro de importação aparece normalmente.

Ver decisoes/2026-11-19-dependencias-no-venv.md.
"""
import glob, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PY = os.path.join(RAIZ, ".venv", "bin", "python")


def no_venv():
    return os.path.realpath(sys.prefix) == os.path.realpath(os.path.join(RAIZ, ".venv"))


def usar_venv(arquivo):
    """Reexecuta o script chamado diretamente com o Python do .venv, se houver."""
    if os.path.abspath(sys.argv[0]) != os.path.abspath(arquivo):
        return                      # importado por outro script: quem manda é o chamador
    if no_venv() or not os.path.exists(VENV_PY) or os.environ.get("AGENTE_SEM_VENV"):
        return
    os.environ["AGENTE_SEM_VENV"] = "1"   # evita laço, se o .venv apontar para outro lugar
    os.execv(VENV_PY, [VENV_PY, os.path.abspath(arquivo)] + sys.argv[1:])


# Fonte DejaVu dos PDFs (fpdf2 precisa de TTF com acentuação). Não há pacote pip com ela: vem do
# sistema (fonts-dejavu-core no Debian/Ubuntu; dejavu-sans-fonts no Fedora; brew no macOS) ou de
# uma pasta indicada em FONTES_TTF.
PASTAS_FONTE = [
    os.environ.get("FONTES_TTF", ""),
    os.path.join(RAIZ, "templates", "fontes"),
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/dejavu-sans-fonts",
    "/usr/share/fonts/dejavu",
    "/usr/share/fonts/TTF",
    "/opt/homebrew/share/fonts",
    "/usr/local/share/fonts",
    os.path.expanduser("~/Library/Fonts"),
    os.path.expanduser("~/.local/share/fonts"),
]


def fonte_ttf(nome):
    """Caminho de um TTF (ex.: 'DejaVuSans.ttf'), procurado nas pastas conhecidas."""
    for pasta in PASTAS_FONTE:
        if not pasta:
            continue
        achados = glob.glob(os.path.join(pasta, "**", nome), recursive=True)
        if achados:
            return achados[0]
    sys.exit(f"ERRO: fonte {nome} não encontrada. Instale a DejaVu (Debian/Ubuntu: "
             "apt-get install fonts-dejavu-core) ou aponte a pasta em FONTES_TTF.")


# (módulo, pacote pip, o que deixa de funcionar sem ele)
DEPENDENCIAS = [
    ("yaml", "PyYAML", "validação de YAML, metadados, listas de verificação, PNCP"),
    ("lxml", "lxml", "conferência do TR contra o docx da AGU"),
    ("fpdf", "fpdf2", "Anexo I do ETP e anexos do TR em PDF"),
    ("pypandoc", "pypandoc_binary", "pandoc embutido (sem ele, o build usa o pandoc do sistema)"),
    ("pypdfium2", "pypdfium2", "leitura de PDFs (scripts/ler-pdf.py)"),
]


def diagnostico():
    """Imprime o estado do ambiente; devolve 1 se faltar algo."""
    import importlib, shutil, subprocess
    falta = 0
    print(f"{'ok   ' if no_venv() else 'FALTA'} .venv ({VENV_PY if os.path.exists(VENV_PY) else 'crie: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'})")
    for mod, pip, uso in DEPENDENCIAS:
        try:
            importlib.import_module(mod)
            print(f"ok    {pip}")
        except ImportError:
            falta = 1
            print(f"FALTA {pip}: {uso}")
    pandoc = None
    try:
        import pypandoc
        pandoc = pypandoc.get_pandoc_path()
    except Exception:
        pandoc = shutil.which("pandoc")
    if pandoc:
        versao = subprocess.run([pandoc, "--version"], capture_output=True, text=True).stdout.split("\n")[0]
        print(f"ok    {versao} ({pandoc})")
    else:
        falta = 1
        print("FALTA pandoc: build do DFD, do ETP e do TR")
    for n in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        achado = next((g for p in PASTAS_FONTE if p
                       for g in glob.glob(os.path.join(p, "**", n), recursive=True)), None)
        if achado:
            print(f"ok    {n} ({achado})")
        else:
            falta = 1
            print(f"FALTA {n}: PDFs (apt-get install fonts-dejavu-core, ou FONTES_TTF=<pasta>)")
    return falta


if __name__ == "__main__":
    # Diagnóstico do ambiente: python3 scripts/_ambiente.py
    usar_venv(__file__)
    sys.exit(diagnostico())
