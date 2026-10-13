"""Tests for the camminady matplotlib styles.

Charts are drawn with the Agg backend and checked through the window extents
of their artists, in pixels with the origin at the bottom left. The styles
set ``figure.dpi`` to 72, so one pixel is one point.
"""

import dataclasses
import re
import subprocess
import sys
import warnings
from collections.abc import Iterator
from importlib.resources import files
from pathlib import Path
from typing import Any, Final

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import vl_convert as vlc
from camminady_altair_theme import theme as altair_theme
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.transforms import Bbox

import camminady_matplotlib_theme
from camminady_matplotlib_theme import (
    OKABE_ITO,
    TABLEAU10,
    Config,
    install,
    rc_params,
    to_mplstyle,
)
from camminady_matplotlib_theme import theme as theme_module
from camminady_matplotlib_theme.layout import (
    LEGEND_OFFSET,
    Y_TITLE_OFFSET,
    ThemeLayoutEngine,
)
from camminady_matplotlib_theme.ticks import VegaLocator, nice, ticks

STYLES: Final = {
    "camminady": theme_module.config,
    "camminady_dark": theme_module.config_dark,
}
CSS_COLORS: Final = {
    "black": "#000000",
    "dimgray": "#696969",
    "lightgray": "#d3d3d3",
    "white": "#ffffff",
}


@pytest.fixture(autouse=True, params=STYLES)
def style(request: pytest.FixtureRequest) -> Iterator[str]:
    """Run each test with both styles and close all figures afterwards."""
    with plt.style.context(f"camminady_matplotlib_theme.{request.param}"):
        yield request.param
    plt.close("all")


def draw(fig: Figure) -> None:
    fig.canvas.draw()


def extent(artist: Any) -> Bbox:
    return artist.get_window_extent(
        artist.get_figure(root=True).canvas.get_renderer()
    )


def line_chart() -> tuple[Figure, Axes]:
    fig, ax = plt.subplots()
    x = np.linspace(0, 10, 50)
    for i in range(3):
        ax.plot(x, np.sin(x + i) * 40 + 50, label=f"series {i}")
    ax.set(xlabel="time (s)", ylabel="Average power per kilogram (W/kg)")
    return fig, ax


def vega_scene(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the scenegraph of a Vega-Lite spec into a list of items."""
    items: list[dict[str, Any]] = []

    def walk(mark: dict[str, Any]) -> None:
        for item in mark.get("items", []):
            items.append({**item, "role": mark.get("role")})
            if mark.get("marktype") == "group":
                for child in item.get("items", []):
                    walk(child)

    walk(vlc.vegalite_to_scenegraph(spec)["scenegraph"])
    return items


def run_python(code: str, cwd: Path | None = None) -> str:
    """Run ``code`` in a fresh interpreter and return its stdout."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", code],
        check=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


# Styles and registration ----------------------------------------------------


@pytest.mark.parametrize("name", STYLES)
def test_style_files_match_the_tokens(name: str) -> None:
    path = files("camminady_matplotlib_theme") / f"{name}.mplstyle"
    assert path.read_text() == to_mplstyle(rc_params(STYLES[name]))


@pytest.mark.parametrize("name", STYLES)
def test_style_files_are_valid(name: str) -> None:
    path = files("camminady_matplotlib_theme") / f"{name}.mplstyle"
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        loaded = mpl.rc_params_from_file(str(path), use_default_template=False)
    assert not record, [str(w.message) for w in record]
    expected = mpl.RcParams(rc_params(STYLES[name]))
    assert dict(loaded) == dict(expected)


def test_import_registers_styles_without_applying_them() -> None:
    code = (
        "import matplotlib as mpl, matplotlib.style\n"
        "before = dict(mpl.rcParams)\n"
        "import camminady_matplotlib_theme\n"
        "print(dict(mpl.rcParams) == before,"
        " {'camminady', 'camminady_dark'} <= set(matplotlib.style.available))"
    )
    assert run_python(code) == "True True"


