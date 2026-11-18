---
data: 2026-09-29
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# TR em treze capítulos do Modelo AGU abr/2026, texto-base literal e conferência automática

## Contexto

O template tinha catorze arquivos de TR, um por inciso do art. 12 da IN SGD/ME nº 94, de
2022, e **não** um por capítulo do modelo da AGU. Isso trazia três problemas, todos
verificados na primeira contratação que redigiu o TR a partir do template:

1. **Ordem.** O documento montado saía fora da ordem do modelo: capítulos do modelo
   ficavam partidos entre arquivos que o build posicionava em lugares diferentes.
2. **Auditabilidade.** Todo afastamento do modelo padrão precisa ser justificado em
   despacho próprio, e o formato usual de despacho no SEI (cabeçalho e estilos em
   `templates/sei/documento-base.html`) organiza-se em tabela cuja
   primeira coluna é *"Item conforme numeração do modelo"*. Sem correspondência direta de
   numeração, conferir o despacho contra o TR vira reconciliação manual.
3. **Numeração invisível.** O docx do modelo numera por lista automática do Word, e a
   conversão pelo pandoc (`templates/agu-tr-servicos-tic.md`) descarta essa numeração.
   Foi assim que se supôs, por engano, que o modelo tinha doze capítulos: *Sanções
   Administrativas e Procedimentos para retenção ou glosa no pagamento* usa o mesmo
   estilo numerado (`Nivel01`) dos demais títulos e é o **capítulo 9**.

Na mesma contratação, a conferência item a item revelou alterações do texto do modelo fora
do destaque (a mais extensa, a troca de "o Contratado" por "a Contratada"), itens novos
inseridos no meio de capítulos, deslocando a numeração de todos os seguintes, e subitens
recuados que o pandoc convertia em bloco de código.

O template também trabalhava sobre a atualização **set/2025** do modelo, enquanto a vigente
é a de **abr/2026**, que difere apenas pela desduplicação do item de atestado em nome da
matriz ou da filial (`normativos/agu-mapeamento.yaml`).

## Decisão

1. **`tr/` tem treze arquivos, um por capítulo do Modelo AGU de TR de Serviços de TIC,
   abr/2026**, de `01-condicoes-gerais.md` a `13-disposicoes-finais.md`. A correspondência
   com os incisos do art. 12 da IN 94 migra para o frontmatter (`fonte_lei_14133`,
   `fonte_in_94`, `capitulo_modelo_agu`) e para `normativos/agu-mapeamento.yaml`.

2. **Os arquivos nascem com o texto literal do modelo**, com a numeração do Word
   reconstruída de `word/numbering.xml` — 463 itens. Tabelas do modelo e escolhas entre
   alternativas ("OU") aparecem como comentários HTML, a resolver na redação.

3. **Regras de redação** (detalhe em `docs/redacao-tr.md`):
   - fora do azul, o texto é o do modelo, literalmente — inclusive "o Contratado" /
     "o Contratante", caixa, pontuação e falhas de digitação do próprio modelo;
   - item que não se aplica não é apagado: fica na posição como
     `N.N. [Suprimido. (Conforme Nota e/ou Justificativa anexada aos autos).]{.azul}`;
   - item novo entra ao final do capítulo, ou como subitem do item do modelo a que se
     refere, depois dos subitens do modelo;
   - todo afastamento sai em azul, e só ele — incluindo preenchimento de campos em aberto e
     escolha entre alternativas: `[trecho]{.azul}` ou `::: azul … :::`;
   - justificativa não é item do TR: vai para o despacho.

4. **O despacho é gerado**: `scripts/gerar-despacho.py` produz
   `despachos/justificativa-modelo-agu.html`, reaproveitando cabeçalho, estilos e timbre do
   exemplo do SEI, com o trecho a colar delimitado por comentários. A pasta `despachos/`
   reúne os despachos em HTML para colagem no SEI.

5. **A conferência é automática**: `scripts/conferir-modelo-agu.py` lê o modelo do docx em
   `referencia/`, classifica cada item do TR e acusa como erro a alteração sem marca, o
   azul sobre texto literal, o item ausente e a numeração deslocada; confere o despacho nos
   dois sentidos; grava `build/conferencia-modelo-agu.html`; e, com `--numerado`, regrava
   `templates/agu-tr-servicos-tic-numerado.md`.

6. **Destaque no documento final**: `scripts/azul.lua` traduz as marcações em estilos do
   docx (`TrechoAlterado`, `ItemAlterado`, injetados por `scripts/estilos-docx.py`) e, no
   HTML (`scripts/build.sh tr-html`), em cor embutida em cada trecho, que sobrevive à
   colagem no Compras.gov.br e no SEI.

## Consequências

- Dependências: `lxml` (conferência) e `pandoc` com as extensões `bracketed_spans` e
  `fenced_divs` (build do TR).
- Toda edição em `tr/` ou no despacho termina com `python3 scripts/conferir-modelo-agu.py`
  sem erro. No template recém-criado, a conferência sai limpa: 463 itens idênticos.
- Tabelas não são conferidas célula a célula: a linha do despacho que as justifica é
  conferência manual.
- Nova atualização do modelo AGU exige: juntar o docx em `referencia/modelos-agu/`,
  apontar `MODELO` em `scripts/conferir-modelo-agu.py`, regerar o numerado e reconferir.

## Alternativas consideradas

- **Manter um arquivo por inciso do art. 12 e reagrupar no build.** Rejeitada: transfere
  ao script uma complexidade invisível a quem lê, e o despacho continuaria exigindo
  tradução de numeração.
- **Conferir contra `templates/agu-tr-servicos-tic.md`.** Inviável: a conversão perde a
  numeração do Word.
- **Deixar fora do azul o preenchimento de campos em aberto.** Rejeitada: o despacho
  precisa apontar tudo o que difere do modelo aprovado.
