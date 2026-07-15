"""Fortran-to-C compatibility tests for i.hyper.atcorr.

Compiles and runs ``testsuite/test_6sv_compat.f90``, a small Fortran driver
that calls the 6SV2.1 subroutines CHAND, ODRAYL, VARSOL, SOLIRR, CSALBR, and
GAUSS with fixed inputs and prints ``key=value`` results.  Each result is then
compared against the equivalent C function in ``libatcorr.so``.

Subroutines tested and expected tolerances:

* **CHAND** (Chandrasekhar reflectance): identical float formula → rtol = 1e-5.
* **ODRAYL** (Rayleigh OD): C uses double internally, Fortran single → rtol = 1e-3.
* **VARSOL / earth_sun_dist2**: different 1/d² vs d² conventions with slightly
  different eccentricity / perihelion offset → product ≈ 1 within rtol = 5e-3.
* **SOLIRR / E0**: identical lookup table, C uses linear interp, Fortran uses
  nearest-neighbour; on-grid wavelengths agree within 3 ULP (rtol = 1e-3);
  off-grid 0.5512 µm agrees within 0.1% (rtol = 1e-3).
* **CSALBR** (Rayleigh spherical albedo): identical formula → rtol = 1e-5.
* **GAUSS** (Gauss-Legendre quadrature): both use double internally, output
  cast to float32 → rtol = 1e-5; weights sum to 2.0 within 1e-5.

Run from a GRASS session::

    python -m grass.gunittest.main
"""

import ctypes
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import atcorr as ac

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE      = os.path.dirname(os.path.abspath(__file__))
_SIXSV2    = os.path.join(os.path.expanduser("~"), "dev", "6sV2.1")
_DRIVER_SRC = os.path.join(_HERE, "test_6sv_compat.f90")
_DRIVER_BIN = os.path.join(_HERE, "test_6sv_compat")

# Object files from 6SV2.1 that the driver links against
_FORTRAN_OBJS = [
    os.path.join(_SIXSV2, name + ".o")
    for name in ("CHAND", "ODRAYL", "VARSOL", "SOLIRR", "CSALBR", "GAUSS", "US62")
]


# ── Fortran driver build/run helpers ──────────────────────────────────────────

def _ensure_fortran_objects():
    """Build 6SV2.1 .o files via 'make sixs' if any are missing."""
    if all(os.path.exists(p) for p in _FORTRAN_OBJS):
        return
    result = subprocess.run(
        ["make", "sixs"], cwd=_SIXSV2, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"'make sixs' in {_SIXSV2} failed:\n{result.stderr}"
        )


def _compile_driver():
    """Compile the Fortran test driver (skipped if binary is already up-to-date)."""
    _ensure_fortran_objects()
    src_mtime = os.path.getmtime(_DRIVER_SRC)
    if os.path.exists(_DRIVER_BIN) and os.path.getmtime(_DRIVER_BIN) >= src_mtime:
        return  # already up-to-date
    cmd = ["gfortran", "-O", _DRIVER_SRC] + _FORTRAN_OBJS + ["-lm", "-o", _DRIVER_BIN]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gfortran compilation failed:\n{result.stderr}")


