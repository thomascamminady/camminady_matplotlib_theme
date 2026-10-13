"""Design tokens and matplotlib rcParams of the camminady styles.

The tokens and their defaults are those of the Altair theme in
``camminady_altair_theme``, so that charts made with either library look
alike. Sizes are in points; the styles set ``figure.dpi`` to 72, so that one
point is one pixel on screen, as in Vega.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Final, Literal

from cycler import Cycler, cycler

FontWeight = Literal[
    "normal",
    "bold",
    100,
    200,
    300,
    400,
    500,
    600,
    700,
    800,
    900,
]

TABLEAU10: Final[tuple[str, ...]] = (
    "#4c78a8",
    "#f58518",
    "#e45756",
    "#72b7b2",
    "#54a24b",
    "#eeca3b",
    "#b279a2",
    "#ff9da6",
    "#9d755d",
    "#bab0ac",
)
"""Vega's default ``tableau10`` category palette, used as the colour cycle."""

OKABE_ITO: Final[tuple[str, ...]] = (
    "#0072b2",  # blue
    "#e69f00",  # orange
    "#009e73",  # bluish green
    "#cc79a7",  # reddish purple
    "#56b4e9",  # sky blue
    "#d55e00",  # vermillion
    "#f0e442",  # yellow
)
"""Okabe-Ito palette (without black), ordered blue and orange first.

The 3rd (red) and 5th (green) colour of the default cycle are nearly
indistinguishable with deuteranopia. Use this palette when a chart has more
than four categories, e.g. ``ax.set_prop_cycle(color=OKABE_ITO)``.
"""

SANS_SERIF: Final[tuple[str, ...]] = (
    "Helvetica",
    "Arial",
    "Liberation Sans",
    "DejaVu Sans",
)
"""Fonts closest to the ``sans-serif`` font that Vega uses in browsers."""

HOOK: Final = "camminady_matplotlib_theme.layout:install"
"""Figure hook that places axis titles and legends like the Altair theme."""

# Space around a plot area of `width` x `height` for tick labels and axis
# titles, so that a chart without a legend gets about that plot area.
MARGIN_WIDTH: Final = 48
MARGIN_HEIGHT: Final = 68


@dataclass
class Config:
    """Design tokens from which a style is built.

    Attributes
    ----------
    color_primary
        Titles, axis titles, legends and text.
    color_secondary
        Tick labels, ticks and axis lines.
    color_background
        Background of the figure and the axes.
    color_grid
        Dashed grid lines.
    color_rule
        Lines without a colour of their own, such as ``ax.axhline`` and
        boxplot whiskers.
    font_weight
        Weight of all text.
    size_small
        Font size of tick labels, legend labels and text in points.
    size_medium
        Font size of axis titles and legend titles in points.
    size_large
        Font size of titles in points.
    height
        Approximate height of the plot area of a single chart in points.
    width
        Approximate width of the plot area of a single chart in points.
    """

    color_primary: str = "dimgray"
    # "gray" (#808080) has a contrast of 3.9:1 on white, below the 4.5:1 that
    # WCAG AA requires for small text such as tick labels; #767676 passes.
    color_secondary: str = "#767676"
    color_background: str = "white"
    color_grid: str = "#dddddd"
    color_rule: str = "dimgray"
    font_weight: FontWeight = "normal"
    size_small: float = 12
    size_medium: float = 14
    size_large: float = 20
    height: float = 400
    width: float = 800


config = Config()
"""Tokens of the ``"camminady"`` style."""

config_dark = Config(
    color_primary="#a9a9a9",
    color_secondary="#8c8c8c",
    color_background="#1e1e1e",
    color_grid="#3a3a3a",
    color_rule="#a9a9a9",
)
"""Tokens of the ``"camminady_dark"`` style."""


