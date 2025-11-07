#!/usr/bin/env python3
"""
Tanager BASIC reader and map projection + gridding helpers

- Reads Tanager BASIC HDF5:
  * selects "surface_reflectance" if available, else "toa_radiance"
  * returns data cube as (rows, cols, bands) float32
  * applies nodata mask where /HDFEOS/SWATHS/HYP/Data Fields/nodata_pixels == 1
  * extracts wavelengths and FWHM from dataset attributes; ensures ascending wavelength order
  * exposes per-pixel Latitude/Longitude arrays
  * exposes selected data field name and its units (read from HDF5 if present)

- Provides projection + gridding helpers:
  * parses Planet_Ortho_Framing (UTM grid, geotransform, rows/cols)
  * builds a per-scene "splat plan" (indices, weights, visit, nodata influence)
  * projects and resamples bands to the target map grid using bilinear forward splatting
  * optionally fills purely geometric gaps within a small neighborhood
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import json
import numpy as np
import h5py

# Optional imports
try:
    from pyproj import CRS, Transformer
    _HAS_PYPROJ = True
except Exception:
    _HAS_PYPROJ = False

try:
    from scipy.ndimage import distance_transform_edt  # used for small-radius nearest fill
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

# ---- HDF5 layout ----
HYP = "/HDFEOS/SWATHS/HYP"
DF  = f"{HYP}/Data Fields"
GF  = f"{HYP}/Geolocation Fields"

DS_ORDER     = ("surface_reflectance", "toa_radiance")
DS_WL_ATTR   = "wavelengths"
DS_FWHM_ATTR = "fwhm"

DS_NODATA = f"{DF}/nodata_pixels"
DS_LAT    = f"{GF}/Latitude"
DS_LON    = f"{GF}/Longitude"


# ---------------------------- Data containers ----------------------------

@dataclass
class TanagerProduct:
    path: str
    data: np.ndarray              # (rows, cols, bands), float32
    wavelengths_nm: np.ndarray    # (bands,)
    fwhm_nm: np.ndarray           # (bands,)
    lat: Optional[np.ndarray]     # (rows, cols)
    lon: Optional[np.ndarray]     # (rows, cols)
    attrs: Dict[str, Any]         # top-level file attributes (optional use)
    data_field: str               # 'surface_reflectance' or 'toa_radiance'
    data_units: str               # human-readable units string


@dataclass(frozen=True)
class MapGrid:
    """Target map grid parsed from Planet_Ortho_Framing."""
    epsg: int
    west: float     # geotransform[0]
    north: float    # geotransform[3]
    ewres: float    # +pixel width  (meters)
    nsres: float    # +pixel height (meters)
    rows: int
    cols: int

    @property
    def east(self) -> float:
        return self.west + self.cols * self.ewres

    @property
    def south(self) -> float:
        return self.north - self.rows * self.nsres


@dataclass(frozen=True)
class SplatPlan:
    """Precomputed per-scene bilinear splat geometry and masks."""
    rows: int
    cols: int
    # neighbor indices
    r0: np.ndarray; c0: np.ndarray
    r1: np.ndarray; c1: np.ndarray
    r2: np.ndarray; c2: np.ndarray
    r3: np.ndarray; c3: np.ndarray
    # neighbor weights
    w0: np.ndarray; w1: np.ndarray; w2: np.ndarray; w3: np.ndarray
    # geometry mask (valid transform & indices in bounds)
    inb: np.ndarray
    # accumulated once (band-independent)
    visit: np.ndarray            # any sample (valid or nodata) contributed
    vnod: np.ndarray             # nodata-only influence


# ---------------------------- Reader ----------------------------

def _maybe(f: h5py.File, path: str):
    return f[path][()] if path in f else None

def _units_from_attrs(attrs: h5py.AttributeManager, fallback: Optional[str]) -> Optional[str]:
    """
    Try to read units from common attribute keys (case-insensitive).
    Returns string if found (as-is), else fallback.
    """
    for key in ("Unit", "Units", "unit", "units"):
        if key in attrs:
            try:
                val = attrs[key]
                if val is None:
                    continue
                s = str(val).strip()
                if s != "":
                    return s
            except Exception:
                pass
    return fallback

def load_tanager_basic(product_path: str) -> TanagerProduct:
    with h5py.File(product_path, "r") as f:
        # file-level attributes (optional)
        attrs: Dict[str, Any] = {}
        for k, v in f.attrs.items():
            try:
                attrs[k] = v.decode(errors="ignore") if isinstance(v, (bytes, bytearray)) else (
                    np.array(v).tolist() if isinstance(v, np.ndarray) else v
                )
            except Exception:
                attrs[k] = v

        # choose data field
        dset = None
        chosen_name = None
        for name in DS_ORDER:
            p = f"{DF}/{name}"
            if p in f:
                dset = f[p]
                chosen_name = name
                break
        if dset is None:
            raise ValueError("No 'surface_reflectance' or 'toa_radiance' dataset found.")

        arr_raw = dset[()]  # (Band, Y, X)
        if arr_raw.ndim != 3:
            raise ValueError(f"Unexpected dataset shape {arr_raw.shape} (expected 3D)")

        # to (rows, cols, bands)
        data = np.transpose(arr_raw, (1, 2, 0)).astype(np.float32, copy=False)

        # spectral metadata
        wl   = np.array(dset.attrs[DS_WL_ATTR], dtype=np.float32)
        fwhm = np.array(dset.attrs.get(DS_FWHM_ATTR, np.full_like(wl, np.nan, dtype=np.float32)),
                        dtype=np.float32)

        # enforce ascending wavelengths (reorder cube accordingly)
        order = np.argsort(wl.astype(np.float32))
        wl = wl[order]
        fwhm = fwhm[order]
        data = data[:, :, order]

        # geolocation & nodata
        lat = _maybe(f, DS_LAT)
        lon = _maybe(f, DS_LON)

        nd = _maybe(f, DS_NODATA)
        if nd is not None:
            if nd.shape != data.shape[:2]:
                raise ValueError(f"nodata_pixels shape {nd.shape} != image plane {data.shape[:2]}")
            m = nd.astype(bool)
            if m.any():
                data[m, :] = np.nan

        # derive human-friendly units
        # 1) prefer dataset attribute if present (e.g., ":Unit = 'W/(m^2 sr um)'")
        # 2) fallback to a reasonable default from the chosen dataset
        fallback_units = "unitless (reflectance)" if chosen_name == "surface_reflectance" else "W/(m^2 sr um)"
        data_units = _units_from_attrs(dset.attrs, fallback_units)
        # normalize a couple of common textual variants
        if data_units.lower() in ("unitless", "none", "1", "ratio"):
            data_units = "unitless (reflectance)"

    return TanagerProduct(
        path=product_path,
        data=data,
        wavelengths_nm=wl,
        fwhm_nm=fwhm,
        lat=lat,
        lon=lon,
        attrs=attrs,
        data_field=chosen_name,
        data_units=str(data_units),
    )


# ---------------------------- Projection + gridding helpers ----------------------------

def read_planet_map_grid(product_path: str) -> MapGrid:
    """
    Parse Planet_Ortho_Framing from:
      /HDFEOS/SWATHS/HYP/Geolocation Fields : Planet_Ortho_Framing
    Expected JSON keys:
      epsg_code, rows, cols, geotransform [west, ewres, 0, north, 0, -nsres]
    """
    with h5py.File(product_path, "r") as f:
        meta = f[GF].attrs["Planet_Ortho_Framing"]
        if isinstance(meta, (bytes, bytearray)):
            meta = meta.decode(errors="ignore")
        meta = json.loads(meta)

    epsg = int(meta["epsg_code"])
    rows = int(meta["rows"])
    cols = int(meta["cols"])
    west, ewres, north, nsres = float(meta["geotransform"][0]), float(meta["geotransform"][1]), \
                                float(meta["geotransform"][3]), float(-meta["geotransform"][5])
    return MapGrid(epsg, west, north, ewres, nsres, rows, cols)


def _transform_lonlat(lon: np.ndarray, lat: np.ndarray, epsg: int) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorized transformation WGS84 lon/lat -> target EPSG (meters)."""
    if not _HAS_PYPROJ:
        raise RuntimeError("pyproj is required for in-memory map projection.")
    t = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(epsg), always_xy=True)
    x, y = t.transform(lon, lat)
    return np.asarray(x), np.asarray(y)


