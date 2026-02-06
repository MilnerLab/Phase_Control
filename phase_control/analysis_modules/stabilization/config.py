# phase_control/modules/stabilization/config.py
from __future__ import annotations

from dataclasses import dataclass, fields
import inspect
from typing import Any, Callable, ClassVar, Sequence, TypeVar, get_type_hints

import lmfit
import numpy as np

from base_core.math.models import Angle, Range
from base_core.quantities.enums import Prefix
from base_core.quantities.models import Length

T = TypeVar("T", bound="FitParameter1")


@dataclass
class FitParameter:
    """
    Fit parameters for the usCFG_projection model.

    This class knows how to:
      - convert itself into kwargs for the fit function
      - rebuild a new instance from an lmfit result
      - compute the mean of several FitParameter instances
    """
    carrier_wavelength: Length = Length(802.38, Prefix.NANO)
    starting_wavelength: Length = Length(808.352, Prefix.NANO)
    bandwidth: Length = Length(7.4728, Prefix.NANO)
    baseline: float = 0.3338
    phase: Angle = Angle(-3.34)
    acceleration: float = 0.0979 * np.pi * 2
    residual: float = 0.0

    def to_fit_kwargs(self, func: Callable[..., Any]) -> dict[str, float]:
        """
        Build a dict of float kwargs for the given fit function.

        The first parameter of 'func' is assumed to be the x-axis and is
        therefore skipped; all following parameters are taken from this
        instance and converted to floats.
        """
        sig = inspect.signature(func)
        # skip first argument (independent variable)
        param_names = list(sig.parameters.keys())[1:]

        kwargs: dict[str, float] = {}
        type_hints = get_type_hints(type(self))

        for name in param_names:
            val = getattr(self, name)
            field_type = type_hints.get(name, type(val))
            conv = type(self)._to_float_conv(field_type)
            kwargs[name] = conv(val)

        return kwargs

    @classmethod
    def from_fit_result(cls: type[T], base: T, result: lmfit.model.ModelResult) -> T:
        """
        Create a new FitParameter instance from an lmfit ModelResult.

        - parameters present in 'best_values' are updated
        - 'residual' is set to the squared sum of residuals
        - all other fields are copied from 'base'
        """
        best = result.best_values
        type_hints: dict[str, type[Any]] = get_type_hints(cls)
        kwargs: dict[str, Any] = {}

        for f in fields(cls):
            name = f.name

            if name in best:
                field_type = type_hints.get(name, float)
                conv = cls._from_float_conv(field_type)
                kwargs[name] = conv(best[name])
            elif name == "residual":
                kwargs[name] = float(np.sum(result.residual ** 2))
            else:
                kwargs[name] = getattr(base, name)

        return cls(**kwargs)

    @classmethod
    def mean(cls: type[T], items: Sequence[T]) -> T:
        """
        Compute the mean of a sequence of FitParameter instances.

        Numeric/angle/length fields are averaged; other fields are taken
        from the first element.
        """
        if not items:
            raise ValueError("At least one FitParameter is required.")

        type_hints = get_type_hints(cls)
        kwargs: dict[str, Any] = {}

        for f in fields(cls):
            name = f.name
            values = [getattr(p, name) for p in items]

            field_type = type_hints.get(name, type(values[0]))
            to_float = cls._to_float_conv(field_type)
            from_float = cls._from_float_conv(field_type)

            if field_type in cls._TO_FLOAT:
                nums = [to_float(v) for v in values]
                mean_val = sum(nums) / len(nums)
                kwargs[name] = from_float(mean_val)
            else:
                # non-numeric fields: just take the first one
                kwargs[name] = values[0]

        return cls(**kwargs)

    def copy_from(self, other: "FitParameter") -> None:
        """
        Copy a subset of fields from another FitParameter/AnalysisConfig.

        Some AnalysisConfig-specific fields are deliberately NOT copied.
        """
        for f in fields(self):
            if f.name not in ("wavelength_range", "avg_spectra", "residuals_threshold"):
                setattr(self, f.name, getattr(other, f.name))

    # ---- conversion helpers ---- #

    _TO_FLOAT: ClassVar[dict[type[Any], Callable[[Any], float]]] = {
        Length: lambda l: l.value(Prefix.NANO),
        Angle: lambda a: a.Rad,
        float: float,
    }

    _FROM_FLOAT: ClassVar[dict[type[Any], Callable[[float], Any]]] = {
        Length: lambda v: Length(v, Prefix.NANO),
        Angle: lambda v: Angle(v),
        float: float,
    }

    @classmethod
    def _to_float_conv(cls, field_type: type[Any]) -> Callable[[Any], float]:
        return cls._TO_FLOAT.get(field_type, lambda v: v)

    @classmethod
    def _from_float_conv(cls, field_type: type[Any]) -> Callable[[float], Any]:
        return cls._FROM_FLOAT.get(field_type, lambda v: v)


