# Redação do TR

## O TR segue o Modelo AGU item a item

`tr/` tem **um arquivo por capítulo do Modelo AGU de TR de Serviços de TIC** (atualização
abr/2026): treze capítulos, com Sanções no capítulo 9. A numeração interna segue o modelo item a
item. ADR:
[`2026-09-29-tr-modelo-agu-treze-capitulos.md`](../decisoes/2026-09-29-tr-modelo-agu-treze-capitulos.md).

**Os arquivos nascem com o texto literal do modelo**, e a conferência passa sem erro. Redigir o TR
é, portanto, afastar-se do modelo onde for preciso. Cada afastamento sai em azul e ganha uma linha
no despacho de justificativa.

Dois comentários HTML marcam decisões pendentes no texto-base. Os dois precisam sumir antes do
status `aprovado`:

- `<!-- OU … -->`: alternativas excludentes do modelo. Adota-se uma, e as demais ficam como
  "Suprimido".
- `<!-- TABELA DO MODELO … -->`: onde o modelo tem tabela. Reproduza-a de
  `templates/agu-tr-servicos-tic.md` e preencha dentro de `::: azul … :::`.

> **Onde está a numeração do modelo?** Não está em `templates/agu-tr-servicos-tic.md`: o docx
> numera por lista automática do Word, e o pandoc a descarta. A referência numerada é
> `templates/agu-tr-servicos-tic-numerado.md`, gerada por
> `python3 scripts/conferir-modelo-agu.py --numerado`. Não a edite à mão.

## As quatro regras

1. **Fora do azul, o texto é o do modelo, literalmente.** Isso inclui:
   - "o Contratado"/"o Contratante";
   - caixa e pontuação;
   - a forma de citar normas;
   - até as falhas de digitação do próprio modelo.

   Reformular sem ganho de conteúdo é erro, mesmo em azul.

2. **Item que não se aplica não é apagado.** Ele fica na posição original:

   ```
   9.10. [Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).]{.azul}
   ```

   Apagar deslocaria a numeração e quebraria a conferência com o despacho.

3. **Item novo entra no fim do capítulo**, ou como subitem do item do modelo a que se refere,
   depois dos subitens do modelo. Justificativa ("por que", "não se aplica porque") **não é item
   do TR**: vai para o despacho.

4. **Todo afastamento sai em azul, e só o afastamento.** Isso inclui o preenchimento de campos em
   aberto (`<...>`, `XX`, `[...]`) e a escolha entre alternativas.

   | Marcação | Uso |
   |---|---|
   | `[trecho]{.azul}` | Fragmento alterado dentro de item que, no resto, reproduz o modelo |
   | `::: azul` … `:::` | Tabela ou bloco inteiramente novo |

   Não recue subitens com quatro ou mais espaços: o pandoc os converte em bloco de código.

O azul é traduzido por `scripts/azul.lua`: nos estilos `TrechoAlterado`/`ItemAlterado` do docx
(via `scripts/estilos-docx.py`) e em cor embutida no HTML.

## O despacho é gerado, não digitado

`despachos/justificativa-modelo-agu.html` é **saída** de `scripts/gerar-despacho.py`. Editar o HTML
é erro, porque a próxima geração o sobrescreve.

- Os dados do cabeçalho (unidade, processo, número do TR, signatário) ficam em constantes no topo
  do script.
- Cada afastamento é uma chamada:
  - `A("4.14", "O que mudou.", "Razão.")`: alteração;
  - `I("4.1.6 a 4.1.14", ...)`: inclusão;
  - `E("2.3", SUP + "Por que não se aplica.")`: exclusão;
  - `N("Geral — ...", ...)`: linha informativa.
- As linhas saem ordenadas pela numeração, qualquer que seja a ordem no script.
- O trecho a colar no SEI (modo Código-Fonte) fica entre os comentários "INÍCIO/FIM DO TRECHO A
  COPIAR NO SEI". Cabeçalho e estilos vêm de `templates/sei/documento-base.html`.

## A conferência é obrigatória

Depois de qualquer edição em `tr/` ou no despacho:

```bash
python3 scripts/conferir-modelo-agu.py   # sai com código 1 se houver erro
# relatório lado a lado: build/conferencia-modelo-agu.html
```

O script aponta:
- alteração sem marca;
- azul sobre texto literal do modelo;
- item do modelo ausente;
- numeração deslocada;
- despacho fora de sincronia, nos dois sentidos.

Tabelas não são conferidas célula a célula: a linha do despacho que as justifica é conferência
manual.

## Build

```bash
scripts/build.sh tr        # build/TR.docx
scripts/build.sh tr-html   # build/TR.html, com o azul, para revisão e colagem no sistema/SEI
```

Para preservar fontes e margens da AGU, copie o docx do modelo para `templates/agu-referencia.docx`.
O build o usa como `--reference-doc` automaticamente.

## Modelo de Serviços × Compras de TIC

O template vem com o modelo de **Serviços** de TIC. Para adotar outro modelo da AGU, troque o
bloco `MODELO_REL`/`MODELO_NOME` em `scripts/conferir-modelo-agu.py` e gere de novo o texto-base
e a referência numerada. Veja [Adaptação ao seu órgão](adaptacao-ao-orgao.md).

## Riscos no TR

`tr/matriz-riscos.yaml` traz **só** os riscos que viram cláusula (SLA, glosa, sanção), com
`referencia_etp` apontando o `id` em `etp/riscos.yaml`. O ETP é a fonte, e o TR não repete a
descrição.
