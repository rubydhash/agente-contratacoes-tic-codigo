#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere o TR (tr/*.md), item a item, contra o Modelo AGU de TR de Serviços de TIC.

O modelo é lido diretamente do docx em referencia/ — e não de templates/, cuja conversão
pelo pandoc perde a numeração automática do Word. A numeração é reconstruída a partir de
word/numbering.xml e da cadeia de estilos, como o Word a exibe.

Para cada item do TR, o texto fora do azul tem de reproduzir o modelo literalmente, e o
azul tem de cobrir só o que de fato difere. Classes:

  IDENTICO             texto igual ao do modelo, sem azul
  ALTERADO-MARCADO     difere do modelo, e toda a diferença está em azul
  SUPRIMIDO            "[Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).]{.azul}"
  INCLUIDO             item sem correspondente no modelo, inteiramente em azul
  ALTERADO-SEM-MARCA   há diferença fora do azul                                  (erro)
  AZUL-EXCESSIVO       o azul cobre trecho que é texto literal do modelo           (erro)
  INCLUIDO-SEM-MARCA   item sem correspondente no modelo com texto fora do azul    (erro)
  NUMERACAO-DESLOCADA  o texto corresponde a outro número do modelo               (erro)
  AUSENTE              item do modelo sem item de mesmo número no TR               (erro)

Também confere o despacho (scripts/gerar-despacho.py) nos dois sentidos: todo afastamento
precisa de linha no despacho, e toda linha do despacho precisa apontar um afastamento.

Uso:
  scripts/conferir-modelo-agu.py              # relatório em build/conferencia-modelo-agu.html
  scripts/conferir-modelo-agu.py --numerado   # também regrava templates/agu-tr-servicos-tic-numerado.md

