# Changelog

As versões seguem `MANIFEST.yaml > projeto.versao_repo`.

## Não publicado

### TR e despacho
- **Código de formatação visual do IPP AGU/MGI de TIC** no TR:
  - inclusão em vermelho;
  - ajuste em verde, após o original tachado;
  - preenchimento em azul;
  - supressão tachada, sem apagar o texto do modelo;
  - justificativa em cinza logo abaixo do item.

  ADR `decisoes/2026-11-19-codigo-formatacao-visual-ipp-agu.md`.
- **Despacho montado a partir das justificativas do TR**: o texto é o mesmo nos dois documentos.
  As chamadas `A/I/E` em `scripts/gerar-despacho.py` passam a ser legado.
- **Conferência**:
  - classes novas `PREENCHIDO`, `TACHADO-FORA-DO-MODELO`, `COR-EXCESSIVA` (antes
    `AZUL-EXCESSIVO`) e `SUPRESSAO-SEM-TACHADO`;
  - erro para afastamento sem justificativa;
  - avisos de semântica das cores.
- `scripts/azul.lua` substituído por `scripts/marcas.lua`; novo módulo comum `scripts/tr_marcas.py`.
- A marca `{.azul}` continua lida, com aviso. Veja "Migrar da marca `.azul`" em
  `docs/redacao-tr.md`.
- **Anexos do TR em markdown, com PDF gerado** (`scripts/gerar-anexos-tr.py`, alvo
  `scripts/build.sh anexos-tr`; `tr` e `all` também os geram). O cabeçalho leva o órgão de
  `etp/00-metadados.yaml`. Sem `tr/ANEXO *.md`, o build não exige o fpdf2. ADR em
  `decisoes/2026-11-19-anexos-tr-md-pdf.md`.

### Ambiente
- **Dependências no `.venv`** (`requirements.txt`, versões fixas): PyYAML, lxml, fpdf2, o pandoc
  (via `pypandoc_binary`) e o pypdfium2. Do sistema ficam só git, `python3-venv` e a fonte
  DejaVu.
  - Os scripts Python se reexecutam no `.venv` sem ativação (`scripts/_ambiente.py`).
  - Os scripts shell pegam dele o Python e o pandoc (`scripts/_ambiente.sh`).
  - `python3 scripts/_ambiente.py` diagnostica o ambiente.

  ADR em `decisoes/2026-11-19-dependencias-no-venv.md`.
- **`scripts/ler-pdf.py`** lê texto e gera imagens de PDFs, no lugar do `pdftotext`/`pdftoppm`.

### Corrigido
- `scripts/pesquisa-pncp.py baixar`: o nome da pasta passa a usar a razão social do detalhe da
  compra. O órgão do índice de busca do PNCP pode vir errado.
- `scripts/build.sh` deixava pastas temporárias para trás, porque as funções rodam em subshell.

## 1.0.0 — 2026-11-18

Primeira versão pública. Consolida o ferramental amadurecido em contratações reais de TIC, agora
neutro quanto ao órgão de origem.

### Artefatos
- **DFD** com os campos do formulário do PGC/Compras.gov.br.
- **ETP em 22 capítulos**, um por capítulo do ETP Digital (modelo SGD v1.2), com numeração
  prefixada conferida por `scripts/validar.sh`.
- **TR em 13 capítulos do Modelo AGU de Serviços de TIC (abr/2026)**, nascendo com o texto literal
  do modelo:
  - afastamentos em azul;
  - "Suprimido" no lugar de exclusão;
  - conferência automática item a item (`scripts/conferir-modelo-agu.py`).
- **Despacho de justificativa** dos afastamentos, gerado em HTML para o SEI
  (`scripts/gerar-despacho.py`).
- **Listas de verificação da AGU** (TIC e adesão a ARP) em YAML → docx e documento do SEI.

### Dados e evidências
- TCO, fontes e riscos em YAML; valor não apurado é `null` com pendência.
- Registro de fontes `[F-nn]` e Anexo I do ETP em PDF paisagem.
- Estados de cobertura (`suportado_sob_premissa` × `indeterminado`).

### Pesquisa no PNCP
- `scripts/pesquisa-pncp.py`:
  - busca multitermo e consolidação sem duplicatas;
  - triagem e classificação de SRP, adesão e tempestividade (IN 65);
  - saldo de adesão (API de dados abertos), atas e Painel de Preços por código de catálogo;
  - contratos e termos aditivos;
  - série de preços.
- Skill `pesquisa-precos-pncp`.

### Checklists normativos
- Lei 14.133, IN 94 (com os Anexos I e II), mapeamento do Modelo AGU e checklist genérico de
  planejamento institucional (PDTI, PCA, PEI).

### Para agentes de IA
- `AGENTS.md` enxuto, `CLAUDE.md`, documentação completa em `docs/`.
- Skill de onboarding `iniciar-contratacao`.
- Hook `scripts/hooks/commit-msg`, que bloqueia marcas de autoria de IA.
