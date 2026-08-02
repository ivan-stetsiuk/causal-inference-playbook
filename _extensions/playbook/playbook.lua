--- Playbook block types: .recall, .assumption, .quiz.
---
--- These operate on the Pandoc AST rather than on raw text, so math, lists,
--- links and nested blocks all survive inside them.
---
--- Syntax:
---
---   ::: {.recall}
---   Randomization makes assignment independent of the potential outcomes.
---   :::
---
---   ::: {.assumption name="Ignorability"}
---   $(Y_0, Y_1) \perp T \mid X$
---   :::
---
---   ::: {.quiz question="Why does controlling for a collider hurt?"}
---   Because it opens a path that did not exist ...
---   :::

local function has_class(el, name)
  return el.attr and el.classes and el.classes:includes(name)
end

--- Anchor counter, so a .recall can be linked to from another page.
local recall_n = 0

--- .assumption — injects the visible name as the first element.
local function render_assumption(div)
  local name = div.attributes["name"]
  if not name or name == "" then
    -- An unnamed assumption cannot be cross-referenced, which is the whole
    -- reason the block exists. Warn, but do not fail the build.
    quarto.log.warning(
      "playbook: ::: {.assumption} without a name= attribute — it will render, " ..
      "but nothing can link to it"
    )
    name = "Unnamed"
  end

  local header = pandoc.Div(
    pandoc.Plain(pandoc.Str(name)),
    pandoc.Attr("", { "assumption-name" })
  )
  table.insert(div.content, 1, header)

  -- The name has been consumed into the header; leaving it on the div would
  -- emit an invalid `name` attribute on an HTML <div>.
  div.attributes["name"] = nil

  if div.identifier == "" then
    -- Stable anchor derived from the name: reordering blocks will not break
    -- existing links.
    div.identifier = "asm-" .. name:lower():gsub("%s+", "-"):gsub("[^%w%-]", "")
  end
  return div
end

--- .quiz — becomes a <details> so the answer takes a deliberate click.
--- Attempting recall before looking is the retention mechanism.
local function render_quiz(div)
  local question = div.attributes["question"]
  if not question or question == "" then
    quarto.log.warning("playbook: ::: {.quiz} without a question= attribute — skipping")
    return div
  end

  if quarto.doc.is_format("html:js") then
    local parsed = pandoc.read(question, "markdown").blocks
    local summary_inlines = (#parsed > 0 and parsed[1].content)
      or pandoc.Inlines({ pandoc.Str(question) })

    local out = pandoc.List()
    out:insert(pandoc.RawBlock("html", '<details class="quiz">'))
    out:insert(pandoc.RawBlock("html", "<summary>"))
    out:insert(pandoc.Plain(summary_inlines))
    out:insert(pandoc.RawBlock("html", "</summary>"))
    out:insert(pandoc.Div(div.content, pandoc.Attr("", { "quiz-answer" })))
    out:insert(pandoc.RawBlock("html", "</details>"))
    return out
  end

  -- Non-HTML output (PDF, docx): show the answer, there is nothing to hide
  -- it behind.
  table.insert(div.content, 1, pandoc.Para({ pandoc.Strong(pandoc.Str(question)) }))
  return div
end

--- .tip — an inline explanation, shown on hover or on keyboard focus.
---
---   [$\mathbb{E}[Y(0) \mid T = 0] = 35$]{.tip tip="The three who did not go ..."}
---
--- The text moves to data-tip, which CSS renders through content: attr(...).
--- Two things that are easy to get wrong and are handled here: tabindex, so
--- the bubble can be opened without a mouse at all, and a visually hidden
--- copy of the text, because a screen reader cannot see a ::after bubble.
--- The hidden copy sits inside the trigger, so it is read as part of it.
local function render_tip(span)
  local text = span.attributes["tip"]
  if not text or text == "" then
    quarto.log.warning("playbook: [...]{.tip} without a tip= attribute")
    return span
  end

  span.attributes["tip"] = nil
  span.attributes["data-tip"] = text
  span.attributes["tabindex"] = "0"
  span.classes:insert("pb-tip")

  span.content:insert(pandoc.Span(
    pandoc.Str(" — " .. text),
    pandoc.Attr("", { "pb-sr-only" })
  ))
  return span
end

--- .recall — attach an anchor. All styling lives in CSS.
local function render_recall(div)
  recall_n = recall_n + 1
  if div.identifier == "" then
    div.identifier = "recall-" .. recall_n
  end
  return div
end

function Div(div)
  if has_class(div, "recall") then return render_recall(div) end
  if has_class(div, "assumption") then return render_assumption(div) end
  if has_class(div, "quiz") then return render_quiz(div) end
  return nil
end

function Span(span)
  if has_class(span, "tip") then return render_tip(span) end
  return nil
end
