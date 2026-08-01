--- Shortcode {{< term key >}} — a glossary link with a hover definition.
---
---   {{< term ate >}}                    -> label taken from the glossary
---   {{< term ate "average effect" >}}   -> custom label
---
--- The glossary lives in _glossary.yml and is attached through
--- metadata-files in _quarto.yml, so it arrives here as meta.glossary and
--- no YAML parsing is needed in Lua.

local stringify = pandoc.utils.stringify

--- Keys already warned about: one warning per key, not per occurrence.
local warned = {}

local function lookup(meta, key)
  if not meta or not meta.glossary then return nil end
  return meta.glossary[key]
end

return {
  ["term"] = function(args, kwargs, meta)
    if #args == 0 then
      quarto.log.warning("playbook: {{< term >}} called without a key")
      return pandoc.Null()
    end

    local key = stringify(args[1])
    local entry = lookup(meta, key)

    -- Label: an explicit second argument, else the glossary's term field,
    -- else the key itself.
    local label
    if #args > 1 then
      label = stringify(args[2])
    elseif entry and entry.term then
      label = stringify(entry.term)
    else
      label = key
    end

    if not entry then
      if not warned[key] then
        quarto.log.warning(
          "playbook: term '" .. key .. "' is not in _glossary.yml — " ..
          "the link will render without a tooltip"
        )
        warned[key] = true
      end
      -- Still emit the link: a dangling glossary entry is a reminder to write
      -- the definition, not a build error.
      return pandoc.Link(
        pandoc.Str(label),
        "/glossary.qmd#term-" .. key,
        "",
        pandoc.Attr("", { "term" })
      )
    end

    local tooltip = (entry.short and stringify(entry.short))
      or (entry.def and stringify(entry.def))
      or ""

    return pandoc.Link(
      pandoc.Str(label),
      "/glossary.qmd#term-" .. key,
      tooltip,
      pandoc.Attr("", { "term" })
    )
  end,
}
