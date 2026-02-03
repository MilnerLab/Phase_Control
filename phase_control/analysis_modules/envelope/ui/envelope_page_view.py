from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
)

from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.envelope.domain.enums import EnvelopeMode
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView

from phase_control.analysis_modules.envelope.ui.envelope_page_vm import EnvelopePageVM


class EnvelopePageView(ViewBase[EnvelopePageVM]):
    @classmethod
    def id(cls) -> str:
        return "envelope.EnvelopePageView"

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # --- header row -----------------------------------------------------
        header = QWidget(self)
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(0, 0, 0, 0)
        header_l.setSpacing(8)

        header_l.addWidget(QLabel("View", header))
        header_l.addStretch(1)

        self._maximize_btn = QPushButton("Maximize", header)
        self._minimize_btn = QPushButton("Minimize", header)
        for b in (self._maximize_btn, self._minimize_btn):
            b.setCheckable(True)

        # exclusive selection
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)
        self._mode_group.addButton(self._maximize_btn)
        self._mode_group.addButton(self._minimize_btn)

        header_l.addWidget(self._maximize_btn)
        header_l.addWidget(self._minimize_btn)

        root.addWidget(header, 0)

        # --- plot area ------------------------------------------------------
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        # UI -> VM (user action only)
        self.connect_binding(self._mode_group.buttonClicked, self._on_mode_button_clicked)

        # VM -> UI
        self.connect_binding(self.vm.mode_changed, self._apply_mode_to_ui)

        # initial sync
        self._apply_mode_to_ui(self.vm.mode)

    # ---------------- bindings ----------------
    @Slot(object)
    def _on_mode_button_clicked(self, btn: QPushButton) -> None:
        if btn is self._maximize_btn:
            self.vm.mode = EnvelopeMode.MAXIMIZE
        elif btn is self._minimize_btn:
            self.vm.mode = EnvelopeMode.MINIMIZE

    @Slot(object)
    def _apply_mode_to_ui(self, mode: EnvelopeMode) -> None:
        # avoid feedback loops
        self._maximize_btn.blockSignals(True)
        self._minimize_btn.blockSignals(True)
        try:
            self._maximize_btn.setChecked(mode == EnvelopeMode.MAXIMIZE)
            self._minimize_btn.setChecked(mode == EnvelopeMode.MINIMIZE)
        finally:
            self._maximize_btn.blockSignals(False)
            self._minimize_btn.blockSignals(False)
