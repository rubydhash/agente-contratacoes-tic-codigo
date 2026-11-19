#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera os anexos do TR em PDF (A4 retrato), a partir das fontes markdown em tr/.

Anexos cobertos: todo tr/ANEXO *.md, cada um em build/<mesmo nome>.pdf. Anexo em docx (ex.:
Termo de Compromisso) não passa por aqui — ver decisoes/2026-11-19-anexos-tr-md-pdf.md.
O cabeçalho de cada página leva o nome do órgão de etp/00-metadados.yaml (orgao.nome e sigla).

O markdown lido é um subconjunto fixo, escrito junto com este script — não um
conversor genérico. São reconhecidos:
  # Título           → centralizado, negrito, 13 pt
  ## Seção           → negrito, 11 pt
  parágrafo          → justificado, 10 pt, com **negrito** (markdown do fpdf2)
  <!--tabela larguras=A,B,...-->  → diretriva: larguras das colunas, em mm,
                                    aplicada à tabela pipe imediatamente seguinte
  tabela pipe        → fpdf2 table(), com **negrito** nas células
Comentários HTML são ignorados, exceto a diretriva acima. Os trechos entre <...>
são placeholders da minuta, preenchidos no uso.

Não edite os PDFs: edite os markdown e regenere. Uso:
  .venv/bin/python scripts/gerar-anexos-tr.py [caminho.md ...]
  (sem argumentos, gera todos os tr/ANEXO *.md)

Requer fpdf2 e PyYAML, do .venv (requirements.txt), e a fonte DejaVu (scripts/_ambiente.py).
O fpdf2 só é importado se houver anexo a gerar: sem tr/ANEXO *.md, o build do TR não depende dele.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)

import yaml                                                    # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def saida_pdf(md):
    return "build/" + os.path.basename(md).rsplit(".", 1)[0] + ".pdf"


def anexos():
    """(fonte .md, saída .pdf) de cada tr/ANEXO *.md, em ordem de nome."""
    return [(os.path.relpath(p, RAIZ), saida_pdf(p))
            for p in sorted(glob.glob(os.path.join(RAIZ, "tr", "ANEXO *.md")))]


def nome_orgao():
    """'Nome — SIGLA' de etp/00-metadados.yaml; vazio enquanto houver <preencher>."""
    try:
        o = yaml.safe_load(open(os.path.join(RAIZ, "etp/00-metadados.yaml"),
                                encoding="utf-8")).get("orgao") or {}
    except (OSError, yaml.YAMLError):
        return ""
    partes = [str(o.get(k) or "").strip() for k in ("nome", "sigla")]
    partes = [p for p in partes if p and "<preencher" not in p]
    return " — ".join(partes)


POS = {"esquerda": "L", "centro": "C", "direita": "R", "justificado": "J"}


