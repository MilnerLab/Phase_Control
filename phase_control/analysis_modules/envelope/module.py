from base_core.framework.modules import BaseModule
from base_qt.view_models.runnable_vm import IUiDispatcher
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.analysis_modules.envelope.config import EnvelopeSignalGeneratorConfig
from phase_control.analysis_modules.envelope.engine import EnvelopeEngine
from phase_control.analysis_modules.envelope.ui.envelope_page_view import EnvelopePageView
from phase_control.analysis_modules.envelope.ui.envelope_page_vm import EnvelopePageVM
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import ICpuTaskRunner
from phase_control.core.module import CoreModule
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.spectrometer.interfaces import IFrameBuffer


class EnvelopeModule(BaseModule):
    name = "stabilization"
    requires = (AppModule, CoreModule,)  

    def register(self, c, ctx) -> None:
        c.register_singleton(EnvelopeSignalGeneratorConfig, lambda c: EnvelopeSignalGeneratorConfig())
        c.register_singleton(EnvelopeEngine, lambda c: EnvelopeEngine(
            config=c.get(EnvelopeSignalGeneratorConfig),
            buffer=c.get(IFrameBuffer),
            rotator_worker=c.get(IRotatorController),
            bus=ctx.event_bus,
            cpu=c.get(ICpuTaskRunner),
            ))
        
        c.register_factory(EnvelopePageVM, lambda c: EnvelopePageVM(
            c.get(EnvelopeEngine),
            c.get(IUiDispatcher),
            ctx.event_bus,
            c.get(SpectrumPlotVM),
            c.get(EnvelopeSignalGeneratorConfig)))
        
        c.register_factory(EnvelopePageView, lambda c: EnvelopePageView(c.get(EnvelopePageVM)))
        
        view_reg = c.get(IViewRegistry)
        view_reg.register(ViewSpec(
            id=EnvelopePageView.id(),
            title="Envelope",
            kind=ViewKind.PAGE,
            factory=lambda: c.get(EnvelopePageView),
        ))
        
        
        