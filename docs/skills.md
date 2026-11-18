# Skills

Um **skill** é um roteiro em markdown (`SKILL.md`) que um agente de IA segue para conduzir uma
tarefa longa **junto com a equipe**, com paradas para confirmação. O formato é independente de
ferramenta:
- o frontmatter (`name`, `description`) permite que agentes com suporte a skills os descubram
  sozinhos;
- os demais agentes simplesmente leem o arquivo e seguem as etapas.

## Skills disponíveis

| Skill | Para quê | Quando usar |
|---|---|---|
| [`iniciar-contratacao`](../skills/iniciar-contratacao/SKILL.md) | Onboarding: dependências, identidade git, dados do órgão, do processo e do objeto, planejamento institucional, modelo AGU, cabeçalho SEI | Logo depois de criar o repositório do processo |
| [`pesquisa-precos-pncp`](../skills/pesquisa-precos-pncp/SKILL.md) | Pesquisa de contratações similares, preços, atas para adesão e contratos no PNCP | Fase do ETP (capítulos 8 a 13), avaliação de adesão, consulta de vigência de contrato |

## Como usar

| Agente | Como invocar |
|---|---|
| **Claude Code** | `/iniciar-contratacao`, `/pesquisa-precos-pncp`, ou um pedido em linguagem natural ("quero pesquisar preços no PNCP"). Os stubs em `.claude/skills/` apontam para `skills/`. |
| **Codex, Gemini CLI, Cursor, Copilot e outros** | "Leia `AGENTS.md` e siga `skills/<nome>/SKILL.md`." O `AGENTS.md` lista os skills, e muitos desses agentes o leem automaticamente. |
| **Chat sem acesso a arquivos** | Cole o conteúdo do `SKILL.md` e execute as etapas manualmente, colando os resultados dos comandos. |

## Como criar um skill

1. Crie `skills/<nome>/SKILL.md` com o frontmatter:

   ```markdown
   ---
   name: <nome>
   description: <o que faz e QUANDO usar — é o texto que o agente usa para decidir acioná-lo>
   ---
   ```

2. Escreva as etapas numeradas. Cada uma termina numa **parada**: o agente mostra o resultado e só
   segue com o aval da equipe. Diga explicitamente o que o agente **não** decide sozinho.
3. Aponte as fontes de regra (`AGENTS.md`, `docs/…`, ADRs) em vez de repeti-las.
4. Para descoberta no Claude Code, crie o stub `.claude/skills/<nome>/SKILL.md` com o mesmo
   frontmatter e o corpo "Leia e siga `skills/<nome>/SKILL.md`."
5. Acrescente o skill à tabela acima e à lista do `AGENTS.md`.

Se um skill introduz um script ou um esquema novo, registre a decisão em `decisoes/`.
