#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera despachos/justificativa-modelo-agu.html — Justificativa Complementar das inclusões,
modificações e exclusões na utilização da minuta padrão da AGU.

O arquivo de saída é HTML: o CORPO do despacho é colado no editor do SEI (modo Código-Fonte),
preservando a formatação. O trecho a copiar fica entre os comentários "INÍCIO/FIM DO TRECHO A
COPIAR NO SEI"; o resto do arquivo serve só para visualização. O cabeçalho e as folhas de estilo
são reaproveitados, sem alteração, de templates/sei/documento-base.html.

Uso: scripts/gerar-despacho.py
"""
import os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(RAIZ, "templates/sei/documento-base.html")
OUT = os.path.join(RAIZ, "despachos/justificativa-modelo-agu.html")

# ----------------------------------------------------------------- montagem HTML
def cell_item(txt):
    return ('\t\t\t<td data-celllook="0" role="rowheader" style="width: 131px;">\n'
            '\t\t\t<div>\n\t\t\t<div>\n'
            f'\t\t\t<p class="Tabela_Texto_Centralizado">{txt}</p>\n'
            '\t\t\t</div>\n\t\t\t</div>\n\t\t\t</td>\n')

def cell_just(paras):
    inner = "\n".join('\t\t\t<div>\n'
                      f'\t\t\t<p class="Texto_Justificado">{p}</p>\n'
                      '\t\t\t</div>' for p in paras)
    return ('\t\t\t<td data-celllook="0" style="width: 643px;">\n'
            f'\t\t\t<div>\n{inner}\n\t\t\t</div>\n\t\t\t</td>\n')

ROWS = []
def ordem_item(item):
    """Chave de ordenação: linhas gerais primeiro; depois, pela numeração do modelo."""
    m = re.match(r"(\d+(?:\.\d+)*)", item)
    if not m:
        return (0, [])
    return (1, [int(x) for x in m.group(1).split(".")])


def linha(item, tipo, paras):
    body = list(paras)
    if tipo:
        body[0] = f"<strong>{tipo}:</strong><br>\n\t\t\t{body[0]}"
    ROWS.append((ordem_item(item), len(ROWS),
                 "\t\t<tr>\n" + cell_item(item) + cell_just(body) + "\t\t</tr>\n"))

A = lambda i, *p: linha(i, "Altera&ccedil;&atilde;o", p)
I = lambda i, *p: linha(i, "Inclus&atilde;o", p)
E = lambda i, *p: linha(i, "Exclus&atilde;o", p)
N = lambda i, *p: linha(i, None, p)

def header_row(txt):
    return ('\t\t<tr>\n\t\t\t<td colspan="2" data-celllook="0" role="rowheader" '
            'style="width: 778px;">\n\t\t\t<div>\n\t\t\t<div>\n'
            f'\t\t\t<p class="Tabela_Texto_Centralizado"><strong>{txt}</strong></p>\n'
            '\t\t\t</div>\n\t\t\t</div>\n\t\t\t</td>\n\t\t</tr>\n')

def col_header_row():
    return ('\t\t<tr>\n'
            '\t\t\t<td class="dark-mode-color-black" data-celllook="0" role="rowheader" '
            'style="width: 131px; background-color: rgb(187, 187, 187);">\n\t\t\t<div>\n\t\t\t<div>\n'
            '\t\t\t<p class="Tabela_Texto_Centralizado"><strong>Item conforme numera&ccedil;&atilde;o '
            'do modelo</strong></p>\n\t\t\t</div>\n\t\t\t</div>\n\t\t\t</td>\n'
            '\t\t\t<td class="dark-mode-color-black" data-celllook="0" '
            'style="width: 643px; background-color: rgb(187, 187, 187);">\n\t\t\t<div>\n\t\t\t<div>\n'
            '\t\t\t<p class="Tabela_Texto_Centralizado"><strong>Inclus&otilde;es, modifica&ccedil;&otilde;es '
            'e exclus&otilde;es</strong></p>\n\t\t\t</div>\n\t\t\t</div>\n\t\t\t</td>\n\t\t</tr>\n')

SUP = ("Item mantido na posi&ccedil;&atilde;o original do Termo de Refer&ecirc;ncia, com a "
       "reda&ccedil;&atilde;o &ldquo;Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).&rdquo;, "
       "de modo a preservar a numera&ccedil;&atilde;o do modelo. ")


# ============================================================ CABEÇALHO DO DESPACHO
# Preencher com os dados do processo. Tudo aqui sai no corpo colado no SEI.
UNIDADE_SIGLA = "&lt;SIGLA DA UNIDADE&gt;"
UNIDADE_NOME = "&lt;NOME DA UNIDADE&gt;"
PROCESSO_SEI = "&lt;00000.000000/0000-00&gt;"
NUMERO_DESPACHO_SEI = "&lt;n&ordm; SEI do despacho&gt;"
INTERESSADO = "&lt;&aacute;rea requisitante&gt;"
TR_NUMERO = "&lt;n&ordm;/ano do TR no Compras.gov.br&gt;"
OBJETO = "&lt;objeto da contrata&ccedil;&atilde;o, como em etp/00-metadados.yaml&gt;"
# Artefatos que instruem o TR, na forma "o Documento de Formaliza&ccedil;&atilde;o da Demanda n&ordm; ..., o ..."
ARTEFATOS = "&lt;DFD n&ordm; .../..., ETP n&ordm; .../... e Mapa de Gerenciamento de Riscos n&ordm; .../...&gt;"
SIGNATARIO_NOME = "NOME"
SIGNATARIO_CARGO = "CARGO"

# ============================================================ LINHAS DO DESPACHO
# Uma chamada por afastamento do modelo, com o número do item como no TR:
#   A("4.14", "O que mudou.", "Razão.")                 alteração
#   I("4.1.6 a 4.1.14", "O que foi incluído.", ...)     inclusão (item novo, sem correspondente)
#   E("2.3 e 2.4", SUP + "Por que não se aplica.")      exclusão (item mantido como "Suprimido")
#   N("Geral — ...", "Texto.")                          linha informativa, sem afastamento
# A ordem no script não importa: as linhas saem ordenadas pela numeração.
# scripts/conferir-modelo-agu.py confere nos dois sentidos: todo afastamento do TR precisa de
# linha aqui, e toda linha A/I/E precisa apontar um afastamento efetivo.

# ------------------------------------------------------------ GERAL
N("Geral &mdash; vers&atilde;o do modelo",
  "<strong>Modelo adotado:</strong> Modelo de Termo de Refer&ecirc;ncia para Contrata&ccedil;&atilde;o de "
  "Servi&ccedil;os de Tecnologia da Informa&ccedil;&atilde;o e Comunica&ccedil;&atilde;o &mdash; Lei n&ordm; 14.133, de "
  "2021, da C&acirc;mara Nacional de Modelos de Licita&ccedil;&otilde;es e Contratos da Consultoria-Geral da "
  "Uni&atilde;o, aprovado pela Secretaria de Governo Digital, <strong>atualiza&ccedil;&atilde;o abr/2026</strong>.")

N("Geral &mdash; numera&ccedil;&atilde;o",
  "A numera&ccedil;&atilde;o deste Termo de Refer&ecirc;ncia segue <strong>item a item</strong> a do modelo, tal como "
  "exibida pela numera&ccedil;&atilde;o autom&aacute;tica do documento-modelo. Os itens do modelo que n&atilde;o se "
  "aplicam <strong>n&atilde;o foram apagados</strong>: permanecem na posi&ccedil;&atilde;o original, com a "
  "reda&ccedil;&atilde;o &ldquo;<em>Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).</em>&rdquo;. "
  "Assim, a confer&ecirc;ncia entre esta justificativa e o artefato &eacute; direta, sem tabela de tradu&ccedil;&atilde;o "
  "intermedi&aacute;ria.",
  "O texto do modelo foi mantido <strong>literalmente</strong> fora dos trechos alterados, inclusive quanto &agrave; "
  "grafia &ldquo;o Contratado&rdquo; e &ldquo;o Contratante&rdquo;. Todo trecho inclu&iacute;do ou alterado &mdash; "
  "inclusive o preenchimento de campos que o modelo deixa em aberto e a escolha entre alternativas &mdash; est&aacute; "
  "<strong>destacado na cor azul</strong> no Termo de Refer&ecirc;ncia.",
  "Itens sem correspondente no modelo foram acrescidos sem deslocar nenhum item do modelo: como "
  "<strong>subitens</strong> do item do modelo a que se referem, ou como itens novos numerados <strong>ap&oacute;s o "
  "&uacute;ltimo item do cap&iacute;tulo</strong>.")

N("Geral &mdash; estrutura de cap&iacute;tulos",
  "A estrutura de cap&iacute;tulos do modelo foi <strong>integralmente preservada</strong>, nos seus treze "
  "cap&iacute;tulos. O bloco &ldquo;San&ccedil;&otilde;es Administrativas e Procedimentos para reten&ccedil;&atilde;o ou "
  "glosa no pagamento&rdquo; constitui o <strong>cap&iacute;tulo 9</strong>, como no modelo; em consequ&ecirc;ncia, os "
  "cap&iacute;tulos de sele&ccedil;&atilde;o do fornecedor, estimativa de valor, adequa&ccedil;&atilde;o or&ccedil;ament&aacute;ria "
  "e disposi&ccedil;&otilde;es finais s&atilde;o os de n&uacute;meros 10 a 13.")

# ------------------------------------------------------------ AFASTAMENTOS
# (acrescentar aqui, à medida que o TR for redigido)


# ----------------------------------------------------------------- escrita
def main():
    src = open(REF, encoding="cp1252", errors="replace").read()
    marker = '<p class="Texto_Centralizado">&nbsp;</p>'
    head = src[:src.index(marker) + len(marker)]
    head = head.replace("<title>Documento SEI</title>",
                        f"<title>Despacho - Justificativa Complementar - TR {TR_NUMERO}</title>")

    tabela = ('<div>\n<table aria-rowcount="%d" border="3" data-tablelook="1184" '
              'data-tablestyle="MsoTableGrid" dir="ltr" '
              'style="border-collapse:collapse;margin-left:auto;margin-right:auto;width:792px;">\n'
              '\t<tbody>\n' % (len(ROWS) + 2))
    tabela += header_row("Termo de Refer&ecirc;ncia &mdash; inclus&otilde;es, modifica&ccedil;&otilde;es e "
                         "exclus&otilde;es identificadas na cor azul")
    tabela += col_header_row()
    tabela += "".join(r for _, _, r in sorted(ROWS))
    tabela += "\t</tbody>\n</table>\n</div>\n"

    corpo = f'''
<!-- ================================================================================
     INÍCIO DO TRECHO A COPIAR NO SEI
     Copie daqui até o comentário "FIM DO TRECHO A COPIAR NO SEI" e cole no
     editor do SEI em modo Código-Fonte. Tudo o que está acima deste comentário
     (html, head, estilos) existe só para visualizar o arquivo no navegador.
     ================================================================================ -->
<p class="Texto_Centralizado"><strong>DESPACHO</strong></p>

<p><br />
<strong>{UNIDADE_NOME} -&nbsp;</strong><b>{UNIDADE_SIGLA}</b></p>

<p><strong>Processo n&ordm; {PROCESSO_SEI}</strong><br />
<br />
<span style="font-size:12pt"><span style="font-family:&quot;Times New Roman&quot;,serif"><strong>Despacho&nbsp;{UNIDADE_SIGLA}&nbsp;SEI n&ordm; {NUMERO_DESPACHO_SEI}</strong></span></span></p>

<p><span style="font-size:12pt;"><span style="font-family:&quot;Times New Roman&quot;,serif;"><strong>Origem:&nbsp;{UNIDADE_SIGLA}</strong></span></span></p>

<p><strong>Interessado:&nbsp;{INTERESSADO}</strong></p>

<p><strong>Assunto:&nbsp;</strong>Justificativa complementar das inclus&otilde;es, modifica&ccedil;&otilde;es e exclus&otilde;es na utiliza&ccedil;&atilde;o de minuta padr&atilde;o &mdash; Termo de Refer&ecirc;ncia n&ordm; {TR_NUMERO}, da contrata&ccedil;&atilde;o de {OBJETO}.</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha">&nbsp;&nbsp;<br />
&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; Prezado(a)&nbsp;Sr.(a),</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha">O Termo de Refer&ecirc;ncia n&ordm; {TR_NUMERO}, instru&iacute;do com {ARTEFATOS}, foi elaborado a partir do <strong>Modelo de Termo de Refer&ecirc;ncia para Contrata&ccedil;&atilde;o de Servi&ccedil;os de Tecnologia da Informa&ccedil;&atilde;o e Comunica&ccedil;&atilde;o &mdash; Lei n&ordm; 14.133, de 2021</strong>, da C&acirc;mara Nacional de Modelos de Licita&ccedil;&otilde;es e Contratos da Consultoria-Geral da Uni&atilde;o, aprovado pela Secretaria de Governo Digital, na sua <strong>atualiza&ccedil;&atilde;o de abril de 2026</strong>. Informamos abaixo as inclus&otilde;es, modifica&ccedil;&otilde;es e exclus&otilde;es efetuadas em rela&ccedil;&atilde;o &agrave;quele modelo.</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha">A numera&ccedil;&atilde;o do Termo de Refer&ecirc;ncia segue <strong>item a item</strong> a do modelo. Os itens do modelo que n&atilde;o se aplicam permanecem na posi&ccedil;&atilde;o original, com a reda&ccedil;&atilde;o &ldquo;<em>Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).</em>&rdquo;, de modo que a confer&ecirc;ncia entre esta justificativa e o artefato seja direta. Os trechos inclu&iacute;dos ou alterados est&atilde;o <strong>destacados na cor azul</strong> no Termo de Refer&ecirc;ncia.</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples">&nbsp;</p>

{tabela}
<p class="Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples">&nbsp;</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha">Atenciosamente,</p>

<p class="Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples">&nbsp;</p>

<p class="Texto_Centralizado"><strong>{SIGNATARIO_NOME}</strong></p>

<p class="Texto_Centralizado">{SIGNATARIO_CARGO}</p>
<!-- ================================================================================
     FIM DO TRECHO A COPIAR NO SEI
     ================================================================================ -->
</body></html>
'''
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="cp1252", errors="xmlcharrefreplace") as fh:
        fh.write(head + corpo)
    print(f">> {os.path.relpath(OUT, RAIZ)} ({len(ROWS)} linhas de justificativa)")

if __name__ == "__main__":
    main()