def build_splat_plan(
    lon2d: np.ndarray,
    lat2d: np.ndarray,
    grid: MapGrid,
    nodata_mask: Optional[np.ndarray]
) -> SplatPlan:
    """
    Build per-scene bilinear splat indices/weights and band-independent masks:
      - visit: any sample (valid or nodata) contributes
      - vnod:  nodata-only influence
    """
    x, y = _transform_lonlat(lon2d, lat2d, grid.epsg)
    rows, cols = grid.rows, grid.cols

    fx = (x - grid.west) / grid.ewres
    fy = (grid.north - y) / grid.nsres

    c0 = np.floor(fx).astype(np.int64)
    r0 = np.floor(fy).astype(np.int64)
    dc = fx - c0
    dr = fy - r0

    rA, cA = r0,     c0
    rB, cB = r0,     c0 + 1
    rC, cC = r0 + 1, c0
    rD, cD = r0 + 1, c0 + 1

    wA = (1 - dr) * (1 - dc)
    wB = (1 - dr) * dc
    wC = dr * (1 - dc)
    wD = dr * dc

    inb = (rA >= 0) & (rD < rows) & (cA >= 0) & (cD < cols) & np.isfinite(fx) & np.isfinite(fy)

    visit = np.zeros((rows, cols), dtype=np.float64)
    vnod  = np.zeros((rows, cols), dtype=np.float64)

    def add_to(target, rr, cc, ww, mask=None):
        m = inb & (ww > 0)
        if mask is not None:
            m &= mask
        if np.any(m):
            np.add.at(target, (rr[m], cc[m]), ww[m])

    add_to(visit, rA, cA, wA)
    add_to(visit, rB, cB, wB)
    add_to(visit, rC, cC, wC)
    add_to(visit, rD, cD, wD)

    if nodata_mask is not None:
        nod = np.asarray(nodata_mask, dtype=bool) & inb
        add_to(vnod, rA, cA, wA, mask=nod)
        add_to(vnod, rB, cB, wB, mask=nod)
        add_to(vnod, rC, cC, wC, mask=nod)
        add_to(vnod, rD, cD, wD, mask=nod)

    return SplatPlan(
        rows=rows, cols=cols,
        r0=rA, c0=cA, r1=rB, c1=cB, r2=rC, c2=cC, r3=rD, c3=cD,
        w0=wA, w1=wB, w2=wC, w3=wD,
        inb=inb, visit=visit, vnod=vnod
    )


