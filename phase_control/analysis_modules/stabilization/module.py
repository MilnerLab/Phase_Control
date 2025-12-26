# your_app/modules/spectrometer/module.py
from __future__ import annotations

from base_core.framework.modules import BaseModule
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.analysis_modules.stabilization.ui.stabiliation_page_VM import StabilizationPageVM
from phase_control.analysis_modules.stabilization.ui.stabilization_page_view import StabilizationPageView
from phase_control.app.module import AppModule
from phase_control.core.module import CoreModule
from phase_control.core.plotting.spectrum_plot_VM import PlotVM
from phase_control.io.frame_buffer import FrameBuffer


class StabilizationModule(BaseModule):
    name = "spectrometer"
    requires = (AppModule, CoreModule,)  

    def register(self, c, ctx) -> None:
        c.register_factory(StabilizationPageVM, lambda c: StabilizationPageVM(ctx.event_bus, c.get(FrameBuffer), c.get(PlotVM)))
        c.register_factory(StabilizationPageView, lambda c: StabilizationPageView(c.get(StabilizationPageVM)))

        view_reg = c.get(IViewRegistry)
        view_reg.register(ViewSpec(
            id="spectrometer",
            title="Spectrometer",
            kind=ViewKind.PAGE,
            factory=lambda: c.get(StabilizationPageView),
        ))

