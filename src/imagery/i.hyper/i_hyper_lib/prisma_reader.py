#!/usr/bin/env python3
"""
PRISMA L2D importer

- Reads VNIR/SWIR/PAN cubes + error matrices from PRISMA L2D HDF-EOS5.
- Converts DN->reflectance on demand using product's L2 scale attributes:
    refl = Min + (DN * (Max - Min)) / 65535
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
from typing import Optional, Tuple, Dict, Any
import numpy as np
import h5py

# ---- HDF5 paths (from PRISMA L2D spec) ----
HCO_VNIR_DATA = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_Cube"
HCO_SWIR_DATA = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_Cube"
PCO_PAN_DATA  = "/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/PAN_Cube"

HCO_VNIR_ERR  = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX"
HCO_SWIR_ERR  = "/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX"
PCO_PAN_ERR   = "/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/PIXEL_L2_ERR_MATRIX"

HCO_LAT = "/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Latitude"
HCO_LON = "/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Longitude"
PCO_LAT = "/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Latitude"
PCO_LON = "/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Longitude"

# ---- Global attributes (per spec) ----
ATTR_CW_VNIR       = "List_Cw_Vnir"
ATTR_CW_VNIR_FLAGS = "List_Cw_Vnir_Flags"
ATTR_FWHM_VNIR     = "List_Fwhm_Vnir"

ATTR_CW_SWIR       = "List_Cw_Swir"
ATTR_CW_SWIR_FLAGS = "List_Cw_Swir_Flags"
ATTR_FWHM_SWIR     = "List_Fwhm_Swir"

ATTR_SCALE_VMAX = "L2ScaleVnirMax"
ATTR_SCALE_VMIN = "L2ScaleVnirMin"
ATTR_SCALE_SMAX = "L2ScaleSwirMax"
ATTR_SCALE_SMIN = "L2ScaleSwirMin"
ATTR_SCALE_PMAX = "L2ScalePanMax"
ATTR_SCALE_PMIN = "L2ScalePanMin"

ATTR_CENTER_E   = "Product_center_easting"
ATTR_CENTER_N   = "Product_center_northing"

ATTR_LL_E = "Product_LLcorner_easting"
ATTR_LL_N = "Product_LLcorner_northing"
ATTR_LR_E = "Product_LRcorner_easting"
ATTR_LR_N = "Product_LRcorner_northing"
ATTR_UL_E = "Product_ULcorner_easting"
ATTR_UL_N = "Product_ULcorner_northing"
ATTR_UR_E = "Product_URcorner_easting"
ATTR_UR_N = "Product_URcorner_northing"

ATTR_EPSG = "Epsg_Code"  # strict per spec

# ---- Data containers ----
@dataclass
class BandInfo:
    wavelengths_nm: np.ndarray     # (bands_kept,)
    fwhm_nm: np.ndarray            # (bands_kept,)
    present_flags: np.ndarray      # (bands_kept,) all ones after filtering
    # Added: indices of kept bands in the original band axis (0-based)
    kept_indices: np.ndarray       # (bands_kept,)

@dataclass
class PrismaCube:
    name: str                          # "VNIR" | "SWIR" | "PAN"
    dn: Optional[np.ndarray]           # VNIR/SWIR: (rows, cols, bands); PAN: (rows, cols)
    err: Optional[np.ndarray]          # same spatial shape; band-dim if provided
    scale_min: Optional[float]
    scale_max: Optional[float]
    bands: Optional[BandInfo] = None   # None for PAN

    def to_reflectance(self) -> Optional[np.ndarray]:
        if self.dn is None or self.scale_min is None or self.scale_max is None:
            return None
        return self.scale_min + (self.dn.astype(np.float32) *
                                 (self.scale_max - self.scale_min) / 65535.0)

    def valid_mask(self) -> Optional[np.ndarray]:
        return (self.err == 0) if self.err is not None else None

@dataclass
class Geolocation:
    lat: np.ndarray                 # (rows, cols)
    lon: np.ndarray                 # (rows, cols)
    x_m: Optional[np.ndarray]       # not computed here
    y_m: Optional[np.ndarray]
    utm_epsg: Optional[int]
    center_e: Optional[float] = None
    center_n: Optional[float] = None
    ll_e: Optional[float] = None
    ll_n: Optional[float] = None
    lr_e: Optional[float] = None
    lr_n: Optional[float] = None
    ul_e: Optional[float] = None
    ul_n: Optional[float] = None
    ur_e: Optional[float] = None
    ur_n: Optional[float] = None

@dataclass
class PrismaL2DProduct:
    path: str
    vnir: Optional[PrismaCube]
    swir: Optional[PrismaCube]
    pan: Optional[PrismaCube]
    hco_geo: Optional[Geolocation]
    pco_geo: Optional[Geolocation]
    attrs: Dict[str, Any]

# ---- Internal helpers ----
def _read_attr_as_array(attrs: h5py.AttributeManager, key: str) -> Optional[np.ndarray]:
    if key not in attrs:
        return None
    v = attrs[key]
    if isinstance(v, (bytes, bytearray, str)):
        try:
            s = v.decode() if isinstance(v, (bytes, bytearray)) else v
            parts = [p for p in s.replace(",", " ").split() if p.strip()]
            return np.array([float(p) for p in parts], dtype=np.float32) if parts else None
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

def _read_attr_scalar(attrs: h5py.AttributeManager, key: str) -> Optional[float]:
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

def _select_present_bands(cw: np.ndarray, fwhm: np.ndarray, flags: np.ndarray):
    flags = flags.astype(int).ravel()
    idx = np.where(flags == 1)[0]  # 0-based indices into the original band axis
    return cw[idx], fwhm[idx], idx

def _maybe_read(f: h5py.File, path: str) -> Optional[np.ndarray]:
    return f[path][()] if path in f else None

def _load_bandinfo_from_attrs(attrs: h5py.AttributeManager,
                              cw_key: str, fwhm_key: str, flags_key: str) -> Optional[BandInfo]:
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

def _read_corners(attrs: h5py.AttributeManager) -> Dict[str, Optional[float]]:
    keys = [ATTR_CENTER_E, ATTR_CENTER_N,
            ATTR_LL_E, ATTR_LL_N, ATTR_LR_E, ATTR_LR_N,
            ATTR_UL_E, ATTR_UL_N, ATTR_UR_E, ATTR_UR_N]
    return {k: _read_attr_scalar(attrs, k) for k in keys}

# Fixed, spec-driven: (E, B, N) -> (N, E, B)
def _l2d_bil_to_rows_cols_bands(arr: np.ndarray) -> np.ndarray:
    """
    PRISMA L2D VNIR/SWIR cubes are (nEastingPixel, nBands, nNorthingPixel).
    Return array as (rows=N, cols=E, bands=B) i.e. np.transpose(arr, (2, 0, 1)).
    """
    if arr.ndim != 3:
        raise ValueError(f"L2D cube must be 3D (E,B,N); got {arr.shape}")
    return np.transpose(arr, (2, 0, 1))

# ---- Public API ----
def load_prisma_l2d(product_path: str,
                    load_pan: bool = False,
                    compute_utm: bool = False  # kept for signature compatibility; not used
                    ) -> PrismaL2DProduct:
    with h5py.File(product_path, "r") as f:
        # Global attrs (kept for reference)
        attrs: Dict[str, Any] = {}
        for k, v in f.attrs.items():
            try:
                attrs[k] = v.decode(errors="ignore") if isinstance(v, (bytes, bytearray)) else (
                    np.array(v).tolist() if isinstance(v, np.ndarray) else v
                )
            except Exception:
                attrs[k] = v

        # Geolocation grids (hyperspectral swath)
        lat_hco = _maybe_read(f, HCO_LAT)
        lon_hco = _maybe_read(f, HCO_LON)

        # EPSG from spec key
        epsg_meta = int(_read_attr_scalar(f.attrs, ATTR_EPSG)) if _read_attr_scalar(f.attrs, ATTR_EPSG) is not None else None

        # VNIR band metadata
        vnir_bands = _load_bandinfo_from_attrs(f.attrs, ATTR_CW_VNIR, ATTR_FWHM_VNIR, ATTR_CW_VNIR_FLAGS)
        # SWIR band metadata
        swir_bands = _load_bandinfo_from_attrs(f.attrs, ATTR_CW_SWIR, ATTR_FWHM_SWIR, ATTR_CW_SWIR_FLAGS)

        # VNIR data
        vnir = None
        vnir_dn_raw = _maybe_read(f, HCO_VNIR_DATA)
        vnir_err_raw = _maybe_read(f, HCO_VNIR_ERR)
        if vnir_dn_raw is not None:
            vnir_dn = _l2d_bil_to_rows_cols_bands(vnir_dn_raw)
            vnir_err = _l2d_bil_to_rows_cols_bands(vnir_err_raw) if (vnir_err_raw is not None and vnir_err_raw.ndim == 3) else vnir_err_raw
            vnir = PrismaCube(
                name="VNIR",
                dn=vnir_dn,
                err=vnir_err,
                scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_VMIN),
                scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_VMAX),
                bands=vnir_bands,
            )

        # SWIR data
        swir = None
        swir_dn_raw = _maybe_read(f, HCO_SWIR_DATA)
        swir_err_raw = _maybe_read(f, HCO_SWIR_ERR)
        if swir_dn_raw is not None:
            swir_dn = _l2d_bil_to_rows_cols_bands(swir_dn_raw)
            swir_err = _l2d_bil_to_rows_cols_bands(swir_err_raw) if (swir_err_raw is not None and swir_err_raw.ndim == 3) else swir_err_raw
            swir = PrismaCube(
                name="SWIR",
                dn=swir_dn,
                err=swir_err,
                scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_SMIN),
                scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_SMAX),
                bands=swir_bands,
            )

        # HCO geolocation (VNIR/SWIR)
        hco_geo = None
        if lat_hco is not None and lon_hco is not None:
            corners = _read_corners(f.attrs)
            hco_geo = Geolocation(
                lat=lat_hco, lon=lon_hco, x_m=None, y_m=None, utm_epsg=epsg_meta,
                center_e=corners.get(ATTR_CENTER_E), center_n=corners.get(ATTR_CENTER_N),
                ll_e=corners.get(ATTR_LL_E), ll_n=corners.get(ATTR_LL_N),
                lr_e=corners.get(ATTR_LR_E), lr_n=corners.get(ATTR_LR_N),
                ul_e=corners.get(ATTR_UL_E), ul_n=corners.get(ATTR_UL_N),
                ur_e=corners.get(ATTR_UR_E), ur_n=corners.get(ATTR_UR_N),
            )

        # PAN (optional; PAN array is already 2D)
        pan = None
        pco_geo = None
        if load_pan:
            pan_dn = _maybe_read(f, PCO_PAN_DATA)
            pan_err = _maybe_read(f, PCO_PAN_ERR)
            if pan_dn is not None:
                pan = PrismaCube(
                    name="PAN", dn=pan_dn, err=pan_err,
                    scale_min=_read_attr_scalar(f.attrs, ATTR_SCALE_PMIN),
                    scale_max=_read_attr_scalar(f.attrs, ATTR_SCALE_PMAX),
                    bands=None
                )
            lat_pco = _maybe_read(f, PCO_LAT)
            lon_pco = _maybe_read(f, PCO_LON)
            if lat_pco is not None and lon_pco is not None:
                corners = _read_corners(f.attrs)
                pco_geo = Geolocation(
                    lat=lat_pco, lon=lon_pco, x_m=None, y_m=None, utm_epsg=epsg_meta,
                    center_e=corners.get(ATTR_CENTER_E), center_n=corners.get(ATTR_CENTER_N),
                    ll_e=corners.get(ATTR_LL_E), ll_n=corners.get(ATTR_LL_N),
                    lr_e=corners.get(ATTR_LR_E), lr_n=corners.get(ATTR_LR_N),
                    ul_e=corners.get(ATTR_UL_E), ul_n=corners.get(ATTR_UL_N),
                    ur_e=corners.get(ATTR_UR_E), ur_n=corners.get(ATTR_UR_N),
                )

    return PrismaL2DProduct(
        path=product_path,
        vnir=vnir,
        swir=swir,
        pan=pan,
        hco_geo=hco_geo,
        pco_geo=pco_geo,
        attrs=attrs,
    )

def concatenate_hyperspectral(product: PrismaL2DProduct
                              ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    vnir_ref = product.vnir.to_reflectance()
    swir_ref = product.swir.to_reflectance()
    if vnir_ref is None or swir_ref is None:
        raise ValueError("Missing scale factors to compute reflectance.")
    if vnir_ref.ndim != 3 or swir_ref.ndim != 3:
        raise ValueError(f"Expected 3D arrays; got VNIR {vnir_ref.shape}, SWIR {swir_ref.shape}")
    if vnir_ref.shape[:2] != swir_ref.shape[:2]:
        raise ValueError(f"Spatial shapes differ after normalization: VNIR {vnir_ref.shape[:2]} vs SWIR {swir_ref.shape[:2]}")

    # ---- Filter by kept indices (flags==1) so band counts match metadata ----
    if product.vnir.bands is None or product.swir.bands is None:
        raise ValueError("Missing wavelength/FWHM metadata.")
    v_idx = product.vnir.bands.kept_indices
    s_idx = product.swir.bands.kept_indices
    vnir_ref_f = vnir_ref[:, :, v_idx]
    swir_ref_f = swir_ref[:, :, s_idx]

    v_wl   = product.vnir.bands.wavelengths_nm
    s_wl   = product.swir.bands.wavelengths_nm
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