@dataclass
class FitParameter1:
    """
    Fit parameters for the ν-domain usCFG projection model (equal amplitudes, no TOD).

    This class knows how to:
      - convert itself into kwargs for the fit function
      - rebuild a new instance from an lmfit result
      - compute the mean of several FitParameter instances

    Notes on units (chosen for numerical stability):
      - carrier_wavelength, bandwidth: Length in nm (Prefix.NANO)
      - tau_ps: delay in picoseconds
      - a_R_THz_per_ps, a_L_THz_per_ps: chirp rates in THz/ps
      - phase: Angle (radians)
    """

    central_wavelength: Length = Length(802.38, Prefix.NANO)
    bandwidth: Length = Length(7.4728, Prefix.NANO)  # interpreted by your fit function (sigma or FWHM)
    baseline: float = 0.3338
    phase: Angle = Angle(-3.34)

    # --- NEW parameters for ν-domain model ---
    tau_ps: float = 0.30              # delay [ps]
    a_R_THz_per_ps: float = 0.60      # chirp rate dν/dt for R [THz/ps]
    a_L_THz_per_ps: float = 0.60      # chirp rate dν/dt for L [THz/ps]

    residual: float = 0.0

    def to_fit_kwargs(self, func: Callable[..., Any]) -> dict[str, float]:
        """
        Build a dict of float kwargs for the given fit function.

        The first parameter of 'func' is assumed to be the x-axis and is
        therefore skipped; all following parameters are taken from this
        instance and converted to floats.
        """
        sig = inspect.signature(func)
        # skip first argument (independent variable)
        param_names = list(sig.parameters.keys())[1:]

        kwargs: dict[str, float] = {}
        type_hints = get_type_hints(type(self))

        for name in param_names:
            val = getattr(self, name)
            field_type = type_hints.get(name, type(val))
            conv = type(self)._to_float_conv(field_type)
            kwargs[name] = conv(val)

        return kwargs

    @classmethod
    def from_fit_result(cls: type[T], base: T, result: lmfit.model.ModelResult) -> T:
        """
        Create a new FitParameter instance from an lmfit ModelResult.

        - parameters present in 'best_values' are updated
        - 'residual' is set to the squared sum of residuals
        - all other fields are copied from 'base'
        """
        best = result.best_values
        type_hints: dict[str, type[Any]] = get_type_hints(cls)
        kwargs: dict[str, Any] = {}

        for f in fields(cls):
            name = f.name

            if name in best:
                field_type = type_hints.get(name, float)
                conv = cls._from_float_conv(field_type)
                kwargs[name] = conv(best[name])
            elif name == "residual":
                kwargs[name] = float(np.sum(result.residual ** 2))
            else:
                kwargs[name] = getattr(base, name)

        return cls(**kwargs)

    @classmethod
    def mean(cls: type[T], items: Sequence[T]) -> T:
        """
        Compute the mean of a sequence of FitParameter instances.

        Numeric/angle/length fields are averaged; other fields are taken
        from the first element.
        """
        if not items:
            raise ValueError("At least one FitParameter is required.")

        type_hints = get_type_hints(cls)
        kwargs: dict[str, Any] = {}

        for f in fields(cls):
            name = f.name
            values = [getattr(p, name) for p in items]

            field_type = type_hints.get(name, type(values[0]))
            to_float = cls._to_float_conv(field_type)
            from_float = cls._from_float_conv(field_type)

            if field_type in cls._TO_FLOAT:
                nums = [to_float(v) for v in values]
                mean_val = sum(nums) / len(nums)
                kwargs[name] = from_float(mean_val)
            else:
                # non-numeric fields: just take the first one
                kwargs[name] = values[0]

        return cls(**kwargs)

    def copy_from(self, other: "FitParameter") -> None:
        """
        Copy a subset of fields from another FitParameter/AnalysisConfig.

        Some AnalysisConfig-specific fields are deliberately NOT copied.
        """
        for f in fields(self):
            if f.name not in ("wavelength_range", "avg_spectra", "residuals_threshold"):
                setattr(self, f.name, getattr(other, f.name))

    # ---- conversion helpers ---- #

    _TO_FLOAT: ClassVar[dict[type[Any], Callable[[Any], float]]] = {
        Length: lambda l: float(l.value(Prefix.NANO)),   # nm
        Angle: lambda a: float(a.Rad),                   # rad
        float: float,
    }

    _FROM_FLOAT: ClassVar[dict[type[Any], Callable[[float], Any]]] = {
        Length: lambda v: Length(float(v), Prefix.NANO),
        Angle: lambda v: Angle(float(v)),
        float: float,
    }

    @classmethod
    def _to_float_conv(cls, field_type: type[Any]) -> Callable[[Any], float]:
        return cls._TO_FLOAT.get(field_type, lambda v: v)

    @classmethod
    def _from_float_conv(cls, field_type: type[Any]) -> Callable[[float], Any]:
        return cls._FROM_FLOAT.get(field_type, lambda v: v)



@dataclass
class AnalysisConfig(FitParameter1):
    """
    Full configuration for the stabilization analysis.

    Extends FitParameter with:
      - wavelength_range: range in which the fit is performed
      - residuals_threshold: max allowed residual for accepting a phase
      - avg_spectra: number of spectra to average in PhaseTracker
    """
    wavelength_range: Range[Length] = Range(Length(796, Prefix.NANO), Length(810, Prefix.NANO))
    residuals_threshold: float = 15
    avg_spectra: int = 10
