-- Traduz as marcas de afastamento do modelo AGU, no markdown do TR, para o docx (estilos) e
-- para o HTML (cor embutida), conforme o "Código de formatação visual sugerida" do
-- Instrumento de Padronização AGU/MGI de TIC (ver scripts/tr_marcas.py):
--
--   [texto]{.inclusao}       ::: inclusao       vermelho   inclusão
--   [texto]{.ajuste}                            verde      ajuste (após o original tachado)
--   [texto]{.preenchimento}  ::: preenchimento  azul       preenchimento de lacuna do modelo
--   ~~texto~~                                   tachado    supressão / alternativa não adotada
--                            ::: justificativa  cinza      justificativa, logo abaixo do item
--   [texto]{.azul}           ::: azul           azul       legado (convenção anterior)
--
-- No docx, o writer do pandoc aplica o atributo `custom-style`; a aparência vem dos estilos
-- injetados por scripts/estilos-docx.py. O tachado é o nativo do Word.
--
-- Uso: pandoc --lua-filter=scripts/marcas.lua ...

-- Cores: as mesmas de scripts/tr_marcas.py (CORES) e scripts/estilos-docx.py.
local COR = {
  inclusao = "#FF0000",
  ajuste = "#00B050",
  preenchimento = "#0000FF",
  justificativa = "#808080",
  azul = "#0000CC",
}
local ESTILO_SPAN = {
  inclusao = "TrechoIncluido",
  ajuste = "TrechoAjustado",
  preenchimento = "TrechoPreenchido",
  justificativa = "TrechoJustificativa",
  azul = "TrechoAlterado",
}
local ESTILO_DIV = {
  inclusao = "ItemIncluido",
  preenchimento = "ItemPreenchido",
  justificativa = "Justificativa",
  azul = "ItemAlterado",
}

local eh_html = FORMAT:match("html") ~= nil

local function marca(classes, tabela)
  for _, c in ipairs(classes) do
    if tabela[c] then return c end
  end
  return nil
end

-- No HTML, a cor e o tachado vão como estilo embutido em cada trecho: é o que sobrevive à
-- colagem no editor do Compras.gov.br e do SEI, que descartam folhas de estilo e classes.
local function cor_embutida(m)
  return "color:" .. COR[m]
end

function Strikeout(el)
  if eh_html then
    return pandoc.Span(el.content, {style = "text-decoration:line-through"})
  end
  return el
end

function Span(el)
  local m = marca(el.classes, ESTILO_SPAN)
  if not m then return el end
  if eh_html then
    el.attributes["style"] = cor_embutida(m)
  else
    el.attributes["custom-style"] = ESTILO_SPAN[m]
  end
  return el
end

function Div(el)
  local m = marca(el.classes, ESTILO_DIV)
  if not m then return el end
  -- Além do estilo no bloco, embrulha o texto de cada parágrafo (inclusive em células de
  -- tabela, que não herdam o estilo do bloco) num trecho com a cor: no HTML, para que ela não se
  -- perca na colagem; no docx, porque o estilo de parágrafo do bloco não chega às tabelas.
  local atributos
  if eh_html then
    el.attributes["style"] = cor_embutida(m)
    atributos = {style = cor_embutida(m)}
  else
    el.attributes["custom-style"] = ESTILO_DIV[m]
    atributos = {["custom-style"] = ESTILO_SPAN[m]}
  end
  local function pinta(b)
    b.content = {pandoc.Span(b.content, atributos)}
    return b
  end
  return el:walk({Para = pinta, Plain = pinta})
end
