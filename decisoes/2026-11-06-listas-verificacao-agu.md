---
data: 2026-11-06
autores: ["Neuton Martins"]
status: aceita  # aceita | aberta | rejeitada
---

# Listas de verificação da AGU preenchidas no repositório

## Contexto

A AGU pede que o órgão preencha a lista de verificação e a junte aos autos antes da remessa à
consultoria jurídica (nota 1 dos modelos). Há uma lista por tipo de processo. Para TIC, as mais
usadas são:

- **TIC (Lei 14.133), set/2024:** seções comuns, pesquisa de preços, aquisições, serviços,
  inexigibilidade e dispensa.
- **Adesão à ata de registro de preços (Lei 14.133), set/2024:** quando o processo adere a ata de
  outro órgão.

Os modelos têm listas suspensas (Sim, Não, Não se aplica) e notas de fim. Preencher o docx à mão a
cada revisão do ETP é trabalho repetido, e a resposta perde o vínculo com o item do ETP que a
sustenta.

## Decisão

1. **Pasta `listas-verificacao/`.** Um YAML por lista; o template traz `tic.yaml` e
   `adesao-arp.yaml` em branco. Cada linha do modelo é um item com os campos abaixo.

   | Campo | Conteúdo |
   |---|---|
   | `id` | seção e item do modelo (`seção` é a tabela do docx, a partir de 1; `item` é a linha, sem o cabeçalho) |
   | `pergunta` | início literal da pergunta, conferido pelo script |
   | `resposta` | `sim`, `nao` ou `nao_se_aplica`, as únicas respostas admitidas pela AGU; vazio = ainda não respondido |
   | `situacao` | `atendido` ou `pendente`; pendente exige resposta `nao` e `providencia` |
   | `local` | onde a exigência é atendida (item do ETP, DFD, portaria); o número SEI entra na juntada |
   | `providencia` | o que falta, ou ressalva |

   No cabeçalho do YAML ficam `modelo`, `saida`, `orgao`, `processo`, `data_revisao` e
   `remover_tabelas`.
2. **Script `scripts/gerar-listas-verificacao.py`**, só com biblioteca padrão (zipfile e expressões
   regulares sobre o XML) e PyYAML.
   - `--esqueleto <nome> <modelo.docx>` cria o YAML com as perguntas do modelo.
   - Sem argumentos, gera o docx de cada YAML:
     - confere a pergunta;
     - marca a lista suspensa nos dois formatos do modelo (lista dentro da célula ou envolvendo a
       célula);
     - escreve local e providência na terceira coluna;
     - troca o marcador do órgão;
     - remove as tabelas inaplicáveis.
   - Item sem resposta mantém o "Resposta" do modelo.
   - A geração falha se faltar item, sobrar item ou a pergunta divergir.
   - O docx gerado fica na mesma pasta e é versionado, como o Anexo I do ETP.
3. **Seções inaplicáveis** vão em `remover_tabelas` (nota 1 do modelo). Numa adesão ou numa
   licitação, as seções de inexigibilidade e de dispensa da lista de TIC (5ª e 6ª tabelas; índices 4 e 5) saem.
4. **TR na adesão.** A nota 8 da lista de adesão cita a IN SEGES/ME 81/2022, art. 11, que dispensa
   o TR na adesão. Para TIC, a IN SGD/ME 94/2022, art. 9º, §1º, IV, exige todas as etapas do
   planejamento também na adesão. Trate o TR como pendente, não como dispensado.
5. **`scripts/validar.sh`** lê `listas-verificacao/*.yaml` e exige o template da lista de adesão.

## Consequências

- **Atualização:** a cada revisão do ETP, atualizar o YAML e regenerar o docx. A resposta aponta o
  item do ETP, e a busca pelo número do item mostra o que conferir quando ele mudar.
- **Juntada:** na juntada ao SEI, acrescentar os números dos documentos.
- **Modelo novo da AGU:** se o texto das perguntas mudar, o script falha na conferência. Gere um
  esqueleto novo e migre as respostas.
