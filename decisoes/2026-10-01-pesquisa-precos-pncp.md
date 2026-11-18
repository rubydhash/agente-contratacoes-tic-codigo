---
data: 2026-10-01
autores: []
status: aceita  # aceita | aberta | rejeitada
---

# Pesquisa de contratações similares e de preços no PNCP

## Contexto

Em contratação anterior (CDN/WAF), a busca de contratações similares no PNCP foi feita com um `busca.sh` preso a
um único termo (`q=saas`), cookie de navegador fixo, filtro `jq` ad hoc e um
`baixa_arquivos.py` para os documentos. Faltavam a busca por vários termos com eliminação
de duplicatas, a classificação de registro de preços e de adesão, e a ligação com a pesquisa
de preços da IN SEGES/ME nº 65/2021 (arts. 3º, 5º e 6º).

## Decisão

1. **Script único, `scripts/pesquisa-pncp.py`**, com subcomandos `iniciar`, `buscar`,
   `consolidar`, `enriquecer`, `baixar`, `propostas` e `serie`. Usa só a biblioteca padrão
   do Python e o PyYAML, já presente no `.venv/` (ADR de 2026-09-23).
2. **Uma pasta por pesquisa**, `pesquisas/pncp/<slug>/`, **versionada inteira**, inclusive
   as páginas brutas da busca: elas são a evidência datada da consulta (IN 65, art. 3º, III).
   Esquemas:
   - `pesquisa.yaml`: `pesquisa` (slug, data de referência, responsáveis, objetivos, objeto),
     `contratante` (órgão, esfera, poder), `busca` (termos, tipos de documento, status,
     limite de páginas, espera), `filtros` (regex de pertinência e de exclusão, data, esferas,
     janela em meses), `detalhes` (espera) e `cautelas`;
   - `triagem.yaml`: por compra, `decisao` (`pendente | pertinente | nao_pertinente`) e
     `motivo`. O script acrescenta compras e nunca altera decisão já tomada;
   - `serie-precos.yaml`: método (`media | mediana | menor`), limiar de sinalização e
     `precos[]` (`origem: pncp` por chave, item e resultado; `origem: externo` com parâmetro
     do art. 5º, valor, fonte e data), com fatores de conversão e de atualização e exclusão
     que exigem justificativa escrita.
3. **Chave de deduplicação: a compra** (`cnpj/ano/sequencial`). Edital, ata
   (`numero_controle_pncp` sem o sufixo da ata) e contrato (`numero_contratacao`) da mesma
   compra viram uma linha, com a lista de termos e de tipos que a encontraram.
4. **APIs do PNCP sem cookie**, só com User-Agent de navegador (testado em 01/10/2026):
   - busca: `pncp.gov.br/api/search/?q=&tipos_documento=edital|ata|contrato&status=todos`;
     várias palavras funcionam como E lógico, sem acento; entre aspas, frase exata;
   - compra: `api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{seq}` (`srp`, `linkSistemaOrigem`);
   - itens e resultados: `api/pncp/v1/orgaos/{cnpj}/compras/{ano}/{seq}/itens[/{n}/resultados]`
     (vencedor, `valorUnitarioHomologado`, `dataResultado`);
   - atas: `.../atas` e `.../atas/{n}` (vigência, `possibilidadeAdesao`);
   - arquivos: `.../arquivos[/{n}]`.
   - saldo de adesão (fora do PNCP, ver a atualização de 2026-11-05): dados abertos do
     Compras.gov.br, `dadosabertos.compras.gov.br/modulo-arp/`.
5. **Classificações** do `enriquecer`, todas com motivo por escrito:
   - adesão para a esfera do contratante (Lei 14.133, art. 86, §§2º, 3º e 8º):
     `sim | nao_pela_esfera | nao_prevista_na_ata | ata_vencida | sem_ata_publicada |
     nao_srp | indeterminado`;
   - tempestividade (IN 65, art. 5º, II): `em_execucao | dentro_12_meses | fora |
     sem_resultado`, com a data de referência da pesquisa.
6. **Compras.gov.br (cnetmobile): obtenção manual.** O ID da compra no sistema é
   UASG (6) + modalidade (2; `05` = pregão) + número (5) + ano (4), por exemplo
   `070017 05 00213 2026`. As APIs públicas de propostas e anexos
   (`comprasnet-fase-externa/public/v1/compras/{id}/itens/{n}/propostas` e afins) exigem
   token hCaptcha. Sem ele, respondem 204 com o cabeçalho "Não foi possível realizar a
   validação do Captcha". O captcha não será contornado. O script gera
   `propostas-a-obter.md` com o link de cada item, e o usuário salva a proposta em
   `propostas/<id>/item-<n>/`.
7. **A série de preços não exclui valor automaticamente.** O limiar em relação à mediana só
   sinaliza para a análise crítica (art. 6º, §4º); excluir exige motivo escrito (§3º).
   Com menos de três preços válidos, o relatório alerta para o art. 6º, §5º.
