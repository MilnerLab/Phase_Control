from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np
from PySide6.QtCore import Signal

from base_core.framework.events import EventBus
from base_qt.view_models.thread_safe_vm_base import ThreadSafeVMBase, ui_thread
from phase_control.io.events import TOPIC_NEW_SPECTRUM
from phase_control.io.frame_buffer import FrameBuffer
from base_qt.app.interfaces import IUiDispatcher


class SpectrumPlotVM(ThreadSafeVMBase):
    """
    Holds plot data (Qt-side VM). View renders it.
    - x axis is shared for all series.
    - series count is dynamic.
    """

    x_changed = Signal(object)            # np.ndarray
    series_updated = Signal(str, object)  # key, np.ndarray(y)
    series_removed = Signal(str)
    cleared = Signal()

    def __init__(self, ui: IUiDispatcher, bus: EventBus, buffer: FrameBuffer) -> None:
        super().__init__(ui, bus)
        self._buffer = buffer

        self._x: Optional[np.ndarray] = None
        self._series: Dict[str, np.ndarray] = {}
        self._unsub: Optional[Callable[[], None]] = None
        
        self.sub_event(TOPIC_NEW_SPECTRUM, self._on_new_spectrum)

    @property
    def x(self) -> Optional[np.ndarray]:
        return self._x

    @ui_thread
    def apply_spectrum(self, x: np.ndarray, y: np.ndarray, key: str) -> None:
        # runs in UI thread
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        if self._x is None:
            self._x = x
            self.x_changed.emit(x)

        self._series[key] = y
        self.series_updated.emit(key, y)

    def remove_series(self, key: str) -> None:
        if key in self._series:
            del self._series[key]
            self.series_removed.emit(key)

    def clear(self) -> None:
        self._series.clear()
        self.cleared.emit()

    def unbind(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
            
    def _on_new_spectrum(self, args) -> None:
        spec = self._buffer.get_latest()
        if spec is None:
            return
        x = spec.wavelengths_nm.copy()
        y = spec.intensity.copy()
        self.apply_spectrum(x, y, "live")  