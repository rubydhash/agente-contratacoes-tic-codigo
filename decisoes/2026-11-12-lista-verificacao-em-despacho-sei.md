---
data: 2026-11-12
status: aceita
autor: "Neuton Martins"
---

# Lista de verificação da AGU também como documento do SEI

## Contexto

Há órgãos que juntam a lista de verificação de adesão ao SEI como documento próprio, em tabela, assinado pela unidade de compras e contratos. O `scripts/gerar-listas-verificacao.py` gera só o docx da AGU (`decisoes/2026-11-06-listas-verificacao-agu.md`).

## Decisão

1. **Novo script.** `scripts/gerar-lista-verificacao-sei.py <nome>` gera `despachos/lista-verificacao-<nome>.html`, a partir do mesmo `listas-verificacao/<nome>.yaml`.
2. **Formato.** Reaproveita o cabeçalho, os estilos e o timbre do documento de referência do SEI, como `scripts/gerar-despacho.py`. O trecho a colar fica entre os comentários "INÍCIO/FIM DO TRECHO A COPIAR NO SEI".
3. **Conteúdo, como no exemplo:**
   - título e introdução literais do modelo;
   - tabela com quatro colunas: exigência (pergunta, alíneas e nota da AGU), resposta, local e OBS;
   - assinatura eletrônica e rodapé da CNMLC.
4. **Fonte das perguntas.** A pergunta completa, as alíneas e as notas saem da cópia em markdown do modelo (`modelo_md`). O script confere o início de cada pergunta do YAML e falha se faltar ou sobrar item.
5. **Chaves novas do YAML**, opcionais e usadas só por este script:
   - `modelo_md`;
   - `titulo`;
   - `rodape`;
   - `signatario` (`nome`, `cargo`, `ato`).

   A coluna OBS é a `providencia`.

## Consequências

- **Atualização.** Mudou o YAML, regenerar os dois formatos:
  - `python3 scripts/gerar-listas-verificacao.py <nome>` (docx);
  - `python3 scripts/gerar-lista-verificacao-sei.py <nome>` (SEI).
- **Números SEI.** A coluna de local traz itens do ETP e do TR. Os números SEI entram no YAML na juntada.
- **Uso em outros processos.** O script é ferramental base. O cabeçalho e os estilos vêm de `templates/sei/documento-base.html`, que cada órgão ajusta no onboarding.
