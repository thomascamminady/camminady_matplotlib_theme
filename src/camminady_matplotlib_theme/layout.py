"""Place axis titles, legends and ticks like the camminady Altair theme.

matplotlib has no rcParams for a horizontal y-axis title above the axis, for
a legend outside the plot or for Vega's tick density, so the styles register
`install` as a figure hook. It gives each figure created with ``plt.figure``
or ``plt.subplots`` a constrained layout engine that, before every layout
pass:

- turns the y-axis title horizontal and moves it above the axis, aligned
  with the axis line (a right y axis gets a right-aligned title),
- lifts the title of the axes above that y-axis title,
- moves a legend whose location was not chosen outside the plot, to the
  right of it, with a left-aligned title,
- replaces the default tick locator of linear axes with one that places
  ticks and rounds the axis limits like Vega (see `ticks`),
- removes grid lines across categorical axes (string data, or ticks with
  fixed labels such as those of a boxplot), which Vega does not draw for
  band scales, and across images.

Figures created with another layout engine (``layout="tight"`` or
``layout="none"``) are left alone. For figures not created through pyplot,
call ``install(fig)`` yourself.
"""

import math
from typing import Final

import matplotlib as mpl
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.backend_bases import RendererBase
from matplotlib.category import StrCategoryConverter
from matplotlib.figure import Figure
from matplotlib.layout_engine import ConstrainedLayoutEngine
from matplotlib.text import Text
from matplotlib.ticker import AutoLocator, FixedFormatter
from matplotlib.transforms import Bbox, ScaledTranslation

from camminady_matplotlib_theme.ticks import PIXELS_PER_TICK, VegaLocator

Y_TITLE_OFFSET: Final = 15.0
"""Distance between the top of the plot and the baseline of the y title."""

LEGEND_OFFSET: Final = 18.0
"""Distance between the plot and a legend outside of it (Vega's default)."""


class ThemeLayoutEngine(ConstrainedLayoutEngine):
    """Constrained layout that first arranges titles, legends and ticks."""

    def execute(self, fig: Figure) -> dict:  # ty: ignore[invalid-method-override]
        """Arrange all axes of ``fig``, then run the constrained layout."""
        for ax in fig.axes:
            arrange(ax)
        result = super().execute(fig)
        # The tick count depends on the axis length, which the layout has
        # just changed; lay out again with the new tick labels if needed.
        # A list, not a generator: update every axes, do not short-circuit.
        if any([_update_tick_count(ax) for ax in fig.axes]):  # noqa: C419
            result = super().execute(fig)
        return result


def install(fig: Figure) -> None:
    """Use the theme's layout for ``fig`` if it has a constrained layout.

    Parameters
    ----------
    fig
        A figure, typically one just created by ``plt.figure``.
    """
    engine = fig.get_layout_engine()
    if type(engine) is not ConstrainedLayoutEngine:
        return
    fig.set_layout_engine(
        ThemeLayoutEngine(
            # `compress` is not part of the engine's public parameters.
            compress=getattr(engine, "_compress", False),
            **engine.get(),
        )
    )


def arrange(ax: Axes) -> None:
    """Place the axis titles, title, legend and ticks of ``ax``.

    Parameters
    ----------
    ax
        Axes to arrange. Only rectilinear axes are changed.
    """
    fig = ax.get_figure(root=True)
    if ax.name != "rectilinear" or fig is None:
        return
    twins = _twins(ax)
    _place_y_title(ax, fig)
    _place_title(ax, fig, twins)
    _place_legend(ax, fig, twins)
    for axis in (ax.xaxis, ax.yaxis):
        if ax.images or _is_categorical(axis):
            axis.grid(False)
        # Colorbars keep their own ticks, like Vega's gradient legends.
        if ax.get_label() == "<colorbar>":
            continue
        if type(axis.get_major_locator()) is AutoLocator:
            axis.set_major_locator(VegaLocator())
            # Still the default, so that e.g. categorical data replaces it.
            axis.isDefault_majloc = True
            # Round the limits with the new locator; this does nothing if
            # the limits were set explicitly.
            ax.autoscale_view(scalex=axis is ax.xaxis, scaley=axis is ax.yaxis)
    _update_tick_count(ax)


def _is_categorical(axis: Axis) -> bool:
    return isinstance(axis.get_converter(), StrCategoryConverter) or isinstance(
        axis.get_major_formatter(), FixedFormatter
    )


