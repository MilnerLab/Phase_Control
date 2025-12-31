from base_core.framework.guard.guard import Guard
from base_qt.view_models.runnable_vm import EventBus, IUiDispatcher, RunnableVMBase
from phase_control.analysis_modules.randomize.engine import RandomizationEngine
from phase_control.core.models import Spectrum
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM


class RandomizationPageVM(RunnableVMBase):

    def __init__(self, engine_service: RandomizationEngine, ui: IUiDispatcher, bus: EventBus, plot: SpectrumPlotVM) -> None:
        super().__init__(engine_service, ui, bus)
        self.plot_vm = plot
    
    def set_rotation_speed(self, percent: int) -> None:
        engine = Guard.is_instance(self.engine, RandomizationEngine)
        engine.set_rotation_speed(percent)