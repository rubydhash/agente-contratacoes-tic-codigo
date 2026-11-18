# Como contribuir

Contribuições são bem-vindas: correções em checklists, scripts novos, skills, documentação e
relatos de uso em processos reais (anonimizados).

## Antes de abrir um PR

1. **Nada de dado de processo real.** Retire nome de órgão, servidor, número de processo, CNPJ,
   preço de proposta e e-mail. Lições se escrevem de forma anônima ("em contratação anterior de
   firewall, …").
2. **Sem marca de IA.** Commits e PRs sem `Co-Authored-By`, "Generated with" ou nome de modelo. O
   hook ajuda: `git config core.hooksPath scripts/hooks`.
3. **Convenção de commit:** `<area>(<slug>): <verbo no infinitivo…>`, em português (veja
   `docs/fluxo-de-trabalho.md`).
4. **Rode as validações:**

   ```bash
   scripts/validar.sh                     # sem ERRO
   python3 scripts/conferir-modelo-agu.py # se mexeu em tr/, templates/ ou no despacho
   ```

5. **Decisão estrutural exige ADR** em `decisoes/AAAA-MM-DD-titulo.md`. Isso inclui esquema de
   YAML novo, mudança na granularidade das seções ou dependência nova.
6. **Atualize a documentação** (`docs/`, e o `AGENTS.md` se a regra muda o comportamento do
   agente) e o `CHANGELOG.md`.

## Normativos e modelos novos

Inclua o original em `referencia/normativos/` (ou `modelos-agu/`):
- com a data de captura no nome;
- com o hash em `SHA256SUMS`;
- com a versão em markdown em `referencia/normativos-md/`, quando couber.

Atualize o checklist correspondente em `normativos/` e o `MANIFEST.yaml`.

## Dúvidas e sugestões

Abra uma issue descrevendo o caso de uso. Se o assunto envolver um processo real, descreva-o de
forma anônima.
