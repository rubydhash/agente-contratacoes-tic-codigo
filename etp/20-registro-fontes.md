---
secao: "Registro de fontes técnicas consultadas"
capitulo: 20               # nº do capítulo no ETP Digital do Compras.gov.br
capitulo_modelo_sgd: ""    # nº no modelo SGD v1.2 ("" = capítulo acrescido)
fonte_lei_14133: "art. 18 §1º IV (documentos que dão suporte ao estudo)"
fonte_in_94: "art. 11, II e III (comparação apoiada em elementos verificáveis)"
status: rascunho           # rascunho | revisao | aprovado
autor: ""
ultima_alteracao: 2026-10-01
pendencias: []
---

# 20. Registro de fontes técnicas consultadas

<!--
> Esta seção e o Anexo I reúnem, em um único lugar, todo documento externo em que este Estudo
> apoia afirmação de capacidade técnica, de licenciamento ou de preço. Existe por uma
> razão prática: as seções do ETP são redigidas em arquivos separados e só se
> convertem em documento único na juntada ao processo. Tabelas de fontes por seção
> reiniciariam a numeração a cada uma delas, e o mesmo documento receberia
> identificadores diferentes em pontos diferentes do mesmo PDF.
>
> Capítulo acrescido ao modelo SGD. Os itens 20.1 e 20.2 abaixo são texto-padrão do
> template e servem a qualquer objeto. O item 20.3 registra regras de fonte adotadas na
> contratação de origem (EDR, 2026): manter, ajustar ou suprimir conforme o objeto. Dados
> das fontes: etp/fontes.yaml. Anexo I:
> .venv/bin/python scripts/gerar-anexo-fontes.py. Apague este bloco antes do build final.
-->

**20.1. Como ler este registro**

20.1.1. Cada documento externo tem um identificador **único no Estudo inteiro**, na
forma `F-nn`. As seções citam o identificador entre colchetes, `[F-10]`, no ponto da
afirmação que ele sustenta; o endereço e a data da consulta constam **somente** do
Anexo I deste Estudo (item 20.2).

20.1.2. **Os identificadores não são renumerados.** Fonte nova entra no fim da lista;
fonte que deixe de ser citada permanece registrada. A regra existe para que remissão
feita em parecer, em diligência ou em documento externo continue válida depois de
qualquer revisão deste Estudo.

20.1.3. A coluna **Consulta** do Anexo I registra a data em que o conteúdo citado foi verificado no
endereço indicado, e não a data de publicação do documento.

20.1.4. **Toda fonte é identificada por endereço público**, e não por cópia juntada aos autos.
A verificação independe, assim, de juntada: quem examina o processo alcança o
documento original pelo mesmo caminho que a Equipe de Planejamento percorreu.

20.1.5. **Contratações de outros órgãos** são identificadas pelo número do pregão e
pelo ano, pela unidade administrativa de serviços gerais (UASG) e pelo endereço da
respectiva divulgação no **Portal Nacional de Contratações Públicas (PNCP)**. Onde o
órgão adota numeração interna distinta da registrada no PNCP, as duas constam, para
que a busca não falhe por divergência de número.

**20.2. Fontes**

20.2.1. A relação das fontes consultadas, identificador, documento, endereço e data da
consulta, consta do **Anexo I deste Estudo Técnico Preliminar, *Registro de fontes
técnicas consultadas***, juntado aos autos em arquivo próprio.

20.2.2. O Anexo I é o único lugar em que endereço e data de consulta são registrados. As
seções deste Estudo citam somente o identificador.

**20.3. Regras de fonte que este Estudo se impôs**

20.3.1. **Capacidade de produto se prova em documento do fabricante daquele produto.**
Afirmação sobre o que uma solução entrega ou deixa de entregar apoia-se em matriz,
datasheet, descrição de serviço ou documentação de produto do respectivo fabricante,
e não em material comparativo de concorrente nem em análise de terceiro.

20.3.2. **Matriz de suporte é conferida na fonte viva, com data.** Matrizes de
compatibilidade mudam nas duas direções, retirando versões antigas e demorando a
incorporar as novas. Por isso toda consulta é datada.

20.3.3. **Ausência de recurso em matriz publicada é registrada como tal.** Quando o
Estudo afirma que uma solução não entrega determinada capacidade, e a afirmação se
apoia na **ausência do recurso** na matriz do fabricante, e não em declaração expressa
de que não o entrega, isso é dito no ponto da afirmação.

20.3.4. **Preço sem fonte formalizada não entra em comparação.** A regra governa a
análise de custos e está desenvolvida na seção de análise comparativa de custos.
