"""Shared visual layer for the playbook's build-time charts (tier T1).

No chart is ever drawn with Plotly's default styling. Everything here derives
from theme/palette.json — the same file that generates the site's CSS
variables and feeds the OJS explorables.

Usage inside a chapter:

    import sys; sys.path.insert(0, "..")
    from pylib.viz import px, go, apply_theme, C, truth_line

    fig = px.scatter(df, x="x", y="y", color="group")
    truth_line(fig, y=2.0, label="True ATE")
    apply_theme(fig)
    fig
"""

from __future__ import annotations

import json
from pathlib import Path

import plotly.express as px  # noqa: F401  (re-exported for chapters)
import plotly.graph_objects as go  # noqa: F401  (re-exported for chapters)
import plotly.io as pio

_PALETTE_PATH = Path(__file__).resolve().parent.parent / "theme" / "palette.json"
PALETTE: dict = json.loads(_PALETTE_PATH.read_text(encoding="utf-8"))

# Charts are baked in this mode. The dark variant is produced in the reader's
# browser by theme/plotly-theme-sync.js.
BAKE_MODE = "light"


class _Colors:
    """Colors addressed by meaning rather than by index.

    ``C.treated`` reads in chapter code; ``series[1]`` does not. The role also
    guarantees one meaning keeps one color everywhere.
    """

    def __init__(self, mode: str = BAKE_MODE) -> None:
        self._mode = mode
        self._series = PALETTE["series"][mode]
        for role, spec in PALETTE["semantic"].items():
            setattr(self, role, self._series[spec["slot"]])
        for name, hex_ in PALETTE["reference"][mode].items():
            setattr(self, f"ref_{name}", hex_)
        for name, hex_ in PALETTE["status"].items():
            if not name.startswith("_"):
                setattr(self, name, hex_)

    def series(self, i: int) -> str:
        """Categorical slot, numbered from 1."""
        if not 1 <= i <= len(self._series):
            raise IndexError(
                f"slot {i} is outside the palette (1..{len(self._series)}). "
                "A ninth series is never a new invented hue — fold it into "
                "'Other' or split into small multiples."
            )
        return self._series[i - 1]

    @property
    def all(self) -> list[str]:
        return list(self._series)

    def dash(self, role: str) -> str:
        """Dash pattern for a role. Counterfactuals are always dashed."""
        return PALETTE["semantic"][role].get("dash", "solid")


C = _Colors()


def _template(mode: str) -> go.layout.Template:
    ch = PALETTE["chrome"][mode]
    font = PALETTE["typography"]["sans"]

    axis = dict(
        showgrid=True,
        gridcolor=ch["grid"],
        gridwidth=1,
        zeroline=True,
        zerolinecolor=ch["axis"],
        zerolinewidth=1,
        showline=True,
        linecolor=ch["axis"],
        linewidth=1,
        ticks="outside",
        ticklen=4,
        tickcolor=ch["axis"],
        tickfont=dict(color=ch["ink-muted"], size=12),
        title=dict(font=dict(color=ch["ink-2"], size=13)),
        automargin=True,
    )

    return go.layout.Template(
        layout=dict(
            colorway=PALETTE["series"][mode],
            # Transparent background: the page supplies the surface color, so
            # the chart survives a theme toggle.
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=font, size=13, color=ch["ink"]),
            title=dict(
                font=dict(family=font, size=16, color=ch["ink"]),
                x=0,
                xanchor="left",
                pad=dict(b=12),
            ),
            xaxis=axis,
            yaxis=axis,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(color=ch["ink-2"], size=12),
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                title=dict(text=""),
            ),
            margin=dict(l=8, r=8, t=48, b=8),
            hovermode="closest",
            hoverlabel=dict(
                bgcolor=ch["surface"],
                bordercolor=ch["axis"],
                font=dict(family=font, size=12, color=ch["ink"]),
                align="left",
            ),
            colorscale=dict(
                sequential=[
                    [i / 6, PALETTE["sequential"]["steps"][s]]
                    for i, s in enumerate(["100", "200", "300", "400", "500", "600", "700"])
                ],
                diverging=[
                    [0.0, PALETTE["diverging"]["negative"][mode]],
                    [0.5, PALETTE["diverging"]["midpoint"][mode]],
                    [1.0, PALETTE["diverging"]["positive"][mode]],
                ],
            ),
        )
    )


pio.templates["playbook_light"] = _template("light")
pio.templates["playbook_dark"] = _template("dark")
pio.templates.default = f"playbook_{BAKE_MODE}"


def apply_theme(fig: go.Figure, mode: str = BAKE_MODE) -> go.Figure:
    """Seat a figure on the template and bring its marks to spec.

    Lines at 2px, markers at least 8px with a surface-colored ring so
    overlapping points stay separable.
    """
    ch = PALETTE["chrome"][mode]
    fig.update_layout(template=f"playbook_{mode}")

    # plotly.express names the legend after the dataframe column ("group"),
    # which is an implementation detail leaking into the chart. The series
    # labels already say what the colors mean.
    fig.update_layout(legend_title_text="")

    for tr in fig.data:
        if tr.type in ("scatter", "scattergl"):
            trace_mode = getattr(tr, "mode", "") or ""
            if "lines" in trace_mode:
                tr.line.width = tr.line.width or 2
            if "markers" in trace_mode:
                if not tr.marker.size:
                    tr.marker.size = 8
                # A surface-colored ring separates overlapping marks.
                tr.marker.line.width = tr.marker.line.width or 1.5
                tr.marker.line.color = tr.marker.line.color or ch["surface"]
        elif tr.type == "bar":
            # 2px surface gap between adjacent fills.
            tr.marker.line.width = tr.marker.line.width or 2
            tr.marker.line.color = tr.marker.line.color or ch["surface"]

    return fig


def truth_line(
    fig: go.Figure,
    y: float,
    label: str = "Truth",
    mode: str = BAKE_MODE,
    axis: str = "y",
) -> go.Figure:
    """Reference line for the simulation's known ground truth.

    Drawn in chrome ink rather than a series color: the truth is a datum to
    measure against, not one more estimate competing for attention.
    """
    color = PALETTE["reference"][mode]["truth"]
    kwargs = dict(
        line=dict(color=color, width=1.5, dash="dot"),
        annotation=dict(
            text=label,
            # No background box: a baked-in surface color would stay light
            # after a theme toggle. The dotted rule separates it well enough.
            font=dict(color=color, size=11),
        ),
        annotation_position="top left" if axis == "y" else "top right",
    )
    if axis == "y":
        fig.add_hline(y=y, **kwargs)
    else:
        fig.add_vline(x=y, **kwargs)
    return fig


def semantic_map(*roles: str, mode: str = BAKE_MODE) -> dict[str, str]:
    """A ready color_discrete_map for plotly.express keyed by role labels.

        px.scatter(df, color="group",
                   color_discrete_map=semantic_map("control", "treated"))
    """
    series = PALETTE["series"][mode]
    return {
        PALETTE["semantic"][r]["label"]: series[PALETTE["semantic"][r]["slot"]]
        for r in roles
    }
