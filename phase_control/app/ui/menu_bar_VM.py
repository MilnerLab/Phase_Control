
from PySide6.QtCore import QObject


class MenuBarViewModel(QObject):
    """
    Minimal shell-level VM interface.
    Implement these methods in your real ShellVM.
    """
    def open_settings(self) -> None: ...
    def show_about(self) -> None: ...
