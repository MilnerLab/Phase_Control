# phase_control/modules/stabilization/phase_tracker.py
from __future__ import annotations

from collections import deque
import inspect
from typing import Any, Deque

import lmfit


from base_core.math.functions import usCFG_projection, cfg_projection_nu_equal_amplitudes_safe
from base_core.math.models import Angle
from phase_control.analysis_modules.stabilization.config import AnalysisConfig, FitParameter, FitParameter1
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
        self._fits: Deque[FitParameter1] = deque(maxlen=self._config.avg_spectra)

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
                self._config.copy_from(FitParameter1.mean(self._fits))

            if len(self._fits) < self._config.avg_spectra:
                # Collect phase-only fits for averaging
                self._fits.append(self._fit_phase(spectrum))
                self.current_phase = Angle(0)
            else:
                # Average current batch and decide whether to accept phase
                new_config = FitParameter1.mean(self._fits)
                self._fits.clear()

                if new_config.residual < self._config.residuals_threshold:
                    print("Residuals: ", new_config.residual)
                    self.current_phase = new_config.phase
                    self._config.phase = new_config.phase
                    self._config.residual = new_config.residual

    # ------------------------------------------------------------------ #
    # Internals: fitting
    # ------------------------------------------------------------------ #

    def _initialize_fit_parameters(self, spectrum: Spectrum) -> FitParameter1:
        """
        Fit parameters on the given spectrum to obtain good starting values,
        but keep a_R fixed (not fitted).
        """
        first_arg_name = self._get_first_arg_name()
        model = lmfit.Model(cfg_projection_nu_equal_amplitudes_safe, independent_vars=[first_arg_name])

        fit_kwargs: dict[str, Any] = self._config.to_fit_kwargs(cfg_projection_nu_equal_amplitudes_safe)

        # Build lmfit Parameters object so we can freeze a_R_THz_per_ps
        params = model.make_params(**fit_kwargs)

        # Freeze a_R_THz_per_ps
        params["a_R_THz_per_ps"].set(vary=False)
        
        if not self._config.has_acceleration:
            self._config.a_L_THz_per_ps = self._config.a_R_THz_per_ps
            params["a_L_THz_per_ps"].set(vary=False)

        # (optional) also freeze envelope params if you don't want to fit them:
        # params["carrier_wavelength"].set(vary=False)
        # params["bandwidth"].set(vary=False)

        # Independent variable
        fit_kwargs[first_arg_name] = spectrum.wavelengths_nm

        result = model.fit(
            spectrum.intensity,
            params=params,                 # <-- crucial
            **{first_arg_name: spectrum.wavelengths_nm},
            max_nfev=int(1_000_000),
        )
        return FitParameter1.from_fit_result(self._config, result)

    def _fit_phase(self, spectrum: Spectrum) -> FitParameter1:
        """
        Fit only the phase parameter on the given spectrum.
        """
        first_arg_name = self._get_first_arg_name()
        model = lmfit.Model(cfg_projection_nu_equal_amplitudes_safe, independent_vars=[first_arg_name])

        floats = self._config.to_fit_kwargs(cfg_projection_nu_equal_amplitudes_safe)
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

        return FitParameter1.from_fit_result(self._config, result)

    @staticmethod
    def _get_first_arg_name() -> str:
        sig = inspect.signature(cfg_projection_nu_equal_amplitudes_safe)
        return next(iter(sig.parameters))
