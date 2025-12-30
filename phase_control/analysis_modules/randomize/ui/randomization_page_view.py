from PySide6.QtWidgets import QVBoxLayout
from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.randomize.ui.randomization_page_vm import RandomizationPageVM
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView


class RandomizationPageView(ViewBase[RandomizationPageVM]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # plot area (new instance per page view)
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)