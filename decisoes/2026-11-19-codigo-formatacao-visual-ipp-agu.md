---
data: 2026-11-19
status: aceita
autores: ["Neuton Martins"]
---

# Código de formatação visual do IPP AGU/MGI no TR, com justificativa na minuta

## Contexto

A ADR `2026-09-29-tr-modelo-agu-treze-capitulos.md` adotou um destaque único: todo afastamento
do modelo saía em azul (`{.azul}`), o item que não se aplicava virava
`[Suprimido. (Conforme Nota…)]{.azul}`, e a justificativa ficava só no despacho, digitada como
chamada `A/I/E` em `scripts/gerar-despacho.py`.

O *Instrumento de Padronização dos Procedimentos de Contratação de Soluções de TIC* (AGU/MGI,
<https://www.gov.br/agu/pt-br/composicao/cgu/cgu/guias/instrumento_de_padronizacao_agu_tic_digital.pdf>),
seção "Como elaborar o Termo de Referência?" (p. 87–88 da numeração impressa), recomenda outra
coisa:
- apontar a motivação das alterações **diretamente na minuta**, logo após a modificação;
- manter o texto original riscado, seguido do texto alterado em cor distinta;
- riscar a redação não escolhida, quando o modelo oferece alternativas, e mantê-la riscada;
- preencher as lacunas em cor distinta.

O quadro "Código de formatação visual sugerida" fixa o código. A "Declaração de utilização de
modelos AGU/MGI" (p. 136) o repete:

| Ação | Formatação |
|---|---|
| Inclusão | fonte vermelha |
| Ajustes | fonte verde |
| Preenchimento | fonte azul |
| Supressão | trecho tachado |
| Justificativas | fonte cinza, logo abaixo de cada item modificado |

O mesmo quadro aparece para o edital (p. 111), o contrato (p. 119) e a ata (p. 127).

## Decisão

1. **Marcas no markdown do TR**, traduzidas por `scripts/marcas.lua` e
   `scripts/estilos-docx.py`:
   - `[…]{.inclusao}` e `::: inclusao`: vermelho;
   - `~~original~~ […]{.ajuste}`: verde;
   - `[…]{.preenchimento}` e `::: preenchimento`: azul;
   - `~~…~~`: tachado;
   - `::: justificativa`: cinza.

   As cores e a frase que descreve o código ficam em `scripts/tr_marcas.py`: vermelho
   `#FF0000`, verde `#00B050`, azul `#0000FF` e cinza `#808080`, as cores padrão do Word.
2. **Supressão é o texto original tachado**, na posição. A redação "Suprimido" deixa de ser
   usada. A alternativa `OU` não adotada também fica tachada.
3. **A justificativa fica no TR**, em bloco cinza logo abaixo do item. Um bloco no item pai cobre
   os subitens. O despacho (`scripts/gerar-despacho.py`) é montado a partir desses blocos, e o
   texto da minuta e o dos autos é um só. A abertura do despacho e a legenda do TR montado usam a
   mesma frase.
4. **Exigem justificativa: inclusão, ajuste e supressão.** Preenchimento de lacuna e escolha de
   alternativa `OU` não exigem: o IPP pede justificativa para acréscimos e supressões, e o
   preenchimento é próprio do uso do modelo.
5. **O build gera só a versão marcada** (`tr` e `tr-html`). É a que vai à consultoria jurídica.
6. **A conferência acompanha o código.** O texto sem cor, normal ou tachado, tem de ser o do
   modelo. Texto do modelo apagado, em vez de tachado, é erro. Afastamento sem justificativa e
   justificativa sem afastamento são erros.
7. **Compatibilidade:** `{.azul}`, `::: azul` e as chamadas `A/I/E` continuam lidos, com aviso,
   para os repositórios derivados migrarem aos poucos.

Esta decisão substitui os itens 3 (regras de redação: azul e "Suprimido") e 6 (destaque no
documento final) da ADR de 2026-09-29, e altera o item 4 (o despacho continua gerado, agora a
partir do TR). O resto daquela ADR continua valendo.

## Consequências

- `scripts/azul.lua` sai, e entra `scripts/marcas.lua`. `scripts/tr_marcas.py` é o módulo comum
  da conferência, do despacho e do build.
- A conferência ganha as classes `PREENCHIDO`, `TACHADO-FORA-DO-MODELO`, `COR-EXCESSIVA` (antes
  `AZUL-EXCESSIVO`) e `SUPRESSAO-SEM-TACHADO`. Ganha também avisos de semântica (verde sem
  tachado, azul fora de lacuna, `.azul` legado).
- O TR montado traz o texto tachado e as justificativas. Se a equipe precisar de uma versão
  limpa para publicação, isso pede decisão nova.
- Tabelas continuam sem conferência célula a célula.

## Alternativas consideradas

- **Justificativa só no despacho, injetada no TR pelo build.** Rejeitada: o texto ficaria longe
  do item que justifica, contra a recomendação do IPP. Manter dois textos parecidos em lugares
  diferentes é o que se quis evitar.
- **Gerar também uma versão limpa** (sem tachado, cores e justificativas). Adiada: a equipe
  optou só pela versão marcada.
- **Manter "Suprimido" no lugar do tachado.** Rejeitada: o IPP pede o texto original riscado,
  para que o parecerista veja o que saiu.
- **Exigir justificativa também do preenchimento.** Rejeitada: o IPP pede justificativa para
  acréscimos e supressões, e o preenchimento de lacuna é o uso previsto do modelo.
