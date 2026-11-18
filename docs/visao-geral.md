# Visão geral

## A ideia: contratação como código

Um ETP ou um TR em Word é um arquivo opaco:
- duas pessoas não editam ao mesmo tempo sem conflito;
- não se sabe quem mudou o quê;
- um agente de IA precisa ler o documento inteiro para mexer num parágrafo.

Este template troca o documento por um **repositório**:

- **Um arquivo por capítulo**, numerado como no sistema ou no modelo oficial
  (`etp/07-estimativa-demanda.md` é o capítulo 7 do ETP Digital). O diff mostra exatamente o que
  mudou.
- **Dados em YAML, ao lado da prosa**: custos (`etp/tco.yaml`), fontes (`etp/fontes.yaml`) e
  riscos (`etp/riscos.yaml`). Número não se perde no meio de parágrafo, e o script confere.
- **Checklists normativos** (`normativos/*.yaml`) dizem, seção por seção, o que a Lei 14.133, a
  IN 94 e o planejamento do órgão exigem, e com que perguntas validar.
- **Build** monta o docx/HTML final na ordem certa. A formatação institucional (brasão,
  assinaturas) fica para o fim, feita à mão.
- **git** guarda o histórico, a revisão por branch e a autoria humana de cada alteração.

## O fluxo do processo

```
DFD  ──►  ETP  ──►  TR  ──►  Listas de verificação AGU  ──►  Despachos SEI
dfd/      etp/      tr/      listas-verificacao/              despachos/
                    │
                    └─ conferido item a item contra o Modelo AGU (scripts/conferir-modelo-agu.py)
```

| Etapa | Onde | Base normativa principal |
|---|---|---|
| Documento de Formalização da Demanda | `dfd/01-dfd.md` | Decreto 10.947/2022, art. 8º; IN 94, art. 10 |
| Estudo Técnico Preliminar (22 capítulos) | `etp/` | Lei 14.133, art. 18, §1º; IN 94, art. 11 |
| Pesquisa de preços e de contratações similares | `pesquisas/pncp/` | IN 65/2021; Lei 14.133, art. 86 |
| Termo de Referência (13 capítulos do Modelo AGU) | `tr/` | Lei 14.133, art. 6º, XXIII; IN 94, art. 12 |
| Listas de verificação da AGU | `listas-verificacao/` | Modelos da CNMLC/AGU |
| Despacho de justificativa dos afastamentos do modelo | `despachos/` | Uso de minuta padrão da AGU |

## Status de cada seção

Todo arquivo de seção tem frontmatter com `status`:

| Status | Significado | Quem promove |
|---|---|---|
| `rascunho` | Em redação; pode ter placeholders e notas de redator | — |
| `revisao` | Pronto para leitura humana | Pessoa ou agente |
| `aprovado` | Conferido contra o checklist, sem pendências | **Só uma pessoa**, depois de `scripts/validar.sh` |

O `MANIFEST.yaml` lista todas as seções e o estado de cada uma. É o ponto de entrada de qualquer
sessão.

## Quem faz o quê

| Pessoas (equipe de planejamento) | Agentes de IA |
|---|---|
| Fornecem os dados do órgão, do processo e do mercado | Propõem redação seção a seção, a partir do checklist |
| Decidem regime, modalidade, quantitativos e valores | Apontam lacunas, divergências e números não propagados |
| Corrigem o texto editando os arquivos diretamente | Tratam essas edições como **comandos de correção** |
| Aprovam seções e fazem os commits | Rodam validações; só commitam quando pedido |
| Assinam os documentos | Nunca deixam marca de autoria de IA no repositório |

A regra de ouro: **é melhor um placeholder honesto do que um parágrafo fluente sem lastro.** Os
agentes são instruídos a não inventar fundamentação legal, jurisprudência, preço ou quantitativo.

## Por que este formato

A ADR [`decisoes/2026-05-08-arquitetura-do-repo.md`](../decisoes/2026-05-08-arquitetura-do-repo.md)
registra a decisão. Em resumo:
- custo de contexto previsível (o agente lê só a seção, o checklist e os metadados);
- paralelismo real (uma seção por arquivo);
- histórico legível;
- fidelidade aos modelos oficiais.