def rc_params(c: Config) -> dict[str, Any]:
    """Return the matplotlib rcParams of a style built from ``c``.

    Parameters
    ----------
    c
        Colours, font sizes and dimensions of the style.

    Returns
    -------
    dict[str, Any]
        rcParams that can be passed to ``plt.style.use`` or
        ``plt.style.context``.
    """
    ticks = {
        "color": c.color_secondary,
        "labelcolor": c.color_secondary,
        "labelsize": c.size_small,
        "direction": "out",
        "major.size": 5,
        "major.width": 1,
        "major.pad": 2,
        "minor.visible": False,
    }
    return {
        # One point is one pixel on screen, as in Vega; save at twice that.
        "figure.dpi": 72,
        "savefig.dpi": 144,
        "figure.figsize": (
            (c.width + MARGIN_WIDTH) / 72,
            (c.height + MARGIN_HEIGHT) / 72,
        ),
        "figure.facecolor": c.color_background,
        "figure.edgecolor": c.color_background,
        "figure.titlesize": c.size_large,
        "figure.titleweight": c.font_weight,
        "figure.labelsize": c.size_medium,
        "figure.labelweight": c.font_weight,
        "figure.constrained_layout.use": True,
        "figure.hooks": [HOOK],
        "font.family": "sans-serif",
        "font.sans-serif": list(SANS_SERIF),
        "font.size": c.size_small,
        "font.weight": c.font_weight,
        "text.color": c.color_primary,
        "axes.facecolor": c.color_background,
        "axes.edgecolor": c.color_secondary,
        "axes.linewidth": 1,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "both",
        "axes.axisbelow": True,
        "axes.labelcolor": c.color_primary,
        "axes.labelsize": c.size_medium,
        "axes.labelweight": c.font_weight,
        "axes.labelpad": 4,
        "axes.titlecolor": c.color_primary,
        "axes.titlesize": c.size_large,
        "axes.titleweight": c.font_weight,
        "axes.titlepad": 8,
        "axes.prop_cycle": _color_cycle(),
        # Like Vega's "nice" scales: axes end at a tick, without padding.
        "axes.autolimit_mode": "round_numbers",
        "axes.xmargin": 0,
        "axes.ymargin": 0,
        # The y title is moved above the axis by the figure hook; without
        # the hook it stays rotated at the top of the axis.
        "xaxis.labellocation": "right",
        "yaxis.labellocation": "top",
        "grid.color": c.color_grid,
        "grid.linewidth": 1,
        # Vega draws 2-on-4-off dashes with round caps, which look like
        # 3-on-3-off dashes with the butt caps matplotlib uses.
        "grid.linestyle": (0, (3, 3)),
        "grid.alpha": 1,
        **{f"xtick.{key}": value for key, value in ticks.items()},
        **{f"ytick.{key}": value for key, value in ticks.items()},
        "lines.linewidth": 2,
        "lines.color": c.color_rule,
        "lines.solid_capstyle": "round",
        # The area of a Vega point is 30 square pixels.
        "lines.markersize": 5.5,
        "patch.facecolor": TABLEAU10[0],
        # Separate adjacent bars, such as histogram bins, like Vega's
        # one-pixel bin spacing.
        "patch.force_edgecolor": True,
        "patch.edgecolor": c.color_background,
        "patch.linewidth": 1,
        "legend.frameon": False,
        "legend.fontsize": c.size_small,
        "legend.title_fontsize": c.size_medium,
        "legend.labelcolor": c.color_primary,
        "legend.borderpad": 0,
        "legend.labelspacing": 0.25,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.5,
        "boxplot.patchartist": True,
        "boxplot.showcaps": False,
        "boxplot.boxprops.color": TABLEAU10[0],
        "boxplot.whiskerprops.color": c.color_rule,
        "boxplot.whiskerprops.linewidth": 1,
        "boxplot.medianprops.color": "white",
        "boxplot.medianprops.linewidth": 1,
        "boxplot.flierprops.marker": "o",
        "boxplot.flierprops.markerfacecolor": "none",
        "boxplot.flierprops.markeredgecolor": TABLEAU10[0],
        "errorbar.capsize": 0,
    }


def _color_cycle() -> Cycler:
    return cycler(color=list(TABLEAU10))


def to_mplstyle(rc: Mapping[str, Any]) -> str:
    """Format rcParams as the contents of a ``.mplstyle`` file.

    Parameters
    ----------
    rc
        rcParams as returned by `rc_params`.

    Returns
    -------
    str
        One ``key: value`` line per parameter.
    """
    return "".join(f"{key}: {_format(value)}\n" for key, value in rc.items())


def _format(value: object) -> str:
    match value:
        case bool() | int() | float():
            return str(value)
        case str() if value.startswith("#"):
            # "#" starts a comment in style files.
            return value[1:]
        case str():
            return value
        case Cycler():
            colors = ", ".join(
                repr(_format(color)) for color in value.by_key()["color"]
            )
            return f"cycler('color', [{colors}])"
        case (int(), tuple()):
            return str(value)
        case tuple() | list():
            return ", ".join(_format(item) for item in value)
        case _:
            raise TypeError(f"cannot write {value!r} to a style file")
