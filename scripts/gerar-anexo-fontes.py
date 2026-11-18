#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o Anexo I do ETP — Registro de fontes técnicas consultadas — em PDF, A4 paisagem.

A tabela de fontes não cabe bem no editor de texto do Compras.gov.br: por isso sai do corpo
de etp/20-registro-fontes.md e vai para este anexo, juntado aos autos em separado.

Fonte dos dados: etp/fontes.yaml (não edite o PDF; edite o YAML e regenere).
Saída:           etp/anexo-i-registro-de-fontes.pdf

Uso:
  .venv/bin/python scripts/gerar-anexo-fontes.py

Requer fpdf2 e PyYAML. Instalação, uma única vez, fora do Python do sistema:
  python3 -m venv .venv && .venv/bin/pip install fpdf2 pyyaml
"""
import os, re, sys

import yaml
from fpdf import FPDF
from fpdf.fonts import FontFace

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "etp/fontes.yaml")
META = os.path.join(RAIZ, "etp/00-metadados.yaml")
SAIDA = os.path.join(RAIZ, "etp/anexo-i-registro-de-fontes.pdf")

FONTES_TTF = "/usr/share/fonts/truetype/dejavu"
TITULO = "ANEXO I DO ESTUDO TÉCNICO PRELIMINAR"
SUBTITULO = "Registro de fontes técnicas consultadas"


def texto_celula(md):
    """Adapta o markdown do YAML ao do fpdf2: mantém **negrito**; o *itálico* sai em redondo,
    porque não há fonte itálica DejaVu no ambiente (no fpdf2, "*" isolado seria literal)."""
    return re.sub(r"(?<!\*)\*(?!\*)", "", md)


def carrega():
    fontes = yaml.safe_load(open(DADOS, encoding="utf-8"))["fontes"]
    ids = [f["id"] for f in fontes]
    if len(ids) != len(set(ids)):
        sys.exit("etp/fontes.yaml: identificador repetido")
    for f in fontes:
        for campo in ("id", "documento", "endereco", "consulta"):
            if not str(f.get(campo, "")).strip():
                sys.exit(f"etp/fontes.yaml: {f.get('id', '?')} sem o campo '{campo}'")
        if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", str(f["consulta"])):
            sys.exit(f"etp/fontes.yaml: {f['id']} com data de consulta fora do formato DD/MM/AAAA")
    meta = yaml.safe_load(open(META, encoding="utf-8"))
    return fontes, meta


class Anexo(FPDF):
    def __init__(self, processo, objeto):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.processo, self.objeto = processo, objeto
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=15)
        # Não há DejaVu itálica no ambiente: o itálico do markdown sai em redondo.
        self.add_font("DejaVu", "", f"{FONTES_TTF}/DejaVuSans.ttf")
        self.add_font("DejaVu", "B", f"{FONTES_TTF}/DejaVuSans-Bold.ttf")
        self.add_font("DejaVu", "I", f"{FONTES_TTF}/DejaVuSans.ttf")
        self.add_font("DejaVu", "BI", f"{FONTES_TTF}/DejaVuSans-Bold.ttf")

    def header(self):
        self.set_font("DejaVu", "B", 11)
        self.cell(0, 6, TITULO, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 10)
        self.cell(0, 5, SUBTITULO, align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 8)
        self.cell(0, 5, f"Processo nº {self.processo} — {self.objeto}", align="C",
                  new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font("DejaVu", "", 7)
        self.cell(0, 5, f"Página {self.page_no()} de {{nb}}", align="R")


def main():
    fontes, meta = carrega()
    pdf = Anexo(meta["processo"]["numero_sei"], meta["contratacao"]["objeto_curto"])
    pdf.set_title(f"{TITULO} — {SUBTITULO}")
    pdf.set_subject(f"Processo nº {meta['processo']['numero_sei']}")
    pdf.add_page()

    pdf.set_font("DejaVu", "", 8.5)
    pdf.multi_cell(0, 4.5,
                   "Registro de todo documento externo em que o Estudo Técnico Preliminar apoia "
                   "afirmação de capacidade técnica, de licenciamento ou de preço. As seções do Estudo "
                   "citam o identificador entre colchetes — por exemplo, [F-10] — no ponto da afirmação "
                   "que ele sustenta. A coluna \"Consulta\" registra a data em que o conteúdo citado foi "
                   "verificado no endereço indicado, e não a data de publicação do documento. Regras de "
                   "uso no item \"Registro de fontes técnicas consultadas\" do Estudo.",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("DejaVu", "", 8)
    cabecalho = FontFace(emphasis="BOLD", fill_color=(220, 220, 220))
    with pdf.table(col_widths=(13, 124, 106, 24), text_align=("CENTER", "LEFT", "LEFT", "CENTER"),
                   line_height=4, padding=1.2, headings_style=cabecalho, repeat_headings=1,
                   markdown=True, v_align="TOP") as tabela:
        cab = tabela.row()
        for t in ("ID", "Documento", "Endereço", "Consulta"):
            cab.cell(t)
        for f in fontes:
            r = tabela.row()
            r.cell(f"**{f['id']}**")
            r.cell(texto_celula(str(f["documento"])))
            # URL sem marcação markdown (sublinhados e asteriscos em endereços são literais)
            r.cell(str(f["endereco"]), link=str(f["endereco"]))
            r.cell(str(f["consulta"]))

    pdf.output(SAIDA)
    print(f">> {os.path.relpath(SAIDA, RAIZ)} ({len(fontes)} fontes, {pdf.page_no()} página(s))")


if __name__ == "__main__":
    main()
