---
data: 2026-11-19
status: aceita
autores: ["Neuton Martins"]
---

# Anexos do TR em markdown, com PDF gerado a cada build

## Contexto

O modelo AGU de TR de TIC remete a anexos que o próprio órgão redige, como o Termo de Compromisso
de Manutenção de Sigilo e o Termo de Ciência (IN SGD/ME 94/2022, art. 18, V, "a" e "b"). Em duas
contratações anteriores de TIC, uma de serviços e outra de aquisição, a equipe redigiu esses anexos
no repositório, e o mesmo script de PDF serviu às duas.

## Decisão

1. Anexo redigido no repositório tem fonte em `tr/ANEXO <romano> - <nome>.md`.
2. `scripts/gerar-anexos-tr.py` converte todo `tr/ANEXO *.md` em `build/<mesmo nome>.pdf` (A4, com
   fpdf2). Lê um subconjunto fixo de markdown, descrito no próprio script: títulos `#` e `##`,
   parágrafos com `**negrito**`, tabelas pipe e a diretiva `<!--tabela larguras=A,B,...-->`. O
   cabeçalho de página leva `orgao.nome` e `orgao.sigla` de `etp/00-metadados.yaml`.
3. O `scripts/build.sh` ganha o alvo `anexos-tr`, e os alvos `tr` e `all` passam a gerar os anexos.
4. Anexo recebido em docx (ex.: Termo de Compromisso, de modelo do Gov.Digital) fica em docx, em
   `tr/`, sem conversão.
5. Só vira anexo o que o TR cita. Em contratação de aquisição, o modelo de ordem de fornecimento
   não foi anexado: nem o modelo AGU de Compras nem a licitação de referência o previam.

## Consequências

- O PDF é saída de build, não versionada. Edita-se o markdown, nunca o PDF.
- O fpdf2 só é importado quando há `tr/ANEXO *.md`: o TR sem anexos continua montando sem ele.
- O fpdf2 vem do `.venv` e a fonte DejaVu é localizada por `scripts/_ambiente.py`
  (`decisoes/2026-11-19-dependencias-no-venv.md`).
- Timbre, cadastro no SEI e assinaturas são aplicados à mão, como nos demais artefatos.
- Registre cada anexo no `MANIFEST.yaml` (`sections_tr`, `tipo: artefato-proprio`, com
  `gerado_por` nos anexos em markdown).
