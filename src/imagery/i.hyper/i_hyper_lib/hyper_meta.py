#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperspectral metadata management for GRASS GIS i.hyper tools.

Stores metadata in JSON format at: $MAPSET/grid3/<mapname>/hyper.json

Provides:
- HyperMetadata class for reading/writing metadata
- Backward compatibility with legacy r3.support description format
- Forward compatibility via schema versioning
"""

from __future__ import annotations

import json
import os
import re
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

    # Dataset-level (component mode - mutually exclusive with spectral)
    is_components: bool = False
    component_method: Optional[str] = None  # e.g., "pca", "kpca", "fastica"
    source_map: Optional[str] = None  # original map this was derived from

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

        Tries JSON file first, falls back to parsing r3.info description
        for backward compatibility.
        """
        path = cls._get_metadata_path(map_name, mapset)

        if path.exists():
            return cls._load_from_json(path)

        # Fallback: parse legacy format from r3.info
        return cls._load_from_r3info(map_name, mapset)

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
        meta.is_components = ds.get("is_components", False)
        meta.component_method = ds.get("component_method")
        meta.source_map = ds.get("source_map")

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

    @classmethod
    def _load_from_r3info(
        cls, map_name: str, mapset: Optional[str] = None
    ) -> "HyperMetadata":
        """
        Parse legacy metadata from r3.info description/comments.

        Supports formats written by current i.hyper tools:
        - "Band N: <wavelength> nm, FWHM: <fwhm> nm"
        - "Measurement: <quantity>"
        - "Measurement Units: <units>"
        - "Component N: <variance>% variance explained"
        """
        full_name = f"{map_name}@{mapset}" if mapset else map_name

        # Get band count
        info = gs.parse_command("r3.info", flags="g", map=full_name)
        n_bands = int(info.get("depths", 0))

        meta = cls()
        meta.n_bands = n_bands

        # Parse description text
        txt = gs.read_command("r3.info", map=full_name)

        # Wavelength/FWHM pattern
        num = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
        band_pat = re.compile(
            rf"Band\s+(\d+)\s*:\s*({num})\s*nm(?:,\s*FWHM:\s*({num})\s*nm)?",
            re.IGNORECASE,
        )

        # Component pattern (PCA output)
        comp_pat = re.compile(
            rf"Component\s+(\d+)\s*:\s*({num})%?\s*(?:variance\s+explained)?",
            re.IGNORECASE,
        )

        wavelengths = [None] * n_bands
        fwhm = [None] * n_bands
        explained_var = []
        comp_count = 0

        for raw_line in txt.splitlines():
            line = raw_line.strip().strip("| ").rstrip("| ").strip()

            # Band wavelength/FWHM
            m = band_pat.search(line)
            if m:
                idx = int(m.group(1)) - 1  # 0-based
                if 0 <= idx < n_bands:
                    wavelengths[idx] = float(m.group(2))
                    if m.group(3) is not None:
                        fwhm[idx] = float(m.group(3))
                continue

            # Component variance
            m = comp_pat.search(line)
            if m:
                comp_count += 1
                var_pct = float(m.group(2))
                # Convert percentage to ratio if > 1
                explained_var.append(var_pct / 100.0 if var_pct > 1 else var_pct)
                continue

            # Measurement type
            if line.lower().startswith("measurement:"):
                val = line.split(":", 1)[1].strip()
                if val:
                    meta.radiometric_quantity = val
                continue

            # Measurement units
            if line.lower().startswith("measurement units:"):
                val = line.split(":", 1)[1].strip()
                if val and val.lower() not in ("unitless", "none", "units", "1"):
                    meta.radiometric_units = val
                continue

        # Set parsed values
        if any(w is not None for w in wavelengths):
            meta.wavelengths = wavelengths
        if any(f is not None for f in fwhm):
            meta.fwhm = fwhm

        # Detect component mode
        if comp_count > 0:
            meta.is_components = True
            meta.n_components = comp_count
            meta.explained_variance_ratio = explained_var
            # Try to detect method from description
            txt_lower = txt.lower()
            for method in ["pca", "kpca", "kernel pca", "fastica", "nmf", "sparsepca"]:
                if method in txt_lower:
                    meta.component_method = method.replace(" ", "").replace("kernel", "k")
                    break

        return meta

    # ---------- Save ----------

    def save(self, map_name: str, mapset: Optional[str] = None) -> None:
        """
        Save metadata for a hyperspectral 3D raster.

        Writes JSON to grid3/<mapname>/hyper.json and also updates
        r3.support description for backward compatibility.
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

        # Build JSON structure
        data = {
            "schema_version": self.schema_version,
            "dataset": {
                "sensor": self.sensor,
                "wavelength_units": self.wavelength_units,
                "radiometric_quantity": self.radiometric_quantity,
                "radiometric_units": self.radiometric_units,
                "is_components": self.is_components,
                "component_method": self.component_method,
                "source_map": self.source_map,
            },
            "bands": {},
            "components": {},
            "processing_history": self.processing_history,
            "custom": self.custom,
        }

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
        if self.is_components:
            data["components"]["count"] = self.n_components
            if self.explained_variance_ratio is not None:
                data["components"]["explained_variance_ratio"] = (
                    self.explained_variance_ratio
                )
            if self.component_labels is not None:
                data["components"]["labels"] = self.component_labels

        # Write JSON
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        # Also write legacy format to r3.support for backward compatibility
        self._write_legacy_description(map_name, mapset)

    def _write_legacy_description(
        self, map_name: str, mapset: Optional[str] = None
    ) -> None:
        """Write metadata to r3.support description in legacy format."""
        full_name = f"{map_name}@{mapset}" if mapset else map_name
        lines = ["Hyperspectral Metadata:"]

        if self.is_components:
            # Component mode
            method_names = {
                "pca": "Principal Component Analysis (PCA)",
                "kpca": "Kernel PCA",
                "fastica": "FastICA",
                "truncatedsvd": "TruncatedSVD",
                "nmf": "NMF",
                "sparsepca": "SparsePCA",
                "nystroem": "Nystroem",
            }
            method_display = method_names.get(
                self.component_method, self.component_method or "Unknown"
            )
            lines.append(method_display)

            if self.explained_variance_ratio:
                for i, var in enumerate(self.explained_variance_ratio, 1):
                    lines.append(f"Component {i}: {var * 100:.2f}% variance explained")
        else:
            # Spectral mode
            if self.n_bands:
                lines.append(f"Valid Bands: {self.n_bands}")

            if self.radiometric_quantity:
                lines.append(f"Measurement: {self.radiometric_quantity}")

            if self.radiometric_units:
                lines.append(f"Measurement Units: {self.radiometric_units}")

            if self.wavelengths:
                for i, wl in enumerate(self.wavelengths):
                    if wl is not None:
                        fwhm_str = ""
                        if self.fwhm and i < len(self.fwhm) and self.fwhm[i] is not None:
                            fwhm_str = f", FWHM: {self.fwhm[i]} nm"
                        lines.append(f"Band {i + 1}: {wl} nm{fwhm_str}")

        # Determine title
        if self.is_components:
            title = f"{self.component_method.upper() if self.component_method else 'Component'} Output"
        else:
            title = f"{self.sensor} Hyperspectral Data" if self.sensor else "Hyperspectral Data"

        try:
            gs.run_command(
                "r3.support",
                map=full_name,
                title=title,
                description="\n".join(lines),
                vunit="nanometers" if not self.is_components else None,
                quiet=True,
            )
        except Exception:
            pass  # Non-fatal if r3.support fails

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

        if self.is_components:
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
    ) -> "HyperMetadata":
        """Create metadata for spectral (hyperspectral) data."""
        meta = cls()
        meta.sensor = sensor
        meta.radiometric_quantity = radiometric_quantity
        meta.radiometric_units = radiometric_units
        meta.set_wavelengths(wavelengths)
        if fwhm is not None:
            meta.set_fwhm(fwhm)
        return meta

    @classmethod
    def for_components(
        cls,
        n_components: int,
        method: str,
        explained_variance_ratio=None,
        source_map: Optional[str] = None,
    ) -> "HyperMetadata":
        """Create metadata for dimensionality reduction output (PCA, etc.)."""
        meta = cls()
        meta.is_components = True
        meta.component_method = method.lower()
        meta.n_components = n_components
        meta.source_map = source_map
        if explained_variance_ratio is not None:
            meta.set_explained_variance(explained_variance_ratio)
        return meta


# ---------- Convenience functions ----------


def load_hyper_metadata(map_name: str, mapset: Optional[str] = None) -> HyperMetadata:
    """Load metadata for a hyperspectral 3D raster."""
    return HyperMetadata.load(map_name, mapset)


def save_hyper_metadata(
    meta: HyperMetadata, map_name: str, mapset: Optional[str] = None
) -> None:
    """Save metadata for a hyperspectral 3D raster."""
    meta.save(map_name, mapset)


def has_hyper_metadata(map_name: str, mapset: Optional[str] = None) -> bool:
    """Check if a map has hyperspectral metadata (JSON or legacy)."""
    # JSON exists
    if HyperMetadata.exists(map_name, mapset):
        return True

    # Try loading legacy - if wavelengths found, it has metadata
    try:
        meta = HyperMetadata._load_from_r3info(map_name, mapset)
        return meta.wavelengths is not None or meta.is_components
    except Exception:
        return False


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
