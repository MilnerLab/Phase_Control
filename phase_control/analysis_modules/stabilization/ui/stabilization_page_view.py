# your_app/modules/spectrometer/spectrometer_page_view.py
from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QWidget

from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView


class StabilizationPageView(ViewBase[StabilizationPageVM]):
    @classmethod
    def id(cls) -> str:
        return "stabilization.StabilizationPageView"
    
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # plot area (new instance per page view)
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)


