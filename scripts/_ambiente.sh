# Ambiente comum dos scripts shell: Python e pandoc do .venv do repositório.
# Uso: source "$(dirname "${BASH_SOURCE[0]}")/_ambiente.sh"   (a partir da raiz ou de scripts/)
#
# Define:
#   PY      .venv/bin/python, se existir; senão, python3 do sistema
#   PANDOC  o pandoc embutido no pacote pypandoc_binary do .venv, se houver; senão, o do sistema
#
# Ver decisoes/2026-11-19-dependencias-no-venv.md e requirements.txt.

_RAIZ_AMBIENTE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -x "$_RAIZ_AMBIENTE/.venv/bin/python" ]]; then
  PY="$_RAIZ_AMBIENTE/.venv/bin/python"
else
  PY="python3"
fi

PANDOC=""
if [[ -x "$_RAIZ_AMBIENTE/.venv/bin/python" ]]; then
  PANDOC="$("$_RAIZ_AMBIENTE/.venv/bin/python" -c \
    'import pypandoc; print(pypandoc.get_pandoc_path())' 2>/dev/null || true)"
fi
if [[ -z "$PANDOC" || ! -x "$PANDOC" ]]; then
  PANDOC="$(command -v pandoc || true)"
fi
