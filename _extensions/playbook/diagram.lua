--- Shortcode {{< diagram name >}} — inline an SVG from assets/diagrams/.
---
---   {{< diagram causation-vs-association >}}
---
--- The file is INLINED into the page rather than linked with <img>. A linked
--- SVG is a separate document: the page's CSS custom properties do not cross
--- into it, so it would be the one element on the site that ignores the theme
--- toggle — the same problem plotly-theme-sync.js exists to solve for baked
--- charts. Inlined, a single file serves both themes and every color still
--- comes from theme/palette.json.
---
--- A second consequence: the file never has to be copied into _site, so no
--- resources: entry is needed in _quarto.yml.
---
--- Wrap the shortcode in a figure div for a caption and a cross-reference:
---
---   ::: {#fig-causation-association}
---   {{< diagram causation-vs-association >}}
---
---   The caption goes here.
---   :::

local DIR = "assets/diagrams/"

--- Diagrams are addressed from the project root, not from the calling
--- document — a chapter in notes/ and the landing page must spell the same
--- name.
local function project_root()
  if quarto and quarto.project and quarto.project.directory then
    return quarto.project.directory
  end
  return pandoc.system.get_working_directory()
end

local function read_file(path)
  local fh = io.open(path, "r")
  if not fh then return nil end
  local text = fh:read("a")
  fh:close()
  return text
end

return {
  ["diagram"] = function(args, kwargs, meta)
    if #args == 0 then
      quarto.log.warning("playbook: {{< diagram >}} called without a name")
      return pandoc.Null()
    end

    local name = pandoc.utils.stringify(args[1])
    local rel = DIR .. name .. ".svg"
    local svg = read_file(pandoc.path.join({ project_root(), rel }))

    if not svg then
      -- A missing diagram is a content error, not a build error: warn and
      -- leave the surrounding prose intact.
      quarto.log.warning("playbook: diagram '" .. name .. "' not found at " .. rel)
      return pandoc.Null()
    end

    -- Non-HTML output (PDF, docx) cannot take inline SVG. It also cannot read
    -- the CSS, so such a diagram renders unstyled — acceptable, since HTML is
    -- the only target that ships.
    if not quarto.doc.is_format("html:js") then
      return pandoc.Image({ pandoc.Str(name) }, rel)
    end

    -- Legal at the top of a standalone file, invalid inside an HTML body.
    svg = svg:gsub("<%?xml.-%?>", ""):gsub("<!DOCTYPE.->", "")

    return pandoc.RawBlock("html", '<div class="pb-diagram">' .. svg .. "</div>")
  end,
}
