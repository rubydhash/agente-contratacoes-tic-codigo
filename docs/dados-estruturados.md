# Dados estruturados ao lado da prosa

Arquivos que guardam **dados**, e não texto, ficam em YAML ao lado das seções. A seção em markdown
**interpreta** os dados (método, memória de cálculo, leitura dos resultados) e não os repete.

| Arquivo | Conteúdo | Origem | Regra ao atualizar |
|---|---|---|---|
| `etp/tco.yaml` | Custos por solução viável (IN 94, art. 11, III) | Catálogo de Soluções de TIC, atas, pesquisa de mercado | Toda linha de custo tem `fonte`. Valor sem fonte não entra no comparativo |
| `etp/fontes.yaml` | Documentos externos citados como `[F-nn]` | Consultas da equipe | Regenerar o Anexo I (`scripts/gerar-anexo-fontes.py`) |
| `etp/riscos.yaml` | Riscos do planejamento, da seleção e da execução | Equipe | `id` no padrão `<FASE>-NNN` (próximo número livre) |
| `tr/matriz-riscos.yaml` | Só os riscos que viram cláusula | `etp/riscos.yaml` | `referencia_etp` aponta o `id` de origem |
| `etp/inventario.yaml` (opcional) | Parque de ativos, quando o objeto depende dele | Inventário do órgão (CMDB, ferramenta de gerência) | Regenerar por script; nunca editar linha a linha. Esquema registrado em ADR ao criar |
| `pesquisas/pncp/<slug>/*` | Pesquisa no PNCP | `scripts/pesquisa-pncp.py` | Veja [Pesquisa no PNCP](pesquisa-pncp.md) |
| `listas-verificacao/*.yaml` | Listas de verificação da AGU | Equipe | Veja [Listas de verificação](listas-verificacao.md) |

## Valor não apurado é `null` com pendência

Esta regra vale para todos os arquivos: **valor ainda não apurado é `null`, com o campo
`pendencia` preenchido.** Nunca entra um número estimado sem origem declarada. Custo ou avaliação
de natureza qualitativa usa o campo `qualitativo`, e não um valor inventado.

## Cobertura: cinco estados, não dois

Quando há conferência de compatibilidade (por exemplo, inventário × matriz do fabricante), a chave
`cobertura` distingue:

| Estado | Significado |
|---|---|
| `suportado` | Verificado diretamente |
| `suportado_condicionado` | Suportado, com condição explícita (versão, módulo, licença) |
| `suportado_sob_premissa` | Depende de premissa declarada em `premissas` (`enunciado`, `consequencia_se_falsa`, `situacao`) |
| `indeterminado` | Sem lastro para afirmar |
| `nao_suportado` | Verificado que não há suporte |

A distinção que mais importa perante a auditoria é a do meio:
- **`suportado_sob_premissa`** é afirmação com lastro declarado e falsificável;
- **`indeterminado`** é ausência de lastro.

Não converta um no outro por conveniência.

Ao relatar em prosa, informe **sempre os dois números**: o verificado diretamente e o total
incluindo premissas. Declarar só o total é o atalho que devolve o processo em diligência.

## Convenções de YAML

- Chaves em snake_case e em **português** (`exige`, `perguntas`, `secao`).
- Listas continuam listas; não as converta em prosa.
- O esquema dos checklists de `normativos/` é contrato com `scripts/validar.sh`. Chave nova
  exige ADR.

ADR do TCO: [`2026-08-20-tco-estruturado.md`](../decisoes/2026-08-20-tco-estruturado.md).
