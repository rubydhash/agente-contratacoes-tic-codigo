#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera a lista de verificação da AGU como documento do SEI (HTML), a partir do YAML preenchido.

Uso:
    python3 scripts/gerar-lista-verificacao-sei.py adesao-arp   # despachos/lista-verificacao-adesao-arp.html

Entradas:
- listas-verificacao/<nome>.yaml: respostas, local nos autos e providência (mesmo YAML de
  scripts/gerar-listas-verificacao.py). Chaves usadas aqui, além das de lá:
    modelo_md   — cópia em markdown do modelo da AGU (templates/agu-lista-verificacao-*.md), de onde
                  saem a pergunta completa, as alíneas e a nota de cada item;
    titulo      — título da lista (ex.: "(Adesão à ata de registro de preços – Lei nº 14.133)");
    rodape      — linhas do rodapé do modelo da CNMLC;
    signatario  — {nome, cargo, ato}: quem assina no SEI.
- templates/sei/documento-base.html: cabeçalho e folhas de estilo do SEI, reaproveitados sem
  alteração (como em scripts/gerar-despacho.py).

Saída: despachos/lista-verificacao-<nome>.html. O trecho a colar no editor do SEI (modo
Código-Fonte) fica entre os comentários "INÍCIO/FIM DO TRECHO A COPIAR NO SEI".

