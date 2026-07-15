"""
04_brdf.py — BRDF surface models, NBAR normalisation, MCD43 disaggregation.

Demonstrates:
  - BRDF evaluation via ctypes (RPV, Ross-Li, Hapke)
  - Hemispherical (white-sky) albedo integration
  - NBAR normalisation from acquisition to nadir geometry
  - MCD43 7-band → hyperspectral kernel weight disaggregation
  - Tikhonov spectral smoothing

Run:
    python3 04_brdf.py
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

def _fp(a):
    return np.ascontiguousarray(a, dtype=np.float32).ctypes.data_as(_FP)

# ── BRDF function signatures ──────────────────────────────────────────────────
# sixs_brdf_eval(brdf_type, params[5], cos_sza, cos_vza, raa_deg) → float
_lib.sixs_brdf_eval.argtypes = [
    ctypes.c_int, _FP,
    ctypes.c_float, ctypes.c_float, ctypes.c_float]
_lib.sixs_brdf_eval.restype  = ctypes.c_float

# sixs_brdf_albe(brdf_type, params[5], cos_sza, n_phi, n_theta) → float
_lib.sixs_brdf_albe.argtypes = [
    ctypes.c_int, _FP,
    ctypes.c_float, ctypes.c_int, ctypes.c_int]
_lib.sixs_brdf_albe.restype  = ctypes.c_float

cos_sza = math.cos(math.radians(35.0))
cos_vza = math.cos(math.radians(8.0))
raa_deg = 90.0

# ── 1. RPV (Rahman-Pinty-Verstraete) model ────────────────────────────────────
# BrdfParams union: 5 floats (rho0, af, k, pad, pad)
rpv_params = (ctypes.c_float * 5)(0.12, -0.15, 0.75, 0., 0.)

rho_rpv  = _lib.sixs_brdf_eval(ctypes.c_int(1), rpv_params,
                                ctypes.c_float(cos_sza), ctypes.c_float(cos_vza),
                                ctypes.c_float(raa_deg))
albe_rpv = _lib.sixs_brdf_albe(ctypes.c_int(1), rpv_params,
                                ctypes.c_float(cos_sza),
                                ctypes.c_int(48), ctypes.c_int(24))
print(f"RPV:       rho = {rho_rpv:.4f}   white-sky albedo = {albe_rpv:.4f}")

# ── 2. Ross-Thick + Li-Sparse (Ross-Li / MCD43-equivalent) ───────────────────
# brdf_type=9 (BRDF_ROSSLIMAIGNAN); params = (f_iso, f_vol, f_geo, 0, 0)
rl_params = (ctypes.c_float * 5)(0.0774, 0.0372, 0.0079, 0., 0.)

rho_rl  = _lib.sixs_brdf_eval(ctypes.c_int(9), rl_params,
                               ctypes.c_float(cos_sza), ctypes.c_float(cos_vza),
                               ctypes.c_float(raa_deg))
albe_rl = _lib.sixs_brdf_albe(ctypes.c_int(9), rl_params,
                               ctypes.c_float(cos_sza),
                               ctypes.c_int(48), ctypes.c_int(24))
print(f"Ross-Li:   rho = {rho_rl:.4f}   white-sky albedo = {albe_rl:.4f}")

# ── 3. Hapke model ────────────────────────────────────────────────────────────
# brdf_type=3 (BRDF_HAPKE); union hapke: (om, af, s0, h, pad)
#   om=single-scatter albedo, af=asymmetry, s0=hotspot amplitude, h=hotspot width
hapke_params = (ctypes.c_float * 5)(0.85, 0.10, 0.06, 0.20, 0.)
rho_hapke = _lib.sixs_brdf_eval(ctypes.c_int(3), hapke_params,
                                 ctypes.c_float(cos_sza), ctypes.c_float(cos_vza),
                                 ctypes.c_float(raa_deg))
print(f"Hapke:     rho = {rho_hapke:.4f}")

# ── 4. NBAR normalisation (view-angle to nadir) ───────────────────────────────
_lib.atcorr_brdf_normalize.argtypes = [ctypes.c_float] * 8
_lib.atcorr_brdf_normalize.restype  = ctypes.c_float

rho_nbar = _lib.atcorr_brdf_normalize(
    ctypes.c_float(0.22),    # rho_boa at acquisition geometry
    ctypes.c_float(0.0774),  # f_iso
    ctypes.c_float(0.0372),  # f_vol
    ctypes.c_float(0.0079),  # f_geo
    ctypes.c_float(35.0),    # sza_obs [deg]
    ctypes.c_float(8.0),     # vza_obs [deg]
    ctypes.c_float(90.0),    # raa_obs [deg]
    ctypes.c_float(35.0),    # sza_nbar [deg] (view normalised to nadir)
)
print(f"\nNBAR:  rho_boa = 0.2200  →  rho_NBAR = {rho_nbar:.4f}  (VZA 8° → nadir)")

# ── 5. MCD43 7-band → hyperspectral disaggregation ───────────────────────────
_lib.mcd43_disaggregate.argtypes = [
    _FP, _FP, _FP,    # fiso_7, fvol_7, fgeo_7
    _FP,              # wl_target [n_wl]
    ctypes.c_int,     # n_wl
    ctypes.c_float,   # alpha (Tikhonov regularisation)
    _FP, _FP, _FP,   # fiso_out, fvol_out, fgeo_out [n_wl]
]
_lib.mcd43_disaggregate.restype = None

fiso_7 = np.array([0.0774, 0.1306, 0.0688, 0.2972, 0.1218, 0.1030, 0.0747],
                   dtype=np.float32)
fvol_7 = np.array([0.0372, 0.0580, 0.0261, 0.1177, 0.0412, 0.0324, 0.0203],
                   dtype=np.float32)
fgeo_7 = np.array([0.0079, 0.0178, 0.0066, 0.0598, 0.0094, 0.0068, 0.0040],
                   dtype=np.float32)

wl_tgt   = np.arange(0.40, 2.51, 0.10, dtype=np.float32)
fiso_hs  = np.empty(wl_tgt.size, np.float32)
fvol_hs  = np.empty(wl_tgt.size, np.float32)
fgeo_hs  = np.empty(wl_tgt.size, np.float32)

_lib.mcd43_disaggregate(
    _fp(fiso_7), _fp(fvol_7), _fp(fgeo_7),
    _fp(wl_tgt), ctypes.c_int(wl_tgt.size), ctypes.c_float(0.10),
    _fp(fiso_hs), _fp(fvol_hs), _fp(fgeo_hs))

print("\nMCD43 disaggregation: f_iso at selected wavelengths:")
for i in range(0, wl_tgt.size, 4):
    print(f"  {wl_tgt[i]:.2f} µm: "
          f"fiso={fiso_hs[i]:.4f}  fvol={fvol_hs[i]:.4f}  fgeo={fgeo_hs[i]:.4f}")

# ── 6. Tikhonov spectral smoothing ───────────────────────────────────────────
_lib.spectral_smooth_tikhonov.argtypes = [_FP, ctypes.c_int, ctypes.c_float]
_lib.spectral_smooth_tikhonov.restype  = None

spectrum = np.array([0.05, 0.07, 0.09, 0.11, 0.12, 0.20, 0.22, 0.23],
                     dtype=np.float32)
smoothed = spectrum.copy()
_lib.spectral_smooth_tikhonov(
    _fp(smoothed), ctypes.c_int(smoothed.size), ctypes.c_float(0.5))
print("\nSmoothed spectrum: " + "  ".join(f"{v:.4f}" for v in smoothed))
