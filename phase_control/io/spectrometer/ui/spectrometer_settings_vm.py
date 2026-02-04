from __future__ import annotations

from concurrent.futures import Future
from typing import Optional

from PySide6.QtCore import Signal, Slot

from base_qt.view_models.vm_base import VMBase
from phase_control.io.spectrometer.spectrometer_service import SpectrometerService


class SpectrometerSettingsViewModel(VMBase):
    status_changed = Signal(str)

    def __init__(self, spectrometer: SpectrometerService) -> None:
        super().__init__()
        self._spectrometer = spectrometer

    @property
    def config(self):
        return self._spectrometer.config

    @Slot(int, float, int, int, int, int)
    def apply(
        self,
        device_index: int,
        exposure_ms: float,
        average: int,
        dark_subtraction: int,
        mode: int,
        scan_delay: int,
    ) -> None:
        # --- validate ---
        device_index = int(device_index)
        if device_index < 0:
            self.status_changed.emit("Device index must be >= 0.")
            return

        exposure_ms = float(exposure_ms)
        if exposure_ms <= 0:
            self.status_changed.emit("Exposure must be > 0 ms.")
            return

        average = int(average)
        if average < 1:
            self.status_changed.emit("Average must be >= 1.")
            return

        dark_subtraction = int(dark_subtraction)
        if dark_subtraction not in (0, 1):
            self.status_changed.emit("Dark subtraction must be 0 or 1.")
            return

        mode = int(mode)
        if mode < 0:
            self.status_changed.emit("Mode must be >= 0.")
            return

        scan_delay = int(scan_delay)
        if scan_delay < 0:
            self.status_changed.emit("Scan delay must be >= 0.")
            return

        # --- update service-owned config (in-place) ---
        cfg = self._spectrometer.config
        cfg.device_index = device_index
        cfg.exposure_ms = exposure_ms
        cfg.average = average
        cfg.dark_subtraction = dark_subtraction
        cfg.mode = mode
        cfg.scan_delay = scan_delay

        # --- apply to child process ---
        self.status_changed.emit("Applying...")
        fut: Future = self._spectrometer.set_config_async()
        fut.add_done_callback(self._on_apply_done)

    def _on_apply_done(self, fut: Future) -> None:
        try:
            _ = fut.result()
        except BaseException as e:
            self.status_changed.emit(f"Apply failed: {e}")
            return
        self.status_changed.emit("Applied.")
