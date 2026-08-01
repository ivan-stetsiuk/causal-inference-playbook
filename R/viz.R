# Visual layer for R chapters. Mirrors pylib/viz.py and reads the same
# theme/palette.json, so both engines cannot drift apart.
#
# Usage inside a chapter:
#   source(file.path("..", "R", "viz.R"))
#   plot_ly(df, x = ~x, y = ~y) |> apply_theme()

suppressPackageStartupMessages({
  library(jsonlite)
  library(plotly)
})

# Chapters render with their own directory as the working directory, so the
# palette is looked up by walking upwards rather than assuming a fixed depth.
.find_palette <- function() {
  candidates <- c(
    "theme/palette.json",
    "../theme/palette.json",
    "../../theme/palette.json"
  )
  hit <- candidates[file.exists(candidates)]
  if (length(hit) == 0L) {
    stop("R/viz.R: theme/palette.json not found from ", getwd())
  }
  normalizePath(hit[1])
}

PALETTE <- jsonlite::fromJSON(.find_palette(), simplifyVector = TRUE)

# Charts are baked in this mode; the dark variant is produced in the browser
# by theme/plotly-theme-sync.js.
BAKE_MODE <- "light"

#' Color addressed by meaning rather than by slot index.
#' @examples C("treated"); C("counterfactual")
C <- function(role, mode = BAKE_MODE) {
  if (!is.null(PALETTE$semantic[[role]])) {
    slot <- PALETTE$semantic[[role]]$slot
    return(PALETTE$series[[mode]][slot + 1L])
  }
  if (!is.null(PALETTE$status[[role]])) return(PALETTE$status[[role]])
  if (!is.null(PALETTE$reference[[mode]][[role]])) {
    return(PALETTE$reference[[mode]][[role]])
  }
  stop(sprintf("unknown color role: '%s'", role))
}

#' Categorical slot, numbered from 1.
series <- function(i, mode = BAKE_MODE) {
  pal <- PALETTE$series[[mode]]
  if (i < 1 || i > length(pal)) {
    stop(sprintf(
      paste0(
        "slot %d is outside the palette (1..%d). A ninth series is never a ",
        "new invented hue - fold it into 'Other' or use small multiples."
      ),
      i, length(pal)
    ))
  }
  pal[i]
}

#' Bring a plotly figure to the playbook's styling.
apply_theme <- function(p, mode = BAKE_MODE) {
  ch <- PALETTE$chrome[[mode]]
  font <- PALETTE$typography$sans

  axis <- list(
    showgrid = TRUE, gridcolor = ch$grid, gridwidth = 1,
    zeroline = TRUE, zerolinecolor = ch$axis, zerolinewidth = 1,
    showline = TRUE, linecolor = ch$axis, linewidth = 1,
    ticks = "outside", ticklen = 4, tickcolor = ch$axis,
    tickfont = list(color = ch$`ink-muted`, size = 12),
    title = list(font = list(color = ch$`ink-2`, size = 13)),
    automargin = TRUE
  )

  plotly::layout(
    p,
    colorway = PALETTE$series[[mode]],
    # Transparent background: the page supplies the surface color, so the
    # chart survives a theme toggle.
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor = "rgba(0,0,0,0)",
    font = list(family = font, size = 13, color = ch$ink),
    title = list(
      font = list(family = font, size = 16, color = ch$ink),
      x = 0, xanchor = "left"
    ),
    xaxis = axis,
    yaxis = axis,
    legend = list(
      orientation = "h", yanchor = "bottom", y = 1.02,
      xanchor = "left", x = 0,
      font = list(color = ch$`ink-2`, size = 12),
      bgcolor = "rgba(0,0,0,0)", borderwidth = 0
    ),
    margin = list(l = 8, r = 8, t = 48, b = 8),
    hovermode = "closest",
    hoverlabel = list(
      bgcolor = ch$surface, bordercolor = ch$axis,
      font = list(family = font, size = 12, color = ch$ink),
      align = "left"
    )
  )
}

#' Reference line for the simulation's known ground truth. Drawn in chrome
#' ink rather than a series color: the truth is a datum to measure against,
#' not one more estimate competing for attention.
truth_line <- function(p, y, label = "Truth", mode = BAKE_MODE) {
  col <- PALETTE$reference[[mode]]$truth
  plotly::layout(
    p,
    shapes = list(list(
      type = "line", xref = "paper", x0 = 0, x1 = 1, y0 = y, y1 = y,
      line = list(color = col, width = 1.5, dash = "dot")
    )),
    annotations = list(list(
      xref = "paper", x = 0, y = y, text = label, showarrow = FALSE,
      xanchor = "left", yanchor = "bottom",
      font = list(color = col, size = 11),
      bgcolor = PALETTE$chrome[[mode]]$surface
    ))
  )
}
