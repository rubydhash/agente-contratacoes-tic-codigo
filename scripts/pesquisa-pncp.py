#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pesquisa-pncp.py — pesquisa de contratações similares no PNCP para subsidiar a
pesquisa de preços do ETP (IN SEGES/ME nº 65/2021, art. 5º, II) e a avaliação de
adesão a ata de registro de preços (Lei nº 14.133/2021, art. 86).

Cada pesquisa vive em pesquisas/pncp/<slug>/ e é conduzida em etapas:

  iniciar <slug>          cria a pasta e o pesquisa.yaml (objetivo, termos, filtros,
                          esfera do contratante, cautelas)
  buscar <slug>           consulta a busca do PNCP para cada termo e tipo de documento,
                          status=todos, uma página por arquivo JSON (retomável)
  consolidar <slug>       junta todas as buscas, elimina duplicatas (uma linha por
                          compra), registra os termos que acharam cada compra, aplica o
                          filtro de pertinência e atualiza o triagem.yaml
  enriquecer <slug>       para as compras pertinentes, consulta compra, itens, resultados,
                          atas e arquivos; classifica SRP, adesão (para a esfera do
                          contratante) e tempestividade (IN 65, art. 5º, II); gera o
                          roteiro de propostas a obter no Compras.gov.br
  baixar <slug>           baixa os documentos publicados no PNCP das compras pertinentes
                          para referencia/contratacoes-outros-orgaos/
  propostas <slug>        confere as propostas já salvas em propostas/ e atualiza o roteiro
  saldo <slug>            para as atas vigentes com adesão compatível, consulta o saldo de
                          adesões na API de dados abertos do Compras.gov.br (modulo-arp) e
                          o limite por órgão (Lei 14.133, art. 86, §§4º e 5º); gera
                          atas-candidatas.md
  serie <slug>            monta a série de preços a partir do serie-precos.yaml e calcula
                          média, mediana e menor valor (IN 65, art. 6º)
  painel <slug>           Painel de Preços por código de catálogo (IN 65, art. 5º, I)
  atas-catalogo <slug>    atas vigentes por código de catálogo (modulo-arp)
  contrato <alvos> --saida <pasta>
                          contrato, termos (aditivos, apostilamentos, rescisões) e documentos
                          de uma compra ou de um contrato no PNCP, ou busca de contratos de um
                          órgão (--orgao --texto); vigência atual pelos termos publicados e,
                          com --ate, se ela cobre a data exigida; gera resumo.md e SHA256SUMS.
                          Não depende de pesquisa (slug)

As APIs do PNCP são públicas e respondem só com User-Agent de navegador, sem cookie.
As páginas públicas do Compras.gov.br (cnetmobile) que mostram propostas e anexos
exigem hCaptcha: o script NÃO as consulta; gera os links para obtenção manual.

Decisão: decisoes/2026-10-01-pesquisa-precos-pncp.md. Receita: docs/pesquisa-pncp.md.
"""

import argparse
import csv
import datetime
import glob
import json
import math
import os
import random
import re
import statistics
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ambiente  # noqa: E402
_ambiente.usar_venv(__file__)   # bibliotecas do .venv (requirements.txt)

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("ERRO: PyYAML ausente. Crie o .venv: python3 -m venv .venv && "
             ".venv/bin/pip install -r requirements.txt")

# ----------------------------- Configuração --------------------------------

RAIZ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PASTA_PESQUISAS = os.path.join(RAIZ, "pesquisas", "pncp")
PASTA_DOCUMENTOS = os.path.join(RAIZ, "referencia", "contratacoes-outros-orgaos")
METADADOS_ETP = os.path.join(RAIZ, "etp", "00-metadados.yaml")

URL_BUSCA = "https://pncp.gov.br/api/search/"
URL_CONSULTA = "https://pncp.gov.br/api/consulta/v1/orgaos"
URL_PNCP = "https://pncp.gov.br/api/pncp/v1/orgaos"
URL_APP = "https://pncp.gov.br/app/editais"
URL_CNET_ITEM = ("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/"
                 "acompanhamento-compra/item/{item}?compra={compra}")
URL_CNET_COMPRA = ("https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/compras/"
                   "acompanhamento-compra?compra={compra}")

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:154.0) "
              "Gecko/20100101 Firefox/154.0")
TAM_PAGINA = 100
TEMP_SUFFIX = ".baixando"
TIPOS_DOCUMENTO = ("edital", "ata", "contrato")
ESFERAS = {"federal": "F", "estadual": "E", "distrital": "D", "municipal": "M"}
NOME_ESFERA = {"F": "Federal", "E": "Estadual", "D": "Distrital", "M": "Municipal",
               "N": "Não se aplica"}
# Modalidades que não são licitação (art. 86, §3º, II exige SRP formalizado por licitação)
MODALIDADES_SEM_LICITACAO = ("dispensa", "inexigibilidade", "inaplicabilidade")

HOJE = datetime.date.today()

# ------------------------------- Utilidades --------------------------------


def log(msg=""):
    print(msg, flush=True)


def aviso(msg):
    print(f"AVISO: {msg}", file=sys.stderr, flush=True)


def morre(msg):
    print(f"ERRO: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


def slug(texto):
    """'TRIBUNAL SUPERIOR DO TRABALHO' -> 'tribunal-superior-do-trabalho'."""
    norm = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    norm = re.sub(r"[^A-Za-z0-9]+", "-", norm).strip("-").lower()
    return norm or "x"


def sanitiza_nome(nome):
    """Limpa o nome de arquivo vindo do PNCP (mantém espaços e acentos)."""
    nome = nome.replace("\\", "/").split("/")[-1]
    nome = unicodedata.normalize("NFC", nome)
    nome = re.sub(r"[\x00-\x1f]", "", nome).strip().strip(".")
    return nome or "arquivo"


def descobre_extensao(dados):
    """Extensão pelo conteúdo, quando o título do documento veio sem extensão."""
    cab = dados[:4096]
    if cab.lstrip()[:5].startswith(b"%PDF"):
        return ".pdf"
    if cab.startswith(b"PK\x03\x04") or cab.startswith(b"PK\x05\x06"):
        for marca, ext in ((b"word/", ".docx"), (b"xl/", ".xlsx"), (b"ppt/", ".pptx")):
            if marca in cab:
                return ext
        return ".zip"
    if cab.startswith(b"Rar!"):
        return ".rar"
    if cab.lstrip()[:5].startswith(b"<?xml"):
        return ".xml"
    return None


def le_yaml(caminho, padrao=None):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f) or padrao


def grava_yaml(caminho, dados, cabecalho=""):
    with open(caminho, "w", encoding="utf-8") as f:
        if cabecalho:
            f.write(cabecalho.rstrip() + "\n\n")
        yaml.safe_dump(dados, f, allow_unicode=True, sort_keys=False, width=100)


def le_json(caminho, padrao=None):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def grava_json(caminho, dados):
    tmp = caminho + TEMP_SUFFIX
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)
        f.write("\n")
    os.replace(tmp, caminho)


def agora_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def data_iso(valor):
    """Converte '2026-09-16', '2026-09-16T23:09:42' etc. em date; None se vazio."""
    if not valor:
        return None
    try:
        return datetime.date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def meses_antes(data, meses):
    ano, mes = data.year, data.month - meses
    while mes <= 0:
        mes += 12
        ano -= 1
    dia = min(data.day, [31, 29 if ano % 4 == 0 and (ano % 100 or ano % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return datetime.date(ano, mes, dia)


def brl(valor):
    if valor is None:
        return "—"
    s = f"{valor:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def dmy(data):
    return data.strftime("%d/%m/%Y") if data else "—"


# --------------------------------- HTTP ------------------------------------


def cliente_detalhes(cfg):
    """Cliente das etapas enriquecer/baixar, com a pausa de detalhes.espera e o recuo
    de detalhes.espera_se_bloqueado (pausa adaptativa — ver Cliente)."""
    det = cfg.get("detalhes") or {}
    esp = det.get("espera") or {}
    blq = det.get("espera_se_bloqueado")
    return Cliente(float(esp.get("min", 1)), float(esp.get("max", 3)),
                   espera_bloqueio=(float(blq.get("min", 0.5)), float(blq.get("max", 1.5)))
                   if blq else None)


class Cliente:
    """GET com espera aleatória entre chamadas e retentativas. Sem cookie.

    Pausa adaptativa: com `espera_bloqueio` (min, max), a primeira falha que indique
    restrição do servidor (HTTP 429, 403, 5xx, timeout ou falha de rede) passa a pausa,
    dali em diante, a no mínimo esses valores. Permite rodar sem pausa (espera 0) e
    recuar sozinho se o PNCP começar a limitar."""

    def __init__(self, espera_min, espera_max, tentativas=3, espera_retry=60,
                 espera_bloqueio=None):
        self.espera_min = espera_min
        self.espera_max = espera_max
        self.tentativas = tentativas
        self.espera_retry = espera_retry
        self.espera_bloqueio = espera_bloqueio
        self.restricoes = 0
        self.primeira = True

    def _recua(self, motivo):
        self.restricoes += 1
        if not self.espera_bloqueio:
            return
        bmin, bmax = self.espera_bloqueio
        if self.espera_max < bmax:
            self.espera_min, self.espera_max = max(self.espera_min, bmin), bmax
            aviso(f"restrição detectada ({motivo}): pausa passa a {self.espera_min:g}–"
                  f"{self.espera_max:g}s entre chamadas até o fim desta execução")

    def _espera(self):
        if self.primeira:
            self.primeira = False
            return
        segundos = random.uniform(self.espera_min, self.espera_max)
        if segundos >= 1:
            log(f"  [aguardando {segundos:.0f}s]")
        time.sleep(segundos)

    def get(self, url, accept="application/json, text/plain, */*"):
        """Retorna (status, bytes). 404 e 204 não são retentados."""
        for tentativa in range(1, self.tentativas + 1):
            self._espera()
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": accept,
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            try:
                with urllib.request.urlopen(req, timeout=90) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as e:
                if e.code in (404, 204):
                    return e.code, b""
                motivo = f"HTTP {e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
                motivo = f"falha de rede: {e}"
            self._recua(motivo)
            if tentativa >= self.tentativas:
                raise RuntimeError(f"{motivo} em {url}")
            log(f"  [{motivo} (tentativa {tentativa}/{self.tentativas}); "
                f"aguardando {self.espera_retry}s]")
            time.sleep(self.espera_retry)
        raise RuntimeError(f"esgotadas as tentativas para {url}")

    def get_json(self, url):
        status, dados = self.get(url)
        if status in (204, 404) or not dados.strip():
            return None
        try:
            return json.loads(dados.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise RuntimeError(f"JSON inválido em {url}: {e}")


# ------------------------------- Pesquisa ----------------------------------

MODELO_PESQUISA = """\
# Pesquisa de contratações similares no PNCP — {slug}
# Gerado por scripts/pesquisa-pncp.py iniciar em {data}. Preencha com o usuário
# (skill pesquisa-precos-pncp) ANTES de rodar "buscar". Esquema e regras:
# decisoes/2026-10-01-pesquisa-precos-pncp.md e docs/pesquisa-pncp.md.

pesquisa:
  slug: "{slug}"
  data_inicio: "{data}"
  # Data-base da pesquisa: referência para a janela de 1 ano do art. 5º, II, da IN 65
  # e para a vigência das atas. Vazio = data de execução de cada comando.
  data_referencia: ""
  responsaveis: []            # IN 65, art. 3º, II — agente(s) ou equipe de planejamento
  # Objetivos (um ou mais): referencia_tecnica | serie_precos | adesao
  objetivos: []
  descricao_objeto: "<descrição do objeto a precificar — IN 65, art. 3º, I>"

contratante:
  orgao: "{orgao}"
  # federal | estadual | distrital | municipal — define a adesão cabível (Lei 14.133, art. 86)
  esfera: "{esfera}"
  poder: "{poder}"

busca:
  # Cada termo é uma consulta à busca do PNCP. Várias palavras = todas devem aparecer
  # (E lógico, sem acento, sem palavras vazias); entre aspas = frase exata.
  # Ex.: '"firewall de aplicação"', 'waf nuvem', 'cdn'.
  termos: []
  tipos_documento: [edital, ata]   # edital | ata | contrato
  status: todos                    # todos = inclui encerradas, revogadas, suspensas
  max_paginas: null                # limite por termo e tipo (null = todas)
  espera: {{min: 10, max: 20}}       # segundos entre chamadas da busca

filtros:
  # Expressões regulares (Python, sem distinção de maiúsculas) sobre título + objeto.
  # Vazio = tudo é pertinente pelo filtro; a decisão final é humana, em triagem.yaml.
  pertinencia_regex: ""
  exclusao_regex: ""
  publicadas_desde: ""             # AAAA-MM-DD, opcional
  esferas: []                      # federal | estadual | distrital | municipal; vazio = todas
  janela_meses: 12                 # IN 65, art. 5º, II

catalogo:
  # Códigos do Catálogo de Materiais e Serviços do Compras.gov.br. Usados pelos comandos
  # painel (Painel de Preços, art. 5º, I) e atas-catalogo (atas que a busca textual perde).
  pdm_material: []                 # PDM (grupo de materiais), ex.: [18374] para FIREWALL
  catmat: []                       # códigos CATMAT específicos (opcional)
  catser: []                       # códigos CATSER (licenças, garantia, serviços)
  # painel_catser: []              # CATSER consultados no Painel; se omitido, usa catser
  marca_regex: ""                  # recorte por modelo no Painel (marca + descrição detalhada)
  texto_regex: ""                  # filtro dos itens de ata pela descrição (útil em CATSER amplos)
  vigencia_inicial_meses: 24       # atas-catalogo: vigência inicial a partir de N meses antes

