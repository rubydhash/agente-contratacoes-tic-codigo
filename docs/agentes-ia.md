# Como os agentes de IA usam o repositório

## Arquivos de instrução

| Arquivo | Lido por | Conteúdo |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | Codex, Cursor, Gemini CLI, Copilot e outros (convenção `AGENTS.md`) | Regras inegociáveis, início de sessão, política de leitura, quando perguntar |
| [`CLAUDE.md`](../CLAUDE.md) | Claude Code | Importa o `AGENTS.md` e acrescenta o que é próprio do Claude Code |
| `.claude/settings.json` | Claude Code | Sem atribuição de co-autoria em commits e PRs; domínios públicos liberados (PNCP, dados abertos) |
| `skills/*/SKILL.md` | Qualquer agente | Roteiros de tarefa (veja [Skills](skills.md)) |

O `AGENTS.md` é curto de propósito: só o que muda o comportamento do agente. O detalhe fica nesta
documentação, que o agente consulta quando a tarefa pede.

## Política de leitura

Carregar o documento inteiro a cada sessão é o principal antipadrão. A hierarquia é esta:

| Sempre | Só se a tarefa pedir | Quase nunca, e só por janela |
|---|---|---|
| `MANIFEST.yaml` | A seção a editar | Texto integral de `referencia/normativos-md/*.md` |
| `etp/00-metadados.yaml` | O checklist YAML da seção | HTML/PDF de `referencia/normativos/` |
| `AGENTS.md` | `templates/agu-*.md` da seção análoga | O PDTI inteiro |
| | `normativos/planejamento-institucional-checklist.yaml` | |

Para conferir um dispositivo, faça `grep` do artigo e leia uma janela de cerca de 30 linhas. Um
`Read` sem limite num arquivo de mais de 1.000 linhas é sinal de que algo saiu do roteiro.

## O que os agentes não fazem

- Editar `referencia/`.
- Remover exigência de checklist para "fazer caber" o texto.
- Citar artigo sem conferir a redação em `referencia/normativos-md/`.
- Citar jurisprudência não verificada na sessão a partir de fonte oficial.
- Promover seção a `aprovado`.
- Rodar o build sem pedido.
- Commitar sem pedido.
- Reverter edição manual da equipe.
- Deixar qualquer marca de autoria de IA.

## Honestidade técnica

Quando não tiver certeza, o agente diz, por exemplo:

- "O texto citado vem de `referencia/normativos-md/lei-14133-2021.md`, linha 412. Não verifiquei
  alteração posterior."
- "Este quantitativo é estimativa minha a partir do padrão de uso informado. Precisa de
  confirmação do integrante técnico."

## Mais de um agente no mesmo trecho

O segundo agente lê o frontmatter atualizado pelo primeiro e respeita as `pendencias` listadas.
Se o primeiro sinalizou algo, não se ignora a pendência só porque "consegue resolver".
