---
data: 2026-11-06
autores: ["Neuton Martins da Costa"]
status: aceita  # aceita | aberta | rejeitada
---

# Checklist da IN 94 passa a cobrir os Anexos I e II

## Contexto

`normativos/in94-checklist.yaml` cobria os arts. 5º, 11, 12 e 16 da IN SGD/ME nº 94/2022, mas não
os anexos. Na contratação de origem, isso teve duas consequências:

- **Anexo II:** o enquadramento indicava uma categoria que só lista serviços (1.12) para um objeto
  de bens.
- **Anexo I:** as diretrizes dos itens 1, 7 e 8 não eram conferidas. O item 8.3 remete à Portaria
  Inmetro nº 170/2012, revogada pela Portaria Inmetro nº 304/2023 (art. 4º, I).

## Decisão

1. **Duas chaves novas no checklist.**
   - `anexo_ii.enquadramento`;
   - `anexo_i`, com `licenciamento_software` (item 1), `seguranca_informacao_privacidade`
     (item 7) e `aquisicao_ativos_tic` (item 8).
   - Os itens 2 a 6 entram quando o objeto os tocar.
2. **Campo novo `aplica_se`** em entradas do Anexo I. Diz em que objeto a diretriz incide. É texto
   livre, e o `scripts/validar.sh` não o lê.
3. **Regulamento do Inmetro:** a referência é a vigente (Portaria nº 304/2023, alterada pela
   nº 211/2026). A remissão da IN à Portaria nº 170/2012 fica registrada no campo `fonte`.
4. **Fontes arquivadas** em `referencia/normativos/`, com `SHA256SUMS`, e extraídas para
   `referencia/normativos-md/` quando citadas por artigo:
   - Portarias Inmetro nºs 304/2023, 211/2026 e 170/2012 (revogada);
   - Decreto nº 7.174/2010;
   - Orientação Normativa SLTI nº 1/2015;
   - Guia de Requisitos e Obrigações SIP v3.2. O gov.br devolveu 404 em 06/11/2026; a cópia é do
     TCE-PB, marcada como espelho não oficial;
   - Guia do Framework PPSI 2.0 v1.2.

## Consequências

- O `scripts/validar.sh` continua só validando o YAML. A conferência das chaves novas é do
  revisor, como as demais.
- **Lições da aplicação na contratação de origem:**
  - firewalls e equipamentos de rede não constam do Anexo A da Portaria Inmetro nº 304/2023;
  - o PPB é preferência (Decreto 7.174, arts. 5º e 8º), não condição de participação;
  - na adesão, o que a ata não prevê (origem dos importados, sanções de SIP, declaração de
    registro de oportunidade) vai para o aceite, a ordem de fornecimento e o contrato.
