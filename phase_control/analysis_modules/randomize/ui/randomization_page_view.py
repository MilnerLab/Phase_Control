from base_qt.views.bases.view_base import ViewBase


class RandomizationPageView(ViewBase[StabilizationPageVM]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # plot area (new instance per page view)
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)