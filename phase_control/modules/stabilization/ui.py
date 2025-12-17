# phase_control/modules/stabilization/ui.py
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from phase_control.modules.stabilization.config import AnalysisConfig
from phase_control.modules.stabilization.engine import AnalysisEngine, AnalysisPlotResult
from phase_control.modules.stabilization.ui.config_panel import ConfigPanel
from phase_control.modules.stabilization.ui.plot_panel import PlotPanel


class StabilizationWindow:
    """
    Standalone UI for the stabilization module.

    - Top bar with "Run" and "Reset" buttons.
    - Notebook with:
        * "Plotting" tab (PlotPanel)
        * "Config parameters" tab (ConfigPanel)

    Behaviour:
      - Run:
          * stops any running loop
          * applies FitParameter fields from UI -> config
          * resets the AnalysisEngine
          * starts Tk .after loop
          * disables FitParameter entries and Run button, enables Reset.
      - Reset:
          * stops loop
          * resets AnalysisEngine
          * clears plot
          * refreshes FitParameter fields from config
          * re-enables FitParameter entries and Run button.
    """

    def __init__(
        self,
        config: AnalysisConfig,
        engine: AnalysisEngine,
        stop_event: threading.Event | None = None,
    ) -> None:
        self._config = config
        self._engine = engine
        self._stop_event = stop_event or threading.Event()

        self._root = tk.Tk()
        self._root.title("Phase control – Stabilization")

        # --- Top control bar: Run & Reset -------------------------------- #
        control_frame = ttk.Frame(self._root)
        control_frame.pack(side="top", fill="x")

        self._run_button = ttk.Button(
            control_frame,
            text="Run",
            command=self._on_run_clicked,
        )
        self._run_button.pack(side="left", padx=8, pady=4)

        self._reset_button = ttk.Button(
            control_frame,
            text="Reset",
            command=self._on_reset_clicked,
            state="disabled",
        )
        self._reset_button.pack(side="left", padx=4, pady=4)

        # --- Notebook with tabs ------------------------------------------ #
        self._notebook = ttk.Notebook(self._root)
        self._notebook.pack(fill="both", expand=True)

        self._plot_panel = PlotPanel(self._notebook)
        self._config_panel = ConfigPanel(self._notebook, config=self._config)

        self._notebook.add(self._plot_panel.frame, text="Plotting")
        self._notebook.add(self._config_panel.frame, text="Config parameters")

        # Analysis loop state
        self._running: bool = False
        self._after_id: str | None = None

        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # Analysis control
    # ------------------------------------------------------------------ #

    def _set_running(self, running: bool) -> None:
        """Update UI state for running/not-running."""
        self._running = running
        self._config_panel.set_running(running)
        self._run_button.configure(state="disabled" if running else "normal")
        self._reset_button.configure(state="normal" if running else "disabled")

    def _on_run_clicked(self) -> None:
        """
        Called when the Run button is pressed.

        - stop any running loop
        - push FitParameter UI values -> shared config
        - reset engine
        - start Tk .after loop
        """
        self._stop_loop_only()

        # Update FitParameter values from UI into config
        self._config_panel.apply_fit_parameters()
        # Engine reset: new PhaseTracker etc. using current config
        self._engine.reset()

        self._set_running(True)
        self._schedule_next_step(delay_ms=0)

    def _on_reset_clicked(self) -> None:
        """
        Stop the analysis and reset everything:

        - stop loop
        - reset engine (internal state)
        - clear plot
        - refresh FitParameter fields from current config
        - re-enable editing of FitParameter fields
        """
        self._stop_loop_only()
        self._engine.reset()
        self._plot_panel.clear()
        self._config_panel.refresh_from_config()
        self._set_running(False)

    def _stop_loop_only(self) -> None:
        """Stop the Tk .after loop without touching config/engine."""
        if not self._running and self._after_id is None:
            return
        if self._after_id is not None:
            try:
                self._root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None
        self._running = False  # UI state is updated by _set_running()

    def _schedule_next_step(self, delay_ms: int = 20) -> None:
        if not self._running:
            return
        self._after_id = self._root.after(delay_ms, self._step_once)

    def _step_once(self) -> None:
        if not self._running:
            return

        result = self._engine.step()
        if result is None:
            # no data yet -> try again a bit later
            self._schedule_next_step(delay_ms=50)
            return

        # Update plot
        self._plot_panel.update_plot(result)

        # Config may have been updated by PhaseTracker (same instance),
        # so mirror that back into the FitParameter fields in the UI.
        self._config_panel.refresh_from_config()

        # Next step
        self._schedule_next_step(delay_ms=20)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def _on_close(self) -> None:
        self._stop_loop_only()
        self._set_running(False)
        self._stop_event.set()
        self._root.destroy()

    def run(self) -> None:
        """Start the Tk main loop."""
        self._root.mainloop()


def run_stabilization_window(
    config: AnalysisConfig,
    engine: AnalysisEngine,
    stop_event: threading.Event | None = None,
) -> None:
    """
    Convenience function to create and run the stabilization window.
    """
    ui = StabilizationWindow(config=config, engine=engine, stop_event=stop_event)
    ui.run()
