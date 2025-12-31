from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from base_qt.views.bases.view_base import ViewBase
from phase_control.io.rotator.ui.rotator_settings_vm import RotatorSettingsViewModel


class RotatorSettingsView(ViewBase[RotatorSettingsViewModel]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # --- speed row ------------------------------------------------------
        row = QWidget(self)
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.setSpacing(8)

        row_l.addWidget(QLabel("Movement speed (%)", row))

        self._speed_edit = QLineEdit(row)
        self._speed_edit.setFixedWidth(90)
        self._speed_edit.setAlignment(Qt.AlignRight)
        self._speed_edit.setPlaceholderText("0–100")
        self._speed_edit.setValidator(QIntValidator(0, 100, self._speed_edit))
        self._speed_edit.textChanged.connect(self._on_speed_changed)

        self._btn_set = QPushButton("Set", row)
        self._btn_set.setEnabled(False)
        self._btn_set.clicked.connect(self._on_set_clicked)

        row_l.addWidget(self._speed_edit)
        row_l.addWidget(self._btn_set)
        row_l.addStretch(1)

        root.addWidget(row)

        # --- command buttons ------------------------------------------------
        cmd_row = QWidget(self)
        cmd_l = QHBoxLayout(cmd_row)
        cmd_l.setContentsMargins(0, 0, 0, 0)
        cmd_l.setSpacing(8)

        self._btn_home = QPushButton("Home", cmd_row)
        self._btn_restart = QPushButton("Restart", cmd_row)

        cmd_l.addWidget(self._btn_home)
        cmd_l.addWidget(self._btn_restart)
        cmd_l.addStretch(1)

        root.addWidget(cmd_row)

        # --- status ---------------------------------------------------------
        self._status = QLabel("", self)
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        # init state from VM
        self._last_set_speed: int | None = None
        self._apply_vm_speed(self.vm.speed_percent)

    def bind(self) -> None:
        super().bind()

        self._btn_home.clicked.connect(self.vm.home)
        self._btn_restart.clicked.connect(self.vm.restart)

        self.vm.speed_applied.connect(self._apply_vm_speed)
        self.vm.status_changed.connect(self._status.setText)

    # ---------------- internals ----------------

    @Slot(str)
    def _on_speed_changed(self, _text: str) -> None:
        self._update_set_enabled()

    @Slot()
    def _on_set_clicked(self) -> None:
        v = self._parsed_speed()
        if v is None:
            return
        self.vm.set_speed(v)

    def _parsed_speed(self) -> int | None:
        txt = self._speed_edit.text().strip()
        if not txt:
            return None
        try:
            v = int(txt)
        except ValueError:
            return None
        if 0 <= v <= 100:
            return v
        return None

    def _update_set_enabled(self) -> None:
        v = self._parsed_speed()
        self._btn_set.setEnabled(v is not None and (self._last_set_speed is None or v != self._last_set_speed))

    @Slot(int)
    def _apply_vm_speed(self, speed: int) -> None:
        self._last_set_speed = int(speed)
        self._speed_edit.setText(str(self._last_set_speed))
        self._update_set_enabled()
