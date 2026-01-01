from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from base_qt.views.bases.menu_view_base import MenuViewBase
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.app.ui.menu_bar_VM import MenuBarViewModel


class MenuBarView(MenuViewBase[MenuBarViewModel]):
    @classmethod
    def id(cls) -> str:
        return "app.MenuBarView"
    def __init__(self, vm: MenuBarViewModel, registry: IViewRegistry):
        super().__init__(vm)
        
    def build_ui(self) -> None:
        super().build_ui()

        # --- Rotator menu ---------------------------------------------------
        self._rotator_menu = self.addMenu("Rotator")

        self._act_rotator_settings = QAction("Open settings", self)
        # optional shortcut
        self._act_rotator_settings.setShortcut("Ctrl+Alt+R")
        self._rotator_menu.addAction(self._act_rotator_settings)

        self._act_rotator_restart = QAction("Restart", self)
        # optional shortcut
        self._act_rotator_restart.setShortcut("Ctrl+Shift+R")
        self._rotator_menu.addAction(self._act_rotator_restart)

        # --- Help menu ------------------------------------------------------
        self._help_menu = self.addMenu("Help")
        self._act_about = QAction("About", self)
        self._help_menu.addAction(self._act_about)

    def bind(self) -> None:
        super().bind()

        # If your VM exposes commands/callables, wire them here.
        # Example (adapt names to your VM):
        # self._act_rotator_settings.triggered.connect(self.vm.open_rotator_settings)
        # self._act_rotator_restart.triggered.connect(self.vm.restart_rotator)
