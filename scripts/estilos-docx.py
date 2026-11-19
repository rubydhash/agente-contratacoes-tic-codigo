#!/usr/bin/env python3
"""Injeta em um reference.docx os estilos das marcas de afastamento do modelo AGU, conforme o
"Código de formatação visual sugerida" do Instrumento de Padronização AGU/MGI de TIC
(ver scripts/tr_marcas.py e scripts/marcas.lua).

Estilos de caractere (trecho dentro de um item do modelo):
  - TrechoIncluido     vermelho   inclusão
  - TrechoAjustado     verde      ajuste (após o texto original, tachado)
  - TrechoPreenchido   azul       preenchimento de lacuna do modelo
  - TrechoJustificativa cinza     justificativa em trecho (usada na legenda)
  - TrechoAlterado     azul       legado (convenção anterior, uma cor só)

Estilos de parágrafo (bloco inteiro):
  - ItemIncluido       vermelho   item ou tabela incluídos
  - ItemPreenchido     azul       tabela do modelo preenchida
  - Justificativa      cinza      justificativa logo abaixo do item modificado
  - ItemAlterado       azul       legado

O tachado da supressão é o nativo do Word e não precisa de estilo.

Uso: scripts/estilos-docx.py <entrada.docx> <saida.docx>

A entrada é o reference.docx padrão do pandoc (obtido com
`pandoc --print-default-data-file reference.docx`) ou, se existir,
templates/agu-referencia.docx — de modo que a formatação institucional seja
preservada e apenas estes estilos sejam acrescentados.
"""
import shutil, sys, zipfile

# Cores: as mesmas de scripts/tr_marcas.py (CORES) e scripts/marcas.lua, sem o "#".
VERMELHO, VERDE, AZUL, CINZA, AZUL_LEGADO = "FF0000", "00B050", "0000FF", "808080", "0000CC"

CARACTERE = [
    ("TrechoIncluido", VERMELHO),
    ("TrechoAjustado", VERDE),
    ("TrechoPreenchido", AZUL),
    ("TrechoJustificativa", CINZA),
    ("TrechoAlterado", AZUL_LEGADO),
]
PARAGRAFO = [
    ("ItemIncluido", VERMELHO),
    ("ItemPreenchido", AZUL),
    ("Justificativa", CINZA),
    ("ItemAlterado", AZUL_LEGADO),
]


def estilo_caractere(nome, cor):
    return ('<w:style w:type="character" w:customStyle="1" w:styleId="%s">'
            '<w:name w:val="%s"/><w:basedOn w:val="DefaultParagraphFont"/>'
            '<w:rPr><w:color w:val="%s"/></w:rPr></w:style>' % (nome, nome, cor))


def estilo_paragrafo(nome, cor):
    return ('<w:style w:type="paragraph" w:customStyle="1" w:styleId="%s">'
            '<w:name w:val="%s"/><w:basedOn w:val="BodyText"/>'
            '<w:qFormat/><w:rPr><w:color w:val="%s"/></w:rPr></w:style>' % (nome, nome, cor))


def main(src, dst):
    shutil.copyfile(src, dst)
    with zipfile.ZipFile(src) as z:
        nomes = z.namelist()
        conteudo = {n: z.read(n) for n in nomes}

    styles = conteudo["word/styles.xml"].decode("utf-8")
    novos = "".join(estilo_caractere(n, c) for n, c in CARACTERE
                    if f'w:styleId="{n}"' not in styles)
    novos += "".join(estilo_paragrafo(n, c) for n, c in PARAGRAFO
                     if f'w:styleId="{n}"' not in styles)
    styles = styles.replace("</w:styles>", novos + "</w:styles>")
    conteudo["word/styles.xml"] = styles.encode("utf-8")

    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n in nomes:
            z.writestr(n, conteudo[n])
    print(f">> estilos das marcas do IPP injetados em {dst}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("uso: estilos-docx.py <entrada.docx> <saida.docx>")
    main(sys.argv[1], sys.argv[2])
