from __future__ import annotations

from PySide6.QtCore import Signal, Slot
from base_qt.view_models.vm_base import VMBase
from phase_control.io.rotator.interfaces import IRotatorController


class RotatorSettingsViewModel(VMBase):
    speed_applied = Signal(int)     # emits the applied speed
    status_changed = Signal(str)    # simple status text

    def __init__(self, rotator: IRotatorController, *, default_speed: int = 40) -> None:
        super().__init__()
        self._rotator = rotator
        self._speed_percent = int(default_speed)

    @property
    def speed_percent(self) -> int:
        return self._speed_percent

    @Slot(int)
    def set_speed(self, percent: int) -> None:
        percent = int(percent)
        if percent < 0 or percent > 100:
            self.status_changed.emit("Speed must be 0–100.")
            return

        self._rotator.request_set_speed(percent)
        self._speed_percent = percent
        self.speed_applied.emit(percent)
        self.status_changed.emit(f"Speed set to {percent}%.")

    @Slot()
    def home(self) -> None:
        self._rotator.request_homing()
        self.status_changed.emit("Homing requested.")

    @Slot()
    def restart(self) -> None:
        # “restart” = close + open (open() homes in your controller)
        self._rotator.close()
        self._rotator.open()
        self.status_changed.emit("Restart requested.")
