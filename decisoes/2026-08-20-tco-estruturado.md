---
data: 2026-08-20
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# Dados do TCO em YAML estruturado, ao lado da seção em markdown

## Contexto

O art. 11, III, da IN SGD/ME nº 94, de 2022, exige duas coisas na análise
comparativa de custos: o cálculo do custo total de propriedade por solução
tecnicamente viável (alínea "a") e a memória de cálculo que referencie os preços
utilizados, "com vistas a permitir a verificação da origem dos dados" (alínea "b").

Materializar isso em prosa produz tabelas grandes em markdown — exatamente o que
`docs/dados-estruturados.md` desaconselha, e por bons motivos: tabela larga em markdown gera
diff ilegível, é frágil a edição manual e não permite validação automática.

Além disso, os valores de um TCO costumam estar em estágios distintos de
maturidade: alguns têm fonte documental (PMC-TIC, atas, contratações de outros
órgãos), outros dependem de pesquisa formal de preços ainda não realizada, e
outros são qualitativos por natureza (esforço incremental de operação). Prosa não distingue
bem esses três estados; estrutura, sim.

## Decisão

Criar **`etp/tco.yaml`** como fonte canônica dos dados da análise de custos,
mantendo `etp/11-analise-custos-tco.md` como a **leitura** desses dados — método,
memória de cálculo narrada, interpretação dos resultados e advertências.

Regras do esquema:

- todo item de custo tem campo `fonte`; item sem fonte rastreável não entra no
  comparativo (exigência direta da alínea "b");
- valor ainda não apurado é registrado como `null` com o campo `pendencia`
  preenchido — nunca como número estimado sem origem;
- custo de natureza qualitativa usa o campo `qualitativo`, e não um valor
  monetário inventado;
- soluções registradas como inviáveis ficam em `sem_tco_por_inviabilidade`, com o
  motivo e a remissão à seção que fundamenta, refletindo a dispensa do art. 11,
  §1º.

Segue o mesmo padrão já adotado no repositório para `etp/riscos.yaml` e
`tr/matriz-riscos.yaml`: o estruturado fica estruturado, a prosa interpreta.

## Consequências

- `MANIFEST.yaml` passa a listar `etp/tco.yaml` em `sections_etp`, com
  `tipo: estruturado`.
- `scripts/validar.sh` passa a validar o parse do novo YAML automaticamente, sem
  alteração no script — o laço já cobre `etp/*.yaml`.
- Quando a pesquisa formal de preços for concluída, a atualização ocorre em um
  único arquivo, e `11` só precisa de ajuste na leitura dos resultados.
- Se, no futuro, a planilha de TCO do Governo Digital
  (`referencia/planilhas/01_modelo-planilha-tco-e-analise-comparativa-de-custos-tic-geral.xlsx`)
  for exigida como anexo do processo, `etp/tco.yaml` é a fonte para preenchê-la —
  não o contrário.

## Alternativas consideradas

- **Tabela em markdown dentro de `11`.** Rejeitada por `docs/dados-estruturados.md` e pelos
  motivos de legibilidade de diff acima.
- **Planilha `.xlsx` no repositório.** Rejeitada: binário não versiona de forma
  legível e não é validável por `scripts/validar.sh`.
