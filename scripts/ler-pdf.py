#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê PDFs de normas, propostas e modelos sem depender do poppler (pdftotext/pdftoppm).

Usa o pypdfium2, do .venv (requirements.txt).

  python3 scripts/ler-pdf.py info   <arquivo.pdf>
  python3 scripts/ler-pdf.py texto  <arquivo.pdf> [-p 3-5] [-o saida.txt]
  python3 scripts/ler-pdf.py imagem <arquivo.pdf> <prefixo> [-p 3-5] [--dpi 150]

- texto: imprime o texto das páginas pedidas (todas, por omissão), com um marcador
  "=== página N ===" entre elas. Texto vazio indica PDF sem camada de texto: use `imagem`.
- imagem: grava <prefixo>-NNN.png por página, para leitura pela ferramenta de imagem do agente.
  Grave em $TMPDIR, não no repositório.

As páginas são numeradas a partir de 1, como no leitor de PDF.
"""
import argparse, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)

import pypdfium2 as pdfium      # noqa: E402


def paginas(spec, total):
    if not spec:
        return list(range(1, total + 1))
    out = []
    for parte in spec.split(","):
        a, _, b = parte.partition("-")
        ini, fim = int(a), int(b or a)
        out += range(max(ini, 1), min(fim, total) + 1)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("info"); i.add_argument("pdf")
    t = sub.add_parser("texto"); t.add_argument("pdf"); t.add_argument("-p", "--paginas")
    t.add_argument("-o", "--saida")
    m = sub.add_parser("imagem"); m.add_argument("pdf"); m.add_argument("prefixo")
    m.add_argument("-p", "--paginas"); m.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args()

    doc = pdfium.PdfDocument(a.pdf)
    total = len(doc)
    if a.cmd == "info":
        meta = doc.get_metadata_dict()
        print(f"páginas: {total}")
        for k, v in meta.items():
            if v:
                print(f"{k}: {v}")
        return
    sel = paginas(a.paginas, total)
    if a.cmd == "texto":
        partes = []
        for n in sel:
            tp = doc[n - 1].get_textpage()
            partes.append(f"=== página {n} ===\n{tp.get_text_range()}")
        txt = "\n".join(partes)
        if a.saida:
            open(a.saida, "w", encoding="utf-8").write(txt)
            print(f">> {a.saida} ({len(sel)} página(s), {len(txt)} caracteres)")
        else:
            sys.stdout.write(txt + "\n")
        return
    os.makedirs(os.path.dirname(os.path.abspath(a.prefixo)), exist_ok=True)
    for n in sel:
        img = doc[n - 1].render(scale=a.dpi / 72).to_pil()
        caminho = f"{a.prefixo}-{n:03d}.png"
        img.save(caminho)
        print(f">> {caminho}")


if __name__ == "__main__":
    main()
