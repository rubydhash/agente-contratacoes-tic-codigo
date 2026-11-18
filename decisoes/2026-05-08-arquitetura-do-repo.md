---
data: 2026-05-08
autores: ["humano"]
status: aceita
---

# Arquitetura do repositório de planejamento da contratação

## Contexto

Vamos elaborar ETP e TR para uma contratação de TIC (Lei 14.133/2021,
IN SGD/ME 94/2022, modelos AGU). O trabalho é colaborativo entre humanos e
agentes baseados em modelos de IA distintos. Editar um único `.docx` polui
o histórico (XML), inviabiliza diff, força carga total no contexto a cada
sessão e cria conflitos sempre que dois colaboradores mexem ao mesmo tempo.

## Decisão

1. **Tratar ETP/TR como código fonte.** Repositório Git, uma seção por arquivo.
2. **Markdown CommonMark** para prosa e **YAML** para dados estruturados
   (riscos, requisitos, metadados).
3. **Normativos como checklists YAML curados** em `normativos/`, não como
   texto bruto carregado no contexto.
4. **`MANIFEST.yaml` como ponto único de entrada** — qualquer agente lê só
   o MANIFEST + seção alvo + checklist correspondente.
5. **Build final via pandoc** com `--reference-doc` apontando para o docx da
   AGU (quando disponível), preservando estilos institucionais.
6. **Originais imutáveis em `referencia/`** — nunca editar; só ler.

## Consequências

- Diff legível, blame por linha, possibilidade de PRs por seção.
- Custo de token cai porque ninguém precisa carregar o documento todo.
- Modelos diferentes podem colaborar sem entrar em conflito (cada um sua seção).
- Custo extra: humanos precisam aprender a montar o docx final via `build.sh`
  ao invés de "abrir o Word".
- Eventual divergência entre o docx montado e a apresentação esperada pela
  AGU pode exigir ajustes manuais — aceitos como custo de fronteira.
