# phase_control/modules/stabilization/ui/config_panel.py
from __future__ import annotations

from dataclasses import fields
import tkinter as tk
from tkinter import ttk

from base_lib.models import Length, Prefix, Angle, Range
from phase_control.modules.stabilization.config import AnalysisConfig


class ConfigPanel:
    """
    Panel for editing and displaying the AnalysisConfig.

    - FitParameter fields (carrier_wavelength, starting_wavelength,
      bandwidth, baseline, phase, acceleration) are two-way bound to the
      shared config instance, but editable only while the analysis is
      NOT running. When running they are disabled and only updated from
      the config (showing the latest fit).

    - AnalysisConfig-specific fields (wavelength_range, residuals_threshold,
      avg_spectra) are always editable and are written into the shared
      config only when the user clicks the "Update analysis settings"
      button. They are effectively one-way UI -> config.
    """

    def __init__(self, parent: ttk.Notebook, config: AnalysisConfig) -> None:
        # public root frame
        self.frame = ttk.Frame(parent)

        # Shared config instance
        self._config = config

        # Tk variables for FitParameter fields
        self._carrier_var = tk.StringVar()
        self._starting_var = tk.StringVar()
        self._bandwidth_var = tk.StringVar()
        self._baseline_var = tk.StringVar()
        self._phase_var = tk.StringVar()
        self._acceleration_var = tk.StringVar()

        # Tk variables for AnalysisConfig-specific fields
        self._wl_min_var = tk.StringVar()
        self._wl_max_var = tk.StringVar()
        self._residuals_threshold_var = tk.StringVar()
        self._avg_spectra_var = tk.StringVar()

        # Entries that should be disabled while analysis is running
        self._fit_entries: list[ttk.Entry] = []

        self._build_ui()
        self._init_from_config()

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frame = self.frame
        frame.columnconfigure(1, weight=1)

        row = 0

        # --- FitParameter section ------------------------------------- #
        fit_frame = ttk.LabelFrame(frame, text="Fit parameters (fitted by analysis)")
        fit_frame.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        fit_frame.columnconfigure(1, weight=1)
        row += 1

        fit_row = 0

        def add_fit_entry(label: str, var: tk.StringVar) -> None:
            nonlocal fit_row
            ttk.Label(fit_frame, text=label).grid(
                row=fit_row, column=0, sticky="w", **pad
            )
            entry = ttk.Entry(fit_frame, textvariable=var, width=16)
            entry.grid(row=fit_row, column=1, sticky="ew", **pad)
            self._fit_entries.append(entry)
            fit_row += 1

        add_fit_entry("Carrier wavelength [nm]:", self._carrier_var)
        add_fit_entry("Starting wavelength [nm]:", self._starting_var)
        add_fit_entry("Bandwidth [nm]:", self._bandwidth_var)
        add_fit_entry("Baseline:", self._baseline_var)
        add_fit_entry("Phase [rad]:", self._phase_var)
        add_fit_entry("Acceleration:", self._acceleration_var)

        # --- Analysis settings section -------------------------------- #
        analysis_frame = ttk.LabelFrame(frame, text="Analysis settings")
        analysis_frame.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        analysis_frame.columnconfigure(1, weight=1)
        row += 1

        arow = 0

        def add_analysis_entry(label: str, var: tk.StringVar) -> None:
            nonlocal arow
            ttk.Label(analysis_frame, text=label).grid(
                row=arow, column=0, sticky="w", **pad
            )
            ttk.Entry(analysis_frame, textvariable=var, width=16).grid(
                row=arow, column=1, sticky="ew", **pad
            )
            arow += 1

        add_analysis_entry("Wavelength min [nm]:", self._wl_min_var)
        add_analysis_entry("Wavelength max [nm]:", self._wl_max_var)
        add_analysis_entry("Residual threshold:", self._residuals_threshold_var)
        add_analysis_entry("Average spectra:", self._avg_spectra_var)

        ttk.Button(
            analysis_frame,
            text="Update analysis settings",
            command=self.apply_analysis_settings,
        ).grid(row=arow, column=0, columnspan=2, sticky="e", **pad)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_float(value: str, fallback: float) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return fallback

    @staticmethod
    def _parse_int(value: str, fallback: int) -> int:
        try:
            return int(float(value.replace(",", ".")))
        except ValueError:
            return fallback

    # ------------------------------------------------------------------ #
    # Initialisation from config
    # ------------------------------------------------------------------ #

    def _init_from_config(self) -> None:
        """
        Called once during __init__ to fill all UI fields from the config.
        Afterwards, FitParameter fields will be kept in sync via
        refresh_from_config(), while analysis settings are one-way
        (UI -> config via apply_analysis_settings()).
        """
        cfg = self._config

        # FitParameter fields
        self.refresh_from_config()

        # Analysis settings (one-way)
        self._wl_min_var.set(
            f"{cfg.wavelength_range.min.value(Prefix.NANO):.6f}"
        )
        self._wl_max_var.set(
            f"{cfg.wavelength_range.max.value(Prefix.NANO):.6f}"
        )
        self._residuals_threshold_var.set(f"{cfg.residuals_threshold:.3f}")
        self._avg_spectra_var.set(str(cfg.avg_spectra))

    # ------------------------------------------------------------------ #
    # Public API – FitParameter fields
    # ------------------------------------------------------------------ #

    def refresh_from_config(self) -> None:
        """
        Update the FitParameter UI fields from the shared config.
        Called whenever the analysis updates the fit (e.g. after a step).
        """
        cfg = self._config

        self._carrier_var.set(f"{cfg.carrier_wavelength.value(Prefix.NANO):.6f}")
        self._starting_var.set(f"{cfg.starting_wavelength.value(Prefix.NANO):.6f}")
        self._bandwidth_var.set(f"{cfg.bandwidth.value(Prefix.NANO):.6f}")
        self._baseline_var.set(f"{cfg.baseline:.6f}")
        self._phase_var.set(f"{cfg.phase.Rad:.6f}")
        self._acceleration_var.set(f"{cfg.acceleration:.6f}")

    def apply_fit_parameters(self) -> None:
        """
        Parse the FitParameter UI fields and write the values into the
        shared config instance (in-place). Intended to be called when
        starting a new run (while not running).
        """
        cfg = self._config

        carrier_nm = self._parse_float(
            self._carrier_var.get(),
            cfg.carrier_wavelength.value(Prefix.NANO),
        )
        starting_nm = self._parse_float(
            self._starting_var.get(),
            cfg.starting_wavelength.value(Prefix.NANO),
        )
        bandwidth_nm = self._parse_float(
            self._bandwidth_var.get(),
            cfg.bandwidth.value(Prefix.NANO),
        )
        baseline = self._parse_float(self._baseline_var.get(), cfg.baseline)
        phase_rad = self._parse_float(self._phase_var.get(), cfg.phase.Rad)
        acceleration = self._parse_float(
            self._acceleration_var.get(),
            cfg.acceleration,
        )

        # Temporary config with new FitParameter values
        tmp = type(cfg)(
            carrier_wavelength=Length(carrier_nm, Prefix.NANO),
            starting_wavelength=Length(starting_nm, Prefix.NANO),
            bandwidth=Length(bandwidth_nm, Prefix.NANO),
            baseline=baseline,
            phase=Angle(phase_rad),
            acceleration=acceleration,
            wavelength_range=cfg.wavelength_range,
            residuals_threshold=cfg.residuals_threshold,
            avg_spectra=cfg.avg_spectra,
        )

        # Copy only FitParameter fields
        for f in fields(cfg):
            if f.name in {
                "carrier_wavelength",
                "starting_wavelength",
                "bandwidth",
                "baseline",
                "phase",
                "acceleration",
            }:
                setattr(cfg, f.name, getattr(tmp, f.name))

    def set_running(self, running: bool) -> None:
        """
        Enable/disable the FitParameter entries depending on whether the
        analysis is currently running.
        """
        state = "disabled" if running else "normal"
        for entry in self._fit_entries:
            entry.configure(state=state)

    # ------------------------------------------------------------------ #
    # Public API – Analysis settings (one-way UI -> config)
    # ------------------------------------------------------------------ #

    def apply_analysis_settings(self) -> None:
        """
        Parse the analysis settings fields and write them into the
        shared config instance. This is one-way (UI -> config) and
        normally invoked when the user presses the button.
        """
        cfg = self._config

        wl_min_nm = self._parse_float(
            self._wl_min_var.get(),
            cfg.wavelength_range.min.value(Prefix.NANO),
        )
        wl_max_nm = self._parse_float(
            self._wl_max_var.get(),
            cfg.wavelength_range.max.value(Prefix.NANO),
        )

        residual_thresh = self._parse_float(
            self._residuals_threshold_var.get(),
            cfg.residuals_threshold,
        )
        avg_spectra = self._parse_int(
            self._avg_spectra_var.get(),
            cfg.avg_spectra,
        )
        if avg_spectra < 1:
            avg_spectra = 1

        cfg.wavelength_range = Range(
            Length(wl_min_nm, Prefix.NANO),
            Length(wl_max_nm, Prefix.NANO),
        )
        cfg.residuals_threshold = residual_thresh
        cfg.avg_spectra = avg_spectra
