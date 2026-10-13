# camminady_matplotlib_theme

A minimal [matplotlib](https://matplotlib.org) style that matches
[camminady_altair_theme](https://github.com/thomascamminady/camminady_altair_theme):
muted gray text, dashed grid lines, no frame around the plot, and horizontal
axis titles at the end of each axis. It comes in a light (`camminady`) and a
dark (`camminady_dark`) variant.

![Light style](https://raw.githubusercontent.com/thomascamminady/camminady_matplotlib_theme/main/assets/camminady.png)

<!-- docs-start -->

## Installation

```bash
uv add camminady-matplotlib-theme
# or
pip install camminady-matplotlib-theme
```

Requires Python 3.11+ and matplotlib 3.10+.

## Usage

```python
import matplotlib.pyplot as plt

plt.style.use("camminady_matplotlib_theme.camminady")  # or ".camminady_dark"
```

There is no need to import the package. After
`import camminady_matplotlib_theme`, the short names `"camminady"` and
`"camminady_dark"` work as well; importing does not apply a style.

To use the style for some figures only:

```python
with plt.style.context("camminady_matplotlib_theme.camminady"):
    fig, ax = plt.subplots()
    ...
    fig.savefig("chart.png")
```

### Matching the Altair theme

The style uses the design tokens of the Altair theme (colours, font sizes and
the 800 × 400 plot area) and Vega's default colour palette. It sets
`figure.dpi` to 72 so that one point is one pixel on screen, as in Vega;
`savefig` writes at 144 dpi.

Some of the look cannot be expressed in a style file. The style therefore
registers a figure hook that gives each figure created through pyplot a
constrained layout which, before drawing:

- turns the y-axis title horizontal and places it above the axis, aligned
  with the axis line (titles of `ax.twinx()` go to the right end),
- moves the axes title above that y-axis title,
- places a legend outside the plot on the right, unless you pass a location
  (`ax.legend(loc="lower right")` stays where you put it),
- places ticks and rounds axis limits like Vega: about one tick per 40
  points, at multiples of 1, 2 or 5 times a power of ten,
- removes grid lines across categorical axes and images.

The hook leaves figures alone that use another layout
(`plt.subplots(layout="tight")`). For a figure created without pyplot, call
`camminady_matplotlib_theme.install(fig)`.

Two differences remain: Vega-Lite includes zero in quantitative axes and
draws points as hollow circles; matplotlib does neither by default.

### Customising

All colours, font sizes and the plot size are fields of `Config`, with the
same names and defaults as in the Altair theme:

```python
import matplotlib.pyplot as plt
from camminady_matplotlib_theme import Config, rc_params

plt.style.use(rc_params(Config(width=400, height=250)))
```

`to_mplstyle(rc_params(...))` returns the contents of a `.mplstyle` file.

### Colour-blind safety

The default palette is Vega's `tableau10`. Its third (red) and fifth (green)
colours are nearly indistinguishable for people with deuteranopia, so for five
or more categories use the bundled Okabe-Ito palette:

```python
from camminady_matplotlib_theme import OKABE_ITO

ax.set_prop_cycle(color=OKABE_ITO)
```

## Examples

The same chart made with Altair and with matplotlib:

![Altair and matplotlib](https://raw.githubusercontent.com/thomascamminady/camminady_matplotlib_theme/main/assets/comparison.png)

The dark variant:

![Dark style](https://raw.githubusercontent.com/thomascamminady/camminady_matplotlib_theme/main/assets/camminady_dark.png)

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check
uv run python create_charts.py  # regenerate the images above
```

The `.mplstyle` files are generated from `Config`; after changing a token,
rewrite them with:

```bash
uv run python -c "
from importlib.resources import files
from camminady_matplotlib_theme import theme
for name, c in {'camminady': theme.config, 'camminady_dark': theme.config_dark}.items():
    (files('camminady_matplotlib_theme') / f'{name}.mplstyle').write_text(
        theme.to_mplstyle(theme.rc_params(c)))
"
```