detalhes:
  espera: {{min: 1, max: 3}}         # segundos entre chamadas na etapa enriquecer/baixar
  # Opcional: pausa mínima adotada após a primeira restrição do servidor (HTTP 429/403/5xx,
  # timeout). Permite espera 0 com recuo automático.
  # espera_se_bloqueado: {{min: 0.5, max: 1.5}}

cautelas:
  - "Preço homologado é o parâmetro; valor estimado da compra de outro órgão não é preço praticado."
  - "Comparar objeto, unidade, quantidade, prazo, local e garantia (IN 65, art. 4º); lote ou grupo exige decomposição."
  - "Janela do art. 5º, II: contratações em execução ou concluídas no ano anterior à data da pesquisa."
  - "Painel de Preços (art. 5º, I): comando painel. Mediana do código de catálogo mistura portes; conferir por modelo e justificar se não usar (art. 5º, §1º)."
  - "Mínimo de três preços (art. 6º); exclusões com critério escrito (art. 6º, §3º); análise crítica da dispersão (§4º)."
  - "Adesão exige ata vigente, previsão de adesão e anuência do gerenciador e do fornecedor (Lei 14.133, art. 86, §2º)."
  - "Dado lido em PDF de proposta é transcrito em nota em anotacoes/ antes de ser citado (docs/ferramentas.md)."
"""


def pasta_da(slug_pesquisa):
    return os.path.join(PASTA_PESQUISAS, slug_pesquisa)


def carrega_pesquisa(slug_pesquisa):
    pasta = pasta_da(slug_pesquisa)
    cfg = le_yaml(os.path.join(pasta, "pesquisa.yaml"))
    if not cfg:
        morre(f"pesquisa não encontrada: {pasta}/pesquisa.yaml (rode: iniciar {slug_pesquisa})")
    return pasta, cfg


def data_referencia(cfg):
    ref = data_iso((cfg.get("pesquisa") or {}).get("data_referencia"))
    return ref or HOJE


def esfera_contratante(cfg):
    esfera = str((cfg.get("contratante") or {}).get("esfera", "")).strip().lower()
    if esfera not in ESFERAS:
        morre("contratante.esfera deve ser federal | estadual | distrital | municipal "
              f"(está: '{esfera}'). Confirme com o usuário e preencha o pesquisa.yaml.")
    return ESFERAS[esfera]


def cmd_iniciar(args):
    pasta = pasta_da(args.slug)
    caminho = os.path.join(pasta, "pesquisa.yaml")
    if os.path.exists(caminho):
        morre(f"já existe: {caminho}")
    meta = le_yaml(METADADOS_ETP, {}) or {}
    orgao = meta.get("orgao") or {}
    nome = orgao.get("nome", "")
    if "<" in str(nome):
        nome = ""
    esfera = str(orgao.get("esfera", "") or "")
    poder = str(orgao.get("poder", "") or "")
    os.makedirs(pasta, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(MODELO_PESQUISA.format(slug=args.slug, data=HOJE.isoformat(),
                                       orgao=nome, esfera=esfera, poder=poder))
    log(f"Criado {os.path.relpath(caminho, RAIZ)}")
    if not esfera:
        aviso("esfera do contratante vazia: confirme com o usuário antes de enriquecer")


# -------------------------------- buscar -----------------------------------

def url_busca(termo, tipo, pagina, status):
    params = {"q": termo, "tipos_documento": tipo, "ordenacao": "-data",
              "pagina": pagina, "tam_pagina": TAM_PAGINA, "status": status}
    return URL_BUSCA + "?" + urllib.parse.urlencode(params)


def pagina_valida(caminho):
    dados = le_json(caminho)
    return bool(dados and isinstance(dados.get("items"), list) and dados["items"])


def cmd_buscar(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    busca = cfg.get("busca") or {}
    termos = [args.termo] if args.termo else list(busca.get("termos") or [])
    if not termos:
        morre("busca.termos vazio no pesquisa.yaml")
    tipos = list(busca.get("tipos_documento") or ["edital", "ata"])
    for t in tipos:
        if t not in TIPOS_DOCUMENTO:
            morre(f"tipo de documento inválido: {t}")
    status = busca.get("status") or "todos"
    max_pag = busca.get("max_paginas")
    esp = busca.get("espera") or {}
    cli = Cliente(float(esp.get("min", 10)), float(esp.get("max", 20)))

    for termo in termos:
        pasta_termo = os.path.join(pasta, "brutos", slug(termo))
        os.makedirs(pasta_termo, exist_ok=True)
        reg_path = os.path.join(pasta_termo, "registro.json")
        registro = le_json(reg_path, {"termo": termo, "consultas": []})
        registro["termo"] = termo
        for tipo in tipos:
            log(f"\n[{termo} | {tipo}]")
            pagina, ultima = 1, None
            while ultima is None or pagina <= ultima:
                arq = os.path.join(pasta_termo, f"{tipo}_pagina{pagina}.json")
                if pagina_valida(arq) and not args.atualizar:
                    dados = le_json(arq)
                else:
                    url = url_busca(termo, tipo, pagina, status)
                    try:
                        dados = cli.get_json(url)
                    except RuntimeError as e:
                        grava_json(reg_path, registro)
                        morre(f"{e}\nRode o mesmo comando de novo para retomar.")
                    if not dados or "items" not in dados:
                        morre(f"resposta sem 'items' em {url}")
                    if not dados["items"]:
                        if pagina == 1:
                            log("  nenhum resultado")
                        break
                    grava_json(arq, dados)
                    registro["consultas"].append({
                        "tipo": tipo, "pagina": pagina, "url": url,
                        "data_hora": agora_iso(), "total": dados.get("total"),
                        "itens": len(dados["items"])})
                    log(f"  página {pagina}: {len(dados['items'])} itens "
                        f"(total da busca: {dados.get('total')})")
                if ultima is None:
                    total = int(dados.get("total") or 0)
                    ultima = max(1, math.ceil(total / TAM_PAGINA))
                    if max_pag and ultima > int(max_pag):
                        aviso(f"'{termo}' ({tipo}): {total} resultados; limitado a "
                              f"{max_pag} página(s) por busca.max_paginas — busca TRUNCADA")
                        ultima = int(max_pag)
                pagina += 1
        grava_json(reg_path, registro)
    log("\nConcluído. Próximo passo: consolidar")


# ------------------------------ consolidar ---------------------------------

RE_CONTROLE = re.compile(r"^(\d{14})-\d-(\d+)/(\d{4})")


def chave_compra(item):
    """Chave 'cnpj/ano/seq' da COMPRA a que o documento pertence."""
    tipo = item.get("document_type")
    if tipo == "contrato":
        m = RE_CONTROLE.match(item.get("numero_contratacao") or "")
    else:
        m = RE_CONTROLE.match(item.get("numero_controle_pncp") or "")
    if not m:
        return None
    cnpj, seq, ano = m.groups()
    return f"{cnpj}/{ano}/{int(seq)}"


def resumo_documento(item):
    campos = ("document_type", "numero_controle_pncp", "title", "data_publicacao_pncp",
              "data_assinatura", "data_inicio_vigencia", "data_fim_vigencia", "cancelado",
              "valor_global", "permite_adesao", "fornecedor_ni", "fornecedor_nome",
              "situacao_nome", "item_url")
    return {k: item.get(k) for k in campos if item.get(k) not in (None, "")}


def cmd_consolidar(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    filtros = cfg.get("filtros") or {}
    re_pert = filtros.get("pertinencia_regex") or ""
    re_excl = filtros.get("exclusao_regex") or ""
    re_pert = re.compile(re_pert, re.I) if re_pert else None
    re_excl = re.compile(re_excl, re.I) if re_excl else None
    desde = data_iso(filtros.get("publicadas_desde"))
    esferas_ok = {ESFERAS[e] for e in (filtros.get("esferas") or []) if e in ESFERAS}

    compras = {}
    por_termo = {}
    for reg_path in sorted(glob.glob(os.path.join(pasta, "brutos", "*", "registro.json"))):
        termo = le_json(reg_path)["termo"]
        chaves_termo = set()
        for arq in sorted(glob.glob(os.path.join(os.path.dirname(reg_path), "*_pagina*.json"))):
            for item in (le_json(arq) or {}).get("items", []):
                chave = chave_compra(item)
                if not chave:
                    aviso(f"documento sem chave de compra: {item.get('numero_controle_pncp')}")
                    continue
                chaves_termo.add(chave)
                cnpj, ano, seq = chave.split("/")
                c = compras.setdefault(chave, {
                    "chave": chave, "cnpj": cnpj, "ano": int(ano), "sequencial": int(seq),
                    "orgao": item.get("orgao_nome"), "unidade": item.get("unidade_nome"),
                    "unidade_codigo": item.get("unidade_codigo"),
                    "uf": item.get("uf"), "municipio": item.get("municipio_nome"),
                    "esfera_id": item.get("esfera_id"), "esfera": item.get("esfera_nome"),
                    "poder": item.get("poder_nome"),
                    "modalidade": item.get("modalidade_licitacao_nome"),
                    "objeto": None, "titulo_edital": None, "situacao": None,
                    "data_publicacao": None,
                    "link_pncp": f"{URL_APP}/{cnpj}/{ano}/{seq}",
                    "termos": [], "tipos": [], "documentos": {}})
                tipo = item.get("document_type")
                if tipo == "edital" or not c["objeto"]:
                    c["objeto"] = (item.get("description") or "").strip()
                if tipo == "edital":
                    c["titulo_edital"] = item.get("title")
                    c["situacao"] = item.get("situacao_nome")
                    c["data_publicacao"] = item.get("data_publicacao_pncp")
                if termo not in c["termos"]:
                    c["termos"].append(termo)
                if tipo not in c["tipos"]:
                    c["tipos"].append(tipo)
                c["documentos"][item.get("numero_controle_pncp")] = resumo_documento(item)
        por_termo[termo] = chaves_termo

    for c in compras.values():
        c["documentos"] = list(c["documentos"].values())
        texto = " ".join([c["objeto"] or ""] + [d.get("title", "") for d in c["documentos"]])
        motivos = []
        if re_pert and not re_pert.search(texto):
            motivos.append("não casa pertinencia_regex")
        if re_excl and re_excl.search(texto):
            motivos.append("casa exclusao_regex")
        datas_doc = [d["data_publicacao_pncp"] for d in c["documentos"]
                     if d.get("data_publicacao_pncp")]
        pub = data_iso(c["data_publicacao"] or (min(datas_doc) if datas_doc else None))
        if desde and pub and pub < desde:
            motivos.append(f"publicada antes de {desde.isoformat()}")
        if esferas_ok and c["esfera_id"] not in esferas_ok:
            motivos.append(f"esfera {c['esfera']} fora do filtro")
        c["passa_filtro"] = not motivos
        c["motivo_filtro"] = "; ".join(motivos)

    # mais recentes primeiro; as que passam no filtro antes das demais (sort estável)
    lista = sorted(compras.values(), key=lambda c: c["data_publicacao"] or "", reverse=True)
    lista.sort(key=lambda c: not c["passa_filtro"])
    grava_json(os.path.join(pasta, "consolidado.json"), {
        "gerado_em": agora_iso(), "pesquisa": args.slug,
        "termos": {t: len(v) for t, v in por_termo.items()},
        "total_compras": len(lista),
        "passam_filtro": sum(c["passa_filtro"] for c in lista),
        "compras": lista})

    with open(os.path.join(pasta, "consolidado.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["chave", "passa_filtro", "motivo_filtro", "orgao", "uf", "esfera",
                    "modalidade", "situacao", "data_publicacao", "tipos", "termos",
                    "objeto", "link_pncp"])
        for c in lista:
            w.writerow([c["chave"], c["passa_filtro"], c["motivo_filtro"], c["orgao"], c["uf"],
                        c["esfera"], c["modalidade"], c["situacao"],
                        (c["data_publicacao"] or "")[:10], "|".join(c["tipos"]),
                        "|".join(c["termos"]), c["objeto"], c["link_pncp"]])

    atualiza_triagem(pasta, lista)

    log(f"Compras distintas: {len(lista)} | passam no filtro: "
        f"{sum(c['passa_filtro'] for c in lista)}")
    log("Compras por termo (antes do filtro):")
    for t, v in por_termo.items():
        exclusivas = v - set().union(*(o for k, o in por_termo.items() if k != t))
        log(f"  {len(v):>6}  {t}  (só este termo: {len(exclusivas)})")
    log("Próximo passo: decidir a triagem em triagem.yaml e rodar enriquecer")


CABECALHO_TRIAGEM = """\
# Triagem humana das compras consolidadas — decisão por compra.
#   decisao: pendente | pertinente | nao_pertinente
#   motivo:  obrigatório para nao_pertinente (rastro da seleção, IN 65, art. 3º, III)
# Só entram compras que passaram no filtro do pesquisa.yaml. "consolidar" acrescenta
# compras novas e NUNCA altera decisão já tomada."""


def atualiza_triagem(pasta, lista):
    caminho = os.path.join(pasta, "triagem.yaml")
    atual = (le_yaml(caminho, {}) or {}).get("compras") or {}
    novas = 0
    for c in lista:
        if not c["passa_filtro"] or c["chave"] in atual:
            continue
        atual[c["chave"]] = {
            "orgao": c["orgao"], "uf": c["uf"], "esfera": c["esfera"],
            "modalidade": c["modalidade"], "publicacao": (c["data_publicacao"] or "")[:10],
            "objeto": re.sub(r"\s+", " ", c["objeto"] or "")[:300],
            "link": c["link_pncp"], "decisao": "pendente", "motivo": ""}
        novas += 1
    grava_yaml(caminho, {"compras": atual}, CABECALHO_TRIAGEM)
    pend = sum(1 for v in atual.values() if v.get("decisao") == "pendente")
    log(f"triagem.yaml: {novas} compra(s) nova(s); {pend} pendente(s)")


