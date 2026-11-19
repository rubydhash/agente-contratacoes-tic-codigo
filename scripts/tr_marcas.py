#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Marcas de afastamento do modelo AGU no TR: leitura do markdown e código de cores.

Adota o "Código de formatação visual sugerida" do Instrumento de Padronização dos
Procedimentos de Contratação de Soluções de TIC (AGU/MGI), seção "Como elaborar o Termo de
Referência?", p. 88 do PDF, e a "Declaração de utilização de modelos AGU/MGI", p. 136:

  Inclusão        fonte vermelha       [texto novo]{.inclusao}   ou  ::: inclusao … :::
  Ajustes         fonte verde          ~~texto do modelo~~ [texto novo]{.ajuste}
  Preenchimento   fonte azul           [15 (quinze) dias]{.preenchimento}  ou  ::: preenchimento
  Supressão       trecho tachado       ~~texto do modelo~~  (inclusive a alternativa "OU" não adotada)
  Justificativas  fonte cinza          ::: justificativa … :::  logo abaixo do item modificado

Legado: [trecho]{.azul} e ::: azul (convenção anterior, uma cor só para todo afastamento).

Este módulo é a fonte única de:
  - CORES      usadas também, por cópia comentada, em scripts/marcas.lua e scripts/estilos-docx.py;
  - LEGENDA    frase que descreve o código, usada no despacho e na legenda do TR montado;
  - le_tr()    leitura de tr/*.md, usada por scripts/conferir-modelo-agu.py e
               scripts/gerar-despacho.py.

Uso direto:
  scripts/tr_marcas.py legenda-md     # imprime a legenda em markdown (usada por scripts/build.sh)
"""
import glob, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cores padrão do Word. Se mudar aqui, mude também em scripts/marcas.lua e scripts/estilos-docx.py.
CORES = {
    "inclusao": "#FF0000",       # vermelho
    "ajuste": "#00B050",         # verde
    "preenchimento": "#0000FF",  # azul
    "justificativa": "#808080",  # cinza
    "azul": "#0000CC",           # legado
}
MARCAS_COR = ("inclusao", "ajuste", "preenchimento", "azul")
CLASSES_DIV = ("inclusao", "preenchimento", "azul", "justificativa")

# Legenda: (marca, trecho destacado, complemento). Fonte única do texto que descreve o código.
LEGENDA = [
    (None, "", "Código de formatação visual adotado, conforme o Instrumento de Padronização dos "
               "Procedimentos de Contratação de Soluções de TIC da AGU/MGI: "),
    ("inclusao", "as inclusões estão em fonte vermelha", "; "),
    ("ajuste", "os ajustes, em fonte verde", ", logo após o texto original tachado; "),
    ("preenchimento", "o preenchimento das lacunas do modelo, em fonte azul", "; "),
    ("tachado", "as supressões e as alternativas não adotadas permanecem no texto, tachadas", "; e "),
    ("justificativa", "as justificativas seguem em fonte cinza", ", logo abaixo de cada item "
                                                                 "modificado."),
]


def legenda_md():
    out = []
    for marca, destaque, resto in LEGENDA:
        if marca == "tachado":
            out.append(f"~~{destaque}~~")
        elif marca:
            out.append(f"[{destaque}]{{.{marca}}}")
        out.append(resto)
    return "".join(out)


def legenda_html():
    """Legenda com entidades HTML e cor embutida, para o despacho do SEI."""
    out = []
    for marca, destaque, resto in LEGENDA:
        d = para_html(destaque)
        if marca == "tachado":
            out.append(f'<span style="text-decoration:line-through">{d}</span>')
        elif marca:
            out.append(f'<span style="color:{CORES[marca]}">{d}</span>')
        out.append(para_html(resto))
    return "".join(out)


def para_html(txt):
    """Markdown simples (**, *, [t](url)) → HTML só com ASCII (acentos viram entidades)."""
    txt = txt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\\", "")
    txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", txt)
    txt = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", txt)
    txt = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', txt)
    return txt.encode("ascii", "xmlcharrefreplace").decode("ascii")


# ------------------------------------------------------------------ normalização
def normaliza(txt):
    """Remove marcação markdown e diferenças só tipográficas."""
    txt = re.sub(r"\*\*|__|~~", "", txt)
    txt = re.sub(r"(?<![\w*])\*(?!\s)|(?<!\s)\*(?![\w*])", "", txt)
    txt = txt.replace("\\", "").replace("`", "")
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), (" ", " "),
                 ("–", "-"), ("—", "-"), ("…", "...")):
        txt = txt.replace(a, b)
    return re.sub(r"\s+", " ", txt).strip()


def tokens(txt):
    return re.findall(r"\w+|[^\w\s]", txt)


# ------------------------------------------------------------------ TR (markdown)
RE_ITEM = re.compile(r"^\s*(\d+(?:\.\d+)+)\.\s+(.*)$")
RE_CAP = re.compile(r"^#\s+(\d+)\.\s+(.*)$")
RE_ALINEA = re.compile(r"^\s*([a-z]|[IVXL]+)\)\s+")
RE_DIV = re.compile(r"^:::\s*\{?\s*\.?(%s)\s*\}?\s*$" % "|".join(CLASSES_DIV))
RE_SPAN_FIM = re.compile(r"\]\{\.(%s)\}" % "|".join(MARCAS_COR))


def _tachados(txt):
    """Divide um trecho sem marca de cor em [(texto, None|'tachado')] segundo ~~…~~."""
    segs, pos = [], 0
    for m in re.finditer(r"~~(.+?)~~", txt):
        if m.start() > pos:
            segs.append((txt[pos:m.start()], None))
        segs.append((m.group(1), "tachado"))
        pos = m.end()
    if pos < len(txt):
        segs.append((txt[pos:], None))
    return segs


def segmentos(txt, marca_div=None):
    """Divide o parágrafo em [(texto, marca)], marca ∈ {None, 'tachado', *MARCAS_COR}."""
    if marca_div:
        return [(txt, marca_div)]
    segs, pos = [], 0
    for m in RE_SPAN_FIM.finditer(txt):
        fim = m.start()
        prof, i = 0, fim - 1
        while i >= pos:
            if txt[i] == "]":
                prof += 1
            elif txt[i] == "[":
                if prof == 0:
                    break
                prof -= 1
            i -= 1
        if i < pos:
            continue
        if i > pos:
            segs += _tachados(txt[pos:i])
        segs.append((txt[i + 1:fim], m.group(1)))
        pos = m.end()
    if pos < len(txt):
        segs += _tachados(txt[pos:])
    return segs


def le_tr(raiz=RAIZ):
    """Lê tr/[0-9][0-9]-*.md. Devolve (itens, ordem, capitulos).

    itens[num] = {
      "pars": [(texto_markdown, marca_div)],
      "segs": [(texto_normalizado | "\\n", marca)],
      "justificativa": [parágrafo markdown, ...],   # blocos ::: justificativa após o item
      "tabela": bool, "arquivo": str, "recuo": int, "duplicado": bool (se houver),
    }
    """
    itens, ordem, capitulos = {}, [], {}
    avulsas = []   # justificativas fora de item (ex.: logo após o título do capítulo)
    for f in sorted(glob.glob(os.path.join(raiz, "tr/[0-9][0-9]-*.md"))):
        s = open(f, encoding="utf-8").read()
        s = re.sub(r"\A---\n.*?\n---\n", "", s, flags=re.S)
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
        arq = os.path.basename(f)
        atual, div, par, par_div = None, None, [], None

        def fecha():
            nonlocal par
            if par:
                if par_div == "justificativa":
                    if atual:
                        itens[atual]["justificativa"].append(" ".join(par))
                    else:
                        avulsas.append((arq, " ".join(par)))
                elif atual:
                    itens[atual]["pars"].append((" ".join(par), par_div))
            par = []

        for linha in s.split("\n"):
            l = linha.strip()
            m = RE_DIV.match(l)
            if m:
                fecha(); div = m.group(1); par_div = div; continue
            if l == ":::":
                fecha(); div = None; par_div = None; continue
            if not l:
                fecha(); continue
            m = RE_CAP.match(l)
            if m:
                fecha(); atual = None
                capitulos[m.group(1)] = (normaliza(m.group(2)), arq)
                continue
            if l.startswith("|"):
                fecha()
                if atual and div != "justificativa":
                    itens[atual]["tabela"] = True
                continue
            if re.match(r"^\*\*[^*].*\*\*$", l) and not RE_ITEM.match(l) and div != "justificativa":
                fecha(); ordem.append(("subtitulo", normaliza(l)))
                continue
            m = RE_ITEM.match(linha)
            if m and div != "justificativa":
                fecha()
                atual = m.group(1)
                if atual in itens:
                    itens[atual]["duplicado"] = True
                    continue
                itens[atual] = {"pars": [], "justificativa": [], "tabela": False, "arquivo": arq,
                                "recuo": len(linha) - len(linha.lstrip())}
                ordem.append(("item", atual))
                par, par_div = [m.group(2)], div
                continue
            if (RE_ALINEA.match(linha) and div != "justificativa") or not par:
                fecha(); par_div = div
            par.append(l)
        fecha()
    for it in itens.values():
        segs = []
        for i, (p, d) in enumerate(it["pars"]):
            if i:
                segs.append(("\n", None))
            segs += segmentos(p, d)
        it["segs"] = [(normaliza(t) if t != "\n" else t, a) for t, a in segs]
        it["segs"] = [(t, a) for t, a in it["segs"] if t]
    le_tr.avulsas = avulsas
    return itens, ordem, capitulos


def marcas(item):
    return {a for t, a in item["segs"] if a and t != "\n"}


def tipos(item):
    """Tipos de afastamento do item, pelas marcas: subconjunto de
    {'inclusao', 'ajuste', 'supressao', 'preenchimento', 'azul'}.

    O tachado imediatamente seguido de trecho verde é parte do ajuste. O tachado que contém
    "OU" é a escolha entre alternativas do modelo, não supressão.
    """
    segs = [(t, a) for t, a in item["segs"] if t != "\n" and t.strip()]
    out = set()
    for k, (t, a) in enumerate(segs):
        if a == "tachado":
            prox = segs[k + 1][1] if k + 1 < len(segs) else None
            if prox != "ajuste" and not re.search(r"\bOU\b", t):
                out.add("supressao")
        elif a:
            out.add(a)
    return out


ROTULOS = {"inclusao": "Inclusão", "ajuste": "Ajuste", "supressao": "Supressão",
           "preenchimento": "Preenchimento", "azul": "Alteração"}


def rotulo(ts):
    ordem = ["inclusao", "ajuste", "supressao", "azul", "preenchimento"]
    nomes = [ROTULOS[t] for t in ordem if t in ts]
    if not nomes:
        return ""
    nomes = [nomes[0]] + [n.lower() for n in nomes[1:]]
    if len(nomes) == 1:
        return nomes[0]
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


if __name__ == "__main__":
    if sys.argv[1:] == ["legenda-md"]:
        print(legenda_md())
    else:
        sys.exit("uso: tr_marcas.py legenda-md")
