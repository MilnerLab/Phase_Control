from __future__ import annotations
from site import PREFIXES

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from base_qt.views.bases.view_base import ViewBase
from base_core.quantities.enums import Prefix
from base_core.quantities.models import Length
from base_core.math.models import Angle, Range
from phase_control.analysis_modules.stabilization.ui.analysis_config_vm import AnalysisConfigVM



class AnalysisConfigView(ViewBase[AnalysisConfigVM]):
    @classmethod
    def id(cls) -> str:
        return "stabilization.AnalysisConfigView"

    def build_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- AnalysisConfig ---
        g1 = QGroupBox("Analysis")
        f1 = QFormLayout(g1)

        self._wl_min = QDoubleSpinBox(); self._wl_min.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._wl_max = QDoubleSpinBox(); self._wl_max.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._res_thresh = QDoubleSpinBox(); self._res_thresh.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._avg = QSpinBox(); self._avg.setButtonSymbols(QAbstractSpinBox.NoButtons)

        for sb in (self._wl_min, self._wl_max):
            sb.setDecimals(3); sb.setRange(-1e6, 1e6); sb.setSingleStep(0.1)
        self._res_thresh.setDecimals(3); self._res_thresh.setRange(0, 1e9); self._res_thresh.setSingleStep(0.5)
        self._avg.setRange(1, 10000)

        f1.addRow("Wavelength min [nm]", self._wl_min)
        f1.addRow("Wavelength max [nm]", self._wl_max)
        f1.addRow("Residual threshold", self._res_thresh)
        f1.addRow("Avg spectra", self._avg)
        root.addWidget(g1)

        # --- FitParameter ---
        g2 = QGroupBox("Fit parameters")
        f2 = QFormLayout(g2)

        self._carrier = QDoubleSpinBox(); self._carrier.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._bw = QDoubleSpinBox(); self._bw.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._baseline = QDoubleSpinBox(); self._baseline.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._phase = QDoubleSpinBox(); self._phase.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._tau = QDoubleSpinBox(); self._tau.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._ar = QDoubleSpinBox(); self._ar.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._al = QDoubleSpinBox(); self._al.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self._residual = QDoubleSpinBox(); self._residual.setButtonSymbols(QAbstractSpinBox.NoButtons)

        for sb in (self._carrier, self._bw):
            sb.setDecimals(4); sb.setRange(-1e6, 1e6); sb.setSingleStep(0.01)
        self._baseline.setDecimals(6); self._baseline.setRange(-1e9, 1e9); self._baseline.setSingleStep(0.001)
        self._phase.setDecimals(6); self._phase.setRange(-1e9, 1e9); self._phase.setSingleStep(0.01)
        self._tau.setDecimals(6); self._tau.setRange(-1e9, 1e9); self._tau.setSingleStep(0.01)
        self._ar.setDecimals(8); self._ar.setRange(-1e12, 1e12); self._ar.setSingleStep(0.001)
        self._al.setDecimals(8); self._al.setRange(-1e12, 1e12); self._al.setSingleStep(0.001)
        self._residual.setDecimals(6); self._residual.setRange(-1e12, 1e12); self._residual.setSingleStep(0.1)

        f2.addRow("Central λ [nm]", self._carrier)
        f2.addRow("Bandwidth [nm]", self._bw)
        f2.addRow("Baseline", self._baseline)
        f2.addRow("Phase", self._phase)
        f2.addRow("Tau [ps]", self._tau)
        f2.addRow("A_r [THz/ps]", self._ar)
        f2.addRow("A_l [THz/ps]", self._al)
        f2.addRow("Residual", self._residual)
        root.addWidget(g2)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self._apply_btn = QPushButton("Apply")
        self._close_btn = QPushButton("Close")
        btn_row.addWidget(self._apply_btn)
        btn_row.addWidget(self._close_btn)
        root.addLayout(btn_row)

    def bind(self) -> None:
        if self._bound:
            return
        super().bind()

        self.connect_binding(self._apply_btn.clicked, self.apply_from_ui)
        self.connect_binding(self._close_btn.clicked, self._close)

        # VM -> UI (single binding)
        self.connect_binding(self.vm.config_changed, self.write_to_ui)
        self.connect_binding(self.vm.is_running_changed, self._update_editable_state)

        # initial
        self.write_to_ui()
        self._update_editable_state(self.vm.is_running())

    @Slot()
    def apply_from_ui(self) -> None:
        cfg = self.vm.config

        # ---- always writable ----
        # Range: passe ggf. an deine Range API an
        cfg.wavelength_range = Range(Length(self._wl_min.value(), Prefix.NANO), Length(self._wl_max.value(), Prefix.NANO))
        cfg.residuals_threshold = float(self._res_thresh.value())
        cfg.avg_spectra = int(self._avg.value())

        # ---- fit params only if not running ----
        if not self.vm.is_running():
            cfg.central_wavelength = Length(self._carrier.value(), Prefix.NANO)
            cfg.bandwidth = Length(self._bw.value(), Prefix.NANO)
            cfg.baseline = float(self._baseline.value())
            cfg.phase = Angle(float(self._phase.value()))
            cfg.tau_ps = Angle(float(self._tau.value()))
            cfg.a_R_THz_per_ps = float(self._ar.value())
            cfg.a_L_THz_per_ps = float(self._al.value())
            cfg.residual = float(self._residual.value())

        self.vm.notify_config_changed()

    @Slot()
    def write_to_ui(self) -> None:
        cfg = self.vm.config

        def setv(sb, v):
            sb.blockSignals(True)
            sb.setValue(v)
            sb.blockSignals(False)

        # Range: passe ggf. an deine Range Felder an
        lo = cfg.wavelength_range.min  # oder .lower
        hi = cfg.wavelength_range.max  # oder .upper
        setv(self._wl_min, cfg.wavelength_range.min.value(Prefix.NANO))
        setv(self._wl_max, cfg.wavelength_range.max.value(Prefix.NANO))
        setv(self._res_thresh, float(cfg.residuals_threshold))
        setv(self._avg, int(cfg.avg_spectra))

        setv(self._carrier, cfg.central_wavelength.value(Prefix.NANO))
        setv(self._bw, cfg.bandwidth.value(Prefix.NANO))
        setv(self._baseline, float(cfg.baseline))
        setv(self._phase, float(getattr(cfg.phase, "value", cfg.phase)))
        setv(self._tau, float(cfg.tau_ps))
        setv(self._ar, float(cfg.a_R_THz_per_ps))
        setv(self._al, float(cfg.a_L_THz_per_ps))
        setv(self._residual, float(cfg.residual))

    @Slot(bool)
    def _update_editable_state(self, running: bool) -> None:
        editable = not running
        for sb in (self._carrier, self._bw, self._baseline, self._phase, self._tau, self._ar, self._al, self._residual):
            sb.setReadOnly(not editable)

    @Slot()
    def _close(self) -> None:
        w = self.window()
        if isinstance(w, QDialog):
            w.accept()
