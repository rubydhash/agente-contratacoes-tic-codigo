# Ferramentas (scripts)

Todos os scripts rodam a partir da raiz do repositório. Nenhum chama modelo de IA.

## Resumo

| Script | O que faz | Quando rodar | Escreve em |
|---|---|---|---|
| `scripts/validar.sh` | Validação estática | Sempre que quiser; obrigatório antes de `aprovado` | — (só lê) |
| `scripts/build.sh [dfd\|etp\|tr\|tr-html]` | Monta os documentos finais | Só quando a equipe pedir | `build/` |
| `scripts/conferir-modelo-agu.py [--numerado]` | Confere o TR item a item contra o docx da AGU e o despacho | Depois de qualquer edição em `tr/` ou no despacho | `build/conferencia-modelo-agu.html` |
| `scripts/gerar-despacho.py` | Gera o despacho de justificativa dos afastamentos | Depois de registrar afastamentos | `despachos/justificativa-modelo-agu.html` |
| `scripts/gerar-anexo-fontes.py` | Gera o Anexo I do ETP (PDF paisagem) | A cada mudança em `etp/fontes.yaml` | `etp/anexo-i-registro-de-fontes.pdf` |
| `scripts/gerar-listas-verificacao.py` | Preenche as listas de verificação da AGU (docx) | Antes da remessa à consultoria jurídica | `listas-verificacao/*.docx` |
| `scripts/gerar-lista-verificacao-sei.py <nome>` | A mesma lista como documento do SEI | Idem | `despachos/lista-verificacao-<nome>.html` |
| `scripts/pesquisa-pncp.py <comando>` | Pesquisa de contratações e preços no PNCP | Fase do ETP | `pesquisas/pncp/<slug>/` |
| `scripts/converter-docx.sh <docx> [md]` | Converte um modelo docx em markdown | Ao incorporar um modelo novo | `templates/` |
| `scripts/estilos-docx.py` | Injeta os estilos de destaque azul no docx de referência | Chamado pelo build | temporário |
| `scripts/anexo-fontes-docx.py` | Leva o Anexo I ao `build/ETP.docx` | Chamado pelo build | `build/` |
| `scripts/azul.lua` | Filtro pandoc: `{.azul}` → estilo no docx / cor no HTML | Chamado pelo build | — |
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
scripts/build.sh tr-html   # só o TR (HTML com o azul, para revisão e colagem)
```

O build concatena as seções na ordem do MANIFEST. Se existir `templates/agu-referencia.docx`, ele é
usado como `--reference-doc`. O despacho e o Anexo I em PDF **não** passam pelo build: são juntados
aos autos em separado.

Agentes não rodam o build "para verificar": ele é dispendioso e só roda a pedido.

## `scripts/conferir-modelo-agu.py`

Lê o modelo **direto do docx** em `referencia/modelos-agu/` e reconstrói a numeração automática do
Word. Classifica cada item do TR:

| Classe | Situação | Resultado |
|---|---|---|
| `IDENTICO` | Texto igual ao do modelo, sem azul | ok |
| `ALTERADO-MARCADO` | Toda a diferença está em azul | ok |
| `SUPRIMIDO` | Item mantido como "Suprimido" | ok |
| `INCLUIDO` | Item novo, inteiro em azul | ok |
| `ALTERADO-SEM-MARCA` | Diferença fora do azul | **erro** |
| `AZUL-EXCESSIVO` | Azul sobre texto do modelo | **erro** |

Também confere o despacho nos dois sentidos. Com `--numerado`, regrava
`templates/agu-tr-servicos-tic-numerado.md`. Requer `python3-lxml`.

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
pdftotext arquivo.pdf - | wc -c          # ~0 → o conteúdo é imagem
pdftoppm -r 150 -png arquivo.pdf "$TMPDIR/pag"
# leia os PNG com a ferramenta de leitura de imagem do agente
```

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
