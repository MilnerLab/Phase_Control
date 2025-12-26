# your_app/modules/spectrometer/spectrometer_page_view.py
from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QWidget

from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.core.plotting.spectrum_plot_view import PlotView



class StabilizationPageView(ViewBase[StabilizationPageVM]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # top controls
        bar = QHBoxLayout()
        self._btn_snapshot = QPushButton("Snapshot")
        self._btn_clear = QPushButton("Clear snapshots")
        bar.addWidget(self._btn_snapshot)
        bar.addWidget(self._btn_clear)
        bar.addStretch(1)
        root.addLayout(bar)

        # plot area (new instance per page view)
        self._plot_view = PlotView(self.vm.plot)
        root.addWidget(self._plot_view, 1)

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        self.vm.bind()
        self._btn_snapshot.clicked.connect(self.vm.snapshot)
        self._btn_clear.clicked.connect(self.vm.clear_snapshots)

    def unbind(self) -> None:
        try:
            self._btn_snapshot.clicked.disconnect(self.vm.snapshot)
            self._btn_clear.clicked.disconnect(self.vm.clear_snapshots)
            self._plot_view.unbind()
        except (TypeError, RuntimeError):
            pass

        self.vm.unbind()
        super().unbind()
