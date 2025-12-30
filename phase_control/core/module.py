# your_app/modules/spectrometer/module.py
from __future__ import annotations
from re import I

from base_core.framework.modules import BaseModule
from phase_control.app.module import AppModule
from phase_control.core.plotting.spectrum_plot_VM import SpectrumPlotVM
from base_qt.app.interfaces import IUiDispatcher
from phase_control.io.spectrometer.interfaces import IFrameBuffer



class CoreModule(BaseModule):
    name = "core"
    requires = (AppModule,)

    def register(self, c, ctx) -> None:
        
        c.register_factory(SpectrumPlotVM, lambda c: SpectrumPlotVM(c.get(IUiDispatcher), ctx.event_bus, c.get(IFrameBuffer)))
        