def compras_selecionadas(pasta, args):
    consolidado = le_json(os.path.join(pasta, "consolidado.json"))
    if not consolidado:
        morre("consolidado.json ausente: rode consolidar")
    por_chave = {c["chave"]: c for c in consolidado["compras"]}
    if getattr(args, "chaves", None):
        faltam = [k for k in args.chaves if k not in por_chave]
        if faltam:
            morre(f"chave(s) fora do consolidado: {', '.join(faltam)}")
        return [por_chave[k] for k in args.chaves]
    if getattr(args, "todos_filtrados", False):
        return [c for c in consolidado["compras"] if c["passa_filtro"]]
    triagem = (le_yaml(os.path.join(pasta, "triagem.yaml"), {}) or {}).get("compras") or {}
    sel = [por_chave[k] for k, v in triagem.items()
           if v.get("decisao") == "pertinente" and k in por_chave]
    if not sel:
        morre("nenhuma compra 'pertinente' em triagem.yaml (ou use --todos-filtrados)")
    return sel


# ------------------------------ enriquecer ---------------------------------

def busca_detalhes(cli, c, pasta, atualizar):
    cnpj, ano, seq = c["cnpj"], c["ano"], c["sequencial"]
    pasta_det = os.path.join(pasta, "detalhes")
    os.makedirs(pasta_det, exist_ok=True)
    caminho = os.path.join(pasta_det, f"{cnpj}_{ano}_{seq}.json")
    cache = le_json(caminho)
    if cache and not atualizar:
        return cache

    base = f"{URL_PNCP}/{cnpj}/compras/{ano}/{seq}"
    det = {"chave": c["chave"], "consultado_em": agora_iso(), "fontes": {}}
    url = f"{URL_CONSULTA}/{cnpj}/compras/{ano}/{seq}"
    det["fontes"]["compra"] = url
    det["compra"] = cli.get_json(url)

    itens, pagina = [], 1
    while True:
        url = f"{base}/itens?pagina={pagina}&tamanhoPagina=500"
        lote = cli.get_json(url) or []
        itens.extend(lote)
        if len(lote) < 500:
            break
        pagina += 1
    det["fontes"]["itens"] = f"{base}/itens"
    for it in itens:
        it["resultados"] = []
        if it.get("temResultado"):
            it["resultados"] = cli.get_json(f"{base}/itens/{it['numeroItem']}/resultados") or []
    det["itens"] = itens

    atas = cli.get_json(f"{base}/atas")
    atas = (atas or {}).get("data", atas) if isinstance(atas, dict) else (atas or [])
    for ata in atas:
        det_ata = cli.get_json(f"{base}/atas/{ata.get('sequencialAta')}")
        if det_ata:
            ata["possibilidadeAdesao"] = det_ata.get("possibilidadeAdesao")
    det["atas"] = atas
    det["fontes"]["atas"] = f"{base}/atas"
    det["arquivos"] = [a for a in (cli.get_json(f"{base}/arquivos") or [])
                       if a.get("statusAtivo", True)]
    det["fontes"]["arquivos"] = f"{base}/arquivos"
    grava_json(caminho, det)
    return det


def id_cnetmobile(link):
    m = re.search(r"[?&]compra=(\d+)", link or "")
    return m.group(1) if m else None


def classifica_adesao(c, det, esfera_contr, ref):
    """Adesão como não participante (Lei 14.133, art. 86, §§2º, 3º e 8º)."""
    compra = det.get("compra") or {}
    if not compra.get("srp"):
        return "nao_srp", "compra não é registro de preços", []
    esfera_ger = ((compra.get("orgaoEntidade") or {}).get("esferaId")
                  or c.get("esfera_id") or "N")
    modalidade = (compra.get("modalidadeNome") or c.get("modalidade") or "").lower()
    licitada = not any(m in modalidade for m in MODALIDADES_SEM_LICITACAO)

    if esfera_ger not in ("F", "E", "D", "M"):
        regra = ("indeterminado", f"esfera do gerenciador não identificada ({esfera_ger})")
    elif esfera_contr == "F" and esfera_ger != "F":
        regra = ("nao_pela_esfera", "art. 86, §8º: vedada ao federal a adesão a ata "
                 f"{NOME_ESFERA[esfera_ger].lower()}")
    elif esfera_contr in ("E", "D") and esfera_ger == "M":
        regra = ("nao_pela_esfera", "art. 86, §3º: ata municipal só admite adesão municipal")
    elif esfera_contr == "M" and esfera_ger == "M" and not licitada:
        regra = ("nao_pela_esfera", "art. 86, §3º, II: SRP municipal não formalizado por licitação")
    else:
        regra = ("sim", "esfera compatível (art. 86, §3º)")

    atas_cls = []
    for ata in det.get("atas") or []:
        fim = data_iso(ata.get("dataVigenciaFim"))
        ini = data_iso(ata.get("dataVigenciaInicio"))
        vigente = (not ata.get("cancelado") and fim is not None and fim >= ref
                   and (ini is None or ini <= ref))
        atas_cls.append({
            "numero": f"{ata.get('numeroAtaRegistroPreco')}/{ata.get('anoAta')}",
            "controle": ata.get("numeroControlePNCP"),
            "vigencia": f"{ata.get('dataVigenciaInicio')} a {ata.get('dataVigenciaFim')}",
            "cancelada": bool(ata.get("cancelado")), "vigente": vigente,
            "possibilidade_adesao": ata.get("possibilidadeAdesao")})

    if regra[0] != "sim":
        return regra[0], regra[1], atas_cls
    if not atas_cls:
        return "sem_ata_publicada", "SRP sem ata publicada no PNCP", atas_cls
    vigentes = [a for a in atas_cls if a["vigente"]]
    if not vigentes:
        return "ata_vencida", "nenhuma ata vigente na data de referência", atas_cls
    if any(a["possibilidade_adesao"] is True for a in vigentes):
        return "sim", (regra[1] + "; ata vigente com adesão prevista — depende ainda de "
                       "anuência do gerenciador e do fornecedor (§2º, III) e dos limites "
                       "dos §§4º e 5º"), atas_cls
    if all(a["possibilidade_adesao"] is False for a in vigentes):
        return "nao_prevista_na_ata", "ata vigente sem previsão de adesão", atas_cls
    return "indeterminado", "ata vigente sem informação de adesão no PNCP: conferir edital", atas_cls


def classifica_tempestividade(det, c, ref, janela):
    """IN 65, art. 5º, II: em execução ou concluída no período de 1 ano anterior."""
    limite = meses_antes(ref, janela)
    # em execução: ata ou contrato com vigência que alcança a data de referência
    vigencias = [(data_iso(a.get("dataVigenciaInicio")), data_iso(a.get("dataVigenciaFim")))
                 for a in det.get("atas") or [] if not a.get("cancelado")]
    vigencias += [(data_iso(d.get("data_inicio_vigencia")), data_iso(d.get("data_fim_vigencia")))
                  for d in c.get("documentos") or [] if d.get("document_type") == "contrato"
                  and not d.get("cancelado")]
    for ini, fim in vigencias:
        if fim and fim >= ref and (ini is None or ini <= ref):
            return "em_execucao", f"vigência até {dmy(fim)}"
    datas = [data_iso(r.get("dataResultado")) for it in det.get("itens") or []
             for r in it.get("resultados") or []]
    datas += [fim for _, fim in vigencias]
    datas = [d for d in datas if d]
    if not datas:
        return "sem_resultado", "sem resultado nem vigência informados no PNCP"
    ultima = max(datas)
    if ultima >= limite:
        return "dentro_12_meses", f"último marco em {dmy(ultima)} (limite {dmy(limite)})"
    return "fora", f"último marco em {dmy(ultima)}, anterior a {dmy(limite)}"


def linhas_itens(c, det, cls):
    """Uma linha por item × resultado (ou por item sem resultado)."""
    linhas = []
    for it in det.get("itens") or []:
        resultados = it.get("resultados") or [None]
        for r in resultados:
            linhas.append({
                "chave": c["chave"], "orgao": c["orgao"], "uf": c["uf"], "esfera": c["esfera"],
                "modalidade": c["modalidade"], "srp": cls["srp"],
                "situacao_compra": cls["situacao_compra"],
                "item": it.get("numeroItem"),
                "descricao": re.sub(r"\s+", " ", it.get("descricao") or "")[:400],
                "material_servico": it.get("materialOuServicoNome"),
                "unidade": it.get("unidadeMedida"), "quantidade": it.get("quantidade"),
                "situacao_item": it.get("situacaoCompraItemNome"),
                "criterio": it.get("criterioJulgamentoNome"),
                "valor_unitario_estimado": it.get("valorUnitarioEstimado"),
                "resultado": r.get("sequencialResultado") if r else None,
                "valor_unitario_homologado": r.get("valorUnitarioHomologado") if r else None,
                "quantidade_homologada": r.get("quantidadeHomologada") if r else None,
                "percentual_desconto": r.get("percentualDesconto") if r else None,
                "moeda_estrangeira": r.get("moedaEstrangeira") if r else None,
                "vencedor": r.get("nomeRazaoSocialFornecedor") if r else None,
                "cnpj_vencedor": r.get("niFornecedor") if r else None,
                "data_resultado": r.get("dataResultado") if r else None,
                "resultado_cancelado": bool(r and r.get("dataCancelamento")),
                "tempestividade": cls["tempestividade"], "adesao": cls["adesao"],
                "link_pncp": c["link_pncp"],
                "link_item_cnetmobile": (URL_CNET_ITEM.format(item=it.get("numeroItem"),
                                                              compra=cls["id_cnetmobile"])
                                         if cls["id_cnetmobile"] else ""),
            })
    return linhas


