# Causal Inference Playbook — Architecture

An interactive set of notes written while working through
[Causal Inference for the Brave and True](https://matheusfacure.github.io/python-causality-handbook/)
and supplementary sources.

**Goal 1** — master the tools and retain the material.
**Goal 2** — make it look like a professional publication.

Everything below follows that order of priority.

---

## 1. Decisions

| # | Decision | Choice | Consequence |
|---|---|---|---|
| D1 | Execution languages | **Python + R** | Two engines in one project; Pyodide + WebR in the browser |
| D2 | Repository and hosting | **Public repo + GitHub Pages** | Free deploys via GH Actions; the site doubles as a portfolio |
| D3 | Retention layer | **Full** | Chapter template, `.recall` blocks, auto-glossary, Anki export, self-checks |
| D4 | Site generator | **Quarto** | See §2 |
| D5 | Quarto project type | **website** (not `book`) | Needs heterogeneous sections: notes, explorables, labs, glossary |
| D6 | Execution strategy | **`freeze: auto`**, `_freeze/` committed | CI renders cached output and never runs Python/R — fast, secret-free deploys |
| D7 | Content language | **English** | Docs, comments, and prose are English; conversation happens in Russian |

### Why Quarto

| Alternative | Why rejected |
|---|---|
| Jupyter Book / MyST | Python-only, which conflicts with D1. Weaker typography and cross-references |
| Next.js / Astro + MDX | Maximum customization, but you build the execution layer yourself — work unrelated to the subject |
| Obsidian Publish | Great notes, zero code execution |
| Streamlit / Shiny Server | Requires a server, which contradicts D2 (Pages serves static files only) |

Quarto gives us out of the box: `.qmd` carrying Python and R in one document,
native interactive Plotly embedding, math, cross-references and citations,
callout blocks, full-text search, dark mode, and a sidebar. It extends through
Lua filters and shortcodes, which is enough to deliver D3.

---

## 2. The core constraint and how it is removed

GitHub Pages serves **static files**. No Python runs on the server. All
interactivity therefore moves into the reader's browser. That is not a
compromise — Python genuinely executes in the browser today via WebAssembly.

This produces the central architectural device: **three tiers of
interactivity**, each with its own cost.

| Tier | Where it runs | Use for | Cost |
|---|---|---|---|
| **T1 — build time** | Real Python/R locally; output frozen into `_freeze/` | Heavy analysis: `econml`, `dowhy`, `linearmodels`, `fixest`, large simulations. Output is baked interactive Plotly | Zero page-load cost, full library access, but parameters are fixed |
| **T2 — WASM runtime** | Pyodide / WebR in the browser (`quarto-live`) | Editable "try it yourself" cells, checking a formula by hand, sliders over real numpy/pandas | 5–15 s first engine boot, limited package set |
| **T3 — plain JS** | Observable JS + Plot / D3 | Instant slider→chart feedback: DAG explorers, bias formulas, Simpson's paradox, overlap, power analysis | Zero boot, but you write JS |

### Choosing a tier

- The point is **intuition about a parameter** → **T3**. A slider that lags
  destroys the intuition it was meant to build.
- The point is **"I can run and change this myself"** → **T2**.
- The point is **the actual estimator on the actual data** → **T1**.

### What is available in T2 (Pyodide)

Works: `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `plotly`,
`scikit-learn`. **Does not work**: `econml`, `dowhy` (compiled extensions) —
which is precisely why T1 exists. WebR ships a CRAN subset built for wasm;
heavy econometrics packages need case-by-case checking.

---

## 3. Stack

| Layer | Tool | Install / status |
|---|---|---|
| Site generator | Quarto CLI 1.10.18 | Installed from tarball to `~/.local/opt/quarto` (the cask needs an admin password) |
| Python | conda 3.11.5 | pandas 2.2.2, numpy 1.26.4, plotly 6.3.0, statsmodels 0.14.2, linearmodels 6.0, sklearn 1.4.1 |
| R | R 4.5.1 | knitr 1.50, rmarkdown 2.31, plotly 4.12.1, jsonlite 2.0.0 |
| WASM execution | `quarto-live` 0.1.3 | `quarto add r-wasm/quarto-live` |
| Reactive JS | Observable JS + Observable Plot | Bundled with Quarto |
| T1 charts | Plotly, single shared template | `pylib/viz.py` + `R/viz.R`, both reading `theme/palette.json` |
| Math | KaTeX (`html-math-method: katex`) | Faster than the MathJax default |
| Bibliography | `references.bib` + CSL | — |
| Editing | VS Code + Quarto extension, **Visual Editor** (`⇧⌘F4`) | WYSIWYG with slash commands — a Notion-like layer over git-tracked files |
| Deployment | GitHub Actions → GitHub Pages | `.github/workflows/publish.yml` |

Escape hatch if T3 is not enough for some explorable: **Shinylive** — a full
reactive Shiny app compiled to wasm, still fully static. Added case by case,
not part of the base.

---

## 4. Repository layout

```
causal-inference-playbook/
├── _quarto.yml                  # navigation, theme, engines, freeze, render hooks
├── index.qmd                    # landing page: course map, how a chapter works
│
├── notes/                       # chapter notes — the core of the project
│   └── 01-introduction.qmd
│
├── explorables/                 # T3: reactive OJS components
│   └── confounding-bias.qmd
│
├── labs/                        # T2: WASM "try it yourself" sandboxes
│   └── wasm-check.qmd
│
├── glossary.qmd                 # generated from _glossary.yml
├── recall.qmd                   # every .recall / .quiz card in one place
│
├── pylib/                       # shared Python
│   ├── dgp.py                   # data generators with known ground truth
│   └── viz.py                   # Plotly template + semantic colors
├── R/viz.R                      # the R mirror of viz.py
│
├── theme/
│   ├── palette.json             # SINGLE SOURCE OF TRUTH for every color
│   ├── tokens.css               # generated
│   ├── tokens.js                # generated
│   ├── _tokens-{light,dark}.scss # generated Bootstrap variables
│   ├── _scripts.html            # generated inline script bundle
│   ├── components.css           # hand-written, references variables only
│   ├── plotly-theme-sync.js     # recolors baked charts on theme toggle
│   └── {light,dark}.scss        # hand-written non-color rules
│
├── _extensions/playbook/        # Lua filters and the {{< term >}} shortcode
├── scripts/
│   ├── build_tokens.py          # palette.json -> all generated theme files
│   ├── recall_parser.py         # extracts .recall / .quiz from .qmd sources
│   └── export_anki.py           # cards -> TSV for Anki
│
├── _freeze/                     # cached cell output — COMMITTED
├── _glossary.yml                # glossary, merged into document metadata
├── environment.yml              # conda environment
├── install-r-deps.R             # R packages
└── .github/workflows/publish.yml
```

### The single source of truth for color

`theme/palette.json` is the only file containing hex values. Everything else
derives from it:

```
theme/palette.json
   ├── scripts/build_tokens.py ──┬── theme/tokens.css          (site CSS variables)
   │                             ├── theme/tokens.js           (browser palette)
   │                             ├── theme/_tokens-*.scss      (Bootstrap variables)
   │                             └── theme/_scripts.html       (inline bundle)
   ├── pylib/viz.py              ──── Plotly template, Python  (T1)
   ├── R/viz.R                   ──── Plotly template, R       (T1)
   └── FileAttachment(...)       ──── OJS explorables          (T3)
```

Bootstrap SCSS variables compile at build time and cannot read CSS custom
properties, so they are generated rather than hand-written — otherwise the site
chrome would silently drift away from the chart colors.

The palette is validated, not eyeballed. The three core causal roles —
control / treated / counterfactual — occupy the three slots that clear the
strict all-pairs colorblindness check, so scatter plots with those series stay
readable under any form of CVD.

| Check | Light | Dark |
|---|---|---|
| Causal core (3 slots), all-pairs CVD ΔE | 9.2 | 9.4 |
| Causal core, normal vision ΔE | 24.0 | 20.9 |
| Full 8 slots, adjacent CVD ΔE | 9.1 | 8.4 |

Three light-mode slots sit below 3:1 contrast against the surface. That is not
a prohibition but an obligation: those series ship with visible direct labels
or a table view.

---

## 5. Retention layer (D3)

The project's primary goal is retention, so the review mechanics are built into
the architecture rather than left to willpower.

### 5.1 Chapter template

Every file in `notes/` follows the same seven steps. The order is deliberate:
intuition before formalism, code before the explorable, own words last.

1. **The question** — what problem the chapter solves, in one sentence
2. **Intuition** — before any math
3. **Formalism** — the estimand plus assumptions as named blocks
4. **Verify with code** — simulate a DGP with known truth, confirm the estimator recovers it
5. **Explorable** — break an assumption with a slider, watch the bias appear
6. **When it breaks** — failure modes and diagnostics
7. **In my own words** — a summary written without looking back

Step 4 carries the most retention value. In real data the counterfactual is
never observed, so there is nothing to check an estimator against. In a
simulation it *is* observed, because we defined both potential outcomes
ourselves. If the estimator returns the effect we planted, the estimator is
understood. If it does not, we have learned exactly what we do not understand.

### 5.2 Mechanics

| Element | Syntax | What it does |
|---|---|---|
| Fact to retain | `::: {.recall}` … `:::` | Styled card, anchored, exported |
| Term | `{{< term ate >}}` | Glossary link with a hover definition |
| Assumption | `::: {.assumption name="Ignorability"}` | Named block, cross-referenceable |
| Self-check | `::: {.quiz question="…"}` | Question with the answer behind a disclosure |
| Anki export | `scripts/export_anki.py` (post-render) | Parses `.recall` / `.quiz`, writes TSV into `_site/` |
| Review page | `recall.qmd` | Every card grouped by chapter |

Parsing runs against `.qmd` sources rather than rendered HTML, so a card exists
before the render and the review page never depends on build order.

---

## 6. Design system (Goal 2)

A professional look comes from every chart reading as one product, not from
decorating individual charts. So the tokens are defined once and reused.

- **Palette** lives in `theme/palette.json` and flows to CSS, both Plotly
  engines, and OJS. Requirements: WCAG-grade contrast, CVD separation validated
  by script, and stable semantics — treatment / control / counterfactual keep
  the same color site-wide.
- **Plotly template** — no chart is ever drawn with default styling. One grid,
  one font, one set of margins, consistent hover behavior, no chart junk.
- **Light and dark are both first-class**, including charts: baked figures are
  recolored on theme toggle by `theme/plotly-theme-sync.js`, since SVG
  attributes do not respond to CSS variables.
- **Semantics of form** — point estimates with intervals always look the same;
  counterfactual quantities are always dashed.

---

## 7. Build and deploy pipeline

```
local:   edit .qmd (VS Code Visual Editor)
            ↓
         quarto preview          — live view, runs only changed cells
            ↓
         quarto render           — refreshes _freeze/
            ↓
         git commit (including _freeze/)
            ↓
         git push
            ↓
GH Actions: setup-quarto → quarto render (NO execution, reads _freeze/)
            ↓
         deploy-pages → https://ivan-stetsiuk.github.io/causal-inference-playbook
```

Because of `freeze: auto` and a committed `_freeze/`, CI needs **no** conda, no
R, no datasets, and no secrets. Actions only assembles HTML from finished
output. Deploys take seconds and cannot break because a package version moved.

The trade-off: rendering must happen locally before pushing, or cell changes
never reach the site. A pre-commit hook catches this.

---

## 8. Rollout order

1. ✅ Install Quarto, init git repo
2. ✅ Design system: validated palette, generated tokens, Plotly templates for both engines
3. ✅ Quarto website skeleton: `_quarto.yml`, navigation, landing page
4. ✅ `playbook` extension: Lua filters for `.recall` / `.assumption` / `.quiz`, `{{< term >}}` shortcode
5. ✅ `quarto-live` plus a page exercising `{pyodide}` and `{webr}` cells
6. ✅ Chapter template and the reference chapter `01-introduction.qmd`
7. ✅ First OJS explorable — T3 verified end to end
8. ✅ Retention layer: `export_anki.py`, `glossary.qmd`, `recall.qmd`
9. ✅ `.github/workflows/publish.yml`, GitHub Pages enabled, first deploy live

Adding chapters is now purely content work.

### Enabling Pages (one-time, already done)

`actions/deploy-pages` fails with a bare `404 Not Found` when Pages has never
been enabled for the repository — the error names the cause only in its final
line. Pushing the workflow file is not enough; the repository has to be told
that Actions is the publishing source:

```bash
gh api -X POST repos/ivan-stetsiuk/causal-inference-playbook/pages \
  -f build_type=workflow
```

The equivalent in the UI is Settings → Pages → Build and deployment →
Source: GitHub Actions.
