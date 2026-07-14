#!/usr/bin/env python3
"""
PRISMA importer

- Reads VNIR/SWIR/PAN cubes + error matrices from PRISMA L2D, L2C, and L1 HDF-EOS5.
- Converts DN->reflectance on demand using product's L2 scale attributes:
    refl = Min + (DN * (Max - Min)) / 65535
- Converts L1 DN->radiance using the required detector scale factor.
- Extracts wavelengths/FWHM from global attributes and filters by *_Flags==1.
- Normalizes VNIR/SWIR arrays to (rows, cols, bands) with bands-last.
- Exposes per-pixel lat/lon grids and scalar corner easting/northing attributes in meters.

Spec assumptions (strict):
- VNIR/SWIR data cubes have dimensions (nEastingPixel, nBands, nNorthingPixel).
- Latitude/Longitude are (nEastingPixel, nNorthingPixel).
- EPSG code is stored in global attribute 'Epsg_Code'.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
import h5py
from pyproj import Transformer
import grass.script as gs

# ---- HDF5 paths (from PRISMA spec for all product types) ----
# L2D paths (original)
HCO_VNIR_DATA_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_Cube"
HCO_SWIR_DATA_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_Cube"
PCO_PAN_DATA_L2D = "/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/PAN_Cube"

HCO_VNIR_ERR_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX"
HCO_SWIR_ERR_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX"
PCO_PAN_ERR_L2D = "/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/PIXEL_L2_ERR_MATRIX"

HCO_LAT_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Latitude"
HCO_LON_L2D = "/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Longitude"
PCO_LAT_L2D = "/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Latitude"
PCO_LON_L2D = "/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Longitude"

# L2C paths (similar to L2D but different swath names)
HCO_VNIR_DATA_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Data Fields/VNIR_Cube"
HCO_SWIR_DATA_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Data Fields/SWIR_Cube"
PCO_PAN_DATA_L2C = "/HDFEOS/SWATHS/PRS_L2C_PCO/Data Fields/PAN_Cube"

HCO_VNIR_ERR_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX"
HCO_SWIR_ERR_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX"
PCO_PAN_ERR_L2C = "/HDFEOS/SWATHS/PRS_L2C_PCO/Data Fields/PIXEL_L2_ERR_MATRIX"

HCO_LAT_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Geolocation Fields/Latitude"
HCO_LON_L2C = "/HDFEOS/SWATHS/PRS_L2C_HCO/Geolocation Fields/Longitude"
PCO_LAT_L2C = "/HDFEOS/SWATHS/PRS_L2C_PCO/Geolocation Fields/Latitude"
PCO_LON_L2C = "/HDFEOS/SWATHS/PRS_L2C_PCO/Geolocation Fields/Longitude"

# L1 paths (completely different structure)
HCO_VNIR_DATA_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/VNIR_Cube"
HCO_SWIR_DATA_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/SWIR_Cube"
PCO_PAN_DATA_L1 = "/HDFEOS/SWATHS/PRS_L1_PCO/Data Fields/PAN_Cube"

HCO_VNIR_ERR_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX"
HCO_SWIR_ERR_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX"
PCO_PAN_ERR_L1 = "/HDFEOS/SWATHS/PRS_L1_PCO/Data Fields/PIXEL_L2_ERR_MATRIX"

HCO_LAT_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Geolocation Fields/Latitude"
HCO_LON_L1 = "/HDFEOS/SWATHS/PRS_L1_HCO/Geolocation Fields/Longitude"
PCO_LAT_L1 = "/HDFEOS/SWATHS/PRS_L1_PCO/Geolocation Fields/Latitude"
PCO_LON_L1 = "/HDFEOS/SWATHS/PRS_L1_PCO/Geolocation Fields/Longitude"


# Product type detection function
def _detect_prisma_product_type(f):
    """Detect PRISMA product type from HDF5 file structure"""
    # Check for L2D first (based on swath names)
    l2d_swath = "/HDFEOS/SWATHS/PRS_L2D_HCO"
    l2c_swath = "/HDFEOS/SWATHS/PRS_L2C_HCO"
    l1_swath = "/HDFEOS/SWATHS/PRS_L1_HCO"

    if l2d_swath in f:
        return "L2D"
    elif l2c_swath in f:
        return "L2C"
    elif l1_swath in f:
        return "L1"
    else:
        return "unknown"


def _get_prisma_paths(product_type):
    """Get appropriate paths for the specified PRISMA product type"""
    if product_type == "L2D":
        return {
            "vnir_data": HCO_VNIR_DATA_L2D,
            "swir_data": HCO_SWIR_DATA_L2D,
            "pan_data": PCO_PAN_DATA_L2D,
            "vnir_err": HCO_VNIR_ERR_L2D,
            "swir_err": HCO_SWIR_ERR_L2D,
            "pan_err": PCO_PAN_ERR_L2D,
            "lat": HCO_LAT_L2D,
            "lon": HCO_LON_L2D,
            "pco_lat": PCO_LAT_L2D,
            "pco_lon": PCO_LON_L2D,
        }
    elif product_type == "L2C":
        return {
            "vnir_data": HCO_VNIR_DATA_L2C,
            "swir_data": HCO_SWIR_DATA_L2C,
            "pan_data": PCO_PAN_DATA_L2C,
            "vnir_err": HCO_VNIR_ERR_L2C,
            "swir_err": HCO_SWIR_ERR_L2C,
            "pan_err": PCO_PAN_ERR_L2C,
            "lat": HCO_LAT_L2C,
            "lon": HCO_LON_L2C,
            "pco_lat": PCO_LAT_L2C,
            "pco_lon": PCO_LON_L2C,
        }
    elif product_type == "L1":
        return {
            "vnir_data": HCO_VNIR_DATA_L1,
            "swir_data": HCO_SWIR_DATA_L1,
            "pan_data": PCO_PAN_DATA_L1,
            "vnir_err": HCO_VNIR_ERR_L1,
            "swir_err": HCO_SWIR_ERR_L1,
            "pan_err": PCO_PAN_ERR_L1,
            "lat": "/HDFEOS/SWATHS/PRS_L1_HCO/Geolocation Fields/Latitude_VNIR",
            "lon": "/HDFEOS/SWATHS/PRS_L1_HCO/Geolocation Fields/Longitude_VNIR",
            "pco_lat": PCO_LAT_L1,
            "pco_lon": PCO_LON_L1,
        }
    else:
        raise ValueError(f"Unknown PRISMA product type: {product_type}")


# ---- Global attributes (per spec) ----
ATTR_CW_VNIR = "List_Cw_Vnir"
ATTR_CW_VNIR_FLAGS = "List_Cw_Vnir_Flags"
ATTR_FWHM_VNIR = "List_Fwhm_Vnir"

ATTR_CW_SWIR = "List_Cw_Swir"
ATTR_CW_SWIR_FLAGS = "List_Cw_Swir_Flags"
ATTR_FWHM_SWIR = "List_Fwhm_Swir"

ATTR_SCALE_VMAX = "L2ScaleVnirMax"
ATTR_SCALE_VMIN = "L2ScaleVnirMin"
ATTR_SCALE_SMAX = "L2ScaleSwirMax"
ATTR_SCALE_SMIN = "L2ScaleSwirMin"
ATTR_SCALE_PMAX = "L2ScalePanMax"
ATTR_SCALE_PMIN = "L2ScalePanMin"
ATTR_SCALE_FACTOR_VNIR = "ScaleFactor_Vnir"
ATTR_SCALE_FACTOR_SWIR = "ScaleFactor_Swir"
ATTR_SCALE_FACTOR_PAN = "ScaleFactor_Pan"

ATTR_CENTER_E = "Product_center_easting"
ATTR_CENTER_N = "Product_center_northing"

ATTR_LL_E = "Product_LLcorner_easting"
ATTR_LL_N = "Product_LLcorner_northing"
ATTR_LR_E = "Product_LRcorner_easting"
ATTR_LR_N = "Product_LRcorner_northing"
ATTR_UL_E = "Product_ULcorner_easting"
ATTR_UL_N = "Product_ULcorner_northing"
ATTR_UR_E = "Product_URcorner_easting"
ATTR_UR_N = "Product_URcorner_northing"

ATTR_CENTER_LAT = "Product_center_lat"
ATTR_CENTER_LON = "Product_center_long"
ATTR_LL_LAT = "Product_LLcorner_lat"
ATTR_LL_LON = "Product_LLcorner_long"
ATTR_LR_LAT = "Product_LRcorner_lat"
ATTR_LR_LON = "Product_LRcorner_long"
ATTR_UL_LAT = "Product_ULcorner_lat"
ATTR_UL_LON = "Product_ULcorner_long"
ATTR_UR_LAT = "Product_URcorner_lat"
ATTR_UR_LON = "Product_URcorner_long"

ATTR_EPSG = "Epsg_Code"  # strict per spec


# ---- Data containers ----
@dataclass
class BandInfo:
    wavelengths_nm: np.ndarray  # (bands_kept,)
    fwhm_nm: np.ndarray  # (bands_kept,)
    present_flags: np.ndarray  # (bands_kept,) all ones after filtering
    # Added: indices of kept bands in the original band axis (0-based)
    kept_indices: np.ndarray  # (bands_kept,)


@dataclass
class PrismaCube:
    name: str  # "VNIR" | "SWIR" | "PAN"
    dn: np.ndarray | None  # VNIR/SWIR: (rows, cols, bands); PAN: (rows, cols)
    err: np.ndarray | None  # same spatial shape; band-dim if provided
    scale_min: float | None
    scale_max: float | None
    scale_factor: float | None = None
    bands: BandInfo | None = None  # None for PAN

    def to_reflectance(self):
        if self.dn is None or self.scale_min is None or self.scale_max is None:
            return None
        return self.scale_min + (
            self.dn.astype(np.float32) * (self.scale_max - self.scale_min) / 65535.0
        )

    def to_radiance(self):
        if self.dn is None:
            return None
        try:
            scale_factor = float(self.scale_factor)
        except (TypeError, ValueError):
            scale_factor = None
        if scale_factor is None or not np.isfinite(scale_factor) or scale_factor <= 0:
            raise ValueError(
                f"Missing or invalid PRISMA L1 {self.name} radiance scale factor."
            )
        return self.dn.astype(np.float32) / scale_factor

    def valid_mask(self):
        return (self.err == 0) if self.err is not None else None


@dataclass
class Geolocation:
    lat: np.ndarray  # (rows, cols)
    lon: np.ndarray  # (rows, cols)
    x_m: np.ndarray | None  # not computed here
    y_m: np.ndarray | None
    utm_epsg: int | None
    center_e: float | None = None
    center_n: float | None = None
    ll_e: float | None = None
    ll_n: float | None = None
    lr_e: float | None = None
    lr_n: float | None = None
    ul_e: float | None = None
    ul_n: float | None = None
    ur_e: float | None = None
    ur_n: float | None = None


@dataclass
class PrismaL2DProduct:
    path: str
    product_type: str
    vnir: PrismaCube | None
    swir: PrismaCube | None
    pan: PrismaCube | None
    hco_geo: Geolocation | None
    pco_geo: Geolocation | None
    attrs: dict[str, Any]


# ---- Internal helpers ----
def _read_attr_as_array(attrs, key):
    if key not in attrs:
        return None
    v = attrs[key]
    if isinstance(v, (bytes, bytearray, str)):
        try:
            s = v.decode() if isinstance(v, (bytes, bytearray)) else v
            parts = [p for p in s.replace(",", " ").split() if p.strip()]
            return (
                np.array([float(p) for p in parts], dtype=np.float32) if parts else None
            )
        except Exception:
            return None
    arr = np.array(v)
    if arr.dtype.kind in ("i", "u", "f"):
        return arr.astype(np.float32)
    if arr.dtype.kind == "S":
        try:
            return np.array([x.decode() for x in arr], dtype=np.float32)
        except Exception:
            return None
    return None


def _read_attr_scalar(attrs, key):
    if key not in attrs:
        return None
    v = attrs[key]
    if isinstance(v, (np.generic, np.ndarray)):
        v = np.array(v).squeeze().tolist()
    if isinstance(v, (bytes, bytearray)):
        try:
            v = float(v.decode())
        except Exception:
            return None
    try:
        return float(v)
    except Exception:
        return None


def _select_present_bands(cw, fwhm, flags):
    flags = flags.astype(int).ravel()
    idx = np.where(flags == 1)[0]  # 0-based indices into the original band axis
    return cw[idx], fwhm[idx], idx


def _maybe_read(f, path):
    return f[path][()] if path in f else None


def _load_bandinfo_from_attrs(attrs, cw_key, fwhm_key, flags_key):
    cw = _read_attr_as_array(attrs, cw_key)
    fwhm = _read_attr_as_array(attrs, fwhm_key)
    flags = _read_attr_as_array(attrs, flags_key)
    if cw is None or fwhm is None or flags is None:
        return None
    cw_sel, fwhm_sel, kept_idx = _select_present_bands(cw, fwhm, flags)
    return BandInfo(
        wavelengths_nm=cw_sel,
        fwhm_nm=fwhm_sel,
        present_flags=np.ones_like(cw_sel, dtype=np.uint8),
        kept_indices=kept_idx.astype(np.int64),
    )


def _read_corners(attrs):
    keys = [
        ATTR_CENTER_E,
        ATTR_CENTER_N,
        ATTR_LL_E,
        ATTR_LL_N,
        ATTR_LR_E,
        ATTR_LR_N,
        ATTR_UL_E,
        ATTR_UL_N,
        ATTR_UR_E,
        ATTR_UR_N,
    ]
    return {k: _read_attr_scalar(attrs, k) for k in keys}


def _infer_utm_epsg(lon, lat):
    if lon is None or lat is None:
        return None
    zone = int((float(lon) + 180.0) / 6.0) + 1
    if not (1 <= zone <= 60):
        return None
    return (32600 if float(lat) >= 0 else 32700) + zone


def _project_lonlat_corners(attrs, epsg_meta):
    center_lat = _read_attr_scalar(attrs, ATTR_CENTER_LAT)
    center_lon = _read_attr_scalar(attrs, ATTR_CENTER_LON)
    target_epsg = epsg_meta or _infer_utm_epsg(center_lon, center_lat)
    if target_epsg is None:
        return None, {}

    pairs = {
        "ll": (
            _read_attr_scalar(attrs, ATTR_LL_LON),
            _read_attr_scalar(attrs, ATTR_LL_LAT),
        ),
        "lr": (
            _read_attr_scalar(attrs, ATTR_LR_LON),
            _read_attr_scalar(attrs, ATTR_LR_LAT),
        ),
        "ul": (
            _read_attr_scalar(attrs, ATTR_UL_LON),
            _read_attr_scalar(attrs, ATTR_UL_LAT),
        ),
        "ur": (
            _read_attr_scalar(attrs, ATTR_UR_LON),
            _read_attr_scalar(attrs, ATTR_UR_LAT),
        ),
    }
    if any(lon is None or lat is None for lon, lat in pairs.values()):
        return target_epsg, {}

    transformer = Transformer.from_crs(4326, target_epsg, always_xy=True)
    out = {}
    for key, (lon, lat) in pairs.items():
        e, n = transformer.transform(lon, lat)
        out[f"{key}_e"] = float(e)
        out[f"{key}_n"] = float(n)
    return target_epsg, out


def _project_grid_corners(lat_grid, lon_grid, epsg_meta):
    if lat_grid is None or lon_grid is None:
        return epsg_meta, {}
    if lat_grid.ndim != 2 or lon_grid.ndim != 2:
        return epsg_meta, {}

    corners_ll = {
        "ul": (float(lon_grid[0, 0]), float(lat_grid[0, 0])),
        "ur": (float(lon_grid[0, -1]), float(lat_grid[0, -1])),
        "ll": (float(lon_grid[-1, 0]), float(lat_grid[-1, 0])),
        "lr": (float(lon_grid[-1, -1]), float(lat_grid[-1, -1])),
    }
    center_lon = float(lon_grid[lat_grid.shape[0] // 2, lat_grid.shape[1] // 2])
    center_lat = float(lat_grid[lat_grid.shape[0] // 2, lat_grid.shape[1] // 2])
    target_epsg = epsg_meta or _infer_utm_epsg(center_lon, center_lat)
    if target_epsg is None:
        return None, {}

    transformer = Transformer.from_crs(4326, target_epsg, always_xy=True)
    out = {}
    for key, (lon, lat) in corners_ll.items():
        e, n = transformer.transform(lon, lat)
        out[f"{key}_e"] = float(e)
        out[f"{key}_n"] = float(n)
    return target_epsg, out


# Fixed, spec-driven: (E, B, N) -> (N, E, B)
def _l2d_bil_to_rows_cols_bands(arr):
    """
    PRISMA L2D VNIR/SWIR cubes are (nEastingPixel, nBands, nNorthingPixel).
    Return array as (rows=N, cols=E, bands=B) i.e. np.transpose(arr, (2, 0, 1)).
    """
    if arr.ndim != 3:
        raise ValueError(f"L2D cube must be 3D (E,B,N); got {arr.shape}")
    return np.transpose(arr, (2, 0, 1))


# ---- Public API ----
def load_prisma_l2d(product_path, load_pan=False):
    with _open_prisma_h5(product_path) as f:
        # Detect product type
        try:
            product_type = _detect_prisma_product_type(f)
            paths = _get_prisma_paths(product_type)
        except ValueError as error:
            gs.fatal(f"Input does not match product=prisma. {error}")

        # Global attrs (kept for reference)
        attrs = {}
        for k, v in f.attrs.items():
            try:
                attrs[k] = (
                    v.decode(errors="ignore")
                    if isinstance(v, (bytes, bytearray))
                    else (np.array(v).tolist() if isinstance(v, np.ndarray) else v)
                )
            except Exception:
                attrs[k] = v

        # Geolocation grids (hyperspectral swath)
        lat_hco = _maybe_read(f, paths["lat"])
        lon_hco = _maybe_read(f, paths["lon"])

        # EPSG from spec key
        epsg_meta = (
            int(_read_attr_scalar(f.attrs, ATTR_EPSG))
            if _read_attr_scalar(f.attrs, ATTR_EPSG) is not None
            else None
        )
        inferred_epsg, projected_corners = _project_lonlat_corners(f.attrs, epsg_meta)
        if epsg_meta is None:
            epsg_meta = inferred_epsg

        # VNIR band metadata
        vnir_bands = _load_bandinfo_from_attrs(
            f.attrs, ATTR_CW_VNIR, ATTR_FWHM_VNIR, ATTR_CW_VNIR_FLAGS
        )
        # SWIR band metadata
        swir_bands = _load_bandinfo_from_attrs(
            f.attrs, ATTR_CW_SWIR, ATTR_FWHM_SWIR, ATTR_CW_SWIR_FLAGS
        )

        # VNIR data
        vnir = None
        vnir_dn_raw = _maybe_read(f, paths["vnir_data"])
        vnir_err_raw = _maybe_read(f, paths["vnir_err"])
        if vnir_dn_raw is not None:
            vnir_dn = _l2d_bil_to_rows_cols_bands(vnir_dn_raw)
            vnir_err = (
                _l2d_bil_to_rows_cols_bands(vnir_err_raw)
                if (vnir_err_raw is not None and vnir_err_raw.ndim == 3)
                else vnir_err_raw
            )
            vnir = PrismaCube(
                name="VNIR",
                dn=vnir_dn,
                err=vnir_err,
                scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_VMIN),
                scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_VMAX),
                scale_factor=_read_attr_scalar(f.attrs, ATTR_SCALE_FACTOR_VNIR),
                bands=vnir_bands,
            )

        # SWIR data
        swir = None
        swir_dn_raw = _maybe_read(f, paths["swir_data"])
        swir_err_raw = _maybe_read(f, paths["swir_err"])
        if swir_dn_raw is not None:
            swir_dn = _l2d_bil_to_rows_cols_bands(swir_dn_raw)
            swir_err = (
                _l2d_bil_to_rows_cols_bands(swir_err_raw)
                if (swir_err_raw is not None and swir_err_raw.ndim == 3)
                else swir_err_raw
            )
            swir = PrismaCube(
                name="SWIR",
                dn=swir_dn,
                err=swir_err,
                scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_SMIN),
                scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_SMAX),
                scale_factor=_read_attr_scalar(f.attrs, ATTR_SCALE_FACTOR_SWIR),
                bands=swir_bands,
            )

        # HCO geolocation (VNIR/SWIR)
        hco_geo = None
        if lat_hco is not None and lon_hco is not None:
            if not projected_corners:
                inferred_epsg, projected_corners = _project_grid_corners(
                    lat_hco, lon_hco, epsg_meta
                )
                if epsg_meta is None:
                    epsg_meta = inferred_epsg
            corners = _read_corners(f.attrs)
            hco_geo = Geolocation(
                lat=lat_hco,
                lon=lon_hco,
                x_m=None,
                y_m=None,
                utm_epsg=epsg_meta,
                center_e=corners.get(ATTR_CENTER_E),
                center_n=corners.get(ATTR_CENTER_N),
                ll_e=corners.get(ATTR_LL_E) or projected_corners.get("ll_e"),
                ll_n=corners.get(ATTR_LL_N) or projected_corners.get("ll_n"),
                lr_e=corners.get(ATTR_LR_E) or projected_corners.get("lr_e"),
                lr_n=corners.get(ATTR_LR_N) or projected_corners.get("lr_n"),
                ul_e=corners.get(ATTR_UL_E) or projected_corners.get("ul_e"),
                ul_n=corners.get(ATTR_UL_N) or projected_corners.get("ul_n"),
                ur_e=corners.get(ATTR_UR_E) or projected_corners.get("ur_e"),
                ur_n=corners.get(ATTR_UR_N) or projected_corners.get("ur_n"),
            )

        # PAN (optional; PAN array is already 2D)
        pan = None
        pco_geo = None
        if load_pan:
            pan_dn = _maybe_read(f, paths["pan_data"])
            pan_err = _maybe_read(f, paths["pan_err"])
            if pan_dn is not None:
                pan = PrismaCube(
                    name="PAN",
                    dn=pan_dn,
                    err=pan_err,
                    scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_PMIN),
                    scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_PMAX),
                    scale_factor=_read_attr_scalar(f.attrs, ATTR_SCALE_FACTOR_PAN),
                    bands=None,
                )
            lat_pco = _maybe_read(f, paths["pco_lat"])
            lon_pco = _maybe_read(f, paths["pco_lon"])
            if lat_pco is not None and lon_pco is not None:
                corners = _read_corners(f.attrs)
                pco_geo = Geolocation(
                    lat=lat_pco,
                    lon=lon_pco,
                    x_m=None,
                    y_m=None,
                    utm_epsg=epsg_meta,
                    center_e=corners.get(ATTR_CENTER_E),
                    center_n=corners.get(ATTR_CENTER_N),
                    ll_e=corners.get(ATTR_LL_E) or projected_corners.get("ll_e"),
                    ll_n=corners.get(ATTR_LL_N) or projected_corners.get("ll_n"),
                    lr_e=corners.get(ATTR_LR_E) or projected_corners.get("lr_e"),
                    lr_n=corners.get(ATTR_LR_N) or projected_corners.get("lr_n"),
                    ul_e=corners.get(ATTR_UL_E) or projected_corners.get("ul_e"),
                    ul_n=corners.get(ATTR_UL_N) or projected_corners.get("ul_n"),
                    ur_e=corners.get(ATTR_UR_E) or projected_corners.get("ur_e"),
                    ur_n=corners.get(ATTR_UR_N) or projected_corners.get("ur_n"),
                )

    return PrismaL2DProduct(
        path=product_path,
        product_type=product_type,
        vnir=vnir,
        swir=swir,
        pan=pan,
        hco_geo=hco_geo,
        pco_geo=pco_geo,
        attrs=attrs,
    )


# ---- Projection info query (for -p flag) ----


def get_prisma_proj_info(product_path):
    """Return CRS/spatial info dict for a PRISMA product.
    
    L2D → grid layout: SRID, west/south/east/north, rows/cols, ewres/nsres.
    L2C/L1 → swath layout: SRID=EPSG:4326, Center, optional Corners, rows/cols.
    """
    with _open_prisma_h5(product_path) as f:
        try:
            product_type = _detect_prisma_product_type(f)
            paths = _get_prisma_paths(product_type)
        except ValueError as error:
            gs.fatal(f"Input does not match product=prisma. {error}")

        if product_type == "L2D":
            epsg = _read_attr_scalar(f.attrs, ATTR_EPSG)
            ul_e = _read_attr_scalar(f.attrs, ATTR_UL_E)
            ul_n = _read_attr_scalar(f.attrs, ATTR_UL_N)
            ur_e = _read_attr_scalar(f.attrs, ATTR_UR_E)
            ur_n = _read_attr_scalar(f.attrs, ATTR_UR_N)
            ll_e = _read_attr_scalar(f.attrs, ATTR_LL_E)
            ll_n = _read_attr_scalar(f.attrs, ATTR_LL_N)
            lr_e = _read_attr_scalar(f.attrs, ATTR_LR_E)
            lr_n = _read_attr_scalar(f.attrs, ATTR_LR_N)

            vnir_raw = _maybe_read(f, paths["vnir_data"])
            if vnir_raw is not None and vnir_raw.ndim == 3:
                rows = int(vnir_raw.shape[2])
                cols = int(vnir_raw.shape[0])
            else:
                rows = cols = None

            if all(v is not None for v in (ul_e, ur_e, ll_e, lr_e)):
                west = float(min(ul_e, ll_e))
                east = float(max(ur_e, lr_e))
            else:
                west = east = None
            if all(v is not None for v in (ul_n, ur_n, ll_n, lr_n)):
                south = float(min(ll_n, lr_n))
                north = float(max(ul_n, ur_n))
            else:
                south = north = None

            ewres = (east - west) / cols if (east is not None and west is not None and cols and cols > 0) else None
            nsres = (north - south) / rows if (north is not None and south is not None and rows and rows > 0) else None

            return {
                "product_type": product_type,
                "layout": "grid",
                "srid": f"EPSG:{int(epsg)}" if epsg is not None else "not available",
                "west": west,
                "east": east,
                "south": south,
                "north": north,
                "rows": rows,
                "cols": cols,
                "ewres": ewres,
                "nsres": nsres,
                "import_behavior": "Imports the data directly on the existing product grid. No additional geocoding or reprojection is performed.",
                "project_requirements": "Use a GRASS project whose CRS matches the product CRS.",
            }

        elif product_type in ("L2C", "L1"):
            center_lat = _read_attr_scalar(f.attrs, ATTR_CENTER_LAT)
            center_lon = _read_attr_scalar(f.attrs, ATTR_CENTER_LON)

            corners = {}
            for key, lat_attr, lon_attr in [
                ("ul", ATTR_UL_LAT, ATTR_UL_LON),
                ("ur", ATTR_UR_LAT, ATTR_UR_LON),
                ("ll", ATTR_LL_LAT, ATTR_LL_LON),
                ("lr", ATTR_LR_LAT, ATTR_LR_LON),
            ]:
                lat = _read_attr_scalar(f.attrs, lat_attr)
                lon = _read_attr_scalar(f.attrs, lon_attr)
                if lat is not None and lon is not None:
                    corners[key] = (float(lat), float(lon))

            vnir_raw = _maybe_read(f, paths["vnir_data"])
            if vnir_raw is not None and vnir_raw.ndim == 3:
                rows = int(vnir_raw.shape[2])
                cols = int(vnir_raw.shape[0])
            else:
                rows = cols = None

            return {
                "product_type": product_type,
                "layout": "swath",
                "srid": "EPSG:4326",
                "center_lat": float(center_lat) if center_lat is not None else None,
                "center_lon": float(center_lon) if center_lon is not None else None,
                "corners": corners if corners else None,
                "rows": rows,
                "cols": cols,
                "import_behavior": "Uses the per-pixel longitude and latitude arrays to geocode the image data onto an output grid generated by the importer in the current GRASS project CRS. Source pixels are assigned to the nearest output cells.",
                "project_requirements": "The current GRASS project CRS defines the output CRS.",
            }

        return {"layout": "unknown"}


def concatenate_hyperspectral(product):
    """
    Concatenate VNIR and SWIR reflectance along band axis (bands-last), **after filtering**
    to only the bands marked present (flags==1). This keeps the reflectance cube and the
    metadata arrays (wavelengths, FWHM) perfectly aligned.
    Returns:
        refl (rows, cols, bands_total_filtered),
        wavelengths_nm (bands_total_filtered,),
        fwhm_nm (bands_total_filtered,)
    """
    if product.vnir is None or product.swir is None:
        raise ValueError("Both VNIR and SWIR must be present to concatenate.")
    if getattr(product, "product_type", None) == "L1":
        vnir_ref = product.vnir.to_radiance()
        swir_ref = product.swir.to_radiance()
        if vnir_ref is None or swir_ref is None:
            raise ValueError("Missing scale factors to compute radiance.")
    else:
        vnir_ref = product.vnir.to_reflectance()
        swir_ref = product.swir.to_reflectance()
        if vnir_ref is None or swir_ref is None:
            raise ValueError("Missing scale factors to compute reflectance.")
    if vnir_ref.ndim != 3 or swir_ref.ndim != 3:
        raise ValueError(
            f"Expected 3D arrays; got VNIR {vnir_ref.shape}, SWIR {swir_ref.shape}"
        )
    if vnir_ref.shape[:2] != swir_ref.shape[:2]:
        raise ValueError(
            f"Spatial shapes differ after normalization: VNIR {vnir_ref.shape[:2]} vs SWIR {swir_ref.shape[:2]}"
        )

    # ---- Filter by kept indices (flags==1) so band counts match metadata ----
    if product.vnir.bands is None or product.swir.bands is None:
        raise ValueError("Missing wavelength/FWHM metadata.")
    v_idx = product.vnir.bands.kept_indices
    s_idx = product.swir.bands.kept_indices
    vnir_ref_f = vnir_ref[:, :, v_idx]
    swir_ref_f = swir_ref[:, :, s_idx]

    v_wl = product.vnir.bands.wavelengths_nm
    s_wl = product.swir.bands.wavelengths_nm
    v_fwhm = product.vnir.bands.fwhm_nm
    s_fwhm = product.swir.bands.fwhm_nm

    refl = np.concatenate([vnir_ref_f, swir_ref_f], axis=2).astype(np.float32)
    wavelengths = np.concatenate([v_wl, s_wl], axis=0)
    fwhm = np.concatenate([v_fwhm, s_fwhm], axis=0)

    # ---- ensure ascending wavelength order for both metadata and cube ----
    order = np.argsort(wavelengths.astype(np.float32))
    wavelengths = wavelengths[order]
    fwhm = fwhm[order]
    refl = refl[:, :, order]

    return refl, wavelengths, fwhm
def _open_prisma_h5(product_path):
    try:
        return h5py.File(product_path, "r")
    except OSError as error:
        gs.fatal(
            "Input does not match product=prisma. "
            f"Expected a PRISMA HDF5 (.he5) product. {error}"
        )

