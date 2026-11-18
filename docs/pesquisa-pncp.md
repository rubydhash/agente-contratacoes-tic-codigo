# Pesquisa de contratações similares e de preços no PNCP

O `scripts/pesquisa-pncp.py` conduz a pesquisa que alimenta o ETP:
- referência técnica (capítulos 8 a 12);
- série de preços (capítulo 13 e `etp/tco.yaml`, IN 65/2021, arts. 5º e 6º);
- avaliação de atas para adesão (Lei 14.133, art. 86).

O passo a passo, com uma parada para a equipe decidir em cada etapa, está no skill
[`pesquisa-precos-pncp`](../skills/pesquisa-precos-pncp/SKILL.md). ADRs:
- [`2026-10-01-pesquisa-precos-pncp.md`](../decisoes/2026-10-01-pesquisa-precos-pncp.md)
  (esquemas);
- [`2026-11-06-painel-e-atas-por-catalogo.md`](../decisoes/2026-11-06-painel-e-atas-por-catalogo.md);
- [`2026-11-09-contratos-e-termos-no-pncp.md`](../decisoes/2026-11-09-contratos-e-termos-no-pncp.md).

## Comandos

```bash
S=scripts/pesquisa-pncp.py
python3 $S iniciar <slug>          # pesquisas/pncp/<slug>/pesquisa.yaml — preencher com a equipe
python3 $S buscar <slug>           # brutos/<termo>/<tipo>_paginaN.json (status=todos, retomável)
python3 $S consolidar <slug>       # consolidado.json/csv + triagem.yaml (uma linha por compra)
#   → triagem humana em triagem.yaml (pertinente | nao_pertinente + motivo)
python3 $S enriquecer <slug>       # detalhes/, classificado.json/csv, propostas-a-obter.md
python3 $S saldo <slug>            # saldo de adesão das atas vigentes → atas-candidatas.md
python3 $S atas-catalogo <slug>    # atas vigentes por código de catálogo → atas-arp/<data>/
python3 $S painel <slug>           # Painel de Preços (IN 65, art. 5º, I) → painel-precos/<data>/
python3 $S contrato <alvo> --saida <pasta>   # contrato, termos aditivos e vigência atual
python3 $S baixar <slug>           # documentos do PNCP → referencia/contratacoes-outros-orgaos/
python3 $S propostas <slug>        # confere as propostas salvas à mão em propostas/
python3 $S serie <slug>            # serie-precos.yaml → serie-precos.md (média, mediana, menor)
```

## Regras

- **Sempre pergunte a esfera do contratante**, mesmo com `orgao.esfera` preenchido. É ela que
  define a adesão cabível:
  - federal adere só a ata federal (art. 86, §8º);
  - estadual e distrital aderem a ata federal, estadual ou distrital (§3º, I);
  - municipal adere também a ata municipal, se o SRP foi licitado (§3º, II).

  `adesao: sim` no classificado indica só compatibilidade documental. A adesão exige ainda
  justificativa, compatibilidade de preços e anuência do gerenciador e do fornecedor (§2º).
- **Busca sempre com `status=todos`.** Compra revogada, anulada ou suspensa fica no consolidado,
  sinalizada. A exclusão é decisão de triagem, com motivo.
- **Preço vem do resultado homologado no PNCP**, lido pelo script e nunca digitado. Valor estimado
  de outro órgão não é preço praticado. Preço de fora do PNCP (Painel de Preços, cotação, sítio
  especializado) entra como `origem: externo`, com `parametro_in65`, `fonte` e `data`.
- **Relate sempre dois números:**
  - compras dentro e fora da janela de 1 ano (IN 65, art. 5º, II);
  - adesão cabível e não cabível.
- **O Compras.gov.br exige captcha** nas páginas de propostas. Não tente contorná-lo. O script gera
  `propostas-a-obter.md` com os links, e a equipe baixa as propostas à mão.
- **O saldo de adesão não está no PNCP.** Ele vem da API de dados abertos do Compras.gov.br
  (`modulo-arp`). Relate:
  - o saldo informado (teto do art. 86, §5º);
  - o limite por órgão (50% do registrado, §4º), que o script calcula.

  Saldo é retrato do dia: rode de novo antes de oficiar o gerenciador.
- **A busca textual perde atas.** Preencha `catalogo` no `pesquisa.yaml` e rode `atas-catalogo` e
  `painel`. O Painel de Preços é parâmetro prioritário: relate o coeficiente de variação e o
  recorte por modelo, e confirme a marca no edital ou na proposta.
- **`aceitaAdesao: true` na API não basta.** Restrições do edital não aparecem na API. Leia a
  cláusula de utilização da ata por não participantes.
- **Item de grupo:** aderir a parte de um grupo exige comprovar que o vencedor teve o menor preço
  em cada item aderido (Parecer Referencial nº 00002/2026/CONJUR-CGU/CGU/AGU).
- **Limite por órgão:** 50% do registrado por item. Item com uma unidade registrada não admite
  adesão (Decreto 11.462/2023, art. 30, §3º, para o remanejamento).
- **Vigência de contrato vem dos termos.** No PNCP, a vigência do contrato é a do termo inicial;
  aditivos e rescisões ficam nos termos. O comando `contrato` calcula a vigência atual e, com
  `--ate`, diz se ela cobre o prazo da solução.
- **Na adesão de TIC, o planejamento continua completo:** ETP e TR são obrigatórios (IN 94,
  art. 9º, §1º, IV). A publicação do ETP é condição para a autorização do gerenciador (§8º).
- **Os arquivos brutos são versionados.** Eles são a evidência datada da consulta (IN 65, art. 3º,
  III), e `registro.json` guarda a URL e a data/hora de cada página.

## Onde ficam os documentos

| Documento | Pasta |
|---|---|
| Contratos do próprio órgão | `referencia/contratacoes-proprias/<assunto>/pncp-<AAAA-MM-DD>/` |
| Documentos de outros órgãos | `referencia/contratacoes-outros-orgaos/` |
| A pesquisa (brutos, triagem, série) | `pesquisas/pncp/<slug>/` |
