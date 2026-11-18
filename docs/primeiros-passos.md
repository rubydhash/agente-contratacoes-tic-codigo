# Primeiros passos

## 1. Crie o repositório do processo

Cada contratação vive no **próprio repositório**, criado a partir deste template:

- **GitHub:** botão *Use this template* → *Create a new repository*. O repositório pode ser
  privado: os dados do processo não precisam ser públicos.
- **Sem GitHub:** copie a pasta (sem `.git/`) e rode `git init -b main`.

Melhorias de ferramental feitas no repositório do processo podem voltar para o template. Veja
[Repositórios derivados](repositorios-derivados.md).

## 2. Instale as dependências

| Ferramenta | Para quê | Instalação (Debian/Ubuntu) |
|---|---|---|
| `git` | Versionamento | `apt-get install git` |
| `pandoc` | Build docx/HTML, conversão de modelos | `apt-get install pandoc` |
| `poppler-utils` | `pdftotext`/`pdftoppm`: ler PDFs de normas e propostas | `apt-get install poppler-utils` |
| `python3-yaml` | Validação de YAML, listas de verificação, PNCP | `apt-get install python3-yaml` |
| `python3-lxml` | Conferência do TR contra o docx da AGU | `apt-get install python3-lxml` |
| `fpdf2` (em `.venv/`) | Anexo I do ETP em PDF | `python3 -m venv .venv && .venv/bin/pip install fpdf2 pyyaml` |
| `fonts-dejavu-core` | Fonte do Anexo I | `apt-get install fonts-dejavu-core` |

No Windows, use o WSL. No macOS, use `brew install pandoc poppler` e `pip install pyyaml lxml`.

Para conferir o ambiente:

```bash
scripts/validar.sh      # barato, não altera arquivos rastreados
```

Num repositório recém-criado, o resultado esperado é uma lista de avisos de placeholder
(`<preencher>`) e nenhuma linha `ERRO`.

## 3. Faça o onboarding com o agente

Abra o agente de IA na raiz do repositório:

- **Claude Code:** `/iniciar-contratacao`
- **Outros agentes** (Codex, Gemini CLI, Cursor etc.): "Leia `AGENTS.md` e siga
  `skills/iniciar-contratacao/SKILL.md`."

O skill conduz, com uma parada para confirmação em cada etapa:

1. conferência das dependências;
2. identidade git e regra de commits sem marca de IA;
3. dados do órgão (nome, sigla, UASG, esfera, poder, áreas);
4. processo e equipe de planejamento;
5. objeto da contratação, descrito de forma genérica;
6. planejamento institucional (PDTI, PCA, PEI) → `normativos/planejamento-institucional-checklist.yaml`;
7. modelo AGU adotado (serviços ou compras de TIC);
8. cabeçalho do SEI e do despacho;
9. validação final e próximo passo.

Prefere fazer à mão? Os mesmos pontos estão em [Adaptação ao seu órgão](adaptacao-ao-orgao.md).

## 4. Primeira sessão de redação

Depois do onboarding, comece pelo DFD. Um prompt que funciona com qualquer agente:

> Rode `git status` e `git diff` e me resuma as alterações não commitadas. Leia `MANIFEST.yaml`
> e me diga quais seções estão em `rascunho`, `revisao` e `aprovado`. Sugira a próxima seção a
> atacar, considerando as dependências (o TR depende do ETP). Não carregue o texto integral de
> leis: use os checklists de `normativos/`.

E, com a seção escolhida:

> Abra `etp/02-descricao-necessidade.md`, aplique o checklist correspondente de
> `normativos/` e me liste o que falta. Não reescreva nada ainda.

O ciclo completo está em [Fluxo de trabalho](fluxo-de-trabalho.md).
