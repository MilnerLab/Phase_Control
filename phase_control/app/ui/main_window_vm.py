from __future__ import annotations

from argparse import OPTIONAL
from dataclasses import dataclass
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal

from base_core.framework.domain.interfaces import IRunnable
from base_core.framework.events.event_bus import EventBus
from base_qt.views.bases.view_base import ViewBase
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec



class MainWindowViewModel(QObject):
    selected_page_changed = Signal()

    def __init__(self, registry: IViewRegistry, event_bus: EventBus) -> None:
        super().__init__()
        self._registry = registry
        self._bus = event_bus

        self._page_specs: List[ViewSpec] = []
        self._selected_id: Optional[str] = None
        self._current_page: Optional[ViewBase] = None

        self._load_pages()
        
    @property
    def current_page(self) -> Optional[ViewBase]:
        return self._current_page
    
    def select_page(self, page_id: str) -> None:
        if self._selected_id == page_id:
            return
        self._selected_id = page_id
        self._current_page = next(s for s in self._page_specs if s.id == page_id).factory()
        self.selected_page_changed.emit()

    def run_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._get_vm().start()
        
    def stop_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._get_vm().stop()
        
    def reset_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._get_vm().reset()
        
    def _load_pages(self) -> None:
        pages: List[ViewSpec] = []
        for spec in self._registry.list():
            if spec.kind == ViewKind.PAGE:
                pages.append(spec)

        self._page_specs = pages

    def _get_vm(self) -> IRunnable:
        vm = self._current_page.vm
        if (vm is not None and isinstance(vm, IRunnable)):
            return vm
        else:
            raise ValueError("View Model is not IRunnable")