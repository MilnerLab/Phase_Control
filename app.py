# app.py (at repo root, e.g. next to phase_control/)
from __future__ import annotations

import threading

from phase_control.io import SpectrometerStreamClient, FrameBuffer
from phase_control.modules import ModuleContext
from phase_control.ui.main_window import run_main_window


def _acquisition_loop(
    client: SpectrometerStreamClient,
    buffer: FrameBuffer,
    stop_event: threading.Event,
) -> None:
    """
    Background loop that pulls frames from the 32-bit process
    and feeds them into the FrameBuffer.
    """
    try:
        for frame in client.frames():
            if stop_event.is_set():
                break
            buffer.update(frame)
    finally:
        # When we exit the loop, the context manager in main() will
        # take care of stopping the client process.
        pass


def main() -> None:
    stop_event = threading.Event()

    # Start 32-bit acquisition process and stream client
    with SpectrometerStreamClient() as client:
        meta = client.start()
        buffer = FrameBuffer(meta)

        # Background thread to fill the buffer
        worker = threading.Thread(
            target=_acquisition_loop,
            args=(client, buffer, stop_event),
            daemon=True,
        )
        worker.start()

        # Create module context and run the global main window
        context = ModuleContext(buffer=buffer)
        run_main_window(context, stop_event)

        # UI has exited -> signal worker to stop and wait
        stop_event.set()
        worker.join(timeout=2.0)


if __name__ == "__main__":
    main()
