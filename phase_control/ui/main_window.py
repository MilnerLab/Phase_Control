# phase_control/ui/main_window.py
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

from phase_control.modules import MODULES, ModuleContext, BaseModule


class MainWindow:
    """
    Global main window.

    Layout:
      - Top bar:
          * module selection (Combobox)
          * Run button
          * Reset button
      - Center:
          * module container frame (active module injects its UI here)
    """

    def __init__(
        self,
        context: ModuleContext,
        stop_event: threading.Event,
    ) -> None:
        self._context = context
        self._stop_event = stop_event

        self._root = tk.Tk()
        self._root.title("Phase control")

        # Top bar
        top_frame = ttk.Frame(self._root)
        top_frame.pack(side="top", fill="x", padx=8, pady=4)

        ttk.Label(top_frame, text="Module:").pack(side="left", padx=(0, 4))

        self._module_names = list(MODULES.keys())
        self._module_var = tk.StringVar(value=self._module_names[0])

        self._module_combo = ttk.Combobox(
            top_frame,
            textvariable=self._module_var,
            values=self._module_names,
            state="readonly",
            width=24,
        )
        self._module_combo.pack(side="left", padx=(0, 8))
        self._module_combo.bind("<<ComboboxSelected>>", self._on_module_changed)

        self._run_button = ttk.Button(
            top_frame,
            text="Run",
            command=self._on_run_clicked,
        )
        self._run_button.pack(side="left", padx=4)

        self._reset_button = ttk.Button(
            top_frame,
            text="Reset",
            command=self._on_reset_clicked,
            state="normal",
        )
        self._reset_button.pack(side="left", padx=4)

        # Module container
        self._module_container = ttk.Frame(self._root)
        self._module_container.pack(fill="both", expand=True)

        self._current_module: BaseModule | None = None
        self._current_module_frame: ttk.Frame | None = None

        # Load initial module
        self._switch_module(self._module_names[0])

        # Window close handling
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # Module management
    # ------------------------------------------------------------------ #

    def _switch_module(self, name: str) -> None:
        # Reset and remove existing module
        if self._current_module is not None:
            try:
                self._current_module.close()
            except Exception:
                pass

        if self._current_module_frame is not None:
            self._current_module_frame.destroy()
            self._current_module_frame = None

        # Create new module
        module_cls = MODULES[name]
        self._current_module = module_cls(self._context)
        self._current_module_frame = self._current_module.create_ui(
            self._module_container
        )
        self._current_module_frame.pack(fill="both", expand=True)

    def _on_module_changed(self, event: object) -> None:
        name = self._module_var.get()
        self._switch_module(name)

    # ------------------------------------------------------------------ #
    # Run / Reset
    # ------------------------------------------------------------------ #

    def _on_run_clicked(self) -> None:
        if self._current_module is None:
            return
        self._current_module.run()

    def _on_reset_clicked(self) -> None:
        if self._current_module is None:
            return
        self._current_module.reset()

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def _on_close(self) -> None:
        if self._current_module is not None:
            try:
                self._current_module.reset()
            except Exception:
                pass
        self._stop_event.set()
        self._root.destroy()

    def run(self) -> None:
        self._root.mainloop()


def run_main_window(
    context: ModuleContext,
    stop_event: threading.Event,
) -> None:
    ui = MainWindow(context=context, stop_event=stop_event)
    ui.run()
