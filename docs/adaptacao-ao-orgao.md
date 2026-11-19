# Adaptação ao seu órgão

O template é neutro: nenhum dado de órgão vem preenchido. O skill
[`iniciar-contratacao`](../skills/iniciar-contratacao/SKILL.md) percorre os pontos abaixo com a
equipe; esta página serve para quem preferir fazer à mão.

## Dados do órgão e do processo

| O quê | Onde |
|---|---|
| Nome, sigla, UASG, esfera, poder | `etp/00-metadados.yaml > orgao` (e `dfd/00-metadados.yaml`) |
| Áreas requisitante, de TIC e administrativa | `etp/00-metadados.yaml > orgao` |
| Número do processo, data de abertura | `etp/00-metadados.yaml > processo` |
| Equipe de planejamento e autoridade máxima de TIC | `etp/00-metadados.yaml > equipe_planejamento` |
| Objeto curto e descrição pública | `etp/00-metadados.yaml > contratacao` (genéricos, sem marca) |
| Data de início | `MANIFEST.yaml > projeto.data_inicio` |

A **esfera** importa: ela define a adesão cabível a atas de registro de preços (Lei 14.133,
art. 86, §§3º e 8º) e é lida pela pesquisa no PNCP.

## Planejamento institucional (PDTI, PCA, PEI)

1. Coloque o PDF do PDTI (e do PEI, se houver) em `referencia/normativos-orgao/`.
2. Converta para consulta por grep:

   ```bash
   python3 scripts/ler-pdf.py texto referencia/normativos-orgao/<pdti>.pdf -o referencia/normativos-md/pdti-<sigla>-<vigencia>.md
   ```

3. Preencha `normativos/planejamento-institucional-checklist.yaml`:
   - versão;
   - tema principal;
   - objetivos e resultados-chave;
   - macroações;
   - itens orçamentários;
   - onde cada elemento aparece no ETP/TR.
4. Preencha `etp/00-metadados.yaml > planejamento_vinculo` (PDTI, PCA, PEI).
5. Se o objeto **não** estiver nominalmente previsto no PDTI, abra uma ADR com `status: aberta`.
   Ela registra as alternativas:
   - enquadrar em item existente;
   - suplementar;
   - revisar o PDTI.

   O `scripts/validar.sh` vai lembrar dela até que seja resolvida.

## Modelo AGU

O template vem com o **Modelo AGU de TR de Serviços de TIC (abr/2026)**. Para usar outro modelo
(por exemplo, compras de TIC):

1. Coloque o docx em `referencia/modelos-agu/`.
2. Troque `MODELO_REL` e `MODELO_NOME` no topo de `scripts/conferir-modelo-agu.py`.
3. Converta o modelo (`scripts/converter-docx.sh`) e gere a referência numerada
   (`python3 scripts/conferir-modelo-agu.py --numerado`).
4. Reorganize `tr/` conforme os capítulos do novo modelo e registre a mudança em ADR.

Para que o build preserve fontes e margens da AGU, copie o docx do modelo para
`templates/agu-referencia.docx`.

## SEI

- **Documento-base:** `templates/sei/documento-base.html` traz as classes de estilo padrão do
  editor do SEI e um cabeçalho com placeholders (nome do órgão, endereço, sítio). O cabeçalho só
  aparece na pré-visualização; no SEI, o timbre vem do próprio sistema. Não renomeie as classes.
- **Despacho de justificativa:** preencha as constantes do topo de `scripts/gerar-despacho.py`:
  - `UNIDADE_SIGLA` e `UNIDADE_NOME`;
  - `PROCESSO_SEI`;
  - `TR_NUMERO`;
  - `OBJETO`;
  - `ARTEFATOS`;
  - `SIGNATARIO_NOME` e `SIGNATARIO_CARGO`.
- **Listas de verificação:** `orgao` e `signatario` no YAML de cada lista.
- Se o órgão não usa o SEI, os HTMLs continuam úteis para colar em outro editor rico, e o
  conteúdo canônico continua no markdown.

## Índice de reajuste: ICTI

A IN 94 (art. 24) torna obrigatório o **Índice de Custos de Tecnologia da Informação (ICTI)**,
mantido pelo Ipea, nos serviços de TIC com reajuste. A menção aparece no texto literal da IN, do
modelo AGU e de `tr/08-criterios-medicao-pagamento.md`, e não deve ser removida.
