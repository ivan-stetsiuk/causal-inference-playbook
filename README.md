# Causal Inference Playbook

Interactive notes written while working through
[Causal Inference for the Brave and True](https://matheusfacure.github.io/python-causality-handbook/).

**Live site:** https://ivan-stetsiuk.github.io/causal-inference-playbook

Every chapter ends with a simulation where the true effect is known in
advance, and an estimator that has to recover it. If the estimator returns the
planted effect, the estimator is understood. If not, the gap is the lesson.

## Quick start

```bash
# Python (build-time execution)
conda env create -f environment.yml
conda activate causal-playbook

# R
Rscript install-r-deps.R

# Serve locally with live reload
quarto preview
```

Quarto itself is installed at `~/.local/opt/quarto` and symlinked onto `PATH`.
To reinstall or upgrade, grab the macOS tarball from
[quarto-cli releases](https://github.com/quarto-dev/quarto-cli/releases)
(the Homebrew cask needs an admin password; the tarball does not).

## Before you push

```bash
quarto render          # refreshes _freeze/
git add _freeze
git commit && git push
```

`_freeze/` **is committed on purpose.** It holds cached cell output, which is
what lets CI build the site without running Python or R — no conda in Actions,
no package-version drift, no secrets. The trade-off is that rendering must
happen locally, or code changes never reach the published site.

## Layout

| Path | What lives there |
|---|---|
| `notes/` | Chapter notes — the core of the project |
| `explorables/` | Reactive OJS components (tier T3) |
| `labs/` | Browser-executed Python and R via WebAssembly (tier T2) |
| `pylib/`, `R/` | Shared helpers: data generators, chart theming |
| `theme/` | `palette.json` plus everything generated from it |
| `_extensions/playbook/` | Lua filters and the `{{< term >}}` shortcode |
| `scripts/` | Token generation, card parsing, Anki export |

## Authoring

Chapters follow a fixed seven-step template — the question, intuition,
formalism, verification in code, an explorable, failure modes, and a summary
in my own words. The rationale is in
[ARCHITECTURE.md](ARCHITECTURE.md#5-retention-layer-d3).

Custom blocks available in any `.qmd`:

```markdown
::: {.recall}
A fact worth retaining. Collected onto the review page and exported to Anki.
:::

::: {.assumption name="Ignorability"}
$(Y(0), Y(1)) \perp T \mid X$
:::

::: {.quiz question="Why does more data not fix selection bias?"}
Because bias is a property of the assignment mechanism, not the sample size.
:::

The {{< term ate >}} shortcode links to the glossary with a hover definition.
```

## Colors

`theme/palette.json` is the only file in the repo containing hex values.
Everything else — site CSS, Bootstrap variables, both Plotly templates, and
the OJS explorables — is generated from it or reads it at runtime. Change a
color there and it propagates everywhere on the next render.

The palette is validated rather than eyeballed: the three core causal roles
(control / treated / counterfactual) occupy the three slots that clear a
strict all-pairs colorblindness check in both light and dark mode.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — decisions, the three interactivity
  tiers, and why the stack looks like this
