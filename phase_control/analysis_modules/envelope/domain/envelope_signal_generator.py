from typing import Optional
import numpy as np
from base_core.math.models import Angle
from phase_control.analysis_modules.envelope.config import EnvelopeSignalGeneratorConfig
from phase_control.analysis_modules.envelope.domain.enums import EnvelopeMode
from phase_control.core.models import Spectrum


class EnvelopeSignalGenerator:
    """
    Reads a spectrum -> computes an "envelope metric" -> outputs a correction angle.

    The generator is stateful:
      - keeps last_metric
      - keeps current direction (+1 / -1)

    It implements a simple fixed-step hill-climb:
      - if metric improved -> keep direction
      - else -> flip direction
      - correction = direction * step_angle
    """

    def __init__(self, config: EnvelopeSignalGeneratorConfig) -> None:
        self.config = config

    def update(self, spectrum: Spectrum) -> tuple[Optional[Angle], dict[str, Spectrum]]:
        """
        Returns:
          (correction_angle | None, debug_spectra_dict)

        debug_spectra_dict can be plotted (e.g. "envelope").
        """
        if spectrum is None:
            return None, {}

        # 1) cut to wavelength window
        spec = spectrum.cut(self.config.wavelength_range)

        # 2) smooth (moving average along wavelength)
        y = np.asarray(spec.intensities, dtype=float)
        if y.size == 0 or not np.all(np.isfinite(y)):
            return None, {}

        y_s = self._smooth_mavg(y)

        # 3) envelope metric (THIS is your "signal")
        #    keep it simple: peak height in the window
        metric = float(np.max(y_s))

        # 4) decide direction vs last metric
        if self._last_metric is not None:
            if not self._is_improved(metric):
                self._direction *= -1

        self._last_metric = metric

        # 5) output correction angle (fixed step)
        correction = self.config.step_angle if self._direction > 0 else Angle(-self.config.step_angle)

        # debug output for plotting
        out: dict[str, Spectrum] = {
            "envelope": Spectrum(spec.wavelengths, y_s),
        }
        return correction, out

    def _smooth_mavg(self, y: np.ndarray) -> np.ndarray:
        w = int(self.config.smooth_window)
        if w <= 1 or y.size < w:
            return y
        kernel = np.ones(w, dtype=float) / w
        return np.convolve(y, kernel, mode="same")

    def _is_improved(self, current: float) -> bool:
        if self.config.mode == EnvelopeMode.MAXIMIZE:
            return current > self._last_metric, + self.config.improve_eps
        else:
            return current < self._last_metric, - self.config.improve_eps