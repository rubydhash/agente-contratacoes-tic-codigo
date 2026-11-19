---
name: iniciar-contratacao
description: Onboarding de um repositório novo criado a partir deste template de contratação de TIC. Confere dependências, combina a identidade git e a regra de commits sem marca de IA, e preenche com a equipe os dados do órgão, do processo, da equipe de planejamento e do objeto. Também cobre o planejamento institucional (PDTI, PCA, PEI), o modelo AGU adotado e o cabeçalho do SEI e do despacho. Termina com a validação e o próximo passo. Use quando o usuário estiver começando uma contratação nova, quando os metadados ainda tiverem `<preencher>` ou quando pedir "setup", "configurar o repositório" ou "onboarding".
---

# Onboarding de uma contratação nova

Roteiro para preparar, **com a equipe**, um repositório recém-criado a partir do template. Cada
etapa termina numa **parada**: mostre o que vai gravar (o diff) e só siga com o aval.

- **Não invente dado de órgão, processo, pessoa ou valor.** O que a equipe não souber agora fica
  `<preencher>` e vai para a lista final de pendências.
- **Não instale pacotes sem aval.**
- **Não commite sem pedido.**

Regras gerais: `AGENTS.md`. Referência manual destes mesmos passos:
`docs/adaptacao-ao-orgao.md`.

## 0. Reconhecimento

```bash
git status
grep -rc "<preencher" etp/00-metadados.yaml dfd/00-metadados.yaml MANIFEST.yaml
```

- Se já houver seções em `revisao`/`aprovado` ou metadados preenchidos, o repositório **não é
  novo**. Diga isso e pergunte se a ideia é só completar as lacunas, pulando as etapas já
  resolvidas.
- Se a pasta ainda for o próprio template (o repositório público), avise: o certo é criar um
  repositório do processo a partir dele (`docs/primeiros-passos.md`).

Apresente as etapas abaixo em uma linha cada e pergunte por onde começar. **Parada.**

## 1. Dependências

```bash
command -v git >/dev/null && echo "ok    git" || echo "FALTA git"
python3 scripts/_ambiente.py      # .venv, pacotes de requirements.txt, pandoc e fonte DejaVu
```

Se faltar o `.venv`, proponha `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`
(precisa de rede para o PyPI). O diagnóstico diz o que deixa de funcionar sem cada item; os
comandos de instalação estão em `docs/primeiros-passos.md`.

**Parada.**

## 2. Identidade git e autoria

1. Pergunte o nome e o e-mail de quem assina os commits. O autor é a pessoa que autoriza o
   conteúdo, e não um valor de conveniência.
2. Explique a regra: nenhum `Co-Authored-By`, "Generated with" ou nome de modelo em commit,
   frontmatter ou documento (AGENTS.md, regra 9).
3. Ofereça o hook que bloqueia essas marcas:

   ```bash
   git config core.hooksPath scripts/hooks
   ```

   Se `git config` não puder gravar (sandbox), mostre como passar a identidade por commit:
   `git -c user.name="…" -c user.email="…" commit …`.

**Parada.**

## 3. Órgão

Pergunte e grave em `etp/00-metadados.yaml > orgao`, que o DFD também usa
(`dfd/00-metadados.yaml` só complementa):
- `nome`, `sigla`, `uasg`;
- `esfera` (federal | estadual | distrital | municipal) e `poder`;
- `area_requisitante`, `area_tic`, `area_administrativa`.

Explique em uma linha por que a **esfera** importa: ela define a adesão cabível a atas (Lei 14.133,
art. 86, §§3º e 8º). **Parada.**

## 4. Processo e equipe

- `processo.numero_sei` e `processo.data_abertura`. Se o processo ainda não existe, deixe
  `<preencher>`.
- `equipe_planejamento`: integrantes requisitante, técnico e administrativo (nome e matrícula), e
  a autoridade máxima da área de TIC (IN 94, art. 11, §§2º e 3º).
- `artefatos_no_comprasgov`: números de DFD/ETP/TR já registrados no sistema, se houver.

**Parada.**

## 5. Objeto

