"""
06_full_pipeline.py — End-to-end hyperspectral atmospheric correction.

Full operational pipeline (mirrors 06_full_pipeline.c):
 1.  Surface pressure from elevation (ISA)
 2.  O₃ column from Chappuis 600 nm band depth
 3.  H₂O map from 940 nm band depth + Gaussian smoothing
 4.  AOD map from MODIS DDV + MAIAC spatial regularisation
 5.  Build 3-D LUT (OpenMP-parallel under the hood)
 6.  Quality bitmask (cloud / shadow / water / snow)
 7.  Per-pixel atmospheric correction (Lambertian, fully vectorised)
 8.  Adjacency effect correction (Vermote 1997)
 9.  Per-band uncertainty propagation
10.  DASF canopy structure retrieval from 710–790 nm NIR plateau

Run:
    python3 06_full_pipeline.py
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

def invert(rho_toa, R_atm, T_down, T_up, s_alb):
    y = (np.asarray(rho_toa, dtype=np.float32) - R_atm) / (T_down * T_up + 1e-10)
    return (y / (1.0 + s_alb * y)).astype(np.float32)

# ── Scene parameters ──────────────────────────────────────────────────────────
nrows, ncols = 32, 32
npix  = nrows * ncols
doy   = 210
sza, vza, raa = 30.0, 6.0, 100.0
elev_m = 800.0

# Hyperspectral: 10 bands 450–870 nm
wl = np.array([0.45, 0.50, 0.55, 0.60, 0.65,
               0.70, 0.75, 0.80, 0.84, 0.87], dtype=np.float32)
n_bands = len(wl)

print("=== lib6sv Full Pipeline ===")
print(f"Scene: {nrows}×{ncols} px  DOY={doy}  SZA={sza:.1f}°  VZA={vza:.1f}°\n")

# ── Synthetic TOA radiance cube ───────────────────────────────────────────────
bases = [90, 85, 78, 68, 60, 50, 45, 42, 38, 35]
idx   = np.arange(npix)
bands = [(b + 8.0 * np.sin(idx * 0.15 + b)).astype(np.float32) for b in bases]

L_470  = (95.0 + 6.0 * np.sin(idx * 0.15 + 95)).astype(np.float32)
L_660  = (60.0 + 4.0 * np.sin(idx * 0.15 + 60)).astype(np.float32)
L_865  = bands[8]
L_2130 = (20.0 + 2.0 * np.sin(idx * 0.15 + 20)).astype(np.float32)
L_940  = (L_865 * 0.82 - 3.0 * np.sin(idx * 0.4)).astype(np.float32)
L_1040 = (L_865 * 0.91).astype(np.float32)
L_540, L_600, L_680 = bands[2], bands[3], bands[5]

# ── Step 1: Surface pressure ──────────────────────────────────────────────────
_lib.retrieve_pressure_isa.argtypes = [ctypes.c_float]
_lib.retrieve_pressure_isa.restype  = ctypes.c_float
pressure = float(_lib.retrieve_pressure_isa(ctypes.c_float(elev_m)))
print(f"[1] Surface pressure: {pressure:.1f} hPa ({elev_m:.0f} m elevation)")

# ── Step 2: O₃ column ────────────────────────────────────────────────────────
_lib.retrieve_o3_chappuis.argtypes = [
    _FP, _FP, _FP, ctypes.c_int, ctypes.c_float, ctypes.c_float]
_lib.retrieve_o3_chappuis.restype  = ctypes.c_float
o3_du = float(_lib.retrieve_o3_chappuis(
    _fp(L_540), _fp(L_600), _fp(L_680),
    ctypes.c_int(npix), ctypes.c_float(sza), ctypes.c_float(vza)))
print(f"[2] O₃ column: {o3_du:.0f} DU")

# ── Step 3: H₂O map ───────────────────────────────────────────────────────────
_lib.retrieve_h2o_940.argtypes = [
    _FP, _FP, _FP, ctypes.c_float, ctypes.c_int,
    ctypes.c_float, ctypes.c_float, _FP]
_lib.retrieve_h2o_940.restype  = None
wvc = np.empty(npix, np.float32)
_lib.retrieve_h2o_940(
    _fp(L_865), _fp(L_940), _fp(L_1040),
    ctypes.c_float(0.), ctypes.c_int(npix),
    ctypes.c_float(sza), ctypes.c_float(vza), _fp(wvc))
wvc_mean = float(wvc.mean())

_lib.spatial_gaussian_filter.argtypes = [_FP, ctypes.c_int, ctypes.c_int, ctypes.c_float]
_lib.spatial_gaussian_filter.restype  = None
wvc_2d = np.ascontiguousarray(wvc.reshape(nrows, ncols))
_lib.spatial_gaussian_filter(
    wvc_2d.ctypes.data_as(_FP),
    ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_float(1.5))
print(f"[3] H₂O: mean WVC = {wvc_mean:.2f} g/cm²")

# ── Step 4: AOD map (DDV + MAIAC) ────────────────────────────────────────────
_lib.retrieve_aod_ddv.argtypes = [
    _FP, _FP, _FP, _FP, ctypes.c_int, ctypes.c_int, ctypes.c_float, _FP]
_lib.retrieve_aod_ddv.restype  = ctypes.c_float
aod_px = np.empty(npix, np.float32)
aod_scene = float(_lib.retrieve_aod_ddv(
    _fp(L_470), _fp(L_660), _fp(L_865), _fp(L_2130),
    ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza), _fp(aod_px)))

_lib.retrieve_aod_maiac.argtypes = [_FP, ctypes.c_int, ctypes.c_int, ctypes.c_int]
_lib.retrieve_aod_maiac.restype  = None
aod_2d = np.ascontiguousarray(aod_px.reshape(nrows, ncols))
_lib.retrieve_aod_maiac(
    aod_2d.ctypes.data_as(_FP),
    ctypes.c_int(nrows), ctypes.c_int(ncols), ctypes.c_int(8))
print(f"[4] AOD: scene mean = {aod_scene:.3f} (after MAIAC)")

# ── Step 5: LUT ───────────────────────────────────────────────────────────────
lut = compute_lut(
    wl  = wl,
    aod = np.array([0.0, 0.1, 0.2, 0.3, 0.5], dtype=np.float32),
    h2o = np.array([0.5, 1.5, 2.5, 3.5],       dtype=np.float32),
    sza=sza, vza=vza, raa=raa,
    altitude_km=1000.0,
    atmo_model=1, aerosol_model=1,
    ozone_du=o3_du, surface_pressure=pressure,
)
print(f"[5] LUT computed: {lut['R_atm'].shape}")

# ── Step 6: Quality bitmask ───────────────────────────────────────────────────
_lib.retrieve_quality_mask.argtypes = [
    _FP, _FP, _FP, _FP,          # L_blue, L_red, L_nir, L_swir
    ctypes.c_int, ctypes.c_int, ctypes.c_float,  # npix, doy, sza_deg
    ctypes.POINTER(ctypes.c_uint8)]              # out_mask
_lib.retrieve_quality_mask.restype = None
mask = np.zeros(npix, dtype=np.uint8)
_lib.retrieve_quality_mask(
    _fp(L_470), _fp(L_660), _fp(L_865), None,
    ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza),
    mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))
n_valid = int((mask == 0).sum())
print(f"[6] Valid pixels: {n_valid} / {npix}")

# ── Step 7: Per-pixel Lambertian correction ───────────────────────────────────
_lib.sixs_E0.argtypes              = [ctypes.c_float]
_lib.sixs_E0.restype               = ctypes.c_float
_lib.sixs_earth_sun_dist2.argtypes = [ctypes.c_int]
_lib.sixs_earth_sun_dist2.restype  = ctypes.c_double

sl      = lut_slice(lut, aod_val=aod_scene, h2o_val=wvc_mean)
cos_sza = math.cos(math.radians(sza))
d2      = float(_lib.sixs_earth_sun_dist2(ctypes.c_int(doy)))
E0_all  = np.array([float(_lib.sixs_E0(ctypes.c_float(float(w)))) for w in wl],
                    dtype=np.float32)

rho_boa = np.full((n_bands, npix), np.nan, dtype=np.float32)
for b in range(n_bands):
    rho_toa = (bands[b] * math.pi
               / (float(E0_all[b]) * cos_sza * d2)).astype(np.float32)
    rho_raw = invert(rho_toa, sl['R_atm'][b], sl['T_down'][b],
                     sl['T_up'][b], sl['s_alb'][b])
    rho_boa[b, mask == 0] = rho_raw[mask == 0]
print("[7] Per-pixel correction done (Lambertian)")

# ── Step 8: Adjacency effect correction ───────────────────────────────────────
_lib.adjacency_correct_band.argtypes = [
    _FP, ctypes.c_int, ctypes.c_int,
    ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
]
_lib.adjacency_correct_band.restype = None

for b in range(n_bands):
    band_2d = np.ascontiguousarray(rho_boa[b].reshape(nrows, ncols))
    T_scat  = float(1.0 - 0.7 * sl['T_down'][b])
    _lib.adjacency_correct_band(
        band_2d.ctypes.data_as(_FP),
        ctypes.c_int(nrows), ctypes.c_int(ncols),
        ctypes.c_float(1.0), ctypes.c_float(30.0),
        ctypes.c_float(T_scat), ctypes.c_float(float(sl['s_alb'][b])),
        ctypes.c_float(float(wl[b])),
        ctypes.c_float(aod_scene), ctypes.c_float(pressure),
        ctypes.c_float(sza), ctypes.c_float(vza))
    rho_boa[b] = band_2d.ravel()
print("[8] Adjacency correction done")

# ── Step 9: Per-band uncertainty propagation ──────────────────────────────────
_lib.uncertainty_compute_band.argtypes = [
    _FP, _FP, ctypes.c_int,
    ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
    ctypes.POINTER(_Cfg), ctypes.POINTER(_Arr),
    ctypes.c_float, ctypes.c_float, ctypes.c_float,
    _FP,
]
_lib.uncertainty_compute_band.restype = None

sigma_all = np.full((n_bands, npix), np.nan, dtype=np.float32)
for b in range(n_bands):
    sig_b = np.empty(npix, np.float32)
    rad_b = np.ascontiguousarray(bands[b], dtype=np.float32)
    boa_b = np.ascontiguousarray(rho_boa[b], dtype=np.float32)
    _lib.uncertainty_compute_band(
        _fp(rad_b), _fp(boa_b), ctypes.c_int(npix),
        ctypes.c_float(float(E0_all[b])), ctypes.c_float(float(d2)),
        ctypes.c_float(cos_sza),
        ctypes.c_float(float(sl['T_down'][b])), ctypes.c_float(float(sl['T_up'][b])),
        ctypes.c_float(float(sl['s_alb'][b])),  ctypes.c_float(float(sl['R_atm'][b])),
        ctypes.c_float(0.0), ctypes.c_float(0.04),
        ctypes.byref(lut['cfg_c']), ctypes.byref(lut['arr_c']),
        ctypes.c_float(float(wl[b])), ctypes.c_float(aod_scene),
        ctypes.c_float(wvc_mean),
        _fp(sig_b),
    )
    sigma_all[b] = sig_b
print("[9] Uncertainty propagation done")

# ── Step 10: DASF canopy structure retrieval ──────────────────────────────────
# DASF requires at least 3 bands within 710–790 nm (PROSPECT-D table).
# Use a synthetic 4-band NIR plateau at 0.71–0.77 µm to demonstrate.
_lib.retrieve_dasf.argtypes = [_FP, _FP, ctypes.c_int, ctypes.c_int, _FP]
_lib.retrieve_dasf.restype  = None

dasf_wl   = np.array([0.71, 0.73, 0.75, 0.77], dtype=np.float32)
n_dasf    = dasf_wl.size
dasf_refl = np.ascontiguousarray(
    np.tile(np.array([0.40, 0.43, 0.45, 0.44], dtype=np.float32)[:, None],
            (1, npix)))  # [n_dasf, npix]
dasf_out  = np.empty(npix, np.float32)
_lib.retrieve_dasf(
    _fp(dasf_refl.ravel()), _fp(dasf_wl),
    ctypes.c_int(n_dasf), ctypes.c_int(npix),
    _fp(dasf_out))
print(f"[10] DASF: mean = {np.nanmean(dasf_out):.3f}  (canopy structure factor)\n")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"{'Band':<6} {'WL(µm)':<8} {'mean_BOA':<10} {'mean_sigma':<12}")
for b in range(n_bands):
    mb = float(np.nanmean(rho_boa[b]))
    ms = float(np.nanmean(sigma_all[b]))
    print(f"{b:<6} {wl[b]:<8.2f} {mb:<10.4f} {ms:<12.5f}")
