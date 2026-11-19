# Redação do TR

## O TR segue o Modelo AGU item a item

`tr/` tem **um arquivo por capítulo do Modelo AGU de TR de Serviços de TIC** (atualização
abr/2026): treze capítulos, com Sanções no capítulo 9. A numeração interna segue o modelo item a
item. ADR:
[`2026-09-29-tr-modelo-agu-treze-capitulos.md`](../decisoes/2026-09-29-tr-modelo-agu-treze-capitulos.md).

**Os arquivos nascem com o texto literal do modelo**, e a conferência passa sem erro. Redigir o TR
é, portanto, afastar-se do modelo onde for preciso. Cada afastamento é marcado no **código de
formatação visual do IPP AGU/MGI de TIC** e, quando não é mero preenchimento, ganha uma
justificativa em cinza logo abaixo do item. ADR:
[`2026-11-19-codigo-formatacao-visual-ipp-agu.md`](../decisoes/2026-11-19-codigo-formatacao-visual-ipp-agu.md).

Dois comentários HTML marcam decisões pendentes no texto-base. Os dois precisam sumir antes do
status `aprovado`:

- `<!-- OU … -->`: alternativas excludentes do modelo. Adota-se uma, e as demais ficam na posição,
  tachadas.
- `<!-- TABELA DO MODELO … -->`: onde o modelo tem tabela. Reproduza-a de
  `templates/agu-tr-servicos-tic.md` e preencha dentro de `::: preenchimento … :::`. Linhas
  acrescidas vão em `::: inclusao … :::`.

> **Onde está a numeração do modelo?** Não está em `templates/agu-tr-servicos-tic.md`: o docx
> numera por lista automática do Word, e o pandoc a descarta. A referência numerada é
> `templates/agu-tr-servicos-tic-numerado.md`, gerada por
> `python3 scripts/conferir-modelo-agu.py --numerado`. Não a edite à mão.

## O código de formatação visual

O *Instrumento de Padronização dos Procedimentos de Contratação de Soluções de TIC* (AGU/MGI),
seção "Como elaborar o Termo de Referência?", recomenda apontar a motivação das alterações
**na própria minuta**, logo após a modificação, mantendo o texto original riscado. O quadro
"Código de formatação visual sugerida" (p. 88 do PDF) e a "Declaração de utilização de modelos
AGU/MGI" (p. 136) fixam o código:

| Ação | Formatação | No markdown |
|---|---|---|
| Inclusão | fonte vermelha | `[texto novo]{.inclusao}`; item ou bloco: `::: inclusao` … `:::` |
| Ajuste | fonte verde, após o original tachado | `~~texto do modelo~~ [texto novo]{.ajuste}` |
| Preenchimento | fonte azul | `[15 (quinze) dias úteis]{.preenchimento}`; tabela: `::: preenchimento` … `:::` |
| Supressão | trecho tachado | `~~texto do modelo~~` (trecho ou item inteiro) |
| Justificativa | fonte cinza, abaixo do item | `::: justificativa` … `:::`, logo depois do item |

As cores ficam num só lugar, em `scripts/tr_marcas.py`: vermelho `#FF0000`, verde `#00B050`, azul
`#0000FF` e cinza `#808080`. `scripts/marcas.lua` e `scripts/estilos-docx.py` repetem os valores,
com comentário apontando para lá.

Exemplos:

```
4.64. … em valor correspondente a [5% (cinco por cento)]{.preenchimento} do valor [total]{.preenchimento} ~~OU [anual]~~ da contratação.

1.11. ~~O contrato ou outro instrumento hábil que o substitua oferece maior detalhamento das regras que serão aplicadas em relação à vigência da contratação.~~ [O contrato oferece maior detalhamento das regras que serão aplicadas em relação à vigência da contratação.]{.ajuste}

::: justificativa
A alteração aqui efetuada se justifica porque não haverá instrumento substitutivo do contrato.
:::

9.2.2. ~~deixar de utilizar materiais e recursos humanos exigidos para fornecimento da solução de TIC, ou utilizá-los com qualidade ou quantidade inferior à demandada;~~

::: justificativa
Não se aplica: a solução não envolve o fornecimento de materiais.
:::
```

## As cinco regras

1. **O texto sem cor é o do modelo, literalmente.** A regra vale para o texto normal e para o
   tachado. Isso inclui:
   - "o Contratado"/"o Contratante";
   - caixa e pontuação;
   - a forma de citar normas;
   - até as falhas de digitação do próprio modelo.

   Reformular sem ganho de conteúdo é erro, mesmo em cor.

2. **Nenhum texto do modelo é apagado.** O que não se aplica fica na posição original, tachado:
   o item inteiro, o trecho e a alternativa `OU` não adotada. Apagar deslocaria a numeração e
   esconderia a escolha que o gestor fez. Só as lacunas do modelo (`<…>`, `[…]`, `XX`, `xxxxx`)
   dão lugar ao preenchimento em azul.

