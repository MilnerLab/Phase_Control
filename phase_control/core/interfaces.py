# phase_control/core/plotting/interfaces.py
from __future__ import annotations

from typing import Protocol


class SpectrumPlotProtocol(Protocol):
    """
    Minimal interface for the shared spectrum plot widget.
    """

    def clear(self) -> None:
        """Remove all data and redraw an empty plot."""
        ...

    def set_base_spectrum(self, x: list[float], y: list[float]) -> None:
        """
        Set the 'raw' spectrum that all modules build on.
        Typically wavelength on x and counts on y.
        """
        ...

    def set_layer(
        self,
        name: str,
        x: list[float] | None,
        y: list[float] | None,
    ) -> None:
        """
        Add or update an overlay layer (e.g. fit, envelope, zero-phase).

        Passing x/y = None may be interpreted as 'hide this layer' in the
        concrete implementation.
        """
        ...