def splat_band_with_plan(values: np.ndarray, plan: SplatPlan, nodata: float = np.nan) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bilinear forward splat using a precomputed SplatPlan.
    Returns:
      ortho: float32 (rows, cols)
      wts:   float64 (rows, cols) sum of weights from valid samples
    """
    out = np.zeros((plan.rows, plan.cols), dtype=np.float64)
    wts = np.zeros((plan.rows, plan.cols), dtype=np.float64)

    valid = plan.inb & np.isfinite(values)

    def add(rr, cc, ww):
        m = valid & (ww > 0)
        if np.any(m):
            np.add.at(out, (rr[m], cc[m]), values[m].astype(np.float64) * ww[m])
            np.add.at(wts, (rr[m], cc[m]), ww[m])

    add(plan.r0, plan.c0, plan.w0)
    add(plan.r1, plan.c1, plan.w1)
    add(plan.r2, plan.c2, plan.w2)
    add(plan.r3, plan.c3, plan.w3)

    ortho = np.full((plan.rows, plan.cols), nodata, dtype=np.float32)
    nz = wts > 0
    ortho[nz] = (out[nz] / wts[nz]).astype(np.float32)
    return ortho, wts


def project_band_to_map_grid(
    band2d: np.ndarray,
    plan: SplatPlan,
    fill_8_neighbor: bool = True
) -> np.ndarray:
    """
    Project and resample one band to the target map grid using a SplatPlan.
    Optionally fills purely geometric gaps via nearest neighbor limited to the 8-neighborhood.
    Nodata is preserved.
    """
    ortho, wts = splat_band_with_plan(band2d, plan, nodata=np.nan)

    if fill_8_neighbor and _HAS_SCIPY:
        holes_geom = (wts == 0) & (plan.visit > 0) & (plan.vnod == 0)
        if np.any(holes_geom):
            filled_mask = np.isfinite(ortho)
            dist, (ri, ci) = distance_transform_edt(~filled_mask, return_indices=True)
            # Strict 8-neighbor: Euclidean distance <= sqrt(2)
            from math import sqrt
            ok = holes_geom & (dist <= sqrt(2))
            ortho[ok] = ortho[ri[ok], ci[ok]]

    return ortho