O script confere o início de cada pergunta do YAML contra o modelo e falha se divergir, se faltar
item ou se sobrar item. ADR: decisoes/2026-11-12-lista-verificacao-em-despacho-sei.md.
"""
import html
import re
import sys
import os
import unicodedata
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)


import yaml

RAIZ = Path(__file__).resolve().parent.parent
REF = RAIZ / "templates/sei/documento-base.html"
RESPOSTAS = {"sim": "Sim.", "nao": "Não.", "nao_se_aplica": "Não se aplica."}


def normaliza(s):
    s = unicodedata.normalize("NFKC", html.unescape(re.sub(r"<[^>]+>", " ", s)))
    return re.sub(r"\s+", " ", s).strip().lower()


def limpa(fragmento):
    """Mantém só <em>, <u>, <strong> e <a> do HTML do pandoc; tira notas e backlinks."""
    f = re.sub(r'<a href="#fn\d+"[^>]*>.*?</a>', "", fragmento, flags=re.S)
    f = re.sub(r'<a href="#fnref\d+"[^>]*>.*?</a>', "", f, flags=re.S)
    f = re.sub(r"</?(?!em\b|u\b|strong\b|a\b)[a-z]+[^>]*>", "", f)
    return re.sub(r"\s+", " ", f).strip()


def le_modelo(caminho):
    """Devolve (itens, introducao): itens = {id: {pergunta, alineas, notas}}."""
    md = caminho.read_text(encoding="utf-8")
    notas = {n: limpa(t).lstrip(". ") for n, t in
             re.findall(r'<li id="fn(\d+)"><p>(.*?)</p></li>', md, flags=re.S)}
    intro = re.search(r"^\[\^1\]: (.*?)(?=\n\S|\Z)", md, flags=re.S | re.M)
    introducao = [html.escape(re.sub(r"<([^<>\s]+)>", r"\1", re.sub(r"\s+", " ", p).strip()))
                  for p in re.split(r"\n\s*\n", intro.group(1))] if intro else []
    itens = {}
    for t, tabela in enumerate(re.findall(r"<table>(.*?)</table>", md, flags=re.S), start=1):
        linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", tabela, flags=re.S)
        n = 0
        for linha in linhas:
            celulas = re.findall(r"<td>(.*?)</td>", linha, flags=re.S)
            if not celulas or "<li>" not in celulas[0]:
                continue                       # cabeçalho da tabela
            n += 1
            c0 = celulas[0]
            perg = re.search(r"<li><p>(.*?)</p></li>", c0, flags=re.S).group(1)
            alineas = re.findall(r"<p>(.*?)</p>", c0.split("</ol>", 1)[1] if "</ol>" in c0 else "",
                                 flags=re.S)
            refs = re.findall(r'href="#fn(\d+)"', c0)
            itens[f"{t}.{n}"] = {
                "pergunta": limpa(perg),
                "alineas": [limpa(a) for a in alineas],
                "notas": [notas[r] for r in refs if r in notas],
            }
    return itens, introducao


def p(classe, conteudo):
    return f'<p class="{classe}">{conteudo}</p>\n'


def celula(conteudo, largura, alinhamento="Tabela_Texto_Alinhado_Esquerda", fundo=False):
    estilo = f"width: {largura}px;" + (" background-color: rgb(187, 187, 187);" if fundo else "")
    paras = conteudo if isinstance(conteudo, list) else [conteudo]
    paras = [x if isinstance(x, tuple) else (alinhamento, x) for x in paras if x is not None]
    corpo = "".join(f'\t\t\t<p class="{c}">{x}</p>\n' for c, x in paras)
    return f'\t\t\t<td style="{estilo}">\n{corpo}\t\t\t</td>\n'


LARGURAS = (390, 90, 130, 170)


def gerar(nome):
    caminho = RAIZ / "listas-verificacao" / f"{nome}.yaml"
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    modelo, introducao = le_modelo(RAIZ / dados["modelo_md"])
    itens = {str(it["id"]): it for it in dados["itens"]}

    faltam = sorted(set(modelo) - set(itens))
    sobram = sorted(set(itens) - set(modelo))
    if faltam or sobram:
        raise SystemExit(f"{caminho.name}: itens do modelo sem resposta {faltam}; itens sem modelo {sobram}")
    for i, it in itens.items():
        if not normaliza(modelo[i]["pergunta"]).startswith(normaliza(it["pergunta"])):
            raise SystemExit(f"{caminho.name} {i}: pergunta diverge do modelo\n  yaml:   {it['pergunta']}\n"
                             f"  modelo: {modelo[i]['pergunta']}")
        if it.get("resposta") not in RESPOSTAS:
            raise SystemExit(f"{caminho.name} {i}: resposta inválida {it.get('resposta')!r}")

    def chave(i):
        return [int(x) for x in i.split(".")]

    cab = ("\t\t<tr>\n"
           + celula("<strong>Aspectos gerais pertinentes à adesão à ata de registro de preços</strong>",
                    LARGURAS[0], "Tabela_Texto_Centralizado", True)
           + celula("<strong>Atende plenamente a exigência?</strong>", LARGURAS[1], "Tabela_Texto_Centralizado", True)
           + celula("<strong>Indicação do local do processo em que foi atendida a exigência (doc. / fls. / SEI)</strong>",
                    LARGURAS[2], "Tabela_Texto_Centralizado", True)
           + celula("<strong>OBS</strong>", LARGURAS[3], "Tabela_Texto_Centralizado", True)
           + "\t\t</tr>\n")
    linhas = []
    for i in sorted(itens, key=chave):
        it, m = itens[i], modelo[i]
        n = i.split(".")[-1]
        exig = ([f"<strong>{n} - {m['pergunta']}</strong>"] + m["alineas"]
                + [("Tabela_Texto_8", x) for x in m["notas"]])
        local = html.escape(it.get("local") or "") or "&nbsp;"
        obs = html.escape(it.get("providencia") or "") or "&nbsp;"
        linhas.append("\t\t<tr>\n"
                      + celula(exig, LARGURAS[0])
                      + celula(RESPOSTAS[it["resposta"]], LARGURAS[1], "Tabela_Texto_Centralizado")
                      + celula(local, LARGURAS[2])
                      + celula(obs, LARGURAS[3])
                      + "\t\t</tr>\n")
    tabela = ('<table border="1" cellpadding="1" cellspacing="1" '
              'style="border-collapse:collapse;margin-left:auto;margin-right:auto;width:792px;">\n'
              "\t<tbody>\n" + cab + "".join(linhas) + "\t</tbody>\n</table>\n")

    sig = dados.get("signatario") or {}
    corpo = ("\n<!-- ================================================================================\n"
             "     INÍCIO DO TRECHO A COPIAR NO SEI\n"
             "     Copie daqui até o comentário \"FIM DO TRECHO A COPIAR NO SEI\" e cole no\n"
             "     editor do SEI em modo Código-Fonte.\n"
             "     ================================================================================ -->\n"
             + p("Texto_Centralizado_Maiusculas_Negrito", "LISTA DE VERIFICAÇÃO")
             + p("Texto_Centralizado", html.escape(dados.get("titulo", "")))
             + p("Texto_Centralizado", f"Processo nº {html.escape(str(dados['processo']))}")
             + "".join(p("Texto_Justificado_Recuo_Primeira_Linha", x) for x in introducao)
             + p("Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples", "&nbsp;")
             + tabela
             + p("Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples", "&nbsp;")
             + p("Texto_Centralizado", "Assinatura Eletrônica")
             + p("Texto_Centralizado", f"<strong>{html.escape(sig.get('nome', 'NOME'))}</strong>")
             + p("Texto_Centralizado", html.escape(sig.get("cargo", "CARGO")))
             + p("Texto_Centralizado", html.escape(sig.get("ato", "ATO DE DESIGNAÇÃO")))
             + p("Texto_Justificado_Recuo_Primeira_Linha_Esp_Simples", "&nbsp;")
             + "".join(p("Texto_Alinhado_Esquerda_Espacamento_Simples", html.escape(x))
                       for x in dados.get("rodape", []))
             + "<!-- ================================================================================\n"
               "     FIM DO TRECHO A COPIAR NO SEI\n"
               "     ================================================================================ -->\n"
               "</body></html>\n")

    src = REF.read_text(encoding="cp1252", errors="replace")
    marcador = '<p class="Texto_Centralizado">&nbsp;</p>'
    head = src[:src.index(marcador) + len(marcador)]
    head = head.replace("<title>Documento SEI</title>",
                        f"<title>Lista de verificação - {html.escape(nome)}</title>")
    saida = RAIZ / "despachos" / f"lista-verificacao-{nome}.html"
    saida.parent.mkdir(exist_ok=True)
    with open(saida, "w", encoding="cp1252", errors="xmlcharrefreplace") as fh:
        fh.write(head + corpo)
    print(f">> {saida.relative_to(RAIZ)} ({len(linhas)} itens)")


def main():
    nomes = sys.argv[1:]
    if not nomes:
        raise SystemExit(__doc__)
    for nome in nomes:
        gerar(nome)


if __name__ == "__main__":
    main()
