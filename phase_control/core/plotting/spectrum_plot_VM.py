# your_app/ui/plot/plot_vm.py
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from PySide6.QtCore import QObject, Signal


class PlotVM(QObject):
    """
    Holds plot data (Qt-side VM). View renders it.
    - x axis is shared for all series.
    - series count is dynamic.
    """

    x_changed = Signal(List[float])              # np.ndarray
    series_updated = Signal(str, List[float])    # key, np.ndarray(y)
    series_removed = Signal(str)            # key
    cleared = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._x: Optional[np.ndarray] = None
        self._series: Dict[str, np.ndarray] = {}

    @property
    def x(self) -> Optional[np.ndarray]:
        return self._x

    def set_x(self, x: np.ndarray) -> None:
        x = np.asarray(x, dtype=float)
        self._x = x
        self.x_changed.emit(x)

    def update_series(self, key: str, y: np.ndarray) -> None:
        y = np.asarray(y, dtype=float)
        self._series[key] = y
        self.series_updated.emit(key, y)

    def remove_series(self, key: str) -> None:
        if key in self._series:
            del self._series[key]
            self.series_removed.emit(key)

    def clear(self) -> None:
        self._series.clear()
        self.cleared.emit()
