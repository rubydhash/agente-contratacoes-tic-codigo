# Primeiros passos

## 1. Crie o repositório do processo

Cada contratação vive no **próprio repositório**, criado a partir deste template:

- **GitHub:** botão *Use this template* → *Create a new repository*. O repositório pode ser
  privado: os dados do processo não precisam ser públicos.
- **Sem GitHub:** copie a pasta (sem `.git/`) e rode `git init -b main`.

Melhorias de ferramental feitas no repositório do processo podem voltar para o template. Veja
[Repositórios derivados](repositorios-derivados.md).

## 2. Instale as dependências

Fora do Python, o sistema só precisa de três coisas:

| Do sistema | Para quê | Debian/Ubuntu |
|---|---|---|
| `git` | Versionamento | `apt-get install git` |
| `python3` com `venv` | Criar o `.venv` do repositório | `apt-get install python3-venv` |
| Fonte DejaVu | PDFs (Anexo I do ETP, anexos do TR) | `apt-get install fonts-dejavu-core` |

O resto fica no `.venv/`, com versões fixas em `requirements.txt`:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

| Pacote (`.venv/`) | Para quê |
|---|---|
| `PyYAML` | Validação de YAML, metadados, listas de verificação, PNCP |
| `lxml` | Conferência do TR contra o docx da AGU |
| `fpdf2` | Anexo I do ETP e anexos do TR em PDF |
| `pypandoc_binary` | O **pandoc**, embutido: build do DFD, do ETP e do TR, conversão de modelos |
| `pypdfium2` | Leitura de PDFs de normas e propostas (`scripts/ler-pdf.py`), no lugar do poppler |

Não é preciso ativar o `.venv`. Os scripts Python se reexecutam nele sozinhos
(`scripts/_ambiente.py`), e os scripts shell pegam dele o Python e o pandoc
(`scripts/_ambiente.sh`). Sem `.venv`, tudo cai no Python e no pandoc do sistema, se houver.

No Windows, use o WSL. No macOS, os mesmos comandos funcionam; a fonte vem de
`brew install --cask font-dejavu`. Se a fonte estiver noutra pasta, aponte-a em `FONTES_TTF`.

Para conferir o ambiente:

```bash
python3 scripts/_ambiente.py   # o que está instalado e o que falta
scripts/validar.sh             # barato, não altera arquivos rastreados
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
