#!/usr/bin/env bash
# Converte novos modelos .docx (em referencia/) para .md (em templates/).
# Útil quando os anexos pendentes do Gov Digital forem baixados.
#
# Uso: scripts/converter-docx.sh <arquivo.docx> [destino.md]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
source scripts/_ambiente.sh   # PANDOC: o do .venv (pypandoc_binary) ou o do sistema
[[ -n "$PANDOC" ]] || { echo "ERRO: pandoc ausente (veja requirements.txt)" >&2; exit 1; }

src="${1:?Informe o caminho do .docx}"
dst="${2:-templates/$(basename "${src%.*}").md}"

"$PANDOC" -f docx -t gfm --wrap=none "$src" -o "$dst"
echo ">> $dst"