@pytest.mark.parametrize("name", STYLES)
def test_style_can_be_used_without_import(name: str) -> None:
    code = (
        "import matplotlib; matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        f"plt.style.use('camminady_matplotlib_theme.{name}')\n"
        "print(type(plt.figure().get_layout_engine()).__name__)"
    )
    assert run_python(code) == "ThemeLayoutEngine"


def test_short_names_work_after_import(style: str) -> None:
    assert camminady_matplotlib_theme.__version__
    with plt.style.context(style):
        fig = plt.figure()
    assert isinstance(fig.get_layout_engine(), ThemeLayoutEngine)


def test_context_restores_rcparams() -> None:
    plt.close("all")
    with plt.style.context("default"):
        before = mpl.rcParams.copy()
        with plt.style.context("camminady"):
            assert mpl.rcParams["figure.dpi"] == 72
        assert mpl.rcParams == before


def test_custom_config() -> None:
    with plt.style.context(rc_params(Config(width=400, size_small=9))):
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        draw(fig)
        assert fig.get_size_inches()[0] == pytest.approx((400 + 48) / 72)
        assert ax.xaxis.get_ticklabels()[0].get_fontsize() == 9


# Parity with the Altair theme ---------------------------------------------


@pytest.mark.parametrize(
    ("mine", "altairs"),
    [
        (theme_module.config, altair_theme.config),
        (theme_module.config_dark, altair_theme.config_dark),
    ],
    ids=["light", "dark"],
)
def test_tokens_match_the_altair_theme(mine: Config, altairs: Any) -> None:
    for field in dataclasses.fields(Config):
        assert getattr(mine, field.name) == getattr(altairs, field.name)


def test_palettes_match_vega() -> None:
    assert OKABE_ITO == altair_theme.OKABE_ITO
    spec = {
        "data": {"values": [{"c": f"{i:02d}"} for i in range(10)]},
        "mark": "bar",
        "encoding": {"x": {"field": "c"}, "color": {"field": "c"}},
    }
    bars = [item for item in vega_scene(spec) if item["role"] == "mark"]
    assert tuple(bar["fill"] for bar in bars) == TABLEAU10


@pytest.mark.parametrize(
    ("start", "stop", "length"),
    [
        (0, 240, 800),
        (46, 230, 800),
        (0, 7, 800),
        (-2.9, 7.3, 400),
        (0.013, 0.087, 400),
        (2000, 2010, 300),
        (5, 50, 400),
    ],
)
def test_ticks_match_vega(start: float, stop: float, length: int) -> None:
    spec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v6.json",
        "data": {"values": [{"x": start}, {"x": stop}]},
        "mark": "point",
        "width": length,
        "encoding": {
            "x": {
                "field": "x",
                "type": "quantitative",
                "scale": {
                    "domain": [start, stop],
                    "nice": False,
                    "zero": False,
                },
                "axis": {"format": ".6~f"},
            }
        },
    }
    labels = [i["text"] for i in vega_scene(spec) if i["role"] == "axis-label"]
    vega = [float(label.replace("\u2212", "-")) for label in labels]
    count = np.ceil(length / 40)
    assert ticks(start, stop, count) == pytest.approx(vega)


@pytest.mark.parametrize(
    ("start", "stop", "expected"),
    [(46, 230, (40, 240)), (-2.9, 7.3, (-3, 8)), (0.013, 0.087, (0.01, 0.09))],
)
def test_nice_rounds_like_d3(
    start: float, stop: float, expected: tuple[float, float]
) -> None:
    assert nice(start, stop) == pytest.approx(expected)


# Accessibility ------------------------------------------------------------


def luminance(color: str) -> float:
    """WCAG relative luminance of a hex or (supported) named colour."""
    hex_color = CSS_COLORS.get(color, color)
    assert re.fullmatch(r"#[0-9a-fA-F]{6}", hex_color), color
    channels = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        for c in channels
    )
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(foreground: str, background: str) -> float:
    high, low = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (high + 0.05) / (low + 0.05)


