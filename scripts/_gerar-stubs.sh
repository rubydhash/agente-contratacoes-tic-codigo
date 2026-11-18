#\!/usr/bin/env bash
# Gera os stubs de seção do ETP e do TR uma única vez.
# Pode ser executado de novo no futuro (não sobrescreve arquivos existentes).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
write_if_absent() {
  local path="$1"
  if [[ -e "$path" ]]; then
    echo "skip (existe): $path"
    return
  fi
  cat > "$path"
  echo "criado:        $path"
}
