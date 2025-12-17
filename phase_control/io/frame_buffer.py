# phase_control/io/frame_buffer.py
from __future__ import annotations

import threading
from typing import Optional

from phase_control.core.models import Spectrum
from phase_control.io.interfaces import FrameBufferProtocol
from phase_control.io.models import StreamFrame, StreamMeta


class FrameBuffer(FrameBufferProtocol):
    """
    Thread-safe buffer holding the most recent StreamFrame.

    Semantics:
      - `update(frame)` overwrites the previously stored frame.
      - `get_latest()` returns a converted Spectrum **at most once**
        per underlying frame. If the latest frame has already been
        consumed, `get_latest()` returns None.

    This ensures that slow consumers do not process the same frame
    repeatedly, while still always getting the newest data.
    """

    def __init__(self, meta: StreamMeta) -> None:
        self._lock = threading.Lock()
        self._latest: Optional[StreamFrame] = None
        self.meta: StreamMeta = meta

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update(self, frame: StreamFrame) -> None:
        """
        Store a new frame, overwriting any previous one.

        Typically called from a background thread that iterates over
        SpectrometerStreamClient.frames().
        """
        with self._lock:
            self._latest = frame

    def get_latest(self) -> Spectrum | None:
        """
        Return the newest Spectrum since the last call, or None if
        there is nothing new.

        This method is thread-safe and may be called from the UI thread.
        """
        with self._lock:
            frame = self._latest
            self._latest = None

        if frame is None:
            return None

        return self._to_spectrum(frame)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _to_spectrum(self, frame: StreamFrame) -> Spectrum:
        """
        Convert a StreamFrame into a Spectrum instance using the meta
        information (wavelength axis).
        """
        if self.meta.wavelengths is None:
            raise ValueError("Wavelengths not available in stream meta data.")

        return Spectrum.from_raw_data(self.meta.wavelengths, frame.counts)
