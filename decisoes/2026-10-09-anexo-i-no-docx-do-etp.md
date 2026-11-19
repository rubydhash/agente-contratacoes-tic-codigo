---
data: 2026-10-09
autores: ["Neuton Martins"]
status: aceita  # aceita | aberta | rejeitada
---

# Anexo I (registro de fontes) também no docx do ETP, em seção paisagem

> Supera, na parte do build, a consequência "O Anexo I **não entra** no `scripts/build.sh`" de
> `decisoes/2026-09-23-anexo-i-registro-de-fontes.md`. O restante daquele ADR continua valendo.

## Contexto

O ADR de 23/09/2026 tirou a tabela de fontes do corpo do ETP. O motivo era o editor do ETP no
Compras.gov.br, onde quatro colunas com endereços longos não cabem. Por isso o anexo saía só em
PDF.

O `build/ETP.docx`, porém, não é colado no Compras.gov.br. Ele é a base de trabalho e de revisão
da equipe, e quem o lê sem o Anexo I vê citações `[F-nn]` sem a tabela que as resolve.

## Decisão

1. **O `scripts/build.sh etp` acrescenta o Anexo I ao fim do `build/ETP.docx`**, numa seção A4
   em paisagem, com o mesmo texto de abertura e as mesmas colunas do PDF (ID, Documento,
   Endereço, Consulta). Os endereços saem como links.
2. **A fonte única continua sendo `etp/fontes.yaml`.** O novo `scripts/anexo-fontes-docx.py`
   faz duas coisas:
   - `md`: gera o markdown do anexo, com as mesmas validações de `scripts/gerar-anexo-fontes.py`;
   - `paisagem`: ajusta o docx gerado pelo pandoc. Troca um parágrafo-marcador pela quebra de
     seção que encerra o corpo em retrato e põe a última seção em paisagem. Também fixa a largura
     das colunas na proporção do PDF, porque o leitor gfm a ignora, e repete o cabeçalho da
     tabela em cada página.
3. **Página A4 explícita, com margens de 2,5 cm, nas duas seções.** O pandoc deste build não
   grava `sectPr`, e o Word aplicava o tamanho padrão da instalação.
4. **O PDF continua sendo o documento dos autos**, gerado por `scripts/gerar-anexo-fontes.py` e
   juntado em separado. O anexo no docx é cópia para leitura e revisão.

Não há dependência nova: só Python do sistema com PyYAML e a biblioteca padrão (`zipfile`, `re`).

## Consequências

- O ETP que vai ao Compras.gov.br continua sem a tabela: cada capítulo é colado à parte, e o
  anexo não é colado.
- O PDF e a tabela do docx saem do mesmo YAML e não se divergem. O texto de abertura está
  duplicado nos dois scripts, com comentário remetendo um ao outro.
- O ajuste do docx depende da estrutura que o pandoc gera: o marcador num parágrafo e a tabela do
  anexo como a última do documento. Se algo falhar, o script aborta o build com mensagem.

## Alternativas consideradas

- **Anexo em retrato, com colunas estreitas.** É mais simples, mas fica mais apertado que o PDF e
  quebra os endereços em muitas linhas.
- **Filtro Lua com bloco `openxml` cru.** O leitor gfm não lê blocos crus de OpenXML, e o
  `sectPr` final do corpo continuaria fora do alcance do filtro.
