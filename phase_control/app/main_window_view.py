# your_app/modules/shell/main_window_view.py
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from base_qt.views.bases.main_window_view_base import MainWindowViewBase
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.app.main_window_vm import MainWindowViewModel



class MainWindowView(MainWindowViewBase[MainWindowViewModel]):
    """
    Main window shell:
    - MenuBar is installed automatically by MainWindowViewBase via MENUBAR ViewSpec
    - Top row: module selector (always visible)
    - Central: tabs containing all ViewKind.PAGE views
    """

    def __init__(self, vm: MainWindowViewModel, registry: IViewRegistry):
        super().__init__(vm, registry, title="Phase Control")

    # ---------------- UI ----------------

    def build_ui(self) -> None:
        # Root layout in the central placeholder widget provided by the base class
        root = QVBoxLayout(self.central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Top selector row (replaces your .ui) -------------------------
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(8)
        
        self._module_label = QLabel("Module", self.central)
        self._module_box = QComboBox(self.central)
        self._btn_run = QPushButton("Run", self.central)
        self._btn_reset = QPushButton("Reset", self.central)

        # two equal columns
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        # ---- left column widget ----
        left = QWidget()
        left_lay = QHBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)
        left_lay.addWidget(self._module_label)
        left_lay.addWidget(self._module_box, 1)

        # ---- right column widget ----
        right = QWidget()
        right_lay = QHBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)
        right_lay.addWidget(self._btn_run)
        right_lay.addWidget(self._btn_reset)

        grid.addWidget(left, 0, 0)
        grid.addWidget(right, 0, 1)

        root.addLayout(grid)

        # --- Pages (tabs) ------------------------------------------------
        self._tabs = QTabWidget(self.central)
        root.addWidget(self._tabs, 1)

        for spec in self._registry.list():
            if spec.kind != ViewKind.PAGE:
                continue
            view: QWidget = spec.factory()
            self._tabs.addTab(view, spec.title)

    # ---------------- bindings ----------------

    def bind(self) -> None:
        super().bind()

        # Fill module dropdown once (expect VM provides module names)
        # Implement one of these in your ShellVM:
        # - get_modules() -> list[str]
        # - modules -> list[str]
        modules: list[str] = []
        if hasattr(self.vm, "get_modules"):
            modules = list(self.vm.get_modules())  # type: ignore[attr-defined]
        elif hasattr(self.vm, "modules"):
            modules = list(self.vm.modules)        # type: ignore[attr-defined]

        self._module_box.clear()
        self._module_box.addItems(modules)

        # UI -> VM (implement these methods in ShellVM)
        # - select_module(name: str)
        # - run_selected_module()
        # - reset_selected_module()
        if hasattr(self.vm, "select_module"):
            self._module_box.currentTextChanged.connect(self.vm.select_module)  # type: ignore[attr-defined]

        if hasattr(self.vm, "run_selected_module"):
            self._btn_run.clicked.connect(self.vm.run_selected_module)          # type: ignore[attr-defined]

        if hasattr(self.vm, "reset_selected_module"):
            self._btn_reset.clicked.connect(self.vm.reset_selected_module)      # type: ignore[attr-defined]

    def unbind(self) -> None:
        # Disconnect safely (VM methods may or may not exist)
        if hasattr(self.vm, "select_module"):
            try:
                self._module_box.currentTextChanged.disconnect(self.vm.select_module)  # type: ignore[attr-defined]
            except (TypeError, RuntimeError):
                pass

        if hasattr(self.vm, "run_selected_module"):
            try:
                self._btn_run.clicked.disconnect(self.vm.run_selected_module)  # type: ignore[attr-defined]
            except (TypeError, RuntimeError):
                pass

        if hasattr(self.vm, "reset_selected_module"):
            try:
                self._btn_reset.clicked.disconnect(self.vm.reset_selected_module)  # type: ignore[attr-defined]
            except (TypeError, RuntimeError):
                pass

        super().unbind()
