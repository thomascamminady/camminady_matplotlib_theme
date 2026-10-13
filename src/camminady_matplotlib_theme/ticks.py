"""Tick positions and "nice" axis limits computed like Vega (d3-scale).

Vega asks for about one tick per 40 pixels of axis length and rounds the
domain of a linear scale outwards to multiples of 1, 2 or 5 times a power of
ten. matplotlib's default `AutoLocator` allows at most 9 intervals and also
uses steps of 2.5, so charts get fewer and differently spaced grid lines.
"""

import math
from collections.abc import Sequence
from typing import Final

import matplotlib as mpl
from matplotlib.ticker import Locator

PIXELS_PER_TICK: Final = 40
"""Vega's default tick count is ``ceil(length / 40)`` for an axis."""

NICE_COUNT: Final = 10
"""Vega rounds the domain (``nice: true``) with d3's default count of 10."""

_E10: Final = math.sqrt(50)
_E5: Final = math.sqrt(10)
_E2: Final = math.sqrt(2)


def _round(x: float) -> int:
    """JavaScript's ``Math.round``: halves are rounded up, not to even."""
    return math.floor(x + 0.5)


def _tick_spec(
    start: float, stop: float, count: float
) -> tuple[int, int, float]:
    """Port of ``tickSpec`` from d3-array."""
    step = (stop - start) / max(0, count)
    power = math.floor(math.log10(step))
    error = step / 10**power
    factor = (
        10 if error >= _E10 else 5 if error >= _E5 else 2 if error >= _E2 else 1
    )
    if power < 0:
        inc = 10 ** (-power) / factor
        i1, i2 = _round(start * inc), _round(stop * inc)
        if i1 / inc < start:
            i1 += 1
        if i2 / inc > stop:
            i2 -= 1
        inc = -inc
    else:
        inc = 10**power * factor
        i1, i2 = _round(start / inc), _round(stop / inc)
        if i1 * inc < start:
            i1 += 1
        if i2 * inc > stop:
            i2 -= 1
    if i2 < i1 and 0.5 <= count < 2:
        return _tick_spec(start, stop, count * 2)
    return i1, i2, inc


def ticks(start: float, stop: float, count: float) -> list[float]:
    """Port of ``ticks`` from d3-array, for ``start < stop``."""
    if not (count > 0 and start < stop):
        return [start] if start == stop else []
    i1, i2, inc = _tick_spec(start, stop, count)
    if i2 < i1:
        return []
    if inc < 0:
        return [(i1 + i) / -inc for i in range(i2 - i1 + 1)]
    return [(i1 + i) * inc for i in range(i2 - i1 + 1)]


def nice(
    start: float, stop: float, count: float = NICE_COUNT
) -> tuple[float, float]:
    """Port of ``linear.nice`` from d3-scale, for ``start < stop``."""
    previous = None
    for _ in range(10):
        _, _, step = _tick_spec(start, stop, count)
        if step == previous:
            break
        if step > 0:
            start, stop = (
                math.floor(start / step) * step,
                math.ceil(stop / step) * step,
            )
        else:
            start, stop = (
                math.ceil(start * step) / step,
                math.floor(stop * step) / step,
            )
        previous = step
    return start, stop


class VegaLocator(Locator):
    """Locate ticks like Vega does on a linear axis.

    Parameters
    ----------
    count
        Desired number of ticks; the layout sets it from the axis length.
    """

    def __init__(self, count: float = NICE_COUNT) -> None:
        self.count = count

    def __call__(self) -> Sequence[float]:
        """Return the tick locations within the view limits."""
        if self.axis is None:
            return []
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin: float, vmax: float) -> Sequence[float]:
        """Return the tick locations between ``vmin`` and ``vmax``."""
        if vmax < vmin:
            vmin, vmax = vmax, vmin
        return self.raise_if_exceeds(ticks(vmin, vmax, self.count))

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """Round the data limits outwards like a Vega scale with ``nice``."""
        vmin, vmax = self.nonsingular(vmin, vmax)
        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return vmin, vmax
        return nice(vmin, vmax)
