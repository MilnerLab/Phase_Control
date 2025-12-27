from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from base_qt.views.bases.menu_view_base import MenuViewBase
from phase_control.app.ui.menu_bar_VM import MenuBarViewModel

class MenuBarView(MenuViewBase[MenuBarViewModel]):
    """
    Extends the base menubar:
    - keeps default File -> Exit from MenuViewBase
    - adds File -> Settings
    - adds Help -> About
    """

    def build_file_menu(self, menu: QMenu) -> None:
        # Insert actions before the default Exit action
        self._act_settings = QAction("Settings", self)
        self._act_settings.setShortcut("Ctrl+,")
        menu.addAction(self._act_settings)

    def build_ui(self) -> None:
        super().build_ui()

        # Extra menus beyond File
        self._help_menu = self.addMenu("Help")
        self._act_about = QAction("About", self)
        self._help_menu.addAction(self._act_about)

    def bind(self) -> None:
        super().bind()
        #self._act_settings.triggered.connect(self.vm.open_settings)
        #self._act_about.triggered.connect(self.vm.show_about)

    def unbind(self) -> None:
        # disconnect safely
        try:
            self._act_settings.triggered.disconnect(self.vm.open_settings)
        except (TypeError, RuntimeError):
            pass
        try:
            self._act_about.triggered.disconnect(self.vm.show_about)
        except (TypeError, RuntimeError):
            pass
        super().unbind()