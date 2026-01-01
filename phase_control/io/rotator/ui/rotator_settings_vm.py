from __future__ import annotations

from dataclasses import dataclass
from PySide6.QtCore import Signal, Slot

from base_qt.view_models.vm_base import VMBase
from base_core.math.models import Angle, AngleUnit, Range
from elliptec.config import ELL14Config
from phase_control.io.rotator.interfaces import IRotatorController

class RotatorSettingsViewModel(VMBase):
    status_changed = Signal(str)

    def __init__(self, rotator: IRotatorController) -> None:
        super().__init__()
        self._rotator = rotator

    @property
    def config(self) -> ELL14Config:
        return self._rotator.config

    @Slot(int, float, float, float)
    def apply(self, speed_percent: int, min_deg: float, max_deg: float, out_of_range_rel_deg: float) -> None:
        # If rotator is busy: do not apply
        if self._rotator.is_busy:
            self.status_changed.emit("Rotator is busy — try again when idle.")
            return

        # --- validate ---
        speed_percent = int(speed_percent)
        if not (0 <= speed_percent <= 100):
            self.status_changed.emit("Speed must be 0–100%.")
            return

        min_deg = float(min_deg)
        max_deg = float(max_deg)
        if not (min_deg < max_deg):
            self.status_changed.emit("Angle range invalid: min must be < max.")
            return

        out_of_range_rel_deg = float(out_of_range_rel_deg)

        # --- apply to singleton config ---
        self._rotator.config.speed = speed_percent
        self._rotator.config.angle_range = Range(Angle(min_deg, AngleUnit.DEG), Angle(max_deg, AngleUnit.DEG))
        self._rotator.config.out_of_range_rel_angle = Angle(out_of_range_rel_deg, AngleUnit.DEG)

        # --- apply to hardware ---
        self._rotator.request_apply_config()

        self.status_changed.emit("Applied.")