@pytest.mark.parametrize("config", STYLES.values(), ids=STYLES)
def test_text_meets_wcag_aa_contrast(config: Config) -> None:
    background = config.color_background
    assert contrast(config.color_primary, background) >= 4.5
    assert contrast(config.color_secondary, background) >= 4.5
    assert contrast(config.color_rule, background) >= 3


# Layout -------------------------------------------------------------------


def test_figure_size_gives_about_the_configured_plot_area(style: str) -> None:
    fig, ax = plt.subplots()
    ax.bar(["a", "b", "c"], [3, 1, 2])
    ax.set(xlabel="group", ylabel="count")
    draw(fig)
    box = extent(ax)
    config = STYLES[style]
    assert box.width == pytest.approx(config.width, rel=0.05)
    assert box.height == pytest.approx(config.height, rel=0.05)


def test_y_title_is_horizontal_above_the_axis() -> None:
    fig, ax = line_chart()
    draw(fig)
    label, box = ax.yaxis.label, extent(ax)
    assert label.get_rotation() == 0
    assert label.get_horizontalalignment() == "left"
    title = extent(label)
    assert title.x0 == pytest.approx(box.x0, abs=1)
    assert title.y0 > box.y1
    # The y title is not cut off at the top of the figure.
    assert title.y1 <= fig.bbox.y1


def test_x_title_is_right_aligned_at_the_end_of_the_axis() -> None:
    fig, ax = line_chart()
    draw(fig)
    title, box = extent(ax.xaxis.label), extent(ax)
    assert title.x1 == pytest.approx(box.x1, abs=1)
    assert title.y1 < box.y0


def test_title_sits_above_the_y_title() -> None:
    fig, ax = line_chart()
    ax.set_title("A title")
    draw(fig)
    assert extent(ax.title).y0 > extent(ax.yaxis.label).y1
    assert extent(ax.title).y1 <= fig.bbox.y1


def test_title_stays_close_without_a_y_title() -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_title("A title")
    draw(fig)
    gap = extent(ax.title).y0 - extent(ax).y1
    assert gap < Y_TITLE_OFFSET


def test_legend_is_placed_outside_on_the_right() -> None:
    fig, ax = line_chart()
    ax.legend(title="series")
    draw(fig)
    legend, box = extent(ax.get_legend()), extent(ax)
    assert legend.x0 == pytest.approx(box.x1 + LEGEND_OFFSET, abs=2)
    assert legend.y1 == pytest.approx(box.y1, abs=2)
    assert legend.x1 <= fig.bbox.x1


def test_legend_with_a_location_stays_where_it_was_put() -> None:
    fig, ax = line_chart()
    ax.legend(loc="lower right")
    draw(fig)
    legend, box = extent(ax.get_legend()), extent(ax)
    assert box.x0 < legend.x0 and legend.x1 <= box.x1 + 1
    assert legend.y0 >= box.y0 - 1


def test_legend_anchored_by_the_user_is_not_moved() -> None:
    fig, ax = line_chart()
    ax.legend(bbox_to_anchor=(0.5, 0.5))
    draw(fig)
    legend, box = extent(ax.get_legend()), extent(ax)
    assert legend.x1 < box.x1


def test_legend_is_not_moved_over_a_secondary_y_axis() -> None:
    fig, ax = line_chart()
    ax.twinx().set_ylabel("right")
    ax.legend()
    draw(fig)
    legend, box = extent(ax.get_legend()), extent(ax)
    assert legend.x1 <= box.x1 + 1


def test_secondary_y_axis() -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_ylabel("left")
    ax2 = ax.twinx()
    ax2.plot([0, 1], [5, 3], color="C1")
    ax2.set_ylabel("right")
    draw(fig)
    box = extent(ax)
    right = extent(ax2.yaxis.label)
    assert ax2.yaxis.label.get_rotation() == 0
    assert right.x1 == pytest.approx(box.x1, abs=1)
    assert right.y0 > box.y1
    assert ax2.spines.right.get_visible()
    assert extent(ax.yaxis.label).x0 == pytest.approx(box.x0, abs=1)


