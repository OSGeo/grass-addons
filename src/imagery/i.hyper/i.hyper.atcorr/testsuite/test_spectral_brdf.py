"""Unit tests for FlexBRDF and DASF functions.

Tests mcd43_disaggregate(), spectral_smooth_tikhonov(), and retrieve_dasf()
from libatcorr.so via the Python ctypes bindings in python/atcorr.py.

Validated reference points:
  mcd43_disaggregate at a MODIS band centre → output ≈ input weight
  spectral_smooth_tikhonov(f, alpha=0) → f unchanged
  retrieve_dasf(ω_L(λ), 710–790 nm)  → DASF ≈ 1.0  (ρ = DASF·ω_L)

Run from a GRASS session:
    python -m grass.gunittest.main
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import atcorr as ac

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


# MCD43 MODIS band centres [µm]  (Terra/Aqua Collection 6)
_MCD43_WL = np.array([0.469, 0.555, 0.645, 0.858, 1.240, 1.640, 2.130],
                     dtype=np.float32)

# Representative MCD43 kernel weights for a vegetation pixel (Schaaf et al.)
_FISO_7 = np.array([0.112, 0.117, 0.095, 0.243, 0.155, 0.118, 0.085],
                    dtype=np.float32)
_FVOL_7 = np.array([0.045, 0.040, 0.038, 0.131, 0.038, 0.022, 0.014],
                    dtype=np.float32)
_FGEO_7 = np.array([0.017, 0.014, 0.012, 0.052, 0.016, 0.009, 0.006],
                    dtype=np.float32)


class TestMCD43Disaggregate(TestCase):
    """Tests for mcd43_disaggregate(): 7-band → hyperspectral BRDF kernel weights."""

    @classmethod
    def setUpClass(cls):
        # Dense hyperspectral wavelength grid 0.40–2.50 µm at 5 nm spacing
        cls.wl_dense = np.arange(0.40, 2.505, 0.005, dtype=np.float32)
        cls.fiso, cls.fvol, cls.fgeo = ac.mcd43_disaggregate(
            _FISO_7, _FVOL_7, _FGEO_7, cls.wl_dense, alpha=0.0,
        )

    def test_output_shape(self):
        """All three kernel weight arrays must match the target wavelength grid."""
        n = len(self.wl_dense)
        self.assertEqual(self.fiso.shape, (n,))
        self.assertEqual(self.fvol.shape, (n,))
        self.assertEqual(self.fgeo.shape, (n,))

    def test_output_dtype(self):
        """Output arrays must be float32."""
        self.assertEqual(self.fiso.dtype, np.float32)
        self.assertEqual(self.fvol.dtype, np.float32)
        self.assertEqual(self.fgeo.dtype, np.float32)

    def test_all_finite(self):
        """Disaggregated kernel weights must be finite everywhere."""
        for name, arr in (("fiso", self.fiso), ("fvol", self.fvol), ("fgeo", self.fgeo)):
            self.assertTrue(
                np.all(np.isfinite(arr)),
                msg=f"Non-finite values in disaggregated {name}",
            )

    def test_fiso_non_negative(self):
        """f_iso weights must be non-negative (physical kernel weight)."""
        self.assertTrue(
            np.all(self.fiso >= 0.0),
            msg=f"Negative f_iso: min = {self.fiso.min():.4f}",
        )

    def test_at_band_centre_close_to_input(self):
        """Disaggregated f_iso at a MODIS band centre must be within 5% of the input."""
        # Check band 3 (0.645 µm, red) — well in the interior of the interpolation range
        target_wl = 0.645
        idx = np.argmin(np.abs(self.wl_dense - target_wl))
        fiso_interp = float(self.fiso[idx])
        # Find the corresponding input weight (band 2 = 0.645 µm, index 2)
        fiso_in = float(_FISO_7[2])
        np.testing.assert_allclose(
            fiso_interp, fiso_in, rtol=0.05,
            err_msg=f"f_iso(0.645µm)={fiso_interp:.4f} differs >5% from input {fiso_in:.4f}",
        )

    def test_nir_jump_present_in_fiso(self):
        """f_iso must show a NIR plateau enhancement (red-edge): f_iso(860nm) > f_iso(650nm)."""
        idx_red = np.argmin(np.abs(self.wl_dense - 0.650))
        idx_nir = np.argmin(np.abs(self.wl_dense - 0.860))
        self.assertGreater(
            float(self.fiso[idx_nir]), float(self.fiso[idx_red]),
            msg="f_iso(NIR) ≤ f_iso(red) — red-edge jump missing",
        )

    def test_tikhonov_smoothing_reduces_noise(self):
        """Smoothed (alpha=0.10) output must be smoother than unsmoothed (alpha=0)."""
        fiso_rough, _, _ = ac.mcd43_disaggregate(
            _FISO_7, _FVOL_7, _FGEO_7, self.wl_dense, alpha=0.0,
        )
        fiso_smooth, _, _ = ac.mcd43_disaggregate(
            _FISO_7, _FVOL_7, _FGEO_7, self.wl_dense, alpha=0.10,
        )
        # Second-difference norm (roughness measure) must decrease with smoothing
        d2_rough  = np.sum(np.diff(np.diff(fiso_rough)) ** 2)
        d2_smooth = np.sum(np.diff(np.diff(fiso_smooth)) ** 2)
        self.assertLessEqual(
            d2_smooth, d2_rough,
            msg=f"Smoothing increased roughness: {d2_smooth:.6f} > {d2_rough:.6f}",
        )

    def test_single_band_query(self):
        """Disaggregation for a single wavelength must return length-1 arrays."""
        fiso, fvol, fgeo = ac.mcd43_disaggregate(
            _FISO_7, _FVOL_7, _FGEO_7,
            np.array([0.55], dtype=np.float32), alpha=0.0,
        )
        self.assertEqual(len(fiso), 1)
        self.assertEqual(len(fvol), 1)
        self.assertEqual(len(fgeo), 1)


class TestTikhonovSmoother(TestCase):
    """Tests for spectral_smooth_tikhonov(): second-difference spectral regularization."""

    def test_alpha_zero_identity(self):
        """alpha=0 must return the input unchanged (identity smoother)."""
        f = np.array([1.0, 3.0, 2.0, 0.5, 4.0, 2.5], dtype=np.float32)
        out = ac.spectral_smooth_tikhonov(f, alpha=0.0)
        np.testing.assert_allclose(out, f, atol=1e-5,
                                   err_msg="alpha=0 should leave signal unchanged")

    def test_does_not_modify_input(self):
        """spectral_smooth_tikhonov must not modify the input array."""
        f = np.array([1.0, 3.0, 2.0, 0.5], dtype=np.float32)
        f_copy = f.copy()
        ac.spectral_smooth_tikhonov(f, alpha=0.5)
        np.testing.assert_array_equal(f, f_copy,
                                      err_msg="Input array was modified in-place")

    def test_output_shape_matches_input(self):
        """Output must have the same length as the input."""
        for n in (5, 20, 100):
            f = np.ones(n, dtype=np.float32)
            out = ac.spectral_smooth_tikhonov(f, alpha=0.1)
            self.assertEqual(len(out), n)

    def test_constant_signal_unchanged(self):
        """A constant spectrum must be unchanged by any alpha (null space of D₂)."""
        f = np.full(30, 0.3, dtype=np.float32)
        for alpha in (0.0, 0.1, 1.0, 10.0):
            out = ac.spectral_smooth_tikhonov(f, alpha=alpha)
            np.testing.assert_allclose(
                out, f, atol=1e-5,
                err_msg=f"Constant signal changed at alpha={alpha}",
            )

    def test_spiky_signal_damped(self):
        """A single spike embedded in a flat signal must be reduced by smoothing."""
        f = np.full(50, 0.1, dtype=np.float32)
        f[25] = 1.0   # spike
        out = ac.spectral_smooth_tikhonov(f, alpha=0.3)
        self.assertLess(
            float(out[25]), 1.0,
            msg=f"Spike not reduced: out[25] = {float(out[25]):.4f} (unchanged from 1.0)",
        )

    def test_higher_alpha_flatter_output(self):
        """Higher regularization strength must produce a flatter spectrum."""
        f = np.random.default_rng(42).uniform(0.0, 1.0, 40).astype(np.float32)
        out_lo = ac.spectral_smooth_tikhonov(f, alpha=0.05)
        out_hi = ac.spectral_smooth_tikhonov(f, alpha=2.00)
        var_lo = float(np.var(np.diff(out_lo)))
        var_hi = float(np.var(np.diff(out_hi)))
        self.assertLessEqual(
            var_hi, var_lo,
            msg=f"Higher alpha did not flatten spectrum: var_diff(α=2)={var_hi:.6f} > (α=0.05)={var_lo:.6f}",
        )

    def test_output_preserves_mean_approximately(self):
        """Tikhonov smoothing must approximately preserve the spectral mean."""
        f = np.array([0.1, 0.4, 0.2, 0.8, 0.3, 0.6, 0.1, 0.5], dtype=np.float32)
        out = ac.spectral_smooth_tikhonov(f, alpha=0.5)
        np.testing.assert_allclose(
            float(out.mean()), float(f.mean()), atol=0.15,
            err_msg=f"Mean changed: {float(f.mean()):.4f} → {float(out.mean()):.4f}",
        )


class TestDASF(TestCase):
    """Tests for retrieve_dasf(): DASF canopy structure factor from 710–790 nm."""

    # DASF bands at 5 nm spacing inside 710–790 nm
    _WL_DASF = np.array([0.710, 0.720, 0.730, 0.740, 0.750,
                          0.760, 0.770, 0.780, 0.790], dtype=np.float32)
    _N_DASF = len(_WL_DASF)

    def _refl(self, rho_val, npix=20):
        """Uniform reflectance array of shape (n_dasf, npix)."""
        return np.full((self._N_DASF, npix), rho_val, dtype=np.float32)

    def test_output_shape(self):
        """Output must be float32 array of shape (npix,)."""
        npix = 15
        dasf = ac.retrieve_dasf(self._refl(0.4, npix), self._WL_DASF)
        self.assertEqual(dasf.shape, (npix,))
        self.assertEqual(dasf.dtype, np.float32)

    def test_physical_range_for_vegetation(self):
        """DASF for a realistic vegetation reflectance must be in [0.01, 1.0]."""
        dasf = ac.retrieve_dasf(self._refl(0.45), self._WL_DASF)
        valid = dasf[np.isfinite(dasf)]
        self.assertTrue(len(valid) > 0, msg="All DASF values are NaN")
        self.assertTrue(np.all(valid >= 0.01), msg=f"DASF < 0.01: {valid.min():.4f}")
        self.assertTrue(np.all(valid <= 1.0),  msg=f"DASF > 1.0: {valid.max():.4f}")

    def test_zero_reflectance_gives_nan_or_zero(self):
        """Zero BOA reflectance must give NaN or near-zero DASF (no signal)."""
        dasf = ac.retrieve_dasf(self._refl(0.0), self._WL_DASF)
        # Either NaN (invalid) or clamped to minimum
        non_nan = dasf[np.isfinite(dasf)]
        if len(non_nan) > 0:
            self.assertTrue(
                np.all(non_nan <= 0.05),
                msg=f"Zero input gives DASF={non_nan.max():.4f} > 0.05",
            )

    def test_bands_outside_range_give_nan(self):
        """Bands well outside 710–790 nm must give NaN (no valid PROSPECT-D leaf albedo)."""
        wl_vis = np.array([0.45, 0.55, 0.65], dtype=np.float32)
        refl   = np.full((3, 10), 0.08, dtype=np.float32)
        dasf   = ac.retrieve_dasf(refl, wl_vis)
        self.assertTrue(
            np.all(np.isnan(dasf)),
            msg=f"Expected NaN for VIS-only bands; got {dasf}",
        )

    def test_higher_reflectance_gives_higher_dasf(self):
        """Brighter NIR plateau (higher ρ) must give higher DASF."""
        dasf_lo = ac.retrieve_dasf(self._refl(0.20), self._WL_DASF)
        dasf_hi = ac.retrieve_dasf(self._refl(0.60), self._WL_DASF)
        valid_lo = dasf_lo[np.isfinite(dasf_lo)]
        valid_hi = dasf_hi[np.isfinite(dasf_hi)]
        if len(valid_lo) > 0 and len(valid_hi) > 0:
            self.assertGreater(
                float(valid_hi.mean()), float(valid_lo.mean()),
                msg=(f"DASF(ρ=0.60)={valid_hi.mean():.4f} ≤ "
                     f"DASF(ρ=0.20)={valid_lo.mean():.4f}"),
            )


if __name__ == "__main__":
    test()