def cmd_enriquecer(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    esfera_contr = esfera_contratante(cfg)
    ref = data_referencia(cfg)
    janela = int((cfg.get("filtros") or {}).get("janela_meses") or 12)
    cli = cliente_detalhes(cfg)
    selecao = compras_selecionadas(pasta, args)
    log(f"Enriquecendo {len(selecao)} compra(s); contratante {NOME_ESFERA[esfera_contr]}; "
        f"data de referência {dmy(ref)}")

    saida, linhas, falhas = [], [], []
    for i, c in enumerate(selecao, 1):
        log(f"[{i}/{len(selecao)}] {c['chave']} — {c['orgao']}")
        try:
            det = busca_detalhes(cli, c, pasta, args.atualizar)
        except RuntimeError as e:
            aviso(f"  falha: {e}")
            falhas.append(c["chave"])
            continue
        compra = det.get("compra") or {}
        adesao, motivo_adesao, atas = classifica_adesao(c, det, esfera_contr, ref)
        tempo, motivo_tempo = classifica_tempestividade(det, c, ref, janela)
        link_origem = compra.get("linkSistemaOrigem") or ""
        cls = {
            "chave": c["chave"], "orgao": c["orgao"], "unidade": c["unidade"],
            "uasg": (compra.get("unidadeOrgao") or {}).get("codigoUnidade"),
            "uf": c["uf"], "esfera": c["esfera"], "modalidade": compra.get("modalidadeNome")
            or c["modalidade"], "numero_compra": compra.get("numeroCompra"),
            "processo": compra.get("processo"), "objeto": compra.get("objetoCompra")
            or c["objeto"], "srp": bool(compra.get("srp")),
            "situacao_compra": compra.get("situacaoCompraNome") or c.get("situacao"),
            "existe_resultado": compra.get("existeResultado"),
            "valor_total_estimado": compra.get("valorTotalEstimado"),
            "valor_total_homologado": compra.get("valorTotalHomologado"),
            "data_publicacao": compra.get("dataPublicacaoPncp"),
            "adesao": adesao, "motivo_adesao": motivo_adesao, "atas": atas,
            "tempestividade": tempo, "motivo_tempestividade": motivo_tempo,
            "link_pncp": c["link_pncp"], "link_sistema_origem": link_origem,
            "id_cnetmobile": id_cnetmobile(link_origem)
            if "cnetmobile" in link_origem else None,
            "arquivos_pncp": len(det.get("arquivos") or []),
            "consultado_em": det.get("consultado_em"), "termos": c["termos"],
        }
        if cls["situacao_compra"] and cls["situacao_compra"] != "Divulgada no PNCP":
            aviso(f"  situação da compra: {cls['situacao_compra']} (mantida e sinalizada)")
        saida.append(cls)
        linhas.extend(linhas_itens(c, det, cls))

    grava_json(os.path.join(pasta, "classificado.json"), {
        "gerado_em": agora_iso(), "data_referencia": ref.isoformat(),
        "esfera_contratante": NOME_ESFERA[esfera_contr], "janela_meses": janela,
        "compras": saida})
    if linhas:
        with open(os.path.join(pasta, "classificado.csv"), "w", newline="",
                  encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
            w.writeheader()
            w.writerows(linhas)
    gera_roteiro_propostas(pasta, saida)

    def conta(campo):
        cont = {}
        for s in saida:
            cont[s[campo]] = cont.get(s[campo], 0) + 1
        return ", ".join(f"{k}: {v}" for k, v in sorted(cont.items()))
    log(f"\nCompras classificadas: {len(saida)}")
    log(f"  tempestividade (IN 65, art. 5º, II): {conta('tempestividade')}")
    log(f"  SRP: {sum(s['srp'] for s in saida)} de {len(saida)}")
    log(f"  adesão para contratante {NOME_ESFERA[esfera_contr].lower()}: {conta('adesao')}")
    log(f"  itens com preço homologado: "
        f"{sum(1 for l in linhas if l['valor_unitario_homologado'] is not None)}")
    if falhas:
        morre(f"{len(falhas)} compra(s) com falha — rode de novo para retomar: "
              + ", ".join(falhas))


# ------------------------------- propostas ---------------------------------

def pasta_proposta(pasta, cls, item):
    ident = cls.get("id_cnetmobile") or cls["chave"].replace("/", "_")
    return os.path.join(pasta, "propostas", ident, f"item-{item}")


def gera_roteiro_propostas(pasta, classificadas):
    linhas = [
        "# Propostas a obter no Compras.gov.br",
        "",
        "<!-- Gerado por scripts/pesquisa-pncp.py (enriquecer/propostas). Não editar. -->",
        "",
        "As páginas públicas do Compras.gov.br exigem captcha: a obtenção é **manual**.",
        "Para cada item: abra o link, localize a proposta **adjudicada/homologada** (ignore",
        "as desclassificadas), baixe os anexos (em geral um PDF ou ZIP com \"proposta\" no",
        "nome) e salve na pasta indicada. Depois rode `propostas <slug>` para atualizar",
        "esta lista. Itens em grupo/lote podem ter numeração própria no Compras.gov.br.",
        "",
        "Dado lido em proposta (marca, modelo, condições comerciais) é transcrito em nota",
        "em `anotacoes/` antes de ser citado (docs/ferramentas.md).",
        "",
    ]
    total = obtidas = 0
    for cls in classificadas:
        det = le_json(os.path.join(pasta, "detalhes",
                                   cls["chave"].replace("/", "_") + ".json")) or {}
        itens = [it for it in det.get("itens") or [] if it.get("resultados")]
        if not itens:
            continue
        linhas.append(f"## {cls['orgao']} — {cls['modalidade']} nº "
                      f"{cls['numero_compra']}/{cls['chave'].split('/')[1]}"
                      f" (UASG {cls['uasg']})")
        linhas.append("")
        linhas.append(f"- PNCP: {cls['link_pncp']}")
        if cls["id_cnetmobile"]:
            linhas.append(f"- Compras.gov.br: "
                          f"{URL_CNET_COMPRA.format(compra=cls['id_cnetmobile'])}")
        elif cls["link_sistema_origem"]:
            linhas.append(f"- Sistema de origem (não é o Compras.gov.br): "
                          f"{cls['link_sistema_origem']}")
        else:
            linhas.append("- Sem link de sistema de origem no PNCP: procurar a proposta "
                          "nos arquivos da compra ou junto ao órgão.")
        linhas.append("")
        for it in itens:
            for r in it["resultados"]:
                destino = pasta_proposta(pasta, cls, it["numeroItem"])
                tem = os.path.isdir(destino) and any(
                    not n.startswith(".") for n in os.listdir(destino))
                total += 1
                obtidas += tem
                marca = "x" if tem else " "
                link = (URL_CNET_ITEM.format(item=it["numeroItem"], compra=cls["id_cnetmobile"])
                        if cls["id_cnetmobile"] else "—")
                desc = re.sub(r"\s+", " ", it.get("descricao") or "")[:120]
                linhas.append(
                    f"- [{marca}] Item {it['numeroItem']} — {desc} | vencedor: "
                    f"{r.get('nomeRazaoSocialFornecedor')} ({r.get('niFornecedor')}) | "
                    f"unitário homologado: {brl(r.get('valorUnitarioHomologado'))} | "
                    f"link: {link} | salvar em: `{os.path.relpath(destino, pasta)}/`")
        linhas.append("")
    linhas.insert(4, f"Obtidas: **{obtidas} de {total}**.")
    linhas.insert(5, "")
    with open(os.path.join(pasta, "propostas-a-obter.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas).rstrip() + "\n")
    log(f"propostas-a-obter.md: {obtidas} de {total} proposta(s) já obtida(s)")


def cmd_propostas(args):
    pasta, _ = carrega_pesquisa(args.slug)
    classificado = le_json(os.path.join(pasta, "classificado.json"))
    if not classificado:
        morre("classificado.json ausente: rode enriquecer")
    gera_roteiro_propostas(pasta, classificado["compras"])
    # pastas de propostas que não correspondem a nenhuma compra classificada
    esperadas = {os.path.normpath(os.path.dirname(pasta_proposta(pasta, c, 0)))
                 for c in classificado["compras"]}
    for d in glob.glob(os.path.join(pasta, "propostas", "*")):
        if os.path.normpath(d) not in esperadas:
            aviso(f"pasta sem compra correspondente: {os.path.relpath(d, RAIZ)}")


# -------------------------------- baixar -----------------------------------

def baixa_arquivo(cli, url, destino, forca=False):
    if os.path.exists(destino) and not forca:
        return "existente"
    sem_ext = not re.search(r"\.[A-Za-z0-9]{1,4}$", destino)
    if sem_ext and not forca and [g for g in glob.glob(glob.escape(destino) + ".*")
                                  if not g.endswith(TEMP_SUFFIX)]:
        return "existente"
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    status, dados = cli.get(url, accept="*/*")
    if status in (204, 404) or not dados:
        raise RuntimeError(f"arquivo indisponível ({status}): {url}")
    if dados[:15].lower().lstrip().startswith(b"<!doctype html") or b"<html" in dados[:200]:
        raise RuntimeError(f"resposta HTML em vez de arquivo: {url}")
    if sem_ext:
        ext = descobre_extensao(dados)
        if ext:
            destino += ext
            if os.path.exists(destino) and not forca:
                return "existente"
    tmp = destino + TEMP_SUFFIX
    with open(tmp, "wb") as f:
        f.write(dados)
    os.replace(tmp, destino)
    log(f"  ok: {os.path.basename(destino)} ({len(dados):,} bytes)")
    return "baixado"


def cmd_baixar(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    cli = cliente_detalhes(cfg)
    selecao = compras_selecionadas(pasta, args)
    saida = os.path.abspath(args.saida)
    falhas = 0
    for i, c in enumerate(selecao, 1):
        det = le_json(os.path.join(pasta, "detalhes",
                                   f"{c['cnpj']}_{c['ano']}_{c['sequencial']}.json"))
        # O nome do órgão no índice de busca do PNCP pode divergir do CNPJ: em contratação
        # anterior, o índice deu a uma autarquia federal o nome de outro órgão. O detalhe da
        # compra (razão social do CNPJ) prevalece.
        orgao = (((det or {}).get("compra") or {}).get("orgaoEntidade") or {}).get("razaoSocial") \
            or c["orgao"] or "orgao"
        nome_pasta = f"{slug(orgao)}_{c['cnpj']}_{c['ano']}_{c['sequencial']}"
        log(f"[{i}/{len(selecao)}] {nome_pasta}")
        try:
            arquivos = (det or {}).get("arquivos")
            if arquivos is None:
                base = f"{URL_PNCP}/{c['cnpj']}/compras/{c['ano']}/{c['sequencial']}"
                arquivos = [a for a in (cli.get_json(f"{base}/arquivos") or [])
                            if a.get("statusAtivo", True)]
        except RuntimeError as e:
            aviso(f"  falha ao listar: {e}")
            falhas += 1
            continue
        if not arquivos:
            log("  sem arquivos publicados")
        usados = set()
        for a in arquivos:
            seq_doc = a.get("sequencialDocumento")
            titulo = sanitiza_nome(a.get("titulo") or f"arquivo_{seq_doc}")
            nome = f"{slug(orgao)}_{titulo}"
            if nome in usados:
                base_n, _, ext = nome.rpartition(".")
                nome = f"{base_n}_{seq_doc}.{ext}" if base_n else f"{nome}_{seq_doc}"
            usados.add(nome)
            url = a.get("url") or (f"{URL_PNCP}/{c['cnpj']}/compras/{c['ano']}/"
                                   f"{c['sequencial']}/arquivos/{seq_doc}")
            try:
                if baixa_arquivo(cli, url, os.path.join(saida, nome_pasta, nome),
                                 args.forca) == "existente":
                    log(f"  já baixado: {nome}")
            except RuntimeError as e:
                aviso(f"  falha: {e}")
                falhas += 1
    if falhas:
        morre(f"{falhas} falha(s) — rode de novo para retomar")
    log("Concluído sem falhas.")


# -------------------------------- serie ------------------------------------

CABECALHO_SERIE = """\
# Série de preços para o preço estimado (IN SEGES/ME 65/2021, arts. 5º e 6º).
# Editado pelo humano; o valor de cada preço do PNCP é lido de detalhes/, NUNCA digitado.
#   metodo: media | mediana | menor (art. 6º)
#   precos[].origem: pncp  -> chave, item, resultado (sequencialResultado; padrão 1)
#                    externo -> parametro_in65 (I | III | IV | V), valor, fonte, data
#   fator_conversao: converte o preço para a unidade comparável (ex.: 1/12 para mensal).
#                    Diferente de 1 exige "memoria_conversao".
#   fator_atualizacao: índice de atualização de preços (art. 5º, II). Diferente de 1
#                    exige "fonte_atualizacao".
#   excluir: true exige "motivo_exclusao" (art. 6º, §3º: critério fundamentado).
#   limiar_sinalizacao: apenas SINALIZA valores distantes da mediana para a análise
#                    crítica (art. 6º, §4º). Não é critério normativo e não exclui nada."""


def candidatos_serie(pasta):
    cand = []
    for arq in sorted(glob.glob(os.path.join(pasta, "detalhes", "*.json"))):
        det = le_json(arq)
        for it in det.get("itens") or []:
            for r in it.get("resultados") or []:
                if r.get("valorUnitarioHomologado") is not None and not r.get("dataCancelamento"):
                    cand.append({
                        "origem": "pncp", "chave": det["chave"], "item": it["numeroItem"],
                        "resultado": r.get("sequencialResultado", 1),
                        "descricao": re.sub(r"\s+", " ", it.get("descricao") or "")[:160],
                        "fator_conversao": 1, "memoria_conversao": "",
                        "fator_atualizacao": 1, "fonte_atualizacao": "",
                        "excluir": False, "motivo_exclusao": ""})
    return cand


def resolve_preco(pasta, p):
    """Retorna dict com valor bruto e metadados, ou levanta ValueError."""
    if p.get("origem", "pncp") == "externo":
        for campo in ("parametro_in65", "valor", "fonte", "data"):
            if p.get(campo) in (None, ""):
                raise ValueError(f"preço externo sem '{campo}'")
        if str(p["parametro_in65"]) not in ("I", "III", "IV", "V"):
            raise ValueError("parametro_in65 deve ser I, III, IV ou V")
        return {"valor": float(p["valor"]), "orgao": p.get("descricao_fonte") or p["fonte"],
                "compra": "—", "item": "—", "data": data_iso(p["data"]),
                "fornecedor": p.get("fornecedor", "—"), "fonte": p["fonte"],
                "parametro": f"art. 5º, {p['parametro_in65']}", "descricao": p.get("descricao", "")}
    chave = p.get("chave")
    if not chave:
        raise ValueError("preço do PNCP sem 'chave'")
    det = le_json(os.path.join(pasta, "detalhes", chave.replace("/", "_") + ".json"))
    if not det:
        raise ValueError(f"{chave}: detalhes ausentes (rode enriquecer)")
    item = next((it for it in det.get("itens") or [] if it.get("numeroItem") == p.get("item")),
                None)
    if not item:
        raise ValueError(f"{chave}: item {p.get('item')} inexistente")
    seq = p.get("resultado", 1)
    r = next((r for r in item.get("resultados") or []
              if r.get("sequencialResultado", 1) == seq), None)
    if not r or r.get("valorUnitarioHomologado") is None:
        raise ValueError(f"{chave} item {p.get('item')}: sem resultado {seq} homologado")
    if r.get("moedaEstrangeira"):
        raise ValueError(f"{chave} item {p.get('item')}: preço em moeda estrangeira — "
                         "converter e lançar como externo, com câmbio e fonte")
    compra = det.get("compra") or {}
    orgao = (compra.get("unidadeOrgao") or {}).get("nomeUnidade") or \
        (compra.get("orgaoEntidade") or {}).get("razaoSocial")
    cnpj, ano, sq = chave.split("/")
    return {"valor": float(r["valorUnitarioHomologado"]), "orgao": orgao,
            "compra": f"{compra.get('modalidadeNome')} nº {compra.get('numeroCompra')}/{ano} "
                      f"(UASG {(compra.get('unidadeOrgao') or {}).get('codigoUnidade')})",
            "item": p.get("item"), "data": data_iso(r.get("dataResultado")),
            "fornecedor": r.get("nomeRazaoSocialFornecedor"),
            "fonte": f"{URL_APP}/{cnpj}/{ano}/{sq}",
            "consulta": data_iso(det.get("consultado_em")),
            "parametro": "art. 5º, II",
            "descricao": re.sub(r"\s+", " ", item.get("descricao") or "")[:160],
            "unidade": item.get("unidadeMedida"), "quantidade": r.get("quantidadeHomologada")}


def cmd_serie(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    caminho = os.path.join(pasta, "serie-precos.yaml")
    serie = le_yaml(caminho)
    if not serie or args.candidatos:
        cand = candidatos_serie(pasta)
        if serie and args.candidatos:
            caminho = os.path.join(pasta, "serie-precos.candidatos.yaml")
        grava_yaml(caminho, {
            "descricao_item": "<item da contratação a precificar>",
            "unidade_comparavel": "<unidade>", "metodo": "mediana",
            "limiar_sinalizacao": {"inferior": 0.5, "superior": 1.5},
            "precos": cand}, CABECALHO_SERIE)
        log(f"Gerado {os.path.relpath(caminho, RAIZ)} com {len(cand)} preço(s) candidato(s) "
            "do PNCP. Remova os não comparáveis, ajuste conversões e exclusões, e rode serie de novo.")
        return

    metodo = serie.get("metodo", "mediana")
    if metodo not in ("media", "mediana", "menor"):
        morre("metodo deve ser media | mediana | menor (art. 6º)")
    lim = serie.get("limiar_sinalizacao") or {}
    erros, linhas = [], []
    for n, p in enumerate(serie.get("precos") or [], 1):
        try:
            info = resolve_preco(pasta, p)
        except ValueError as e:
            erros.append(f"preço {n}: {e}")
            continue
        fc = float(p.get("fator_conversao") or 1)
        fa = float(p.get("fator_atualizacao") or 1)
        if fc != 1 and not p.get("memoria_conversao"):
            erros.append(f"preço {n}: fator_conversao sem memoria_conversao")
        if fa != 1 and not p.get("fonte_atualizacao"):
            erros.append(f"preço {n}: fator_atualizacao sem fonte_atualizacao")
        if p.get("excluir") and not p.get("motivo_exclusao"):
            erros.append(f"preço {n}: excluído sem motivo_exclusao (art. 6º, §3º)")
        info.update(n=n, valor_comparavel=info["valor"] * fc * fa, fc=fc, fa=fa,
                    excluir=bool(p.get("excluir")), motivo=p.get("motivo_exclusao", ""),
                    conversao=p.get("memoria_conversao", ""),
                    atualizacao=p.get("fonte_atualizacao", ""))
        linhas.append(info)
    if erros:
        morre("serie-precos.yaml inconsistente:\n  " + "\n  ".join(erros))

    validos = [l["valor_comparavel"] for l in linhas if not l["excluir"]]
    alertas = []
    if len(validos) < 3:
        alertas.append(f"Apenas {len(validos)} preço(s) válido(s): o art. 6º exige três ou mais; "
                       "abaixo disso, justificativa do gestor e aprovação da autoridade "
                       "competente (art. 6º, §5º).")
    est = {}
    if validos:
        est = {"n": len(validos), "media": statistics.mean(validos),
               "mediana": statistics.median(validos), "menor": min(validos),
               "maior": max(validos)}
        if len(validos) > 1:
            est["desvio"] = statistics.stdev(validos)
            est["cv"] = est["desvio"] / est["media"] if est["media"] else None
    for l in linhas:
        l["sinal"] = ""
        if est and not l["excluir"]:
            razao = l["valor_comparavel"] / est["mediana"] if est["mediana"] else 1
            if razao < float(lim.get("inferior", 0.5)):
                l["sinal"] = f"↓ {razao:.0%} da mediana"
            elif razao > float(lim.get("superior", 1.5)):
                l["sinal"] = f"↑ {razao:.0%} da mediana"
    if any(l["sinal"] for l in linhas):
        alertas.append("Há valores sinalizados pelo limiar: analisar criticamente (art. 6º, §4º) "
                       "e, se for o caso, excluir com critério escrito (§3º).")
    if any(l["parametro"] == "art. 5º, II" for l in linhas):
        ref = data_referencia(cfg)
        limite = meses_antes(ref, int((cfg.get("filtros") or {}).get("janela_meses") or 12))
        velhos = [l for l in linhas if l["parametro"] == "art. 5º, II" and l["data"]
                  and l["data"] < limite and not l["excluir"]]
        if velhos:
            alertas.append(f"{len(velhos)} preço(s) do PNCP com resultado anterior a "
                           f"{dmy(limite)}: confirmar que o contrato está em execução "
                           "(art. 5º, II) ou excluir.")

    escreve_serie_md(pasta, cfg, serie, linhas, est, metodo, alertas)
    log(f"Gerado serie-precos.md: {len(validos)} preço(s) válido(s) de {len(linhas)}")
    if est:
        log(f"  média {brl(est['media'])} | mediana {brl(est['mediana'])} | "
            f"menor {brl(est['menor'])} | método: {metodo} → "
            f"{brl(est[metodo])}")
    for a in alertas:
        aviso(a)


def escreve_serie_md(pasta, cfg, serie, linhas, est, metodo, alertas):
    p = cfg.get("pesquisa") or {}
    out = [
        f"# Série de preços — {serie.get('descricao_item')}",
        "",
        "<!-- Gerado por scripts/pesquisa-pncp.py serie a partir de serie-precos.yaml. "
        "Não editar. -->",
        "",
        f"- Objeto: {p.get('descricao_objeto', '')} (IN 65, art. 3º, I)",
        f"- Responsáveis: {', '.join(p.get('responsaveis') or []) or '<preencher>'} "
        "(art. 3º, II)",
        f"- Unidade comparável: {serie.get('unidade_comparavel')}",
        f"- Data de referência: {dmy(data_referencia(cfg))}",
        f"- Método (art. 6º): **{ {'media': 'média', 'mediana': 'mediana', 'menor': 'menor valor'}[metodo] }**",
        "",
        "## Série de preços coletados (art. 3º, III e IV)",
        "",
        "| # | Parâmetro | Órgão / fonte | Compra | Item | Data | Fornecedor | Unitário | "
        "Comparável | Situação |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for l in linhas:
        situacao = f"excluído: {l['motivo']}" if l["excluir"] else (l["sinal"] or "válido")
        out.append(f"| {l['n']} | {l['parametro']} | {l['orgao']} | {l['compra']} | {l['item']} "
                   f"| {dmy(l['data'])} | {l['fornecedor']} | {brl(l['valor'])} | "
                   f"{brl(l['valor_comparavel'])} | {situacao} |")
    out += ["", "## Estatísticas sobre os preços válidos (art. 3º, V)", ""]
    if est:
        out += [f"- Quantidade: {est['n']}",
                f"- Média: {brl(est['media'])}",
                f"- Mediana: {brl(est['mediana'])}",
                f"- Menor valor: {brl(est['menor'])}",
                f"- Maior valor: {brl(est['maior'])}"]
        if est.get("cv") is not None:
            cv = f"{est['cv']:.1%}".replace(".", ",")
            out.append(f"- Desvio padrão: {brl(est['desvio'])}; coeficiente de variação: "
                       f"{cv} (análise crítica, art. 6º, §4º)")
        out += ["", f"**Preço estimado unitário pelo método adotado: {brl(est[metodo])}**"]
    else:
        out.append("Sem preços válidos.")
    out += ["", "## Memória de cálculo (art. 3º, VII)", ""]
    for l in linhas:
        txt = f"{l['n']}. {brl(l['valor'])}"
        if l["fc"] != 1:
            txt += f" × {l['fc']:g} ({l['conversao']})"
        if l["fa"] != 1:
            txt += f" × {l['fa']:g} ({l['atualizacao']})"
        txt += f" = {brl(l['valor_comparavel'])}. Fonte: {l['fonte']}"
        if l.get("consulta"):
            txt += f", consulta em {dmy(l['consulta'])}"
        out.append(txt + ".")
    if alertas:
        out += ["", "## Alertas", ""] + [f"- {a}" for a in alertas]
    out += ["", "## Cautelas registradas na pesquisa", ""]
    out += [f"- {c}" for c in cfg.get("cautelas") or []]
    out += ["", "## Sugestão de entradas para etp/fontes.yaml (não gravadas)", "",
            "```yaml"]
    vistos = set()
    for l in linhas:
        if l["fonte"] in vistos or l["parametro"] != "art. 5º, II":
            continue
        vistos.add(l["fonte"])
        out += [f"  - id: F-nn",
                f"    documento: \"{l['orgao']}, {l['compra']} — resultado no PNCP\"",
                f"    endereco: \"{l['fonte']}\"",
                f"    consulta: \"{dmy(l.get('consulta'))}\""]
    out += ["```", ""]
    with open(os.path.join(pasta, "serie-precos.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out))


# -------------------------------- saldo ------------------------------------
# Saldo de adesão nas atas vigentes (Lei 14.133, art. 86, §§4º e 5º). O PNCP não informa
# saldo; ele vem da API de dados abertos do Compras.gov.br (modulo-arp), sem autenticação.

URL_ARP = "https://dadosabertos.compras.gov.br/modulo-arp"
LIMITE_POR_ORGAO = 0.5   # art. 86, §4º: até 50% do registrado, por órgão não participante


def num(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def fmt_qtd(valor, casas=0):
    if valor is None:
        return "—"
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def consulta_arp(cli, endpoint, **params):
    url = f"{URL_ARP}/{endpoint}?" + urllib.parse.urlencode(params)
    return url, (cli.get_json(url) or {})


def link_ata_pncp(controle):
    m = re.match(r"(\d{14})-\d-0*(\d+)/(\d{4})-0*(\d+)", controle or "")
    return (f"https://pncp.gov.br/app/atas/{m.group(1)}/{m.group(3)}/{m.group(2)}/{m.group(4)}"
            if m else "")


def cmd_saldo(args):
    pasta, cfg = carrega_pesquisa(args.slug)
    classificado = le_json(os.path.join(pasta, "classificado.json"))
    if not classificado:
        morre("classificado.json ausente: rode enriquecer")
    ref = data_referencia(cfg)
    rx = re.compile((cfg.get("filtros") or {}).get("pertinencia_regex") or ".", re.I)
    cli = cliente_detalhes(cfg)
    compras = [c for c in classificado["compras"]
               if (c["chave"] in args.chaves if args.chaves else c.get("adesao") == "sim")]
    hoje = HOJE.isoformat()
    log(f"Saldo de adesão: {len(compras)} compra(s); data de referência {dmy(ref)}")

    linhas = []
    for c in compras:
        for ata in c.get("atas") or []:
            if not ata.get("controle") or not (ata.get("vigente") or args.chaves):
                continue
            url_itens, resp = consulta_arp(cli, "2.1_consultarARPItem_Id",
                                           numeroControlePncpAta=ata["controle"])
            itens = resp.get("resultado") if isinstance(resp, dict) else resp
            itens = [i for i in (itens or []) if not i.get("itemExcluido")]
            if not itens:
                aviso(f"{c['chave']} ata {ata.get('numero')}: sem itens no modulo-arp")
                linhas.append({"chave": c["chave"], "orgao": c.get("orgao"),
                               "ata": ata.get("numero"), "controle": ata["controle"],
                               "erro": "ata sem itens no modulo-arp"})
                continue
            n_ata = itens[0]["numeroAtaRegistroPreco"]
            uasg = itens[0]["codigoUnidadeGerenciadora"]
            destino = os.path.join(pasta, "atas-saldo", f"{uasg}-{n_ata.replace('/', '-')}-{hoje}")
            os.makedirs(destino, exist_ok=True)
            grava_json(os.path.join(destino, "itens.json"), {"fonte": url_itens, "resposta": resp})
            casam = [i for i in itens if rx.search(i.get("descricaoItem") or "")]
            alvo = itens if (args.todos_itens or not casam) else casam
            sem_numero = [i for i in alvo if not i.get("numeroItem")]
            alvo = [i for i in alvo if i.get("numeroItem")]
            for it in sem_numero:   # a API às vezes devolve item sem número nem descrição
                linhas.append({"chave": c["chave"], "orgao": it.get("nomeUnidadeGerenciadora"),
                               "ata": n_ata, "controle": ata["controle"],
                               "valor_unitario": num(it.get("valorUnitario")),
                               "maximo_adesao": num(it.get("maximoAdesao")),
                               "erro": "item sem número nem descrição no modulo-arp (conferir na ata)"})
            if sem_numero:
                aviso(f"{c['chave']} ata {n_ata}: {len(sem_numero)} item(ns) sem número no modulo-arp")
            for it in alvo:
                n = it["numeroItem"]
                q = {"numeroAta": n_ata, "unidadeGerenciadora": uasg, "numeroItem": n}
                url_u, un = consulta_arp(cli, "3_consultarUnidadesItem", **q)
                url_a, ad = consulta_arp(cli, "5_consultarAdesoesItem", **q)
                grava_json(os.path.join(destino, f"unidades-item-{n}.json"),
                           {"fonte": url_u, "resposta": un})
                grava_json(os.path.join(destino, f"adesoes-item-{n}.json"),
                           {"fonte": url_a, "resposta": ad})
                unidades = un.get("resultado") or []
                adesoes = ad.get("resultado") or []
                registrado = (sum(num(u.get("quantidadeRegistrada")) or 0 for u in unidades)
                              or num(it.get("quantidadeHomologadaItem")))
                saldo = next((num(u["saldoAdesoes"]) for u in unidades
                              if num(u.get("saldoAdesoes")) is not None), None)
                aceita = any(u.get("aceitaAdesao") for u in unidades) if unidades else None
                limite = registrado * LIMITE_POR_ORGAO if registrado else None
                fim = data_iso(it.get("dataVigenciaFinal"))
                linhas.append({
                    "chave": c["chave"], "orgao": it.get("nomeUnidadeGerenciadora"), "uasg": uasg,
                    "ata": n_ata, "controle": ata["controle"],
                    "vigencia_fim": it.get("dataVigenciaFinal"),
                    "vigente": bool(fim and fim >= ref),
                    "item": n, "descricao": it.get("descricaoItem"), "tipo": it.get("tipoItem"),
                    "codigo_item": it.get("codigoItem"), "pdm": it.get("nomePdm"),
                    "fornecedor": it.get("nomeRazaoSocialFornecedor"),
                    "ni_fornecedor": it.get("niFornecedor"),
                    "valor_unitario": num(it.get("valorUnitario")), "registrado": registrado,
                    "maximo_adesao": num(it.get("maximoAdesao")), "saldo_adesoes": saldo,
                    "aceita_adesao": aceita,
                    "adesoes_aprovadas": sum(num(a.get("quantidadeAprovadaAdesao")) or 0
                                             for a in adesoes),
                    "n_adesoes": len(adesoes), "limite_por_orgao": limite,
                    "disponivel": min(saldo, limite) if saldo is not None and limite else None,
                    "casa_regex": bool(rx.search(it.get("descricaoItem") or "")),
                    "pasta": os.path.relpath(destino, RAIZ)})
            log(f"  {c['chave']} ata {n_ata} (UASG {uasg}): "
                f"{len(alvo)}/{len(itens)} item(ns) consultado(s)")

    grava_json(os.path.join(pasta, "atas-saldo.json"),
               {"consulta": agora_iso(), "data_referencia": ref.isoformat(),
                "restricoes_http": cli.restricoes, "itens": linhas})
    com = [x for x in linhas if (x.get("disponivel") or 0) > 0 and x.get("aceita_adesao")
           and x.get("vigente")]
    escreve_atas_candidatas(pasta, cfg, ref, com, [x for x in linhas if x not in com])
    log(f"itens consultados: {len(linhas)} | com saldo, aceite e vigência: {len(com)} | "
        f"sem saldo, sem aceite, vencidos ou a conferir: {len(linhas) - len(com)}")
    log(f"Gerado {os.path.relpath(os.path.join(pasta, 'atas-candidatas.md'), RAIZ)}")


def escreve_atas_candidatas(pasta, cfg, ref, com, sem):
    orgao = (cfg.get("contratante") or {}).get("orgao") or "contratante"

    def tabela(rows):
        out = ["| Gerenciador (UASG) | Ata · vigência até | It. | Descrição | Fornecedor | "
               "R$ unit. | Registr. | Saldo adesões | Limite por órgão (50%) | Links |",
               "|---|---|---|---|---|--:|--:|--:|--:|---|"]
        for x in rows:
            if x.get("erro"):
                out.append(f"| {x.get('orgao')} | {x['ata']} | — | {x['erro']} | | | | | | "
                           f"[ata no PNCP]({link_ata_pncp(x['controle'])}) |")
                continue
            marca = "" if x["casa_regex"] else " ⚠"
            out.append(
                f"| {x['orgao']} ({x['uasg']}) | {x['ata']} · {dmy(data_iso(x['vigencia_fim']))} | "
                f"{int(x['item'])} | {(x['descricao'] or '')[:90]}{marca} | {x['fornecedor']} | "
                f"{fmt_qtd(x['valor_unitario'], 2)} | {fmt_qtd(x['registrado'])} | "
                f"{fmt_qtd(x['saldo_adesoes'])} | {fmt_qtd(x['limite_por_orgao'], 1)} | "
                f"[ata no PNCP]({link_ata_pncp(x['controle'])}) · `{x['pasta']}` |")
        return out

    md = [f"# Atas candidatas à adesão — {cfg['pesquisa']['slug']}", "",
          "<!-- GERADO por scripts/pesquisa-pncp.py saldo; não editar à mão. -->", "",
          f"Consulta em {dmy(HOJE)}; data de referência {dmy(ref)}; contratante: {orgao}. "
          "Fonte: API de dados abertos do Compras.gov.br (`modulo-arp`), brutos em `atas-saldo/`.",
          "",
          "- **Saldo adesões**: informado pela API (`saldoAdesoes`); teto do art. 86, §5º "
          "(dobro do registrado para gerenciador e participantes).",
          "- **Limite por órgão**: 50% do registrado (art. 86, §4º), calculado pelo script — "
          "a API não informa.",
          "- ⚠ = a descrição de catálogo do item não casa com `pertinencia_regex` (conferir na ata).",
          "- Preço registrado na ata não é, por si, série de preços da IN 65. A adesão ainda exige "
          "justificativa da vantagem, compatibilidade de preços e anuência do gerenciador e do "
          "fornecedor (art. 86, §2º).", "",
          f"## Com saldo, aceite e vigência — {len(com)} item(ns)", "", *tabela(com), "",
          f"## Sem saldo, sem aceite, vencidos ou a conferir — {len(sem)} item(ns)", "",
          *tabela(sem), ""]
    with open(os.path.join(pasta, "atas-candidatas.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))


# ------------------- Catálogo: Painel de Preços e atas ---------------------
# Duas consultas por código de catálogo, na API de dados abertos do Compras.gov.br, que
# complementam a busca textual do PNCP (decisoes/2026-11-06-painel-e-atas-por-catalogo.md):
#   painel         — base do Painel de Preços (IN 65, art. 5º, I), modulo-pesquisa-preco
#   atas-catalogo  — itens de atas de registro de preços, modulo-arp/2_consultarARPItem
# Os códigos ficam em pesquisa.yaml > catalogo (pdm_material, catmat, catser).

URL_PRECO = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco"


def catalogo_cfg(cfg, painel=False):
    """Consultas (tipo, código). No Painel, os CATSER vêm de painel_catser, se a chave existir:
    códigos amplos (ex.: 27502, licença de software) têm dezenas de milhares de preços."""
    cat = cfg.get("catalogo") or {}
    lista = lambda k: [str(x) for x in (cat.get(k) or [])]
    catser = lista("painel_catser") if painel and "painel_catser" in cat else lista("catser")
    consultas = ([("pdm", c) for c in lista("pdm_material")] + [("catmat", c) for c in lista("catmat")]
                 + [("catser", c) for c in catser])
    if not consultas:
        morre("pesquisa.yaml > catalogo sem códigos: preencha pdm_material, catmat ou catser "
              "(códigos do Catálogo de Materiais e Serviços do Compras.gov.br)")
    return cat, consultas


def baixa_paginado(cli, url_base, params, pasta_dest, prefixo, registro, tam=500):
    """Baixa todas as páginas (tamanhoPagina até 500) e grava cada uma; devolve os registros."""
    todos, pagina = [], 1
    while True:
        q = dict(params, pagina=pagina, tamanhoPagina=tam)
        url = f"{url_base}?" + urllib.parse.urlencode(q)
        dados = cli.get_json(url) or {}
        arq = os.path.join(pasta_dest, f"{prefixo}_pagina{pagina}.json")
        grava_json(arq, dados)
        res = dados.get("resultado") or []
        registro.append({"url": url, "arquivo": os.path.relpath(arq, RAIZ), "consultado_em": agora_iso(),
                         "registros": len(res), "total": dados.get("totalRegistros")})
        todos.extend(res)
        if pagina >= int(dados.get("totalPaginas") or 1) or not res:
            return todos
        pagina += 1


def grava_registro(pasta_dest, novos):
    """registro.json acumula as consultas do dia (não apaga as de outra execução)."""
    caminho = os.path.join(pasta_dest, "registro.json")
    antigos = le_json(caminho) or []
    if not isinstance(antigos, list):          # registro em formato antigo: substituído
        antigos = []
    antigos = [r for r in antigos if r.get("arquivo") not in {n["arquivo"] for n in novos}]
    grava_json(caminho, antigos + novos)


def compras_da_pesquisa(pasta):
    """Identificadores das compras já cobertas pela busca do PNCP: chaves PNCP, id do
    Compras.gov.br (UASG + modalidade + número + ano) e o par (UASG, número/ano)."""
    chaves, ids, pares = set(), set(), set()
    cons = le_json(os.path.join(pasta, "consolidado.json")) or {}
    for c in cons.get("compras") or []:
        chaves.add(c.get("chave"))
    cls = le_json(os.path.join(pasta, "classificado.json")) or {}
    for c in cls.get("compras") or []:
        chaves.add(c.get("chave"))
        if c.get("id_cnetmobile"):
            ids.add(str(c["id_cnetmobile"]).zfill(17))
        if c.get("uasg") and c.get("numero_compra"):
            pares.add((str(c["uasg"]).zfill(6), str(c["numero_compra"]).split("/")[0].lstrip("0")))
    # compras com detalhe já baixado (inclusive as acrescentadas fora da busca textual)
    for arq in glob.glob(os.path.join(pasta, "detalhes", "*.json")):
        det = le_json(arq) or {}
        if det.get("chave"):
            chaves.add(det["chave"])
        m = re.search(r"compra=(\d+)", str((det.get("compra") or {}).get("linkSistemaOrigem") or ""))
        if m:
            ids.add(m.group(1).zfill(17))
    return chaves, ids, pares


def na_pesquisa_id(id_compra, ids, pares):
    """idCompra do Compras.gov.br = UASG (6) + modalidade (2) + número (5) + ano (4)."""
    s = str(id_compra or "").zfill(17)          # a API omite o zero à esquerda da UASG
    if s in ids:
        return True
    return len(s) == 17 and (s[:6], s[8:13].lstrip("0")) in pares


def chave_de_controle(controle):
    """'00394502000144-1-012188/2025' → '00394502000144/2025/12188'."""
    m = re.match(r"(\d{14})-\d-0*(\d+)/(\d{4})", controle or "")
    return f"{m.group(1)}/{m.group(3)}/{m.group(2)}" if m else None


def estatisticas_simples(vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    media = statistics.mean(vals)
    q = statistics.quantiles(vals, n=4) if len(vals) >= 2 else [vals[0]] * 3
    cv = statistics.stdev(vals) / media if len(vals) >= 2 and media else 0.0
    return {"n": len(vals), "mediana": statistics.median(vals), "media": media, "menor": vals[0],
            "maior": vals[-1], "q1": q[0], "q3": q[2], "cv": cv}


def cmd_painel(args):
    """Painel de Preços (IN 65, art. 5º, I) pela API de dados abertos. O endpoint de material
    exige tipo=codigoPdm|codigoItemCatalogo e codigo=<código>; o de serviço, codigoItemCatalogo."""
    pasta, cfg = carrega_pesquisa(args.slug)
    cat, consultas = catalogo_cfg(cfg, painel=True)
    ref = data_referencia(cfg)
    janela = int((cfg.get("filtros") or {}).get("janela_meses") or 12)
    lim = meses_antes(ref, janela)
    dest = os.path.join(pasta, "painel-precos", HOJE.isoformat())
    os.makedirs(dest, exist_ok=True)
    cli = cliente_detalhes(cfg)
    registro, regs = [], []
    for tipo, cod in consultas:
        if tipo == "catser":
            url, params = f"{URL_PRECO}/3_consultarServico", {"codigoItemCatalogo": cod}
        else:
            url = f"{URL_PRECO}/1_consultarMaterial"
            params = {"tipo": "codigoPdm" if tipo == "pdm" else "codigoItemCatalogo", "codigo": cod}
        log(f"Painel de Preços: {tipo} {cod}")
        for r in baixa_paginado(cli, url, params, dest, f"{tipo}-{cod}", registro):
            regs.append(dict(r, _consulta=f"{tipo} {cod}"))
    grava_registro(dest, registro)

    chaves, ids, pares = compras_da_pesquisa(pasta)
    rx_marca = re.compile(cat.get("marca_regex") or r"(?!)", re.I)
    rx_pert = re.compile((cfg.get("filtros") or {}).get("pertinencia_regex") or ".", re.I)
    for r in regs:
        dr = data_iso(r.get("dataResultado"))
        r["_janela"] = bool(dr and lim <= dr <= ref)
        r["_na_pesquisa"] = na_pesquisa_id(r.get("idCompra"), ids, pares)
        texto = " ".join(str(r.get(k) or "") for k in ("marca", "descricaoDetalhadaItem", "descricaoItem"))
        r["_marca"] = bool(rx_marca.search(texto))
        r["_pertinente"] = bool(rx_pert.search(texto + " " + str(r.get("objetoCompra") or "")))

    resumo = {"gerado_em": agora_iso(), "data_referencia": ref.isoformat(), "janela_inicio": lim.isoformat(),
              "consultas": {}, "por_modelo": [], "fora_da_pesquisa": []}
    for tipo, cod in consultas:
        rr = [r for r in regs if r["_consulta"] == f"{tipo} {cod}"]
        resumo["consultas"][f"{tipo} {cod}"] = {
            "total": len(rr), "na_janela": sum(r["_janela"] for r in rr),
            "estatisticas_janela": estatisticas_simples([r.get("precoUnitario") for r in rr if r["_janela"]])}

    def linha(r):
        return {k: r.get(k) for k in ("dataResultado", "codigoUasg", "nomeUasg", "esfera", "idCompra",
                                       "numeroItemCompra", "codigoItemCatalogo", "marca", "quantidade",
                                       "precoUnitario", "nomeFornecedor")} | {
            "janela": r["_janela"], "na_pesquisa": r["_na_pesquisa"],
            "link": URL_CNET_COMPRA.format(compra=r.get("idCompra"))}
    vistos = set()
    for r in sorted(regs, key=lambda r: r.get("dataResultado") or "", reverse=True):
        k = (r.get("idCompra"), r.get("numeroItemCompra"))
        if k in vistos:
            continue
        vistos.add(k)
        if r["_marca"]:
            resumo["por_modelo"].append(linha(r))
        if r["_janela"] and not r["_na_pesquisa"] and (r["_marca"] or not cat.get("marca_regex")):
            resumo["fora_da_pesquisa"].append(linha(r))
    grava_json(os.path.join(dest, "painel.json"), resumo)
    escreve_painel_md(dest, cfg, resumo)
    log(f">> {os.path.relpath(dest, RAIZ)}/painel.md ({len(regs)} registros; "
        f"{len(resumo['por_modelo'])} por modelo; {len(resumo["fora_da_pesquisa"])} na janela e não avaliados)")


def escreve_painel_md(dest, cfg, res):
    def pct(v):
        return f"{v * 100:.0f}%"
    md = [f"# Painel de Preços — {cfg['pesquisa']['slug']}", "",
          "<!-- GERADO por scripts/pesquisa-pncp.py painel; não editar à mão. -->", "",
          f"Consulta em {dmy(HOJE)} pela API de dados abertos do Compras.gov.br (`modulo-pesquisa-preco`, "
          f"base do Painel de Preços; IN 65, art. 5º, I). Janela: resultado de {dmy(data_iso(res['janela_inicio']))} "
          f"a {dmy(data_iso(res['data_referencia']))}. Brutos e `registro.json` nesta pasta.", "",
          "## Estatísticas por código (na janela)", "",
          "| Consulta | Registros | Na janela | Mediana | Menor | Maior | 1º quartil | 3º quartil | CV |",
          "|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for k, v in res["consultas"].items():
        e = v["estatisticas_janela"]
        md.append(f"| {k} | {v['total']} | {v['na_janela']} | " + (
            f"{brl(e['mediana'])} | {brl(e['menor'])} | {brl(e['maior'])} | {brl(e['q1'])} | {brl(e['q3'])} | "
            f"{pct(e['cv'])} |" if e else "— | — | — | — | — | — |"))
    md += ["", "Leitura: o código de catálogo costuma reunir equipamentos de portes diferentes e preços com e "
           "sem licença; CV alto indica que a mediana do código não representa o objeto (art. 4º). "
           "Use o recorte por modelo abaixo.", "",
           "## Registros por modelo (`catalogo.marca_regex`)", "",
           "| Resultado | Órgão (UASG) | Esfera | Compra | Item | Marca/modelo | Qtd. | Preço unitário | Janela | Já na pesquisa |",
           "|---|---|---|---|--:|---|--:|--:|---|---|"]

    def row(r):
        return (f"| {dmy(data_iso(r['dataResultado']))} | {r['nomeUasg']} ({r['codigoUasg']}) | {r['esfera']} | "
                f"[{r['idCompra']}]({r['link']}) | {r['numeroItemCompra']} | {(r['marca'] or '')[:40]} | "
                f"{fmt_qtd(r['quantidade'])} | {brl(r['precoUnitario'])} | {'sim' if r['janela'] else 'não'} | "
                f"{'sim' if r['na_pesquisa'] else '**não**'} |")
    md += [row(r) for r in res["por_modelo"]] or ["| — | | | | | | | | | |"]
    md += ["", "## Na janela e ainda não avaliadas — candidatas a conferir", "",
           "\"Já na pesquisa\" = compra presente na busca do PNCP (consolidado/classificado) ou com detalhe em "
           "`detalhes/`.", "",
           "Ler edital, TR e proposta antes de usar: o campo de marca do Painel é declarado pelo fornecedor e "
           "pode divergir da ata (em contratação anterior, um modelo de firewall apareceu com o sufixo de outro).", "",
           "| Resultado | Órgão (UASG) | Esfera | Compra | Item | Marca/modelo | Qtd. | Preço unitário | Janela | Já na pesquisa |",
           "|---|---|---|---|--:|---|--:|--:|---|---|"]
    md += [row(r) for r in res["fora_da_pesquisa"]] or ["| — | | | | | | | | | |"]
    with open(os.path.join(dest, "painel.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


def cmd_atas_catalogo(args):
    """Itens de atas por código de catálogo (modulo-arp/2_consultarARPItem): acha atas que a busca
    textual do PNCP perde. Material: codigoPdm (PDM) ou codigoItem (CATMAT); serviço: codigoItem."""
    pasta, cfg = carrega_pesquisa(args.slug)
    cat, consultas = catalogo_cfg(cfg)
    ref = data_referencia(cfg)
    desde = meses_antes(ref, int(cat.get("vigencia_inicial_meses") or 24))
    dest = os.path.join(pasta, "atas-arp", HOJE.isoformat())
    os.makedirs(dest, exist_ok=True)
    cli = cliente_detalhes(cfg)
    registro, regs = [], []
    for tipo, cod in consultas:
        params = {"dataVigenciaInicialMin": desde.isoformat(), "dataVigenciaInicialMax": HOJE.isoformat(),
                  ("codigoPdm" if tipo == "pdm" else "codigoItem"): cod}
        log(f"Atas por catálogo: {tipo} {cod}")
        regs += baixa_paginado(cli, f"{URL_ARP}/2_consultarARPItem", params, dest, f"{tipo}-{cod}", registro)
    grava_registro(dest, registro)

    chaves, _, _ = compras_da_pesquisa(pasta)
    rx_txt = re.compile(cat.get("texto_regex") or ".", re.I)
    atas = {}
    for r in regs:
        if r.get("itemExcluido") or not rx_txt.search(str(r.get("descricaoItem") or "")):
            continue
        fim = data_iso(r.get("dataVigenciaFinal"))
        if not fim or fim < HOJE:
            continue
        a = atas.setdefault(r.get("numeroControlePncpAta"), {
            "gerenciadora": r.get("nomeUnidadeGerenciadora"), "uasg": r.get("codigoUnidadeGerenciadora"),
            "ata": r.get("numeroAtaRegistroPreco"), "vigencia_fim": r.get("dataVigenciaFinal"),
            "chave": chave_de_controle(r.get("numeroControlePncpCompra")), "itens": {}})
        a["itens"][r.get("numeroItem")] = r
    for a in atas.values():
        a["na_pesquisa"] = a["chave"] in chaves
    lst = sorted(atas.items(), key=lambda kv: (kv[1]["na_pesquisa"], kv[1]["gerenciadora"] or ""))
    md = [f"# Atas vigentes por código de catálogo — {cfg['pesquisa']['slug']}", "",
          "<!-- GERADO por scripts/pesquisa-pncp.py atas-catalogo; não editar à mão. -->", "",
          f"Consulta em {dmy(HOJE)} (`modulo-arp/2_consultarARPItem`), vigência inicial desde {dmy(desde)}; "
          f"{len(lst)} ata(s) vigente(s), {sum(not a['na_pesquisa'] for _, a in lst)} ainda não avaliada(s) "
          "(\"Já na pesquisa\" = compra na busca do PNCP ou com detalhe em `detalhes/`).", "",
          "Antes de tratar uma ata como candidata: conferir a esfera do gerenciador (Lei 14.133, art. 86, §§3º e 8º), "
          "ler a cláusula de adesão do edital (`aceitaAdesao` da API não reflete restrição a categorias de órgão) e, "
          "em grupo, a comprovação do menor preço por item. Para os itens pertinentes, rodar `saldo --chaves <chave>`.", "",
          "| Gerenciadora (UASG) | Ata · vigência até | Itens (qtd.; valor unitário) | Já na pesquisa | Links |",
          "|---|---|---|---|---|"]
    for ctrl, a in lst:
        its = "; ".join(f"it{int(n)} {fmt_qtd(r.get('quantidadeHomologadaItem'))} un. "
                        f"{brl(r.get('valorUnitario'))} — {(r.get('descricaoItem') or '')[:50]}"
                        for n, r in sorted(a["itens"].items()))
        md.append(f"| {a['gerenciadora']} ({a['uasg']}) | {a['ata']} · {dmy(data_iso(a['vigencia_fim']))} | {its} | "
                  f"{'sim' if a['na_pesquisa'] else '**não**'} | [ata no PNCP]({link_ata_pncp(ctrl)}) · "
                  f"chave `{a['chave']}` |")
    with open(os.path.join(dest, "atas-catalogo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    log(f">> {os.path.relpath(dest, RAIZ)}/atas-catalogo.md ({len(lst)} atas vigentes)")


# ------------------------- Contratos e termos (PNCP) -------------------------
#   contrato — contrato, termos (aditivos, apostilamentos, rescisões) e documentos de uma
#   compra ou de um contrato publicados no PNCP, ou busca de contratos de um órgão por texto.
#   Uso típico: comprovar o objeto e a vigência atual de contrato correlato (ex.: o contrato de
#   sustentação que justifica não contratar operação), ou acompanhar contrato de outro órgão.

URL_CONSULTA_CONTRATOS = "https://pncp.gov.br/api/consulta/v1/contratos"
URL_APP_CONTRATOS = "https://pncp.gov.br/app/contratos"
RE_CONTROLE_ALVO = re.compile(r"(\d{14})-([12])-0*(\d{1,6})/(\d{4})")
RE_LINK_APP = re.compile(r"pncp\.gov\.br/app/(editais|contratos)/(\d{14})/(\d{4})/0*(\d+)")
RE_CHAVE = re.compile(r"^(\d{14})/(\d{4})/0*(\d+)$")


def interpreta_alvo(texto):
    """'33892175000100-1-000004/2025', link do app do PNCP ou 'cnpj/ano/seq' (compra) →
    (tipo, cnpj, ano, seq), com tipo 'compra' ou 'contrato'."""
    texto = texto.strip()
    m = RE_CONTROLE_ALVO.search(texto)
    if m:
        return ("compra" if m.group(2) == "1" else "contrato", m.group(1), int(m.group(4)), int(m.group(3)))
    m = RE_LINK_APP.search(texto)
    if m:
        return ("compra" if m.group(1) == "editais" else "contrato", m.group(2), int(m.group(3)), int(m.group(4)))
    m = RE_CHAVE.match(texto)
    if m:
        return ("compra", m.group(1), int(m.group(2)), int(m.group(3)))
    morre(f"alvo não reconhecido: {texto!r} (use o número de controle PNCP, o link do app ou cnpj/ano/seq)")


def janelas_365(desde, ate):
    """Divide [desde, ate] em janelas de até 365 dias (limite da API de consulta de contratos)."""
    ini = desde
    while ini <= ate:
        fim = min(ini + datetime.timedelta(days=364), ate)
        yield ini, fim
        ini = fim + datetime.timedelta(days=1)


def busca_contratos(cli, cnpj, desde, ate, registro, pasta_dest, prefixo):
    """Contratos publicados pelo órgão entre as datas (consulta/v1/contratos, por data de
    publicação), janela a janela e página a página. Grava cada página."""
    achados = []
    for ini, fim in janelas_365(desde, ate):
        pagina = 1
        while True:
            q = {"dataInicial": ini.strftime("%Y%m%d"), "dataFinal": fim.strftime("%Y%m%d"),
                 "cnpjOrgao": cnpj, "pagina": pagina, "tamanhoPagina": 100}
            url = f"{URL_CONSULTA_CONTRATOS}?" + urllib.parse.urlencode(q)
            dados = cli.get_json(url) or {}
            arq = os.path.join(pasta_dest, "busca", f"{prefixo}_{ini:%Y%m%d}_pagina{pagina}.json")
            os.makedirs(os.path.dirname(arq), exist_ok=True)
            grava_json(arq, dados)
            res = dados.get("data") or []
            registro.append({"url": url, "arquivo": os.path.relpath(arq, RAIZ), "consultado_em": agora_iso(),
                             "registros": len(res), "total": dados.get("totalRegistros")})
            achados.extend(res)
            if pagina >= int(dados.get("totalPaginas") or 1) or not res:
                break
            pagina += 1
    return achados


def baixa_json(cli, url, destino, registro):
    dados = cli.get_json(url)
    grava_json(destino, dados if dados is not None else [])
    registro.append({"url": url, "arquivo": os.path.relpath(destino, RAIZ), "consultado_em": agora_iso()})
    return dados


def vigencia_atual(contrato, termos):
    """Maior data de fim de vigência entre o contrato e os termos, e de onde ela vem."""
    fim, origem = data_iso(contrato.get("dataVigenciaFim")), "termo inicial"
    for t in termos:
        f = data_iso(t.get("dataVigenciaFim"))
        if f and (not fim or f > fim) and "rescis" not in (t.get("tipoTermoContratoNome") or "").lower():
            fim, origem = f, f"{t.get('tipoTermoContratoNome')} {t.get('numeroTermoContrato')}"
    for t in termos:   # rescisão encerra antes, qualquer que seja o aditivo
        if "rescis" in (t.get("tipoTermoContratoNome") or "").lower():
            f = data_iso(t.get("dataVigenciaFim")) or data_iso(t.get("dataAssinatura"))
            if f:
                fim, origem = f, f"{t.get('tipoTermoContratoNome')} {t.get('numeroTermoContrato')}"
    return fim, origem


def sha256_pasta(pasta):
    import hashlib
    linhas = []
    for raiz, _, arquivos in os.walk(pasta):
        for nome in sorted(arquivos):
            if nome == "SHA256SUMS" or nome.endswith(TEMP_SUFFIX):
                continue
            caminho = os.path.join(raiz, nome)
            with open(caminho, "rb") as f:
                h = hashlib.sha256(f.read()).hexdigest()
            linhas.append(f"{h}  {os.path.relpath(caminho, pasta)}")
    with open(os.path.join(pasta, "SHA256SUMS"), "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(linhas, key=lambda l: l[66:])) + "\n")


def cmd_contrato(args):
    dest = os.path.abspath(args.saida)
    os.makedirs(dest, exist_ok=True)
    cli = Cliente(0.5, 1.5, espera_bloqueio=(2, 5))
    ref = data_iso(args.data_referencia) or HOJE
    ate = data_iso(args.ate) if args.ate else None
    registro, compras, alvos = [], {}, []   # alvos: (cnpj, ano, seq) de contrato

    if args.orgao:
        if not args.texto:
            morre("--orgao exige --texto (regex sobre objeto e fornecedor)")
        desde = data_iso(args.desde) or meses_antes(HOJE, 24)
        rx = re.compile(args.texto, re.I)
        for c in busca_contratos(cli, args.orgao, desde, HOJE, registro, dest, f"orgao-{args.orgao}"):
            alvo_txt = f"{c.get('objetoContrato') or ''} {c.get('nomeRazaoSocialFornecedor') or ''}"
            if rx.search(alvo_txt):
                alvos.append((args.orgao, int(c["anoContrato"]), int(c["sequencialContrato"])))
        log(f"busca no órgão {args.orgao} desde {dmy(desde)}: {len(alvos)} contrato(s) casam com /{args.texto}/")

    for texto in args.alvos or []:
        tipo, cnpj, ano, seq = interpreta_alvo(texto)
        if tipo == "contrato":
            alvos.append((cnpj, ano, seq))
            continue
        url = f"{URL_CONSULTA}/{cnpj}/compras/{ano}/{seq}"
        compra = baixa_json(cli, url, os.path.join(dest, f"compra-{cnpj}-{ano}-{seq}.json"), registro)
        if not compra:
            aviso(f"compra {cnpj}/{ano}/{seq} não encontrada no PNCP")
            continue
        ctrl = compra.get("numeroControlePNCP")
        compras[ctrl] = compra
        desde = data_iso(compra.get("dataPublicacaoPncp")) or datetime.date(ano, 1, 1)
        achados = [c for c in busca_contratos(cli, cnpj, desde, HOJE, registro, dest, f"compra-{cnpj}-{ano}-{seq}")
                   if c.get("numeroControlePncpCompra") == ctrl]
        log(f"compra {ctrl}: {len(achados)} contrato(s) publicado(s) desde {dmy(desde)}")
        if not achados:
            aviso(f"nenhum contrato da compra {ctrl} na consulta por data de publicação; "
                  "informe o contrato diretamente, se ele existir")
        alvos.extend((cnpj, int(c["anoContrato"]), int(c["sequencialContrato"])) for c in achados)

    if not alvos and not compras:
        morre("nada a consultar (informe alvos ou --orgao/--texto)")

    vistos, fichas = set(), []
    for cnpj, ano, seq in alvos:
        if (cnpj, ano, seq) in vistos:
            continue
        vistos.add((cnpj, ano, seq))
        base = f"{URL_PNCP}/{cnpj}/contratos/{ano}/{seq}"
        sufixo = f"{cnpj}-{ano}-{seq}"
        contrato = baixa_json(cli, base, os.path.join(dest, f"contrato-{sufixo}.json"), registro)
        if not contrato:
            aviso(f"contrato {cnpj}/{ano}/{seq} não encontrado")
            continue
        termos = baixa_json(cli, f"{base}/termos", os.path.join(dest, f"termos-{sufixo}.json"), registro) or []
        arquivos = baixa_json(cli, f"{base}/arquivos", os.path.join(dest, f"arquivos-{sufixo}.json"), registro) or []
        docs = [(a.get("titulo") or f"arquivo-{a.get('sequencialDocumento')}", a.get("url") or a.get("uri"),
                 f"{a.get('sequencialDocumento')}") for a in arquivos]
        for t in termos:
            st = t.get("sequencialTermoContrato")
            if st is None:
                continue
            lst = baixa_json(cli, f"{base}/termos/{st}/arquivos",
                             os.path.join(dest, f"arquivos-{sufixo}-termo{st}.json"), registro) or []
            docs += [(a.get("titulo") or f"termo{st}-arquivo-{a.get('sequencialDocumento')}",
                      a.get("url") or a.get("uri"), f"termo{st}-{a.get('sequencialDocumento')}") for a in lst]
        if args.documentos:
            for titulo, url, pref in docs:
                if not url:
                    continue
                destino = os.path.join(dest, "documentos", sanitiza_nome(f"{sufixo}-{pref}-{titulo}".replace("/", "-")))
                try:
                    baixa_arquivo(cli, url, destino, forca=args.forca)
                except RuntimeError as e:
                    aviso(str(e))
        fichas.append((contrato, termos, docs))

    grava_registro(dest, registro)
    escreve_resumo_contratos(dest, compras, fichas, ref, ate)
    sha256_pasta(dest)
    log(f">> {os.path.relpath(dest, RAIZ)}/resumo.md ({len(fichas)} contrato(s)); SHA256SUMS atualizado")


def escreve_resumo_contratos(dest, compras, fichas, ref, ate):
    md = ["# Contratos no PNCP", "",
          f"Consulta em {dmy(HOJE)} por `scripts/pesquisa-pncp.py contrato`; data de referência {dmy(ref)}"
          + (f"; cobertura exigida até {dmy(ate)}" if ate else "") + ". Brutos e `registro.json` nesta pasta "
          "(evidência datada; IN 65, art. 3º, III, quando servir à pesquisa de preços).", "",
          "A vigência atual é a maior data de fim entre o termo inicial e os termos publicados. Aditivo ainda "
          "não publicado no PNCP não aparece: vigência vencida aqui pede conferência no SEI ou com a gestão do "
          "contrato antes de ser afirmada no ETP.", ""]
    for ctrl, c in compras.items():
        cnpj, ano, seq = interpreta_alvo(ctrl)[1:]
        md += [f"## Compra {ctrl}", "",
               f"- {c.get('modalidadeNome')} nº {c.get('numeroCompra')}/{c.get('anoCompra')}, processo "
               f"{c.get('processo')}, UASG {(c.get('unidadeOrgao') or {}).get('codigoUnidade')}; situação: "
               f"{c.get('situacaoCompraNome')}.",
               f"- Objeto: {c.get('objetoCompra')}",
               f"- Link: {URL_APP}/{cnpj}/{ano}/{seq}", ""]
    for contrato, termos, docs in fichas:
        cnpj = (contrato.get("orgaoEntidade") or {}).get("cnpj") or contrato["numeroControlePNCP"][:14]
        ano, seq = contrato.get("anoContrato"), contrato.get("sequencialContrato")
        fim, origem = vigencia_atual(contrato, termos)
        if not fim:
            situacao = "sem data de fim informada"
        elif fim < ref:
            situacao = f"vencida em {dmy(fim)} na base do PNCP — conferir aditivo não publicado"
        else:
            situacao = f"vigente até {dmy(fim)} ({origem})"
        if ate and fim and fim < ate:
            situacao += f"; termina antes de {dmy(ate)}: a cobertura depende de prorrogação ou de contrato sucessor"
        link = f"{URL_APP_CONTRATOS}/{cnpj}/{ano}/{seq}"
        md += [f"## Contrato {contrato.get('numeroContratoEmpenho')}/{ano} — {contrato.get('nomeRazaoSocialFornecedor')}", "",
               f"- Controle PNCP: `{contrato.get('numeroControlePNCP')}`; compra `{contrato.get('numeroControlePncpCompra')}`"
               + (f"; ata `{contrato['numeroControlePncpAta']}`" if contrato.get("numeroControlePncpAta") else ""),
               f"- Processo {contrato.get('processo')}; fornecedor CNPJ {contrato.get('niFornecedor')}; "
               f"categoria {(contrato.get('categoriaProcesso') or {}).get('nome')}.",
               f"- Objeto: {contrato.get('objetoContrato')}",
               f"- Assinatura {dmy(data_iso(contrato.get('dataAssinatura')))}; vigência inicial "
               f"{dmy(data_iso(contrato.get('dataVigenciaInicio')))} a {dmy(data_iso(contrato.get('dataVigenciaFim')))}.",
               f"- Valor inicial {brl(contrato.get('valorInicial'))}; global {brl(contrato.get('valorGlobal'))}; "
               f"acumulado {brl(contrato.get('valorAcumulado'))}.",
               f"- **Situação na data de referência: {situacao}.**",
               f"- Link: {link}", ""]
        if termos:
            md += ["| Termo | Assinatura | Vigência | Objeto |", "|---|---|---|---|"]
            for t in sorted(termos, key=lambda t: str(t.get("dataAssinatura"))):
                obj = re.sub(r"\s+", " ", t.get("objetoTermoContrato") or "")[:220]
                md.append(f"| {t.get('tipoTermoContratoNome')} {t.get('numeroTermoContrato')} | "
                          f"{dmy(data_iso(t.get('dataAssinatura')))} | {dmy(data_iso(t.get('dataVigenciaInicio')))} a "
                          f"{dmy(data_iso(t.get('dataVigenciaFim')))} | {obj} |")
            md.append("")
        if docs:
            md += ["Documentos publicados: " + "; ".join(f"{t} ({p})" for t, _, p in docs) + ".", ""]
        md += ["Sugestão para `etp/fontes.yaml` (próximo `F-nn` livre; confira antes de usar):", "", "```yaml",
               f"  - id: F-nn",
               f"    documento: \"<órgão>, *Contrato nº {contrato.get('numeroContratoEmpenho')}/{ano}* com "
               f"{contrato.get('nomeRazaoSocialFornecedor')} (PNCP {contrato.get('numeroControlePNCP')}), "
               f"assinado em {dmy(data_iso(contrato.get('dataAssinatura')))}; {situacao}\"",
               f"    endereco: \"{link}\"", f"    consulta: \"{dmy(HOJE)}\"", "```", ""]
    with open(os.path.join(dest, "resumo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")


# --------------------------------- Main ------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Pesquisa de contratações similares no PNCP (IN SEGES/ME 65/2021).")
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("iniciar", help="cria pesquisas/pncp/<slug>/pesquisa.yaml")
    p.add_argument("slug")
    p.set_defaults(func=cmd_iniciar)

    p = sub.add_parser("buscar", help="consulta a busca do PNCP para cada termo")
    p.add_argument("slug")
    p.add_argument("--termo", help="busca só este termo (precisa estar no pesquisa.yaml "
                   "para ser consolidado com os demais)")
    p.add_argument("--atualizar", action="store_true",
                   help="baixa de novo páginas já salvas (o total cresce com o tempo)")
    p.set_defaults(func=cmd_buscar)

    p = sub.add_parser("consolidar", help="merge e eliminação de duplicatas")
    p.add_argument("slug")
    p.set_defaults(func=cmd_consolidar)

    for nome, func, ajuda in (("enriquecer", cmd_enriquecer, "detalhes e classificação"),
                              ("baixar", cmd_baixar, "documentos do PNCP para referencia/")):
        p = sub.add_parser(nome, help=ajuda)
        p.add_argument("slug")
        p.add_argument("--chaves", nargs="+", help="só estas compras (cnpj/ano/seq)")
        p.add_argument("--todos-filtrados", action="store_true", dest="todos_filtrados",
                       help="usa todas as que passam no filtro, ignorando a triagem")
        if nome == "enriquecer":
            p.add_argument("--atualizar", action="store_true", help="ignora o cache de detalhes/")
        else:
            p.add_argument("--saida", default=PASTA_DOCUMENTOS)
            p.add_argument("--forca", action="store_true", help="baixa de novo os existentes")
        p.set_defaults(func=func)

    p = sub.add_parser("propostas", help="atualiza o roteiro de propostas obtidas")
    p.add_argument("slug")
    p.set_defaults(func=cmd_propostas)

    p = sub.add_parser("serie", help="série de preços e estatísticas (art. 6º)")
    p.add_argument("slug")
    p.add_argument("--candidatos", action="store_true",
                   help="gera serie-precos.candidatos.yaml com todos os preços disponíveis")
    p.set_defaults(func=cmd_serie)

    p = sub.add_parser("saldo", help="saldo de adesão das atas vigentes (modulo-arp)")
    p.add_argument("slug")
    p.add_argument("--chaves", nargs="+",
                   help="só estas compras (cnpj/ano/seq), mesmo sem adesao=sim ou ata vigente")
    p.add_argument("--todos-itens", action="store_true", dest="todos_itens",
                   help="consulta também os itens que não casam com pertinencia_regex")
    p.set_defaults(func=cmd_saldo)

    p = sub.add_parser("painel", help="Painel de Preços por código de catálogo (art. 5º, I)")
    p.add_argument("slug")
    p.set_defaults(func=cmd_painel)

    p = sub.add_parser("atas-catalogo", help="atas vigentes por código de catálogo (modulo-arp)")
    p.add_argument("slug")
    p.set_defaults(func=cmd_atas_catalogo)

    p = sub.add_parser("contrato", help="contrato, termos aditivos e documentos no PNCP")
    p.add_argument("alvos", nargs="*", help="número de controle PNCP da compra (-1-) ou do contrato (-2-), "
                   "link do app do PNCP (editais/contratos) ou cnpj/ano/seq da compra")
    p.add_argument("--saida", required=True, help="pasta de destino, por exemplo "
                   "referencia/contratacoes-proprias/<assunto>/pncp-<AAAA-MM-DD>/")
    p.add_argument("--orgao", help="CNPJ do órgão: busca contratos publicados por ele (com --texto)")
    p.add_argument("--texto", help="regex sobre objeto e fornecedor, para --orgao")
    p.add_argument("--desde", help="data inicial da busca por --orgao (AAAA-MM-DD; padrão: 24 meses)")
    p.add_argument("--ate", help="data até a qual a cobertura é exigida (ex.: fim da garantia de 60 meses)")
    p.add_argument("--data-referencia", dest="data_referencia", help="data de referência (padrão: hoje)")
    p.add_argument("--documentos", action="store_true", help="baixa também os documentos publicados")
    p.add_argument("--forca", action="store_true", help="baixa de novo os documentos existentes")
    p.set_defaults(func=cmd_contrato)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
