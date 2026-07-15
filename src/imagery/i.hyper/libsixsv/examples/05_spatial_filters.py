"""
05_spatial_filters.py — Spatial filtering, terrain, and adjacency corrections.

Demonstrates:
  - Gaussian and box spatial filters (NaN-safe)
  - Terrain illumination and transmittance corrections
  - Adjacency effect correction (Vermote 1997)
  - Uncertainty propagation (noise + AOD perturbation in quadrature)

Run:
    python3 05_spatial_filters.py
"""

import os, ctypes, math
import numpy as np

# ── Load libsixsv.so ──────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
for _p in [os.environ.get("LIB_SIXSV", ""),
           os.path.join(_here, "..", "testsuite", "libsixsv.so")]:
    if _p and os.path.exists(_p):
        _lib = ctypes.CDLL(_p); break
else:
    raise ImportError("libsixsv.so not found — run 'make' in testsuite/ first.")

_FP = ctypes.POINTER(ctypes.c_float)

class _Cfg(ctypes.Structure):
    _fields_ = [
        ("wl",  _FP), ("n_wl",  ctypes.c_int),
        ("aod", _FP), ("n_aod", ctypes.c_int),
        ("h2o", _FP), ("n_h2o", ctypes.c_int),
        ("sza", ctypes.c_float), ("vza", ctypes.c_float),
        ("raa", ctypes.c_float), ("altitude_km", ctypes.c_float),
        ("atmo_model",    ctypes.c_int), ("aerosol_model",    ctypes.c_int),
        ("surface_pressure", ctypes.c_float), ("ozone_du", ctypes.c_float),
        ("mie_r_mode",   ctypes.c_float), ("mie_sigma_g", ctypes.c_float),
        ("mie_m_real",   ctypes.c_float), ("mie_m_imag",  ctypes.c_float),
        ("brdf_type",    ctypes.c_int),   ("brdf_params",  ctypes.c_float * 5),
        ("enable_polar", ctypes.c_int),
    ]

class _Arr(ctypes.Structure):
    _fields_ = [
        ("R_atm", _FP), ("T_down", _FP), ("T_up", _FP), ("s_alb", _FP),
        ("T_down_dir", _FP), ("R_atmQ", _FP), ("R_atmU", _FP),
    ]

def _fp(a):
    return np.ascontiguousarray(a, dtype=np.float32).ctypes.data_as(_FP)

def compute_lut(wl, aod, h2o, sza=30., vza=5., raa=90., altitude_km=1000.,
                atmo_model=1, aerosol_model=1, ozone_du=300.,
                surface_pressure=0., enable_polar=0):
    wl_  = np.asarray(wl,  dtype=np.float32)
    aod_ = np.asarray(aod, dtype=np.float32)
    h2o_ = np.asarray(h2o, dtype=np.float32)
    N    = wl_.size * aod_.size * h2o_.size
    Ra, Td, Tu, ss = [np.empty(N, np.float32) for _ in range(4)]
    cfg_c = _Cfg(
        wl=_fp(wl_), n_wl=wl_.size, aod=_fp(aod_), n_aod=aod_.size,
        h2o=_fp(h2o_), n_h2o=h2o_.size,
        sza=sza, vza=vza, raa=raa, altitude_km=altitude_km,
        atmo_model=atmo_model, aerosol_model=aerosol_model,
        ozone_du=ozone_du, surface_pressure=surface_pressure,
        enable_polar=enable_polar,
    )
    arr_c = _Arr(R_atm=_fp(Ra), T_down=_fp(Td), T_up=_fp(Tu), s_alb=_fp(ss))
    _lib.atcorr_compute_lut(ctypes.byref(cfg_c), ctypes.byref(arr_c))
    sh = (aod_.size, h2o_.size, wl_.size)
    return dict(cfg_c=cfg_c, arr_c=arr_c,
                wl=wl_, aod=aod_, h2o=h2o_,
                R_atm=Ra.reshape(sh), T_down=Td.reshape(sh),
                T_up=Tu.reshape(sh),  s_alb=ss.reshape(sh),
                _Ra=Ra, _Td=Td, _Tu=Tu, _ss=ss)

