#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperspectral metadata management for GRASS GIS i.hyper tools.

Stores metadata in JSON format at: $MAPSET/grid3/<mapname>/hyper.json

Provides:
- HyperMetadata class for reading/writing metadata
- Forward compatibility via schema versioning
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

import grass.script as gs

SCHEMA_VERSION = "1.0"
METADATA_FILENAME = "hyper.json"


@dataclass
class HyperMetadata:
    """
    Metadata container for hyperspectral 3D rasters.

    Two main modes:
    - Spectral data: has wavelengths, fwhm, radiometric info
    - Component data: has component labels, explained variance (PCA output)
    """

    # Schema
    schema_version: str = SCHEMA_VERSION

    # Dataset-level (spectral mode)
    sensor: Optional[str] = None
    wavelength_units: str = "nm"
    radiometric_quantity: Optional[str] = None  # e.g., "surface_reflectance", "toa_radiance"
    radiometric_units: Optional[str] = None  # e.g., "unitless", "W/(m^2 sr um)"
    acquisition_datetime: Optional[str] = None
    solar_zenith_angle: Optional[float] = None
    solar_azimuth_angle: Optional[float] = None
    satellite_zenith_angle: Optional[float] = None
    satellite_azimuth_angle: Optional[float] = None
    region: Optional[dict[str, Any]] = None

    # Band-level arrays (spectral mode)
    n_bands: Optional[int] = None
    wavelengths: Optional[list[float]] = None
    fwhm: Optional[list[float]] = None
    bad_bands: Optional[list[bool]] = None
    gain: Optional[list[float]] = None
    offset: Optional[list[float]] = None

    # Component-level arrays (component mode)
    n_components: Optional[int] = None
    explained_variance_ratio: Optional[list[float]] = None
    component_labels: Optional[list[str]] = None

    # Processing history
    processing_history: list[dict] = field(default_factory=list)

    # Extensibility
    custom: dict[str, Any] = field(default_factory=dict)

    # ---------- Path resolution ----------

    @staticmethod
    def _get_mapset_path(mapset: Optional[str] = None) -> Path:
        """Get the filesystem path to a mapset."""
        env = gs.gisenv()
        if mapset is None:
            mapset = env["MAPSET"]
        gisdbase = env["GISDBASE"]
        location = env["LOCATION_NAME"]
        return Path(gisdbase) / location / mapset

    @classmethod
    def _get_metadata_path(cls, map_name: str, mapset: Optional[str] = None) -> Path:
        """Get path to hyper.json for a 3D raster map."""
        # Handle map@mapset format
        if "@" in map_name:
            map_name, mapset = map_name.split("@", 1)
        mapset_path = cls._get_mapset_path(mapset)
        return mapset_path / "grid3" / map_name / METADATA_FILENAME

    # ---------- Existence check ----------

    @classmethod
    def exists(cls, map_name: str, mapset: Optional[str] = None) -> bool:
        """Check if JSON metadata exists for a map."""
        return cls._get_metadata_path(map_name, mapset).exists()

    # ---------- Load ----------

    @classmethod
    def load(cls, map_name: str, mapset: Optional[str] = None) -> "HyperMetadata":
        """
        Load metadata from a hyperspectral 3D raster.
        """
        path = cls._get_metadata_path(map_name, mapset)

        if not path.exists():
            raise FileNotFoundError(
                f"JSON metadata file not found for map '{map_name}' at '{path}'."
            )

        return cls._load_from_json(path)

    @classmethod
    def _load_from_json(cls, path: Path) -> "HyperMetadata":
        """Load metadata from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        meta = cls()
        meta.schema_version = data.get("schema_version", "unknown")

        # Dataset level
        ds = data.get("dataset", {})
        meta.sensor = ds.get("sensor")
        meta.wavelength_units = ds.get("wavelength_units", "nm")
        meta.radiometric_quantity = ds.get("radiometric_quantity")
        meta.radiometric_units = ds.get("radiometric_units")
        meta.acquisition_datetime = ds.get("acquisition_datetime")
        meta.solar_zenith_angle = ds.get("solar_zenith_angle")
        meta.solar_azimuth_angle = ds.get("solar_azimuth_angle")
        meta.satellite_zenith_angle = ds.get("satellite_zenith_angle")
        meta.satellite_azimuth_angle = ds.get("satellite_azimuth_angle")
        meta.region = ds.get("region")
        # Band level
        bands = data.get("bands", {})
        meta.n_bands = bands.get("count")
        meta.wavelengths = bands.get("wavelength")
        meta.fwhm = bands.get("fwhm")
        meta.bad_bands = bands.get("bad_band")
        meta.gain = bands.get("gain")
        meta.offset = bands.get("offset")

        # Component level
        comps = data.get("components", {})
        meta.n_components = comps.get("count")
        meta.explained_variance_ratio = comps.get("explained_variance_ratio")
        meta.component_labels = comps.get("labels")

        # History and custom
        meta.processing_history = data.get("processing_history", [])
        meta.custom = data.get("custom", {})

        return meta

    # ---------- Save ----------

    def save(
        self,
        map_name: str,
        mapset: Optional[str] = None,
        save_region: bool = False,
    ) -> None:
        """
        Save metadata for a hyperspectral 3D raster.
        """
        path = self._get_metadata_path(map_name, mapset)

        if not path.parent.exists():
            raise FileNotFoundError(
                f"3D raster directory '{path.parent}' does not exist. "
                f"Create the 3D raster first."
            )

        # Update computed fields
        if self.wavelengths is not None:
            self.n_bands = len(self.wavelengths)
        region = self._get_region_json(map_name, mapset) if save_region else None

        # Build JSON structure
        data = {
            "schema_version": self.schema_version,
            "dataset": {
                "sensor": self.sensor,
                "wavelength_units": self.wavelength_units,
                "radiometric_quantity": self.radiometric_quantity,
                "radiometric_units": self.radiometric_units,
                "acquisition_datetime": self.acquisition_datetime,
                "solar_zenith_angle": self.solar_zenith_angle,
                "solar_azimuth_angle": self.solar_azimuth_angle,
                "satellite_zenith_angle": self.satellite_zenith_angle,
                "satellite_azimuth_angle": self.satellite_azimuth_angle,
            },
            "bands": {},
            "components": {},
            "processing_history": self.processing_history,
            "custom": self.custom,
        }
        if region is not None:
            data["dataset"]["region"] = region

        # Band arrays
        if self.wavelengths is not None:
            data["bands"]["count"] = len(self.wavelengths)
            data["bands"]["wavelength"] = self.wavelengths
        if self.fwhm is not None:
            data["bands"]["fwhm"] = self.fwhm
        if self.bad_bands is not None:
            data["bands"]["bad_band"] = self.bad_bands
        if self.gain is not None:
            data["bands"]["gain"] = self.gain
        if self.offset is not None:
            data["bands"]["offset"] = self.offset

        # Component arrays
        if self.n_components is not None and self.n_components > 0:
            data["components"]["count"] = self.n_components
            if self.explained_variance_ratio is not None:
                data["components"]["explained_variance_ratio"] = (
                    self.explained_variance_ratio
                )
            if self.component_labels is not None:
                data["components"]["labels"] = self.component_labels
        elif self.explained_variance_ratio is not None or self.component_labels is not None:
            if self.explained_variance_ratio is not None:
                data["components"]["explained_variance_ratio"] = (
                    self.explained_variance_ratio
                )
            if self.component_labels is not None:
                data["components"]["labels"] = self.component_labels

        # Write JSON
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def _get_region_json(
        cls, map_name: str, mapset: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Get current computational region as JSON from g.region."""
        try:
            out = gs.read_command("g.region", flags="p3", format="json", quiet=True)
            return json.loads(out)
        except Exception:
            return None

    # ---------- Setters for numpy arrays ----------

    def set_wavelengths(self, wavelengths) -> None:
        """Set center wavelengths for all bands (accepts numpy array or list)."""
        arr = np.asarray(wavelengths, dtype=float)
        self.wavelengths = [float(x) if np.isfinite(x) else None for x in arr]
        self.n_bands = len(self.wavelengths)

    def set_fwhm(self, fwhm) -> None:
        """Set FWHM (bandwidth) for all bands."""
        arr = np.asarray(fwhm, dtype=float)
        self.fwhm = [float(x) if np.isfinite(x) else None for x in arr]

    def set_bad_bands(self, bad_bands) -> None:
        """Set bad band flags (boolean array)."""
        arr = np.asarray(bad_bands, dtype=bool)
        self.bad_bands = arr.tolist()

    def mark_bad_bands(self, indices: list[int]) -> None:
        """Mark specific band indices (0-based) as bad."""
        if self.bad_bands is None and self.n_bands:
            self.bad_bands = [False] * self.n_bands
        for idx in indices:
            if 0 <= idx < len(self.bad_bands):
                self.bad_bands[idx] = True

    def set_explained_variance(self, variance_ratios) -> None:
        """Set explained variance ratios for components."""
        arr = np.asarray(variance_ratios, dtype=float)
        self.explained_variance_ratio = arr.tolist()
        self.n_components = len(self.explained_variance_ratio)

    # ---------- Query methods ----------

    def get_wavelengths_array(self) -> Optional[np.ndarray]:
        """Return wavelengths as numpy array (None values become NaN)."""
        if self.wavelengths is None:
            return None
        return np.array(
            [w if w is not None else np.nan for w in self.wavelengths], dtype=np.float32
        )

    def get_fwhm_array(self) -> Optional[np.ndarray]:
        """Return FWHM as numpy array."""
        if self.fwhm is None:
            return None
        return np.array(
            [f if f is not None else np.nan for f in self.fwhm], dtype=np.float32
        )

    def get_good_band_indices(self) -> np.ndarray:
        """Return indices (0-based) of good (non-flagged) bands."""
        if self.bad_bands is None:
            return np.arange(self.n_bands or 0)
        return np.array([i for i, bad in enumerate(self.bad_bands) if not bad])

    def select_bands_by_wavelength(
        self, min_wl: Optional[float] = None, max_wl: Optional[float] = None
    ) -> np.ndarray:
        """Return indices (0-based) of bands within wavelength range."""
        if self.wavelengths is None:
            raise ValueError("Wavelengths not set")
        wl = self.get_wavelengths_array()
        mask = np.ones(len(wl), dtype=bool)
        if min_wl is not None:
            mask &= wl >= min_wl
        if max_wl is not None:
            mask &= wl <= max_wl
        return np.where(mask)[0]

    def select_good_bands_by_wavelength(
        self, min_wl: Optional[float] = None, max_wl: Optional[float] = None
    ) -> np.ndarray:
        """Return indices of good bands within wavelength range."""
        range_bands = set(self.select_bands_by_wavelength(min_wl, max_wl))
        good_bands = set(self.get_good_band_indices())
        return np.array(sorted(range_bands & good_bands))

    def find_nearest_band(self, target_wl: float) -> int:
        """Find the band index (0-based) nearest to target wavelength."""
        if self.wavelengths is None:
            raise ValueError("Wavelengths not set")
        wl = self.get_wavelengths_array()
        return int(np.nanargmin(np.abs(wl - target_wl)))

    # ---------- Processing history ----------

    def add_processing_step(
        self,
        operation: str,
        module: Optional[str] = None,
        params: Optional[dict] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """Record a processing step in history."""
        step = {
            "operation": operation,
            "module": module,
            "params": params or {},
            "timestamp": timestamp or datetime.now().isoformat(),
        }
        self.processing_history.append(step)

    # ---------- Validation ----------

    def validate(self, require_wavelengths: bool = True) -> list[str]:
        """Return list of validation issues (empty if valid)."""
        issues = []

        is_components = (
            (self.n_components is not None and self.n_components > 0)
            or self.explained_variance_ratio is not None
            or self.component_labels is not None
        )

        if is_components:
            if self.n_components is None or self.n_components <= 0:
                issues.append("Component count not set")
        else:
            if require_wavelengths and self.wavelengths is None:
                issues.append("Missing wavelengths")

            if self.wavelengths is not None and self.fwhm is not None:
                if len(self.wavelengths) != len(self.fwhm):
                    issues.append("Wavelength and FWHM arrays have different lengths")

            if self.wavelength_units not in ("nm", "um", "cm-1"):
                issues.append(f"Unknown wavelength units: {self.wavelength_units}")

        return issues

    # ---------- Factory methods ----------

    @classmethod
    def for_spectral_data(
        cls,
        wavelengths,
        fwhm=None,
        sensor: Optional[str] = None,
        radiometric_quantity: Optional[str] = None,
        radiometric_units: Optional[str] = None,
        acquisition_datetime: Optional[str] = None,
        solar_zenith_angle: Optional[float] = None,
        solar_azimuth_angle: Optional[float] = None,
        satellite_zenith_angle: Optional[float] = None,
        satellite_azimuth_angle: Optional[float] = None,
    ) -> "HyperMetadata":
        """Create metadata for spectral (hyperspectral) data."""
        meta = cls()
        meta.sensor = sensor
        meta.radiometric_quantity = radiometric_quantity
        meta.radiometric_units = radiometric_units
        meta.acquisition_datetime = acquisition_datetime
        meta.solar_zenith_angle = solar_zenith_angle
        meta.solar_azimuth_angle = solar_azimuth_angle
        meta.satellite_zenith_angle = satellite_zenith_angle
        meta.satellite_azimuth_angle = satellite_azimuth_angle
        meta.set_wavelengths(wavelengths)
        if fwhm is not None:
            meta.set_fwhm(fwhm)
        return meta

    @classmethod
    def for_components(
        cls,
        n_components: int,
        explained_variance_ratio=None,
    ) -> "HyperMetadata":
        """Create metadata for dimensionality reduction output (PCA, etc.)."""
        meta = cls()
        meta.n_components = n_components
        if explained_variance_ratio is not None:
            meta.set_explained_variance(explained_variance_ratio)
        return meta


# ---------- Convenience functions ----------


def load_hyper_metadata(map_name: str, mapset: Optional[str] = None) -> HyperMetadata:
    """Load metadata for a hyperspectral 3D raster."""
    return HyperMetadata.load(map_name, mapset)


def save_hyper_metadata(
    meta: HyperMetadata,
    map_name: str,
    mapset: Optional[str] = None,
    save_region: bool = False,
) -> None:
    """Save metadata for a hyperspectral 3D raster."""
    meta.save(map_name, mapset, save_region=save_region)


def has_hyper_metadata(map_name: str, mapset: Optional[str] = None) -> bool:
    """Check if a map has hyperspectral JSON metadata."""
    return HyperMetadata.exists(map_name, mapset)


def copy_hyper_metadata(
    src_map: str,
    dst_map: str,
    src_mapset: Optional[str] = None,
    dst_mapset: Optional[str] = None,
) -> None:
    """Copy hyperspectral metadata from one map to another."""
    meta = HyperMetadata.load(src_map, src_mapset)
    meta.save(dst_map, dst_mapset)


def remove_hyper_metadata(map_name: str, mapset: Optional[str] = None) -> bool:
    """Remove hyperspectral metadata file. Returns True if file existed."""
    path = HyperMetadata._get_metadata_path(map_name, mapset)
    if path.exists():
        path.unlink()
        return True
    return False
