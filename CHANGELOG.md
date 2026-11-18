# Changelog

As versões seguem `MANIFEST.yaml > projeto.versao_repo`.

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
