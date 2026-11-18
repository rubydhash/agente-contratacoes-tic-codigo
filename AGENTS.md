# AGENTS.md

Instruções para qualquer agente de IA que edite este repositório. Leia este arquivo na primeira
interação de cada sessão. O detalhe de cada assunto está em `docs/`; aqui fica só o que muda o seu
comportamento.

## 1. O que é este repositório

Não é código de aplicação. É o **planejamento jurídico-técnico de uma contratação pública de TIC**
(DFD, ETP, TR), sob a Lei 14.133/2021, a IN SGD/ME 94/2022, a IN SEGES/ME 65/2021 e os modelos da
AGU. O objeto está em `etp/00-metadados.yaml > contratacao.objeto_curto`. Um erro aqui não é bug:
é apontamento de órgão de controle, nulidade de licitação ou prejuízo orçamentário. Aja com a
cautela proporcional.

Repositório recém-criado (metadados com `<preencher>`)? Proponha o skill `iniciar-contratacao`
antes de qualquer redação.

## 2. Regras inegociáveis

1. **Nunca edite `referencia/`.** É a fonte primária imutável.
2. **Nunca remova exigência de checklist** (`normativos/*.yaml`) para fazer o texto caber. Registre
   a pendência no frontmatter da seção.
3. **Nunca invente fundamentação legal.** Confira a redação literal em
   `referencia/normativos-md/` antes de citar artigo, parágrafo ou inciso.
4. **Nunca cite jurisprudência** que você não tenha verificado nesta sessão em fonte oficial.
5. **Nunca promova uma seção a `aprovado`.** Só uma pessoa promove, depois de `scripts/validar.sh`
   sem `ERRO` e com todos os itens de `exige` cobertos.
6. **Nunca rode `scripts/build.sh` para "verificar".** Ele só roda a pedido.
7. **Nunca commite sem pedido explícito.** Diff e proposta, sim.
8. **Nunca reverta edições manuais da equipe.** Elas são comandos de correção (§3).
9. **Nunca deixe marca de autoria de IA.** Isso vale para commit, frontmatter, ADR e documento:
   nada de `Co-Authored-By`, "Generated with", nome ou versão de modelo. O autor é a pessoa que
   autorizou o conteúdo.

## 3. Início de sessão

1. `git status` e `git diff`, **antes de ler qualquer seção**. Alteração não commitada da equipe é
   instrução:
   - trecho removido não volta;
   - valor fixado se propaga, mas você propõe a propagação em vez de aplicá-la em silêncio;
   - erro de digitação se aponta, não se corrige calado.

   Tabela completa em `docs/fluxo-de-trabalho.md`.
2. Leia o `MANIFEST.yaml` e o `etp/00-metadados.yaml`. Se houver `<preencher>` no que a tarefa
   exige, pare e pergunte.
3. Veja se há ADRs com `status: aberta` em `decisoes/` que afetem a tarefa.
4. Confirme com a pessoa qual seção atacar.

## 4. Política de leitura

| Sempre | Só se a tarefa pedir | Quase nunca, e só por janela (`grep` + ~30 linhas) |
|---|---|---|
| `MANIFEST.yaml`, `etp/00-metadados.yaml`, este arquivo | A seção alvo, o checklist dela, `templates/agu-*.md` análogo, `normativos/planejamento-institucional-checklist.yaml` | Texto integral de `referencia/normativos-md/*`, HTML/PDF de `referencia/normativos/` |

## 5. Editando uma seção (`dfd/`, `etp/`, `tr/`)

- **Checklist primeiro.** Os campos `fonte_lei_14133` e `fonte_in_94` do frontmatter levam aos
  checklists de `normativos/`. Classifique cada `exige` como coberto, falta ou depende da equipe.
- **Placeholder honesto vale mais que texto fluente sem dado.** O que falta vai para `pendencias`.
- **Frontmatter:**
  - `status` no máximo `revisao`;
  - `ultima_alteracao` em AAAA-MM-DD;
  - `pendencias` atualizada;
  - nenhum campo removido.
