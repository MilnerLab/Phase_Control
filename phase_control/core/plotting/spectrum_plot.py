from __future__ import annotations

from typing import Dict, Optional

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from phase_control.core.interfaces import SpectrumPlotProtocol


class SpectrumPlotPanel(ttk.Frame, SpectrumPlotProtocol):
    """
    Reusable spectrum plot widget embedded in a Tkinter frame.

    Features:
    - one "base" spectrum line (raw spectrometer data)
    - arbitrary named overlay layers (e.g. fit, envelope, zero-phase)
    - simple legend that updates when layers are added/removed

    API (implements SpectrumPlotProtocol):
      - clear()
      - set_base_spectrum(x, y)
      - set_layer(name, x, y)
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        show_legend: bool = True,
        xlabel: str = "Wavelength",
        ylabel: str = "Counts",
        title: str = "Spectrum",
    ) -> None:
        super().__init__(parent)

        self._show_legend = show_legend

        # Matplotlib figure/axis
        self._figure = Figure(figsize=(6, 4), dpi=100)
        self._ax = self._figure.add_subplot(111)
        self._ax.set_xlabel(xlabel)
        self._ax.set_ylabel(ylabel)
        self._ax.set_title(title)

        # Canvas embedded in Tkinter
        self._canvas = FigureCanvasTkAgg(self._figure, master=self)
        canvas_widget = self._canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)

        # Lines
        self._base_line = None  # type: Optional["matplotlib.lines.Line2D"]
        self._layers: Dict[str, "matplotlib.lines.Line2D"] = {}

        # Some sensible initial layout
        self._ax.grid(True)

    # ------------------------------------------------------------------ #
    # Protocol implementation
    # ------------------------------------------------------------------ #

    def clear(self) -> None:
        """Remove all data and redraw an empty plot."""
        self._ax.cla()  # clear axis
        self._layers.clear()
        self._base_line = None

        # Re-apply basic labels/grid (they are cleared by cla())
        self._ax.set_xlabel(self._ax.get_xlabel() or "Wavelength")
        self._ax.set_ylabel(self._ax.get_ylabel() or "Counts")
        self._ax.set_title(self._ax.get_title() or "Spectrum")
        self._ax.grid(True)

        self._update_legend()
        self._canvas.draw_idle()

    def set_base_spectrum(self, x: list[float], y: list[float]) -> None:
        """
        Set or update the raw/base spectrum.
        """
        if self._base_line is None:
            # Create base line
            (self._base_line,) = self._ax.plot(
                x,
                y,
                label="spectrum",
                linewidth=1.5,
            )
        else:
            self._base_line.set_data(x, y)

        # Adjust axes to data
        if x and y:
            self._ax.relim()
            self._ax.autoscale_view()

        self._update_legend()
        self._canvas.draw_idle()

    def set_layer(
        self,
        name: str,
        x: list[float] | None,
        y: list[float] | None,
    ) -> None:
        """
        Add/update/remove an overlay layer.

        - If x and y are not None: create or update the line.
        - If x or y is None: remove/hide the layer (if present).
        """
        # Remove layer if no data
        if x is None or y is None:
            line = self._layers.pop(name, None)
            if line is not None:
                try:
                    line.remove()
                except ValueError:
                    # Line may already be removed from axis
                    pass
            self._update_legend()
            self._canvas.draw_idle()
            return

        # Create or update line
        if name in self._layers:
            line = self._layers[name]
            line.set_data(x, y)
        else:
            # Different styles per layer can be added here if you like
            (line,) = self._ax.plot(
                x,
                y,
                label=name,
                linewidth=1.0,
            )
            self._layers[name] = line

        # Axis scaling: include all data
        self._ax.relim()
        self._ax.autoscale_view()

        self._update_legend()
        self._canvas.draw_idle()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _update_legend(self) -> None:
        """Update or hide the legend based on existing lines."""
        if not self._show_legend:
            # Remove legend if one exists
            leg = self._ax.get_legend()
            if leg is not None:
                leg.remove()
            return

        # Collect visible artists with labels
        handles, labels = self._ax.get_legend_handles_labels()
        if handles:
            self._ax.legend(handles, labels, loc="best")
        else:
            leg = self._ax.get_legend()
            if leg is not None:
                leg.remove()
