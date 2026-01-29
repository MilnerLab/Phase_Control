from __future__ import annotations

from PySide6.QtCore import Signal

from base_core.framework.events import EventBus
from base_qt.view_models.runnable_vm import IUiDispatcher, RunnableVMBase
from phase_control.analysis_modules.envelope.config import EnvelopeSignalGeneratorConfig
from phase_control.analysis_modules.envelope.domain.enums import EnvelopeMode
from phase_control.analysis_modules.envelope.engine import EnvelopeEngine
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM

class EnvelopePageVM(RunnableVMBase):
    mode_changed = Signal(object)  # EnvelopeViewMode

    def __init__(
        self,
        engine_service: EnvelopeEngine,
        ui: IUiDispatcher,
        bus: EventBus,
        plot: SpectrumPlotVM,
        config: EnvelopeSignalGeneratorConfig
    ) -> None:
        super().__init__(engine_service, ui, bus)
        self.plot_vm = plot
        self.plot_vm.normalize_spectrum = False
        self._config = config

    # new
    @property
    def mode(self) -> EnvelopeMode:
        return self._config.mode

    @mode.setter
    def mode(self, m: EnvelopeMode) -> None:
        if m == self._config.mode:
            return
        self._config.mode = m
        self.mode_changed.emit(self._config.mode)
