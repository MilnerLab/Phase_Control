# phase_control/core/models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from base_lib.quantities.enums import Prefix
from base_lib.quantities.models import Length
from elliptec.elliptec_ell14 import Range



@dataclass(slots=True)
class Spectrum:
    wavelengths: list[Length]
    intensity: list[float]

    @property
    def wavelengths_nm(self) -> list[float]:
        return [w.value(Prefix.NANO) for w in self.wavelengths]

    @classmethod
    def from_raw_data(
        cls,
        wavelengths: Sequence[float],
        counts: Sequence[int | float],
        normalize: bool = True,
    ) -> Spectrum:
        arr = np.asarray(counts, dtype=float)

        if normalize and arr.size > 0:
            arr = arr - np.amin(arr)
            max_val = np.amax(arr)
            if max_val > 0:
                arr = arr / max_val

        wl_lengths = [Length(w, Prefix.NANO) for w in wavelengths]

        return cls(
            wavelengths=wl_lengths,
            intensity=arr.tolist(),
        )

    def cut(self, range_wl: Range) -> Spectrum:
        wavelengths_cut: list[Length] = []
        intensity_cut: list[float] = []

        for wl, inten in zip(self.wavelengths, self.intensity):
            if range_wl.is_in_range(wl):
                wavelengths_cut.append(wl)
                intensity_cut.append(inten)

        return Spectrum(wavelengths_cut, intensity_cut)
