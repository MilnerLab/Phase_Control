# your_app/modules/spectrometer/spectrometer_page_vm.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from base_core.framework.events.event_bus import EventBus
from base_qt.view_models.runnable_vm import RunnableVMBase
from phase_control.analysis_modules.stabilization.config import AnalysisConfig
from phase_control.analysis_modules.stabilization.engine import AnalysisEngine
from phase_control.core.models import Spectrum
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from base_qt.app.interfaces import IUiDispatcher


class StabilizationPageVM(RunnableVMBase):
    
    def __init__(self, engine_service: AnalysisEngine, ui: IUiDispatcher, bus: EventBus, plot: SpectrumPlotVM, config: AnalysisConfig) -> None:
        super().__init__(engine_service, ui, bus)
        self.plot_vm = plot
        self._config = config

    def get_phase_pi(self) -> float:
        return float(self._config.phase_pi)

    def set_phase_pi(self, value: float) -> None:
        self._config.phase_pi = float(value)
        
    def start(self):
        self._engine.set_on_result(self._on_new_result)
        super().start()
    
    def stop(self):
        super().stop()
        self._engine.set_on_result(None)
    
    def _on_new_result(self, spectra: dict[str, Spectrum]) -> None:
        for key, spec in spectra.items():

            y = spec.intensity.copy()

            self.plot_vm.apply_spectrum([], y, key)  
 