Sai com código 1 se houver erro. Requer python3 e lxml.
"""
import difflib, glob, html, os, re, sys, zipfile
from collections import Counter, defaultdict
from lxml import etree

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Modelo de referência do TR. Trocar o modelo (ex.: Compras de TIC set/2025, para aquisição de
# bens) é trocar só este bloco e o NUMERADO abaixo.
MODELO_REL = "referencia/modelos-agu/modelo-de-termo-de-referencia-servicos-tic-lei-no-14-133-abr-26.docx"
MODELO_NOME = "Modelo AGU de TR de Serviços de TIC — abr/2026"
MODELO = os.path.join(RAIZ, MODELO_REL)
DESPACHO = os.path.join(RAIZ, "scripts/gerar-despacho.py")
SAIDA = os.path.join(RAIZ, "build/conferencia-modelo-agu.html")
NUMERADO = os.path.join(RAIZ, "templates/agu-tr-servicos-tic-numerado.md")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
SUPRIMIDO = "Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos)."
ERROS = ("ALTERADO-SEM-MARCA", "AZUL-EXCESSIVO", "INCLUIDO-SEM-MARCA",
         "NUMERACAO-DESLOCADA", "AUSENTE")
# Trecho azul que coincide com o modelo por até esta quantidade de palavras é tolerado:
# é o conector que o difflib casa no meio de uma substituição ("de", "a", "o").
TOLERANCIA_AZUL = 3


def chave(num):
    return [int(x) for x in num.split(".")]


# ------------------------------------------------------------------ normalização
def normaliza(txt):
    """Remove marcação markdown e diferenças só tipográficas."""
    txt = re.sub(r"\*\*|__", "", txt)
    txt = re.sub(r"(?<![\w*])\*(?!\s)|(?<!\s)\*(?![\w*])", "", txt)
    txt = txt.replace("\\", "").replace("`", "")
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), (" ", " "),
                 ("–", "-"), ("—", "-"), ("…", "...")):
        txt = txt.replace(a, b)
    return re.sub(r"\s+", " ", txt).strip()


def tokens(txt):
    return re.findall(r"\w+|[^\w\s]", txt)


# ------------------------------------------------------------------ modelo (docx)
def romano(n):
    val = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, r in val:
        while n >= v:
            s += r
            n -= v
    return s


def le_modelo():
    z = zipfile.ZipFile(MODELO)
    doc = etree.fromstring(z.read("word/document.xml"))
    sty = etree.fromstring(z.read("word/styles.xml"))
    num = etree.fromstring(z.read("word/numbering.xml"))
    estilos = {s.get(W + "styleId"): s for s in sty.iter(W + "style")}

    def numpr_estilo(sid, prof=0):
        s = estilos.get(sid)
        if s is None or prof > 10:
            return None, None
        n = s.find(f"{W}pPr/{W}numPr")
        nid = il = None
        if n is not None:
            a, b = n.find(W + "numId"), n.find(W + "ilvl")
            nid = a.get(W + "val") if a is not None else None
            il = b.get(W + "val") if b is not None else None
        if nid is None:
            bo = s.find(W + "basedOn")
            if bo is not None:
                pn, pi = numpr_estilo(bo.get(W + "val"), prof + 1)
                nid, il = pn, il or pi
        return nid, il

    num2abs = {n.get(W + "numId"): n.find(W + "abstractNumId").get(W + "val")
               for n in num.findall(W + "num")}
    formatos = {}
    for a in num.findall(W + "abstractNum"):
        lv = {}
        for l in a.findall(W + "lvl"):
            f, t = l.find(W + "numFmt"), l.find(W + "lvlText")
            lv[l.get(W + "ilvl")] = (f.get(W + "val") if f is not None else "",
                                     t.get(W + "val") if t is not None else "")
        formatos[a.get(W + "abstractNumId")] = lv

    contadores = defaultdict(lambda: [0] * 9)
    itens = {}        # num -> {"texto": [paragrafos], "tabela": bool, "estilo": str}
    ordem = []        # [("item", num) | ("subtitulo", texto) | ("ou", "")]
    atual = None
    alinea = 0
    for p in doc.find(W + "body").iter(W + "p"):
        em_tabela = any(a.tag == W + "tbl" for a in p.iterancestors())
        ps = p.find(f"{W}pPr/{W}pStyle")
        est = ps.get(W + "val") if ps is not None else None
        n = p.find(f"{W}pPr/{W}numPr")
        nid = il = None
        if n is not None:
            a, b = n.find(W + "numId"), n.find(W + "ilvl")
            nid = a.get(W + "val") if a is not None else None
            il = b.get(W + "val") if b is not None else None
        if nid is None and est:
            sn, si = numpr_estilo(est)
            nid, il = sn, il or si
        il = int(il or 0)
        txt = normaliza("".join(t.text or "" for t in p.iter(W + "t")))
        if not txt:
            continue
        if em_tabela:
            if atual:
                itens[atual]["tabela"] = True
            continue
        if nid and nid != "0" and nid in num2abs:
            ab = num2abs[nid]
            c = contadores[ab]
            c[il] += 1
            for k in range(il + 1, 9):
                c[k] = 0
            fmt, tpl = formatos[ab].get(str(il), ("", ""))
            if fmt == "decimal":
                rot = re.sub(r"%(\d)", lambda m: str(c[int(m.group(1)) - 1]), tpl).rstrip(".")
                # Lista do Word sem os níveis superiores (o Word exibe "0.0.0.0.1"): o item é
                # subitem do anterior, como o modelo o apresenta (ex.: 8.4.4.2.1 no de Compras).
                if atual and "0" in rot.split(".")[:il]:
                    rot = f"{atual}.{c[il]}"
                atual, alinea = rot, 0
                itens[rot] = {"texto": [txt], "tabela": False, "estilo": est}
                ordem.append(("item", rot))
                continue
            if atual:
                alinea += 1
                marca = (romano(alinea) if fmt.startswith("upperRoman")
                         else chr(ord("a") + alinea - 1) if fmt.startswith("lowerLetter")
                         else str(alinea))
                itens[atual]["texto"].append(f"{marca}) {txt}")
            continue
        if est and "SemNum" in est:
            ordem.append(("subtitulo", txt))
        elif txt.upper() == "OU":
            ordem.append(("ou", ""))
        elif atual:
            itens[atual]["texto"].append(txt)
    return itens, ordem


# ------------------------------------------------------------------ TR (markdown)
RE_ITEM = re.compile(r"^\s*(\d+(?:\.\d+)+)\.\s+(.*)$")
RE_CAP = re.compile(r"^#\s+(\d+)\.\s+(.*)$")
RE_ALINEA = re.compile(r"^\s*([a-z]|[IVXL]+)\)\s+")


def segmentos(txt, azul_div):
    """Divide o parágrafo em [(texto, azul)] segundo os spans [..]{.azul}."""
    if azul_div:
        return [(txt, True)]
    segs, pos = [], 0
    for m in re.finditer(r"\]\{\.azul\}", txt):
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
            segs.append((txt[pos:i], False))
        segs.append((txt[i + 1:fim], True))
        pos = m.end()
    if pos < len(txt):
        segs.append((txt[pos:], False))
    return segs


def le_tr():
    itens, ordem, capitulos = {}, [], {}
    arquivos = sorted(glob.glob(os.path.join(RAIZ, "tr/[0-9][0-9]-*.md")))
    for f in arquivos:
        s = open(f, encoding="utf-8").read()
        s = re.sub(r"\A---\n.*?\n---\n", "", s, flags=re.S)
        s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
        atual, div, par, par_azul = None, False, [], False

        def fecha():
            nonlocal par
            if par and atual:
                itens[atual]["pars"].append((" ".join(par), par_azul))
            par = []

        for linha in s.split("\n"):
            l = linha.strip()
            if re.match(r"^:::\s*\{?\.?azul\}?\s*$", l):
                fecha(); div = True; continue
            if l == ":::":
                fecha(); div = False; continue
            if not l:
                fecha(); continue
            m = RE_CAP.match(l)
            if m:
                fecha(); atual = None
                capitulos[m.group(1)] = (normaliza(m.group(2)), os.path.basename(f))
                continue
            if l.startswith("|"):
                fecha()
                if atual:
                    itens[atual]["tabela"] = True
                continue
            if re.match(r"^\*\*[^*].*\*\*$", l) and not RE_ITEM.match(l):
                fecha(); ordem.append(("subtitulo", normaliza(l)))
                continue
            m = RE_ITEM.match(linha)
            if m:
                fecha()
                atual = m.group(1)
                if atual in itens:
                    itens[atual]["duplicado"] = True
                    continue
                itens[atual] = {"pars": [], "tabela": False, "arquivo": os.path.basename(f),
                                "recuo": len(linha) - len(linha.lstrip())}
                ordem.append(("item", atual))
                par, par_azul = [m.group(2)], div
                continue
            if RE_ALINEA.match(linha) or not par:
                fecha(); par_azul = div
            par.append(l)
        fecha()
    for it in itens.values():
        segs = []
        for i, (p, az) in enumerate(it["pars"]):
            if i:
                segs.append(("\n", False))
            segs += segmentos(p, az)
        it["segs"] = [(normaliza(t) if t != "\n" else t, a) for t, a in segs]
    return itens, ordem, capitulos


# ------------------------------------------------------------------ comparação
def tokens_tr(segs):
    out = []
    for t, a in segs:
        if t == "\n":
            continue
        out += [(tk, a) for tk in tokens(t)]
    return out


def texto_tr(segs):
    return " ".join(t for t, _ in segs if t != "\n")


def compara(mod_txt, segs):
    """Devolve (classe, ops) com ops = [(tag, tokens_modelo, [(token, azul)])]."""
    tm = tokens(mod_txt)
    # conteúdo de placeholder do modelo (<...>, [...]) não é texto literal: pode sair em azul
    ph, prof = [], 0
    for t in tm:
        prof += t in ("<", "[")
        ph.append(prof > 0)
        prof -= prof > 0 and t in (">", "]")
    tt = tokens_tr(segs)
    sm = difflib.SequenceMatcher(None, tm, [t for t, _ in tt], autojunk=False)
    ops = [(tag, tm[i1:i2], tt[j1:j2], ph[i1:i2]) for tag, i1, i2, j1, j2 in sm.get_opcodes()]
    sem_marca = excesso = False
    for k, (tag, mt, trt, mph) in enumerate(ops):
        if tag == "equal":
            run = 0
            for (_, az), p in zip(trt, mph):
                run = run + 1 if az and not p else 0
                if run > TOLERANCIA_AZUL:
                    excesso = True
        elif tag in ("replace", "insert"):
            if not all(az for _, az in trt):
                sem_marca = True
        elif tag == "delete":
            # supressão parcial: aceita se encostada em trecho azul
            antes = ops[k - 1][2][-1:] if k > 0 else []
            depois = ops[k + 1][2][:1] if k + 1 < len(ops) else []
            if not any(az for _, az in antes + depois):
                sem_marca = True
    if sem_marca:
        return "ALTERADO-SEM-MARCA", [o[:3] for o in ops]
    if excesso:
        return "AZUL-EXCESSIVO", [o[:3] for o in ops]
    ops = [o[:3] for o in ops]
    if all(tag == "equal" for tag, _, _ in ops) and not any(az for _, az in tt):
        return "IDENTICO", ops
    return "ALTERADO-MARCADO", ops


def eh_suprimido(segs):
    txt = texto_tr(segs)
    return txt == SUPRIMIDO or txt == f"[{SUPRIMIDO}]"


def razao(a, b):
    return difflib.SequenceMatcher(None, tokens(a), tokens(b), autojunk=False).ratio()


def classifica(mod, tr):
    res = {}
    por_cap = defaultdict(list)
    for n in mod:
        por_cap[n.split(".")[0]].append(n)
    for n, it in tr.items():
        segs = it["segs"]
        m = mod.get(n)
        mtxt = " ".join(m["texto"]) if m else ""
        if eh_suprimido(segs):
            cls = "SUPRIMIDO" if m and all(a for t, a in segs if t.strip()) else (
                  "SUPRIMIDO" if m else "INCLUIDO-SEM-MARCA")
            if m and not all(a for t, a in segs if t.strip()):
                cls = "ALTERADO-SEM-MARCA"
            res[n] = {"classe": cls, "ops": None, "modelo": mtxt}
            continue
        if not m:
            todo_azul = all(a for t, a in segs if t.strip() and t != "\n")
            res[n] = {"classe": "INCLUIDO" if todo_azul else "INCLUIDO-SEM-MARCA",
                      "ops": None, "modelo": ""}
            continue
        cls, ops = compara(mtxt, segs)
        if cls == "IDENTICO" and it.get("tabela"):
            cls = "ALTERADO-MARCADO"   # tabela do modelo preenchida (conferir à parte)
        # substituição integral: item todo em azul com texto sem relação com o do modelo —
        # as palavras coincidentes ("de", "Plataforma Gov.br") não são azul excessivo
        if (cls == "AZUL-EXCESSIVO" and all(a for t, a in segs if t.strip() and t != "\n")
                and razao(mtxt, texto_tr(segs)) < 0.5):
            cls = "ALTERADO-MARCADO"
        info = {"classe": cls, "ops": ops, "modelo": mtxt}
        if cls in ("ALTERADO-SEM-MARCA",) and not all(a for t, a in segs if t.strip()):
            preto = " ".join(t for t, a in segs if not a and t != "\n")
            r0 = razao(mtxt, texto_tr(segs))
            if r0 < 0.6 and len(tokens(preto)) >= 6:
                melhor, rm = None, 0.0
                for o in por_cap[n.split(".")[0]]:
                    if o == n:
                        continue
                    r = razao(" ".join(mod[o]["texto"]), texto_tr(segs))
                    if r > rm:
                        melhor, rm = o, r
                if melhor and rm >= 0.85:
                    info["classe"] = "NUMERACAO-DESLOCADA"
                    info["corresponde"] = melhor
        res[n] = info
    ausentes = [n for n in mod if n not in tr]
    for n in ausentes:
        res[n] = {"classe": "AUSENTE", "ops": None, "modelo": " ".join(mod[n]["texto"])}
    return res


# ------------------------------------------------------------------ despacho
def le_despacho():
    s = open(DESPACHO, encoding="utf-8").read()
    citados = set()
    for m in re.finditer(r'^\s*([AIEN])\(\s*"([^"]*)"', s, flags=re.M):
        tipo, arg = m.group(1), html.unescape(m.group(2))
        faixas = re.findall(r"(\d+(?:\.\d+)+)\s+a\s+(\d+(?:\.\d+)+)", arg)
        for a, b in faixas:
            citados.add(("faixa", a, b))
        pontas = {x for f in faixas for x in f}
        for x in re.findall(r"\d+(?:\.\d+)+", arg):
            # linha informativa (N) e ponta de faixa não precisam apontar afastamento
            citados.add(("item", x) if tipo != "N" and x not in pontas else ("ref", x))
        for x in re.findall(r"^(\d+) e subitens", arg):
            citados.add(("cap", x))
    return citados


def coberto(n, citados):
    partes = n.split(".")
    for i in range(len(partes), 1, -1):
        if ("item", ".".join(partes[:i])) in citados:
            return True
    if ("cap", partes[0]) in citados:
        return True
    for c in citados:
        if c[0] == "faixa" and chave(c[1]) <= chave(n) <= chave(c[2]) + [99]:
            return True
    return False


# ------------------------------------------------------------------ relatório HTML
CORES = {
    "IDENTICO": "#e8f5e9", "ALTERADO-MARCADO": "#e3f2fd", "SUPRIMIDO": "#eceff1",
    "INCLUIDO": "#e3f2fd", "ALTERADO-SEM-MARCA": "#ffcdd2", "AZUL-EXCESSIVO": "#fff3c4",
    "INCLUIDO-SEM-MARCA": "#ffcdd2", "NUMERACAO-DESLOCADA": "#ffcdd2", "AUSENTE": "#ffcdd2",
}


def e(x):
    return html.escape(x, quote=False)


def junta(tks):
    s = ""
    for t in tks:
        if s and re.match(r"\w", t) and (re.search(r"[\w,;:.)!?\"%]$", s)):
            s += " "
        elif s and t in "(\"" and not s.endswith(("(", " ")):
            s += " "
        s += t
    return s


def render_ops(ops):
    mod, tr = [], []
    for tag, mt, trt in ops:
        if tag in ("replace", "delete") and mt:
            mod.append(f'<del>{e(junta(mt))}</del>')
        elif mt:
            mod.append(e(junta(mt)))
        grupo, cur = [], None
        for tk, az in trt:
            k = ("eqaz" if az else "eq") if tag == "equal" else ("az" if az else "sm")
            if k != cur and grupo:
                tr.append((cur, grupo)); grupo = []
            cur = k; grupo.append(tk)
        if grupo:
            tr.append((cur, grupo))
    cls = {"eq": None, "az": "az", "sm": "sm", "eqaz": "ex"}
    out = []
    for k, g in tr:
        t = e(junta(g))
        out.append(f'<span class="{cls[k]}">{t}</span>' if cls[k] else t)
    return " ".join(mod), " ".join(out)


def render_segs(segs):
    out = []
    for t, a in segs:
        if t == "\n":
            out.append("<br>")
        else:
            out.append(f'<span class="az">{e(t)}</span>' if a else e(t))
    return " ".join(out)


def relatorio(mod, tr, res, capitulos, faltam_desp, desp_sobra, mod_caps):
    cont = Counter(r["classe"] for r in res.values())
    linhas = []
    cap_ant = None
    for n in sorted(res, key=chave):
        cap = n.split(".")[0]
        if cap != cap_ant:
            titulo_mod = mod_caps.get(cap, "—")
            titulo_tr = capitulos.get(cap, ("—", ""))
            ok = "" if normaliza(titulo_mod).upper() == titulo_tr[0].upper() else " style='background:#ffcdd2'"
            linhas.append(f'<tr class="cap"><td colspan="4"{ok}>{cap}. Modelo: {e(titulo_mod)}'
                          f' &nbsp;|&nbsp; TR: {e(titulo_tr[0])} <small>({e(titulo_tr[1])})</small></td></tr>')
            cap_ant = cap
        r = res[n]
        c = r["classe"]
        it = tr.get(n)
        if r.get("ops"):
            mh, th = render_ops(r["ops"])
        else:
            mh = e(r["modelo"]) if r["modelo"] else "<i>—</i>"
            th = render_segs(it["segs"]) if it else "<i>(ausente no TR)</i>"
        extra = []
        if r.get("corresponde"):
            extra.append(f'texto corresponde ao item {r["corresponde"]} do modelo')
        if it and it.get("tabela"):
            extra.append("contém tabela (conferir à parte)")
        if n in faltam_desp:
            extra.append("<b>sem linha no despacho</b>")
        if it and it.get("duplicado"):
            extra.append("<b>número duplicado no TR</b>")
        nota = f'<div class="nota">{"; ".join(extra)}</div>' if extra else ""
        linhas.append(f'<tr class="l {c}" style="--bg:{CORES[c]}"><td class="n">{n}</td>'
                      f'<td class="c">{c}</td><td>{mh}</td><td>{th}{nota}</td></tr>')
    filtros = "".join(
        f'<label style="background:{CORES[k]}"><input type="checkbox" checked data-c="{k}"> '
        f'{k} ({cont.get(k, 0)})</label>' for k in CORES)
    sobra = ("<p><b>Linhas do despacho sem afastamento correspondente no TR:</b> "
             + ", ".join(sorted(desp_sobra, key=chave)) + "</p>") if desp_sobra else ""
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência TR × Modelo AGU</title><style>
body{{font-family:system-ui,sans-serif;font-size:14px;margin:16px;color:#111;background:#fff}}
table{{border-collapse:collapse;width:100%}} td{{border:1px solid #ccc;padding:4px 6px;vertical-align:top}}
tr.l td{{background:var(--bg)}} tr.l td:nth-child(3),tr.l td:nth-child(4){{background:#fff;width:42%}}
td.n{{white-space:nowrap;font-weight:600}} td.c{{font-size:11px;white-space:nowrap}}
tr.cap td{{background:#263238;color:#fff;font-weight:600}}
.az{{color:#0000cc}} .sm{{background:#ffcdd2;color:#b71c1c;font-weight:600}}
.ex{{color:#0000cc;background:#fff3c4}} del{{color:#b71c1c}}
.nota{{font-size:12px;color:#555;margin-top:4px}} label{{display:inline-block;margin:2px;padding:2px 6px;border-radius:4px;font-size:12px}}
.leg span{{padding:0 4px}}
</style></head><body>
<h1>Conferência do TR contra o {e(MODELO_NOME)}</h1>
<p class="leg">Coluna do TR: <span class="az">azul</span> = marcado como alteração;
<span class="sm">vermelho</span> = difere do modelo sem marcação;
<span class="ex">azul em amarelo</span> = azul sobre texto idêntico ao modelo.
Coluna do modelo: <del>riscado</del> = texto do modelo substituído ou retirado.</p>
<div>{filtros}</div>{sobra}
<table>{"".join(linhas)}</table>
<script>
document.querySelectorAll('input[data-c]').forEach(function(cb){{cb.addEventListener('change',function(){{
document.querySelectorAll('tr.'+cb.dataset.c).forEach(function(r){{r.style.display=cb.checked?'':'none'}})}})}});
</script></body></html>"""


