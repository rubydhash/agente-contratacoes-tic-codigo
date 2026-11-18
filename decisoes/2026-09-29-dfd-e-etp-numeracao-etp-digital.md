---
data: 2026-09-29
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# DFD no repositório e numeração do ETP alinhada ao ETP Digital do Compras.gov.br

> **Item 2 (numeração do ETP) superado** por `decisoes/2026-10-01-etp-capitulos-modelo-sgd.md`.

## Contexto

O template nasceu com duas pastas de artefatos, `etp/` e `tr/`. Na prática, o primeiro
artefato registrado no Compras.gov.br é o **Documento de Formalização da Demanda**, que
precede o ETP (IN SGD/ME nº 94, de 2022, art. 10, §1º; Decreto nº 10.947, de 2022,
art. 8º). Redigi-lo fora do repositório deixava sem controle de versão o texto que fixa o
objeto, o quantitativo e a estimativa preliminar, e que o ETP e o TR precisam repetir sem
divergência.

O ETP tinha catorze seções, uma por inciso do art. 18, §1º, da Lei nº 14.133, de 2021. O
ETP é, porém, preenchido no **ETP Digital** do Compras.gov.br, cujo formulário de TIC segue
o modelo do Governo Digital (`templates/govdigital-etp.md`) e desdobra em capítulos próprios
o que o template juntava numa seção só:

| Capítulo do ETP Digital | Antes (template) |
|---|---|
| 8. Levantamento de soluções | `05-mercado-alternativas` |
| 9. Análise comparativa de soluções | `05-mercado-alternativas` |
| 10. Registro de soluções consideradas inviáveis | `05-mercado-alternativas` |
| 11. Análise comparativa de custos (TCO) | `06-analise-custos-tco` |
| 12. Descrição da solução de TIC a ser contratada | `08-descricao-solucao` |
| 13. Estimativa de custo total da contratação | `07-estimativa-valor` |
| 14. Justificativa técnica da escolha da solução | — (não existia) |
| 15. Justificativa econômica da escolha da solução | — (não existia) |

Com uma seção agregando três capítulos, a colagem no sistema exigia recortar o texto, e a
justificativa da escolha, técnica e econômica, não tinha lugar próprio.

## Decisão

1. **Nova pasta `dfd/`**, com `00-metadados.yaml` (campos estruturados, para conferência
   cruzada) e `01-dfd.md`, cujas seções espelham os campos do formulário do DFD no PGC. O
   `scripts/build.sh` ganha o alvo `dfd`, e `scripts/validar.sh` passa a cobrir `dfd/`.

2. **O ETP adota, de 08 a 15, a numeração dos capítulos do ETP Digital.** As seções 01 a
   04 permanecem (necessidade, PCA, requisitos, quantitativos) e absorvem os capítulos 1 a 7
   do formulário; por isso **não existem arquivos 05 a 07**. As seções seguintes, que
   cobrem os incisos restantes do art. 18, §1º, passam a 16-21:

   | Arquivo | Conteúdo |
   |---|---|
   | `08-levantamento-solucoes.md` | IN 94, art. 11, II, "a", "b", "c", "d" e "h" |
   | `09-analise-comparativa.md` | IN 94, art. 11, II, "e", "f", "g", "i" e "j" |
   | `10-solucoes-inviaveis.md` | IN 94, art. 11, §1º |
   | `11-analise-custos-tco.md` | IN 94, art. 11, III (dados em `tco.yaml`) |
   | `12-descricao-solucao.md` | Lei 14.133, art. 18, §1º, VII; IN 94, art. 14 |
   | `13-estimativa-custo.md` | Lei 14.133, art. 18, §1º, VI; IN 94, art. 20 |
   | `14-justificativa-tecnica.md` | Lei 14.133, art. 41, I, e art. 43; IN 94, art. 9º, §6º |
   | `15-justificativa-economica.md` | IN 94, art. 11, V |
   | `16` a `21` | parcelamento, resultados, providências, correlatas, impactos, declaração |
   | `22-referencias-tecnicas.md` | registro de fontes (dados em `fontes.yaml`, Anexo I) |

3. **Registro de riscos em dois níveis.** `etp/riscos.yaml` é o registro interno completo
   da Equipe de Planejamento; o Mapa de Gerenciamento de Riscos lançado no sistema é
   artefato autônomo. O campo opcional `publicado` (`R-xx` ou `false`) faz a ponte. O
   cabeçalho do arquivo deixa de citar "IN 94, art. 9º, IV", dispositivo inexistente (o
   art. 9º tem três incisos), e passa a citar o art. 8º, §1º, e o art. 38.

## Consequências

- `MANIFEST.yaml`, `scripts/build.sh` e os checklists de `normativos/` foram
  renumerados. Remissões do tipo "etp/NN-…" em textos de projetos derivados precisam de
  `grep` a cada renumeração.
- Os números 05 a 07 ficam livres. Não reutilizá-los para outra finalidade: a
  correspondência com o ETP Digital é o que torna a colagem direta.

## Alternativas consideradas

- **Adotar a numeração do ETP Digital em todas as seções (1 a 18).** Rejeitada: os
  capítulos 16 a 18 do formulário não separam parcelamento, correlatas e impactos
  ambientais, que a Lei 14.133 exige como incisos próprios e que os checklists conferem
  um a um.
- **Manter a seção única de mercado e recortar na colagem.** Rejeitada pelo retrabalho a
  cada revisão e pela ausência de lugar para as justificativas técnica e econômica.
