# phase_control/io/interfaces.py
from __future__ import annotations

from typing import Any, Protocol

from phase_control.core.models import Spectrum
from phase_control.io.spectrometer.models import StreamMeta


class IFrameBuffer(Protocol):
    """
    Minimal interface for an object that provides live spectrometer frames.

    The concrete implementation can store arbitrary frame types
    (e.g. StreamFrame, Spectrum), so we keep the return type as Any
    and let each module interpret it.
    """
    
    def set_meta_data(self,  meta: StreamMeta): ...

    def get_latest(self) -> Spectrum: ...
