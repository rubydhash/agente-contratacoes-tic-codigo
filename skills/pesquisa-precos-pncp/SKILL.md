---
name: pesquisa-precos-pncp
description: Conduz a pesquisa de contratações similares no PNCP para o ETP. Define com o usuário o objetivo, os termos, os filtros, a esfera do contratante e as cautelas; busca por vários termos (status=todos), consolida sem duplicatas, faz a triagem, classifica registro de preços, adesão e tempestividade (IN SEGES/ME 65/2021, art. 5º, II; Lei 14.133, art. 86), consulta o Painel de Preços e as atas vigentes por código de catálogo (API de dados abertos do Compras.gov.br), o saldo de adesão das atas vigentes (art. 86, §§4º e 5º), gera o roteiro de propostas do Compras.gov.br e a série de preços (art. 6º), e consulta contratos, termos aditivos e vigência atual no PNCP. Use quando o usuário pedir referências de outros órgãos, pesquisa de preços, contratações similares, preços praticados, atas para adesão ou dados de um contrato (objeto, vigência, aditivos).
---

# Pesquisa de contratações similares e de preços no PNCP

Roteiro para conduzir, **com o usuário**, uma pesquisa no PNCP que sirva ao ETP: referência
técnica para os capítulos 8 a 12, série de preços para o capítulo 13 e `etp/tco.yaml`, e
avaliação de atas para adesão. Ferramenta: `scripts/pesquisa-pncp.py`. Regras do repositório:
`docs/pesquisa-pncp.md`; esquemas: `decisoes/2026-10-01-pesquisa-precos-pncp.md`.

Pré-requisito: onboarding feito (`skills/iniciar-contratacao`), com o objeto e `orgao.esfera`
preenchidos em `etp/00-metadados.yaml`.

Cada etapa termina numa **parada**: mostre o resultado ao usuário e só siga com o aval dele.
Não escolha termo, não descarte compra e não fixe preço por conta própria.

## 0. Reconhecimento

1. `git status` e `git diff` (docs/fluxo-de-trabalho.md). Se houver pesquisa em andamento em
   `pesquisas/pncp/`, leia o `pesquisa.yaml` e o `triagem.yaml` dela antes de propor algo.
2. Leia `etp/00-metadados.yaml`: objeto, órgão, `orgao.esfera`. Se o objeto ainda tiver
   `<preencher>`, peça a descrição ao usuário. Os termos dependem dela.

## 1. Esfera do contratante — pergunte sempre

Pergunte a esfera (federal, estadual, distrital, municipal) e o poder, sugerindo o valor de
`orgao.esfera`. Explique o efeito em uma linha. Base: Lei 14.133, art. 86,
conferida em `referencia/normativos-md/lei-14133-2021.md`.

- **federal**: só adere a ata de gerenciador federal (§8º);
- **estadual/distrital**: adere a ata federal, estadual ou distrital (§3º, I);
- **municipal**: adere também a ata municipal, se o SRP foi formalizado por licitação (§3º, II).

A esfera não restringe a **série de preços**: contratação de qualquer esfera vale como
parâmetro do art. 5º, II, da IN 65. Ela restringe só a **adesão**.

## 2. Objetivo, termos e filtros — `iniciar`

```bash
python3 scripts/pesquisa-pncp.py iniciar <slug>     # slug curto: waf-cdn-2026, firewall-2026
```

Preencha `pesquisas/pncp/<slug>/pesquisa.yaml` **com o usuário**:

- `objetivos`: `referencia_tecnica`, `serie_precos` e/ou `adesao`;
- `descricao_objeto` (IN 65, art. 3º, I) e `responsaveis` (art. 3º, II);
- `termos`: proponha uma lista de sinônimos, siglas, grafias e termos em inglês usados em
  editais, e o usuário escolhe. Na busca do PNCP, várias palavras funcionam como **E**
  (sem acento e sem palavras vazias); entre aspas, é **frase exata**. Termo genérico
  ("firewall", "saas") traz milhares de resultados: combine com `max_paginas` ou refine.
  Marca ou fabricante só entra como termo com justificativa (risco de direcionamento) e,
  quando entrar, serve para achar preço, não para descrever o objeto;
