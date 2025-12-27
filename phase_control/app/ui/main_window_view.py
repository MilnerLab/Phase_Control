from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from base_qt.views.bases.main_window_view_base import MainWindowViewBase
from base_qt.views.bases.view_base import ViewBase
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.app.ui.main_window_vm import MainWindowViewModel


class MainWindowView(MainWindowViewBase[MainWindowViewModel]):
    def __init__(self, vm: MainWindowViewModel, registry: IViewRegistry):
        self._current_page: Optional[ViewBase] = None
        super().__init__(vm, registry, title="Phase Control")

    def build_ui(self) -> None:
        root = QVBoxLayout(self.central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Top selector row -------------------------------------------
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

        left = QWidget(self.central)
        left_lay = QHBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(8)
        left_lay.addWidget(self._module_label)
        left_lay.addWidget(self._module_box, 1)

        right = QWidget(self.central)
        right_lay = QHBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(8)
        right_lay.addWidget(self._btn_run)
        right_lay.addWidget(self._btn_reset)

        grid.addWidget(left, 0, 0)
        grid.addWidget(right, 0, 1)
        root.addLayout(grid)
        
        # --- Single-page host -------------------------------------------
        self._page_host = QWidget(self.central)
        self._page_host_layout = QVBoxLayout(self._page_host)
        self._page_host_layout.setContentsMargins(0, 0, 0, 0)
        self._page_host_layout.setSpacing(0)

        root.addWidget(self._page_host, 1)


    def bind(self) -> None:
        super().bind()
        self._fill_combo_box()

        self.connect_binding(self.vm.selected_page_changed, self._show_page)

        self.connect_binding(self._module_box.currentIndexChanged, self._on_combo_changed)
        self.connect_binding(self._btn_run.clicked, self.vm.run_selected_module)
        self.connect_binding(self._btn_reset.clicked, self.vm.reset_selected_module)

    # ---------------- internals ----------------

    @Slot(int)
    def _on_combo_changed(self, _idx: int) -> None:
        page_id = self._module_box.currentData()
        if page_id is not None:
            self.vm.select_page(str(page_id))

    @Slot(ViewBase)
    def _show_page(self, page: ViewBase) -> None:
        old = self._current_page
        if old is not None:
            self._page_host_layout.removeWidget(old)
            old.close()
            self._current_page = None

        page.setParent(self._page_host)
        self._page_host_layout.addWidget(page)
        self._current_page = page

    def _fill_combo_box(self):
        self._module_box.blockSignals(True)
        try:
            self._module_box.clear()
            self._module_box.addItem("", "test") 
            for spec in self.vm.pages:
                self._module_box.addItem(spec.title, spec.id) 

        finally:
            self._module_box.blockSignals(False)
            
    def closeEvent(self, event):
        if self._current_page is not None:
            self._current_page.close()
        return super().closeEvent(event)