8. **O roteiro de condução fica em `skills/pesquisa-precos-pncp/SKILL.md`**, na raiz e
   versionado, em markdown com frontmatter `name`/`description`. É independente de
   ferramenta: agente com suporte a skills o carrega pelo frontmatter, e os demais o leem
   como instrução (docs/pesquisa-pncp.md). Configuração de ferramenta específica não é lugar
   de conteúdo do processo.
9. **`etp/00-metadados.yaml` ganha `orgao.esfera` e `orgao.poder`**, que o `iniciar` usa para
   pré-preencher o contratante. A skill confirma a esfera com o usuário mesmo assim.

## Fora do escopo

- Painel de Preços (art. 5º, I), notas fiscais (inciso V) e cotação direta (inciso IV): entram
  na série como `origem: externo`, coletados fora do script.
- Conversão de PDF em markdown: o conversor usado na contratação de origem dependia de um manifesto do
  caso concreto e não foi trazido.

## Consequências

- Os brutos aumentam o repositório: de 100 a 250 KB por página da busca. `busca.max_paginas`
  limita o volume, e o script avisa quando trunca.
- A busca é ordenada por data. Ao retomar, páginas novas deslocam as antigas. A
  deduplicação absorve as repetições, e `buscar --atualizar` refaz tudo quando a lacuna importar.
- Compra de outro sistema (sem `linkSistemaOrigem` do cnetmobile) não ganha link de item; o
  roteiro indica o sistema de origem.

## Atualização de 2026-10-05 — pausa adaptativa no enriquecimento

Em uma pesquisa de firewall, enriquecer ~500 compras com a pausa padrão de 1–3 s levaria cerca de
7 horas: o PNCP não tem endpoint que traga todos os resultados de uma compra (testado:
`.../itens/resultados` → 400), e cada compra exige de 10 a 30 chamadas, uma por item com
resultado. A pausa fixa respondia por cerca de 70% do tempo.

- **`Cliente` ganhou recuo automático** (`espera_bloqueio`). A primeira falha que indique
  restrição (HTTP 429, 403, 5xx, timeout, falha de rede) eleva a pausa, até o fim da execução,
  ao mínimo configurado. A espera de 60 s antes de repetir a chamada continua.
- **`pesquisa.yaml > detalhes.espera_se_bloqueado`** (opcional, `{min, max}`) liga o recuo.
  Sem ela, o comportamento é o anterior. O modelo gerado por `iniciar` mantém 1–3 s e traz a
  chave comentada.
- **Medido em 05/10/2026:** sem pausa, o PNCP devolveu HTTP 429 depois de cerca de 12 compras.
  Com o recuo para 0,5–1,5 s, não houve nova restrição, a cerca de 10 compras por minuto.
  Para lotes grandes, a pausa de 0,5–1,5 s é o ponto de partida mais realista.

## Atualização de 2026-11-05 — saldo de adesão (`saldo`)

O PNCP informa a ata, a vigência e `possibilidadeAdesao`, mas não o saldo. Em uma pesquisa de firewall,
o saldo de uma ata federal foi conferido à mão, em 09/10/2026, na API de dados abertos do
Compras.gov.br. Em pesquisa posterior, a consulta virou o subcomando `saldo`, levado ao template.

- **Endpoints** (`dadosabertos.compras.gov.br/modulo-arp/`, públicos, sem cookie nem captcha):
  `2.1_consultarARPItem_Id?numeroControlePncpAta=` (itens da ata, a partir do número de controle
  que o `enriquecer` já grava); `3_consultarUnidadesItem` (quantidade registrada por unidade,
  `saldoAdesoes`, `aceitaAdesao`); `5_consultarAdesoesItem` (adesões aprovadas). Os dois últimos
  pedem `numeroAta`, `unidadeGerenciadora` e `numeroItem` com zeros à esquerda (`00001`).
- **Limites.** `saldoAdesoes` é o teto do art. 86, §5º (o dobro do registrado) já descontadas as
  adesões. O limite **por órgão** do §4º (50% do registrado) não vem na API: o script o calcula
  e mostra os dois.
- **Seleção.** Atas vigentes de compras com `adesao: sim`. Por padrão, só os itens cuja descrição
  casa com `pertinencia_regex` (a ata inteira se nenhum casar); `--todos-itens` consulta tudo e
  `--chaves` força compras específicas.
- **Evidência.** Brutos em `pesquisas/pncp/<slug>/atas-saldo/<uasg>-<ata>-<data>/`, versionados
  como os demais (IN 65, art. 3º, III); `atas-saldo.json` e `atas-candidatas.md` são gerados.
- **Conferido em 05/11/2026** contra uma ata federal real: os números são os do registro manual
  de 09/10/2026 (itens 1–2: registrado 4, saldo 6, limite por órgão 2).
- Também testado: `modulo-arp/2_consultarARPItem` filtra por `codigoItem`/`codigoPdm` e por faixa
  de vigência. Ainda não está no script; serve para achar, pelo código de catálogo, atas que a
  busca textual do PNCP não traz.
