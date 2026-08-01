# R packages for build-time execution (tier T1).
#
# Plain script rather than renv: because CI never runs R (cell output is
# cached in _freeze/), a lockfile would only add friction on the one machine
# that does the rendering.
#
#   Rscript install-r-deps.R

repos <- "https://cloud.r-project.org"

required <- c(
  # Quarto's knitr engine
  "knitr",
  "rmarkdown",

  # Charts and the palette bridge
  "plotly",
  "jsonlite",
  "ggplot2",

  # Data wrangling
  "dplyr",
  "tidyr",
  "broom",

  # Causal inference
  "fixest",    # fast fixed effects, difference-in-differences
  "MatchIt",   # matching
  "AER",       # instrumental variables
  "dagitty",   # DAGs
  "ggdag"
)

missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]

if (length(missing) == 0L) {
  message("All R packages already present.")
} else {
  message("Installing: ", paste(missing, collapse = ", "))
  install.packages(missing, repos = repos)
}

# Report what is actually loadable, so a silent build failure is visible here
# rather than three steps later inside a render.
for (p in required) {
  ok <- requireNamespace(p, quietly = TRUE)
  version <- if (ok) as.character(packageVersion(p)) else "MISSING"
  message(sprintf("%-12s %s", p, version))
}
