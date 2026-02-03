# phase_control/modules/stabilization/phase_tracker.py
from __future__ import annotations

from collections import deque
import inspect
from typing import Any, Deque

import lmfit


from base_core.math.functions import usCFG_projection
from base_core.math.models import Angle
from phase_control.analysis_modules.stabilization.config import AnalysisConfig, FitParameter
from phase_control.core.models import Spectrum


class PhaseTracker:
    """
    Tracks the current phase by fitting a model to incoming spectra.

    Workflow (per spectrum):
      - during initial phase, gather several full fits to build a good
        starting configuration (FitParameter.mean)
      - once configured, only fit the phase parameter on subsequent spectra
      - if the residuals are low enough, accept the new phase as current
    """

    current_phase: Angle | None = None

    def __init__(self, start_config: AnalysisConfig) -> None:
        self._config: AnalysisConfig = start_config
        self._fits: Deque[FitParameter] = deque(maxlen=self._config.avg_spectra)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def update(self, spectrum: Spectrum) -> None:
        """
        Update the internal phase estimate based on a new spectrum.
        """
        if len(self._fits) < self._config.avg_spectra and self.current_phase is None:
            # Initial phase: gather good starting parameters
            self._fits.append(self._initialize_fit_parameters(spectrum))
            print("gathering configs")
            return
        else:
            if self.current_phase is None:
                # Once we have enough initial fits, consolidate them
                self._config.copy_from(FitParameter.mean(self._fits))

            if len(self._fits) < self._config.avg_spectra:
                # Collect phase-only fits for averaging
                self._fits.append(self._fit_phase(spectrum))
                self.current_phase = Angle(0)
            else:
                # Average current batch and decide whether to accept phase
                new_config = FitParameter.mean(self._fits)
                self._fits.clear()

                if new_config.residual < self._config.residuals_threshold:
                    print("Residuals: ", new_config.residual)
                    self.current_phase = new_config.phase
                    self._config.phase = new_config.phase
                    self._config.residual = new_config.residual

    # ------------------------------------------------------------------ #
    # Internals: fitting
    # ------------------------------------------------------------------ #

    def _initialize_fit_parameters(self, spectrum: Spectrum) -> FitParameter:
        """
        Perform a full fit of all parameters on the given spectrum to obtain
        good starting values.
        """
        first_arg_name = self._get_first_arg_name()
        model = lmfit.Model(usCFG_projection, independent_vars=[first_arg_name])

        fit_kwargs: dict[str, Any] = self._config.to_fit_kwargs(usCFG_projection)
        fit_kwargs[first_arg_name] = spectrum.wavelengths_nm

        result = model.fit(
            spectrum.intensity,
            **fit_kwargs,
            max_nfev=int(1_000_000),
        )
        return FitParameter.from_fit_result(self._config, result)

    def _fit_phase(self, spectrum: Spectrum) -> FitParameter:
        """
        Fit only the phase parameter on the given spectrum.
        """
        first_arg_name = self._get_first_arg_name()
        model = lmfit.Model(usCFG_projection, independent_vars=[first_arg_name])

        floats = self._config.to_fit_kwargs(usCFG_projection)
        param_kwargs: dict[str, Any] = dict(floats)

        params = model.make_params(**param_kwargs)
        for name, par in params.items():
            par.vary = (name == "phase")

        x_kwargs: dict[str, Any] = {first_arg_name: spectrum.wavelengths_nm}

        result = model.fit(
            spectrum.intensity,
            params=params,
            **x_kwargs,
        )

        return FitParameter.from_fit_result(self._config, result)

    @staticmethod
    def _get_first_arg_name() -> str:
        sig = inspect.signature(usCFG_projection)
        return next(iter(sig.parameters))
