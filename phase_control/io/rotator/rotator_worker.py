# rotator_worker.py
import threading
from base_core.framework.concurrency.task_runner import ITaskRunner
from base_core.math.models import Angle
from elliptec.base.enums import StatusCode
from elliptec.elliptec_ell14 import Rotator
from phase_control.io.rotator.interfaces import IRotatorController


class RotatorController(IRotatorController):
    def __init__(self, port: str, io: ITaskRunner):
        self._port = port
        self._runner = io
        self._rotator: Rotator | None = None

        self._busy = threading.Event()
        self._busy_lock = threading.Lock()
        self._busy_gen = 0  # increments for each scheduled command

    @property
    def is_busy(self) -> bool:
        # IMPORTANT: no hardware / serial reads here
        return self._busy.is_set()

    def open(self) -> None:
        gen = self._mark_busy()

        def work() -> None:
            try:
                r = self._ensure_open()
                r.home()
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.open",
            cancel_previous=True,
            drop_outdated=True,
        )


    def close(self) -> None:
        gen = self._mark_busy()

        def work() -> None:
            try:
                if self._rotator is not None:
                    try:
                        self._rotator.close()
                    finally:
                        self._rotator = None
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.close",
            cancel_previous=True,
            drop_outdated=True,
        )


    def request_restart(self) -> None:
        gen = self._mark_busy()

        def work() -> None:
            try:
                if self._rotator is not None:
                    try:
                        self._rotator.close()
                    finally:
                        self._rotator = None
                self._ensure_open()
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.restart",
            cancel_previous=True,
            drop_outdated=True,
        )

    def _mark_busy(self) -> int:
        with self._busy_lock:
            self._busy_gen += 1
            gen = self._busy_gen
            self._busy.set()
            return gen

    def _clear_busy(self, gen: int) -> None:
        # Only clear if this is still the newest scheduled command
        with self._busy_lock:
            if gen == self._busy_gen:
                self._busy.clear()

    def request_rotation(self, angle: Angle) -> None:
        if angle is None or float(angle) == 0.0:
            return

        gen = self._mark_busy()

        def work() -> None:
            try:
                self._ensure_open().rotate(angle)
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.rotate",
            cancel_previous=True,
            drop_outdated=True,
        )

    def request_homing(self) -> None:
        gen = self._mark_busy()

        def work() -> None:
            try:
                self._ensure_open().home()  # <-- Klammern! (bei dir fehlt das) :contentReference[oaicite:2]{index=2}
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.home",
            cancel_previous=True,
            drop_outdated=True,
        )

    def request_set_speed(self, percent: int) -> None:
        gen = self._mark_busy()

        def work() -> None:
            try:
                self._ensure_open().set_speed(percent)
            finally:
                self._clear_busy(gen)

        self._runner.run(
            work,
            key="rotator.set_speed",
            cancel_previous=True,
            drop_outdated=True,
        )

    def _ensure_open(self) -> Rotator:
        if self._rotator is None:
            r = Rotator()
            r.open(port=self._port)
            self._rotator = r
        return self._rotator
