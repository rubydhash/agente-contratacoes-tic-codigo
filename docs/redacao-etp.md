# Redação do DFD e do ETP

## DFD

`dfd/01-dfd.md` reproduz os campos do formulário do Documento de Formalização da Demanda no
PGC/Compras.gov.br (Decreto 10.947/2022, art. 8º; IN 94, art. 10, §1º). Os metadados próprios do
DFD ficam em `dfd/00-metadados.yaml`. ADR:
[`2026-09-29-dfd-e-etp-numeracao-etp-digital.md`](../decisoes/2026-09-29-dfd-e-etp-numeracao-etp-digital.md).

## ETP: um arquivo por capítulo do ETP Digital

Cada arquivo de `etp/` é **um capítulo do ETP Digital do Compras.gov.br**, com o número e o nome
do modelo de ETP de TIC da SGD (v1.2, em `templates/govdigital-etp.md`):

- **01 a 17**: iguais ao modelo.
- **18 (parcelamento), 19 (impactos ambientais) e 20 (registro de fontes)**: capítulos
  acrescidos, porque a Lei 14.133 exige o conteúdo (art. 18, §1º, VIII e XII) e o modelo não os
  destaca.
- **21 e 22**: declaração de viabilidade e responsáveis, que correspondem aos capítulos finais
  do modelo.

ADR: [`2026-10-01-etp-capitulos-modelo-sgd.md`](../decisoes/2026-10-01-etp-capitulos-modelo-sgd.md).

### Numeração

- **Todo item começa pelo número do capítulo.** No capítulo 3, o primeiro item é `**3.1. …**`,
  seguido de `3.1.1.` e `3.1.1.1.`. Nunca `1.` ou `1.1`. O primeiro nível vai em negrito.
- No capítulo 21, o texto fica dentro do subcampo fixo `21.1. Justificativa da Viabilidade` e
  começa em `21.1.1`.
- A remissão entre capítulos usa o número completo ("conforme o item 7.4").
- O `scripts/validar.sh` acusa como `ERRO`:
  - item fora da numeração;
  - título `# N.` divergente;
  - `capitulo` do frontmatter diferente do prefixo do arquivo.

### Convenções de texto

- O frontmatter é obrigatório. Campo que não se aplica fica vazio (`""` ou `[]`), nunca removido.
- Nada de tabelas grandes em markdown: dado estruturado vai para YAML ao lado
  (veja [Dados estruturados](dados-estruturados.md)).
- Notas de redator em `<!-- … -->` são bem-vindas no rascunho e somem antes de `aprovado`.
- O bloco "O que esta seção precisa cobrir", no topo de cada arquivo, é orientação. Apague-o
  antes do build final.
- **O objeto é genérico quanto ao produto.** A solução escolhida aparece no capítulo 12 e é
  fundamentada no 14. Nomear marca no objeto, antes do estudo, dá margem à leitura de
  direcionamento.

### Campo de parcelamento no sistema

No Compras.gov.br, os capítulos acrescidos (18 a 20) não existem. O capítulo 7 do ETP Digital
tem o campo "Contratação de mais de uma solução de TIC em um único grupo": é ali que vai o
fundamento do parcelamento (Lei 14.133, art. 18, §1º, VIII, obrigatório pelo §2º).

## Registro de fontes e Anexo I

Toda afirmação sobre capacidade técnica, licenciamento ou preço que se apoie em documento externo
cita a fonte pelo identificador entre colchetes, `[F-nn]`, no ponto da afirmação.

- As fontes ficam em `etp/fontes.yaml`, com os campos `id`, `documento`, `endereco` e `consulta`
  (data em DD/MM/AAAA).
- O capítulo `etp/20-registro-fontes.md` traz só as regras de leitura.
- O **Anexo I** é gerado em PDF A4 paisagem e juntado aos autos em separado (a tabela não cabe no
  editor do sistema):

  ```bash
  .venv/bin/python scripts/gerar-anexo-fontes.py   # → etp/anexo-i-registro-de-fontes.pdf
  ```

- `scripts/build.sh etp` também acrescenta o anexo ao fim do `build/ETP.docx`, em seção paisagem,
  para revisão. O documento dos autos é o PDF.

Regras:

- **Identificador não se renumera.** Fonte nova entra no fim; fonte que deixou de ser citada
  permanece.
- **Registro único, por documento**, nunca uma tabela por seção. Tabelas por seção reiniciam em
  F-1 e duplicam identificadores no documento juntado.
- **Fonte que aparece só na prosa ganha identificador.**
- **Contratação de outro órgão se cita por pregão/ano, UASG e endereço no PNCP.** Confira o
  número: a numeração interna do órgão pode divergir da do PNCP; quando divergir, registre as
  duas.
- **Capacidade de produto se prova com documento do fabricante.** Recurso ausente da matriz
  publicada é dito como tal. Preço sem fonte formalizada não entra em comparação.

ADRs: [`2026-09-23-anexo-i-registro-de-fontes.md`](../decisoes/2026-09-23-anexo-i-registro-de-fontes.md)
e [`2026-10-09-anexo-i-no-docx-do-etp.md`](../decisoes/2026-10-09-anexo-i-no-docx-do-etp.md).

## Fontes em PDF sem texto

Impressões de e-mail e digitalizações não têm camada de texto. A leitura visual é possível
(veja [Ferramentas](ferramentas.md#pdfs-sem-camada-de-texto)), mas **o que se lê de imagem não é
citável diretamente**:
- transcreva os dados para `anotacoes/AAAA-MM-DD-assunto.md`, com fonte, aviso de leitura visual
  e instrução de conferir o original;
- a seção cita a nota.

## Compatibilidade com matriz de fabricante

Quando a solução depende de suporte a sistemas operacionais ou plataformas específicas:

1. **Consulte a matriz na fonte viva do fabricante e registre a data.** Matrizes mudam nos dois
   sentidos: retiram versões antigas e demoram a incluir as novas.
2. **Confira também o repositório de pacotes do fabricante.** Pode haver agente em canal de
   produção para uma versão que a documentação ainda não lista. "Não há produto" e "a
   documentação está atrasada" levam a classificações diferentes. Fórum de comunidade é indício,
   nunca fundamento.
3. **Cruze mais de uma fonte de inventário** quando houver. A informação do agente em execução
   tem precedência sobre a etiqueta de catálogo, e a divergência é achado a registrar.
4. Classifique a cobertura nos estados de [Dados estruturados](dados-estruturados.md) e isole as
   zonas cegas, com o motivo de cada uma.
5. Registre a conferência como **evidência datada**.
6. Fim de suporte do fornecedor do sistema operacional não é ausência de cobertura pela solução.
   São eixos distintos.
