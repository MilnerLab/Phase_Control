# phase_control/modules/randomize/module.py
from __future__ import annotations

import random
from typing import Optional

import tkinter as tk
from tkinter import ttk

from phase_control.modules.base import BaseModule, ModuleContext
from phase_control.core.plotting.spectrum_plot import SpectrumPlotPanel


class RandomizeModule(BaseModule):
    """
    Dummy module that demonstrates how a module can:

      - own its own UI (controls + plot)
      - use the shared FrameBuffer from ModuleContext
      - run a simple Tk .after loop

    It periodically generates a random value and, if a spectrum is
    available in the buffer, displays it in the plot.
    """

    name = "Randomize"

    def __init__(self, context: ModuleContext) -> None:
        super().__init__(context)
        self._running: bool = False
        self._after_id: str | None = None

        self._random_value_var: Optional[tk.StringVar] = None
        self._plot: Optional[SpectrumPlotPanel] = None

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def build_ui(self, parent: ttk.Frame) -> None:
        """
        Build a simple UI:

          - top: "Randomize" group with a label showing a random value
          - bottom: shared spectrum plot
        """
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        # Top controls
        control_frame = ttk.LabelFrame(parent, text="Randomize demo")
        control_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        control_frame.columnconfigure(1, weight=1)

        ttk.Label(control_frame, text="Last random value:").grid(
            row=0, column=0, sticky="w", padx=4, pady=4
        )

        self._random_value_var = tk.StringVar(value="N/A")
        ttk.Label(control_frame, textvariable=self._random_value_var).grid(
            row=0, column=1, sticky="w", padx=4, pady=4
        )

        ttk.Button(
            control_frame,
            text="Generate once",
            command=self._generate_once,
        ).grid(row=0, column=2, sticky="e", padx=4, pady=4)

        # Plot area
        plot_frame = ttk.Frame(parent)
        plot_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)

        self._plot = SpectrumPlotPanel(
            plot_frame,
            xlabel="Wavelength [nm]",
            ylabel="Normalized intensity",
            title="Randomize – latest spectrum",
        )
        self._plot.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Start periodic random generation + spectrum update.
        """
        if self._running:
            return
        self._running = True
        self._schedule_next_step(0)

    def reset(self) -> None:
        """
        Stop the loop and reset UI state.
        """
        if self._after_id is not None:
            try:
                self.root_frame.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self._running = False

        if self._random_value_var is not None:
            self._random_value_var.set("N/A")
        if self._plot is not None:
            self._plot.clear()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _generate_once(self) -> None:
        """
        Generate a random value and update the label immediately.
        """
        if self._random_value_var is None:
            return
        value = random.random()
        self._random_value_var.set(f"{value:.4f}")

    def _schedule_next_step(self, delay_ms: int) -> None:
        if not self._running:
            return
        self._after_id = self.root_frame.after(delay_ms, self._step_once)

    def _step_once(self) -> None:
        if not self._running:
            return

        # Update random value
        self._generate_once()

        # Try to fetch latest spectrum from buffer
        spectrum = self.context.buffer.get_latest()
        if spectrum is not None and self._plot is not None:
            x = spectrum.wavelengths_nm
            y = spectrum.intensity
            self._plot.set_base_spectrum(x, y)

        # schedule next update
        self._schedule_next_step(200)
