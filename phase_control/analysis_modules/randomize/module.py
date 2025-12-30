from base_core.framework.modules import BaseModule
from base_qt.view_models.runnable_vm import IUiDispatcher
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.analysis_modules.randomize.engine import RandomizationEngine
from phase_control.analysis_modules.randomize.ui.randomization_page_view import RandomizationPageView
from phase_control.analysis_modules.randomize.ui.randomization_page_vm import RandomizationPageVM
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import ICpuTaskRunner
from phase_control.core.module import CoreModule
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from phase_control.io.rotator.interfaces import IRotatorController


class RandomizationModule(BaseModule):
    name = "spectrometer"
    requires = (AppModule, CoreModule,)  

    def register(self, c, ctx) -> None:
        
        c.register_singleton(RandomizationEngine, lambda c: RandomizationEngine(
            rotator_worker=c.get(IRotatorController),
            cpu=c.get(ICpuTaskRunner),
            ))
        
        c.register_factory(RandomizationPageVM, lambda c: RandomizationPageVM(c.get(RandomizationEngine), c.get(IUiDispatcher), ctx.event_bus, c.get(SpectrumPlotVM)))
        c.register_factory(RandomizationPageView, lambda c: RandomizationPageView(c.get(RandomizationPageVM)))

        view_reg = c.get(IViewRegistry)
        view_reg.register(ViewSpec(
            id="randomizer",
            title="Randomizer",
            kind=ViewKind.PAGE,
            factory=lambda: c.get(RandomizationPageView),
        ))

