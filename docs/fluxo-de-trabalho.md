# Fluxo de trabalho

## Início de cada sessão (pessoa ou agente)

1. **`git status` e `git diff`**, antes de qualquer leitura. Alterações não commitadas são as
   correções mais recentes da equipe e têm precedência sobre tudo (veja abaixo).
2. **`MANIFEST.yaml`**: estado de cada seção.
3. **`etp/00-metadados.yaml`**: objeto, órgão, processo. Se ainda houver `<preencher>`, resolva
   isso primeiro. Redação substantiva sem esses dados vira retrabalho.
4. **ADRs com `status: aberta`** em `decisoes/` que afetem a seção em questão.
5. **Escolha da seção** a trabalhar. O agente pergunta; não escolhe sozinho.

## Edições manuais são comandos de correção

O ciclo normal é este: a IA propõe, e a equipe corrige editando o arquivo diretamente, no editor,
sem passar pelo agente. Por isso, **toda alteração não commitada em texto que a IA gerou é uma
instrução**, e não ruído:

| Sinal no diff | Significado | O que fazer |
|---|---|---|
| Trecho removido | Estava errado ou foi resolvido fora | Não reintroduzir |
| Placeholder → valor | Dado que faltava, agora fixado | Tratar como verdade e propor a propagação aos outros arquivos |
| Campo de frontmatter alterado | Decisão deliberada (status, pendências) | Não "corrigir" de volta |
| Pendência removida | Resolvida | Não recriar |
| Arquivo novo não rastreado | Insumo da equipe | Ler antes de propor algo que conflite |
| Erro de digitação introduzido | Provavelmente acidental | **Avisar**, não corrigir em silêncio |

Propagação: quando um valor é fixado num arquivo, faça `grep` pelo placeholder antigo e pelo nome
do campo em `dfd/`, `etp/`, `tr/` e `decisoes/`. Liste os pontos e proponha a propagação; não a
aplique em silêncio.

## Editando uma seção

1. O frontmatter da seção indica os dispositivos (`fonte_lei_14133`, `fonte_in_94`). Abra o
   checklist correspondente em `normativos/`.
2. Para cada item de `exige`, classifique: **coberto**, **falta** ou **depende de dado da equipe**.
3. Para cada `pergunta` do checklist, responda. Um "não" que não vira "sim" sem inventar dados
   vai para `pendencias`.
4. Redija. Prefira placeholder curto e honesto a texto de enchimento.
5. Atualize o frontmatter:
   - `status`: no máximo `revisao`;
   - `ultima_alteracao`: AAAA-MM-DD;
   - `pendencias`;
   - `autor`: quando houver revisão humana.
6. **Propague números.** Se um quantitativo, valor ou prazo mudou, rode
   `grep -rn "<valor antigo>" dfd/ etp/ tr/`.

## Aprovação

Antes de promover uma seção a `aprovado` (só uma pessoa promove):

```bash
scripts/validar.sh                     # nenhuma linha ERRO
python3 scripts/conferir-modelo-agu.py # se a seção é do TR
```

Todos os itens de `exige` precisam estar materialmente cobertos. Notas de redator (`<!-- … -->`)
e marcações `<!-- OU … -->` do TR precisam ter sumido.

## Branches e commits

- **Nunca commite direto em `main`.** Use uma branch por seção
  (`etp/02-descricao-necessidade`) ou uma por sessão, com um commit por seção.
- **Mensagem:** `<area>(<slug>): <verbo no infinitivo…>`, em português, com até 72 caracteres.
  - `<area>` é um de: `dfd`, `etp`, `tr`, `riscos`, `normativos`, `templates`, `scripts`,
    `decisoes`, `manifest`, `referencia`, `docs`, `skills`.
  - Exemplos:

    ```
    etp(necessidade): redigir descrição alinhada ao PDTI
    tr(requisitos): incorporar requisitos de segurança da informação
    riscos(EXEC-001): ajustar probabilidade após reunião técnica
    ```

- **Sem marca de autoria de IA.** Nada de `Co-Authored-By`, "Generated with", nome ou versão de
  modelo, em commit, frontmatter, ADR ou documento. Os documentos são atos administrativos
  subscritos por servidores; a ferramenta usada na redação não faz parte do processo.
- **Identidade do autor.** Se o git não tiver identidade configurada (comum em sandbox), passe-a
  na invocação, sem gravar em disco:

  ```bash
  git -c user.name="<nome>" -c user.email="<email>" commit -m "..."
  ```

  O autor é a pessoa que autorizou o conteúdo. Para conferir antes de publicar:

  ```bash
  git log --format="%an <%ae>%n%B" <base>..HEAD | grep -iE "co-authored|generated with"
  ```

### Hook opcional que bloqueia marcas de IA

```bash
git config core.hooksPath scripts/hooks   # ativa scripts/hooks/commit-msg
```

O hook recusa mensagens com `Co-Authored-By` ou "Generated with".

## Minutas do Compras.gov.br e a pasta `temp/`

- `temp/` é área **não versionada**: PDFs de minuta baixados do sistema e downloads transitórios.
- **A fonte canônica do conteúdo é o markdown.** Ajustes no sistema saem do repositório e são
  aplicados à mão pela equipe; o agente não opera o Compras.gov.br.
- Snapshot que precisa ser preservado vai para `referencia/artefatos-em-elaboracao-externos/`. O
  número do artefato fica em `etp/00-metadados.yaml > artefatos_no_comprasgov`.

## Arquivos de ambiente

Alguns harnesses de IA criam na raiz arquivos como `.bashrc`, `.mcp.json`, `.idea` e `.claude/*`.
O `.gitignore` já os exclui. Se aparecerem como não rastreados, **não commite**.

## Retomando o trabalho

Prompt para começar uma sessão nova do zero:

> Estou retomando o planejamento da contratação deste repositório. Antes de qualquer ação:
> (1) rode `git status` e `git diff` e trate as alterações como minhas correções; (2) leia
> `MANIFEST.yaml` e me diga o estado das seções; (3) para cada seção em `rascunho` ou `revisao`,
> me diga a pendência mais saliente; (4) sugira a próxima seção, justificando pelas dependências.
> Não carregue o texto integral de leis: use os checklists de `normativos/`.
