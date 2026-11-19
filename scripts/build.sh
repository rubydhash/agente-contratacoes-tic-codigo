#!/usr/bin/env bash
# Monta DFD, ETP e TR finais em docx, concatenando as seções na ordem do MANIFEST.
# Uso:
#   scripts/build.sh           # gera build/DFD.docx, build/ETP.docx e build/TR.docx
#   scripts/build.sh dfd       # apenas DFD
#   scripts/build.sh etp       # apenas ETP
#   scripts/build.sh tr        # apenas TR (docx + anexos em PDF)
#   scripts/build.sh tr-html   # apenas TR (html, com o codigo de cores do IPP, para colar no SEI)
#   scripts/build.sh anexos-tr # apenas os anexos do TR em markdown (tr/ANEXO *.md -> build/*.pdf)
#
# Requer o .venv (requirements.txt): Python e pandoc vem de la (scripts/_ambiente.sh). Sem
# .venv, usa python3 e pandoc do sistema. Os anexos do TR em PDF exigem fpdf2 e a fonte DejaVu.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source scripts/_ambiente.sh
[[ -n "$PANDOC" ]] || { echo "ERRO: pandoc ausente. Crie o .venv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2; exit 1; }
mkdir -p build

REFERENCE_DOC=""
if [[ -f templates/agu-referencia.docx ]]; then
  REFERENCE_DOC="--reference-doc=templates/agu-referencia.docx"
fi

# Leitor e filtros do TR.
#
# O TR marca, no proprio markdown, os afastamentos do modelo AGU conforme o codigo de
# formatacao visual do IPP AGU/MGI de TIC (scripts/tr_marcas.py):
#   [texto]{.inclusao}  ::: inclusao       vermelho  inclusao
#   [texto]{.ajuste}                       verde     ajuste, apos o original tachado
#   [texto]{.preenchimento}                azul      preenchimento de lacuna
#   ~~texto~~                              tachado   supressao / alternativa nao adotada
#   ::: justificativa                      cinza     justificativa, abaixo do item
#
# Isso exige as extensoes bracketed_spans e fenced_divs no leitor (o gfm ja le o tachado),
# o filtro scripts/marcas.lua para traduzir as marcas em estilos, e um reference.docx
# que defina esses estilos (scripts/estilos-docx.py).
FROM_TR="gfm+bracketed_spans+fenced_divs"
MARCAS_FILTER="--lua-filter=scripts/marcas.lua"

# legenda_tr → ecoa o caminho de um markdown com a legenda do codigo de cores, a mesma
# frase do despacho (scripts/tr_marcas.py), para abrir o TR montado
legenda_tr() {
  [[ -z "$TMPDIR_BUILD" ]] && TMPDIR_BUILD="$(mktemp -d)"
  local saida="$TMPDIR_BUILD/00-legenda.md"
  "$PY" scripts/tr_marcas.py legenda-md > "$saida"
  echo "$saida"
}

# prepara_reference_azul → ecoa o caminho do reference.docx com os estilos das marcas
prepara_reference_azul() {
  [[ -z "$TMPDIR_BUILD" ]] && TMPDIR_BUILD="$(mktemp -d)"
  local base="$TMPDIR_BUILD/ref-base.docx"
  local saida="$TMPDIR_BUILD/ref-azul.docx"
  if [[ -f templates/agu-referencia.docx ]]; then
    cp templates/agu-referencia.docx "$base"
  else
    "$PANDOC" --print-default-data-file reference.docx > "$base"
  fi
  "$PY" scripts/estilos-docx.py "$base" "$saida" >&2
  echo "$saida"
}

# O pandoc concatena os arquivos ANTES de interpretá-los: só o frontmatter do
# primeiro vira metadado; o das demais seções cairia no corpo do documento como
# texto, levando ao docx as pendências internas da Equipe de Planejamento.
# Por isso o frontmatter é removido de todas as seções antes da montagem — os
# metadados do documento vêm dos arquivos 00-metadados.yaml, via --metadata-file.
TMPDIR_BUILD="$(mktemp -d)"   # criado aqui: as funcoes rodam em subshell ($(...), <(...))
cleanup() { [[ -n "$TMPDIR_BUILD" && -d "$TMPDIR_BUILD" ]] && rm -rf "$TMPDIR_BUILD"; }
trap cleanup EXIT

# strip_frontmatter <arquivos...> → ecoa os caminhos das cópias já limpas
strip_frontmatter() {
  [[ -z "$TMPDIR_BUILD" ]] && TMPDIR_BUILD="$(mktemp -d)"
  local f dest
  for f in "$@"; do
    dest="$TMPDIR_BUILD/$(echo "$f" | tr '/' '_')"
    awk 'NR==1 && $0=="---" { infm=1; next }
         infm && $0=="---"   { infm=0; next }
         !infm               { print }' "$f" > "$dest"
    echo "$dest"
  done
}

build_dfd() {
  echo ">> Montando DFD..."
  local out="build/DFD.docx"
  local files=(
    dfd/01-dfd.md
  )
  mapfile -t files < <(strip_frontmatter "${files[@]}")
  "$PANDOC" \
    --from=gfm --to=docx \
    --metadata-file=etp/00-metadados.yaml \
    --metadata-file=dfd/00-metadados.yaml \
    $REFERENCE_DOC \
    -o "$out" \
    "${files[@]}"
  echo ">> $out"
}

build_etp() {
  echo ">> Montando ETP..."
  local out="build/ETP.docx"
  # Um arquivo por capítulo do ETP Digital do Compras.gov.br (modelo SGD v1.2 + 18 a 20
  # acrescidos) — ver decisoes/2026-10-01-etp-capitulos-modelo-sgd.md.
  local files=(
    etp/01-informacoes-basicas.md
    etp/02-descricao-necessidade.md
    etp/03-area-requisitante.md
    etp/04-necessidades-negocio.md
    etp/05-necessidades-tecnologicas.md
    etp/06-demais-requisitos.md
    etp/07-estimativa-demanda.md
    etp/08-levantamento-solucoes.md
    etp/09-analise-comparativa-solucoes.md
    etp/10-registro-solucoes-inviaveis.md
    etp/11-analise-comparativa-custos-tco.md
    etp/12-descricao-solucao.md
    etp/13-estimativa-custo-total.md
    etp/14-justificativa-tecnica.md
    etp/15-justificativa-economica.md
    etp/16-beneficios.md
    etp/17-providencias.md
    etp/18-parcelamento.md
    etp/19-impactos-ambientais.md
    etp/20-registro-fontes.md
    etp/21-declaracao-viabilidade.md
    etp/22-responsaveis.md
  )
  mapfile -t files < <(strip_frontmatter "${files[@]}")
  # Anexo I (fontes) no fim, em seção paisagem — mesma fonte do PDF (etp/fontes.yaml).
  # Ver decisoes/2026-10-09-anexo-i-no-docx-do-etp.md.
  [[ -z "$TMPDIR_BUILD" ]] && TMPDIR_BUILD="$(mktemp -d)"
  local anexo="$TMPDIR_BUILD/anexo-i-fontes.md"
  "$PY" scripts/anexo-fontes-docx.py md "$anexo"
  "$PANDOC" \
    --from=gfm --to=docx \
    --metadata-file=etp/00-metadados.yaml \
    --resource-path=.:etp \
    $REFERENCE_DOC \
    -o "$out" \
    "${files[@]}" "$anexo"
  "$PY" scripts/anexo-fontes-docx.py paisagem "$out"
  echo ">> $out (com o Anexo I em paisagem)"
}

build_tr() {
  echo ">> Montando TR..."
  local out="build/TR.docx"
  # Ordem espelhando os 13 capítulos do Modelo AGU de TR de Serviços de TIC,
  # atualização abr/2026 — ver decisoes/2026-09-29-tr-modelo-agu-treze-capitulos.md.
  local files=(
    tr/01-condicoes-gerais.md
    tr/02-fundamentacao.md
    tr/03-descricao-solucao.md
    tr/04-requisitos.md
    tr/05-papeis-responsabilidades.md
    tr/06-modelo-execucao.md
    tr/07-modelo-gestao.md
    tr/08-criterios-medicao-pagamento.md
    tr/09-sancoes-glosa.md
    tr/10-selecao-fornecedor-regime.md
    tr/11-estimativas-valor.md
    tr/12-adequacao-orcamentaria.md
    tr/13-disposicoes-finais.md
  )
  mapfile -t files < <(strip_frontmatter "${files[@]}")
  files=("$(legenda_tr)" "${files[@]}")
  local ref
  ref="$(prepara_reference_azul)"
  "$PANDOC" \
    --from="$FROM_TR" --to=docx \
    --metadata-file=etp/00-metadados.yaml \
    --metadata-file=tr/00-metadados.yaml \
    $MARCAS_FILTER \
    --reference-doc="$ref" \
    -o "$out" \
    "${files[@]}"
  echo ">> $out"
  echo ">> afastamentos do modelo AGU no codigo de cores do IPP (estilos Trecho*/Item*/Justificativa)"
}

# Versao HTML do TR, com o codigo de cores do IPP — para revisao e para colagem no
# Compras.gov.br e no SEI. Mesma fonte de conteudo do docx. Cor e tachado saem como estilo
# embutido em cada trecho (scripts/marcas.lua), que e o que sobrevive a colagem em editores
# de texto rico; a folha de estilo abaixo cuida so da leitura na tela.
build_tr_html() {
  echo ">> Montando TR (HTML, codigo de cores do IPP)..."
  local out="build/TR.html"
  local files=(
    tr/01-condicoes-gerais.md
    tr/02-fundamentacao.md
    tr/03-descricao-solucao.md
    tr/04-requisitos.md
    tr/05-papeis-responsabilidades.md
    tr/06-modelo-execucao.md
    tr/07-modelo-gestao.md
    tr/08-criterios-medicao-pagamento.md
    tr/09-sancoes-glosa.md
    tr/10-selecao-fornecedor-regime.md
    tr/11-estimativas-valor.md
    tr/12-adequacao-orcamentaria.md
    tr/13-disposicoes-finais.md
  )
  mapfile -t files < <(strip_frontmatter "${files[@]}")
  files=("$(legenda_tr)" "${files[@]}")
  [[ -z "$TMPDIR_BUILD" ]] && TMPDIR_BUILD="$(mktemp -d)"
  cat > "$TMPDIR_BUILD/marcas.css" <<'CSSEOF'
body { font-family: "Times New Roman", serif; font-size: 12pt; text-align: justify;
       max-width: 52em; margin: 2em auto; padding: 0 16px; background: #fff; color: #000; }
/* cores: as de scripts/tr_marcas.py; o estilo embutido de scripts/marcas.lua prevalece */
.inclusao { color: #FF0000; } .ajuste { color: #00B050; } .preenchimento { color: #0000FF; }
.justificativa { color: #808080; } .azul { color: #0000CC; }
table { border-collapse: collapse; display: block; overflow-x: auto; }
table, th, td { border: 1px solid #000; padding: 3pt; }
h1 { font-size: 13pt; background: #e6e6e6; padding: 4pt; }
nav#TOC { font-family: sans-serif; font-size: 10pt; border: 1px solid #ccc; padding: 6pt 12pt; }
nav#TOC ul { columns: 2; }
code { font-family: inherit; background: #fff3c4; }
CSSEOF
  "$PANDOC" \
    --from="$FROM_TR" --to=html --standalone --embed-resources \
    --metadata title="Termo de Referência" \
    --toc --toc-depth=1 \
    --css="$TMPDIR_BUILD/marcas.css" \
    $MARCAS_FILTER \
    -o "$out" \
    "${files[@]}"
  echo ">> $out"
}

# Anexos do TR que nascem no repositorio (tr/ANEXO *.md): convertidos para PDF a cada build
# por scripts/gerar-anexos-tr.py (fpdf2). Anexo em docx (Termo de Compromisso) nao passa por
# aqui. Ver decisoes/2026-11-19-anexos-tr-md-pdf.md.
build_anexos_tr() {
  echo ">> Gerando os anexos do TR em PDF..."
  "$PY" scripts/gerar-anexos-tr.py
}

# O despacho de justificativa (despachos/justificativa-modelo-agu.html) NAO passa por este
# build: e HTML, para ser colado diretamente no SEI preservando a formatacao.
# O Anexo I do ETP sai em PDF proprio para os autos (scripts/gerar-anexo-fontes.py); o docx
# leva uma copia em secao paisagem (scripts/anexo-fontes-docx.py).
# Ver decisoes/2026-09-29-tr-modelo-agu-treze-capitulos.md.

case "${1:-all}" in
  dfd)     build_dfd ;;
  etp)     build_etp ;;
  tr)      build_tr && build_anexos_tr ;;
  tr-html) build_tr_html ;;
  anexos-tr) build_anexos_tr ;;
  all)     build_dfd && build_etp && build_tr && build_anexos_tr ;;
  *)       echo "Uso: $0 [dfd|etp|tr|tr-html|anexos-tr|all]"; exit 1 ;;
esac