def grava_numerado(mod, ordem):
    out = [f"# {MODELO_NOME}, com a numeração do Word",
           "",
           "<!-- GERADO por scripts/conferir-modelo-agu.py --numerado a partir de",
           f"{MODELO_REL}.",
           "Não editar à mão. As notas explicativas do modelo (comentários do Word) e o conteúdo",
           "das tabelas não são reproduzidos. -->", ""]
    for tipo, v in ordem:
        if tipo == "subtitulo":
            out += [f"**{v}**", ""]
        elif tipo == "ou":
            out += ["OU", ""]
        else:
            it = mod[v]
            if "." not in v:
                out += [f"## {v}. {it['texto'][0]}", ""]
                continue
            out += [f"{v}. {it['texto'][0]}", ""]
            out += [f"   {p}" for p in it["texto"][1:]] + ([""] if it["texto"][1:] else [])
            if it["tabela"]:
                out += ["   *(tabela no modelo)*", ""]
    open(NUMERADO, "w", encoding="utf-8").write("\n".join(out))
    print(f">> {os.path.relpath(NUMERADO, RAIZ)}")


def main():
    mod_todos, ordem_mod = le_modelo()
    mod_caps = {n: v["texto"][0] for n, v in mod_todos.items() if "." not in n}
    mod = {n: v for n, v in mod_todos.items() if "." in n}
    if "--numerado" in sys.argv:
        grava_numerado(mod_todos, ordem_mod)
    tr, ordem_tr, capitulos = le_tr()
    res = classifica(mod, tr)

    citados = le_despacho()
    afast = {n for n, r in res.items() if r["classe"] not in ("IDENTICO", "AUSENTE")}
    faltam_desp = {n for n in afast if not coberto(n, citados)}
    itens_desp = {c[1] for c in citados if c[0] == "item"}
    desp_sobra = {n for n in itens_desp
                  if n in res and res[n]["classe"] == "IDENTICO"
                  and not any(a.startswith(n + ".") for a in afast)}

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    open(SAIDA, "w", encoding="utf-8").write(
        relatorio(mod, tr, res, capitulos, faltam_desp, desp_sobra, mod_caps))

    cont = Counter(r["classe"] for r in res.values())
    print(f"Modelo: {len(mod)} itens em {len(mod_caps)} capítulos. TR: {len(tr)} itens.")
    for k in CORES:
        if cont.get(k):
            print(f"  {k:22s} {cont[k]:4d}{'   <- erro' if k in ERROS else ''}")
    caps_div = [c for c in mod_caps
                if normaliza(mod_caps[c]).upper() != capitulos.get(c, ("",))[0].upper()]
    if caps_div:
        print(f"  títulos de capítulo divergentes: {', '.join(caps_div)}")
    recuo = [n for n, it in tr.items() if it["recuo"] >= 4]
    if recuo:
        print(f"  itens com recuo >= 4 espaços (viram bloco de código): {len(recuo)}")
    print(f"  afastamentos sem linha no despacho: {len(faltam_desp)}")
    print(f"  linhas do despacho sem afastamento: {len(desp_sobra)}")
    print(f">> {os.path.relpath(SAIDA, RAIZ)}")
    erro = any(cont.get(k) for k in ERROS) or caps_div or recuo or faltam_desp or desp_sobra
    sys.exit(1 if erro else 0)


if __name__ == "__main__":
    main()
