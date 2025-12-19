# phase_control/modules/stabilization/module.py
from __future__ import annotations

from typing import Optional

from tkinter import ttk

from phase_control.modules.base import BaseModule, ModuleContext
from phase_control.modules.stabilization.config import AnalysisConfig
from phase_control.modules.stabilization.engine import AnalysisEngine
from phase_control.modules.stabilization.ui.config_panel import ConfigPanel
from phase_control.modules.stabilization.ui.plot_panel import PlotPanel


class StabilizationModule(BaseModule):
    """
    Phase stabilization module as a BaseModule.

    UI:
      - Notebook with:
          * Plotting tab (PlotPanel)
          * Config parameters tab (ConfigPanel)

    Behaviour:
      - run():
          * pushes FitParameter UI -> config
          * resets engine
          * starts .after loop
          * disables FitParameter editing
      - reset():
          * stops loop
          * resets engine
          * clears plot
          * refreshes FitParameter fields from config
          * re-enables FitParameter editing
    """

    name = "Phase stabilization"

    def __init__(self, context: ModuleContext) -> None:
        super().__init__(context)
        self._config = AnalysisConfig()
        self._engine = AnalysisEngine(config=self._config, buffer=context.buffer)

        self._plot_panel: Optional[PlotPanel] = None
        self._config_panel: Optional[ConfigPanel] = None

        self._running: bool = False
        self._after_id: str | None = None

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def build_ui(self, parent: ttk.Frame) -> None:
        """
        Build the notebook with Plot + Config tabs inside the given parent.
        """
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        self._plot_panel = PlotPanel(notebook)
        self._config_panel = ConfigPanel(notebook, config=self._config)

        notebook.add(self._plot_panel.frame, text="Plotting")
        notebook.add(self._config_panel.frame, text="Config parameters")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """
        Start the analysis loop.

        Called by the global MainWindow when the user presses "Run".
        """
        if self._running:
            return
        if self._plot_panel is None or self._config_panel is None:
            # UI not yet created
            return

        # Push FitParameter fields from UI -> config
        self._config_panel.apply_fit_parameters()

        # Reset engine state (PhaseTracker, etc.)
        self._engine.reset()

        # Update UI state
        self._config_panel.set_running(True)
        self._running = True

        # Schedule first step immediately
        self._schedule_next_step(delay_ms=0)

    def reset(self) -> None:
        """
        Stop the analysis and reset state and UI.
        """
        if self._plot_panel is None or self._config_panel is None:
            return

        self._stop_loop_only()
        self._engine.reset()
        self._plot_panel.clear()
        self._config_panel.refresh_from_config()
        self._config_panel.set_running(False)
        
    def close(self):
        self.reset()
        self._engine.close()

    # ------------------------------------------------------------------ #
    # Internals: Tk .after loop
    # ------------------------------------------------------------------ #

    def _stop_loop_only(self) -> None:
        if not self._running and self._after_id is None:
            return

        if self._after_id is not None:
            try:
                self.root_frame.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

        self._running = False

    def _schedule_next_step(self, delay_ms: int = 20) -> None:
        if not self._running:
            return
        self._after_id = self.root_frame.after(delay_ms, self._step_once)

    def _step_once(self) -> None:
        if not self._running:
            return

        result = self._engine.step()
        if result is not None and self._plot_panel is not None:
            # Update plot
            self._plot_panel.update_plot(result)

            # Update FitParameter UI from config (same instance updated by PhaseTracker)
            if self._config_panel is not None:
                self._config_panel.refresh_from_config()

        # Schedule the next iteration
        self._schedule_next_step(delay_ms=20)