def _update_tick_count(ax: Axes) -> bool:
    """Set the tick count from the axis length; return whether it changed."""
    fig = ax.get_figure(root=True)
    if ax.name != "rectilinear" or fig is None:
        return False
    changed = False
    position = ax.get_position()
    width, height = fig.get_size_inches() * 72
    for axis, length in (
        (ax.xaxis, position.width * width),
        (ax.yaxis, position.height * height),
    ):
        locator = axis.get_major_locator()
        if isinstance(locator, VegaLocator):
            count = math.ceil(length / PIXELS_PER_TICK)
            changed |= locator.count != count
            locator.count = count
    return changed


def _twins(ax: Axes) -> list[Axes]:
    """Axes that share the plot area of ``ax``, including ``ax`` itself."""
    fig = ax.get_figure(root=False)
    if fig is None:
        return [ax]
    bounds = ax.get_position().bounds
    return [a for a in fig.axes if a.get_position().bounds == bounds]


def _offset(fig: Figure, dx: float = 0, dy: float = 0) -> ScaledTranslation:
    """Translation by ``dx`` and ``dy`` points."""
    return ScaledTranslation(dx / 72, dy / 72, fig.dpi_scale_trans)


class _TitleExtent(Artist):
    """Invisible artist that makes the layout reserve room for a y title.

    Constrained layout only counts one pixel of the height of a y-axis
    title (it expects a rotated title), so a horizontal title above the
    axis would be cut off at the top of the figure.
    """

    def __init__(self, axis: Axis) -> None:
        super().__init__()
        self._title: Text = axis.label
        self.set_label("_camminady_y_title_extent")

    def get_window_extent(self, renderer: RendererBase | None = None) -> Bbox:
        if not (self._title.get_visible() and self._title.get_text()):
            return Bbox.null()
        return self._title.get_window_extent(renderer)

    def get_tightbbox(self, renderer: RendererBase | None = None) -> Bbox:
        return self.get_window_extent(renderer)

    def draw(self, renderer: RendererBase) -> None:
        pass


def _place_y_title(ax: Axes, fig: Figure) -> None:
    label = ax.yaxis.label
    # Leave titles alone that the user rotated to some other angle.
    if label.get_rotation() not in (0, 90):
        return
    right = ax.yaxis.get_label_position() == "right"
    ax.yaxis.set_label_coords(
        1 if right else 0,
        1,
        transform=ax.transAxes + _offset(fig, dy=Y_TITLE_OFFSET),
    )
    label.set(
        rotation=0,
        horizontalalignment="right" if right else "left",
        verticalalignment="baseline",
    )
    if not any(isinstance(a, _TitleExtent) for a in ax.artists):
        extent = ax.add_artist(_TitleExtent(ax.yaxis))
        # `add_artist` clips to the axes, which hides it from the layout.
        extent.set_clip_on(False)
    if ax.yaxis.get_ticks_position() == "right":
        # A secondary y axis (`ax.twinx()`) gets the axis line that the
        # style hides on the right.
        ax.spines.right.set_visible(True)
        ax.spines.left.set_visible(False)


def _has_y_title(ax: Axes) -> bool:
    label = ax.yaxis.label
    return bool(label.get_visible() and label.get_text())


def _place_title(ax: Axes, fig: Figure, twins: list[Axes]) -> None:
    pad = mpl.rcParams["axes.titlepad"]
    titled = [a for a in twins if _has_y_title(a)]
    if titled:
        size = max(
            a.yaxis.label.get_fontproperties().get_size_in_points()
            for a in titled
        )
        pad += Y_TITLE_OFFSET + size
    ax.title.set_transform(ax.transAxes + _offset(fig, dy=pad))


def _place_legend(ax: Axes, fig: Figure, twins: list[Axes]) -> None:
    legend = ax.get_legend()
    # `_loc_used_default` is True only while the location is the default
    # one, i.e. neither passed to `legend()` nor set since; the legend is
    # moved once.
    if legend is None or not getattr(legend, "_loc_used_default", False):
        return
    if legend.get_bbox_to_anchor() is not ax.bbox:
        return
    # A secondary y axis would need the legend further right.
    if any(a.yaxis.get_ticks_position() == "right" for a in twins):
        return
    legend.set_loc("upper left")
    legend.set_bbox_to_anchor(
        (1, 1), transform=ax.transAxes + _offset(fig, dx=LEGEND_OFFSET)
    )
    legend.borderaxespad = 0
    legend.set_alignment("left")
