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

import copy
import json
import shlex
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    derived: bool = False
    data_type: str = "spectral"  # spectral | component

    # Dataset-level
    sensor: str | None = None
    wavelength_units: str = "nm"
    radiometric_quantity: str | None = (
        None  # e.g., "surface_reflectance", "toa_radiance"
    )
    radiometric_units: str | None = None  # e.g., "unitless", "W/(m^2 sr um)"
    acquisition_datetime: str | None = None
    region: dict[str, Any] | None = None

    # Band-level arrays
    n_bands: int | None = None
    n_bands_source: int | None = None
    n_bands_valid: int | None = None
    wavelengths: list[float] | None = None
    fwhm: list[float] | None = None
    validity: list[bool] | None = None

    # Backward-compatibility aliases for old callers
    bad_bands: list[bool] | None = None
    gain: list[float] | None = None
    offset: list[float] | None = None

    # Backward-compatibility aliases for old callers (component mode)
    n_components: int | None = None
    explained_variance_ratio: list[float] | None = None
    component_labels: list[str] | None = None
    dimensionality_reduction: dict[str, Any] | None = None

    # Processing history
    processing_history: list[dict] = field(default_factory=list)

    # Extensibility
    extended_metadata: dict[str, Any] = field(default_factory=dict)

    # Snapshots of all input datasets (direct + recursive ancestors), keyed by dataset_id.
    input_datasets_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    # ---------- Path resolution ----------

    @staticmethod
    def new_dataset_id() -> str:
        """Create a new dataset identifier."""
        return uuid.uuid4().hex

    @staticmethod
    def _get_mapset_path(mapset: str | None = None) -> Path:
        """Get the filesystem path to a mapset."""
        env = gs.gisenv()
        if mapset is None:
            mapset = env["MAPSET"]
        gisdbase = env["GISDBASE"]
        location = env["LOCATION_NAME"]
        return Path(gisdbase) / location / mapset

    @classmethod
    def _get_metadata_path(cls, map_name: str, mapset: str | None = None) -> Path:
        """Get path to hyper.json for a 3D raster map."""
        # Handle map@mapset format
        if "@" in map_name:
            map_name, mapset = map_name.split("@", 1)
        mapset_path = cls._get_mapset_path(mapset)
        return mapset_path / "grid3" / map_name / METADATA_FILENAME

    @classmethod
    def load_raw(cls, map_name: str, mapset: str | None = None) -> dict[str, Any]:
        """Load raw JSON metadata for a map."""
        path = cls._get_metadata_path(map_name, mapset)
        if not path.exists():
            raise FileNotFoundError(
                f"JSON metadata file not found for map '{map_name}' at '{path}'."
            )
        with open(path, "r") as f:
            return json.load(f)

    @staticmethod
    def to_full_map_name(map_name: str, mapset: str | None = None) -> str:
        """Normalize map name to map@mapset format."""
        if "@" in map_name:
            return map_name
        if mapset:
            return f"{map_name}@{mapset}"
        env = gs.gisenv()
        return f"{map_name}@{env.get('MAPSET', '')}".rstrip("@")

    # ---------- Existence check ----------

    @classmethod
    def exists(cls, map_name: str, mapset: str | None = None) -> bool:
        """Check if JSON metadata exists for a map."""
        return cls._get_metadata_path(map_name, mapset).exists()

    # ---------- Load ----------

    @classmethod
    def load(cls, map_name: str, mapset: str | None = None) -> HyperMetadata:
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
    def _load_from_json(cls, path: Path) -> HyperMetadata:
        """Load metadata from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)

        meta = cls()
        meta.schema_version = data.get("schema_version", "unknown")
        meta.dataset_id = str(data.get("dataset_id") or cls.new_dataset_id())
        if "derived" in data:
            meta.derived = bool(data.get("derived"))
        else:
            meta.derived = cls._is_derived_from_history(
                data.get("processing_history", [])
            )

        # New schema (top-level dataset fields)
        if "dataset" not in data:
            inherited_data_type, has_inherited_data_type = cls.resolve_inherited_value(
                data, "data_type"
            )
            if "data_type" in data:
                meta.data_type = str(data.get("data_type") or "spectral")
            elif has_inherited_data_type and inherited_data_type is not None:
                meta.data_type = str(inherited_data_type)
            else:
                meta.data_type = "spectral"

            inherited_sensor, has_inherited_sensor = cls.resolve_inherited_value(
                data, "sensor"
            )
            meta.sensor = (
                data.get("sensor")
                if "sensor" in data
                else inherited_sensor
                if has_inherited_sensor
                else None
            )

            inherited_wu, has_inherited_wu = cls.resolve_inherited_value(
                data, "wavelength_units"
            )
            if "wavelength_units" in data and data.get("wavelength_units") is not None:
                meta.wavelength_units = str(data.get("wavelength_units"))
            elif has_inherited_wu and inherited_wu is not None:
                meta.wavelength_units = str(inherited_wu)
            else:
                meta.wavelength_units = "nm"

            inherited_rq, has_inherited_rq = cls.resolve_inherited_value(
                data, "radiometric_quantity"
            )
            meta.radiometric_quantity = (
                data.get("radiometric_quantity")
                if "radiometric_quantity" in data
                else inherited_rq
                if has_inherited_rq
                else None
            )

            inherited_ru, has_inherited_ru = cls.resolve_inherited_value(
                data, "radiometric_units"
            )
            meta.radiometric_units = (
                data.get("radiometric_units")
                if "radiometric_units" in data
                else inherited_ru
                if has_inherited_ru
                else None
            )

            inherited_region, has_inherited_region = cls.resolve_inherited_value(
                data, "region"
            )
            if "region" in data:
                meta.region = data.get("region")
            else:
                meta.region = inherited_region if has_inherited_region else None

            inherited_bands, has_inherited_bands = cls.resolve_inherited_value(
                data, "bands"
            )
            if "bands" in data and isinstance(data.get("bands"), dict):
                bands = data.get("bands", {})
            elif has_inherited_bands and isinstance(inherited_bands, dict):
                bands = inherited_bands
            else:
                bands = {}
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

            dr_meta = data.get("dimensionality_reduction")
            if isinstance(dr_meta, dict) and dr_meta:
                meta.dimensionality_reduction = copy.deepcopy(dr_meta)
                n_components = dr_meta.get("n_components")
                if n_components is not None:
                    try:
                        meta.n_components = int(n_components)
                    except (TypeError, ValueError):
                        pass
                explained = dr_meta.get("explained_variance_ratio")
                if isinstance(explained, list):
                    meta.explained_variance_ratio = explained
            else:
                meta.dimensionality_reduction = None

            meta.processing_history = cls._normalize_history_entries(
                data.get("processing_history", [])
            )

            input_meta = data.get("input_datasets_metadata", {})
            meta.input_datasets_metadata = (
                input_meta if isinstance(input_meta, dict) else {}
            )

            ext_raw = data.get("extended_metadata", {})
            ext_raw = ext_raw if isinstance(ext_raw, dict) else {}
            lineage_root = {
                "processing_history": meta.processing_history,
                "input_datasets_metadata": meta.input_datasets_metadata,
            }
            inherited_ext, has_inherited_ext = cls.resolve_inherited_value(
                lineage_root, "extended_metadata"
            )
            if has_inherited_ext and isinstance(inherited_ext, dict):
                ext = copy.deepcopy(inherited_ext)
                cls._deep_merge_dict(ext, ext_raw)
                meta.extended_metadata = ext
            else:
                meta.extended_metadata = ext_raw
            meta.acquisition_datetime = data.get("acquisition_datetime")
            if meta.acquisition_datetime is None:
                acquisition = meta.extended_metadata.get("acquisition", {})
                if isinstance(acquisition, dict):
                    meta.acquisition_datetime = acquisition.get("start_time_utc")
            if meta.acquisition_datetime is None:
                inherited_acq, has_inherited_acq = cls.resolve_inherited_value(
                    data, "acquisition_datetime"
                )
                if has_inherited_acq:
                    meta.acquisition_datetime = inherited_acq
            cls._set_unified_geometry(
                meta.extended_metadata,
                solar_zenith_angle=data.get("solar_zenith_angle"),
                solar_azimuth_angle=data.get("solar_azimuth_angle"),
                satellite_zenith_angle=data.get("satellite_zenith_angle"),
                satellite_azimuth_angle=data.get("satellite_azimuth_angle"),
                skip_existing=True,
            )
            return meta

        # Legacy schema fallback (dataset + bands + components)
        ds = data.get("dataset", {})
        meta.sensor = ds.get("sensor")
        meta.wavelength_units = ds.get("wavelength_units", "nm")
        meta.radiometric_quantity = ds.get("radiometric_quantity")
        meta.radiometric_units = ds.get("radiometric_units")
        meta.acquisition_datetime = ds.get("acquisition_datetime")
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

        dr_meta = data.get("dimensionality_reduction")
        if isinstance(dr_meta, dict) and dr_meta:
            meta.dimensionality_reduction = copy.deepcopy(dr_meta)
            n_components = dr_meta.get("n_components")
            if n_components is not None:
                try:
                    meta.n_components = int(n_components)
                except (TypeError, ValueError):
                    pass
            explained = dr_meta.get("explained_variance_ratio")
            if isinstance(explained, list):
                meta.explained_variance_ratio = explained
        else:
            meta.dimensionality_reduction = None

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
        ext = data.get("extended_metadata", {})
        meta.extended_metadata = ext if isinstance(ext, dict) else {}
        input_meta = data.get("input_datasets_metadata", {})
        meta.input_datasets_metadata = (
            input_meta if isinstance(input_meta, dict) else {}
        )
        if meta.acquisition_datetime is None:
            acquisition = meta.extended_metadata.get("acquisition", {})
            if isinstance(acquisition, dict):
                meta.acquisition_datetime = acquisition.get("start_time_utc")
        cls._set_unified_geometry(
            meta.extended_metadata,
            solar_zenith_angle=ds.get("solar_zenith_angle"),
            solar_azimuth_angle=ds.get("solar_azimuth_angle"),
            satellite_zenith_angle=ds.get("satellite_zenith_angle"),
            satellite_azimuth_angle=ds.get("satellite_azimuth_angle"),
            skip_existing=True,
        )
        return meta

    # ---------- Save ----------

    def save(
        self,
        map_name: str,
        mapset: str | None = None,
        *,
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
        # Enforce provenance rule: datasets with lineage inputs are derived.
        self.derived = bool(self.derived) or self._is_derived_from_history(
            self.processing_history
        )

        self.set_extended_value("acquisition.start_time_utc", self.acquisition_datetime)
        self.input_datasets_metadata = {}
        dataset_index: dict[str, dict[str, Any]] = {}
        if self._is_derived_from_history(self.processing_history):
            try:
                dataset_index, _ = self.discover_dataset_index()
                snapshots, missing_ids = self.collect_input_datasets_metadata(
                    {"processing_history": self.processing_history},
                    dataset_index,
                )
                self.input_datasets_metadata = snapshots
                if missing_ids:
                    joined = ", ".join(missing_ids)
                    gs.warning(
                        f"Input dataset metadata snapshots not found for dataset_id(s): {joined}"
                    )
            except Exception as error:
                gs.warning(
                    f"Failed to collect input dataset metadata snapshots: {error}"
                )

        region = self._get_region_json(map_name, mapset) if save_region else self.region
        self.region = region

        normalized_history = self._normalize_history_entries(self.processing_history)

        bands_data: dict[str, Any] = {}
        if self.n_bands_source is not None:
            bands_data["count"] = int(self.n_bands_source)
        if self.n_bands_valid is not None:
            bands_data["count_valid"] = int(self.n_bands_valid)
        if self.wavelengths is not None:
            bands_data["wavelength"] = self.wavelengths
        if self.fwhm is not None:
            bands_data["fwhm"] = self.fwhm
        if self.validity is not None:
            bands_data["validity"] = [bool(v) for v in self.validity]
        if self.component_labels is not None:
            bands_data["labels"] = self.component_labels

        # Build JSON structure (new schema)
        data = {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id or self.new_dataset_id(),
            "derived": bool(self.derived),
            "processing_history": normalized_history,
        }

        if self.input_datasets_metadata:
            data["input_datasets_metadata"] = self.input_datasets_metadata

        if (
            isinstance(self.dimensionality_reduction, dict)
            and self.dimensionality_reduction
        ):
            data["dimensionality_reduction"] = copy.deepcopy(
                self.dimensionality_reduction
            )

        if not bool(self.derived):
            data.update(
                {
                    "data_type": self.data_type or "spectral",
                    "sensor": self.sensor,
                    "wavelength_units": self.wavelength_units,
                    "radiometric_quantity": self.radiometric_quantity,
                    "radiometric_units": self.radiometric_units,
                    "region": self.region,
                    "bands": bands_data,
                    "extended_metadata": self.extended_metadata,
                }
            )
        else:
            lineage_root = {
                "processing_history": normalized_history,
                "input_datasets_metadata": self.input_datasets_metadata,
            }

            candidates = {
                "data_type": self.data_type,
                "sensor": self.sensor,
                "wavelength_units": self.wavelength_units,
                "radiometric_quantity": self.radiometric_quantity,
                "radiometric_units": self.radiometric_units,
                "region": self.region,
                "bands": bands_data,
            }
            for key, value in candidates.items():
                if value is None:
                    continue
                if isinstance(value, dict) and not value:
                    continue
                inherited_value, has_inherited = self.resolve_inherited_value(
                    lineage_root,
                    key,
                    dataset_index=dataset_index,
                )
                if has_inherited and value == inherited_value:
                    continue
                data[key] = value

            current_ext = (
                self.extended_metadata
                if isinstance(self.extended_metadata, dict)
                else {}
            )
            if current_ext:
                inherited_ext, has_inherited_ext = self.resolve_inherited_value(
                    lineage_root,
                    "extended_metadata",
                    dataset_index=dataset_index,
                )
                if has_inherited_ext and isinstance(inherited_ext, dict):
                    diff_ext = self._dict_diff(current_ext, inherited_ext)
                else:
                    diff_ext = copy.deepcopy(current_ext)
                if diff_ext:
                    data["extended_metadata"] = diff_ext

        # Write JSON
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def _get_region_json(
        cls, _map_name: str, _mapset: str | None = None
    ) -> dict[str, Any] | None:
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

    def get_wavelengths_array(self) -> np.ndarray | None:
        """Return wavelengths as numpy array (None values become NaN)."""
        if self.wavelengths is None:
            return None
        values = list(self.wavelengths)
        if self.validity is not None and len(self.validity) == len(values):
            values = [w for i, w in enumerate(values) if bool(self.validity[i])]
        return np.array(
            [w if w is not None else np.nan for w in values], dtype=np.float32
        )

    def get_fwhm_array(self) -> np.ndarray | None:
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
        self, min_wl: float | None = None, max_wl: float | None = None
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
        self, min_wl: float | None = None, max_wl: float | None = None
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
        module: str | None = None,
        params: dict | None = None,
        timestamp: str | None = None,
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
        inputs: list[dict[str, Any]] | None = None,
        outputs: list[dict[str, Any]] | None = None,
        timestamp: str | None = None,
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

    def validate(self, *, require_wavelengths: bool = True) -> list[str]:
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
                    issues.append(
                        "Wavelength and validity arrays have different lengths"
                    )

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
        sensor: str | None = None,
        radiometric_quantity: str | None = None,
        radiometric_units: str | None = None,
        acquisition_datetime: str | None = None,
        solar_zenith_angle: float | None = None,
        solar_azimuth_angle: float | None = None,
        satellite_zenith_angle: float | None = None,
        satellite_azimuth_angle: float | None = None,
    ) -> HyperMetadata:
        """Create metadata for spectral (hyperspectral) data."""
        meta = cls()
        meta.derived = False
        meta.data_type = "spectral"
        meta.sensor = sensor
        meta.radiometric_quantity = radiometric_quantity
        meta.radiometric_units = radiometric_units
        meta.acquisition_datetime = acquisition_datetime
        cls._set_unified_geometry(
            meta.extended_metadata,
            solar_zenith_angle=solar_zenith_angle,
            solar_azimuth_angle=solar_azimuth_angle,
            satellite_zenith_angle=satellite_zenith_angle,
            satellite_azimuth_angle=satellite_azimuth_angle,
        )
        meta.set_wavelengths(wavelengths)
        if fwhm is not None:
            meta.set_fwhm(fwhm)
        return meta

    @classmethod
    def for_components(
        cls,
        n_components: int,
        explained_variance_ratio=None,
    ) -> HyperMetadata:
        """Create metadata for dimensionality reduction output (PCA, etc.)."""
        meta = cls()
        meta.derived = True
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
    def _parse_timestamp(ts: str | None) -> datetime:
        """Parse ISO timestamp for sorting; invalid timestamps are ordered last."""
        if not ts:
            return datetime.max.replace(tzinfo=timezone.utc)
        text = str(ts).strip()
        if not text:
            return datetime.max.replace(tzinfo=timezone.utc)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            value = datetime.fromisoformat(text)
        except ValueError:
            return datetime.max.replace(tzinfo=timezone.utc)
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _is_derived_from_history(entries: list[Any]) -> bool:
        """Infer derived flag from history when explicit flag is missing."""
        for step in entries or []:
            if not isinstance(step, dict):
                continue
            if step.get("inputs"):
                return True
        return False

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
                        "timestamp": step.get("timestamp")
                        or datetime.now().isoformat(),
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

    @staticmethod
    def _deep_merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> None:
        """Deep-merge dicts; None leaf values are ignored."""
        for key, value in src.items():
            if isinstance(value, dict):
                child = dst.get(key)
                if not isinstance(child, dict):
                    child = {}
                    dst[key] = child
                HyperMetadata._deep_merge_dict(child, value)
            elif value is not None:
                dst[key] = value

    @staticmethod
    def _dict_diff(
        current: dict[str, Any], inherited: dict[str, Any]
    ) -> dict[str, Any]:
        """Return keys from current that differ from inherited."""
        out: dict[str, Any] = {}
        for key, value in current.items():
            inherited_value = (
                inherited.get(key) if isinstance(inherited, dict) else None
            )
            if isinstance(value, dict):
                if isinstance(inherited_value, dict):
                    child = HyperMetadata._dict_diff(value, inherited_value)
                    if child:
                        out[key] = child
                else:
                    out[key] = copy.deepcopy(value)
                continue
            if value != inherited_value:
                out[key] = copy.deepcopy(value)
        return out

    @classmethod
    def _direct_input_dataset_ids(cls, data: dict[str, Any]) -> list[str]:
        """Collect unique direct input dataset IDs from local processing history."""
        out: list[str] = []
        seen: set[str] = set()
        for step in data.get("processing_history", []) or []:
            if not isinstance(step, dict):
                continue
            for inp in cls._normalize_io_refs(step.get("inputs") or []):
                dataset_id = inp.get("id")
                if not dataset_id or dataset_id in seen:
                    continue
                seen.add(dataset_id)
                out.append(dataset_id)
        return out

    @classmethod
    def _resolve_dataset_data(
        cls,
        dataset_id: str,
        embedded_snapshots: dict[str, dict[str, Any]],
        dataset_index: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        """Resolve one dataset JSON record from index or embedded snapshots."""
        if dataset_index and dataset_id in dataset_index:
            record = dataset_index.get(dataset_id) or {}
            data = record.get("data")
            if isinstance(data, dict):
                return data
        snapshot = embedded_snapshots.get(dataset_id)
        if isinstance(snapshot, dict):
            return snapshot
        return None

    @classmethod
    def resolve_inherited_value(
        cls,
        root_data: dict[str, Any],
        key: str,
        dataset_index: dict[str, dict[str, Any]] | None = None,
    ) -> tuple[Any, bool]:
        """Resolve inherited value by following input lineage recursively.

        Rules:
        - If key exists in current dataset and is not None, use it.
        - For single-input chains, inherit recursively.
        - For multiple inputs, inherit only when all resolved input values are equal.
        """
        embedded_snapshots = root_data.get("input_datasets_metadata")
        if not isinstance(embedded_snapshots, dict):
            embedded_snapshots = {}

        visiting: set[str] = set()

        def _visit(data: dict[str, Any] | None) -> tuple[Any, bool]:
            if not isinstance(data, dict):
                return None, False

            if key in data and data.get(key) is not None:
                return copy.deepcopy(data.get(key)), True

            marker = str(data.get("dataset_id") or f"obj:{id(data)}")
            if marker in visiting:
                return None, False

            visiting.add(marker)
            try:
                values = []
                for input_id in cls._direct_input_dataset_ids(data):
                    input_data = cls._resolve_dataset_data(
                        input_id,
                        embedded_snapshots,
                        dataset_index=dataset_index,
                    )
                    value, found = _visit(input_data)
                    if found:
                        values.append(value)

                if not values:
                    return None, False

                first = values[0]
                if all(value == first for value in values[1:]):
                    return copy.deepcopy(first), True
                return None, False
            finally:
                visiting.discard(marker)

        return _visit(root_data)

    @staticmethod
    def _set_unified_geometry(
        extended_metadata: dict[str, Any],
        *,
        solar_zenith_angle: float | None = None,
        solar_azimuth_angle: float | None = None,
        satellite_zenith_angle: float | None = None,
        satellite_azimuth_angle: float | None = None,
        skip_existing: bool = False,
    ) -> None:
        """Store geometry angles in unified extended_metadata.geometry.* keys."""
        if not isinstance(extended_metadata, dict):
            return

        geometry = extended_metadata.setdefault("geometry", {})
        if not isinstance(geometry, dict):
            geometry = {}
            extended_metadata["geometry"] = geometry

        for key, value in (
            ("sun_zenith_deg", solar_zenith_angle),
            ("sun_azimuth_deg", solar_azimuth_angle),
            ("view_zenith_deg", satellite_zenith_angle),
            ("view_azimuth_deg", satellite_azimuth_angle),
        ):
            if value is None:
                continue
            try:
                cast_value = float(value)
            except (TypeError, ValueError):
                continue
            if skip_existing and key in geometry and geometry.get(key) is not None:
                continue
            geometry[key] = cast_value

    def set_extended_value(
        self,
        key_path: str,
        value: Any,
        *,
        skip_none: bool = True,
    ) -> None:
        """Set one extended metadata value by dotted path."""
        if skip_none and value is None:
            return
        parts = [p for p in str(key_path).split(".") if p]
        if not parts:
            return
        node = self.extended_metadata
        for part in parts[:-1]:
            child = node.get(part)
            if not isinstance(child, dict):
                child = {}
                node[part] = child
            node = child
        node[parts[-1]] = value

    def set_extended_form_value(
        self,
        key_path: str,
        *,
        value: Any = None,
        form: str | None = None,
        source: str | None = None,
    ) -> None:
        """Set `<key>.value/.form/.source` triplet for map-vs-scalar fields."""
        self.set_extended_value(f"{key_path}.value", value, skip_none=True)
        self.set_extended_value(f"{key_path}.form", form, skip_none=True)
        self.set_extended_value(f"{key_path}.source", source, skip_none=True)

    def merge_extended_metadata(self, payload: dict[str, Any]) -> None:
        """Deep-merge extended metadata payload, skipping None leaf values."""
        if not isinstance(payload, dict):
            return

        def merge(dst: dict[str, Any], src: dict[str, Any]) -> None:
            for key, value in src.items():
                if isinstance(value, dict):
                    child = dst.get(key)
                    if not isinstance(child, dict):
                        child = {}
                        dst[key] = child
                    merge(child, value)
                elif value is not None:
                    dst[key] = value

        merge(self.extended_metadata, payload)

    # ---------- Dataset graph helpers ----------

    @classmethod
    def discover_dataset_index(
        cls,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
        """
        Build dataset_id -> metadata record index by scanning current LOCATION mapsets.
        Returns (index, duplicates).
        """
        env = gs.gisenv()
        location_path = Path(env["GISDBASE"]) / env["LOCATION_NAME"]
        index: dict[str, dict[str, Any]] = {}
        duplicates: dict[str, list[str]] = {}

        for mapset_dir in location_path.iterdir():
            if not mapset_dir.is_dir():
                continue
            grid3_dir = mapset_dir / "grid3"
            if not grid3_dir.is_dir():
                continue
            for map_dir in grid3_dir.iterdir():
                if not map_dir.is_dir():
                    continue
                meta_path = map_dir / METADATA_FILENAME
                if not meta_path.is_file():
                    continue
                try:
                    with open(meta_path, "r") as f:
                        data = json.load(f)
                except Exception:
                    continue

                dataset_id = data.get("dataset_id")
                if not dataset_id:
                    continue
                full_map_name = f"{map_dir.name}@{mapset_dir.name}"
                if dataset_id in index:
                    duplicates.setdefault(
                        dataset_id, [index[dataset_id]["map_name"]]
                    ).append(full_map_name)
                    continue
                index[dataset_id] = {
                    "map_name": full_map_name,
                    "data": data,
                    "path": str(meta_path),
                }
        return index, duplicates

    @classmethod
    def resolve_history_names(
        cls,
        history_entries: list[dict[str, Any]],
        dataset_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Resolve history IO map names from dataset ids for display."""
        out = []
        for step in history_entries or []:
            step_out = {
                "command": step.get("command"),
                "timestamp": step.get("timestamp"),
                "inputs": cls._normalize_io_refs(step.get("inputs") or []),
                "outputs": cls._normalize_io_refs(step.get("outputs") or []),
            }
            for side in ("inputs", "outputs"):
                for ref in step_out[side]:
                    ref_id = ref.get("id")
                    if ref_id and ref_id in dataset_index:
                        ref["map_name"] = dataset_index[ref_id]["map_name"]
            out.append(step_out)
        return out

    @classmethod
    def collect_input_datasets_metadata(
        cls,
        root_data: dict[str, Any],
        dataset_index: dict[str, dict[str, Any]],
    ) -> tuple[dict[str, dict[str, Any]], list[str]]:
        """Collect full metadata snapshots for all input datasets recursively."""
        snapshots: dict[str, dict[str, Any]] = {}
        missing_ids: set[str] = set()
        visited_dataset_ids: set[str] = set()

        root_produced_ids = set()
        for step in root_data.get("processing_history", []) or []:
            if not isinstance(step, dict):
                continue
            for out in cls._normalize_io_refs(step.get("outputs") or []):
                out_id = out.get("id")
                if out_id:
                    root_produced_ids.add(out_id)

        def visit_dataset(dataset_id: str | None) -> None:
            if not dataset_id or dataset_id in visited_dataset_ids:
                return
            if dataset_id in root_produced_ids:
                return
            visited_dataset_ids.add(dataset_id)

            record = dataset_index.get(dataset_id)
            if not record:
                missing_ids.add(dataset_id)
                return

            data = record.get("data")
            if not isinstance(data, dict):
                missing_ids.add(dataset_id)
                return

            snapshot = copy.deepcopy(data)
            snapshot.pop("input_datasets_metadata", None)
            snapshots[dataset_id] = snapshot

            for step in snapshot.get("processing_history", []) or []:
                if not isinstance(step, dict):
                    continue
                for inp in cls._normalize_io_refs(step.get("inputs") or []):
                    visit_dataset(inp.get("id"))

        for step in root_data.get("processing_history", []) or []:
            if not isinstance(step, dict):
                continue
            for inp in cls._normalize_io_refs(step.get("inputs") or []):
                visit_dataset(inp.get("id"))

        ordered = {
            dataset_id: snapshots[dataset_id] for dataset_id in sorted(snapshots)
        }
        return ordered, sorted(missing_ids)

    @classmethod
    def collect_aggregated_history(
        cls,
        root_data: dict[str, Any],
        dataset_index: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Recursively collect all history entries from origin to current dataset,
        following inputs[].id references.
        """
        root_id = root_data.get("dataset_id")
        embedded_snapshots = root_data.get("input_datasets_metadata")
        if not isinstance(embedded_snapshots, dict):
            embedded_snapshots = {}
        root_produced_ids = set()
        for step in root_data.get("processing_history", []) or []:
            if not isinstance(step, dict):
                continue
            for out in cls._normalize_io_refs(step.get("outputs") or []):
                out_id = out.get("id")
                if out_id:
                    root_produced_ids.add(out_id)
        visited_dataset_ids = set()
        collected = []
        order = 0

        def visit_dataset(dataset_id: str | None):
            nonlocal order
            if not dataset_id or dataset_id in visited_dataset_ids:
                return
            if dataset_id != root_id and dataset_id in root_produced_ids:
                return
            visited_dataset_ids.add(dataset_id)

            record = dataset_index.get(dataset_id)
            if record:
                data = record["data"]
            elif dataset_id == root_id:
                data = root_data
            else:
                data = embedded_snapshots.get(dataset_id)
            if data is None:
                return

            for step in data.get("processing_history", []) or []:
                entry = {
                    "command": step.get("command"),
                    "timestamp": step.get("timestamp"),
                    "inputs": cls._normalize_io_refs(step.get("inputs") or []),
                    "outputs": cls._normalize_io_refs(step.get("outputs") or []),
                }
                collected.append(
                    (cls._parse_timestamp(entry.get("timestamp")), order, entry)
                )
                order += 1
                for inp in entry["inputs"]:
                    visit_dataset(inp.get("id"))

        visit_dataset(root_id)
        collected.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in collected]

    @classmethod
    def summarize_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Build summary payload from raw metadata."""
        bands = data.get("bands") or {}
        if not isinstance(bands, dict) or not bands:
            inherited_bands, has_inherited_bands = cls.resolve_inherited_value(
                data, "bands"
            )
            if has_inherited_bands and isinstance(inherited_bands, dict):
                bands = inherited_bands
            else:
                bands = {}

        wavelengths = [
            w for w in (bands.get("wavelength") or []) if isinstance(w, (int, float))
        ]

        data_type = data.get("data_type")
        if data_type is None:
            inherited_data_type, has_inherited_data_type = cls.resolve_inherited_value(
                data, "data_type"
            )
            if has_inherited_data_type:
                data_type = inherited_data_type

        sensor = data.get("sensor")
        if sensor is None:
            inherited_sensor, has_inherited_sensor = cls.resolve_inherited_value(
                data, "sensor"
            )
            if has_inherited_sensor:
                sensor = inherited_sensor

        wavelength_units = data.get("wavelength_units")
        if wavelength_units is None:
            inherited_wu, has_inherited_wu = cls.resolve_inherited_value(
                data, "wavelength_units"
            )
            if has_inherited_wu:
                wavelength_units = inherited_wu

        radiometric_quantity = data.get("radiometric_quantity")
        if radiometric_quantity is None:
            inherited_rq, has_inherited_rq = cls.resolve_inherited_value(
                data, "radiometric_quantity"
            )
            if has_inherited_rq:
                radiometric_quantity = inherited_rq

        radiometric_units = data.get("radiometric_units")
        if radiometric_units is None:
            inherited_ru, has_inherited_ru = cls.resolve_inherited_value(
                data, "radiometric_units"
            )
            if has_inherited_ru:
                radiometric_units = inherited_ru

        ext = data.get("extended_metadata")
        if not isinstance(ext, dict):
            ext = {}
        inherited_ext, has_inherited_ext = cls.resolve_inherited_value(
            data, "extended_metadata"
        )
        if has_inherited_ext and isinstance(inherited_ext, dict):
            merged_ext = copy.deepcopy(inherited_ext)
            cls._deep_merge_dict(merged_ext, ext)
            ext = merged_ext

        acquisition_datetime = data.get("acquisition_datetime")
        if acquisition_datetime is None:
            acquisition = ext.get("acquisition", {})
            if isinstance(acquisition, dict):
                acquisition_datetime = acquisition.get("start_time_utc")
        if acquisition_datetime is None:
            inherited_acq, has_inherited_acq = cls.resolve_inherited_value(
                data, "acquisition_datetime"
            )
            if has_inherited_acq:
                acquisition_datetime = inherited_acq

        return {
            "schema_version": data.get("schema_version"),
            "dataset_id": data.get("dataset_id"),
            "derived": data.get("derived"),
            "data_type": data_type,
            "sensor": sensor,
            "bands_count": bands.get("count"),
            "bands_count_valid": bands.get("count_valid"),
            "wavelength_units": wavelength_units,
            "radiometric_quantity": radiometric_quantity,
            "radiometric_units": radiometric_units,
            "acquisition_datetime": acquisition_datetime,
            "wavelength_min": min(wavelengths) if wavelengths else None,
            "wavelength_max": max(wavelengths) if wavelengths else None,
            "processing_steps_local": len(data.get("processing_history", []) or []),
        }

    @classmethod
    def build_band_rows(
        cls,
        data: dict[str, Any],
        wavelength_range: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build band rows for listing output."""
        bands = data.get("bands") or {}
        if not isinstance(bands, dict) or not bands:
            inherited_bands, has_inherited_bands = cls.resolve_inherited_value(
                data, "bands"
            )
            if has_inherited_bands and isinstance(inherited_bands, dict):
                bands = inherited_bands
            else:
                bands = {}

        wavelengths = bands.get("wavelength") or []
        fwhm = bands.get("fwhm") or []
        validity = bands.get("validity") or []
        count = bands.get("count")

        if not wavelengths and isinstance(count, int) and count > 0:
            rows = []
            for i in range(1, count + 1):
                rows.append(
                    {
                        "index": i,
                        "wavelength": None,
                        "fwhm": None,
                        "validity": validity[i - 1] if i - 1 < len(validity) else True,
                    }
                )
            return rows

        wl_min, wl_max = None, None
        if wavelength_range:
            try:
                parts = wavelength_range.split("-")
                wl_min = float(parts[0]) if parts[0] else None
                wl_max = float(parts[1]) if len(parts) > 1 and parts[1] else None
            except ValueError as e:
                raise ValueError(f"Invalid wavelength range: {wavelength_range}") from e

        rows = []
        for i, wl in enumerate(wavelengths, start=1):
            if wl is None:
                continue
            if wl_min is not None and wl < wl_min:
                continue
            if wl_max is not None and wl > wl_max:
                continue
            rows.append(
                {
                    "index": i,
                    "wavelength": wl,
                    "fwhm": fwhm[i - 1] if i - 1 < len(fwhm) else None,
                    "validity": validity[i - 1] if i - 1 < len(validity) else None,
                }
            )
        return rows

    @classmethod
    def validate_strict(
        cls,
        meta: HyperMetadata,
        raw_data: dict[str, Any],
        map_name: str,
        dataset_index: dict[str, dict[str, Any]],
        duplicate_dataset_ids: dict[str, list[str]] | None = None,
    ) -> list[str]:
        """Validate strict schema + lineage consistency."""
        issues = []
        issues.extend(meta.validate(require_wavelengths=False))

        derived_flag = bool(raw_data.get("derived"))

        required = ["schema_version", "dataset_id", "processing_history"]
        if not derived_flag:
            required.extend(["data_type", "bands"])

        for key in required:
            if key not in raw_data:
                issues.append(f"Missing required top-level key: {key}")

        if "derived" in raw_data and not isinstance(raw_data.get("derived"), bool):
            issues.append("derived must be boolean")

        bands = raw_data.get("bands") or {}
        if (not isinstance(bands, dict) or not bands) and derived_flag:
            inherited_bands, has_inherited_bands = cls.resolve_inherited_value(
                raw_data,
                "bands",
                dataset_index=dataset_index,
            )
            if has_inherited_bands and isinstance(inherited_bands, dict):
                bands = inherited_bands
            else:
                bands = {}
        data_type = raw_data.get("data_type")
        if data_type is None:
            inherited_data_type, has_inherited_data_type = cls.resolve_inherited_value(
                raw_data,
                "data_type",
                dataset_index=dataset_index,
            )
            if has_inherited_data_type:
                data_type = inherited_data_type
        count = bands.get("count")
        count_valid = bands.get("count_valid")
        wavelengths = bands.get("wavelength")
        fwhm = bands.get("fwhm")
        validity = bands.get("validity")

        if count is None:
            issues.append("bands.count is missing")
        if count_valid is None:
            issues.append("bands.count_valid is missing")
        if data_type == "spectral" and wavelengths is None:
            issues.append("Missing wavelengths")
        if wavelengths is not None and not isinstance(wavelengths, list):
            issues.append("bands.wavelength must be an array")
        if fwhm is not None and not isinstance(fwhm, list):
            issues.append("bands.fwhm must be an array")
        if validity is not None and not isinstance(validity, list):
            issues.append("bands.validity must be an array")

        if isinstance(count, int) and count >= 0:
            if isinstance(wavelengths, list) and len(wavelengths) != count:
                issues.append("bands.count does not match len(bands.wavelength)")
            if isinstance(fwhm, list) and len(fwhm) != count:
                issues.append("bands.count does not match len(bands.fwhm)")
            if isinstance(validity, list) and len(validity) != count:
                issues.append("bands.count does not match len(bands.validity)")

        if (
            isinstance(count, int)
            and isinstance(count_valid, int)
            and count_valid > count
        ):
            issues.append("bands.count_valid cannot be larger than bands.count")
        if isinstance(validity, list) and isinstance(count_valid, int):
            valid_sum = int(sum(bool(v) for v in validity))
            if valid_sum != count_valid:
                issues.append("bands.count_valid does not match sum(bands.validity)")

        try:
            info = gs.parse_command("r3.info", map=map_name, flags="g")
            depth = int(float(info.get("depths")))
            expected_depth = count if isinstance(count, int) else None
            if expected_depth is not None and depth != expected_depth:
                issues.append(
                    f"Raster depth mismatch: depths={depth}, expected={expected_depth}"
                )
        except Exception as exc:
            issues.append(f"Could not validate raster depth with r3.info: {exc}")

        input_datasets_metadata = raw_data.get("input_datasets_metadata")
        embedded_snapshot_ids = set()
        if input_datasets_metadata is not None and not isinstance(
            input_datasets_metadata, dict
        ):
            issues.append(
                "input_datasets_metadata must be an object keyed by dataset_id"
            )
        elif isinstance(input_datasets_metadata, dict):
            for dsid, snapshot in input_datasets_metadata.items():
                embedded_snapshot_ids.add(str(dsid))
                if not isinstance(snapshot, dict):
                    issues.append(f"input_datasets_metadata[{dsid}] must be an object")
                    continue
                if "input_datasets_metadata" in snapshot:
                    issues.append(
                        f"input_datasets_metadata[{dsid}] must not contain nested input_datasets_metadata"
                    )

        aggregated = cls.collect_aggregated_history(raw_data, dataset_index)
        producer_counts = {}
        referenced_input_ids = set()
        for step in aggregated:
            for out in step.get("outputs", []) or []:
                out_id = out.get("id")
                if out_id:
                    producer_counts[out_id] = producer_counts.get(out_id, 0) + 1
            for inp in step.get("inputs", []) or []:
                in_id = inp.get("id")
                if in_id:
                    referenced_input_ids.add(in_id)

        for dataset_id, n_producers in producer_counts.items():
            if n_producers > 1:
                issues.append(
                    f"Dataset '{dataset_id}' has multiple producing history entries ({n_producers})"
                )

        root_dataset_id = raw_data.get("dataset_id")
        if root_dataset_id:
            n_root = producer_counts.get(root_dataset_id, 0)
            if n_root == 0:
                issues.append(
                    f"Current dataset_id '{root_dataset_id}' has no producing history entry"
                )
            elif n_root > 1:
                issues.append(
                    f"Current dataset_id '{root_dataset_id}' has multiple producing history entries ({n_root})"
                )

        for input_id in sorted(referenced_input_ids):
            if (
                input_id not in dataset_index
                and input_id not in producer_counts
                and input_id not in embedded_snapshot_ids
            ):
                issues.append(
                    f"Input dataset_id '{input_id}' cannot be resolved in current LOCATION"
                )

        if duplicate_dataset_ids:
            for dsid, maps in sorted(duplicate_dataset_ids.items()):
                joined = ", ".join(maps)
                issues.append(f"Duplicate dataset_id '{dsid}' found in maps: {joined}")

        unique = []
        seen = set()
        for issue in issues:
            if issue in seen:
                continue
            seen.add(issue)
            unique.append(issue)
        return unique


# ---------- Convenience functions ----------


def load_hyper_metadata(map_name: str, mapset: str | None = None) -> HyperMetadata:
    """Load metadata for a hyperspectral 3D raster."""
    return HyperMetadata.load(map_name, mapset)


def save_hyper_metadata(
    meta: HyperMetadata,
    map_name: str,
    mapset: str | None = None,
    *,
    save_region: bool = False,
) -> None:
    """Save metadata for a hyperspectral 3D raster."""
    meta.save(map_name, mapset, save_region=save_region)


def has_hyper_metadata(map_name: str, mapset: str | None = None) -> bool:
    """Check if a map has hyperspectral JSON metadata."""
    return HyperMetadata.exists(map_name, mapset)


def copy_hyper_metadata(
    src_map: str,
    dst_map: str,
    src_mapset: str | None = None,
    dst_mapset: str | None = None,
) -> None:
    """Copy hyperspectral metadata from one map to another."""
    meta = HyperMetadata.load(src_map, src_mapset)
    meta.save(dst_map, dst_mapset)


def remove_hyper_metadata(map_name: str, mapset: str | None = None) -> bool:
    """Remove hyperspectral metadata file. Returns True if file existed."""
    path = HyperMetadata._get_metadata_path(map_name, mapset)
    if path.exists():
        path.unlink()
        return True
    return False
