# phase_control/modules/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from tkinter import ttk

from phase_control.io.interfaces import FrameBufferProtocol
from phase_control.core.interfaces import SpectrumPlotProtocol


# ---------------------------------------------------------------------------
# Module context
# ---------------------------------------------------------------------------

@dataclass
class ModuleContext:
    """
    Shared services that every module has access to.

    Extend this later if you need more cross-cutting services (logging,
    global app config, waveplate control, ...).
    """
    buffer: FrameBufferProtocol
    plot: SpectrumPlotProtocol


# ---------------------------------------------------------------------------
# Base class for all modules
# ---------------------------------------------------------------------------

class BaseModule(ABC):
    """
    Base class for all application modules.

    Lifecycle (from the MainWindow's perspective):

      1. Create a ModuleContext (buffer, plot, ...).
      2. Instantiate a module: module = SomeModule(context).
      3. Ask the module to build its UI:
            root_frame = module.create_ui(parent_frame)
      4. When the user clicks "Run":
            module.run()
      5. When the user clicks "Reset" or switches modules:
            module.reset()
    """

    # Display name shown in the module selection UI
    name: str = "Unnamed module"

    def __init__(self, context: ModuleContext) -> None:
        self.context = context
        self._root_frame: ttk.Frame | None = None

    # ---------------- UI creation ---------------- #

    def create_ui(self, parent: ttk.Frame) -> ttk.Frame:
        """
        Create and return the root UI frame for this module.

        Modules should not override this; instead, implement `build_ui()`.
        """
        if self._root_frame is not None:
            raise RuntimeError("UI for this module has already been created.")

        frame = ttk.Frame(parent)
        self._root_frame = frame
        self.build_ui(frame)
        return frame

    @property
    def root_frame(self) -> ttk.Frame:
        """
        Accessor for the module's root frame (created by create_ui()).
        """
        if self._root_frame is None:
            raise RuntimeError(
                "Module UI has not been created yet. "
                "Call create_ui(parent) first."
            )
        return self._root_frame

    @abstractmethod
    def build_ui(self, parent: ttk.Frame) -> None:
        """
        Build the module-specific UI inside 'parent'.
        """
        ...

    # ---------------- lifecycle control ---------------- #

    @abstractmethod
    def run(self) -> None:
        """
        Start the module's processing.

        Typical responsibilities:
          - set an internal 'running' flag,
          - schedule the first iteration via `root_frame.after(...)`,
          - optionally pull initial state from the ModuleContext.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Stop the module and reset its state.

        Typical responsibilities:
          - clear internal 'running' flags,
          - cancel any outstanding `.after` callbacks,
          - clear the shared plot (self.context.plot.clear()),
          - reset UI elements to their default state.
        """
        ...


# Factory type for a registry
ModuleFactory = Callable[[ModuleContext], BaseModule]
