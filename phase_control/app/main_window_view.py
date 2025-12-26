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
from base_qt.views.registry.interfaces import IViewRegistry
from phase_control.app.main_window_vm import MainWindowViewModel


class MainWindowView(MainWindowViewBase[MainWindowViewModel]):
    """
    Shell main window:
    - Top row: Module label + combobox + Run/Reset (wie vorher)
    - Central: exactly one ViewKind.PAGE at a time, chosen via combobox
    """

    def __init__(self, vm: MainWindowViewModel, registry: IViewRegistry):
        self._pages: Dict[str, QWidget] = {}
        self._current_page_id: Optional[str] = None
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
        self._stack = QStackedWidget(self.central)
        root.addWidget(self._stack, 1)

    def bind(self) -> None:
        super().bind()

        self.vm.pages_changed.connect(self._rebuild_pages)
        self.vm.selected_page_changed.connect(self._show_page)

        self._module_box.currentIndexChanged.connect(self._on_combo_changed)
        self._btn_run.clicked.connect(self.vm.run_selected_module)
        self._btn_reset.clicked.connect(self.vm.reset_selected_module)

        self._rebuild_pages()
        if self.vm.selected_page_id:
            self._show_page(self.vm.selected_page_id)

    def unbind(self) -> None:
        try:
            self.vm.pages_changed.disconnect(self._rebuild_pages)
            self.vm.selected_page_changed.disconnect(self._show_page)
        except (TypeError, RuntimeError):
            pass

        try:
            self._module_box.currentIndexChanged.disconnect(self._on_combo_changed)
        except (TypeError, RuntimeError):
            pass

        try:
            self._btn_run.clicked.disconnect(self.vm.run_selected_module)
            self._btn_reset.clicked.disconnect(self.vm.reset_selected_module)
        except (TypeError, RuntimeError):
            pass

        super().unbind()

    # ---------------- internals ----------------

    @Slot()
    def _rebuild_pages(self) -> None:
        self._module_box.blockSignals(True)
        try:
            self._module_box.clear()
            for p in self.vm.pages:
                self._module_box.addItem(p.title, p.id)  # userData = page_id

            sel = self.vm.selected_page_id
            if sel is not None:
                idx = self._module_box.findData(sel)
                if idx >= 0:
                    self._module_box.setCurrentIndex(idx)
        finally:
            self._module_box.blockSignals(False)

    @Slot(int)
    def _on_combo_changed(self, _idx: int) -> None:
        page_id = self._module_box.currentData()
        if page_id is not None:
            self.vm.select_page(str(page_id))

    @Slot(str)
    def _show_page(self, page_id: str) -> None:
        # optional: unbind old page (stop subscriptions while hidden)
        if self._current_page_id is not None:
            old = self._pages.get(self._current_page_id)
            if old is not None and hasattr(old, "unbind"):
                try:
                    old.unbind()  # type: ignore[attr-defined]
                except Exception:
                    pass

        page = self._pages.get(page_id)
        if page is None:
            factory = self.vm.page_factory(page_id)
            page = factory()  # new page instance (first time)
            self._pages[page_id] = page
            self._stack.addWidget(page)

        self._stack.setCurrentWidget(page)
        self._current_page_id = page_id

        # optional: bind new page
        if hasattr(page, "bind"):
            try:
                page.bind()  # type: ignore[attr-defined]
            except Exception:
                pass
