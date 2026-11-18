---
data: 2026-09-23
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# Registro de fontes do ETP em anexo próprio (Anexo I), gerado em PDF paisagem

## Contexto

A seção `etp/22-referencias-tecnicas.md` trazia, no corpo, uma tabela com as fontes
`F-nn` do Estudo (30, na contratação de origem): identificador, documento, endereço e
data de consulta. No formulário do
ETP no Compras.gov.br, a tabela não ficou bem formatada. Com quatro colunas, endereços
longos e descrições de várias linhas, ela não cabe na largura do editor de texto.

## Decisão

1. **A tabela sai do corpo do ETP** e passa a constituir o **Anexo I do Estudo Técnico
   Preliminar — Registro de fontes técnicas consultadas**, juntado aos autos em arquivo
   próprio. A seção 22 mantém as regras de leitura e de fonte e remete ao Anexo I.

2. **Os dados vão para `etp/fontes.yaml`**, com os campos `id`, `documento`, `endereco`
   e `consulta`, conforme o docs/dados-estruturados.md: tabela grande vai para YAML ao lado. As regras de
   identificador continuam as da seção 22: o identificador é único, não se renumera, e fonte
   nova entra no fim da lista.

3. **O PDF é gerado, não editado**: `scripts/gerar-anexo-fontes.py` lê o YAML e produz
   `etp/anexo-i-registro-de-fontes.pdf`, em A4 paisagem, com o cabeçalho da tabela
   repetido a cada página, endereços clicáveis e numeração "Página X de Y". O script valida
   identificador repetido, campo vazio e data fora do formato DD/MM/AAAA.

4. **Dependência nova: fpdf2 e PyYAML**, instalados em ambiente virtual local
   (`.venv/`, fora do versionamento), sem tocar no Python do sistema:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install fpdf2 pyyaml
   .venv/bin/python scripts/gerar-anexo-fontes.py
   ```

   O ambiente não tinha LaTeX, `wkhtmltopdf`, WeasyPrint nem driver PDF do `groff`. A
   fpdf2 é Python puro e gera a tabela com quebra de linha e fonte embutida. A fonte é a
   DejaVu Sans do sistema.

## Consequências

- O itálico do campo `documento` sai em redondo no PDF, porque o ambiente não tem DejaVu
  Sans itálica. O negrito é preservado.
- O Anexo I **não entra** no `scripts/build.sh`. É artefato próprio, como o despacho do TR.
  Toda alteração em `etp/fontes.yaml` exige regenerar o PDF e juntar a nova versão aos autos.
- As citações `[F-nn]` nas seções do ETP não dependem do anexo: o identificador é estável.

## Alternativas consideradas

- **Manter a tabela no markdown e ajustar só a largura das colunas.** Não resolve o limite do
  editor do Compras.gov.br.
- **Gerar o PDF pelo navegador do Windows (impressão *headless*).** Dependeria de caminho
  fora do repositório e de permissão fora da sandbox. O resultado não seria reproduzível por
  script.
