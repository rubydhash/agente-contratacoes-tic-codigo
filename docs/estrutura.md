# Estrutura do repositório

```
.
├── MANIFEST.yaml              # Índice de todas as seções e status de cada uma (ponto de entrada)
├── AGENTS.md                  # Instruções para agentes de IA (CLAUDE.md o importa)
├── normativos/                # Checklists YAML curados: o que cada seção precisa cobrir
│   ├── lei14133-checklist.yaml
│   ├── in94-checklist.yaml             # inclui os Anexos I e II da IN 94
│   ├── agu-mapeamento.yaml             # capítulos do Modelo AGU ↔ arquivos de tr/
│   └── planejamento-institucional-checklist.yaml  # PDTI/PCA/PEI do órgão (onboarding)
├── templates/                 # Modelos convertidos para markdown e documento-base do SEI
│   ├── agu-tr-servicos-tic.md          # TR AGU (texto)
│   ├── agu-tr-servicos-tic-numerado.md # TR AGU com a numeração do Word (GERADO)
│   ├── agu-contrato-tic.md
│   ├── agu-lista-verificacao-tic.md
│   ├── agu-lista-verificacao-adesao-arp.md
│   ├── govdigital-etp.md               # Modelo de ETP de TIC da SGD (v1.2)
│   └── sei/documento-base.html         # Cabeçalho e estilos do SEI para os despachos
├── dfd/                       # Documento de Formalização da Demanda
│   ├── 00-metadados.yaml
│   └── 01-dfd.md
├── etp/                       # ETP: um arquivo por capítulo do ETP Digital (01 a 22)
│   ├── 00-metadados.yaml               # objeto, órgão, processo, equipe (lido por todos)
│   ├── 01-informacoes-basicas.md … 22-responsaveis.md
│   ├── tco.yaml                        # custos por solução viável (IN 94, art. 11, III)
│   ├── fontes.yaml                     # fontes [F-nn] → Anexo I em PDF
│   └── riscos.yaml
├── tr/                        # TR: um arquivo por capítulo do Modelo AGU (01 a 13)
│   ├── 00-metadados.yaml
│   ├── 01-condicoes-gerais.md … 13-disposicoes-finais.md
│   └── matriz-riscos.yaml              # só os riscos que viram cláusula
├── listas-verificacao/        # Listas de verificação da AGU em YAML (tic, adesao-arp)
├── despachos/                 # HTML para colar no SEI (GERADOS por scripts)
├── pesquisas/pncp/<slug>/     # Pesquisas no PNCP (criadas por scripts/pesquisa-pncp.py)
├── decisoes/                  # ADRs: AAAA-MM-DD-titulo.md
├── skills/                    # Roteiros para agentes de IA (SKILL.md), independentes de ferramenta
│   ├── iniciar-contratacao/
│   └── pesquisa-precos-pncp/
├── docs/                      # Esta documentação
├── anotacoes/                 # Notas de trabalho, atas, transcrições (insumo, não entra no build)
├── referencia/                # ORIGINAIS: somente leitura
│   ├── normativos/            # Lei, INs, decretos, portarias (HTML/PDF capturados, com SHA256SUMS)
│   ├── normativos-md/         # Versões markdown limpas, para consulta por grep
│   ├── normativos-orgao/      # PDTI, PEI e normas internas do órgão (criar no onboarding)
│   ├── modelos-agu/           # docx originais da AGU
│   ├── templates-gov-digital/ # docx do Gov.Digital
│   ├── planilhas/             # xlsx (TCO etc.)
│   │   # criadas conforme a necessidade:
│   ├── artefatos-em-elaboracao-externos/  # DFD/ETP/TR já registrados no Compras.gov.br
│   ├── contratacoes-proprias/             # contratos do próprio órgão (scripts/pesquisa-pncp.py contrato)
│   └── contratacoes-outros-orgaos/        # documentos de outros órgãos baixados do PNCP
├── scripts/                   # Ver docs/ferramentas.md
├── temp/                      # Área de trabalho não versionada (.gitignore)
└── build/                     # Saídas do build (.gitignore)
```

## Regras que a estrutura impõe

- **`referencia/` é imutável.** Lê-se, não se escreve. Snapshot que precisa ser preservado entra
  como arquivo novo, nunca sobrescrevendo outro.
- **Arquivos GERADOS não se editam à mão.** Isso vale para:
  - `templates/agu-tr-servicos-tic-numerado.md`;
  - `despachos/*.html`;
  - `etp/anexo-i-registro-de-fontes.pdf`;
  - tudo em `build/`.

  Edite a fonte (script ou YAML) e gere de novo.
- **O prefixo numérico é o número do capítulo** no sistema ou no modelo. Juntar ou separar
  arquivos exige ADR.
- **`MANIFEST.yaml` acompanha o disco.** Seção nova entra no MANIFEST, e `scripts/validar.sh`
  acusa as que faltam.
