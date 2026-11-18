#!/usr/bin/env bash
# Converte novos modelos .docx (em referencia/) para .md (em templates/).
# Útil quando os anexos pendentes do Gov Digital forem baixados.
#
# Uso: scripts/converter-docx.sh <arquivo.docx> [destino.md]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

src="${1:?Informe o caminho do .docx}"
dst="${2:-templates/$(basename "${src%.*}").md}"

pandoc -f docx -t gfm --wrap=none "$src" -o "$dst"
echo ">> $dst"
