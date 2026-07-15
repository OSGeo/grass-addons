"""Fortran-to-C compatibility tests for lib6sv.

Compiles and runs ``test_6sv_compat.f90``, a small Fortran driver that calls
the 6SV2.1 subroutines CHAND, ODRAYL, VARSOL, SOLIRR, CSALBR, and GAUSS with
fixed inputs and prints ``key=value`` results.  Each result is then compared
against the equivalent C function in ``libsixsv.so`` via ``_support.py``.

Subroutines tested and expected tolerances:

* **CHAND** (Chandrasekhar reflectance): identical float formula → rtol = 1e-5.
* **ODRAYL** (Rayleigh OD): C uses double internally, Fortran single → rtol = 5e-3.
* **VARSOL / earth_sun_dist2**: different 1/d² vs d² conventions with slightly
  different eccentricity / perihelion offset → product ≈ 1 within rtol = 5e-3.
* **SOLIRR / E0**: identical lookup table, C uses linear interp, Fortran uses
  nearest-neighbour; on-grid wavelengths agree within 3 ULP (rtol = 1e-3);
  off-grid 0.5512 µm agrees within 0.1% (rtol = 1e-3).
* **CSALBR** (Rayleigh spherical albedo): identical formula → rtol = 1e-5.
* **GAUSS** (Gauss-Legendre quadrature): both use double internally, output
  cast to float32 → rtol = 1e-5; weights sum to 2.0 within 1e-5.

Run with::

    make test-fortran
    # or directly:
    LIB_SIXSV=./libsixsv.so python3 -m pytest test_fortran_compat.py -v
"""

import os
import subprocess
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import (
    chand as _c_chand,
    csalbr as _c_csalbr,
    earth_sun_dist2,
    gauss as _c_gauss,
    odrayl as _c_odrayl,
    solar_E0,
)

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE       = os.path.dirname(os.path.abspath(__file__))
_SIXSV2     = os.path.join(os.path.expanduser("~"), "dev", "6sV2.1")
_DRIVER_SRC = os.path.join(_HERE, "test_6sv_compat.f90")
_DRIVER_BIN = os.path.join(_HERE, "test_6sv_compat")

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
    """Compile the Fortran driver (skipped if already up-to-date)."""
    _ensure_fortran_objects()
    src_mtime = os.path.getmtime(_DRIVER_SRC)
    if os.path.exists(_DRIVER_BIN) and os.path.getmtime(_DRIVER_BIN) >= src_mtime:
        return
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


# ── Test class ────────────────────────────────────────────────────────────────

class TestFortranCompat(unittest.TestCase):
    """Numerical compatibility between 6SV2.1 Fortran subroutines and the C port."""

    @classmethod
    def setUpClass(cls):
        """Compile the Fortran driver (if needed) and capture reference values."""
        _compile_driver()
        cls.f = _run_driver()

    # ── CHAND — Chandrasekhar Rayleigh reflectance ────────────────────────────

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
        """CHAND: 45° azimuth, thin Rayleigh tau=0.05."""
        self._assert_chand("4", xphi=45.0, xmuv=0.8, xmus=0.7, xtau=0.05)

    # ── ODRAYL — Rayleigh optical depth ──────────────────────────────────────

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

    # ── VARSOL vs sixs_earth_sun_dist2 ───────────────────────────────────────
    # Fortran VARSOL returns dsol = 1/d²; C returns d².  Product ≈ 1.

    def _assert_varsol_product(self, doy_str, doy):
        dsol    = self.f[f"varsol_{doy_str}"]
        d2      = earth_sun_dist2(doy)
        product = dsol * d2
        np.testing.assert_allclose(
            product, 1.0, rtol=5e-3, atol=1e-3,
            err_msg=f"VARSOL×d2 ≈ 1 for DOY={doy}",
        )
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

    def _assert_solirr(self, tag, wl, rtol):
        f_val = self.f[f"solirr_{tag}"]
        c_val = float(solar_E0(np.array([wl], dtype=np.float32))[0])
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
        self._assert_solirr("05512", 0.5512, rtol=1e-3)

    # ── CSALBR — Rayleigh spherical albedo ───────────────────────────────────

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
        np.testing.assert_allclose(sum(w), 2.0, rtol=1e-5)

    def test_gauss_n8_weight_sum(self):
        """Weights of 8-point quadrature on [-1,1] must sum to 2."""
        _, w = _c_gauss(-1.0, 1.0, 8)
        np.testing.assert_allclose(sum(w), 2.0, rtol=1e-5)

    def test_gauss_n4_symmetry(self):
        """GAUSS n=4: nodes and weights are symmetric around 0."""
        x, w = _c_gauss(-1.0, 1.0, 4)
        np.testing.assert_allclose(x[0], -x[3], rtol=1e-6)
        np.testing.assert_allclose(x[1], -x[2], rtol=1e-6)
        np.testing.assert_allclose(w[0],  w[3],  rtol=1e-6)
        np.testing.assert_allclose(w[1],  w[2],  rtol=1e-6)


if __name__ == "__main__":
    unittest.main()
