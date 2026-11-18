---
data: 2026-11-06
autores: ["Neuton Martins da Costa"]
status: aceita  # aceita | aberta | rejeitada
---

# Painel de Preços e atas por código de catálogo no `pesquisa-pncp.py`

> Supera, quanto ao Painel de Preços, o item de `decisoes/2026-10-01-pesquisa-precos-pncp.md` que o
> deixava fora do script ("entram como `origem: externo`").

## Contexto

A busca do PNCP é textual: depende das palavras do objeto. Em contratação anterior de firewall, ela perdeu
duas atas federais decisivas, uma delas a que embasou a adesão. As duas só apareceram pela
consulta por código de catálogo na API de dados abertos do Compras.gov.br.

O Painel de Preços (IN SEGES/ME nº 65/2021, art. 5º, I) é parâmetro prioritário (§1º) e não era
consultado. A mesma API tem o módulo `modulo-pesquisa-preco`, que é a base do Painel e é pública,
sem captcha.

## Decisão

1. **Comando `atas-catalogo <slug>`.**
   - Consulta `modulo-arp/2_consultarARPItem` por `codigoPdm` (PDM) ou `codigoItem` (CATMAT ou
     CATSER), com vigência inicial a partir de `vigencia_inicial_meses`.
   - Lista as atas vigentes e marca as ainda não avaliadas.
   - Saída: `atas-arp/<data>/` (brutos, `registro.json`, `atas-catalogo.md`).
2. **Comando `painel <slug>`.**
   - Consulta `modulo-pesquisa-preco`:
     - material: `1_consultarMaterial` com `tipo=codigoPdm|codigoItemCatalogo` e `codigo`; só o
       código devolve 404;
     - serviço: `3_consultarServico` com `codigoItemCatalogo`.
   - Saída: `painel-precos/<data>/` com:
     - brutos e `registro.json`;
     - `painel.json`;
     - `painel.md`, com estatísticas por código na janela da pesquisa (mediana, quartis, CV), o
       recorte por modelo (`marca_regex`) e as compras na janela ainda não avaliadas.
3. **Seção `catalogo` no `pesquisa.yaml`:** `pdm_material`, `catmat`, `catser`, `painel_catser`,
   `marca_regex`, `texto_regex` e `vigencia_inicial_meses`. Com `painel_catser`, o Painel consulta
   só os CATSER listados. Códigos amplos, como o 27502 (licença de software), têm cerca de 15 mil
   preços.
4. **"Já avaliada"** é a compra que está no consolidado ou no classificado da busca do PNCP, ou que
   tem detalhe em `detalhes/`.
   - **No Painel:** o `idCompra` vem sem o zero à esquerda da UASG, e o script o completa com zeros
     para chegar aos 17 dígitos.
   - **Nas atas:** a chave PNCP sai de `numeroControlePncpCompra`.
5. **Sem dependência nova:** só biblioteca padrão e o cliente HTTP do script, com pausa adaptativa.

## Consequências

- **Rotina:** toda pesquisa passa a consultar a busca textual do PNCP, as atas por catálogo e o
  Painel. O relatório da pesquisa de preços relata o Painel com números, mesmo quando não o usa
  como parâmetro.
- **Lições do caso de origem**, registradas na skill:
  - o CV do código de catálogo passa de 300%, por misturar portes e preços com e sem licença;
  - o campo de marca do Painel pode divergir da ata (FG-200F apareceu como FG-200G);
  - `aceitaAdesao` não reflete restrição de adesão do edital.
- **Versionamento:** os brutos são versionados como evidência datada (IN 65, art. 3º, III).
- **Ferramental do repositório de origem que não veio para o template:** um script de cruzamento
  de vazão e preços, específico do estudo de dimensionamento daquele firewall.
  - lista das exclusões com o motivo;
  - rótulo "abaixo da classe mínima" separado de "indeterminado".
