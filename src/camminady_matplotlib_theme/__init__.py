"""Minimal matplotlib styles: ``"camminady"`` and ``"camminady_dark"``.

They match the Altair theme of ``camminady_altair_theme``. Use a style
without importing this package::

    import matplotlib.pyplot as plt

    plt.style.use("camminady_matplotlib_theme.camminady")

Importing the package also registers the short names ``"camminady"`` and
``"camminady_dark"`` with matplotlib, without applying a style.

.. include:: ../../README.md
   :start-after: <!-- docs-start -->
"""

from importlib.metadata import version

import matplotlib
import matplotlib.style

from camminady_matplotlib_theme.layout import install
from camminady_matplotlib_theme.theme import (
    OKABE_ITO,
    TABLEAU10,
    Config,
    config,
    config_dark,
    rc_params,
    to_mplstyle,
)

__all__ = [
    "OKABE_ITO",
    "TABLEAU10",
    "Config",
    "install",
    "rc_params",
    "to_mplstyle",
]
__version__ = version("camminady-matplotlib-theme")

matplotlib.style.library["camminady"] = matplotlib.RcParams(rc_params(config))
matplotlib.style.library["camminady_dark"] = matplotlib.RcParams(
    rc_params(config_dark)
)
matplotlib.style.available[:] = sorted(matplotlib.style.library)
