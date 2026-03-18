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
import shlex
import uuid
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

    Data model:
    - spectral: bands are on wavelength axis
    - component: bands are component/layer indices
    """

    # Schema
    schema_version: str = SCHEMA_VERSION
    dataset_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    data_type: str = "spectral"  # spectral | component

    # Dataset-level
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

    # Band-level arrays
    n_bands: Optional[int] = None
    n_bands_source: Optional[int] = None
    n_bands_valid: Optional[int] = None
    wavelengths: Optional[list[float]] = None
    fwhm: Optional[list[float]] = None
    validity: Optional[list[bool]] = None

    # Backward-compatibility aliases for old callers
    bad_bands: Optional[list[bool]] = None
    gain: Optional[list[float]] = None
    offset: Optional[list[float]] = None

    # Backward-compatibility aliases for old callers (component mode)
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
        meta.dataset_id = str(data.get("dataset_id") or uuid.uuid4().hex)

        # New schema (top-level dataset fields)
        if "dataset" not in data:
            meta.data_type = str(data.get("data_type") or "spectral")
            meta.sensor = data.get("sensor")
            meta.wavelength_units = data.get("wavelength_units", "nm")
            meta.radiometric_quantity = data.get("radiometric_quantity")
            meta.radiometric_units = data.get("radiometric_units")
            meta.acquisition_datetime = data.get("acquisition_datetime")
            meta.solar_zenith_angle = data.get("solar_zenith_angle")
            meta.solar_azimuth_angle = data.get("solar_azimuth_angle")
            meta.satellite_zenith_angle = data.get("satellite_zenith_angle")
            meta.satellite_azimuth_angle = data.get("satellite_azimuth_angle")
            meta.region = data.get("region")

            bands = data.get("bands", {})
            meta.n_bands_source = bands.get("count")
            meta.n_bands_valid = bands.get("count_valid")
            meta.wavelengths = bands.get("wavelength")
            meta.fwhm = bands.get("fwhm")
            meta.validity = bands.get("validity")
            meta.component_labels = bands.get("labels")

            if meta.n_bands_source is None and meta.wavelengths is not None:
                meta.n_bands_source = len(meta.wavelengths)
            if meta.n_bands_source is None and meta.validity is not None:
                meta.n_bands_source = len(meta.validity)
            if meta.n_bands_source is None and meta.component_labels is not None:
                meta.n_bands_source = len(meta.component_labels)
            if meta.n_bands_valid is None:
                if meta.validity is not None:
                    meta.n_bands_valid = int(sum(bool(v) for v in meta.validity))
                else:
                    meta.n_bands_valid = meta.n_bands_source

            if meta.validity is not None:
                meta.bad_bands = [not bool(v) for v in meta.validity]

            if meta.data_type == "component":
                meta.n_components = int(meta.n_bands_valid or meta.n_bands_source or 0)

            meta.n_bands = meta.n_bands_valid

            meta.processing_history = cls._normalize_history_entries(
                data.get("processing_history", [])
            )
            meta.custom = data.get("custom", {})
            return meta

        # Legacy schema fallback (dataset + bands + components)
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

        bands = data.get("bands", {})
        meta.n_bands = bands.get("count")
        meta.n_bands_source = meta.n_bands
        meta.n_bands_valid = meta.n_bands
        meta.wavelengths = bands.get("wavelength")
        meta.fwhm = bands.get("fwhm")
        meta.validity = bands.get("validity")
        meta.bad_bands = bands.get("bad_band")
        meta.gain = bands.get("gain")
        meta.offset = bands.get("offset")
        if meta.validity is None and meta.bad_bands is not None:
            meta.validity = [not bool(v) for v in meta.bad_bands]
        elif meta.validity is not None and meta.bad_bands is None:
            meta.bad_bands = [not bool(v) for v in meta.validity]

        comps = data.get("components", {})
        meta.n_components = comps.get("count")
        meta.explained_variance_ratio = comps.get("explained_variance_ratio")
        meta.component_labels = comps.get("labels")

        has_components = (
            (meta.n_components is not None and meta.n_components > 0)
            or meta.explained_variance_ratio is not None
            or meta.component_labels is not None
        )
        meta.data_type = "component" if has_components else "spectral"
        if meta.data_type == "component" and meta.n_bands is None:
            meta.n_bands = meta.n_components

        meta.processing_history = cls._normalize_history_entries(
            data.get("processing_history", [])
        )
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
            self.n_bands_source = len(self.wavelengths)
            self.data_type = "spectral"
        elif self.data_type == "component" and self.n_components is not None:
            self.n_bands_source = int(self.n_components)
        elif self.n_bands_source is None and self.validity is not None:
            self.n_bands_source = len(self.validity)
        elif self.n_bands_source is None and self.n_bands is not None:
            self.n_bands_source = int(self.n_bands)

        if self.validity is None and self.bad_bands is not None:
            self.validity = [not bool(v) for v in self.bad_bands]
        if self.validity is None and self.n_bands_source:
            self.validity = [True] * int(self.n_bands_source)
        if self.validity is not None and self.n_bands_source is not None:
            n = int(self.n_bands_source)
            if len(self.validity) < n:
                self.validity = self.validity + [True] * (n - len(self.validity))
            elif len(self.validity) > n:
                self.validity = self.validity[:n]
            self.n_bands_valid = int(sum(bool(v) for v in self.validity))
        elif self.n_bands_valid is None and self.n_bands_source is not None:
            self.n_bands_valid = int(self.n_bands_source)

        self.n_bands = self.n_bands_valid

        region = self._get_region_json(map_name, mapset) if save_region else self.region
        self.region = region

        # Build JSON structure (new schema)
        data = {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id or uuid.uuid4().hex,
            "data_type": self.data_type or "spectral",
            "sensor": self.sensor,
            "wavelength_units": self.wavelength_units,
            "radiometric_quantity": self.radiometric_quantity,
            "radiometric_units": self.radiometric_units,
            "acquisition_datetime": self.acquisition_datetime,
            "solar_zenith_angle": self.solar_zenith_angle,
            "solar_azimuth_angle": self.solar_azimuth_angle,
            "satellite_zenith_angle": self.satellite_zenith_angle,
            "satellite_azimuth_angle": self.satellite_azimuth_angle,
            "region": self.region,
            "bands": {},
            "processing_history": self._normalize_history_entries(
                self.processing_history
            ),
            "custom": self.custom,
        }

        # Band arrays
        if self.n_bands_source is not None:
            data["bands"]["count"] = int(self.n_bands_source)
        if self.n_bands_valid is not None:
            data["bands"]["count_valid"] = int(self.n_bands_valid)
        if self.wavelengths is not None:
            data["bands"]["wavelength"] = self.wavelengths
        if self.fwhm is not None:
            data["bands"]["fwhm"] = self.fwhm
        if self.validity is not None:
            data["bands"]["validity"] = [bool(v) for v in self.validity]
        if self.component_labels is not None:
            data["bands"]["labels"] = self.component_labels

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
        self.n_bands_source = len(self.wavelengths)
        if self.validity is None:
            self.n_bands_valid = self.n_bands_source
            self.n_bands = self.n_bands_source
        else:
            self.n_bands_valid = int(sum(bool(v) for v in self.validity))
            self.n_bands = self.n_bands_valid

    def set_fwhm(self, fwhm) -> None:
        """Set FWHM (bandwidth) for all bands."""
        arr = np.asarray(fwhm, dtype=float)
        self.fwhm = [float(x) if np.isfinite(x) else None for x in arr]

    def set_validity(self, validity) -> None:
        """Set per-band validity flags."""
        arr = np.asarray(validity, dtype=bool)
        self.validity = arr.tolist()
        self.n_bands_source = len(self.validity)
        self.n_bands_valid = int(sum(bool(v) for v in self.validity))
        self.n_bands = self.n_bands_valid
        self.bad_bands = [not bool(v) for v in self.validity]

    def set_bad_bands(self, bad_bands) -> None:
        """Set bad band flags (boolean array)."""
        arr = np.asarray(bad_bands, dtype=bool)
        self.bad_bands = arr.tolist()
        self.validity = [not bool(v) for v in self.bad_bands]
        self.n_bands_source = len(self.validity)
        self.n_bands_valid = int(sum(bool(v) for v in self.validity))
        self.n_bands = self.n_bands_valid

    def mark_bad_bands(self, indices: list[int]) -> None:
        """Mark specific band indices (0-based) as bad."""
        if self.bad_bands is None and self.n_bands_source:
            self.bad_bands = [False] * self.n_bands_source
        elif self.bad_bands is None and self.n_bands:
            self.bad_bands = [False] * self.n_bands
        if self.validity is None and self.n_bands_source:
            self.validity = [True] * self.n_bands_source
        for idx in indices:
            if 0 <= idx < len(self.bad_bands):
                self.bad_bands[idx] = True
                self.validity[idx] = False
        self.n_bands_valid = int(sum(bool(v) for v in self.validity))
        self.n_bands = self.n_bands_valid

    def set_explained_variance(self, variance_ratios) -> None:
        """Set explained variance ratios for components."""
        arr = np.asarray(variance_ratios, dtype=float)
        self.explained_variance_ratio = arr.tolist()
        self.n_components = len(self.explained_variance_ratio)
        self.data_type = "component"
        self.n_bands = self.n_components

    # ---------- Query methods ----------

    def get_wavelengths_array(self) -> Optional[np.ndarray]:
        """Return wavelengths as numpy array (None values become NaN)."""
        if self.wavelengths is None:
            return None
        values = list(self.wavelengths)
        if self.validity is not None and len(self.validity) == len(values):
            values = [w for i, w in enumerate(values) if bool(self.validity[i])]
        return np.array(
            [w if w is not None else np.nan for w in values], dtype=np.float32
        )

    def get_fwhm_array(self) -> Optional[np.ndarray]:
        """Return FWHM as numpy array."""
        if self.fwhm is None:
            return None
        values = list(self.fwhm)
        if self.validity is not None and len(self.validity) == len(values):
            values = [f for i, f in enumerate(values) if bool(self.validity[i])]
        return np.array(
            [f if f is not None else np.nan for f in values], dtype=np.float32
        )

    def get_good_band_indices(self) -> np.ndarray:
        """Return indices (0-based) of good (non-flagged) bands."""
        if self.validity is not None:
            return np.arange(self.n_bands or int(sum(bool(v) for v in self.validity)))
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
        """Backward-compatible wrapper that records history as command + I/O."""
        command = self._command_from_module_params(module or operation, params or {})
        self.add_history_entry(
            command=command,
            inputs=[],
            outputs=[],
            timestamp=timestamp,
        )

    def add_history_entry(
        self,
        command: str,
        inputs: Optional[list[dict[str, Any]]] = None,
        outputs: Optional[list[dict[str, Any]]] = None,
        timestamp: Optional[str] = None,
    ) -> None:
        """Record a processing history entry in the compact schema."""
        entry = {
            "command": str(command),
            "timestamp": timestamp or datetime.now().isoformat(),
            "inputs": self._normalize_io_refs(inputs or []),
            "outputs": self._normalize_io_refs(outputs or []),
        }
        self.processing_history.append(entry)

    # ---------- Validation ----------

    def validate(self, require_wavelengths: bool = True) -> list[str]:
        """Return list of validation issues (empty if valid)."""
        issues = []

        if self.data_type not in ("spectral", "component"):
            issues.append(f"Unknown data_type: {self.data_type}")

        if self.data_type == "spectral":
            if require_wavelengths and self.wavelengths is None:
                issues.append("Missing wavelengths")

            if self.wavelengths is not None and self.fwhm is not None:
                if len(self.wavelengths) != len(self.fwhm):
                    issues.append("Wavelength and FWHM arrays have different lengths")
            if self.wavelengths is not None and self.validity is not None:
                if len(self.wavelengths) != len(self.validity):
                    issues.append("Wavelength and validity arrays have different lengths")

            if self.wavelength_units not in ("nm", "um", "cm-1"):
                issues.append(f"Unknown wavelength units: {self.wavelength_units}")
        else:
            if (self.n_bands is None or self.n_bands <= 0) and (
                self.n_components is None or self.n_components <= 0
            ):
                issues.append("Component data must define at least one band/layer")

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
        meta.data_type = "spectral"
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
        meta.data_type = "component"
        meta.n_components = n_components
        meta.n_bands_source = int(n_components or 0)
        meta.n_bands_valid = int(n_components or 0)
        meta.n_bands = int(n_components or 0)
        if explained_variance_ratio is not None:
            meta.set_explained_variance(explained_variance_ratio)
        return meta

    # ---------- Internal normalization ----------

    @staticmethod
    def _command_from_module_params(module: str, params: dict[str, Any]) -> str:
        if not module:
            return ""
        parts = [module]
        for key in sorted(params):
            val = params[key]
            if val is None or val == "":
                continue
            if isinstance(val, (list, tuple)):
                val = ",".join(str(x) for x in val)
            parts.append(f"{key}={shlex.quote(str(val))}")
        return " ".join(parts)

    @classmethod
    def _normalize_io_refs(cls, refs: list[Any]) -> list[dict[str, Any]]:
        out = []
        for item in refs:
            if isinstance(item, dict):
                out.append(
                    {
                        "id": item.get("id"),
                        "map_name": item.get("map_name"),
                    }
                )
            elif isinstance(item, str):
                out.append({"id": item, "map_name": None})
        return out

    @classmethod
    def _normalize_history_entries(cls, entries: list[Any]) -> list[dict[str, Any]]:
        normalized = []
        for step in entries or []:
            if not isinstance(step, dict):
                continue
            if "command" in step:
                normalized.append(
                    {
                        "command": str(step.get("command", "")),
                        "timestamp": step.get("timestamp") or datetime.now().isoformat(),
                        "inputs": cls._normalize_io_refs(step.get("inputs") or []),
                        "outputs": cls._normalize_io_refs(step.get("outputs") or []),
                    }
                )
                continue

            command = cls._command_from_module_params(
                step.get("module") or step.get("operation") or "",
                step.get("params") or {},
            )
            normalized.append(
                {
                    "command": command,
                    "timestamp": step.get("timestamp") or datetime.now().isoformat(),
                    "inputs": [],
                    "outputs": [],
                }
            )
        return normalized


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
