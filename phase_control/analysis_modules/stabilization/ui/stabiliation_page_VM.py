# your_app/modules/spectrometer/spectrometer_page_vm.py
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot
import numpy as np

from base_core.framework.events.event_bus import EventBus
from base_core.math.models import Angle
from base_qt.view_models.runnable_vm import RunnableVMBase
from phase_control.analysis_modules.stabilization.config import AnalysisConfig
from phase_control.analysis_modules.stabilization.engine import AnalysisEngine
from phase_control.core.models import Spectrum
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from base_qt.app.interfaces import IUiDispatcher


class StabilizationPageVM(RunnableVMBase):
    
    def __init__(self, engine_service: AnalysisEngine, ui: IUiDispatcher, bus: EventBus, plot: SpectrumPlotVM) -> None:
        super().__init__(engine_service, ui, bus)
        self.plot_vm = plot

    def get_phase_pi(self) -> float:
        return float(self._engine.target_phase / np.pi)

    def set_phase_pi(self, value: float) -> None:
        self._engine.target_phase = Angle(float(value) * np.pi)
        
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
 
