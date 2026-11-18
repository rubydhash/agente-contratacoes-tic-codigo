-- Converte as marcações de alteração deste repositório em estilos do docx (ou, no HTML,
-- em cor embutida).
--
-- Convenção adotada no markdown do TR:
--   [trecho]{.azul}   → fragmento alterado dentro de um item que, no restante,
--                       reproduz o texto do modelo AGU
--   ::: azul          → item inteiro incluído ou substancialmente alterado
--   :::
--
-- O writer docx do pandoc aplica o atributo `custom-style`; a aparência (azul)
-- vem das definições de estilo injetadas em scripts/estilos-docx.py.
--
-- Uso: pandoc --lua-filter=scripts/azul.lua ...

local function tem(classes, nome)
  for _, c in ipairs(classes) do if c == nome then return true end end
  return false
end

-- No HTML, o azul vai como estilo embutido em cada elemento: é o que sobrevive à colagem
-- no editor do Compras.gov.br e do SEI, que descartam folhas de estilo e classes.
local AZUL_HTML = "color:#0000CC"
local eh_html = FORMAT:match("html") ~= nil

function Span(el)
  if tem(el.classes, "azul") then
    if eh_html then
      el.attributes["style"] = AZUL_HTML
    else
      el.attributes["custom-style"] = "TrechoAlterado"
    end
  end
  return el
end

function Div(el)
  if tem(el.classes, "azul") then
    if eh_html then
      el.attributes["style"] = AZUL_HTML
    else
      el.attributes["custom-style"] = "ItemAlterado"
    end
  end
  return el
end
