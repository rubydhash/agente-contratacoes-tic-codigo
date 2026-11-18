# Repositórios derivados

Cada contratação começa por uma cópia deste template e evolui no próprio repositório. É comum que,
no caminho, o ferramental melhore: um script ganha um comando, uma regra nasce de um apontamento,
um checklist ganha um item. **Essas melhorias devem voltar ao template**, de preferência na mesma
sessão em que foram feitas, para que a próxima contratação já comece com elas.

## O que volta e o que não volta

| Volta ao template | Não volta |
|---|---|
| Scripts genéricos de `scripts/` | Dados e decisões do processo (`dfd/`, `etp/`, `tr/`, `pesquisas/`) |
| Skills de `skills/` | `referencia/` do caso (contratos, propostas, PDTI do órgão) |
| Regras de `AGENTS.md` e páginas de `docs/` | Scripts presos ao caso concreto |
| Checklists de `normativos/` | Valores do processo em scripts (cabeçalho do despacho, signatário) |
| ADRs sobre essas peças | Qualquer dado que identifique órgão, servidor ou processo |

Em script com valores do processo, volta só a mudança de lógica; os valores do template continuam
genéricos.

## Como devolver

1. **Compare antes de copiar.** O template pode ter evoluído por outro processo.
2. Copie o arquivo inteiro só quando a única diferença for a melhoria; caso contrário, aplique a
   mudança à mão.
3. **Anonimize as lições.** Escreva "em contratação anterior de firewall", e não o nome do órgão,
   do repositório ou o número do processo.
4. Registre a evolução no [`CHANGELOG.md`](../CHANGELOG.md).
5. Faça um commit por arquivo, na convenção do projeto, sem marca de ferramenta.

Contribuições ao template público seguem o [CONTRIBUTING.md](../CONTRIBUTING.md).

## Configuração útil no repositório derivado

Se o agente roda em sandbox com escrita restrita, acrescente o caminho local do template às
permissões de escrita do sandbox no repositório derivado. Assim, o agente consegue devolver o
ferramental na mesma sessão.
