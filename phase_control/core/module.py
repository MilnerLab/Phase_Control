# your_app/modules/spectrometer/module.py
from __future__ import annotations

from base_core.framework.modules import BaseModule
from phase_control.app.module import AppModule
from phase_control.core.plotting.spectrum_plot_VM import PlotVM


class CoreModule(BaseModule):
    name = "core"
    requires = (AppModule,)

    def register(self, c, ctx) -> None:
        
        c.register_factory(PlotVM, lambda c: PlotVM())
        