def classe_pdf():
    """Importa o fpdf2 sob demanda e devolve (AnexoTR, FontFace)."""
    from fpdf import FPDF
    from fpdf.fonts import FontFace
    normal = _ambiente.fonte_ttf("DejaVuSans.ttf")
    negrito = _ambiente.fonte_ttf("DejaVuSans-Bold.ttf")

    class AnexoTR(FPDF):
        def __init__(self, titulo):
            super().__init__(orientation="P", unit="mm", format="A4")
            self.titulo = titulo
            self.set_margins(15, 15, 15)          # área útil: 180 mm
            self.set_auto_page_break(True, margin=15)
            # Não há DejaVu itálica no fonts-dejavu-core: o itálico sai em redondo.
            self.add_font("DejaVu", "", normal)
            self.add_font("DejaVu", "B", negrito)
            self.add_font("DejaVu", "I", normal)
            self.add_font("DejaVu", "BI", negrito)

        def header(self):
            self.set_font("DejaVu", "", 8)
            self.set_text_color(90, 90, 90)
            self.cell(0, 4, nome_orgao(), align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_font("DejaVu", "B", 8)
            self.cell(0, 5, self.titulo, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(0, 0, 0)
            self.ln(3)

        def footer(self):
            self.set_y(-10)
            self.set_font("DejaVu", "", 7)
            self.set_text_color(90, 90, 90)
            self.cell(0, 5, f"Página {self.page_no()} de {{nb}}", align="R")
            self.set_text_color(0, 0, 0)

    return AnexoTR, FontFace


def blocos(md):
    """Divide o markdown em blocos: ('titulo'|'secao'|'paragrafo'|'tabela', conteúdo).
    Diretriva <!--tabela larguras=..--> vira o campo larguras da tabela seguinte."""
    linhas = md.splitlines()
    out, i, larguras = [], 0, None
    while i < len(linhas):
        l = linhas[i].strip()
        if not l:
            i += 1
            continue
        if l.startswith("<!--"):
            m = re.match(r"<!--\s*tabela\s+larguras=([\d,\s]+)\s*-->", l)
            if m:
                larguras = tuple(int(x) for x in m.group(1).split(","))
            else:
                # comentário multilinha: pular até fechar
                while i < len(linhas) and "-->" not in linhas[i]:
                    i += 1
            i += 1
            continue
        if l.startswith("# "):
            out.append(("titulo", l[2:].strip(), None)); i += 1; continue
        if l.startswith("## "):
            out.append(("secao", l[3:].strip(), None)); i += 1; continue
        if l.startswith("|"):
            tbl = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                tbl.append(linhas[i].strip()); i += 1
            out.append(("tabela", tbl, larguras)); larguras = None
            continue
        # parágrafo: juntar linhas até linha em branco ou próximo bloco
        para = [l]
        while (i + 1 < len(linhas) and linhas[i + 1].strip()
               and not linhas[i + 1].strip().startswith(("#", "|", "<!--"))):
            i += 1
            para.append(linhas[i].strip())
        out.append(("paragrafo", " ".join(para), None))
        i += 1
    return out


def texto_celula(t):
    """Sem itálico no ambiente (não há DejaVu itálica): '*' isolado sai em redondo."""
    return re.sub(r"(?<!\*)\*(?!\*)", "", t.strip())


def gera(md_path, pdf_path):
    AnexoTR, FontFace = classe_pdf()
    pdf = AnexoTR(os.path.basename(md_path).rsplit(".md", 1)[0])
    pdf.set_title(pdf.titulo)
    pdf.add_page()
    for tipo, conteudo, larguras in blocos(open(os.path.join(RAIZ, md_path), encoding="utf-8").read()):
        if tipo == "titulo":
            pdf.set_font("DejaVu", "B", 13)
            pdf.cell(0, 8, conteudo, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif tipo == "secao":
            pdf.ln(1)
            pdf.set_font("DejaVu", "B", 11)
            pdf.cell(0, 6, conteudo, align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif tipo == "paragrafo":
            pdf.set_font("DejaVu", "", 10)
            # alinha à direita o parágrafo final de local/data (convenção do formulário)
            if re.match(r"^<Local>, <dia>", conteudo):
                pdf.multi_cell(0, 5, conteudo, markdown=True, align="R")
            else:
                pdf.multi_cell(0, 5, conteudo, markdown=True, align="J")
            pdf.ln(1.5)
        else:  # tabela
            linhas = [l for l in conteudo if not re.match(r"^\|[\s\-:|]+\|$", l)]
            dados = [[texto_celula(c) for c in l.strip("|").split("|")] for l in linhas]
            ncol = max(len(r) for r in dados)
            dados = [r + [""] * (ncol - len(r)) for r in dados]
            if larguras and len(larguras) != ncol:
                sys.exit(f"{md_path}: diretriva com {len(larguras)} larguras, "
                         f"mas a tabela tem {ncol} colunas")
            pdf.set_font("DejaVu", "", 9)
            cab = FontFace(emphasis="BOLD", fill_color=(220, 220, 220))
            with pdf.table(col_widths=larguras, text_align="LEFT", line_height=5.5,
                           padding=1.2, headings_style=cab, repeat_headings=1,
                           markdown=True, v_align="MIDDLE") as tabela:
                for r in dados:
                    row = tabela.row()
                    for c in r:
                        row.cell(c)
            pdf.ln(2)
    os.makedirs(os.path.dirname(os.path.join(RAIZ, pdf_path)), exist_ok=True)
    pdf.output(os.path.join(RAIZ, pdf_path))
    print(f">> {pdf_path} ({pdf.page_no()} página(s))")


def main():
    args = sys.argv[1:]
    alvo = []
    if not args:
        alvo = anexos()
        if not alvo:
            print("!! nenhum tr/ANEXO *.md encontrado; nada a gerar", file=sys.stderr)
    else:
        for a in args:
            if a.endswith(".md") and os.path.exists(os.path.join(RAIZ, a)):
                alvo.append((a, saida_pdf(a)))
            else:
                sys.exit(f"argumento não reconhecido: {a}")
    for md, pdf in alvo:
        gera(md, pdf)


if __name__ == "__main__":
    main()
