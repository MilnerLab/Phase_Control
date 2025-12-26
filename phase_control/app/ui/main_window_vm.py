from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal

from base_core.framework.events.event_bus import EventBus
from base_qt.views.bases.view_base import ViewBase
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.app.events import TOPIC_SHELL_RESET, TOPIC_SHELL_RUN



class MainWindowViewModel(QObject):
    selected_page_changed = Signal(ViewBase)

    def __init__(self, registry: IViewRegistry, event_bus: EventBus) -> None:
        super().__init__()
        self._registry = registry
        self._bus = event_bus

        self._pages: List[ViewSpec] = []
        self._selected_id: Optional[str] = None

        self._load_pages()
        
    @property
    def pages(self) -> List[ViewSpec]:
        return self._pages
    
    def select_page(self, page_id: str) -> None:
        if self._selected_id == page_id:
            return
        self._selected_id = page_id
        page = next(s for s in self._pages if s.id == page_id)
        self.selected_page_changed.emit(page.factory())

    def run_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._bus.publish(TOPIC_SHELL_RUN, self._selected_id)

    def reset_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._bus.publish(TOPIC_SHELL_RESET, self._selected_id)
    
    def _load_pages(self) -> None:
        pages: List[ViewSpec] = []
        for spec in self._registry.list():
            if spec.kind == ViewKind.PAGE:
                pages.append(spec)

        self._pages = pages
