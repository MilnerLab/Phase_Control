# your_app/modules/spectrometer/spectrometer_page_view.py
from __future__ import annotations

from PySide6.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QWidget

from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView

from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QDoubleSpinBox,
    QAbstractSpinBox,
)


class StabilizationPageView(ViewBase[StabilizationPageVM]):
    @classmethod
    def id(cls) -> str:
        return "stabilization.StabilizationPageView"

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # --- Phase row: Phase [factor] π ---
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        row.addWidget(QLabel("Phase"))

        self._phase_edit = QDoubleSpinBox()
        self._phase_edit.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._phase_edit.setDecimals(4)
        self._phase_edit.setRange(-1e6, 1e6)
        self._phase_edit.setMaximumWidth(110)
        row.addWidget(self._phase_edit)

        row.addWidget(QLabel("π"))
        row.addStretch(1)

        root.addLayout(row)

        # plot area
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        # one-time init from config via VM
        self._phase_edit.blockSignals(True)
        self._phase_edit.setValue(self.vm.get_phase_pi())
        self._phase_edit.blockSignals(False)

        # UI -> VM (cleanup-safe binding)
        self.connect_binding(self._phase_edit.valueChanged[float], self.vm.set_phase_pi)
