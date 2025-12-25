from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from base_core.framework.concurrency.models import StreamHandle
from base_core.framework.events import EventBus
from phase_control.core.services.service_base import ServiceBase
from phase_control.io.frame_buffer import FrameBuffer
from phase_control.io.stream_client import SpectrometerStreamClient

from base_core.framework.concurrency.interfaces import ITaskRunner


TOPIC_SPECTRUM_ARRIVED = "io.spectrum_arrived"
TOPIC_ACQ_ERROR = "io.acquisition_error"


@dataclass(frozen=True)
class SpectrumArrived:
    timestamp: float
    device_index: int


class SpectrometerAcquisitionService(ServiceBase):
    def __init__(
        self,
        io: ITaskRunner,
        bus: EventBus,
        buffer: FrameBuffer,
        client: SpectrometerStreamClient,
    ) -> None:
        super().__init__()
        self._io = io
        self._bus = bus
        self._buffer = buffer
        self._client = client

        self._lock = threading.RLock()
        self._handle: Optional[StreamHandle] = None

    def start(self) -> None:
        with self._lock:
            if self.is_running:
                return

            # start stream in IO worker
            try:
                self._handle = self._io.stream(
                    self._producer,
                    on_item=self._on_frame,
                    on_error=self._on_error,
                    on_complete=self._on_complete,
                    key="io.spectrometer_stream",
                    cancel_previous=True,
                    drop_outdated=True,
                )
            except BaseException:
                # state stays STOPPED if we fail before super().start()
                raise

            super().start()

    def stop(self) -> None:
        with self._lock:
            if not self.is_running:
                return

            # cooperative stop (best-effort)
            handle = self._handle
            self._handle = None

            # Force-stop the subprocess so frames() unblocks quickly. :contentReference[oaicite:5]{index=5}
            self._client.stop()

            if handle is not None:
                handle.stop()

            super().stop()

    def reset(self) -> None:
        self.stop()
        self.start()

    # ---------------- internals ----------------

    def _producer(self, stop: threading.Event):
        """
        Runs in IO worker thread. Must not touch UI.
        """
        meta = self._client.start()  # starts subprocess + reads meta :contentReference[oaicite:6]{index=6}
        self._buffer.set_meta_data(meta)  # required for get_latest() :contentReference[oaicite:7]{index=7}

        try:
            for frame in self._client.frames():  # blocking iterator :contentReference[oaicite:8]{index=8}
                if stop.is_set():
                    break
                yield frame
        finally:
            self._client.stop()  # ensure process is terminated :contentReference[oaicite:9]{index=9}

    def _on_frame(self, frame) -> None:
        """
        Called from worker thread (TaskRunner). Keep it short.
        """
        # NOTE: Buffer API assumed to be `.set(frame)` (FrameBuffer inherits Buffer). :contentReference[oaicite:10]{index=10}
        # If your Buffer uses another name (e.g. put/update), change ONLY this line.
        self._buffer.set(frame)

        # Trigger only (no heavy work here!)
        self._bus.publish(
            TOPIC_SPECTRUM_ARRIVED,
            SpectrumArrived(timestamp=frame.timestamp, device_index=frame.device_index),
        )

    def _on_error(self, e: BaseException) -> None:
        self._bus.publish(TOPIC_ACQ_ERROR, e)
        # keep state consistent
        with self._lock:
            self._handle = None
            super().stop()

    def _on_complete(self) -> None:
        with self._lock:
            self._handle = None
            super().stop()
