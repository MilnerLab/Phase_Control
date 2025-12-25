# phase_control/modules/envelope/module.py
from __future__ import annotations

from typing import Optional

import tkinter as tk
from tkinter import ttk

from phase_control.modules.base import BaseModule, ModuleContext
from phase_control.core.plotting.spectrum_plot import SpectrumPlotPanel


class EnvelopeModule(BaseModule):
    """
    Dummy module for a Min/Max envelope.

    For now it:

      - lets you select "Min" or "Max" mode via radio buttons
      - shows the latest spectrum in the plot
      - overlays a very simple fake "envelope" line:
          * Min: constant line at min(intensity)
          * Max: constant line at max(intensity)

    This is just a structural placeholder for your later real envelope
    computation.
    """

    name = "Min/Max envelope"

    def __init__(self, context: ModuleContext) -> None:
        super().__init__(context)
        self._running: bool = False
        self._after_id: str | None = None

        self._mode_var: Optional[tk.StringVar] = None
        self._mode_label_var: Optional[tk.StringVar] = None
        self._plot: Optional[SpectrumPlotPanel] = None

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def build_ui(self, parent: ttk.Frame) -> None:
        """
        Build envelope options + plot.
        """
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Options
        options = ttk.LabelFrame(parent, text="Envelope options")
        options.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        options.columnconfigure(0, weight=1)

        self._mode_var = tk.StringVar(value="max")
        self._mode_label_var = tk.StringVar(value="Current mode: max")

        ttk.Radiobutton(
            options,
            text="Max envelope",
            value="max",
            variable=self._mode_var,
            command=self._on_mode_changed,
        ).grid(row=0, column=0, sticky="w", padx=4, pady=4)

        ttk.Radiobutton(
            options,
            text="Min envelope",
            value="min",
            variable=self._mode_var,
            command=self._on_mode_changed,
        ).grid(row=1, column=0, sticky="w", padx=4, pady=4)

        ttk.Label(
            options,
            textvariable=self._mode_label_var,
        ).grid(row=2, column=0, sticky="w", padx=4, pady=4)

        # Plot area
        plot_frame = ttk.Frame(parent)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self._plot = SpectrumPlotPanel(
            plot_frame,
            xlabel="Wavelength [nm]",
            ylabel="Normalized intensity",
            title="Envelope – latest spectrum",
        )
        self._plot.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        if self._running:
            return
        self._running = True
        self._schedule_next_step(0)

    def reset(self) -> None:
        if self._after_id is not None:
            try:
                self.root_frame.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self._running = False

        if self._plot is not None:
            self._plot.clear()
        if self._mode_label_var is not None and self._mode_var is not None:
            self._mode_label_var.set(f"Current mode: {self._mode_var.get()}")

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _on_mode_changed(self) -> None:
        if self._mode_var is None or self._mode_label_var is None:
            return
        self._mode_label_var.set(f"Current mode: {self._mode_var.get()}")

    def _schedule_next_step(self, delay_ms: int) -> None:
        if not self._running:
            return
        self._after_id = self.root_frame.after(delay_ms, self._step_once)

    def _step_once(self) -> None:
        if not self._running:
            return

        spectrum = self.context.buffer.get_latest()
        if spectrum is not None and self._plot is not None:
            x = spectrum.wavelengths_nm
            y = spectrum.intensity

            # base spectrum
            self._plot.set_base_spectrum(x, y)

            # simple fake envelope
            if self._mode_var is not None:
                mode = self._mode_var.get()
            else:
                mode = "max"

            if y:
                if mode == "min":
                    level = min(y)
                else:
                    level = max(y)
                env = [level] * len(y)
                self._plot.set_layer("envelope", x, env)
            else:
                self._plot.set_layer("envelope", None, None)

        self._schedule_next_step(200)
