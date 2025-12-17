# phase_control/modules/stabilization/ui/plot_panel.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from phase_control.core.plotting.spectrum_plot import SpectrumPlotPanel
from phase_control.modules.stabilization.engine import AnalysisPlotResult


class PlotPanel:
    """
    Plotting panel for the stabilization module.

    This wraps a generic SpectrumPlotPanel and adds a few checkboxes
    to control which curves are shown (current / fit / zero-phase).

    Public API:
      - frame: ttk.Frame  (root widget to pack into a Notebook tab)
      - update_plot(result: AnalysisPlotResult) -> None
      - clear() -> None
    """

    def __init__(self, parent: ttk.Notebook) -> None:
        # public root frame
        self.frame = ttk.Frame(parent)

        # state
        self._show_current_var = tk.BooleanVar(value=True)
        self._show_fit_var = tk.BooleanVar(value=True)
        self._show_zero_var = tk.BooleanVar(value=True)
        self._last_result: AnalysisPlotResult | None = None

        self._build_ui()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frame = self.frame
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Options
        options_frame = ttk.LabelFrame(frame, text="Plot options")
        options_frame.grid(row=0, column=0, sticky="ew", **pad)
        options_frame.columnconfigure(0, weight=1)

        ttk.Checkbutton(
            options_frame,
            text="Show current spectrum",
            variable=self._show_current_var,
            command=self._redraw,
        ).grid(row=0, column=0, sticky="w", **pad)

        ttk.Checkbutton(
            options_frame,
            text="Show fitted spectrum",
            variable=self._show_fit_var,
            command=self._redraw,
        ).grid(row=1, column=0, sticky="w", **pad)

        ttk.Checkbutton(
            options_frame,
            text="Show zero-phase fit",
            variable=self._show_zero_var,
            command=self._redraw,
        ).grid(row=2, column=0, sticky="w", **pad)

        # Shared spectrum plot
        plot_frame = ttk.Frame(frame)
        plot_frame.grid(row=1, column=0, sticky="nsew")
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self._plot = SpectrumPlotPanel(
            plot_frame,
            xlabel="Wavelength [nm]",
            ylabel="Normalized intensity",
            title="Phase stabilization",
        )
        self._plot.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update_plot(self, result: AnalysisPlotResult) -> None:
        """
        Store the latest result and redraw according to the checkbox state.
        """
        self._last_result = result
        self._redraw()

    def clear(self) -> None:
        """Clear the underlying SpectrumPlotPanel and forget last result."""
        self._last_result = None
        self._plot.clear()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _redraw(self) -> None:
        """
        Apply the current checkbox settings to the stored AnalysisPlotResult
        using the SpectrumPlotPanel API.
        """
        if self._last_result is None:
            self._plot.clear()
            return

        res = self._last_result
        x = res.x.tolist()

        # base spectrum: only if "current" is checked
        if self._show_current_var.get():
            self._plot.set_base_spectrum(x, res.y_current.tolist())
        else:
            # show nothing as base, but we still want layers, so use empty
            self._plot.set_base_spectrum([], [])

        # fit layer
        if self._show_fit_var.get() and res.y_fit is not None:
            self._plot.set_layer("fit", x, res.y_fit.tolist())
        else:
            self._plot.set_layer("fit", None, None)

        # zero-phase layer
        if self._show_zero_var.get() and res.y_zero_phase is not None:
            self._plot.set_layer("zero_phase", x, res.y_zero_phase.tolist())
        else:
            self._plot.set_layer("zero_phase", None, None)
