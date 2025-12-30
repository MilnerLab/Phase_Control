from __future__ import annotations

from re import I
from typing import Callable, Dict, Optional

from base_core.math.models import Range
from base_core.quantities.enums import Prefix
from base_core.quantities.models import Length
import numpy as np
from PySide6.QtCore import Signal

from base_core.framework.events import EventBus
from base_qt.view_models.thread_safe_vm_base import ThreadSafeVMBase, ui_thread
from phase_control.io.events import TOPIC_NEW_SPECTRUM
from base_qt.app.interfaces import IUiDispatcher
from phase_control.io.spectrometer.frame_buffer import FrameBuffer
from phase_control.io.spectrometer.interfaces import IFrameBuffer


class SpectrumPlotVM(ThreadSafeVMBase):
    """
    Holds plot data (Qt-side VM). View renders it.
    - x axis is shared for all series.
    - series count is dynamic.
    """

    series_updated = Signal(str, object, object) 
    series_removed = Signal(str)
    cleared = Signal()

    def __init__(self, ui: IUiDispatcher, bus: EventBus, buffer: IFrameBuffer) -> None:
        super().__init__(ui, bus)
        self._buffer = buffer

        self._series: Dict[str, np.ndarray] = {}
        self._unsub: Optional[Callable[[], None]] = None
        
        self.sub_event(TOPIC_NEW_SPECTRUM, self._on_new_spectrum)

    @ui_thread
    def apply_spectrum(self, x: np.ndarray, y: np.ndarray, key: str) -> None:
        # runs in UI thread
        x = np.asarray(x, dtype=float)
        y = np.asarray(y, dtype=float)

        self._series[key] = y
        self.series_updated.emit(key, x, y)

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
        cut = spec.cut(Range(Length(800, Prefix.NANO), Length(805, Prefix.NANO)))
        x = cut.wavelengths_nm.copy()
        y = cut.intensity.copy()
        self.apply_spectrum(x, y, "live")  