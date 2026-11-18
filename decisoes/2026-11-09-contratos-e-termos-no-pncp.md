---
data: 2026-11-09
autores: ["Neuton Martins da Costa"]
status: aceita  # aceita | aberta | rejeitada
---

# Contratos e termos aditivos no `pesquisa-pncp.py`

## Contexto

Na contratação de origem, o ETP justificou não contratar operação nem SOC pelo contrato de
sustentação vigente do órgão. Para afirmar o objeto e a vigência foi preciso consultar o PNCP à mão.
O registro do contrato no PNCP mostrava a vigência do termo inicial, já vencida; só os termos do
contrato mostravam o 1º Termo Aditivo, que prorrogava a vigência.

O script só tratava compras e atas. A consulta de contratos tem duas armadilhas:

- a API `consulta/v1/contratos` filtra por data de publicação e recusa período maior que 365 dias
  (HTTP 422);
- a vigência do contrato no PNCP é a do termo inicial; aditivo, apostilamento e rescisão ficam em
  `pncp/v1/orgaos/{cnpj}/contratos/{ano}/{seq}/termos`.

## Decisão

1. **Comando `contrato`**, que não depende de pesquisa (slug). Aceita:
   - o número de controle da compra (`-1-`) ou do contrato (`-2-`);
   - o link do app do PNCP (`/app/editais/...` ou `/app/contratos/...`);
   - `cnpj/ano/seq` da compra;
   - ou `--orgao <CNPJ> --texto <regex>` (com `--desde`), para achar contratos de um órgão pelo
     objeto ou pelo fornecedor.
2. **Da compra ao contrato:** busca os contratos do órgão desde a publicação da compra, em janelas de
   365 dias, e fica com os de `numeroControlePncpCompra` igual ao da compra.
3. **Por contrato:** contrato, termos, lista de arquivos do contrato e de cada termo; com
   `--documentos`, baixa os arquivos.
4. **Vigência atual:** a maior data de fim entre o termo inicial e os termos; rescisão prevalece.
   Com `--ate`, o resumo diz se a vigência cobre a data exigida (por exemplo, o fim da garantia).
5. **Saída** em `--saida` (obrigatório): brutos, `registro.json`, `resumo.md` (com sugestão de
   entrada para `etp/fontes.yaml`) e `SHA256SUMS`. Convenção: contrato do próprio órgão em
   `referencia/contratacoes-proprias/<assunto>/pncp-<data>/`; de outro órgão, em
   `referencia/contratacoes-outros-orgaos/`.
6. **Sem dependência nova:** biblioteca padrão e o cliente HTTP do script.

## Consequências

- Vigência vencida no resumo não prova contrato encerrado: aditivo pode não estar publicado. O
  resumo avisa, e a skill manda conferir no SEI antes de afirmar no ETP.
- Receita na skill `skills/pesquisa-precos-pncp/SKILL.md`, seção 9, e no `docs/pesquisa-pncp.md`.
