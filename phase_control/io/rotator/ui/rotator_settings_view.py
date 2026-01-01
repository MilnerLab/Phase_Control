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
from phase_control.io.rotator.ui.rotator_settings_vm import RotatorSettingsViewModel


def _feq(a: float, b: float, eps: float = 1e-9) -> bool:
    return abs(a - b) <= eps


class RotatorSettingsView(ViewBase[RotatorSettingsViewModel]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ---------- validators ----------
        int_val = QIntValidator(0, 100, self)
        dbl_val = QDoubleValidator(self)
        dbl_val.setNotation(QDoubleValidator.StandardNotation)

        # ---------- speed row ----------
        speed_row = QWidget(self)
        speed_l = QHBoxLayout(speed_row)
        speed_l.setContentsMargins(0, 0, 0, 0)
        speed_l.setSpacing(8)

        speed_l.addWidget(QLabel("Movement Speed (%)", speed_row))

        self._speed_edit = QLineEdit(speed_row)
        self._speed_edit.setFixedWidth(90)
        self._speed_edit.setAlignment(Qt.AlignRight)
        self._speed_edit.setValidator(int_val)

        speed_l.addWidget(self._speed_edit)
        speed_l.addStretch(1)

        root.addWidget(speed_row)

        # ---------- angle range row ----------
        range_row = QWidget(self)
        range_l = QHBoxLayout(range_row)
        range_l.setContentsMargins(0, 0, 0, 0)
        range_l.setSpacing(8)

        range_l.addWidget(QLabel("Angle range (deg)", range_row))

        self._min_edit = QLineEdit(range_row)
        self._min_edit.setFixedWidth(90)
        self._min_edit.setAlignment(Qt.AlignRight)
        self._min_edit.setValidator(dbl_val)
        self._min_edit.setPlaceholderText("min")

        self._max_edit = QLineEdit(range_row)
        self._max_edit.setFixedWidth(90)
        self._max_edit.setAlignment(Qt.AlignRight)
        self._max_edit.setValidator(dbl_val)
        self._max_edit.setPlaceholderText("max")

        range_l.addWidget(self._min_edit)
        range_l.addWidget(QLabel("to", range_row))
        range_l.addWidget(self._max_edit)
        range_l.addStretch(1)

        root.addWidget(range_row)

        # ---------- out-of-range row ----------
        oor_row = QWidget(self)
        oor_l = QHBoxLayout(oor_row)
        oor_l.setContentsMargins(0, 0, 0, 0)
        oor_l.setSpacing(8)

        oor_l.addWidget(QLabel("Out-of-range rel angle (deg)", oor_row))

        self._oor_edit = QLineEdit(oor_row)
        self._oor_edit.setFixedWidth(90)
        self._oor_edit.setAlignment(Qt.AlignRight)
        self._oor_edit.setValidator(dbl_val)

        oor_l.addWidget(self._oor_edit)
        oor_l.addStretch(1)

        root.addWidget(oor_row)

        # ---------- Apply button centered ----------
        btn_row = QWidget(self)
        btn_l = QHBoxLayout(btn_row)
        btn_l.setContentsMargins(0, 8, 0, 0)
        btn_l.setSpacing(8)

        self._btn_apply = QPushButton("Apply", btn_row)
        self._btn_apply.setEnabled(False)

        btn_l.addStretch(1)
        btn_l.addWidget(self._btn_apply)
        btn_l.addStretch(1)

        root.addWidget(btn_row)

        # ---------- status ----------
        self._status = QLabel("", self)
        self._status.setAlignment(Qt.AlignCenter)
        root.addWidget(self._status)

        # ---------- init from singleton config ----------
        cfg = self.vm.config
        self._last_speed = int(cfg.speed)
        self._last_min = float(cfg.angle_range.min.deg)
        self._last_max = float(cfg.angle_range.max.deg)
        self._last_oor = float(cfg.out_of_range_rel_angle.deg)

        self._speed_edit.setText(str(self._last_speed))
        self._min_edit.setText(f"{self._last_min:g}")
        self._max_edit.setText(f"{self._last_max:g}")
        self._oor_edit.setText(f"{self._last_oor:g}")

        self._update_apply_enabled()

    def bind(self) -> None:
        super().bind()
        self.connect_binding(self.vm.status_changed, self._status.setText)
        self.connect_binding(self._speed_edit.textChanged, self._update_apply_enabled)
        self.connect_binding(self._btn_apply.clicked, self._on_apply_clicked)
        self.connect_binding(self._oor_edit.textChanged, self._update_apply_enabled)
        self.connect_binding(self._max_edit.textChanged, self._update_apply_enabled)
        self.connect_binding(self._min_edit.textChanged, self._update_apply_enabled)
        

    # ---------- parsing helpers ----------
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

    # ---------- apply enable logic ----------
    @Slot()
    def _update_apply_enabled(self) -> None:
        sp = self._parse_int(self._speed_edit)
        mn = self._parse_float(self._min_edit)
        mx = self._parse_float(self._max_edit)
        oor = self._parse_float(self._oor_edit)

        valid = (
            sp is not None and 0 <= sp <= 100 and
            mn is not None and
            mx is not None and mn < mx and
            oor is not None
        )

        if not valid:
            self._btn_apply.setEnabled(False)
            return

        changed = (
            sp != self._last_speed or
            not _feq(mn, self._last_min) or
            not _feq(mx, self._last_max) or
            not _feq(oor, self._last_oor)
        )

        self._btn_apply.setEnabled(changed)

    @Slot()
    def _on_apply_clicked(self) -> None:
        sp = self._parse_int(self._speed_edit)
        mn = self._parse_float(self._min_edit)
        mx = self._parse_float(self._max_edit)
        oor = self._parse_float(self._oor_edit)

        if sp is None or mn is None or mx is None or oor is None:
            return
        if mn >= mx:
            self._status.setText("Angle range invalid: min must be < max.")
            return

        self.vm.apply(sp, mn, mx, oor)

        # update "last applied" snapshot from the singleton config
        cfg = self.vm.config
        self._last_speed = int(cfg.speed)
        self._last_min = float(cfg.angle_range.min.deg)
        self._last_max = float(cfg.angle_range.max.deg)
        self._last_oor = float(cfg.out_of_range_rel_angle.deg)

        self._update_apply_enabled()