3. **Item novo entra no fim do capítulo**, ou como subitem do item do modelo a que se refere,
   depois dos subitens do modelo, e todo em vermelho.

4. **A cor diz o tipo, e só cobre o afastamento.**
   - O verde vem logo depois do original tachado. A frase reescrita pode repetir palavras do
     trecho tachado, como no exemplo do IPP.
   - O azul é só para lacuna e escolha.
   - Não recue subitens com quatro ou mais espaços: o pandoc os converte em bloco de código.

5. **Inclusão, ajuste e supressão levam justificativa** em `::: justificativa`, logo abaixo do
   item. Um bloco no item pai cobre os subitens marcados sem justificativa própria. Preenchimento
   e escolha de alternativa `OU` não precisam de justificativa. A justificativa é texto corrido,
   sem número de item. Comece pela razão, como no exemplo do IPP: "A alteração aqui efetuada se
   justifica porque…".

O build traduz as marcas com `scripts/marcas.lua`:
- no docx, nos estilos `TrechoIncluido`, `TrechoAjustado`, `TrechoPreenchido`, `ItemIncluido`,
  `ItemPreenchido` e `Justificativa` (via `scripts/estilos-docx.py`), com o tachado nativo do
  Word;
- no HTML, em cor e tachado embutidos em cada trecho, o que sobrevive à colagem no SEI e no
  Compras.gov.br.

O TR montado abre com a legenda do código, a mesma frase do despacho.

## O despacho é gerado, a partir do TR

`despachos/justificativa-modelo-agu.html` é **saída** de `scripts/gerar-despacho.py`. Editar o HTML
é erro, porque a próxima geração o sobrescreve.

- **Cada bloco `::: justificativa` do TR vira uma linha da tabela**, com o número do item e o tipo
  lido das marcas ("Inclusão", "Ajuste", "Supressão", ou combinações). Para mudar o texto do
  despacho, mude a justificativa no TR: os dois são o mesmo texto.
- Os dados do cabeçalho (unidade, processo, número do TR, signatário) ficam em constantes no topo
  do script.
- Linhas gerais, sem afastamento, continuam no script: `N("Geral — ...", "Texto.")`.
- A abertura do despacho descreve o código de cores com a mesma frase da legenda do TR
  (`LEGENDA` em `scripts/tr_marcas.py`).
- As linhas saem ordenadas pela numeração.
- O trecho a colar no SEI (modo Código-Fonte) fica entre os comentários "INÍCIO/FIM DO TRECHO A
  COPIAR NO SEI". Cabeçalho e estilos vêm de `templates/sei/documento-base.html`.

O IPP admite a nota técnica em separado, mas recomenda a justificativa na própria minuta. Aqui as
duas coisas saem juntas: a minuta traz a justificativa em cinza, e o despacho a consolida para os
autos.

## A conferência é obrigatória

Depois de qualquer edição em `tr/` ou no despacho:

```bash
python3 scripts/conferir-modelo-agu.py   # sai com código 1 se houver erro
# relatório lado a lado: build/conferencia-modelo-agu.html
```

O script aponta:
- diferença sem cor;
- tachado que não é o texto do modelo;
- cor sobre texto literal do modelo;
- texto do modelo apagado em vez de tachado;
- item do modelo ausente;
- numeração deslocada;
- afastamento sem justificativa e justificativa sem afastamento.

Também avisa, sem bloquear:
- verde sem original tachado antes ("é inclusão?");
- azul em item sem lacuna ("é ajuste?");
- uso da marca `.azul` antiga.

Tabelas não são conferidas célula a célula: a justificativa ou o preenchimento que as acompanha é
conferência manual.

## Migrar da marca `.azul`

Até a versão 1.0.0, todo afastamento saía em azul (`[trecho]{.azul}`, `::: azul`), o item que não
se aplicava virava `[Suprimido. (Conforme Nota…)]{.azul}` e a justificativa ficava só em chamadas
`A/I/E` de `scripts/gerar-despacho.py`. Essas marcas ainda são lidas, e a conferência emite aviso.
Para migrar:

1. **Preenchimento de lacuna ou escolha:** troque `{.azul}` por `{.preenchimento}`, e tache a
   alternativa descartada.
2. **Alteração:** tache o texto original (`~~…~~`) e marque o novo com `{.ajuste}`.
3. **Item novo:** troque `{.azul}`/`::: azul` por `{.inclusao}`/`::: inclusao`.
4. **"Suprimido":** volte o texto do modelo e tache-o.
5. **Justificativa:** mova o texto de cada `A/I/E` para um `::: justificativa` abaixo do item e
   apague a chamada.

## Build

```bash
scripts/build.sh tr        # build/TR.docx
scripts/build.sh tr-html   # build/TR.html, com o código de cores, para revisão e colagem no sistema/SEI
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