- **ETP:** numeração prefixada pelo capítulo (`3.1`, `3.1.1`). Cite fontes externas como
  `[F-nn]`, registradas em `etp/fontes.yaml`. Veja `docs/redacao-etp.md`.
- **TR:** fora do azul, o texto é o do modelo AGU literal. Item que não se aplica vira
  "Suprimido", nunca é apagado. Todo afastamento sai em azul e ganha linha em
  `scripts/gerar-despacho.py`. Depois de editar, rode `python3 scripts/conferir-modelo-agu.py`.
  Veja `docs/redacao-tr.md`.
- **Dados vão para YAML** (`tco`, `fontes`, `riscos`). Valor não apurado é `null` com `pendencia`.
  Veja `docs/dados-estruturados.md`.
- **Arquivos gerados não se editam à mão:**
  - `despachos/*.html`;
  - `templates/agu-tr-servicos-tic-numerado.md`;
  - `etp/anexo-i-*.pdf`;
  - `build/`.
- **Propague números:** `grep -rn "<valor antigo>" dfd/ etp/ tr/` antes de encerrar.
- **Mudança de esquema YAML, de granularidade de seções ou nova dependência exige ADR** em
  `decisoes/AAAA-MM-DD-titulo.md`.

## 6. Commits (só quando pedido)

- Mensagem: `<area>(<slug>): <verbo no infinitivo…>`, em português, com até 72 caracteres. Áreas:
  `dfd`, `etp`, `tr`, `riscos`, `normativos`, `templates`, `scripts`, `decisoes`, `manifest`,
  `referencia`, `docs`, `skills`.
- Faça branch antes; nunca commite em `main`.
- Sem identidade git configurada, use `git -c user.name=… -c user.email=… commit`, com a
  identidade confirmada pela pessoa.
- Não commite arquivos de ambiente do harness (`.bashrc`, `.mcp.json`, `.idea`…).

## 7. Pergunte antes de

- escolher a próxima seção quando houver mais de uma candidata;
- inferir valor, quantitativo ou prazo que não esteja nos metadados;
- assumir regime de execução, critério de julgamento ou modalidade;
- remover seção do `MANIFEST.yaml` ou qualquer arquivo de `referencia/`.

Não precisa perguntar para corrigir typo em `rascunho`, atualizar `ultima_alteracao`, acrescentar
pendência evidente ou rodar `scripts/validar.sh`.

**Na dúvida, diga.** Declare a origem do que afirma ("linha 412 de `lei-14133-2021.md`") e o que é
estimativa sua.

## 8. Skills

| Skill | Quando |
|---|---|
| `skills/iniciar-contratacao/SKILL.md` | Repositório novo: onboarding completo |
| `skills/pesquisa-precos-pncp/SKILL.md` | Contratações similares, preços, atas para adesão, contratos no PNCP |

## 9. Onde está o detalhe

| Assunto | Página |
|---|---|
| Sessão, edições manuais, commits, `temp/` | `docs/fluxo-de-trabalho.md` |
| DFD, ETP, fontes, Anexo I, PDF sem texto, matriz de fabricante | `docs/redacao-etp.md` |
| TR, azul, despacho, conferência | `docs/redacao-tr.md` |
| YAML, estados de cobertura | `docs/dados-estruturados.md` |
| Scripts | `docs/ferramentas.md` |
| PNCP | `docs/pesquisa-pncp.md` |
| Listas de verificação da AGU | `docs/listas-verificacao.md` |
| Dados do órgão, modelo AGU, SEI | `docs/adaptacao-ao-orgao.md` |
| Devolver ferramental ao template | `docs/repositorios-derivados.md` |

Se este arquivo divergir do estado real do repositório, avise e proponha a correção. Não siga a
versão errada em silêncio.
