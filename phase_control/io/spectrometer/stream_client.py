# phase_control/io/stream_client.py
"""
Low-level stream client for the 32-bit acquisition process.

Responsibilities:
- start the 32-bit Python process running `spm_002.json_stream_server`
- read the initial 'meta' JSON object
- provide an iterator over 'frame' JSON objects
- stop/terminate the process when done

This module does NOT:
- start any threads
- manage any buffers or queues
"""

from __future__ import annotations

import json
import subprocess
from typing import Iterator, Optional

from phase_control.io.spectrometer.models import StreamFrame, StreamMeta
from spm_002.config import PYTHON32_PATH


class SpectrometerStreamClient:
    """
    Stream client for the JSON output of the 32-bit acquisition process.

    Typical usage:

        client = SpectrometerStreamClient()
        meta = client.start()

        for frame in client.frames():
            ...

        client.stop()

    or as a context manager:

        with SpectrometerStreamClient() as client:
            meta = client.start()
            for frame in client.frames():
                ...
    """

    def __init__(self, python32_path: Optional[str] = None) -> None:
        self.python32_path = str(python32_path or PYTHON32_PATH)
        self._proc: Optional[subprocess.Popen[str]] = None
        self._meta: Optional[StreamMeta] = None

    # ------------------------------------------------------------------ #
    # Context manager
    # ------------------------------------------------------------------ #

    def __enter__(self) -> "SpectrometerStreamClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    @property
    def meta(self) -> StreamMeta:
        """
        Static meta information. Only valid after start() has been called.
        """
        if self._meta is None:
            raise RuntimeError("StreamMeta not available. Did you call start()?")

        return self._meta

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> StreamMeta:
        """
        Start the 32-bit acquisition process and read the 'meta' frame.

        Returns
        -------
        StreamMeta
            Static meta information describing the stream.
        """
        if self._proc is not None:
            raise RuntimeError("Acquisition process is already running.")

        proc = subprocess.Popen(
            [self.python32_path, "-m", "spm_002.json_stream_server"],
            stdout=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        self._proc = proc

        if proc.stdout is None:
            raise RuntimeError("Failed to open stdout from acquisition process.")

        # Read one line (meta)
        meta_line = proc.stdout.readline()
        if not meta_line:
            stderr_msg = ""
            if proc.stderr is not None:
                stderr_msg = proc.stderr.read()
            raise RuntimeError(
                "Acquisition process terminated before sending meta data.\n"
                f"stderr:\n{stderr_msg}"
            )

        meta_raw = json.loads(meta_line)
        if meta_raw.get("type") != "meta":
            raise RuntimeError(f"Expected meta frame, got: {meta_raw!r}")

        self._meta = StreamMeta(
            device_index=meta_raw["device_index"],
            num_pixels=meta_raw["num_pixels"],
            wavelengths=meta_raw["wavelengths"],  # may be None
        )

        return self._meta

    def frames(self) -> Iterator[StreamFrame]:
        """
        Iterate over frames from the acquisition process.

        This is a blocking iterator. It should normally be called from a
        background thread. It does NOT do any buffering itself.
        """
        proc = self._proc
        if proc is None or proc.stdout is None:
            raise RuntimeError(
                "Acquisition process is not running. Call start() first."
            )

        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue

            try:
                frame_raw = json.loads(line)
            except json.JSONDecodeError:
                continue

            if frame_raw.get("type") != "frame":
                # Ignore 'meta' or other messages.
                continue

            yield StreamFrame(
                timestamp=frame_raw["timestamp"],
                device_index=frame_raw["device_index"],
                counts=frame_raw["counts"],
            )

    def stop(self) -> None:
        """
        Stop the acquisition process if it is still running.
        """
        proc = self._proc
        self._proc = None

        if proc is None:
            return

        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
