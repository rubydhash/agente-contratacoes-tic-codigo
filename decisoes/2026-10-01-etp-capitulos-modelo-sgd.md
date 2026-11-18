---
data: 2026-10-01
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# ETP com um arquivo por capítulo do ETP Digital e numeração interna prefixada

> Supera o item 2 de `decisoes/2026-09-29-dfd-e-etp-numeracao-etp-digital.md`.

## Contexto

A decisão de 29/09/2026 alinhou ao ETP Digital do Compras.gov.br só os capítulos 8 a 15. As
seções 01 a 04 continuaram a seguir os incisos da Lei nº 14.133, de 2021, art. 18, §1º, e
"absorviam" os capítulos 1 a 7 do formulário. O efeito prático apareceu no primeiro ETP
elaborado a partir do template:

- os requisitos ficavam aglutinados em `03-requisitos.md`, enquanto o modelo de ETP de TIC
  da SGD (`referencia/templates-gov-digital/2-Estudo_Técnico_Preliminar_V1_2.docx`) e o
  sistema os separam em três capítulos (4 Necessidades de negócio, 5 Necessidades
  tecnológicas, 6 Demais requisitos) — a colagem exigia recortar o texto;
- a numeração de arquivo deixava de corresponder ao capítulo justamente no início do
  documento, o que dificultava achar no repositório o texto de um capítulo do sistema;
- dentro de cada capítulo, a numeração reiniciava em `1.`, `1.1`; colado no sistema, o
  capítulo 3 tinha um "item 1.1", ambíguo em remissão, parecer ou diligência.

O ETP 64/2026 também acrescentou ao modelo três capítulos (Parcelamento, Impactos ambientais
e Registro de fontes técnicas consultadas), antes da Declaração de viabilidade.

## Decisão

1. **Um arquivo por capítulo do ETP Digital**, com o prefixo igual ao número do capítulo e o
   nome abreviado do título do modelo SGD v1.2:

   | Nº | Capítulo | Arquivo | Modelo SGD v1.2 | Antes |
   |---|---|---|---|---|
   | 1 | Informações básicas | `01-informacoes-basicas.md` | 1 | — |
   | 2 | Descrição da necessidade | `02-descricao-necessidade.md` | 2 | `01-necessidade`, `02-pca` |
   | 3 | Área requisitante | `03-area-requisitante.md` | 3 | — |
   | 4 | Necessidades de negócio | `04-necessidades-negocio.md` | 4 | `03-requisitos` |
   | 5 | Necessidades tecnológicas | `05-necessidades-tecnologicas.md` | 5 | `03-requisitos` |
   | 6 | Demais requisitos necessários e suficientes à escolha da solução de TIC | `06-demais-requisitos.md` | 6 | `03-requisitos` |
   | 7 | Estimativa da demanda | `07-estimativa-demanda.md` | 7 | `04-quantitativos`, `19-contratacoes-correlatas` |
   | 8 | Levantamento de soluções | `08-levantamento-solucoes.md` | 8 | idem |
   | 9 | Análise comparativa de soluções | `09-analise-comparativa-solucoes.md` | 9 | `09-analise-comparativa` |
   | 10 | Registro de soluções consideradas inviáveis | `10-registro-solucoes-inviaveis.md` | 10 | `10-solucoes-inviaveis` |
   | 11 | Análise comparativa de custos (TCO) | `11-analise-comparativa-custos-tco.md` | 11 | `11-analise-custos-tco` |
   | 12 | Descrição da solução de TIC a ser contratada | `12-descricao-solucao.md` | 12 | idem |
   | 13 | Estimativa de custo total da contratação | `13-estimativa-custo-total.md` | 13 | `13-estimativa-custo` |
   | 14 | Justificativa técnica da escolha da solução | `14-justificativa-tecnica.md` | 14 | idem |
   | 15 | Justificativa econômica da escolha da solução | `15-justificativa-economica.md` | 15 | idem |
   | 16 | Benefícios a serem alcançados com a contratação | `16-beneficios.md` | 16 | `17-resultados-pretendidos` |
   | 17 | Providências a serem adotadas | `17-providencias.md` | 17 | `18-providencias-previas` |
   | 18 | Parcelamento | `18-parcelamento.md` | acrescido (SGD 14.1 e 14.2) | `16-parcelamento` |
   | 19 | Impactos ambientais | `19-impactos-ambientais.md` | acrescido | `20-impactos-ambientais` |
   | 20 | Registro de fontes técnicas consultadas | `20-registro-fontes.md` | acrescido | `22-referencias-tecnicas` |
   | 21 | Declaração de viabilidade | `21-declaracao-viabilidade.md` | 18 | idem |
   | 22 | Responsáveis | `22-responsaveis.md` | 19 e 20 | — |

2. **Incisos da Lei 14.133 sem capítulo próprio no modelo SGD** viram subitem fixo:
   previsão no PCA (art. 18, §1º, II) no **item 2.3**; contratações correlatas e
   interdependentes (inciso XI) no **item 7.4**, como fez o ETP 64/2026. Os checklists
   (`normativos/*.yaml`) apontam para esses arquivos; nenhum item de `exige` foi removido.

3. **Numeração interna prefixada pelo capítulo**: no capítulo N, `**N.1. …**` (primeiro nível
   em negrito), `N.1.1.`, `N.1.1.1.`. No capítulo 21, o sistema já traz o subcampo fixo
   `21.1. Justificativa da Viabilidade`; o texto colado começa em `21.1.1`.

4. **Frontmatter** das seções do ETP ganha `capitulo` (nº no ETP Digital) e
   `capitulo_modelo_sgd` (nº no modelo v1.2, `""` quando acrescido). O título `# N. …`
   repete o número.

5. **Conferência automática**: `scripts/validar.sh` acusa como erro item fora da numeração
   do capítulo, título sem o número e `capitulo` diferente do prefixo do arquivo.

## Consequências

- Remissões a nomes antigos (`etp/03-requisitos.md` etc.) em projetos derivados precisam
  de `grep` e troca, conforme a tabela acima. As ADRs de 2026-05-08 (arquitetura),
  2026-08-20 (TCO), 2026-09-23 (Anexo I) e 2026-09-29 citam nomes antigos como registro
  histórico e não foram reescritas.
- A ordem do documento passa a ser a do sistema, e não a dos incisos do art. 18, §1º. A
  correspondência com os incisos fica no frontmatter (`fonte_lei_14133`) e nos checklists.

## Alternativas consideradas

- **Manter 01–04 aglutinados (decisão de 29/09/2026).** Rejeitada pelos motivos do contexto.
- **Capítulos próprios para PCA e contratações correlatas.** Rejeitada: deslocaria a
  numeração de 21 e 22 em relação ao ETP já registrado no sistema, sem ganho de conteúdo.
- **Nomes de arquivo com o título integral do modelo.** Rejeitada pelo comprimento
  (`06-demais-requisitos-necessarios-e-suficientes-a-escolha-da-solucao-de-tic.md`).
