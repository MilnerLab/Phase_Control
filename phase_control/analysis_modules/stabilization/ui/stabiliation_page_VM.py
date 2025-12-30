# your_app/modules/spectrometer/spectrometer_page_vm.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from base_core.framework.events.event_bus import EventBus
from base_qt.view_models.runnable_vm import RunnableVMBase
from phase_control.analysis_modules.stabilization.engine import AnalysisEngine
from phase_control.core.models import Spectrum
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from base_qt.app.interfaces import IUiDispatcher


TOPIC_SPECTRUM_ARRIVED = "io.spectrum_arrived"


class StabilizationPageVM(RunnableVMBase):
    """
    Qt VM (ok): subscribes to EventBus and emits PlotVM updates.
    Services stay Qt-free; VM does dispatch via Signals/PlotVM.
    """

    status_changed = Signal(str)

    def __init__(self, engine_service: AnalysisEngine, ui: IUiDispatcher, bus: EventBus, plot: SpectrumPlotVM) -> None:
        super().__init__(engine_service, ui, bus)
        self.plot_vm = plot
        
        self._snap_idx = 0

    def start(self):
        self._engine.set_on_result(self._on_new_result)
        super().start()
    
    def stop(self):
        super().stop()
        self._engine.set_on_result(None)
    
    def _on_new_result(self, spectra: dict[str, Spectrum]) -> None:
        for key, spec in spectra.items():

            x = spec.wavelengths_nm.copy()
            y = spec.intensity.copy()

            self.plot_vm.apply_spectrum(x, y, key)  
 
        
    @Slot()
    def snapshot(self) -> None:
        spec = self._buffer.get_latest()
        if spec is None:
            self.status_changed.emit("No spectrum yet.")
            return

        x = spec.wavelengths_nm
        y = spec.intensity

        if self.plot_vm.x is None:
            self.plot_vm.set_x(x)

        key = f"snap_{self._snap_idx}"
        self._snap_idx += 1
        self.plot_vm.update_series(key, y)

    @Slot()
    def clear_snapshots(self) -> None:
        # keep live, remove everything else
        # simplest: rebuild: clear then re-add live if present
        live = None
        if "live" in getattr(self.plot_vm, "_series", {}):
            live = self.plot_vm._series["live"]  # if you don't like this, keep live in VM
        self.plot_vm.clear()
        if live is not None and self.plot_vm.x is not None:
            self.plot_vm.update_series("live", live)
