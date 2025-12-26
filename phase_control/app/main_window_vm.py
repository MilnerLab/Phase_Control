from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal

from base_core.framework.events.event_bus import EventBus
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry


TOPIC_SHELL_RUN = "shell.run"
TOPIC_SHELL_RESET = "shell.reset"


@dataclass(frozen=True)
class PageItem:
    id: str
    title: str


class MainWindowViewModel(QObject):
    pages_changed = Signal()
    selected_page_changed = Signal(str)

    def __init__(self, registry: IViewRegistry, event_bus: EventBus) -> None:
        super().__init__()
        self._registry = registry
        self._bus = event_bus

        self._pages: List[PageItem] = []
        self._selected_id: Optional[str] = None

        self.reload_pages()

    @property
    def pages(self) -> List[PageItem]:
        return list(self._pages)

    @property
    def selected_page_id(self) -> Optional[str]:
        return self._selected_id

    def reload_pages(self) -> None:
        pages: List[PageItem] = []
        for spec in self._registry.list():
            if spec.kind == ViewKind.PAGE:
                pages.append(PageItem(id=spec.id, title=spec.title))

        self._pages = pages
        self.pages_changed.emit()

        if self._selected_id is None and self._pages:
            self.select_page(self._pages[0].id)

    def select_page(self, page_id: str) -> None:
        if self._selected_id == page_id:
            return
        self._selected_id = page_id
        self.selected_page_changed.emit(page_id)

    def page_factory(self, page_id: str) -> Callable[[], object]:
        # View bleibt dumm: sie bekommt nur die Factory und swapped dann Widgets
        spec = self._registry.get(page_id)
        return spec.factory

    # Buttons
    def run_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._bus.publish(TOPIC_SHELL_RUN, self._selected_id)

    def reset_selected_module(self) -> None:
        if self._selected_id is None:
            return
        self._bus.publish(TOPIC_SHELL_RESET, self._selected_id)

    def open_settings(self) -> None:
        pass

    def show_about(self) -> None:
        pass
