# your_app/ui/plot/plot_view.py
from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Slot
from shiboken6 import Object

from base_qt.views.bases.view_base import ViewBase
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM

class SpectrumPlotView(ViewBase[SpectrumPlotVM]):
    @classmethod
    def id(cls) -> str:
        return "core.SpectrumPlotView"
    def build_ui(self) -> None:
        self._plot = pg.PlotWidget()
        self._plot.showGrid(x=True, y=True)

        layout = pg.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._plot)

        self._curves: Dict[str, pg.PlotDataItem] = {}
        self._curve_order: list[str] = []

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        self.connect_binding(self.vm.series_updated, self._on_series_updated)
        self.connect_binding(self.vm.series_removed, self._on_series_removed)
        self.connect_binding(self.vm.cleared, self._on_cleared)


    @Slot(str, object)
    def _on_series_updated(self, key: str, x_obj: Object, y_obj: object) -> None:
        x = x_obj
        y = y_obj
        curve = self._curves.get(key)
        if curve is None:
            curve = self._plot.plot()
            self._curves[key] = curve
            self._curve_order.append(key)
            # simple distinct colors without extra config
            curve.setPen(pg.intColor(len(self._curve_order) - 1))
            curve.setData(x, y)
        else:
            curve.setData(x, y)

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
