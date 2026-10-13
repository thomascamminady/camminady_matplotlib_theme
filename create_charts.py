"""Render the example charts shown in the README."""

from pathlib import Path

import altair as alt
import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
import vl_convert as vlc
from matplotlib.axes import Axes
from vega_datasets import data

ASSETS = Path(__file__).parent / "assets"
SCALE = 2
TITLE = "Stock prices"


def draw_stocks(ax: Axes, stocks: pd.DataFrame) -> None:
    for symbol, group in stocks.groupby("symbol"):
        ax.plot(group["date"], group["price"], label=symbol)
    ax.set(title=TITLE, xlabel="date", ylabel="Price (USD)")
    ax.legend(title="symbol")


def matplotlib_chart(style: str, stocks: pd.DataFrame, path: Path) -> None:
    with plt.style.context(f"camminady_matplotlib_theme.{style}"):
        fig, ax = plt.subplots()
        draw_stocks(ax, stocks)
        fig.savefig(path, dpi=72 * SCALE)
        plt.close(fig)


def altair_chart(stocks: pd.DataFrame, path: Path) -> None:
    chart = (
        alt.Chart(stocks, mark="line")
        .encode(
            x="date:T",
            y=alt.Y("price:Q", title="Price (USD)"),
            color="symbol:N",
        )
        .properties(title=TITLE)
    )
    with alt.theme.enable("camminady"):  # ty: ignore[invalid-context-manager]
        spec = chart.to_dict()
    path.write_bytes(vlc.vegalite_to_png(spec, scale=SCALE))


def side_by_side(top: Path, bottom: Path, path: Path) -> None:
    """Stack two images with a label above each."""
    images = [mpimg.imread(top)[..., :3], mpimg.imread(bottom)[..., :3]]
    label_height, gap = 40 * SCALE, 30 * SCALE
    width = max(image.shape[1] for image in images)
    height = sum(image.shape[0] for image in images) + 2 * label_height + gap
    dpi = 72 * SCALE
    with plt.style.context("camminady_matplotlib_theme.camminady"):
        fig = plt.figure(
            figsize=(width / dpi, height / dpi), dpi=dpi, layout="none"
        )
        y = height
        for image, label in zip(images, ["Altair", "matplotlib"], strict=True):
            y -= label_height
            fig.text(0.01, y / height, label, fontsize=16, va="bottom")
            y -= image.shape[0]
            fig.figimage(image, xo=0, yo=y)
            y -= gap
        fig.savefig(path, dpi=dpi)
        plt.close(fig)


def main() -> None:
    stocks = data.stocks()
    for style in ("camminady", "camminady_dark"):
        matplotlib_chart(style, stocks, ASSETS / f"{style}.png")
    altair = ASSETS / "altair.png"
    altair_chart(stocks, altair)
    side_by_side(altair, ASSETS / "camminady.png", ASSETS / "comparison.png")
    altair.unlink()


if __name__ == "__main__":
    main()
