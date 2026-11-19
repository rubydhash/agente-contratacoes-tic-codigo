#!/usr/bin/env python3
"""Preenche as listas de verificação da AGU a partir de listas-verificacao/*.yaml.

Uso:
    python3 scripts/gerar-listas-verificacao.py            # todas as listas
    python3 scripts/gerar-listas-verificacao.py adesao-arp # só uma
    python3 scripts/gerar-listas-verificacao.py --esqueleto tic referencia/modelos-agu/<modelo>.docx
        # cria listas-verificacao/tic.yaml com as perguntas do modelo e as respostas em branco

Cada YAML aponta o modelo .docx da AGU (em referencia/modelos-agu/) e traz, por linha das
tabelas do modelo, a resposta, o local nos autos e a providência. O script:

- confere o início de cada pergunta do YAML contra o texto do modelo (falha se divergir);
- marca a lista suspensa da coluna "Atende plenamente a exigência?" (Sim, Não, Não se aplica);
- escreve o local e, se pendente, a providência na terceira coluna;
- troca "[ÓRGÃO OU ENTIDADE PÚBLICA]" pelo nome do órgão;
- remove as tabelas inaplicáveis (nota 1 dos modelos);
- grava o docx em listas-verificacao/.

Item com `resposta` vazia fica com o texto "Resposta" do modelo, para preencher depois.

Só usa a biblioteca padrão; o YAML é lido pelo PyYAML do .venv, se houver, ou pelo do sistema.
ADR: decisoes/2026-11-06-listas-verificacao-agu.md.
"""
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)


import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "listas-verificacao"
RESPOSTAS = {"sim": "Sim", "nao": "Não", "nao_se_aplica": "Não se aplica"}
SITUACOES = {"atendido", "pendente"}


def texto(xml):
    return "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", xml))


def normaliza(s):
    return re.sub(r"\s+", " ", s).strip()


def inserir_run(celula, conteudo, tamanho=20):
    """Acrescenta um run de texto ao último parágrafo da célula."""
    run = (
        f'<w:r><w:rPr><w:sz w:val="{tamanho}"/><w:szCs w:val="{tamanho}"/></w:rPr>'
        f'<w:t xml:space="preserve">{escape(conteudo)}</w:t></w:r>'
    )
    i = celula.rfind("</w:p>")
    if i < 0:
        raise ValueError("célula sem parágrafo")
    return celula[:i] + run + celula[i:]


def marcar_resposta(celula, valor):
    """Troca o texto "Resposta" da lista suspensa pelo valor.

    O modelo tem dois formatos: a lista dentro da célula (w:sdt > w:sdtContent > w:r) e a lista
    envolvendo a célula inteira (w:sdt > w:sdtContent > w:tc). Nos dois, o texto "Resposta" está
    dentro da célula. Célula sem lista (linha do SIP no modelo de TIC) recebe o valor como texto.
    """
    novo, n = re.subn(r"(<w:t(?: [^>]*)?>)Resposta(</w:t>)",
                      lambda m: m.group(1) + escape(valor) + m.group(2), celula, count=1)
    if n == 1:
        return novo
    return inserir_run(celula, valor, tamanho=24)


def coluna_local(item):
    partes = []
    if item.get("local"):
        partes.append(normaliza(item["local"]))
    if item["situacao"] == "pendente" and item.get("providencia"):
        partes.append("Pendente: " + normaliza(item["providencia"]))
    elif item.get("providencia"):
        partes.append("Providência: " + normaliza(item["providencia"]))
    return " ".join(partes)


