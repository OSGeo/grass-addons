"""
01_basic_lut.py — LUT computation and single-pixel Lambertian correction.

Demonstrates:
  - Loading libsixsv.so via ctypes (no external dependencies)
  - compute_lut: builds 3-D [n_aod × n_h2o × n_wl] correction tables
  - lut_slice: bilinear interpolation → 1-D per-band arrays
  - Lambertian inversion formula (vectorised NumPy)
  - Solar irradiance E0 and Earth–Sun distance factor d²

Run:
    python3 01_basic_lut.py
    LIB_SIXSV=/path/to/libsixsv.so python3 01_basic_lut.py
"""

import os, ctypes
import numpy as np

# ── Load libsixsv.so ──────────────────────────────────────────────────────────
_here = os.path.dirname(os.path.abspath(__file__))
for _p in [os.environ.get("LIB_SIXSV", ""),
           os.path.join(_here, "..", "testsuite", "libsixsv.so")]:
    if _p and os.path.exists(_p):
        _lib = ctypes.CDLL(_p); break
else:
    raise ImportError("libsixsv.so not found — run 'make' in testsuite/ first.")

# ── ctypes struct mirrors (match atcorr.h exactly) ────────────────────────────
_FP = ctypes.POINTER(ctypes.c_float)

class _Cfg(ctypes.Structure):
    _fields_ = [
        ("wl",  _FP), ("n_wl",  ctypes.c_int),
        ("aod", _FP), ("n_aod", ctypes.c_int),
        ("h2o", _FP), ("n_h2o", ctypes.c_int),
        ("sza", ctypes.c_float), ("vza", ctypes.c_float),
        ("raa", ctypes.c_float), ("altitude_km", ctypes.c_float),
        ("atmo_model",       ctypes.c_int),
        ("aerosol_model",    ctypes.c_int),
        ("surface_pressure", ctypes.c_float),
        ("ozone_du",         ctypes.c_float),
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
    """Return a ctypes float* pointing to a C-contiguous float32 array."""
    return np.ascontiguousarray(a, dtype=np.float32).ctypes.data_as(_FP)

# ── LUT helpers ───────────────────────────────────────────────────────────────
def compute_lut(wl, aod, h2o, sza=30., vza=5., raa=90., altitude_km=1000.,
                atmo_model=1, aerosol_model=1, ozone_du=300.,
                surface_pressure=0., enable_polar=0):
    """Compute 3-D LUT [n_aod × n_h2o × n_wl].  Returns a bundle dict."""
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
    # Keep all arrays in the dict so ctypes pointers remain valid
    return dict(cfg_c=cfg_c, arr_c=arr_c,
                wl=wl_, aod=aod_, h2o=h2o_,
                R_atm=Ra.reshape(sh), T_down=Td.reshape(sh),
                T_up=Tu.reshape(sh),  s_alb=ss.reshape(sh),
                _Ra=Ra, _Td=Td, _Tu=Tu, _ss=ss)

def lut_slice(lut, aod_val, h2o_val):
    """Bilinear interpolation to (aod_val, h2o_val) → 1-D arrays [n_wl]."""
    n = lut['wl'].size
    Rs, Tds, Tus, ss = [np.empty(n, np.float32) for _ in range(4)]
    _lib.atcorr_lut_slice(
        ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
        ctypes.c_float(aod_val), ctypes.c_float(h2o_val),
        _fp(Rs), _fp(Tds), _fp(Tus), _fp(ss), None)
    return dict(R_atm=Rs, T_down=Tds, T_up=Tus, s_alb=ss)

def invert(rho_toa, R_atm, T_down, T_up, s_alb):
    """Lambertian BOA inversion (vectorised; mirrors atcorr_invert() in C)."""
    y = (np.asarray(rho_toa) - R_atm) / (T_down * T_up + 1e-10)
    return y / (1.0 + s_alb * y)

# ── 1. Build LUT: 4 wavelengths × 4 AOD × 3 H₂O ─────────────────────────────
lut = compute_lut(
    wl  = [0.45, 0.55, 0.65, 0.87],
    aod = [0.0, 0.1, 0.2, 0.4],
    h2o = [1.0, 2.0, 3.0],
    sza=35., vza=5., raa=90., altitude_km=1000.,
    atmo_model=1, aerosol_model=1, ozone_du=300.,
)
print(f"LUT shape: R_atm {lut['R_atm'].shape}  (n_aod × n_h2o × n_wl)")

# ── 2. Slice at AOD=0.15, H₂O=2.0 ────────────────────────────────────────────
sl = lut_slice(lut, aod_val=0.15, h2o_val=2.0)

# ── 3. Lambertian inversion for 4 bands ──────────────────────────────────────
band_names = ["Blue", "Green", "Red", "NIR"]
rho_toa    = np.array([0.18, 0.20, 0.15, 0.35], dtype=np.float32)
rho_boa    = invert(rho_toa, sl['R_atm'], sl['T_down'], sl['T_up'], sl['s_alb'])

print(f"\n{'Band':<6} {'TOA':>7} {'BOA':>7} {'R_atm':>7} "
      f"{'T_dn':>7} {'T_up':>7} {'s_alb':>7}")
print("-" * 54)
for b, name in enumerate(band_names):
    print(f"{name:<6} {rho_toa[b]:7.4f} {rho_boa[b]:7.4f} "
          f"{sl['R_atm'][b]:7.4f} {sl['T_down'][b]:7.4f} "
          f"{sl['T_up'][b]:7.4f} {sl['s_alb'][b]:7.4f}")

# ── 4. Solar irradiance and Earth–Sun distance ────────────────────────────────
_lib.sixs_E0.argtypes              = [ctypes.c_float]
_lib.sixs_E0.restype               = ctypes.c_float
_lib.sixs_earth_sun_dist2.argtypes = [ctypes.c_int]
_lib.sixs_earth_sun_dist2.restype  = ctypes.c_double

E0 = _lib.sixs_E0(ctypes.c_float(0.55))
d2 = _lib.sixs_earth_sun_dist2(ctypes.c_int(185))
print(f"\nSolar irradiance at 550 nm: {E0:.1f} W/m²/µm")
print(f"Earth-Sun d² at DOY 185 (aphelion): {d2:.6f} AU²")