def test_rotated_y_title_is_left_alone() -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_ylabel("tilted", rotation=45)
    draw(fig)
    assert ax.yaxis.label.get_rotation() == 45


def test_categorical_axes_have_no_grid_lines() -> None:
    fig, (bars, boxes) = plt.subplots(1, 2)
    bars.bar(["a", "b", "c"], [3, 1, 2])
    boxes.boxplot([[1, 2, 3], [2, 3, 4]], tick_labels=["x", "y"])
    draw(fig)
    for ax in (bars, boxes):
        assert not any(line.get_visible() for line in ax.xaxis.get_gridlines())
        assert any(line.get_visible() for line in ax.yaxis.get_gridlines())


def test_images_have_no_grid_lines() -> None:
    fig, ax = plt.subplots()
    image = ax.imshow(np.arange(12).reshape(3, 4))
    fig.colorbar(image, ax=ax, label="value")
    draw(fig)
    for axis in (ax.xaxis, ax.yaxis):
        assert not any(line.get_visible() for line in axis.get_gridlines())


def test_ticks_are_placed_like_vega() -> None:
    fig, ax = plt.subplots()
    ax.plot([46, 230], [9, 46.6])
    draw(fig)
    locator = ax.xaxis.get_major_locator()
    assert isinstance(locator, VegaLocator)
    assert locator.count == np.ceil(extent(ax).width / 40)
    # Limits are rounded like a Vega scale with `nice: true` and end at ticks.
    assert ax.get_xlim() == (40, 240)
    assert ax.get_ylim() == (5, 50)
    assert list(ax.get_yticks()) == list(range(5, 51, 5))


def test_explicit_limits_and_locators_are_kept() -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xlim(0.13, 0.87)
    ax.yaxis.set_major_locator(MaxNLocator(3))
    draw(fig)
    assert ax.get_xlim() == (0.13, 0.87)
    assert isinstance(ax.yaxis.get_major_locator(), MaxNLocator)


@pytest.mark.parametrize("layout", ["tight", "none"])
def test_other_layout_engines_are_respected(layout: str) -> None:
    fig = plt.figure(layout=layout)
    assert not isinstance(fig.get_layout_engine(), ThemeLayoutEngine)


def test_compressed_layout_is_kept() -> None:
    fig = plt.figure(layout="compressed")
    engine = fig.get_layout_engine()
    assert isinstance(engine, ThemeLayoutEngine)
    assert getattr(engine, "_compress", False)


def test_install_works_for_figures_created_without_pyplot() -> None:
    fig = Figure(layout="constrained")
    install(fig)
    assert isinstance(fig.get_layout_engine(), ThemeLayoutEngine)


def test_polar_axes_are_left_alone() -> None:
    fig = plt.figure()
    ax = fig.add_subplot(projection="polar")
    ax.plot([0, 1], [1, 2])
    ax.set_title("polar")
    draw(fig)


@pytest.mark.parametrize("fmt", ["png", "svg", "pdf"])
def test_savefig(fmt: str, tmp_path: Any) -> None:
    fig, ax = line_chart()
    ax.legend()
    path = tmp_path / f"chart.{fmt}"
    with plt.rc_context({"svg.fonttype": "none"}):
        fig.savefig(path)
    assert path.stat().st_size > 0
    if fmt == "svg":
        # The artist that reserves room for the y title draws nothing.
        assert path.read_text().count("Average power per kilogram") == 1


def test_readme_example_runs(tmp_path: Path) -> None:
    readme = (Path(__file__).parents[1] / "README.md").read_text()
    section = readme.split("## Example\n", 1)[1]
    code = re.search(r"```python\n(.*?)```", section, re.DOTALL)
    assert code is not None
    run_python(code.group(1), cwd=tmp_path)
    assert (tmp_path / "stock_prices.png").stat().st_size > 0
