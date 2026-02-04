from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from base_qt.views.bases.view_base import ViewBase
from phase_control.io.spectrometer.ui.spectrometer_settings_vm import SpectrometerSettingsViewModel


def _feq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


class SpectrometerSettingsView(ViewBase[SpectrometerSettingsViewModel]):
    @classmethod
    def id(cls) -> str:
        return "io.SpectrometerSettingsView"

    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        int_val = QIntValidator(self)
        dbl_val = QDoubleValidator(self)
        dbl_val.setNotation(QDoubleValidator.StandardNotation)

        # ----- helper to build one row -----
        def row(label: str, edit: QLineEdit) -> None:
            w = QWidget(self)
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(8)
            l.addWidget(QLabel(label, w))
            l.addWidget(edit)
            l.addStretch(1)
            root.addWidget(w)

        # device_index
        self._dev = QLineEdit(self)
        self._dev.setFixedWidth(110)
        self._dev.setAlignment(Qt.AlignRight)
        self._dev.setValidator(QIntValidator(0, 999, self))
        row("Device index", self._dev)

        # exposure_ms
        self._exp = QLineEdit(self)
        self._exp.setFixedWidth(110)
        self._exp.setAlignment(Qt.AlignRight)
        self._exp.setValidator(dbl_val)
        row("Exposure (ms)", self._exp)

        # average
        self._avg = QLineEdit(self)
        self._avg.setFixedWidth(110)
        self._avg.setAlignment(Qt.AlignRight)
        self._avg.setValidator(QIntValidator(1, 10_000, self))
        row("Average", self._avg)

        # dark_subtraction (0/1)
        self._dark = QLineEdit(self)
        self._dark.setFixedWidth(110)
        self._dark.setAlignment(Qt.AlignRight)
        self._dark.setValidator(QIntValidator(0, 1, self))
        row("Dark subtraction (0/1)", self._dark)

        # mode
        self._mode = QLineEdit(self)
        self._mode.setFixedWidth(110)
        self._mode.setAlignment(Qt.AlignRight)
        self._mode.setValidator(QIntValidator(0, 999, self))
        row("Mode", self._mode)

        # scan_delay
        self._delay = QLineEdit(self)
        self._delay.setFixedWidth(110)
        self._delay.setAlignment(Qt.AlignRight)
        self._delay.setValidator(QIntValidator(0, 1_000_000, self))
        row("Scan delay", self._delay)

        # Apply button
        btn_row = QWidget(self)
        btn_l = QHBoxLayout(btn_row)
        btn_l.setContentsMargins(0, 8, 0, 0)

        self._btn_apply = QPushButton("Apply", btn_row)
        self._btn_apply.setEnabled(False)

        btn_l.addStretch(1)
        btn_l.addWidget(self._btn_apply)
        btn_l.addStretch(1)
        root.addWidget(btn_row)

        # Status
        self._status = QLabel("", self)
        self._status.setAlignment(Qt.AlignCenter)
        root.addWidget(self._status)

        # Init from service-owned config
        cfg = self.vm.config
        self._last_dev = int(cfg.device_index)
        self._last_exp = float(cfg.exposure_ms)
        self._last_avg = int(cfg.average)
        self._last_dark = int(cfg.dark_subtraction)
        self._last_mode = int(cfg.mode)
        self._last_delay = int(cfg.scan_delay)

        self._dev.setText(str(self._last_dev))
        self._exp.setText(f"{self._last_exp:g}")
        self._avg.setText(str(self._last_avg))
        self._dark.setText(str(self._last_dark))
        self._mode.setText(str(self._last_mode))
        self._delay.setText(str(self._last_delay))

        self._update_apply_enabled()

    def bind(self) -> None:
        super().bind()
        self.connect_binding(self.vm.status_changed, self._status.setText)

        for e in (self._dev, self._exp, self._avg, self._dark, self._mode, self._delay):
            self.connect_binding(e.textChanged, self._update_apply_enabled)

        self.connect_binding(self._btn_apply.clicked, self._on_apply_clicked)

    def _parse_int(self, edit: QLineEdit) -> int | None:
        t = edit.text().strip()
        if not t:
            return None
        try:
            return int(t)
        except ValueError:
            return None

    def _parse_float(self, edit: QLineEdit) -> float | None:
        t = edit.text().strip()
        if not t:
            return None
        try:
            return float(t)
        except ValueError:
            return None

    @Slot()
    def _update_apply_enabled(self) -> None:
        dev = self._parse_int(self._dev)
        exp = self._parse_float(self._exp)
        avg = self._parse_int(self._avg)
        dark = self._parse_int(self._dark)
        mode = self._parse_int(self._mode)
        delay = self._parse_int(self._delay)

        valid = (
            dev is not None and dev >= 0 and
            exp is not None and exp > 0 and
            avg is not None and avg >= 1 and
            dark is not None and dark in (0, 1) and
            mode is not None and mode >= 0 and
            delay is not None and delay >= 0
        )
        if not valid:
            self._btn_apply.setEnabled(False)
            return

        changed = (
            dev != self._last_dev or
            not _feq(exp, self._last_exp) or
            avg != self._last_avg or
            dark != self._last_dark or
            mode != self._last_mode or
            delay != self._last_delay
        )
        self._btn_apply.setEnabled(changed)

    @Slot()
    def _on_apply_clicked(self) -> None:
        dev = self._parse_int(self._dev)
        exp = self._parse_float(self._exp)
        avg = self._parse_int(self._avg)
        dark = self._parse_int(self._dark)
        mode = self._parse_int(self._mode)
        delay = self._parse_int(self._delay)

        if dev is None or exp is None or avg is None or dark is None or mode is None or delay is None:
            return

        self.vm.apply(dev, exp, avg, dark, mode, delay)

        # Update "last applied" snapshot from service-owned config
        cfg = self.vm.config
        self._last_dev = int(cfg.device_index)
        self._last_exp = float(cfg.exposure_ms)
        self._last_avg = int(cfg.average)
        self._last_dark = int(cfg.dark_subtraction)
        self._last_mode = int(cfg.mode)
        self._last_delay = int(cfg.scan_delay)

        self._update_apply_enabled()
