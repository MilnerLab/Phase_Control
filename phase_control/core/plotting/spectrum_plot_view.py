# your_app/ui/plot/plot_view.py
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot

from base_qt.views.bases.view_base import ViewBase
from phase_control.core.plotting.spectrum_plot_VM import PlotVM

class PlotView(ViewBase[PlotVM]):
    def build_ui(self) -> None:
        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True)

        layout = pg.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)

        self._x: Optional[np.ndarray] = None
        self._curves: Dict[str, pg.PlotDataItem] = {}
        self._curve_order: list[str] = []

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        self.vm.x_changed.connect(self._on_x_changed)
        self.vm.series_updated.connect(self._on_series_updated)
        self.vm.series_removed.connect(self._on_series_removed)
        self.vm.cleared.connect(self._on_cleared)

    def unbind(self) -> None:
        if not self._bound:
            return

        for sig, fn in [
            (self.vm.x_changed, self._on_x_changed),
            (self.vm.series_updated, self._on_series_updated),
            (self.vm.series_removed, self._on_series_removed),
            (self.vm.cleared, self._on_cleared),
        ]:
            try:
                sig.disconnect(fn)
            except (TypeError, RuntimeError):
                pass

        super().unbind()

    @Slot(object)
    def _on_x_changed(self, x: object) -> None:
        self._x = x  # numpy array
        # re-render existing curves with new x
        for key, curve in self._curves.items():
            y = curve.yData
            if y is None:
                continue
            curve.setData(self._x, y)

    @Slot(str, object)
    def _on_series_updated(self, key: str, y_obj: object) -> None:
        y = y_obj
        curve = self._curves.get(key)
        if curve is None:
            curve = self._plot.plot()
            self._curves[key] = curve
            self._curve_order.append(key)
            # simple distinct colors without extra config
            curve.setPen(pg.intColor(len(self._curve_order) - 1))

        if self._x is None:
            curve.setData(y)
        else:
            curve.setData(self._x, y)

    @Slot(str)
    def _on_series_removed(self, key: str) -> None:
        curve = self._curves.pop(key, None)
        if curve is None:
            return
        self._plot.removeItem(curve)
        if key in self._curve_order:
            self._curve_order.remove(key)

    @Slot()
    def _on_cleared(self) -> None:
        for curve in self._curves.values():
            self._plot.removeItem(curve)
        self._curves.clear()
        self._curve_order.clear()
