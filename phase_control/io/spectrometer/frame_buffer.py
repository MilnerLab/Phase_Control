# phase_control/io/frame_buffer.py
from __future__ import annotations

from typing import Optional

from phase_control.core.models import Spectrum
from phase_control.io.interfaces import IFrameBuffer
from phase_control.io.models import StreamFrame, StreamMeta
from base_core.framework.concurrency.buffer import Buffer


class FrameBuffer(IFrameBuffer, Buffer[StreamFrame]):
    _meta: Optional[StreamMeta] = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def set_meta_data(self,  meta: StreamMeta):
        self._meta = meta
        
    def get_latest(self) -> Spectrum | None:
        
        if self._meta is None:
            raise RuntimeError("Meta data has to be initialized.")
        
        frame = self.get()
        if  frame is None:
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
        if self._meta.wavelengths is None:
            raise ValueError("Wavelengths not available in stream meta data.")

        return Spectrum.from_raw_data(self._meta.wavelengths, frame.counts)
