#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confere o TR (tr/*.md), item a item, contra o Modelo AGU de TR de Serviços de TIC.

O modelo é lido diretamente do docx em referencia/ — e não de templates/, cuja conversão
pelo pandoc perde a numeração automática do Word. A numeração é reconstruída a partir de
word/numbering.xml e da cadeia de estilos, como o Word a exibe.

As marcas seguem o "Código de formatação visual sugerida" do Instrumento de Padronização AGU/MGI
de TIC (ver scripts/tr_marcas.py): inclusão em vermelho, ajuste em verde após o original tachado,
preenchimento em azul, supressão tachada e justificativa em cinza abaixo do item.

Para cada item do TR:
  - o texto sem cor (normal ou tachado) tem de reproduzir o modelo literalmente;
  - o texto colorido tem de cobrir só o que de fato foi acrescentado;
  - nenhum texto do modelo some: o que não se aplica fica tachado (só as lacunas do modelo,
    <…>, […], XX, podem dar lugar ao preenchimento).

Classes:
  IDENTICO                texto igual ao do modelo, sem marca
  PREENCHIDO              só preenchimento de lacunas, tabela do modelo ou escolha de alternativa "OU"
  ALTERADO-MARCADO        inclusão, ajuste ou supressão parcial, toda marcada
  SUPRIMIDO               item inteiro tachado, com o texto do modelo
  INCLUIDO                item sem correspondente no modelo, inteiro em vermelho
  ALTERADO-SEM-MARCA      texto diferente do modelo sem cor                               (erro)
  TACHADO-FORA-DO-MODELO  o trecho tachado não é o texto do modelo                       (erro)
  COR-EXCESSIVA           cor sobre trecho que é texto literal do modelo                 (erro)
  SUPRESSAO-SEM-TACHADO   texto do modelo apagado em vez de tachado                      (erro)
  INCLUIDO-SEM-MARCA      item sem correspondente no modelo com texto fora do vermelho   (erro)
  NUMERACAO-DESLOCADA     o texto corresponde a outro número do modelo                   (erro)
  AUSENTE                 item do modelo sem item de mesmo número no TR                  (erro)

Justificativa: todo item com inclusão, ajuste ou supressão precisa de bloco ::: justificativa
logo abaixo dele (ou de um item ascendente). Preenchimento e escolha de alternativa "OU" não
precisam. Linhas A/I/E legadas em scripts/gerar-despacho.py ainda contam, com aviso. Também é
erro justificativa sem afastamento.

Uso:
  scripts/conferir-modelo-agu.py              # relatório em build/conferencia-modelo-agu.html
  scripts/conferir-modelo-agu.py --numerado   # também regrava templates/agu-tr-servicos-tic-numerado.md

