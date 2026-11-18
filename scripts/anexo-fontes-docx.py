#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anexo I do ETP (Registro de fontes técnicas consultadas) no build/ETP.docx.

O PDF juntado aos autos continua sendo gerado por scripts/gerar-anexo-fontes.py. Este script
leva a mesma tabela ao docx de trabalho da equipe, em seção A4 paisagem no fim do documento.
Fonte única dos dados: etp/fontes.yaml. Decisão: decisoes/2026-10-09-anexo-i-no-docx-do-etp.md.

Uso (chamado por scripts/build.sh):
  python3 scripts/anexo-fontes-docx.py md <saida.md>       # markdown do anexo, com o marcador de seção
  python3 scripts/anexo-fontes-docx.py paisagem <ETP.docx>  # seção do anexo em paisagem; cabeçalho repetido

Requer só PyYAML (Python do sistema).
"""
import os, re, sys, zipfile, shutil, tempfile

import yaml

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS = os.path.join(RAIZ, "etp/fontes.yaml")

# Parágrafo-marcador: o pandoc o escreve como texto comum; o passo "paisagem" o troca pela
# quebra de seção que encerra o corpo do ETP em retrato.
MARCADOR = "ANEXO-I-QUEBRA-DE-SECAO-PAISAGEM"

# Página A4 (twips) e margens de 2,5 cm; colunas na proporção do PDF (13/124/106/24 mm).
A4_CURTO, A4_LONGO, MARGEM = 11906, 16838, 1418
PROPORCAO = (13, 124, 106, 24)
SECAO = ('<w:sectPr><w:pgSz w:w="{w}" w:h="{h}"{orient} />'
         '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1418" '
         'w:header="709" w:footer="709" w:gutter="0" /></w:sectPr>')

# Mesmo texto de abertura do PDF (scripts/gerar-anexo-fontes.py).
INTRO = ("Registro de todo documento externo em que o Estudo Técnico Preliminar apoia "
         "afirmação de capacidade técnica, de licenciamento ou de preço. As seções do Estudo "
         "citam o identificador entre colchetes — por exemplo, [F-10] — no ponto da afirmação "
         "que ele sustenta. A coluna \"Consulta\" registra a data em que o conteúdo citado foi "
         "verificado no endereço indicado, e não a data de publicação do documento. Regras de "
         "uso no item \"Registro de fontes técnicas consultadas\" do Estudo.")


def carrega():
    """Mesmas validações de scripts/gerar-anexo-fontes.py."""
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
    return fontes


def celula(txt):
    return str(txt).replace("|", "\\|").replace("\n", " ").strip()


def gera_md(saida):
    fontes = carrega()
    # A largura das colunas é fixada no passo "paisagem" (o leitor gfm a ignora).
    linhas = [
        MARCADOR, "",
        "# ANEXO I DO ESTUDO TÉCNICO PRELIMINAR — Registro de fontes técnicas consultadas", "",
        INTRO, "",
        "| ID | Documento | Endereço | Consulta |",
        "|---|---|---|---|",
    ]
    for f in fontes:
        linhas.append(f"| **{f['id']}** | {celula(f['documento'])} | <{celula(f['endereco'])}> | "
                      f"{celula(f['consulta'])} |")
    open(saida, "w", encoding="utf-8").write("\n".join(linhas) + "\n")


def paisagem(docx):
    tmp = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(docx) as z:
            z.extractall(tmp)
            nomes = z.namelist()
        caminho = os.path.join(tmp, "word", "document.xml")
        xml = open(caminho, encoding="utf-8").read()

        # O pandoc deste build não grava sectPr (o documento de referência não define página):
        # as duas seções ficam explícitas em A4, com margens de 2,5 cm.
        # O sectPr do fim do corpo (vazio, "<w:sectPr />", ou vindo do documento de referência)
        # sai e é substituído pelo da seção paisagem.
        corpo = list(re.finditer(r"<w:sectPr\s*/>|<w:sectPr\b.*?</w:sectPr>", xml, re.S))
        if corpo and xml.find("</w:body>", corpo[-1].end()) - corpo[-1].end() < 5:
            xml = xml[:corpo[-1].start()] + xml[corpo[-1].end():]
        retrato = SECAO.format(w=A4_CURTO, h=A4_LONGO, orient="")
        paisagem_xml = SECAO.format(w=A4_LONGO, h=A4_CURTO, orient=' w:orient="landscape"')

        # 1) o parágrafo-marcador vira a quebra que encerra o corpo do ETP em retrato
        pm = re.search(r"<w:p\b(?:(?!<w:p\b).)*?" + MARCADOR + r".*?</w:p>", xml, re.S)
        if not pm:
            sys.exit("anexo-fontes-docx: marcador do Anexo I não encontrado no docx")
        xml = xml[:pm.start()] + f"<w:p><w:pPr>{retrato}</w:pPr></w:p>" + xml[pm.end():]

        # 2) a última seção (o anexo) em paisagem
        fim_corpo = xml.rfind("</w:body>")
        xml = xml[:fim_corpo] + paisagem_xml + xml[fim_corpo:]

        # 3) tabela do anexo (a última do documento): largura útil da página, colunas
        #    proporcionais às do PDF e cabeçalho repetido em cada página
        ini = xml.rfind("<w:tbl>")
        fim = xml.find("</w:tbl>", ini) + len("</w:tbl>")
        tbl = xml[ini:fim]
        util = A4_LONGO - 2 * MARGEM
        larg = [round(util * p / sum(PROPORCAO)) for p in PROPORCAO]
        tbl = re.sub(r'<w:tblW [^>]*/>', f'<w:tblW w:type="dxa" w:w="{util}" /><w:tblLayout w:type="fixed" />', tbl, 1)
        tbl = re.sub(r"<w:tblGrid>.*?</w:tblGrid>",
                     "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}" />' for w in larg) + "</w:tblGrid>", tbl, 1, re.S)
        cont = iter(range(10 ** 6))
        tbl = re.sub(r"<w:tcPr />",
                     lambda _: f'<w:tcPr><w:tcW w:type="dxa" w:w="{larg[next(cont) % len(larg)]}" /></w:tcPr>', tbl)
        tr = tbl.find("<w:tr>")
        if tbl.find("<w:tblHeader", tr, tbl.find("</w:tr>", tr)) < 0:
            tbl = tbl[:tr] + "<w:tr><w:trPr><w:tblHeader /></w:trPr>" + tbl[tr + len("<w:tr>"):]
        xml = xml[:ini] + tbl + xml[fim:]

        open(caminho, "w", encoding="utf-8").write(xml)
        novo = docx + ".tmp"
        with zipfile.ZipFile(novo, "w", zipfile.ZIP_DEFLATED) as z:
            for n in nomes:  # mantém a ordem original ([Content_Types].xml primeiro)
                z.write(os.path.join(tmp, n), n)
        os.replace(novo, docx)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("md", "paisagem"):
        sys.exit(__doc__)
    (gera_md if sys.argv[1] == "md" else paisagem)(sys.argv[2])
