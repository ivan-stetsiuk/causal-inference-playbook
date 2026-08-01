// Keep baked Plotly charts in sync with Quarto's theme toggle.
//
// The problem: T1 charts (see ARCHITECTURE.md §2) are computed at build time
// and land on the page with their colors already fixed. Toggling the theme
// swaps CSS, but nothing in CSS reaches the SVG attributes inside a chart —
// without this script a chart stays a bright rectangle in dark mode.
//
// The fix: on a theme change, walk every chart, restyle the chrome
// (background, font, grid, axes) and remap series colors through the
// light<->dark table from theme/tokens.js — the same palette.json that feeds
// everything else.

(function () {
  "use strict";

  const isDark = () => document.body.classList.contains("quarto-dark");

  function chrome(mode) {
    const p = window.PLAYBOOK_PALETTE;
    const c = p.chrome[mode];
    return {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      "font.color": c.ink,
      "font.family": p.typography.sans,
      "title.font.color": c.ink,
      "xaxis.gridcolor": c.grid,
      "yaxis.gridcolor": c.grid,
      "xaxis.linecolor": c.axis,
      "yaxis.linecolor": c.axis,
      "xaxis.zerolinecolor": c.axis,
      "yaxis.zerolinecolor": c.axis,
      "xaxis.tickfont.color": c["ink-muted"],
      "yaxis.tickfont.color": c["ink-muted"],
      "xaxis.title.font.color": c["ink-2"],
      "yaxis.title.font.color": c["ink-2"],
      "legend.font.color": c["ink-2"],
      "hoverlabel.bgcolor": c.surface,
      "hoverlabel.bordercolor": c.axis,
      "hoverlabel.font.color": c.ink,
    };
  }

  // Remap one color. Unknown colors pass through untouched: a series colored
  // by hand outside the palette should not break.
  function mapColor(color, table) {
    if (typeof color !== "string") return color;
    return table[color.toLowerCase()] || color;
  }

  function mapDeep(value, table) {
    if (Array.isArray(value)) return value.map((v) => mapColor(v, table));
    return mapColor(value, table);
  }

  function applyTheme(gd, mode) {
    const p = window.PLAYBOOK_PALETTE;
    const table = mode === "dark" ? p.swapLightToDark : p.swapDarkToLight;
    const lower = {};
    for (const [k, v] of Object.entries(table)) lower[k.toLowerCase()] = v;

    // Series: marker fills, lines, borders.
    if ((gd.data || []).length) {
      const restyle = {
        "marker.color": [],
        "marker.line.color": [],
        "line.color": [],
        fillcolor: [],
      };
      let touched = false;
      for (const trace of gd.data) {
        const mc = trace.marker && trace.marker.color;
        const mlc = trace.marker && trace.marker.line && trace.marker.line.color;
        const lc = trace.line && trace.line.color;
        const fc = trace.fillcolor;
        restyle["marker.color"].push(mc === undefined ? undefined : mapDeep(mc, lower));
        restyle["marker.line.color"].push(mlc === undefined ? undefined : mapDeep(mlc, lower));
        restyle["line.color"].push(lc === undefined ? undefined : mapDeep(lc, lower));
        restyle.fillcolor.push(fc === undefined ? undefined : mapDeep(fc, lower));
        if (mc || mlc || lc || fc) touched = true;
      }
      if (touched) Plotly.restyle(gd, restyle);
    }

    // Reference lines and their labels live in layout, not in the traces, so
    // they need their own pass — otherwise a truth line keeps its light-mode
    // ink against a dark surface.
    const layoutPatch = Object.assign({ colorway: p.series[mode] }, chrome(mode));

    (gd.layout.shapes || []).forEach((shape, i) => {
      if (shape.line && shape.line.color) {
        layoutPatch[`shapes[${i}].line.color`] = mapColor(shape.line.color, lower);
      }
    });

    (gd.layout.annotations || []).forEach((ann, i) => {
      if (ann.font && ann.font.color) {
        layoutPatch[`annotations[${i}].font.color`] = mapColor(ann.font.color, lower);
      }
      if (ann.bgcolor) {
        layoutPatch[`annotations[${i}].bgcolor`] = mapColor(ann.bgcolor, lower);
      }
    });

    Plotly.relayout(gd, layoutPatch);
  }

  function syncAll() {
    if (!window.Plotly || !window.PLAYBOOK_PALETTE) return;
    const mode = isDark() ? "dark" : "light";
    document.querySelectorAll(".js-plotly-plot").forEach((gd) => {
      try {
        applyTheme(gd, mode);
      } catch (e) {
        console.warn("plotly-theme-sync: failed to recolor a chart", e);
      }
    });
  }

  // Quarto swaps a class on <body> when the theme changes, which is signal
  // enough — no custom event to wait for.
  const observer = new MutationObserver((records) => {
    if (records.some((r) => r.attributeName === "class")) syncAll();
  });

  function start() {
    observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    // First pass: the page may have loaded straight into dark mode.
    if (isDark()) syncAll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