def gerar(caminho_yaml):
    dados = yaml.safe_load(caminho_yaml.read_text(encoding="utf-8"))
    modelo = RAIZ / dados["modelo"]
    saida = RAIZ / dados["saida"]
    itens = {str(it["id"]): it for it in dados["itens"]}
    for it in itens.values():
        if it.get("resposta") is None:
            continue
        if it.get("resposta") not in RESPOSTAS:
            raise SystemExit(f"{caminho_yaml.name} {it['id']}: resposta inválida {it.get('resposta')!r}")
        if it.get("situacao") not in SITUACOES:
            raise SystemExit(f"{caminho_yaml.name} {it['id']}: situação inválida {it.get('situacao')!r}")
        if it["resposta"] == "sim" and it["situacao"] == "pendente":
            raise SystemExit(f"{caminho_yaml.name} {it['id']}: resposta 'sim' não pode estar pendente")

    with zipfile.ZipFile(modelo) as z:
        membros = {n: z.read(n) for n in z.namelist()}
    doc = membros["word/document.xml"].decode("utf-8")

    remover = set(dados.get("remover_tabelas", []))
    usados = set()
    tabelas = list(re.finditer(r"<w:tbl>.*?</w:tbl>", doc, flags=re.S))
    pedacos, pos = [], 0
    for t_idx, mt in enumerate(tabelas):
        pedacos.append(doc[pos:mt.start()])
        pos = mt.end()
        if t_idx in remover:
            continue
        tabela = mt.group(0)
        linhas = list(re.finditer(r"<w:tr[ >].*?</w:tr>", tabela, flags=re.S))
        partes, p = [], 0
        for l_idx, ml in enumerate(linhas):
            partes.append(tabela[p:ml.start()])
            p = ml.end()
            linha = ml.group(0)
            if l_idx == 0:  # cabeçalho da seção
                partes.append(linha)
                continue
            iid = f"{t_idx + 1}.{l_idx}"
            if iid not in itens:
                raise SystemExit(f"{caminho_yaml.name}: falta o item {iid} ({normaliza(texto(linha))[:70]})")
            it = itens[iid]
            celulas = list(re.finditer(r"<w:tc>.*?</w:tc>", linha, flags=re.S))
            if len(celulas) != 3:
                raise SystemExit(f"{caminho_yaml.name} {iid}: linha com {len(celulas)} células")
            pergunta = normaliza(texto(celulas[0].group(0)))
            esperado = normaliza(it["pergunta"])
            if not pergunta.startswith(esperado):
                raise SystemExit(f"{caminho_yaml.name} {iid}: pergunta divergente\n  modelo: {pergunta[:90]}\n  yaml:   {esperado[:90]}")
            if it.get("resposta") is not None:
                c2 = marcar_resposta(celulas[1].group(0), RESPOSTAS[it["resposta"]])
                local = coluna_local(it)
                c3 = inserir_run(celulas[2].group(0), local) if local else celulas[2].group(0)
                linha = (linha[:celulas[1].start()] + c2 + linha[celulas[1].end():celulas[2].start()]
                         + c3 + linha[celulas[2].end():])
                linha = linha.replace("<w:showingPlcHdr/>", "")  # o valor deixa de ser o texto de exemplo
            partes.append(linha)
            usados.add(iid)
        partes.append(tabela[p:])
        pedacos.append("".join(partes))
    pedacos.append(doc[pos:])
    doc = "".join(pedacos)

    sobra = set(itens) - usados
    if sobra:
        raise SystemExit(f"{caminho_yaml.name}: itens sem linha no modelo: {sorted(sobra)}")

    orgao = escape(dados["orgao"])
    doc, n = re.subn(r'<w:color w:val="FF0000"/>(</w:rPr><w:t>)\[ÓRGÃO OU ENTIDADE PÚBLICA\]',
                     r"\1" + orgao, doc)
    if n != 1:
        raise SystemExit(f"{caminho_yaml.name}: marcador do órgão não encontrado")

    membros["word/document.xml"] = doc.encode("utf-8")
    saida.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, conteudo in membros.items():
            z.writestr(nome, conteudo)
    pend = sum(1 for it in itens.values() if it.get("situacao") == "pendente")
    cont = {r: sum(1 for it in itens.values() if it.get("resposta") == r) for r in RESPOSTAS}
    branco = sum(1 for it in itens.values() if it.get("resposta") is None)
    print(f">> {saida.relative_to(RAIZ)} ({len(itens)} itens: {cont['sim']} sim, {cont['nao']} não, "
          f"{cont['nao_se_aplica']} não se aplica, {branco} em branco; {pend} pendentes)")


def esqueleto(nome, modelo):
    """Cria listas-verificacao/<nome>.yaml com as perguntas do modelo e respostas em branco."""
    destino = PASTA / f"{nome}.yaml"
    if destino.exists():
        raise SystemExit(f"{destino.relative_to(RAIZ)} já existe; não sobrescrevo")
    caminho = (RAIZ / modelo).resolve()
    doc = zipfile.ZipFile(caminho).read("word/document.xml").decode("utf-8")
    linhas_yaml = []
    for t_idx, tabela in enumerate(re.findall(r"<w:tbl>.*?</w:tbl>", doc, flags=re.S)):
        for l_idx, linha in enumerate(re.findall(r"<w:tr[ >].*?</w:tr>", tabela, flags=re.S)[1:], 1):
            celula = re.findall(r"<w:tc>.*?</w:tc>", linha, flags=re.S)[0]
            pergunta = normaliza(texto(celula))
            if len(pergunta) > 90:
                pergunta = pergunta[:90].rsplit(" ", 1)[0]
            pergunta = pergunta.replace("\\", "\\\\").replace('"', '\\"')
            linhas_yaml += [f'- id: "{t_idx + 1}.{l_idx}"', f'  pergunta: "{pergunta}"',
                            "  resposta:     # sim | nao | nao_se_aplica", "  situacao:     # atendido | pendente",
                            '  local: ""', '  providencia: ""']
    rel = caminho.relative_to(RAIZ)
    cab = [
        f"# Lista de verificação da AGU preenchida a partir de {rel.name}",
        f"# Gera o docx por: python3 scripts/gerar-listas-verificacao.py {nome}",
        "# Esquema: ver o cabeçalho de scripts/gerar-listas-verificacao.py e o ADR das listas em decisoes/.",
        "# Tabelas inaplicáveis (nota 1 do modelo) vão em remover_tabelas, com índice a partir de 0.",
        f'modelo: "{rel}"',
        f'saida: "listas-verificacao/lista-verificacao-{nome}.docx"',
        'orgao: "<preencher>"',
        'processo: "<preencher>"',
        'data_revisao: ""',
        "remover_tabelas: []",
        "",
        "itens:",
    ]
    PASTA.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(cab + linhas_yaml) + "\n", encoding="utf-8")
    print(f">> {destino.relative_to(RAIZ)} ({len(linhas_yaml) // 6} itens em branco)")


def main():
    if sys.argv[1:2] == ["--esqueleto"]:
        if len(sys.argv) != 4:
            raise SystemExit("uso: --esqueleto <nome> <modelo.docx>")
        esqueleto(sys.argv[2], sys.argv[3])
        return
    nomes = sys.argv[1:]
    arquivos = [PASTA / f"{n}.yaml" for n in nomes] if nomes else sorted(PASTA.glob("*.yaml"))
    if not arquivos:
        raise SystemExit("nenhuma lista em listas-verificacao/")
    for a in arquivos:
        gerar(a)


if __name__ == "__main__":
    main()
