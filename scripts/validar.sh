#!/usr/bin/env bash
# Validador estático e barato (sem chamada a modelo de IA).
# Verifica:
#   - se todas as seções listadas no MANIFEST.yaml existem no disco;
#   - se nenhuma seção em status=aprovado tem placeholders pendentes;
#   - se YAMLs do projeto fazem parse;
#   - se templates de referência da AGU continuam acessíveis;
#   - se a numeração interna de cada capítulo do ETP começa pelo nº do capítulo.
#
# Uso:
#   scripts/validar.sh
#
# Não requer python — só bash, grep, awk.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

errors=0
warnings=0
log_err()  { echo "ERRO:    $*"; errors=$((errors+1)); }
log_warn() { echo "AVISO:   $*"; warnings=$((warnings+1)); }
log_ok()   { echo "OK:      $*"; }

echo "=== validar.sh — checagens estáticas ==="

# 1) Existência das seções listadas no MANIFEST
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  [[ -e "$path" ]] || log_err "seção declarada mas ausente: $path"
done < <(awk '/^[[:space:]]*-[[:space:]]*path:/ {sub(/^[[:space:]]*-[[:space:]]*path:[[:space:]]*/,""); print}' MANIFEST.yaml)

# 2) Placeholders em seções aprovadas
while IFS= read -r f; do
  if grep -nqE "(<preencher|<AAAA|<R\\\$|XXXXXX|DD/MM/AAAA)" "$f"; then
    log_warn "placeholders encontrados em arquivo possivelmente aprovado: $f"
  fi
done < <(grep -lE "^status:[[:space:]]*aprovado" dfd/*.md etp/*.md tr/*.md 2>/dev/null || true)

# 3) Parse dos YAMLs (parser leve via python -c se disponível, senão pula)
if command -v python3 >/dev/null 2>&1 && python3 -c "import yaml" >/dev/null 2>&1; then
  for y in MANIFEST.yaml normativos/*.yaml dfd/*.yaml etp/*.yaml tr/*.yaml listas-verificacao/*.yaml; do
    [[ -e "$y" ]] || continue
    python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$y" \
      && log_ok "YAML válido: $y" \
      || log_err "YAML inválido: $y"
  done
else
  log_warn "python3+pyyaml não disponível — pulando parse YAML."
fi

# 4) Referências obrigatórias presentes (templates AGU + checklists + normativos institucionais)
for ref in templates/agu-tr-servicos-tic.md templates/agu-lista-verificacao-tic.md \
           templates/agu-lista-verificacao-adesao-arp.md \
           normativos/in94-checklist.yaml normativos/lei14133-checklist.yaml \
           normativos/planejamento-institucional-checklist.yaml; do
  [[ -e "$ref" ]] && log_ok "referência presente: $ref" || log_err "referência faltando: $ref"
done

# 5) ADRs em status aberto — sinalizar ao usuário (não é erro, é alerta)
for adr in decisoes/*.md; do
  [[ -e "$adr" ]] || continue
  if grep -qE "^status:[[:space:]]*aberta" "$adr"; then
    log_warn "ADR em aberto: $adr — resolver antes de promover seções correlatas a 'aprovado'"
  fi
done

# 6) Numeração do ETP: o prefixo do arquivo é o nº do capítulo no ETP Digital; o campo
#    `capitulo` do frontmatter, o título "# N." e todo item numerado (N.1, N.1.1…) têm de
#    começar por esse número. Ver decisoes/2026-10-01-etp-capitulos-modelo-sgd.md.
for f in etp/[0-9][0-9]-*.md; do
  [[ -e "$f" ]] || continue
  base="$(basename "$f")"
  n=$((10#${base:0:2}))
  cap="$(awk 'NR==1 && $0=="---" {fm=1; next} fm && $0=="---" {exit}
              fm && /^capitulo:/ {print $2; exit}' "$f")"
  [[ "$cap" == "$n" ]] || log_err "$f: frontmatter 'capitulo: ${cap:-ausente}' não corresponde ao prefixo do arquivo ($n)"
  while IFS= read -r msg; do
    log_err "$f: $msg"
  done < <(awk -v n="$n" '
    NR==1 && $0=="---" { fm=1; next }
    fm { if ($0=="---") fm=0; next }
    /<!--/ { com=1 }
    com { if (/-->/) com=0; next }
    /^# / && !h1 { h1=1; if ($0 !~ ("^# " n "\\. ")) print "linha " NR ": título deve começar por \"# " n ". \""; next }
    {
      linha=$0; sub(/^\*\*/, "", linha)
      if (match(linha, /^[0-9]+(\.[0-9]+)*\.[ *]/)) {
        split(linha, p, ".")
        if (p[1] != n) print "linha " NR ": item \"" substr(linha, 1, RLENGTH-1) "\" fora da numeração do capítulo " n " (esperado " n ".x)"
      }
    }' "$f")
done

echo "---"
echo "Total: $errors erro(s), $warnings aviso(s)"
[[ $errors -eq 0 ]]
