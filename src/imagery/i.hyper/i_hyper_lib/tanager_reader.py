#!/usr/bin/env python3
"""
Tanager reader and map projection + gridding helpers

- Reads Tanager HDF5:
  * selects "surface_reflectance" if available, else "toa_radiance"
  * supports BASIC (/HDFEOS/SWATHS/HYP/...) and ORTHO (/HDFEOS/GRIDS/HYP/...)
  * returns data cube as (rows, cols, bands) float32
  * applies nodata mask from Data Fields/nodata_pixels when present
  * extracts wavelengths and FWHM from dataset attributes; ensures ascending wavelength order
  * exposes per-pixel Latitude/Longitude arrays for BASIC products
  * exposes selected data field name and its units (read from HDF5 if present)

- Provides projection + gridding helpers:
  * parses target map grid:
    - BASIC: Planet_Ortho_Framing
    - ORTHO: /HDFEOS INFORMATION/StructMetadata.0 + /HDFEOS/GRIDS/HYP epsg_code
  * builds a per-scene "splat plan" (indices, weights, visit, nodata influence)
  * projects and resamples bands to the target map grid using bilinear forward splatting
  * optionally fills purely geometric gaps within a small neighborhood
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import json
import re
import numpy as np
import h5py
import grass.script as gs

# Optional imports
try:
    from pyproj import CRS, Transformer

    _HAS_PYPROJ = True
except Exception:
    _HAS_PYPROJ = False

try:
    from scipy.ndimage import (
        distance_transform_edt,
    )  # used for small-radius nearest fill

    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

# ---- HDF5 layout ----
HYP = "/HDFEOS/SWATHS/HYP"
DF = f"{HYP}/Data Fields"
GF = f"{HYP}/Geolocation Fields"
HYP_GRID = "/HDFEOS/GRIDS/HYP"
DF_GRID = f"{HYP_GRID}/Data Fields"

DS_ORDER = ("surface_reflectance", "toa_radiance")
DS_WL_ATTR = "wavelengths"
DS_FWHM_ATTR = "fwhm"

DS_NODATA = f"{DF}/nodata_pixels"
DS_LAT = f"{GF}/Latitude"
DS_LON = f"{GF}/Longitude"


# ---------------------------- Data containers ----------------------------


@dataclass
class TanagerProduct:
    path: str
    data: np.ndarray  # (rows, cols, bands), float32
    wavelengths_nm: np.ndarray  # (bands,)
    fwhm_nm: np.ndarray  # (bands,)
    lat: np.ndarray | None  # (rows, cols)
    lon: np.ndarray | None  # (rows, cols)
    attrs: dict[str, Any]  # top-level file attributes (optional use)
    data_field: str  # 'surface_reflectance' or 'toa_radiance'
    data_units: str  # human-readable units string
    product_layout: str  # 'swaths' or 'grids'


@dataclass(frozen=True)
class MapGrid:
    """Target map grid parsed from product metadata."""

    epsg: int
    west: float  # geotransform[0]
    north: float  # geotransform[3]
    ewres: float  # +pixel width  (meters)
    nsres: float  # +pixel height (meters)
    rows: int
    cols: int

    @property
    def east(self):
        return self.west + self.cols * self.ewres

    @property
    def south(self):
        return self.north - self.rows * self.nsres


@dataclass(frozen=True)
class SplatPlan:
    """Precomputed per-scene bilinear splat geometry and masks."""

    rows: int
    cols: int
    # neighbor indices
    r0: np.ndarray
    c0: np.ndarray
    r1: np.ndarray
    c1: np.ndarray
    r2: np.ndarray
    c2: np.ndarray
    r3: np.ndarray
    c3: np.ndarray
    # neighbor weights
    w0: np.ndarray
    w1: np.ndarray
    w2: np.ndarray
    w3: np.ndarray
    # geometry mask (valid transform & indices in bounds)
    inb: np.ndarray
    # accumulated once (band-independent)
    visit: np.ndarray  # any sample (valid or nodata) contributed
    vnod: np.ndarray  # nodata-only influence


# ---------------------------- Reader ----------------------------


def _maybe(f, path):
    return f[path][()] if path in f else None


def _units_from_attrs(attrs, fallback):
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


def _read_tanager_h5_product(f):
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

    if HYP in f:
        data_root = DF
        nodata_path = f"{DF}/nodata_pixels"
        lat = _maybe(f, DS_LAT)
        lon = _maybe(f, DS_LON)
        layout = "swaths"
    elif HYP_GRID in f:
        data_root = DF_GRID
        nodata_path = f"{DF_GRID}/nodata_pixels"
        lat = None
        lon = None
        layout = "grids"
    else:
        raise ValueError(
            "Expected Tanager BASIC or ORTHO metadata under '/HDFEOS/SWATHS/HYP' or '/HDFEOS/GRIDS/HYP'."
        )

    dset = None
    chosen_name = None
    for name in DS_ORDER:
        p = f"{data_root}/{name}"
        if p in f:
            dset = f[p]
            chosen_name = name
            break
    if dset is None:
        raise ValueError(
            f"No Tanager dataset found in '{data_root}': expected 'surface_reflectance' or 'toa_radiance'."
        )

    arr_raw = dset[()]
    if arr_raw.ndim != 3:
        raise ValueError(f"Unexpected dataset shape {arr_raw.shape} (expected 3D)")

    data = np.transpose(arr_raw, (1, 2, 0)).astype(np.float32, copy=False)
    wl = np.array(dset.attrs[DS_WL_ATTR], dtype=np.float32)
    fwhm = np.array(
        dset.attrs.get(DS_FWHM_ATTR, np.full_like(wl, np.nan, dtype=np.float32)),
        dtype=np.float32,
    )

    order = np.argsort(wl.astype(np.float32))
    wl = wl[order]
    fwhm = fwhm[order]
    data = data[:, :, order]

    nd = _maybe(f, nodata_path)
    if nd is not None:
        if nd.shape != data.shape[:2]:
            raise ValueError(
                f"nodata_pixels shape {nd.shape} != image plane {data.shape[:2]}"
            )
        m = nd.astype(bool)
        if m.any():
            data[m, :] = np.nan

    fallback_units = (
        "unitless (reflectance)"
        if chosen_name == "surface_reflectance"
        else "W/(m^2 sr um)"
    )
    data_units = _units_from_attrs(dset.attrs, fallback_units)
    if data_units.lower() in ("unitless", "none", "1", "ratio"):
        data_units = "unitless (reflectance)"

    return data, wl, fwhm, attrs, lat, lon, layout, chosen_name, data_units


def load_tanager_basic(product_path):
    with _open_tanager_h5(product_path) as f:
        try:
            data, wl, fwhm, attrs, lat, lon, layout, chosen_name, data_units = (
                _read_tanager_h5_product(f)
            )
        except ValueError as error:
            gs.fatal(f"Input does not match product=tanager. {error}")

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
        product_layout=layout,
    )


# ---------------------------- Projection + gridding helpers ----------------------------


def _parse_structmetadata_pair(meta_text, key):
    pattern = rf"{re.escape(key)}\s*=\s*\(\s*([-+0-9.eE]+)\s*,\s*([-+0-9.eE]+)\s*\)"
    m = re.search(pattern, meta_text)
    if not m:
        return None
    return float(m.group(1)), float(m.group(2))


def _read_tanager_map_grid_from_h5(f):
    if GF in f and "Planet_Ortho_Framing" in f[GF].attrs:
        meta = f[GF].attrs["Planet_Ortho_Framing"]
        if isinstance(meta, (bytes, bytearray)):
            meta = meta.decode(errors="ignore")
        meta = json.loads(meta)

        epsg = int(meta["epsg_code"])
        rows = int(meta["rows"])
        cols = int(meta["cols"])
        west, ewres, north, nsres = (
            float(meta["geotransform"][0]),
            float(meta["geotransform"][1]),
            float(meta["geotransform"][3]),
            float(-meta["geotransform"][5]),
        )
        return MapGrid(epsg, west, north, ewres, nsres, rows, cols)

    if HYP_GRID in f:
        epsg_raw = f[HYP_GRID].attrs.get("epsg_code")
        epsg = int(epsg_raw) if epsg_raw is not None else None

        rows = None
        cols = None
        for name in DS_ORDER:
            dpath = f"{DF_GRID}/{name}"
            if dpath in f:
                shape = f[dpath].shape
                if len(shape) == 3:
                    rows = int(shape[1])
                    cols = int(shape[2])
                    break

        struct_path = "/HDFEOS INFORMATION/StructMetadata.0"
        if struct_path not in f:
            raise ValueError(
                "Missing '/HDFEOS INFORMATION/StructMetadata.0' for Tanager ortho map grid."
            )
        meta = f[struct_path][()]
        if isinstance(meta, (bytes, bytearray)):
            meta = meta.decode(errors="ignore")
        else:
            meta = str(meta)

        ul = _parse_structmetadata_pair(meta, "UpperLeftPointMtrs")
        lr = _parse_structmetadata_pair(meta, "LowerRightMtrs")

        if (
            epsg is None
            or ul is None
            or lr is None
            or rows is None
            or cols is None
            or rows <= 0
            or cols <= 0
        ):
            raise ValueError(
                "Incomplete Tanager ortho map grid metadata (epsg_code, UL/LR corners, spectral dataset shape)."
            )

        west, north = float(ul[0]), float(ul[1])
        ewres = float((float(lr[0]) - float(ul[0])) / float(cols))
        nsres = float((float(ul[1]) - float(lr[1])) / float(rows))
        if ewres <= 0 or nsres <= 0:
            raise ValueError(
                "Invalid Tanager ortho map grid resolution parsed from StructMetadata.0."
            )
        return MapGrid(epsg, west, north, ewres, nsres, rows, cols)

    raise ValueError(
        "Unsupported Tanager product metadata: expected BASIC Planet_Ortho_Framing or ORTHO StructMetadata.0 grid definition."
    )


def read_planet_map_grid(product_path):
    """
    Parse target map grid for Tanager products.
    BASIC:
      /HDFEOS/SWATHS/HYP/Geolocation Fields : Planet_Ortho_Framing
    ORTHO:
      /HDFEOS/GRIDS/HYP (epsg_code) +
      /HDFEOS INFORMATION/StructMetadata.0 (UL/LR corners) +
      spectral dataset shape (rows, cols)
    """
    try:
        with _open_tanager_h5(product_path) as f:
            return _read_tanager_map_grid_from_h5(f)
    except ValueError as error:
        gs.fatal(f"Input does not match product=tanager. {error}")


# ---- Projection info query (for -p flag) ----


def get_tanager_proj_info(product_path):
    """Return CRS/spatial info dict for a Tanager product.

    Both BASIC and ORTHO → grid layout with SRID, bounds, rows/cols, ewres/nsres.
    """
    product_type = "ORTHO"
    with _open_tanager_h5(product_path) as f:
        if GF in f and "Planet_Ortho_Framing" in f[GF].attrs:
            product_type = "BASIC"

    grid = read_planet_map_grid(product_path)
    return {
        "product_type": product_type,
        "layout": "grid",
        "srid": f"EPSG:{grid.epsg}",
        "west": grid.west,
        "east": grid.east,
        "south": grid.south,
        "north": grid.north,
        "rows": grid.rows,
        "cols": grid.cols,
        "ewres": grid.ewres,
        "nsres": grid.nsres,
        "import_behavior": (
            "Uses the per-pixel longitude and latitude arrays to geocode the image data onto the target grid defined in the product metadata, using bilinear forward splatting."
            if product_type == "BASIC"
            else "Imports the data directly on the existing product grid. No additional geocoding or reprojection is performed."
        ),
        "project_requirements": (
            "Use a GRASS project whose CRS matches the target-grid EPSG code specified in the product metadata."
            if product_type == "BASIC"
            else "Use a GRASS project whose CRS matches the product CRS."
        ),
    }


def _transform_lonlat(lon, lat, epsg):
    """Vectorized transformation WGS84 lon/lat -> target EPSG (meters)."""
    if not _HAS_PYPROJ:
        raise RuntimeError("pyproj is required for in-memory map projection.")
    t = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_epsg(epsg), always_xy=True)
    x, y = t.transform(lon, lat)
    return np.asarray(x), np.asarray(y)


def map_grid_center_lonlat(grid):
    """Return (lat, lon) for map-grid center or (None, None) if unavailable."""
    if not _HAS_PYPROJ:
        return None, None
    try:
        x = grid.west + (grid.cols * grid.ewres) * 0.5
        y = grid.north - (grid.rows * grid.nsres) * 0.5
        t = Transformer.from_crs(
            CRS.from_epsg(grid.epsg), CRS.from_epsg(4326), always_xy=True
        )
        lon, lat = t.transform(x, y)
        if not np.isfinite(lat) or not np.isfinite(lon):
            return None, None
        return float(lat), float(lon)
    except Exception:
        return None, None


def build_splat_plan(lon2d, lat2d, grid, nodata_mask):
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

    rA, cA = r0, c0
    rB, cB = r0, c0 + 1
    rC, cC = r0 + 1, c0
    rD, cD = r0 + 1, c0 + 1

    wA = (1 - dr) * (1 - dc)
    wB = (1 - dr) * dc
    wC = dr * (1 - dc)
    wD = dr * dc

    inb = (
        (rA >= 0)
        & (rD < rows)
        & (cA >= 0)
        & (cD < cols)
        & np.isfinite(fx)
        & np.isfinite(fy)
    )

    visit = np.zeros((rows, cols), dtype=np.float64)
    vnod = np.zeros((rows, cols), dtype=np.float64)

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
        rows=rows,
        cols=cols,
        r0=rA,
        c0=cA,
        r1=rB,
        c1=cB,
        r2=rC,
        c2=cC,
        r3=rD,
        c3=cD,
        w0=wA,
        w1=wB,
        w2=wC,
        w3=wD,
        inb=inb,
        visit=visit,
        vnod=vnod,
    )


def splat_band_with_plan(values, plan, nodata=np.nan):
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


def project_band_to_map_grid(band2d, plan, fill_8_neighbor=True):
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


def _open_tanager_h5(product_path):
    try:
        return h5py.File(product_path, "r")
    except OSError as error:
        gs.fatal(
            "Input does not match product=tanager. "
            f"Expected a Tanager HDF5 (.h5) product. {error}"
        )
