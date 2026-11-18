# Listas de verificação da AGU

Antes da remessa à consultoria jurídica, a AGU pede a lista de verificação preenchida. O
repositório as mantém em YAML, uma linha do modelo por item, com resposta, local nos autos e
providência. A partir do YAML, gera o docx no formato da AGU e, se o órgão quiser, o documento
para o SEI.

| Lista | YAML | Modelo |
|---|---|---|
| TIC (set/2024) | `listas-verificacao/tic.yaml` | `referencia/modelos-agu/modelo-de-lista-de-verificacao-tic-…docx` |
| Adesão a ARP (set/2024) | `listas-verificacao/adesao-arp.yaml` | `referencia/modelos-agu/modelo-de-lista-de-verificacao-adesao-…docx` |

```bash
# lista nova a partir de um modelo da AGU (perguntas copiadas, respostas em branco)
python3 scripts/gerar-listas-verificacao.py --esqueleto <nome> referencia/modelos-agu/<modelo>.docx

# docx no formato da AGU
python3 scripts/gerar-listas-verificacao.py            # todas
python3 scripts/gerar-listas-verificacao.py <nome>     # só uma

# a mesma lista como documento do SEI → despachos/lista-verificacao-<nome>.html
python3 scripts/gerar-lista-verificacao-sei.py <nome>
```

## Regras

- **Respostas admitidas:** `sim`, `nao` e `nao_se_aplica`. Pendência é `nao` com
  `situacao: pendente` e `providencia`.
- Os scripts **recusam resposta em branco** e pergunta que diverge do modelo. Por isso, os
  esqueletos só geram documento depois de preenchidos.
- **`local` aponta o item do ETP ou o documento.** Quando a numeração do ETP mudar, procure o
  número antigo nas listas.
- **Seções inaplicáveis saem** por `remover_tabelas` (nota 1 dos modelos).
- **A lista de adesão** só se usa quando o processo adere a ata de outro órgão.
- Para o documento do SEI, as chaves opcionais `modelo_md`, `titulo`, `rodape` e `signatario`
  completam o cabeçalho e a assinatura.

## Lacunas que a lista costuma revelar

A revisão pelas listas encontra pontos que o checklist interno não pega:

- alinhamento à Estratégia Federal de Governo Digital (IN 94, art. 6º, II; Decreto 12.198/2024;
  Portaria SGD/MGI 6.618/2024);
- declaração sobre os Catálogos de Soluções de TIC da SGD (IN 94, art. 9º, §6º);
- vedações dos arts. 3º e 4º da IN 94;
- providências de adesão:
  - publicação do ETP;
  - consultas SICAF, CEIS, CNJ, TCU e CADIN;
  - prazo de 90 dias.

ADRs:
- [`2026-11-06-listas-verificacao-agu.md`](../decisoes/2026-11-06-listas-verificacao-agu.md);
- [`2026-11-12-lista-verificacao-em-despacho-sei.md`](../decisoes/2026-11-12-lista-verificacao-em-despacho-sei.md).
