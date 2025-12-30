# your_app/modules/spectrometer/module.py
from __future__ import annotations

from base_core.framework.modules import BaseModule
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.analysis_modules.stabilization.config import AnalysisConfig
from phase_control.analysis_modules.stabilization.engine import AnalysisEngine
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.analysis_modules.stabilization.ui.stabilization_page_view import StabilizationPageView
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import ICpuTaskRunner
from phase_control.core.module import CoreModule
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.spectrometer.interfaces import IFrameBuffer
from base_qt.app.interfaces import IUiDispatcher


class StabilizationModule(BaseModule):
    name = "spectrometer"
    requires = (AppModule, CoreModule,)  

    def register(self, c, ctx) -> None:
        
        c.register_singleton(AnalysisConfig, lambda c: AnalysisConfig())
        c.register_singleton(AnalysisEngine, lambda c: AnalysisEngine(
            config=c.get(AnalysisConfig),
            buffer=c.get(IFrameBuffer),
            rotator_worker=c.get(IRotatorController),
            bus=ctx.event_bus,
            cpu=c.get(ICpuTaskRunner),
            ))
        
        c.register_factory(StabilizationPageVM, lambda c: StabilizationPageVM(c.get(AnalysisEngine), c.get(IUiDispatcher), ctx.event_bus, c.get(SpectrumPlotVM)))
        c.register_factory(StabilizationPageView, lambda c: StabilizationPageView(c.get(StabilizationPageVM)))

        view_reg = c.get(IViewRegistry)
        view_reg.register(ViewSpec(
            id="stabilization",
            title="Stabilization",
            kind=ViewKind.PAGE,
            factory=lambda: c.get(StabilizationPageView),
        ))