Peça uma descrição da necessidade e proponha:
- `contratacao.objeto_curto` (até 200 caracteres);
- `contratacao.descricao_publica` (1 a 2 linhas).

As duas devem ser **genéricas quanto ao produto**. Nomear marca ou fabricante no objeto, antes do
estudo, dá margem à leitura de direcionamento; a solução aparece no capítulo 12 do ETP. Grave
também `MANIFEST.yaml > projeto.objeto_curto`. **Parada.**

## 6. Planejamento institucional

1. Peça o PDTI vigente (e o PEI, se houver) em PDF. Salve em `referencia/normativos-orgao/` (crie
   a pasta) e converta:

   ```bash
   python3 scripts/ler-pdf.py texto referencia/normativos-orgao/<arquivo>.pdf -o referencia/normativos-md/pdti-<sigla>-<vigencia>.md
   ```

   Se a conversão voltar vazia, o PDF é imagem: siga `docs/redacao-etp.md` (PDF sem texto).
2. Leia o PDTI **por janelas** (sumário primeiro; depois só os temas candidatos). Proponha o
   preenchimento de `normativos/planejamento-institucional-checklist.yaml`:
   - versão e unidade responsável;
   - tema principal, objetivos, resultados-chave e macroações, com `fonte_pdti` (item e linhas);
   - itens orçamentários relevantes;
   - `aplicacao_no_etp_tr`, ajustado ao objeto.
3. Preencha `etp/00-metadados.yaml > planejamento_vinculo` (PDTI, item orçamentário, PCA, PEI).
4. Se o objeto **não** estiver nominalmente previsto no PDTI ou no orçamento dele, proponha uma ADR
   `decisoes/<hoje>-alinhamento-pdti.md` com `status: aberta`. Ela registra as alternativas, e a
   decisão cabe à área de TIC:
   - enquadrar em item existente;
   - suplementar;
   - revisar o PDTI.

**Parada.**

## 7. Modelo AGU

Pergunte se a contratação é de **serviços** de TIC (o modelo que já vem no template) ou de
**compras/bens** de TIC.

- **Serviços:** nada a trocar.
- **Outro modelo:** siga `docs/adaptacao-ao-orgao.md` (seção Modelo AGU). É uma mudança
  estrutural e exige ADR. Proponha-a, mas não a execute sem aval explícito.

Pergunte também se a equipe tem o docx do modelo com a formatação desejada para
`templates/agu-referencia.docx`, que o build usa como referência de estilo. **Parada.**

## 8. SEI e despacho

- O órgão usa o SEI? Se usa, proponha substituir os placeholders de cabeçalho em
  `templates/sei/documento-base.html` (nome do órgão, endereço, sítio). Isso só afeta a
  pré-visualização; não mexa nas classes de estilo.
- Preencha as constantes do topo de `scripts/gerar-despacho.py` que já forem conhecidas:
  - `UNIDADE_SIGLA` e `UNIDADE_NOME`;
  - `PROCESSO_SEI`;
  - `INTERESSADO`;
  - `OBJETO`;
  - `SIGNATARIO_NOME` e `SIGNATARIO_CARGO`.

  Rode `python3 scripts/gerar-despacho.py` e mostre o resultado.
- Nas listas de verificação (`listas-verificacao/*.yaml`), preencha `orgao` e `signatario`.

**Parada.**

## 9. Fechamento

1. `MANIFEST.yaml > projeto.data_inicio` com a data de hoje (AAAA-MM-DD).
2. Rode:

   ```bash
   scripts/validar.sh
   ```

   Nenhuma linha `ERRO`. Liste os avisos que restam, agrupados por arquivo.
3. Mostre o resumo:
   - o que foi preenchido;
   - o que ficou `<preencher>` e com quem está cada pendência;
   - as ADRs abertas.
4. Se a equipe pedir commit, sugira uma branch (`setup/onboarding`) e um commit por área, por
   exemplo `etp(metadados): preencher dados do órgão e do processo`, sem marca de ferramenta.
5. **Próximo passo:** o DFD (`dfd/01-dfd.md`). Depois vem o ETP, capítulo a capítulo, com o skill
   `pesquisa-precos-pncp` na fase de levantamento de soluções e preços (capítulos 8 a 13).
