---
data: 2026-11-19
status: aceita
autores: ["Neuton Martins"]
---

# Dependências no .venv do repositório, inclusive o pandoc

## Contexto

As dependências estavam espalhadas entre o sistema e o `.venv`:
- **sistema (apt):** pandoc, poppler-utils, python3-yaml, python3-lxml, fonts-dejavu-core;
- **`.venv`:** fpdf2 e PyYAML (ADR de 2026-09-23).

Isso trazia três problemas:
- cada script exigia um Python diferente (`python3` para a conferência, `.venv/bin/python` para os
  PDFs);
- a versão do pandoc variava com a distribuição;
- a instalação pedia permissão de administrador para quase tudo.

O patch dos anexos do TR (`decisoes/2026-11-19-anexos-tr-md-pdf.md`) acrescentou mais um script com
fpdf2, chamado pelo build do TR.

## Decisão

1. **`requirements.txt` com versões fixas**, instalado no `.venv/` do repositório (fora do
   versionamento):

   | Pacote | Para quê |
   |---|---|
   | PyYAML | YAML |
   | lxml | conferência do TR |
   | fpdf2 | PDFs |
   | pypandoc_binary | traz o pandoc embutido, sem apt |
   | pypdfium2 | leitura de PDF, no lugar do poppler |

2. **Sem ativação.**
   - Os scripts Python com dependência chamam `_ambiente.usar_venv(__file__)` antes de importá-la.
     Se houver `.venv/bin/python` e o script não estiver nele, o processo é reexecutado com o
     Python do `.venv`. Os comandos documentados (`python3 scripts/…`) continuam valendo.
   - Os scripts shell fazem `source scripts/_ambiente.sh`, que define `PY` e `PANDOC`: os do
     `.venv`, se houver; senão, os do sistema.
3. **`scripts/ler-pdf.py`** (`info`, `texto`, `imagem`) substitui `pdftotext`/`pdftoppm` nos
   roteiros. O poppler continua utilizável, mas deixa de ser exigido.
4. **A fonte DejaVu continua vindo do sistema.** Não há pacote pip com ela, e versionar os TTF
   acrescentaria binários ao template. `_ambiente.fonte_ttf()` procura nas pastas usuais de
   Debian, Fedora e macOS, em `templates/fontes/` (opcional) e em `FONTES_TTF`.
5. **Diagnóstico:** `python3 scripts/_ambiente.py` lista o que há e o que falta.

## Consequências

- Do sistema ficam só git, `python3-venv` e a fonte DejaVu. A instalação do `.venv` precisa de
  rede para o PyPI uma vez.
- O pandoc do `.venv` (3.9) é mais novo que o das distribuições LTS. O filtro `scripts/marcas.lua`
  foi testado nas versões 3.1.3 e 3.9.
- O `pdftotext -layout` preserva melhor tabelas em colunas do que o pypdfium2. Em PDF com tabela
  extensa, o poppler, se instalado, ainda é a melhor opção.
- Atualizar uma dependência é editar `requirements.txt` e reinstalar. Versão nova do pandoc pede
  reconferir o build do TR.

## Alternativas consideradas

- **Manter o pandoc e o poppler do sistema.** Rejeitada: a versão varia por distribuição, e a
  instalação exige administrador.
- **Exigir a ativação do `.venv`** (`source .venv/bin/activate`). Rejeitada: agentes e pessoas
  esquecem, e a falha aparece como erro de importação longe da causa.
- **Versionar os TTF da DejaVu em `templates/fontes/`.** Adiada: elimina a última dependência de
  sistema, mas põe cerca de 1,4 MB de binário no template. A pasta já é procurada, se a equipe
  optar por isso.
