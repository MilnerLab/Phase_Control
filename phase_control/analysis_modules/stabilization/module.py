# phase_control/modules/stabilization/module.py
from __future__ import annotations

from base_core.framework.app import AppContext
from base_core.framework.di import Container
from base_core.framework.modules import BaseModule
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.app.module import AppModule


class StabilizationModule(BaseModule):
    name = "shell"
    requires = (AppModule)

    def register(self, c: Container, ctx: AppContext) -> None:
        
        # --- Shell VM + MenuBar -------------------------------------------
        c.register_factory(MainWindowViewModel, lambda c: MainWindowViewModel())
        c.register_factory(MenuBarViewModel, lambda c: MenuBarViewModel())
        
        # If you want exactly one menubar instance, you can register it as singleton.
        c.register_singleton(MenuBarView, lambda c: MenuBarView(c.get(MenuBarViewModel)))

        # Register MENUBAR view spec (MainWindowViewBase will pick this up automatically)
        reg = c.get(IViewRegistry)
        reg.register(
            ViewSpec(
                id="stabilization.view",
                title="Phase Stabilization",
                kind=ViewKind.PAGE,
                factory=lambda: c.get(MenuBarView),
                order=0,
            )
        )

