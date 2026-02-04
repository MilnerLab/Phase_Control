from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDialog, QMenu, QVBoxLayout
from base_qt.views.bases.menu_view_base import MenuViewBase
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.app.ui.menu_bar_VM import MenuBarViewModel


from PySide6.QtGui import QAction

from phase_control.io.spectrometer.ui.spectrometer_settings_view import SpectrometerSettingsView

class MenuBarView(MenuViewBase[MenuBarViewModel]):
    @classmethod
    def id(cls) -> str:
        return "app.MenuBarView"

    def __init__(self, vm: MenuBarViewModel, registry: IViewRegistry):
        super().__init__(vm)
        self._registry = registry  # keep it

    def build_ui(self) -> None:
        super().build_ui()

        # --- Rotator menu ---------------------------------------------------
        self._rotator_menu = self.addMenu("Rotator")
        self._act_rotator_settings = QAction("Open settings", self)
        self._act_rotator_settings.setShortcut("Ctrl+Alt+R")
        self._rotator_menu.addAction(self._act_rotator_settings)

        self._act_rotator_restart = QAction("Restart", self)
        self._act_rotator_restart.setShortcut("Ctrl+Shift+R")
        self._rotator_menu.addAction(self._act_rotator_restart)

        # --- Spectrometer menu ---------------------------------------------
        self._spectrometer_menu = self.addMenu("Spectrometer")

        self._act_spec_settings = QAction("Open settings", self)
        self._act_spec_settings.setShortcut("Ctrl+Alt+S")
        self._spectrometer_menu.addAction(self._act_spec_settings)

        # --- Help menu ------------------------------------------------------
        self._help_menu = self.addMenu("Help")
        self._act_about = QAction("About", self)
        self._help_menu.addAction(self._act_about)

    def bind(self) -> None:
        super().bind()

        self._act_spec_settings.triggered.connect(self._open_spectrometer_settings)

    def _open_spectrometer_settings(self) -> None:
        # Create view via registry
        view = self._registry.get(SpectrometerSettingsView.id())  # matches SpectrometerSettingsView.id()

        # Show as a standalone window (Qt minimal version)
        dlg = QDialog(self)
        dlg.setWindowTitle("Spectrometer Settings")
        dlg.setModal(False)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(view)

        dlg.resize(420, 320)
        dlg.show()

        # keep reference so it doesn't get GC'd
        if not hasattr(self, "_open_windows"):
            self._open_windows = []
        self._open_windows.append(dlg)

