# phase_control/modules/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from tkinter import ttk

from phase_control.io.interfaces import FrameBufferProtocol


@dataclass
class ModuleContext:
    """
    Shared services that every module has access to.

    For now this is just the FrameBuffer which provides live spectra.
    If you later need more cross-cutting services (logging, global config,
    waveplate access, ...), you can extend this dataclass.
    """
    buffer: FrameBufferProtocol


class BaseModule(ABC):
    """
    Base class for all application modules.

    Lifecycle (from the MainWindow's perspective):

      1. Create a ModuleContext (buffer, ...).
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

        The module is free to use `root_frame.after(...)`, threads, etc.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """
        Stop the module and reset its state.

        Should stop any .after loops, worker threads, clear plots, and
        reset config UI where appropriate.
        """
        ...


# Factory type for a registry
ModuleFactory = Callable[[ModuleContext], BaseModule]
