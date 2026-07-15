"""
02_scene_correction.py — Per-pixel scene-scale Lambertian correction.

Demonstrates:
  - Per-pixel trilinear LUT interpolation from a spatially varying AOD map
  - Vectorised NumPy inversion (no Python loop over pixels)
  - Polarized RT (enable_polar=1) for improved blue-band accuracy
  - BRDF-coupled inversion (RPV model, green band)

Run:
    python3 02_scene_correction.py
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

def invert(rho_toa, R_atm, T_down, T_up, s_alb):
    y = (np.asarray(rho_toa) - R_atm) / (T_down * T_up + 1e-10)
    return y / (1.0 + s_alb * y)

# ── Scene dimensions ──────────────────────────────────────────────────────────
nrows, ncols = 64, 64
npix = nrows * ncols

# ── Build LUT with polarized RT ───────────────────────────────────────────────
lut = compute_lut(
    wl  = [0.45, 0.55, 0.65, 0.87],
    aod = [0.0, 0.1, 0.2, 0.3, 0.5],
    h2o = [0.5, 1.5, 2.5, 3.5],
    sza=32., vza=8., raa=120., altitude_km=1000.,
    atmo_model=1, aerosol_model=1, ozone_du=310.,
    enable_polar=1,   # Polarized RT: Stokes I/Q/U, improves blue-band R_atm
)
print(f"LUT computed: R_atm {lut['R_atm'].shape}  (polarized RT enabled)")

# ── Spatially varying AOD and H₂O maps ───────────────────────────────────────
col_idx = np.tile(np.arange(ncols), nrows).astype(np.float32)
row_idx = np.repeat(np.arange(nrows), ncols).astype(np.float32)
aod_map = (0.05 + 0.3 * col_idx / ncols).astype(np.float32)   # [npix]
h2o_map = (1.0  + 2.0 * row_idx / nrows).astype(np.float32)   # [npix]

# ── Per-band correction with per-pixel AOD/H₂O via trilinear interpolation ───
# atcorr_lut_interp_pixel: trilinear lookup in the 3-D [aod, h2o, wl] LUT.
_lib.atcorr_lut_interp_pixel.restype = None

band_names = ["Blue", "Green", "Red", "NIR"]
wl = lut['wl']

for b, name in enumerate(band_names):
    rho_toa = (0.05 + 0.25 * b / 4
               + 0.02 * np.sin(np.arange(npix) * 0.1)).astype(np.float32)
    Ra  = np.empty(npix, np.float32)
    Td  = np.empty(npix, np.float32)
    Tu  = np.empty(npix, np.float32)
    sa  = np.empty(npix, np.float32)

    for i in range(npix):
        Ra_s  = ctypes.c_float()
        Td_s  = ctypes.c_float()
        Tu_s  = ctypes.c_float()
        sa_s  = ctypes.c_float()
        _lib.atcorr_lut_interp_pixel(
            ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
            ctypes.c_float(float(aod_map[i])),
            ctypes.c_float(float(h2o_map[i])),
            ctypes.c_float(float(wl[b])),
            ctypes.byref(Ra_s), ctypes.byref(Td_s),
            ctypes.byref(Tu_s), ctypes.byref(sa_s))
        Ra[i] = Ra_s.value; Td[i] = Td_s.value
        Tu[i] = Tu_s.value; sa[i] = sa_s.value

    rho_boa = invert(rho_toa, Ra, Td, Tu, sa)
    print(f"Band {b} {name} ({wl[b]:.2f} µm): mean BOA = {rho_boa.mean():.4f}")

# ── BRDF-coupled inversion (RPV model, green band) ────────────────────────────
# sixs_brdf_albe() returns the white-sky (hemispherical) albedo for an RPV surface.
# atcorr_invert_brdf is a static inline in atcorr.h:
#   y = (rho_toa - R_atm) / (T_down * T_up + 1e-10)
#   rho_brdf = y * (1 - s_alb * rho_albe)
_lib.sixs_brdf_albe.argtypes = [ctypes.c_int, _FP, ctypes.c_float,
                                 ctypes.c_int, ctypes.c_int]
_lib.sixs_brdf_albe.restype = ctypes.c_float

import math
rpv_params = (ctypes.c_float * 5)(0.12, -0.15, 0.75, 0., 0.)
cos_sza = math.cos(math.radians(32.))
rho_albe = float(_lib.sixs_brdf_albe(
    ctypes.c_int(1), rpv_params,
    ctypes.c_float(cos_sza), ctypes.c_int(48), ctypes.c_int(24)))

sl_green = lut_slice(lut, aod_val=0.15, h2o_val=2.0)
Ra  = float(sl_green['R_atm'][1])
Td  = float(sl_green['T_down'][1])
Tu  = float(sl_green['T_up'][1])
sa  = float(sl_green['s_alb'][1])
rho_toa_val = 0.18
y = (rho_toa_val - Ra) / (Td * Tu + 1e-10)
rho_brdf = y * (1.0 - sa * rho_albe)
print(f"\nRPV BRDF correction: rho_BRDF = {rho_brdf:.4f}  "
      f"(white-sky albedo = {rho_albe:.4f})")
