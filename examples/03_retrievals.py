"""
03_retrievals.py — Atmospheric state retrievals.

Demonstrates:
  - Surface pressure from elevation (ISA)
  - H₂O column from 940 nm band depth
  - AOD from MODIS DDV + MAIAC patch-median smoothing
  - O₃ from Chappuis 600 nm band depth
  - Cloud/shadow/water/snow quality bitmask
  - Joint AOD + H₂O optimal estimation

Run:
    python3 03_retrievals.py
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

# ── Quality-mask bit constants (from atcorr.h) ────────────────────────────────
MASK_CLOUD  = 0x01
MASK_SHADOW = 0x02
MASK_WATER  = 0x04
MASK_SNOW   = 0x08

# ── Scene setup ───────────────────────────────────────────────────────────────
npix = 32 * 32
doy, sza, vza = 185, 32.0, 5.0

# ── Synthetic per-pixel radiances ─────────────────────────────────────────────
def band(base, noise=5.0):
    return (base + noise * np.sin(np.arange(npix) * 0.37)).astype(np.float32)

L_470  = band(80.0, 5.0)
L_540  = band(70.0, 3.0)
L_600  = band(62.0, 3.0)
L_660  = band(55.0, 4.0)
L_680  = band(50.0, 3.0)
L_860  = band(120.0, 8.0)
L_865  = band(118.0, 8.0)
L_940  = (L_865 * 0.85 - 2.0 * np.sin(np.arange(npix) * 0.5)).astype(np.float32)
L_1040 = (L_865 * 0.92).astype(np.float32)
L_2130 = band(25.0, 2.0)

# ── 1. Surface pressure from elevation ────────────────────────────────────────
_lib.retrieve_pressure_isa.argtypes = [ctypes.c_float]
_lib.retrieve_pressure_isa.restype  = ctypes.c_float
p_surface = _lib.retrieve_pressure_isa(ctypes.c_float(1500.0))
print(f"Surface pressure at 1500 m: {p_surface:.1f} hPa")

# ── 2. H₂O retrieval from 940 nm band depth ───────────────────────────────────
_lib.retrieve_h2o_940.argtypes = [
    _FP, _FP, _FP,          # L_865, L_940, L_1040
    ctypes.c_float,          # fwhm_um (0 = broadband)
    ctypes.c_int,            # npix
    ctypes.c_float,          # sza_deg
    ctypes.c_float,          # vza_deg
    _FP,                     # out_wvc [npix]
]
_lib.retrieve_h2o_940.restype = None
wvc = np.empty(npix, np.float32)
_lib.retrieve_h2o_940(_fp(L_865), _fp(L_940), _fp(L_1040),
                      ctypes.c_float(0.), ctypes.c_int(npix),
                      ctypes.c_float(sza), ctypes.c_float(vza), _fp(wvc))
print(f"\nH₂O retrieval (940 nm): mean WVC = {wvc.mean():.2f} g/cm²")

# ── 3. AOD retrieval (DDV) ────────────────────────────────────────────────────
_lib.retrieve_aod_ddv.argtypes = [
    _FP, _FP, _FP, _FP,   # L_470, L_660, L_860, L_2130
    ctypes.c_int,           # npix
    ctypes.c_int,           # doy
    ctypes.c_float,         # sza_deg
    _FP,                    # out_aod [npix]
]
_lib.retrieve_aod_ddv.restype = ctypes.c_float
aod_px = np.empty(npix, np.float32)
aod_scene = _lib.retrieve_aod_ddv(
    _fp(L_470), _fp(L_660), _fp(L_860), _fp(L_2130),
    ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza), _fp(aod_px))
print(f"AOD retrieval (DDV): scene mean = {float(aod_scene):.3f}")

# MAIAC patch-median spatial regularisation (in-place, 32×32 grid)
_lib.retrieve_aod_maiac.argtypes = [
    _FP, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.retrieve_aod_maiac.restype = None
aod_2d = aod_px.reshape(32, 32).copy()
_lib.retrieve_aod_maiac(_fp(aod_2d), ctypes.c_int(32), ctypes.c_int(32),
                         ctypes.c_int(8))
print(f"AOD after MAIAC smoothing: mean = {aod_2d.mean():.3f}")

# ── 4. O₃ retrieval from Chappuis band ────────────────────────────────────────
_lib.retrieve_o3_chappuis.argtypes = [
    _FP, _FP, _FP,           # L_540, L_600, L_680
    ctypes.c_int,             # npix
    ctypes.c_float,           # sza_deg
    ctypes.c_float,           # vza_deg
]
_lib.retrieve_o3_chappuis.restype = ctypes.c_float
o3_du = _lib.retrieve_o3_chappuis(
    _fp(L_540), _fp(L_600), _fp(L_680),
    ctypes.c_int(npix), ctypes.c_float(sza), ctypes.c_float(vza))
print(f"O₃ column (Chappuis 600 nm): {float(o3_du):.0f} DU")

# ── 5. Quality bitmask ────────────────────────────────────────────────────────
_lib.retrieve_quality_mask.argtypes = [
    _FP, _FP, _FP,           # L_blue, L_red, L_nir
    _FP,                      # L_swir (or NULL for no snow)
    ctypes.c_int,             # npix
    ctypes.c_int,             # doy
    ctypes.c_float,           # sza_deg
    ctypes.POINTER(ctypes.c_uint8),  # out_mask [npix]
]
_lib.retrieve_quality_mask.restype = None
mask = np.zeros(npix, dtype=np.uint8)
_lib.retrieve_quality_mask(
    _fp(L_470), _fp(L_660), _fp(L_865),
    None,
    ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza),
    mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))
n_cloud = int((mask & MASK_CLOUD).astype(bool).sum())
n_water = int((mask & MASK_WATER).astype(bool).sum())
print(f"Quality mask: cloud={n_cloud}  water={n_water}  (of {npix} pixels)")

# ── 6. Joint AOD + H₂O optimal estimation ─────────────────────────────────────
lut = compute_lut(
    wl  = [0.47, 0.55, 0.66, 0.87],
    aod = [0.0, 0.1, 0.2, 0.4],
    h2o = [1.0, 2.0, 3.0],
    sza=sza, vza=vza, raa=90., altitude_km=1000.,
    atmo_model=1, aerosol_model=1, ozone_du=300.,
)

n_vis   = 4
vis_wl  = np.array([0.47, 0.55, 0.66, 0.87], dtype=np.float32)
rho_vis = np.column_stack([
    (0.10 + 0.05 * b + 0.02 * np.sin(np.arange(npix) * 0.2)).astype(np.float32)
    for b in range(n_vis)
])  # [npix, n_vis]

_lib.oe_invert_aod_h2o.argtypes = [
    ctypes.POINTER(_Cfg), ctypes.POINTER(_Arr),
    _FP, ctypes.c_int, ctypes.c_int,   # rho_toa_vis, npix, n_vis
    _FP,                               # vis_wl
    _FP, _FP, _FP,                    # L_865, L_940, L_1040
    ctypes.c_float, ctypes.c_float,   # sza, vza
    ctypes.c_float, ctypes.c_float,   # aod_prior, h2o_prior
    ctypes.c_float, ctypes.c_float, ctypes.c_float,  # sigma_aod, _h2o, _spec
    ctypes.c_float,                   # fwhm_940
    _FP, _FP,                         # out_aod, out_h2o
]
_lib.oe_invert_aod_h2o.restype = None

out_aod = np.empty(npix, np.float32)
out_h2o = np.empty(npix, np.float32)
_lib.oe_invert_aod_h2o(
    ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
    _fp(rho_vis), ctypes.c_int(npix), ctypes.c_int(n_vis), _fp(vis_wl),
    _fp(L_865), _fp(L_940), _fp(L_1040),
    ctypes.c_float(sza), ctypes.c_float(vza),
    ctypes.c_float(float(aod_scene)), ctypes.c_float(float(wvc.mean())),
    ctypes.c_float(0.5), ctypes.c_float(1.0), ctypes.c_float(0.01),
    ctypes.c_float(0.),
    _fp(out_aod), _fp(out_h2o))
print(f"OE retrieval: mean AOD = {out_aod.mean():.3f}  "
      f"mean H₂O = {out_h2o.mean():.2f} g/cm²")