- `tipos_documento`: `edital` e `ata` por padrão; `contrato` acrescenta contratações diretas e
  vigências;
- `pertinencia_regex` / `exclusao_regex`: rede fina sobre título e objeto, depois da busca
  ampla. Teste a regex mentalmente contra dois ou três objetos reais;
- `data_referencia`: data-base da pesquisa (vazio = hoje).

Leia em voz alta as `cautelas` do modelo e acrescente as do caso, como grupo ou lote,
moeda estrangeira, unidade de medida, subscrição anual ou mensal e porte. **Parada.**

## 3. Busca — `buscar`

```bash
python3 scripts/pesquisa-pncp.py buscar <slug>      # retomável; espera 10–20 s entre páginas
```

Sempre `status=todos`, para incluir encerradas, revogadas e suspensas. Rode em segundo plano
se houver muitas páginas. Se o script avisar **busca TRUNCADA**, diga isso ao usuário: o
resultado não é exaustivo.

## 4. Consolidação e triagem — `consolidar`

```bash
python3 scripts/pesquisa-pncp.py consolidar <slug>
```

Relate: compras distintas, quantas passam no filtro, compras por termo e quantas só aquele
termo achou. Termo que não acha nada exclusivo é redundante; termo que só traz ruído pede
exclusão ou regex. **Parada.**

Triagem em `triagem.yaml`: leia os objetos e **proponha** `pertinente`/`nao_pertinente`
com motivo curto. Compra pertinente tem objeto comparável, não apenas a mesma palavra. O
usuário decide. Grave só o que ele aprovar. Compra revogada, anulada ou deserta não se
descarta pelo status: o motivo diz por que sai, ou ela fica como referência técnica.
**Parada.**

## 5. Enriquecimento — `enriquecer`

```bash
python3 scripts/pesquisa-pncp.py enriquecer <slug>
```

Relate **sempre os dois números** de cada eixo:

- tempestividade (IN 65, art. 5º, II): `em_execucao` + `dentro_12_meses` × `fora` /
  `sem_resultado`;
- adesão para a esfera informada: `sim` × os demais estados, com o motivo predominante;
- itens com preço homologado.

`adesao: sim` significa só que os documentos são compatíveis. A adesão ainda depende de
justificativa da vantagem, compatibilidade de preços (art. 86, §2º, I e II), anuência do
gerenciador e do fornecedor (§2º, III) e dos limites dos §§4º e 5º. Diga isso ao usuário.
Para a vantagem da adesão, a IN 65 se aplica (art. 1º, §3º).

### Saldo de adesão — `saldo`

Se o objetivo inclui `adesao`, consulte o saldo das atas vigentes com `adesao: sim`. O PNCP não
informa saldo. O script lê a API de dados abertos do Compras.gov.br (`modulo-arp`, pública e sem
captcha):

```bash
python3 scripts/pesquisa-pncp.py saldo <slug>       # → atas-saldo/, atas-saldo.json, atas-candidatas.md
python3 scripts/pesquisa-pncp.py saldo <slug> --chaves <cnpj/ano/seq>   # uma compra específica
```

Por padrão, só entram os itens cuja descrição de catálogo casa com `pertinencia_regex`; se
nenhum item casar, entra a ata inteira. `--todos-itens` consulta todos. Relate os **dois
números**: itens com saldo, aceite e vigência × os demais. Para cada item, mostre o **saldo de
adesões** que a API informa (teto do §5º, o dobro do registrado) e o **limite por órgão**, que
é 50% do registrado (§4º) e é calculado pelo script, porque a API não o informa. Item com ⚠ tem
descrição de catálogo genérica e precisa ser conferido na ata. Saldo é retrato do dia: antes de
oficiar o gerenciador, rode `saldo` de novo. Os brutos em `atas-saldo/` são a evidência datada.
**Parada.**

### Busca por código de catálogo — `atas-catalogo` e `painel`

