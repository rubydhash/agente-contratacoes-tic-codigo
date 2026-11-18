# Agente de contratação de TIC como código

Template para planejar **contratações públicas de TIC** (Lei nº 14.133/2021, IN SGD/ME nº 94/2022,
IN SEGES/ME nº 65/2021) tratando o DFD, o ETP e o TR como **código-fonte**: um arquivo markdown
por capítulo, dados em YAML, histórico no git e saída nos formatos oficiais (modelos AGU, ETP
Digital do Compras.gov.br, SEI).

O repositório foi desenhado para que **pessoas e agentes de IA** (Claude Code, Codex, Gemini e
outros) trabalhem juntos:
- cada agente carrega só a seção em que está mexendo;
- os checklists normativos dizem o que cada seção precisa cobrir;
- scripts conferem o que dá para conferir sem IA.

## Para quem é

Equipes de planejamento de contratações de TIC de órgãos e entidades públicas, nos papéis de
requisitante, técnico e administrativo, que querem:
- rastreabilidade (quem mudou o quê, e por quê);
- aderência literal aos modelos da AGU;
- apoio de IA sem abrir mão do controle humano.

## Início rápido

```bash
# 1. Crie o repositório do seu processo a partir deste template (botão "Use this template"
#    no GitHub) e clone-o.
git clone <url-do-seu-repositorio> && cd <pasta>

# 2. Instale as dependências (Debian/Ubuntu)
sudo apt-get install -y pandoc poppler-utils python3-yaml python3-lxml fonts-dejavu-core
python3 -m venv .venv && .venv/bin/pip install fpdf2 pyyaml

# 3. Abra seu agente de IA na pasta e peça o onboarding
#    (Claude Code: /iniciar-contratacao; outros agentes: "siga skills/iniciar-contratacao/SKILL.md")
```

O onboarding preenche os dados do órgão, do processo e do planejamento institucional, e no fim
indica o primeiro documento a redigir. Detalhes em [Primeiros passos](docs/primeiros-passos.md).

## O que tem aqui

| Pasta | Conteúdo |
|---|---|
| `dfd/`, `etp/`, `tr/` | Os artefatos do processo, um arquivo por capítulo do sistema ou do modelo |
| `normativos/` | Checklists YAML do que a lei, a IN 94 e o planejamento do órgão exigem de cada seção |
| `templates/` | Modelos AGU e Gov.Digital em markdown, e o documento-base do SEI |
| `scripts/` | Validação, build para docx/HTML, conferência contra o modelo AGU, pesquisa no PNCP |
| `skills/` | Roteiros passo a passo para agentes de IA |
| `decisoes/` | ADRs: o porquê das escolhas estruturais |
| `referencia/` | Originais (leis, INs, modelos), somente leitura |

## Documentação

- [Visão geral](docs/visao-geral.md): a ideia, o fluxo DFD → ETP → TR e quem faz o quê
- [Primeiros passos](docs/primeiros-passos.md): instalação e onboarding
- [Estrutura do repositório](docs/estrutura.md)
- [Fluxo de trabalho](docs/fluxo-de-trabalho.md): sessões, status, branches, commits
- Redação: [ETP](docs/redacao-etp.md) · [TR](docs/redacao-tr.md) ·
  [Dados estruturados](docs/dados-estruturados.md)
- [Ferramentas (scripts)](docs/ferramentas.md)
- [Pesquisa de preços no PNCP](docs/pesquisa-pncp.md) ·
  [Listas de verificação da AGU](docs/listas-verificacao.md)
- [Skills](docs/skills.md) · [Como os agentes de IA usam o repositório](docs/agentes-ia.md)
- [Adaptação ao seu órgão](docs/adaptacao-ao-orgao.md) ·
  [Repositórios derivados](docs/repositorios-derivados.md)

As instruções para os agentes ficam em [`AGENTS.md`](AGENTS.md).

## Aviso

Este template organiza e confere, mas **não substitui** a análise da equipe de planejamento nem
o parecer jurídico. Todo texto produzido com apoio de IA precisa ser revisado e assumido por
servidor identificado antes de ir aos autos.

## Licença e autoria

Criado e mantido por **Neuton Martins**. Contribuições são bem-vindas: veja
[CONTRIBUTING.md](CONTRIBUTING.md).

- Código (`scripts/`): [MIT](LICENSE).
- Documentação, templates e checklists: [CC BY 4.0](LICENSE-docs).
- O material em `referencia/` é de domínio público ou dos respectivos órgãos emissores, e não
  entra nessas licenças (veja [`referencia/README.md`](referencia/README.md)).
