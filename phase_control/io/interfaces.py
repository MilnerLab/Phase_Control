# phase_control/io/interfaces.py
from __future__ import annotations

from typing import Any, Protocol


class FrameBufferProtocol(Protocol):
    """
    Minimal interface for an object that provides live spectrometer frames.

    The concrete implementation can store arbitrary frame types
    (e.g. StreamFrame, Spectrum), so we keep the return type as Any
    and let each module interpret it.
    """

    def get_latest(self) -> Any:
        """
        Return the latest frame or None if nothing is available yet.
        """
        ...