A busca textual do PNCP perde compras: depende das palavras do objeto. Em contratação anterior
de firewall, a ata que embasou a adesão e uma ata federal com os mesmos produtos só apareceram pela
consulta por código de catálogo. Preencha `catalogo` no `pesquisa.yaml` com o usuário:
- `pdm_material`: PDM do objeto, por exemplo 18374 (FIREWALL);
- `catmat` e `catser`: códigos específicos;
- `marca_regex`: modelos de interesse;
- `texto_regex`: filtro de descrição para CATSER amplos;
- `painel_catser`: limita os serviços consultados no Painel.

Depois rode:

```bash
python3 scripts/pesquisa-pncp.py atas-catalogo <slug>  # → atas-arp/<data>/atas-catalogo.md
python3 scripts/pesquisa-pncp.py painel <slug>         # → painel-precos/<data>/painel.md e painel.json
```

- **`atas-catalogo`:**
  - consulta `modulo-arp/2_consultarARPItem` por PDM ou código;
  - lista as atas vigentes e marca as que ainda não foram avaliadas, ou seja, que não estão na
    busca do PNCP nem em `detalhes/`.

  Para cada federal pertinente:
  - leia a cláusula de adesão do edital. `aceitaAdesao` da API não reflete restrição a categorias
    de órgão; no caso de origem, uma ata só admitia o Judiciário;
  - rode `saldo --chaves <chave>`;
  - em grupo, confira o menor preço do vencedor em cada item (Parecer Referencial AGU 00002/2026,
    itens 84 a 88).
  - unidade indivisível: item com uma unidade registrada tem limite por órgão de meia unidade, e o
    remanejamento pelo gerenciador não afasta o limite (Decreto 11.462/2023, art. 30, §3º).
- **`painel`:** é a base do Painel de Preços (art. 5º, I).
  - O endpoint de material exige `tipo=codigoPdm` ou `codigoItemCatalogo` e `codigo`; só o código
    devolve 404. O script já faz isso.
  - A mediana do código costuma misturar portes e preços com e sem licença, com CV acima de 300% no
    caso de origem. Relate o CV e use o recorte por modelo.
  - O campo de marca do Painel é declarado pelo fornecedor e pode divergir da ata: um FG-200F
    apareceu como FG-200G. Confirme no edital, no TR ou na proposta antes de usar.
- **Compra nova:** se aparecer compra nova pertinente, baixe o detalhe (`enriquecer --chaves`) e
  peça ao usuário edital, TR e proposta.
- **Justificativa:** se o Painel não servir como parâmetro, a justificativa vai ao relatório da
  pesquisa (art. 5º, §1º), com os números do `painel.md`.

**Parada.**

Documentos do PNCP das compras pertinentes, se o usuário quiser lê-los:

```bash
python3 scripts/pesquisa-pncp.py baixar <slug>      # → referencia/contratacoes-outros-orgaos/
```

## 6. Propostas do Compras.gov.br — obtenção manual

As páginas públicas de propostas e anexos do Compras.gov.br exigem **captcha**. Não tente
contorná-lo, nem por API, nem por automação. Mostre `propostas-a-obter.md` ao usuário: para
cada item há o link do Compras.gov.br, o vencedor, o valor homologado e a pasta de destino.
Ele abre o item, ignora as propostas desclassificadas, baixa a da adjudicada (em geral um PDF
ou ZIP com "proposta" no nome) e salva na pasta. Depois:

```bash
python3 scripts/pesquisa-pncp.py propostas <slug>
```

A proposta serve para conferir marca, modelo, prazo, garantia e condições comerciais
(IN 65, art. 4º). O que for lido nela vai para uma nota em `anotacoes/` antes de ser citado
(docs/ferramentas.md). Proposta escaneada segue a receita de PDF sem texto.

## 7. Série de preços — `serie`

```bash
python3 scripts/pesquisa-pncp.py serie <slug>       # 1ª vez: gera serie-precos.yaml com os candidatos
```

Com o usuário, em `serie-precos.yaml`:

- manter só preços de item **comparável**, na mesma unidade. Use `fator_conversao` com
  `memoria_conversao` para anual→mensal, lote→unidade etc.;
- `fator_atualizacao` com `fonte_atualizacao` quando houver índice (art. 5º, II);
- preços de fora do PNCP, como cotação ou sítio especializado, entram como `origem: externo`.
  O Painel de Preços (art. 5º, I) tem prioridade (§1º): consulte-o com `painel`. Se ele não servir
  como parâmetro, a justificativa vai aos autos com os números do `painel.md`;