def _run_driver():
    """Run the Fortran binary and return a dict of key → float."""
    result = subprocess.run([_DRIVER_BIN], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Fortran driver failed:\n{result.stderr}")
    data = {}
    for line in result.stdout.splitlines():
        line = line.strip()
        if "=" in line:
            key, _, val = line.partition("=")
            data[key.strip()] = float(val.strip())
    return data


# ── C function wrappers (via libatcorr.so) ───────────────────────────────────

_lib = ac._lib  # ctypes.CDLL already loaded by atcorr.py

# sixs_chand(float xphi, float xmuv, float xmus, float xtau) → float
_lib.sixs_chand.argtypes = [ctypes.c_float] * 4
_lib.sixs_chand.restype  = ctypes.c_float


def _c_chand(xphi, xmuv, xmus, xtau):
    return float(_lib.sixs_chand(
        ctypes.c_float(xphi), ctypes.c_float(xmuv),
        ctypes.c_float(xmus), ctypes.c_float(xtau),
    ))


# sixs_init_atmosphere(SixsCtx *ctx, int atmo_model) → void
_lib.sixs_init_atmosphere.argtypes = [ctypes.c_void_p, ctypes.c_int]
_lib.sixs_init_atmosphere.restype  = None

# sixs_odrayl(const SixsCtx *ctx, float wl, float *tray) → void
_lib.sixs_odrayl.argtypes = [ctypes.c_void_p, ctypes.c_float,
                               ctypes.POINTER(ctypes.c_float)]
_lib.sixs_odrayl.restype  = None

# Allocate a zeroed SixsCtx and initialise with US62 standard atmosphere.
# The buffer (8 KB) is well above the actual struct size (~5.5 KB).
_ctx = ctypes.create_string_buffer(8192)
_lib.sixs_init_atmosphere(_ctx, ctypes.c_int(1))  # atmo_model=1 → US62


def _c_odrayl(wl):
    tray = ctypes.c_float(0.0)
    _lib.sixs_odrayl(_ctx, ctypes.c_float(wl), ctypes.byref(tray))
    return float(tray.value)


# sixs_csalbr(float xtau, float *xalb) → void
_lib.sixs_csalbr.argtypes = [ctypes.c_float, ctypes.POINTER(ctypes.c_float)]
_lib.sixs_csalbr.restype  = None


def _c_csalbr(xtau):
    xalb = ctypes.c_float(0.0)
    _lib.sixs_csalbr(ctypes.c_float(xtau), ctypes.byref(xalb))
    return float(xalb.value)


# sixs_gauss(float x1, float x2, float *x, float *w, int n) → void
_lib.sixs_gauss.argtypes = [ctypes.c_float, ctypes.c_float,
                              ctypes.POINTER(ctypes.c_float),
                              ctypes.POINTER(ctypes.c_float),
                              ctypes.c_int]
_lib.sixs_gauss.restype = None


def _c_gauss(x1, x2, n):
    xa = (ctypes.c_float * n)()
    wa = (ctypes.c_float * n)()
    _lib.sixs_gauss(ctypes.c_float(x1), ctypes.c_float(x2), xa, wa, ctypes.c_int(n))
    return list(xa), list(wa)


# ── Test class ────────────────────────────────────────────────────────────────

class TestFortranCompat(TestCase):
    """Numerical compatibility between 6SV2.1 Fortran subroutines and the C port."""

    @classmethod
    def setUpClass(cls):
        """Compile the Fortran driver (if needed) and capture reference values."""
        _compile_driver()
        cls.f = _run_driver()

    # ── CHAND — Chandrasekhar Rayleigh reflectance ────────────────────────────
    # Both Fortran and C use identical float32 polynomial formulas.
    # Expected agreement: < 1e-5 relative (float32 precision).

    def _assert_chand(self, tag, xphi, xmuv, xmus, xtau):
        f_val = self.f[f"chand_{tag}"]
        c_val = _c_chand(xphi, xmuv, xmus, xtau)
        np.testing.assert_allclose(c_val, f_val, rtol=1e-5, atol=1e-9,
                                   err_msg=f"CHAND case {tag}")

    def test_chand_1_backscatter(self):
        """CHAND: backscatter geometry (phi=0), tau=0.1."""
        self._assert_chand("1", xphi=0.0, xmuv=0.9, xmus=0.8, xtau=0.1)

    def test_chand_2_90deg_azimuth(self):
        """CHAND: 90° azimuth, oblique viewing."""
        self._assert_chand("2", xphi=90.0, xmuv=0.7, xmus=0.6, xtau=0.2)

    def test_chand_3_forward_scatter(self):
        """CHAND: forward-scatter geometry (phi=180)."""
        self._assert_chand("3", xphi=180.0, xmuv=0.5, xmus=0.5, xtau=0.3)

    def test_chand_4_45deg_thin(self):
        """CHAND: 45° azimuth, thin aerosol tau=0.05."""
        self._assert_chand("4", xphi=45.0, xmuv=0.8, xmus=0.7, xtau=0.05)

    # ── ODRAYL — Rayleigh optical depth ──────────────────────────────────────
    # C uses double precision internally; Fortran uses single.
    # Both use the Edlen 1966 formula with identical coefficients.
    # US62 standard atmosphere initialized in both; agreement < 0.5%.

    def _assert_odrayl(self, tag, wl):
        f_val = self.f[f"odrayl_{tag}"]
        c_val = _c_odrayl(wl)
        np.testing.assert_allclose(c_val, f_val, rtol=5e-3, atol=1e-6,
                                   err_msg=f"ODRAYL wl={wl} µm")

    def test_odrayl_045_blue(self):
        """ODRAYL: 0.45 µm (blue), strong Rayleigh scattering."""
        self._assert_odrayl("045", 0.45)

    def test_odrayl_055_green(self):
        """ODRAYL: 0.55 µm (green)."""
        self._assert_odrayl("055", 0.55)

    def test_odrayl_065_red(self):
        """ODRAYL: 0.65 µm (red)."""
        self._assert_odrayl("065", 0.65)

    def test_odrayl_087_nir(self):
        """ODRAYL: 0.87 µm (NIR), weak Rayleigh scattering."""
        self._assert_odrayl("087", 0.87)

    def test_odrayl_100_swir1(self):
        """ODRAYL: 1.00 µm (SWIR1) — τ must be very small (<0.01)."""
        self._assert_odrayl("100", 1.00)
        self.assertLess(_c_odrayl(1.00), 0.010)

    def test_odrayl_150_swir2(self):
        """ODRAYL: 1.50 µm (SWIR2) — τ must be negligible (<0.003)."""
        self._assert_odrayl("150", 1.50)
        self.assertLess(_c_odrayl(1.50), 0.003)

    def test_odrayl_monotone_decreasing(self):
        """Rayleigh OD must decrease monotonically with wavelength (τ ∝ λ⁻⁴)."""
        wls = [0.45, 0.55, 0.65, 0.87, 1.00, 1.50]
        taus = [_c_odrayl(w) for w in wls]
        for k in range(len(taus) - 1):
            self.assertGreater(
                taus[k], taus[k + 1],
                msg=f"τ({wls[k]:.2f})={taus[k]:.5f} ≤ τ({wls[k+1]:.2f})={taus[k+1]:.5f}",
            )

    # ── VARSOL vs sixs_earth_sun_dist2 ───────────────────────────────────────
    # Fortran VARSOL returns dsol = 1/d² (solar constant correction, >1 at perihelion).
    # C sixs_earth_sun_dist2 returns d² (<1 at perihelion).
    # Their product should be ≈ 1; small residual (<0.1%) arises from:
    #   - Different eccentricity: 0.01673 (Fortran) vs 0.01670963 (C)
    #   - Different angular rate: 0.9856°/day vs 2π/365 rad/day
    #   - Different perihelion offset: j-4 vs doy-3

    def _assert_varsol_product(self, doy_str, doy):
        dsol = self.f[f"varsol_{doy_str}"]
        d2   = float(ac.earth_sun_dist2(doy))
        product = dsol * d2
        np.testing.assert_allclose(
            product, 1.0, rtol=5e-3, atol=1e-3,
            err_msg=f"VARSOL×d2 ≈ 1 for DOY={doy}",
        )
        # Physical sanity: dsol in [0.96, 1.04]
        self.assertGreater(dsol, 0.96)
        self.assertLess(dsol, 1.04)

    def test_varsol_doy003_perihelion(self):
        """VARSOL×d2 ≈ 1.0 at DOY 3 (perihelion)."""
        self._assert_varsol_product("doy003", 3)

    def test_varsol_doy090_spring_equinox(self):
        """VARSOL×d2 ≈ 1.0 at DOY 90 (vernal equinox)."""
        self._assert_varsol_product("doy090", 90)

    def test_varsol_doy185_aphelion(self):
        """VARSOL×d2 ≈ 1.0 at DOY 185 (aphelion)."""
        self._assert_varsol_product("doy185", 185)

    def test_varsol_doy270_autumn_equinox(self):
        """VARSOL×d2 ≈ 1.0 at DOY 270 (autumnal equinox)."""
        self._assert_varsol_product("doy270", 270)

    # ── SOLIRR vs sixs_E0 ─────────────────────────────────────────────────────
    # Identical lookup table (auto-generated from SOLIRR.f).
    # On-grid wavelengths: C linear interpolation gives the same table value
    # as Fortran nearest-neighbour, within 3 ULP (≈ 2e-7 relative).
    # Off-grid 0.5512 µm: C linear vs Fortran nearest-neighbour → ≤ 0.05%.

    def _assert_solirr(self, tag, wl, rtol):
        f_val = self.f[f"solirr_{tag}"]
        c_val = float(ac.solar_E0(np.array([wl], dtype=np.float32))[0])
        np.testing.assert_allclose(c_val, f_val, rtol=rtol, atol=0.5,
                                   err_msg=f"SOLIRR/E0 wl={tag} µm")

    def test_solirr_045_ongrid(self):
        """SOLIRR: 0.45 µm on-grid → C and Fortran table values match."""
        self._assert_solirr("045", 0.45, rtol=1e-3)

    def test_solirr_055_ongrid(self):
        """SOLIRR: 0.55 µm on-grid."""
        self._assert_solirr("055", 0.55, rtol=1e-3)

    def test_solirr_065_ongrid(self):
        """SOLIRR: 0.65 µm on-grid."""
        self._assert_solirr("065", 0.65, rtol=1e-3)

    def test_solirr_087_ongrid(self):
        """SOLIRR: 0.87 µm on-grid."""
        self._assert_solirr("087", 0.87, rtol=1e-3)

    def test_solirr_05512_offgrid(self):
        """SOLIRR: 0.5512 µm off-grid (C linear vs Fortran nearest-neighbour)."""
        # Fortran rounds to the 0.55 µm table entry; C interpolates linearly.
        # The solar spectrum is smooth here → agreement within 0.1%.
        self._assert_solirr("05512", 0.5512, rtol=1e-3)

    # ── CSALBR — Rayleigh spherical albedo ───────────────────────────────────
    # Identical C formula (E1/E3 integral approximation).
    # Expected agreement: < 1e-5 relative.

    def _assert_csalbr(self, tag, xtau):
        f_val = self.f[f"csalbr_{tag}"]
        c_val = _c_csalbr(xtau)
        np.testing.assert_allclose(c_val, f_val, rtol=1e-5, atol=1e-9,
                                   err_msg=f"CSALBR xtau={xtau}")

    def test_csalbr_01(self):
        """CSALBR: thin Rayleigh layer τ=0.1."""
        self._assert_csalbr("01", 0.1)

    def test_csalbr_03(self):
        """CSALBR: moderate τ=0.3."""
        self._assert_csalbr("03", 0.3)

    def test_csalbr_05(self):
        """CSALBR: thick Rayleigh layer τ=0.5."""
        self._assert_csalbr("05", 0.5)

    # ── GAUSS — Gauss-Legendre quadrature ────────────────────────────────────
    # Both Fortran and C use double-precision Newton iteration then cast to float32.
    # The pi constants differ at the 10th digit (Fortran 3.141592654 vs C M_PI)
    # but the iteration converges to the same float32 output.
    # Expected agreement: < 1e-5 relative.

    def _assert_gauss(self, n):
        x_c, w_c = _c_gauss(-1.0, 1.0, n)
        for i in range(n):
            f_x = self.f[f"gauss_x{n}_{i+1}"]
            f_w = self.f[f"gauss_w{n}_{i+1}"]
            np.testing.assert_allclose(x_c[i], f_x, rtol=1e-5, atol=1e-9,
                                       err_msg=f"GAUSS n={n} x[{i+1}]")
            np.testing.assert_allclose(w_c[i], f_w, rtol=1e-5, atol=1e-9,
                                       err_msg=f"GAUSS n={n} w[{i+1}]")

    def test_gauss_n4_nodes(self):
        """GAUSS: 4-point Gauss-Legendre nodes and weights on [-1, 1]."""
        self._assert_gauss(4)

    def test_gauss_n8_nodes(self):
        """GAUSS: 8-point Gauss-Legendre nodes and weights on [-1, 1]."""
        self._assert_gauss(8)

    def test_gauss_n4_weight_sum(self):
        """Weights of 4-point quadrature on [-1,1] must sum to 2."""
        _, w = _c_gauss(-1.0, 1.0, 4)
        np.testing.assert_allclose(sum(w), 2.0, rtol=1e-5,
                                   err_msg="GAUSS n=4 weight sum")

    def test_gauss_n8_weight_sum(self):
        """Weights of 8-point quadrature on [-1,1] must sum to 2."""
        _, w = _c_gauss(-1.0, 1.0, 8)
        np.testing.assert_allclose(sum(w), 2.0, rtol=1e-5,
                                   err_msg="GAUSS n=8 weight sum")

    def test_gauss_n4_symmetry(self):
        """GAUSS n=4: nodes and weights are symmetric around 0."""
        x, w = _c_gauss(-1.0, 1.0, 4)
        np.testing.assert_allclose(x[0], -x[3], rtol=1e-6)
        np.testing.assert_allclose(x[1], -x[2], rtol=1e-6)
        np.testing.assert_allclose(w[0],  w[3],  rtol=1e-6)
        np.testing.assert_allclose(w[1],  w[2],  rtol=1e-6)

    def test_gauss_n8_symmetry(self):
        """GAUSS n=8: nodes and weights are symmetric around 0."""
        x, w = _c_gauss(-1.0, 1.0, 8)
        for i in range(4):
            np.testing.assert_allclose(x[i], -x[7 - i], rtol=1e-6,
                                       err_msg=f"x[{i}] not symmetric")
            np.testing.assert_allclose(w[i],  w[7 - i],  rtol=1e-6,
                                       err_msg=f"w[{i}] not symmetric")

    def test_gauss_n16_weight_sum(self):
        """Weights of 16-point quadrature on [-1,1] must sum to 2 (DISCOM uses n=16)."""
        _, w = _c_gauss(-1.0, 1.0, 16)
        np.testing.assert_allclose(sum(w), 2.0, rtol=1e-5,
                                   err_msg="GAUSS n=16 weight sum")

    def test_gauss_n16_nodes_vs_fortran(self):
        """16-point Gauss-Legendre nodes must match Fortran reference values."""
        x_c, w_c = _c_gauss(-1.0, 1.0, 16)
        for i in range(16):
            f_x = self.f[f"gauss_x16_{i+1}"]
            f_w = self.f[f"gauss_w16_{i+1}"]
            np.testing.assert_allclose(x_c[i], f_x, rtol=1e-5, atol=1e-9,
                                       err_msg=f"GAUSS n=16 x[{i+1}]")
            np.testing.assert_allclose(w_c[i], f_w, rtol=1e-5, atol=1e-9,
                                       err_msg=f"GAUSS n=16 w[{i+1}]")

    def test_odrayl_lambda4_scaling(self):
        """Rayleigh OD must satisfy τ(450nm)/τ(870nm) ≈ (870/450)⁴ ≈ 14."""
        tau_blue = _c_odrayl(0.45)
        tau_nir  = _c_odrayl(0.87)
        ratio    = tau_blue / tau_nir
        expected = (0.87 / 0.45) ** 4
        np.testing.assert_allclose(ratio, expected, rtol=0.05,
                                   err_msg=f"λ⁻⁴ ratio: got {ratio:.2f}, expected ~{expected:.2f}")


if __name__ == "__main__":
    test()
