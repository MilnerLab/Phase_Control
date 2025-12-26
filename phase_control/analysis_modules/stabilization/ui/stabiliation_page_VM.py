# your_app/modules/spectrometer/spectrometer_page_vm.py
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import QObject, Signal, Slot

from base_core.framework.events.event_bus import EventBus
from phase_control.core.plotting.spectrum_plot_VM import PlotVM
from phase_control.io.frame_buffer import FrameBuffer


TOPIC_SPECTRUM_ARRIVED = "io.spectrum_arrived"


class StabilizationPageVM(QObject):
    """
    Qt VM (ok): subscribes to EventBus and emits PlotVM updates.
    Services stay Qt-free; VM does dispatch via Signals/PlotVM.
    """

    status_changed = Signal(str)

    def __init__(self, bus: EventBus, buffer: FrameBuffer, plot: PlotVM) -> None:
        super().__init__()
        self.plot = plot
        self._bus = bus
        self._buffer = buffer

        self._unsub: Optional[Callable[[], None]] = None
        self._snap_idx = 0

    def bind(self) -> None:
        if self._unsub is not None:
            return

        def on_arrived(_payload) -> None:
            # runs in publisher thread (IO thread). Keep it light.
            spec = self._buffer.get_latest()  # must return something like (x, y) or Spectrum
            if spec is None:
                return

            # adapt these two lines to your Spectrum shape:
            x = spec.x
            y = spec.y

            if self.plot.x is None:
                self.plot.set_x(x)
            self.plot.update_series("live", y)

        self._unsub = self._bus.subscribe(TOPIC_SPECTRUM_ARRIVED, on_arrived)

    def unbind(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

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