- exclusão só com `motivo_exclusao` fundamentado (art. 6º, §3º). O limiar só **sinaliza**,
  e quem exclui é o usuário;
- `metodo`: média, mediana ou menor valor (art. 6º), escolhido pelo usuário.

Rode `serie` de novo e mostre `serie-precos.md`. Com menos de três preços válidos, aponte o
art. 6º, §5º. **Parada.**

## 8. Levar ao ETP

Proponha, **como diff e sem aplicar**:

- entradas em `etp/fontes.yaml` para cada compra usada. O `serie-precos.md` traz a sugestão;
  o identificador `F-nn` é o próximo livre, e fonte nova entra no fim (docs/redacao-etp.md);
- texto para `etp/13-estimativa-custo-total.md` (13.1 método e parâmetros; 13.2 composição e
  memória), remetendo à série e citando `[F-nn]`;
- linhas de `etp/tco.yaml` com `fonte` preenchida;
- compras usadas como referência técnica nos capítulos 8 e 9, citadas por pregão/ano, UASG e
  endereço no PNCP (docs/redacao-etp.md).

## 9. Contratos e termos aditivos — `contrato`

Use quando o ETP precisa afirmar objeto, valor ou vigência de um contrato: contrato correlato do
próprio órgão (por exemplo, o de sustentação que torna desnecessário contratar operação), contrato
de outro órgão usado como referência, ou o contrato resultante de uma compra da pesquisa. Não
depende de slug.

```bash
S=scripts/pesquisa-pncp.py
python3 $S contrato 33892175000100-1-000004/2025 --saida <pasta>      # compra → contratos dela
python3 $S contrato https://pncp.gov.br/app/contratos/<cnpj>/<ano>/<seq> --saida <pasta> --documentos
python3 $S contrato --orgao <CNPJ> --texto "sustentacao|suporte" --desde 2025-01-01 --saida <pasta>
python3 $S contrato <alvo> --saida <pasta> --ate 2031-12-31          # a vigência cobre esta data?
```

- **Pasta:** contrato do próprio órgão em `referencia/contratacoes-proprias/<assunto>/pncp-<AAAA-MM-DD>/`; de
  outro órgão, em `referencia/contratacoes-outros-orgaos/`. A saída traz brutos, `registro.json`,
  `resumo.md` e `SHA256SUMS`.
- **Vigência:** o campo de vigência do contrato no PNCP é o do termo inicial. A vigência atual sai
  dos termos (aditivo, apostilamento, rescisão), e o `resumo.md` a calcula. Se o resumo der
  vigência vencida, não afirme que o contrato acabou: o aditivo pode não estar publicado. Confira no
  SEI ou com a gestão do contrato.
- **Prazo da solução:** com `--ate` (por exemplo, o fim da garantia de 60 meses), o resumo diz se o
  contrato cobre o período. Se não cobre, o ETP diz que a cobertura depende de prorrogação ou de
  contrato sucessor.
- **Número do contrato:** o número do órgão (ex.: "08/2025") pode diferir do número no PNCP
  (`00008/2025`) e do sequencial do PNCP (`2025/19`). Registre os dois em `etp/fontes.yaml`.
- **Documentos:** com `--documentos`, baixa o contrato e os termos publicados. O que for lido neles
  segue o docs/ferramentas.md se o PDF for imagem.
- **Ao ETP:** o `resumo.md` traz sugestão de entrada para `etp/fontes.yaml`. Proponha como diff;
  objeto e vigência no texto citam `[F-nn]`.

**Parada.**

## Nunca

- Digitar preço que o script não leu de `detalhes/` ou que não tenha fonte e data.
- Tratar valor estimado de outro órgão como preço praticado.
- Contornar o captcha do Compras.gov.br.
- Citar jurisprudência (AGENTS regra #4).
- Commitar sem pedido. Se o usuário pedir, a área do commit é `docs` ou `etp`, e o slug é o da
  pesquisa (ex.: `docs(waf-cdn-2026): registrar pesquisa no PNCP`).
