# your_app/modules/shell/module.py
from __future__ import annotations

from base_core.framework.app import AppContext
from base_core.framework.di import Container
from base_core.framework.modules import BaseModule
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from base_qt.views.registry.view_registry import ViewRegistry
from phase_control.app.main_window_view import MainWindowView
from phase_control.app.main_window_vm import MainWindowViewModel
from phase_control.app.menu_bar_view import MenuBarViewModel
from phase_control.app.menu_bar_vm import MenuBarView


class AppModule(BaseModule):
    """
    Shell module:
    - provides the global ViewRegistry
    - registers the app menu bar (MENUBAR ViewSpec)
    - registers the app main window (factory)
    """

    name = "shell"
    requires = ()

    def register(self, c: Container, ctx: AppContext) -> None:
        # --- Registry (singleton) ------------------------------------------
        c.register_singleton(IViewRegistry, lambda c: ViewRegistry())

        # --- Shell VM + MenuBar -------------------------------------------
        c.register_factory(MainWindowViewModel, lambda c: MainWindowViewModel())
        c.register_factory(MenuBarViewModel, lambda c: MenuBarViewModel())
        
        # If you want exactly one menubar instance, you can register it as singleton.
        c.register_singleton(MenuBarView, lambda c: MenuBarView(c.get(MenuBarViewModel)))

        # Register MENUBAR view spec (MainWindowViewBase will pick this up automatically)
        reg = c.get(IViewRegistry)
        reg.register(
            ViewSpec(
                id="shell.menubar",
                title="MenuBar",
                kind=ViewKind.MENUBAR,
                factory=lambda: c.get(MenuBarView),
                order=0,
            )
        )

        # --- Main window ---------------------------------------------------
        c.register_factory(MainWindowView, lambda c: MainWindowView(
            vm=c.get(MainWindowViewModel),
            registry=c.get(IViewRegistry),
        ))

    def start(self, c: Container, ctx: AppContext) -> None:
        # Nothing required here for the shell itself.
        # If you add global hotkeys, background services etc., start them here.
        return None

    def stop(self, c: Container, ctx: AppContext) -> None:
        # Nothing required here for the shell itself.
        return None