def lut_slice(lut, aod_val, h2o_val):
    n = lut['wl'].size
    Rs, Tds, Tus, ss = [np.empty(n, np.float32) for _ in range(4)]
    _lib.atcorr_lut_slice(
        ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
        ctypes.c_float(aod_val), ctypes.c_float(h2o_val),
        _fp(Rs), _fp(Tds), _fp(Tus), _fp(ss), None)
    return dict(R_atm=Rs, T_down=Tds, T_up=Tus, s_alb=ss)

nrows, ncols = 64, 64
npix = nrows * ncols

# ── Synthetic AOD map with NaN outliers ───────────────────────────────────────
r_idx = np.repeat(np.arange(nrows), ncols).astype(np.float32)
c_idx = np.tile(np.arange(ncols), nrows).astype(np.float32)
aod_map = (0.10 + 0.15 * np.sin(r_idx * 0.3) * np.cos(c_idx * 0.3)).astype(np.float32)
aod_map[::100] = float('nan')   # cloud-masked outliers

# ── 1. Gaussian filter (in-place, NaN excluded from neighbourhood) ────────────
_lib.spatial_gaussian_filter.argtypes = [
    _FP, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.spatial_gaussian_filter.restype = None

aod_gauss = aod_map.copy()
n_nan_before = int(np.isnan(aod_gauss).sum())
_lib.spatial_gaussian_filter(
    _fp(aod_gauss), ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_float(2.5))
n_nan_after = int(np.isnan(aod_gauss).sum())
print(f"Gaussian filter: NaN before={n_nan_before}  after={n_nan_after}")

# ── 2. Box filter (input → separate output buffer) ────────────────────────────
_lib.spatial_box_filter.argtypes = [
    _FP, _FP, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.spatial_box_filter.restype = None

aod_box = np.empty(npix, np.float32)
_lib.spatial_box_filter(
    _fp(aod_map), _fp(aod_box),
    ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_int(3))
print(f"Box filter (half=3): output mean = {np.nanmean(aod_box):.4f}")

# ── 3. Terrain illumination correction ───────────────────────────────────────
_lib.cos_incidence.argtypes   = [ctypes.c_float] * 4
_lib.cos_incidence.restype    = ctypes.c_float
_lib.skyview_factor.argtypes  = [ctypes.c_float]
_lib.skyview_factor.restype   = ctypes.c_float
_lib.atcorr_terrain_T_down.argtypes = [ctypes.c_float] * 5
_lib.atcorr_terrain_T_down.restype  = ctypes.c_float
_lib.atcorr_terrain_T_up.argtypes   = [ctypes.c_float] * 3
_lib.atcorr_terrain_T_up.restype    = ctypes.c_float

sza, saa, slope, aspect = 35.0, 150.0, 20.0, 180.0   # south-facing slope
cos_i = _lib.cos_incidence(ctypes.c_float(sza), ctypes.c_float(saa),
                            ctypes.c_float(slope), ctypes.c_float(aspect))
V_d   = _lib.skyview_factor(ctypes.c_float(slope))
print(f"\nTerrain:  cos_i = {cos_i:.4f}  skyview = {V_d:.4f}"
      + ("  (topographic shadow)" if cos_i <= 0 else ""))

T_down, T_down_dir = 0.85, 0.70
cos_sza = math.cos(math.radians(sza))
T_down_eff = _lib.atcorr_terrain_T_down(
    ctypes.c_float(T_down), ctypes.c_float(T_down_dir),
    ctypes.c_float(cos_sza), ctypes.c_float(cos_i), ctypes.c_float(V_d))
print(f"T_down flat={T_down:.4f}  T_down_eff (slope)={T_down_eff:.4f}")

T_up = 0.90
T_up_eff = _lib.atcorr_terrain_T_up(
    ctypes.c_float(T_up), ctypes.c_float(math.cos(math.radians(8.0))),
    ctypes.c_float(15.0))
print(f"T_up flat={T_up:.4f}   T_up_eff (off-nadir view)={T_up_eff:.4f}")

# ── 4. Adjacency effect correction ───────────────────────────────────────────
_lib.adjacency_correct_band.argtypes = [
    _FP, ctypes.c_int, ctypes.c_int,
    ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
]
_lib.adjacency_correct_band.restype = None

r_boa = (0.10 + 0.25 * c_idx / ncols).astype(np.float32).copy()
_lib.adjacency_correct_band(
    _fp(r_boa), ctypes.c_int(nrows), ctypes.c_int(ncols),
    ctypes.c_float(1.0),    # psf_radius_km
    ctypes.c_float(30.0),   # pixel_size_m (Landsat 30 m)
    ctypes.c_float(1.0 - T_down_dir),  # T_scat
    ctypes.c_float(0.10),   # s_alb
    ctypes.c_float(0.65),   # wl_um
    ctypes.c_float(0.15),   # aod550
    ctypes.c_float(1013.25),# pressure [hPa]
    ctypes.c_float(sza), ctypes.c_float(8.0))
print(f"\nAdjacency correction: mean BOA = {r_boa.mean():.4f}")

# ── 5. Uncertainty propagation ────────────────────────────────────────────────
lut = compute_lut(
    wl=[0.65], aod=[0.0, 0.1, 0.2, 0.4], h2o=[1.0, 3.0],
    sza=35., vza=8., raa=90., altitude_km=1000.,
    atmo_model=1, aerosol_model=1, ozone_du=300.,
)

_lib.sixs_E0.argtypes              = [ctypes.c_float]
_lib.sixs_E0.restype               = ctypes.c_float
_lib.sixs_earth_sun_dist2.argtypes = [ctypes.c_int]
_lib.sixs_earth_sun_dist2.restype  = ctypes.c_double
E0 = float(_lib.sixs_E0(ctypes.c_float(0.65)))
d2 = float(_lib.sixs_earth_sun_dist2(ctypes.c_int(185)))

_lib.uncertainty_compute_band.argtypes = [
    _FP, _FP,                         # rad_band (or NULL), refl_band
    ctypes.c_int,                     # npix
    ctypes.c_float, ctypes.c_float,   # E0, d2
    ctypes.c_float,                   # cos_sza
    ctypes.c_float, ctypes.c_float,   # T_down, T_up
    ctypes.c_float, ctypes.c_float,   # s_alb, R_atm
    ctypes.c_float, ctypes.c_float,   # nedl, aod_sigma
    ctypes.POINTER(_Cfg),
    ctypes.POINTER(_Arr),
    ctypes.c_float, ctypes.c_float, ctypes.c_float,  # wl_um, aod_val, h2o_val
    _FP,                              # sigma_out
]
_lib.uncertainty_compute_band.restype = None

sigma = np.empty(npix, np.float32)
_lib.uncertainty_compute_band(
    None, _fp(r_boa),
    ctypes.c_int(npix),
    ctypes.c_float(E0), ctypes.c_float(d2),
    ctypes.c_float(math.cos(math.radians(35.))),
    ctypes.c_float(0.85), ctypes.c_float(0.90),
    ctypes.c_float(0.08), ctypes.c_float(0.05),
    ctypes.c_float(0.), ctypes.c_float(0.04),
    ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
    ctypes.c_float(0.65), ctypes.c_float(0.15), ctypes.c_float(2.0),
    _fp(sigma),
)
print(f"Uncertainty (σ_rfl) at 650 nm: mean = {np.nanmean(sigma):.5f}")
