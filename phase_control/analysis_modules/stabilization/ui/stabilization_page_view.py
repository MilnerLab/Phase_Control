from __future__ import annotations

from typing import Protocol, List

from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QDoubleSpinBox,
    QPushButton,
    QDialog,
    QWidget,
)

from base_qt.views.bases.view_base import ViewBase
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.analysis_modules.stabilization.ui.analysis_config_view import AnalysisConfigView
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView

class StabilizationPageView(ViewBase[StabilizationPageVM]):
    @classmethod
    def id(cls) -> str:
        return "stabilization.StabilizationPageView"

    def __init__(self, vm: StabilizationPageVM, registry: IViewRegistry):
        self._registry = registry
        super().__init__(vm)

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        row.addWidget(QLabel("Phase"))

        self._phase_edit = QDoubleSpinBox()
        self._phase_edit.setDecimals(4)
        self._phase_edit.setRange(0, 2)
        self._phase_edit.setSingleStep(0.1)
        self._phase_edit.setMaximumWidth(110)

        self._phase_edit.blockSignals(True)
        self._phase_edit.setValue(self.vm.get_phase_pi())
        self._phase_edit.blockSignals(False)

        row.addWidget(self._phase_edit)
        row.addWidget(QLabel("π"))

        row.addStretch(1)

        self._config_btn = QPushButton("Config")
        self._config_btn.setMaximumWidth(90)
        row.addWidget(self._config_btn)

        root.addLayout(row)

        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        self.connect_binding(self._phase_edit.valueChanged[float], self.vm.set_phase_pi)
        self.connect_binding(self._config_btn.clicked, self._open_config_popup)

    @Slot()
    def _open_config_popup(self) -> None:
        # prevent double-open while dialog exists
        self._config_btn.setEnabled(False)

        spec = self._registry.get("stabilization.AnalysisConfigView")
        cfg_view = spec.factory()

        if hasattr(cfg_view, "bind"):
            cfg_view.bind()  # type: ignore[attr-defined]

        dlg = QDialog(self.window())
        dlg.setWindowTitle("Stabilization Config")
        dlg.setModal(False)
        dlg.setAttribute(Qt.WA_DeleteOnClose, True)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(cfg_view)

        # re-enable button when popup closes
        dlg.finished.connect(self._on_config_closed)  # (accepted/rejected/closed)

        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    @Slot()
    def _on_config_closed(self, _result: int) -> None:
        self._config_btn.setEnabled(True)