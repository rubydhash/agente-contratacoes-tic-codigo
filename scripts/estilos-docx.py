#!/usr/bin/env python3
"""Injeta em um reference.docx os estilos usados para destacar, em azul, os trechos
alterados em relação ao modelo AGU.

Cria dois estilos:
  - TrechoAlterado  (caractere)  → fragmento alterado dentro de um item do modelo
  - ItemAlterado    (parágrafo)  → item inteiro incluído ou substancialmente alterado

Uso: scripts/estilos-docx.py <entrada.docx> <saida.docx>

A entrada é o reference.docx padrão do pandoc (obtido com
`pandoc --print-default-data-file reference.docx`) ou, se existir,
templates/agu-referencia.docx — de modo que a formatação institucional seja
preservada e apenas os dois estilos sejam acrescentados.
"""
import re, shutil, sys, zipfile

AZUL = "0000CC"

CHAR_STYLE = (
    '<w:style w:type="character" w:customStyle="1" w:styleId="TrechoAlterado">'
    '<w:name w:val="TrechoAlterado"/><w:basedOn w:val="DefaultParagraphFont"/>'
    '<w:rPr><w:color w:val="%s"/></w:rPr></w:style>' % AZUL
)
PARA_STYLE = (
    '<w:style w:type="paragraph" w:customStyle="1" w:styleId="ItemAlterado">'
    '<w:name w:val="ItemAlterado"/><w:basedOn w:val="BodyText"/>'
    '<w:qFormat/><w:rPr><w:color w:val="%s"/></w:rPr></w:style>' % AZUL
)

def main(src, dst):
    shutil.copyfile(src, dst)
    with zipfile.ZipFile(src) as z:
        nomes = z.namelist()
        conteudo = {n: z.read(n) for n in nomes}

    styles = conteudo["word/styles.xml"].decode("utf-8")
    if "TrechoAlterado" not in styles:
        styles = styles.replace("</w:styles>", CHAR_STYLE + PARA_STYLE + "</w:styles>")
    conteudo["word/styles.xml"] = styles.encode("utf-8")

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n in nomes:
            z.writestr(n, conteudo[n])
    print(f">> estilos de destaque injetados em {dst}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: estilos-docx.py <entrada.docx> <saida.docx>")
    main(sys.argv[1], sys.argv[2])
