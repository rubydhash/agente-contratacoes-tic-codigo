# Ferramentas (scripts)

Todos os scripts rodam a partir da raiz do repositório. Nenhum chama modelo de IA.

As dependências ficam no `.venv/` (`requirements.txt`), inclusive o pandoc. Não é preciso ativar o
`.venv`: `python3 scripts/<script>.py` se reexecuta nele (`scripts/_ambiente.py`), e os scripts
shell pegam dele o Python e o pandoc (`scripts/_ambiente.sh`). `python3 scripts/_ambiente.py`
diagnostica o ambiente. Veja [Primeiros passos](primeiros-passos.md#2-instale-as-dependências).

## Resumo

| Script | O que faz | Quando rodar | Escreve em |
|---|---|---|---|
| `scripts/validar.sh` | Validação estática | Sempre que quiser; obrigatório antes de `aprovado` | — (só lê) |
| `scripts/build.sh [dfd\|etp\|tr\|tr-html\|anexos-tr]` | Monta os documentos finais (`tr` e `all` incluem os anexos do TR) | Só quando a equipe pedir | `build/` |
| `scripts/gerar-anexos-tr.py [tr/ANEXO ….md]` | Gera em PDF os anexos do TR redigidos em markdown (`tr/ANEXO *.md`) | A cada mudança num anexo; chamado pelo build | `build/ANEXO *.pdf` |
| `scripts/conferir-modelo-agu.py [--numerado]` | Confere o TR item a item contra o docx da AGU e o despacho | Depois de qualquer edição em `tr/` ou no despacho | `build/conferencia-modelo-agu.html` |
| `scripts/gerar-despacho.py` | Gera o despacho a partir das justificativas do TR | Depois de justificar afastamentos no TR | `despachos/justificativa-modelo-agu.html` |
| `scripts/gerar-anexo-fontes.py` | Gera o Anexo I do ETP (PDF paisagem) | A cada mudança em `etp/fontes.yaml` | `etp/anexo-i-registro-de-fontes.pdf` |
| `scripts/gerar-listas-verificacao.py` | Preenche as listas de verificação da AGU (docx) | Antes da remessa à consultoria jurídica | `listas-verificacao/*.docx` |
| `scripts/gerar-lista-verificacao-sei.py <nome>` | A mesma lista como documento do SEI | Idem | `despachos/lista-verificacao-<nome>.html` |
| `scripts/pesquisa-pncp.py <comando>` | Pesquisa de contratações e preços no PNCP | Fase do ETP | `pesquisas/pncp/<slug>/` |
| `scripts/ler-pdf.py info\|texto\|imagem <pdf>` | Lê PDFs (texto ou PNG por página), sem poppler | Ao consultar normas, propostas e modelos em PDF | stdout ou `$TMPDIR` |
| `scripts/_ambiente.py` | Diagnóstico do ambiente; módulo que leva os scripts ao `.venv` | Na instalação, ou quando algo faltar | — |
| `scripts/converter-docx.sh <docx> [md]` | Converte um modelo docx em markdown | Ao incorporar um modelo novo | `templates/` |
| `scripts/estilos-docx.py` | Injeta os estilos das marcas do IPP no docx de referência | Chamado pelo build | temporário |
| `scripts/anexo-fontes-docx.py` | Leva o Anexo I ao `build/ETP.docx` | Chamado pelo build | `build/` |
| `scripts/marcas.lua` | Filtro pandoc: marcas do IPP → estilo no docx / cor e tachado no HTML | Chamado pelo build | — |
| `scripts/tr_marcas.py` | Módulo comum: leitura das marcas do TR, cores e legenda (`legenda-md`) | Usado pela conferência, pelo despacho e pelo build | — |
| `scripts/_gerar-stubs.sh` | Recria os stubs de seção que faltarem (não sobrescreve) | Raramente | `etp/`, `tr/` |

## `scripts/validar.sh`

Validação barata, só com bash, grep e awk (usa Python e PyYAML, se houver, para o parse de YAML).
Verifica:

- se todas as seções do `MANIFEST.yaml` existem;
- se nenhuma seção `aprovado` tem placeholder;
- se os YAMLs fazem parse;
- se as referências obrigatórias estão presentes (modelos AGU, checklists);
- se a numeração interna do ETP começa pelo número do capítulo;
- se há ADRs com `status: aberta` (emite aviso).

A saída tem linhas `OK`, `AVISO` e `ERRO`. Não pode haver `ERRO` para aprovar uma seção.

## `scripts/build.sh`

```bash
scripts/build.sh           # build/DFD.docx, build/ETP.docx, build/TR.docx
scripts/build.sh dfd       # só o DFD
scripts/build.sh etp       # só o ETP (com o Anexo I em seção paisagem)
scripts/build.sh tr        # só o TR (docx)
scripts/build.sh tr-html   # só o TR (HTML com o código de cores, para revisão e colagem)
```

O build concatena as seções na ordem do MANIFEST. Se existir `templates/agu-referencia.docx`, ele é
usado como `--reference-doc`. O despacho e o Anexo I em PDF **não** passam pelo build: são juntados
aos autos em separado.

Agentes não rodam o build "para verificar": ele é dispendioso e só roda a pedido.

## `scripts/conferir-modelo-agu.py`

Lê o modelo **direto do docx** em `referencia/modelos-agu/` e reconstrói a numeração automática do
Word. Classifica cada item do TR segundo as marcas do código de formatação visual do IPP
(veja [Redação do TR](redacao-tr.md#o-código-de-formatação-visual)):

| Classe | Situação | Resultado |
|---|---|---|
| `IDENTICO` | Texto igual ao do modelo, sem marca | ok |
| `PREENCHIDO` | Só lacuna preenchida em azul, tabela do modelo ou alternativa `OU` tachada | ok |
| `ALTERADO-MARCADO` | Inclusão, ajuste ou supressão parcial, toda marcada | ok |
| `SUPRIMIDO` | Item inteiro tachado, com o texto do modelo | ok |
| `INCLUIDO` | Item novo, inteiro em vermelho | ok |
| `ALTERADO-SEM-MARCA` | Diferença sem cor | **erro** |
| `TACHADO-FORA-DO-MODELO` | O tachado não é o texto do modelo | **erro** |
| `COR-EXCESSIVA` | Cor sobre texto literal do modelo | **erro** |
| `SUPRESSAO-SEM-TACHADO` | Texto do modelo apagado em vez de tachado | **erro** |

Também é erro:
- inclusão, ajuste ou supressão sem `::: justificativa`, no item ou num item pai;
- justificativa sem afastamento;
- justificativa fora de item.

Avisos, sem erro:
- verde sem original tachado;
- azul fora de lacuna;
- marca `.azul` antiga;
- linha `A/I/E` legada no despacho. Com `--numerado`, regrava
`templates/agu-tr-servicos-tic-numerado.md`. Requer `lxml`, do `.venv`.

## `scripts/pesquisa-pncp.py`

Subcomandos:
- `iniciar`
- `buscar`
- `consolidar`
- `enriquecer`
- `saldo`
- `atas-catalogo`
- `painel`
- `contrato`
- `baixar`
- `propostas`
- `serie`

O roteiro completo está em [Pesquisa no PNCP](pesquisa-pncp.md) e no skill
[`pesquisa-precos-pncp`](../skills/pesquisa-precos-pncp/SKILL.md). As APIs consultadas são
públicas:
- `pncp.gov.br`;
- `dadosabertos.compras.gov.br`.

## PDFs sem camada de texto

```bash
python3 scripts/ler-pdf.py texto arquivo.pdf -p 1-3     # texto vazio → o conteúdo é imagem
python3 scripts/ler-pdf.py imagem arquivo.pdf "$TMPDIR/pag" -p 1-3 --dpi 150
# leia os PNG com a ferramenta de leitura de imagem do agente
```

Se o poppler estiver instalado, `pdftotext`/`pdftoppm` também servem; o `-layout` do `pdftotext`
preserva melhor tabelas em colunas.

O que se lê de imagem é transcrito para uma nota em `anotacoes/` antes de ser citado (veja
[Redação do ETP](redacao-etp.md#fontes-em-pdf-sem-texto)).

## Conferir um artigo sem carregar a lei inteira

```bash
grep -nE "^Art\. 11" referencia/normativos-md/in-94-2022-sgd.md
# leia só uma janela de ~30 linhas a partir do número encontrado
```

## Incorporar um modelo docx novo

```bash
scripts/converter-docx.sh referencia/templates-gov-digital/<arquivo>.docx
```

Depois:
- atualize `MANIFEST.yaml`: tire o item de `pendencias_de_referencia` e acrescente-o em
  `referencia.templates_md`;
- crie uma ADR se a estrutura de arquivos mudar.
