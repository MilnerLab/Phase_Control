# your_app/modules/spectrometer/spectrometer_page_vm.py
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Slot

from base_core.framework.events.event_bus import EventBus
from base_qt.view_models.vm_base import VMBase
from phase_control.core.analysis_modules.view_models.interfaces import IRunnableVM
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from phase_control.io.frame_buffer import FrameBuffer


TOPIC_SPECTRUM_ARRIVED = "io.spectrum_arrived"


class StabilizationPageVM(VMBase, IRunnableVM):
    """
    Qt VM (ok): subscribes to EventBus and emits PlotVM updates.
    Services stay Qt-free; VM does dispatch via Signals/PlotVM.
    """

    status_changed = Signal(str)

    def __init__(self, bus: EventBus, plot: SpectrumPlotVM) -> None:
        super().__init__()
        self.plot = plot
        self._bus = bus
        
        self._snap_idx = 0
    
    def run(self) -> None:
        return
    def stop(self) -> None:
        return
    def reset(self) -> None:
        return

    @Slot()
    def snapshot(self) -> None:
        spec = self._buffer.get_latest()
        if spec is None:
            self.status_changed.emit("No spectrum yet.")
            return

        x = spec.wavelengths_nm
        y = spec.intensity

        if self.plot.x is None:
            self.plot.set_x(x)

        key = f"snap_{self._snap_idx}"
        self._snap_idx += 1
        self.plot.update_series(key, y)

    @Slot()
    def clear_snapshots(self) -> None:
        # keep live, remove everything else
        # simplest: rebuild: clear then re-add live if present
        live = None
        if "live" in getattr(self.plot, "_series", {}):
            live = self.plot._series["live"]  # if you don't like this, keep live in VM
        self.plot.clear()
        if live is not None and self.plot.x is not None:
            self.plot.update_series("live", live)