Sai com código 1 se houver erro. Requer lxml, do .venv (requirements.txt).
"""
import difflib, html, os, re, sys, zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)

from lxml import etree                                         # noqa: E402
import tr_marcas as tm_                                       # noqa: E402
from tr_marcas import normaliza, tokens, MARCAS_COR           # noqa: E402

RAIZ = tm_.RAIZ
# Modelo de referência do TR. Trocar o modelo (ex.: Compras de TIC set/2025, para aquisição de
# bens) é trocar só este bloco e o NUMERADO abaixo.
MODELO_REL = "referencia/modelos-agu/modelo-de-termo-de-referencia-servicos-tic-lei-no-14-133-abr-26.docx"
MODELO_NOME = "Modelo AGU de TR de Serviços de TIC — abr/2026"
MODELO = os.path.join(RAIZ, MODELO_REL)
DESPACHO = os.path.join(RAIZ, "scripts/gerar-despacho.py")
SAIDA = os.path.join(RAIZ, "build/conferencia-modelo-agu.html")
NUMERADO = os.path.join(RAIZ, "templates/agu-tr-servicos-tic-numerado.md")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ERROS = ("ALTERADO-SEM-MARCA", "TACHADO-FORA-DO-MODELO", "COR-EXCESSIVA",
         "SUPRESSAO-SEM-TACHADO", "INCLUIDO-SEM-MARCA", "NUMERACAO-DESLOCADA", "AUSENTE")
# Trecho colorido que coincide com o modelo por até esta quantidade de palavras é tolerado:
# é o conector que o difflib casa no meio de uma substituição ("de", "a", "o").
TOLERANCIA_COR = 3


def chave(num):
    return [int(x) for x in num.split(".")]


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
def le_tr():
    return tm_.le_tr(RAIZ)


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


def lacunas(tm):
    """Marca os tokens do modelo que são lacuna a preencher: <…>, […], XX, xxxxx.

    "XX% (xxxxx por cento)" é lacuna inteira: o "%" colado ao XX e o parêntese que contém
    xxxxx também contam, para que o valor por extenso possa ser preenchido de uma vez.
    """
    xis = [bool(re.fullmatch(r"X+|x{2,}", t)) for t in tm]
    ph, prof = [], 0
    for k, t in enumerate(tm):
        prof += t in ("<", "[")
        ph.append(prof > 0 or xis[k] or (t == "%" and k > 0 and xis[k - 1]))
        prof -= prof > 0 and t in (">", "]")
    for k, t in enumerate(tm):
        if t == "(":
            fim = next((m for m in range(k + 1, min(k + 12, len(tm))) if tm[m] == ")"), None)
            if fim and any(xis[k + 1:fim]):
                for m in range(k, fim + 1):
                    ph[m] = True
    return ph


def razao(a, b):
    return difflib.SequenceMatcher(None, tokens(a), tokens(b), autojunk=False).ratio()


def compara(mod_txt, segs, alternativa=False):
    """Compara um item do TR com o do modelo.

    Duas visões do TR:
      1. original = texto sem cor (normal + tachado): tem de ser o texto do modelo, salvo as
         lacunas que deram lugar a texto colorido;
      2. nova = texto sem o tachado: o texto colorido não pode repetir o modelo, salvo o
         trecho que está tachado (o ajuste reescreve a frase toda, como no exemplo do IPP).

    Devolve dict com classe, tipos, tokens marcados (tt, flag_tr), tokens do modelo (tm,
    flag_mod) e avisos.
    """
    tm = tokens(mod_txt)
    ph = lacunas(tm)
    tt = tokens_tr(segs)
    n = len(tt)
    flag_tr, flag_mod = [None] * n, [None] * len(tm)
    mapa = {}                       # índice em tt -> índice em tm (visão original, iguais)

    # 1. visão original
    idx1 = [j for j, (_, a) in enumerate(tt) if a not in MARCAS_COR]
    sm = difflib.SequenceMatcher(None, tm, [tt[j][0] for j in idx1], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        js = idx1[j1:j2]
        if tag == "equal":
            for i, j in zip(range(i1, i2), js):
                mapa[j] = i
                if tt[j][1] == "tachado":
                    flag_mod[i] = "tc"
            continue
        for j in js:
            flag_tr[j] = "tf" if tt[j][1] == "tachado" else "sm"
        if i2 > i1:
            lo = idx1[j1 - 1] if j1 > 0 else -1
            hi = idx1[j2] if j2 < len(idx1) else n
            cor = {tt[j][1] for j in range(lo + 1, hi) if tt[j][1] in MARCAS_COR}
            for i in range(i1, i2):
                # lacuna substituída por texto colorido: ok; marca .azul legada: tolerada
                if not ((ph[i] and cor) or "azul" in cor):
                    flag_mod[i] = "del"
    tachado_mod = {i for i, f in enumerate(flag_mod) if f == "tc"}

    # 2. visão nova
    idx2 = [j for j, (_, a) in enumerate(tt) if a != "tachado"]
    sm2 = difflib.SequenceMatcher(None, tm, [tt[j][0] for j in idx2], autojunk=False)
    for tag, i1, i2, j1, j2 in sm2.get_opcodes():
        if tag != "equal":
            continue
        run = []
        for i, j in zip(range(i1, i2), idx2[j1:j2]):
            if tt[j][1] in MARCAS_COR and not ph[i] and i not in tachado_mod:
                run.append(j)
                if len(run) > TOLERANCIA_COR:
                    for x in run:
                        flag_tr[x] = flag_tr[x] or "ex"
            else:
                run = []
    todo_cor = n > 0 and all(a in MARCAS_COR for _, a in tt)
    if todo_cor and razao(mod_txt, texto_tr(segs)) < 0.5:
        # substituição integral: as palavras coincidentes ("de", "Gov.br") não são excesso
        flag_tr = [None if f == "ex" else f for f in flag_tr]

    # tipos de afastamento e escolhas entre alternativas
    tipos, avisos = set(), []
    todo_tachado = n > 0 and all(a == "tachado" for _, a in tt)
    j = 0
    while j < n:
        a = tt[j][1]
        if a == "tachado":
            k = j
            while k < n and tt[k][1] == "tachado":
                k += 1
            ims = [mapa[x] for x in range(j, k) if x in mapa]
            escolha = (any(tm[i] == "OU" for i in ims) or (ims and all(ph[i] for i in ims))
                       or (todo_tachado and alternativa))
            seguinte = tt[k][1] if k < n else None
            if seguinte != "ajuste" and not escolha:
                tipos.add("supressao")
            j = k
            continue
        if a in MARCAS_COR:
            tipos.add(a)
            if a == "ajuste" and (j == 0 or tt[j - 1][1] not in ("tachado", "ajuste")):
                avisos.append("trecho verde sem o texto original tachado antes dele "
                              "(é inclusão?)")
        j += 1
    if "preenchimento" in tipos and not any(ph) and "OU" not in tm:
        avisos.append("azul em item sem lacuna no modelo (é ajuste ou inclusão?)")
    if "azul" in tipos:
        avisos.append("marca .azul (convenção anterior): migrar para o código do IPP")

    if "sm" in flag_tr:
        cls = "ALTERADO-SEM-MARCA"
    elif "tf" in flag_tr:
        cls = "TACHADO-FORA-DO-MODELO"
    elif "ex" in flag_tr:
        cls = "COR-EXCESSIVA"
    elif "del" in flag_mod:
        cls = "SUPRESSAO-SEM-TACHADO"
    elif todo_tachado:
        cls = "SUPRIMIDO"
    elif not tipos and not any(a for _, a in tt):
        cls = "IDENTICO"
    elif tipos <= {"preenchimento"}:
        cls = "PREENCHIDO"
    else:
        cls = "ALTERADO-MARCADO"
    return {"classe": cls, "tipos": tipos, "tt": tt, "flag_tr": flag_tr, "tm": tm,
            "flag_mod": flag_mod, "avisos": avisos}


def alternativas(ordem_mod):
    """Itens do modelo vizinhos a um "OU" isolado: alternativas excludentes."""
    alt, ant, pendente = set(), None, False
    for tipo, v in ordem_mod:
        if tipo == "ou":
            if ant:
                alt.add(ant)
            pendente = True
        elif tipo == "item":
            if pendente:
                alt.add(v)
            ant, pendente = v, False
    return alt


def classifica(mod, tr, alt=frozenset()):
    res = {}
    por_cap = defaultdict(list)
    for n in mod:
        por_cap[n.split(".")[0]].append(n)
    for n, it in tr.items():
        segs = it["segs"]
        m = mod.get(n)
        mtxt = " ".join(m["texto"]) if m else ""
        if not m:
            tt = tokens_tr(segs)
            ok = tt and all(a in ("inclusao", "azul") for _, a in tt)
            outras = tt and all(a in MARCAS_COR for _, a in tt)
            avisos = []
            if not ok and outras:
                avisos.append("item novo deveria estar todo em vermelho (inclusão)")
            res[n] = {"classe": "INCLUIDO" if outras else "INCLUIDO-SEM-MARCA",
                      "tipos": {"inclusao"}, "tt": tt,
                      "flag_tr": [None if a in MARCAS_COR else "sm" for _, a in tt],
                      "tm": [], "flag_mod": [], "avisos": avisos, "modelo": ""}
            continue
        info = compara(mtxt, segs, alternativa=n in alt)
        info["modelo"] = mtxt
        if info["classe"] == "IDENTICO" and it.get("tabela"):
            info["classe"] = "PREENCHIDO"   # tabela do modelo preenchida (conferir à parte)
        if info["classe"] == "ALTERADO-SEM-MARCA":
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
    for n in mod:
        if n not in tr:
            res[n] = {"classe": "AUSENTE", "tipos": set(), "avisos": [],
                      "modelo": " ".join(mod[n]["texto"])}
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



# ------------------------------------------------------------------ justificativas
def justificado(n, tr):
    """O item, ou um ascendente, tem bloco ::: justificativa no TR."""
    partes = n.split(".")
    for i in range(len(partes), 1, -1):
        p = ".".join(partes[:i])
        if p in tr and tr[p]["justificativa"]:
            return True
    return False


# ------------------------------------------------------------------ relatório HTML
CORES = {
    "IDENTICO": "#e8f5e9", "PREENCHIDO": "#e3f2fd", "ALTERADO-MARCADO": "#e3f2fd",
    "SUPRIMIDO": "#eceff1", "INCLUIDO": "#e3f2fd",
    "ALTERADO-SEM-MARCA": "#ffcdd2", "TACHADO-FORA-DO-MODELO": "#ffcdd2",
    "COR-EXCESSIVA": "#fff3c4", "SUPRESSAO-SEM-TACHADO": "#ffcdd2",
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




def render_tokens(tt, flags):
    """Tokens do TR agrupados por (marca, alerta)."""
    grupos, cur, buf = [], None, []
    for (tk, a), f in zip(tt, flags):
        k = (a, f)
        if k != cur and buf:
            grupos.append((cur, buf)); buf = []
        cur = k; buf.append(tk)
    if buf:
        grupos.append((cur, buf))
    out = []
    for (a, f), g in grupos:
        cls = " ".join(c for c in (a, f) if c)
        t = e(junta(g))
        out.append(f'<span class="{cls}">{t}</span>' if cls else t)
    return " ".join(out)


def render_modelo(tm, flags):
    out, cur, buf = [], None, []
    for tk, f in zip(tm, flags):
        if f != cur and buf:
            out.append((cur, buf)); buf = []
        cur = f; buf.append(tk)
    if buf:
        out.append((cur, buf))
    return " ".join(f"<del>{e(junta(g))}</del>" if f == "del" else e(junta(g))
                    for f, g in out)


def relatorio(mod, tr, res, capitulos, faltam_just, just_sobra, mod_caps):
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
        mh = (render_modelo(r["tm"], r["flag_mod"]) if r.get("tm")
              else e(r["modelo"]) if r["modelo"] else "<i>—</i>")
        th = render_tokens(r["tt"], r["flag_tr"]) if it else "<i>(ausente no TR)</i>"
        if it and it["justificativa"]:
            th += "".join(f'<div class="justificativa">{e(p)}</div>' for p in it["justificativa"])
        extra = []
        if r.get("tipos"):
            extra.append("tipos: " + tm_.rotulo(r["tipos"]).lower())
        if r.get("corresponde"):
            extra.append(f'texto corresponde ao item {r["corresponde"]} do modelo')
        if it and it.get("tabela"):
            extra.append("contém tabela (conferir à parte)")
        if n in faltam_just:
            extra.append("<b>sem justificativa</b>")
        if n in just_sobra:
            extra.append("<b>justificativa sem afastamento</b>")
        if it and it.get("duplicado"):
            extra.append("<b>número duplicado no TR</b>")
        extra += [f"aviso: {e(a)}" for a in r.get("avisos", [])]
        nota = f'<div class="nota">{"; ".join(extra)}</div>' if extra else ""
        linhas.append(f'<tr class="l {c}" style="--bg:{CORES[c]}"><td class="n">{n}</td>'
                      f'<td class="c">{c}</td><td>{mh}</td><td>{th}{nota}</td></tr>')
    filtros = "".join(
        f'<label style="background:{CORES[k]}"><input type="checkbox" checked data-c="{k}"> '
        f'{k} ({cont.get(k, 0)})</label>' for k in CORES)
    sobra = ("<p><b>Justificativas sem afastamento correspondente no TR:</b> "
             + ", ".join(sorted(just_sobra, key=chave)) + "</p>") if just_sobra else ""
    c = tm_.CORES
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Conferência TR × Modelo AGU</title><style>
body{{font-family:system-ui,sans-serif;font-size:14px;margin:16px;color:#111;background:#fff}}
table{{border-collapse:collapse;width:100%}} td{{border:1px solid #ccc;padding:4px 6px;vertical-align:top}}
tr.l td{{background:var(--bg)}} tr.l td:nth-child(3),tr.l td:nth-child(4){{background:#fff;width:42%}}
td.n{{white-space:nowrap;font-weight:600}} td.c{{font-size:11px;white-space:nowrap}}
tr.cap td{{background:#263238;color:#fff;font-weight:600}}
.inclusao{{color:{c["inclusao"]}}} .ajuste{{color:{c["ajuste"]}}} .preenchimento{{color:{c["preenchimento"]}}}
.azul{{color:{c["azul"]}}} .tachado{{text-decoration:line-through}}
.justificativa{{color:{c["justificativa"]};margin-top:4px}}
.sm,.tf{{background:#ffcdd2;outline:1px solid #b71c1c}} .ex{{background:#fff3c4}} del{{color:#b71c1c;background:#ffcdd2}}
.nota{{font-size:12px;color:#555;margin-top:4px}} label{{display:inline-block;margin:2px;padding:2px 6px;border-radius:4px;font-size:12px}}
.leg span{{padding:0 4px}}
</style></head><body>
<h1>Conferência do TR contra o {e(MODELO_NOME)}</h1>
<p class="leg">Coluna do TR, no código do IPP AGU/MGI: <span class="inclusao">inclusão</span>,
<span class="ajuste">ajuste</span>, <span class="preenchimento">preenchimento</span>,
<span class="tachado">supressão</span>, <span class="justificativa">justificativa</span>.
Alertas: <span class="sm">fundo vermelho</span> = difere do modelo sem cor, ou tachado que não é o
texto do modelo; <span class="ex">fundo amarelo</span> = cor sobre texto idêntico ao modelo.
Coluna do modelo: <del>vermelho riscado</del> = texto do modelo apagado em vez de tachado.</p>
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
    res = classifica(mod, tr, alternativas(ordem_mod))

    # Justificativas: no TR (::: justificativa) ou, legado, em linha A/I/E do despacho.
    citados = le_despacho()
    exige = {n for n, r in res.items() if r.get("tipos", set()) - {"preenchimento"}}
    faltam_just = {n for n in exige if not justificado(n, tr) and not coberto(n, citados)}
    via_despacho = {n for n in exige if not justificado(n, tr) and coberto(n, citados)}
    marcados = {n for n, r in res.items() if r["classe"] not in ("IDENTICO", "AUSENTE")}
    just_sobra = {n for n, it in tr.items() if it["justificativa"]
                  and not any(a == n or a.startswith(n + ".") for a in marcados)}
    itens_desp = {c[1] for c in citados if c[0] == "item"}
    just_sobra |= {n for n in itens_desp
                   if n in res and res[n]["classe"] == "IDENTICO"
                   and not any(a.startswith(n + ".") for a in marcados)}
    avulsas = getattr(tm_.le_tr, "avulsas", [])

    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    open(SAIDA, "w", encoding="utf-8").write(
        relatorio(mod, tr, res, capitulos, faltam_just, just_sobra, mod_caps))

    cont = Counter(r["classe"] for r in res.values())
    print(f"Modelo: {len(mod)} itens em {len(mod_caps)} capítulos. TR: {len(tr)} itens.")
    for k in CORES:
        if cont.get(k):
            print(f"  {k:24s} {cont[k]:4d}{'   <- erro' if k in ERROS else ''}")
    caps_div = [c for c in mod_caps
                if normaliza(mod_caps[c]).upper() != capitulos.get(c, ("",))[0].upper()]
    if caps_div:
        print(f"  títulos de capítulo divergentes: {', '.join(caps_div)}")
    recuo = [n for n, it in tr.items() if it["recuo"] >= 4]
    if recuo:
        print(f"  itens com recuo >= 4 espaços (viram bloco de código): {len(recuo)}")
    print(f"  afastamentos sem justificativa: {len(faltam_just)}"
          + (f" ({', '.join(sorted(faltam_just, key=chave)[:10])}…)" if faltam_just else ""))
    print(f"  justificativas sem afastamento: {len(just_sobra)}"
          + (f" ({', '.join(sorted(just_sobra, key=chave))})" if just_sobra else ""))
    if avulsas:
        print(f"  justificativas fora de item (não vão ao despacho): {len(avulsas)} "
              f"({', '.join(sorted({a for a, _ in avulsas}))})")
    if via_despacho:
        print(f"  AVISO: {len(via_despacho)} afastamento(s) justificado(s) só em linha A/I/E de "
              "scripts/gerar-despacho.py; leve o texto para ::: justificativa no TR")
    n_avisos = sum(1 for r in res.values() if r.get("avisos"))
    if n_avisos:
        print(f"  AVISO: {n_avisos} item(ns) com aviso de semântica das cores (ver relatório)")
    print(f">> {os.path.relpath(SAIDA, RAIZ)}")
    erro = (any(cont.get(k) for k in ERROS) or caps_div or recuo or faltam_just or just_sobra
            or avulsas)
    sys.exit(1 if erro else 0)


if __name__ == "__main__":
    main()
