"""OpenMP parallelism and GPU offload tests for lib6sv.

Three test classes:

``TestOpenMPRuntime``
    Verifies that the OpenMP runtime is accessible and reports sane values for
    ``omp_get_max_threads()`` and ``omp_get_num_devices()``.  The device count
    is informational: 0 means CPU-only, > 0 means at least one GPU is available
    for target offload.

``TestLutParallelConsistency``
    Calls ``atcorr_compute_lut()`` with one thread and with the maximum thread
    count and asserts that both results are numerically identical (rtol = 1e-5).
    The LUT outer loop is parallelised over AOD with a per-thread ``SixsCtx``;
    results must be independent of scheduling.

``TestSpatialFilter``
    Exercises ``spatial_box_filter()`` and ``spatial_gaussian_filter()``, which
    carry ``#pragma omp target teams distribute parallel for collapse(2)``
    directives.  Tests cover:

    - Correctness on uniform arrays (filter must preserve constant fields).
    - Known 3 × 3 box-filter average.
    - NaN-pixel exclusion (NaN neighbours must be skipped, not propagate).
    - Result reproducibility across repeated calls (GPU path must be deterministic).
    - Consistency between single-threaded and multi-threaded execution.

Run with::

    make test-openmp
    # or directly:
    LIB_SIXSV=./libsixsv.so python3 -m pytest test_openmp.py -v
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import (
    LutConfig,
    compute_lut,
    omp_get_max_threads,
    omp_get_num_devices,
    omp_set_num_threads,
    spatial_box_filter,
    spatial_gaussian_filter,
)

# ── Shared LUT config (small grid: fast to compute repeatedly) ────────────────
_WL  = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32)
_AOD = np.array([0.0, 0.1, 0.2, 0.4],     dtype=np.float32)
_H2O = np.array([1.0, 3.0],               dtype=np.float32)

_CFG = LutConfig(
    wl=_WL, aod=_AOD, h2o=_H2O,
    sza=35.0, vza=5.0, raa=90.0,
    altitude_km=1000.0,
    atmo_model=1,
    aerosol_model=1,
    ozone_du=300.0,
)


# ─────────────────────────────────────────────────────────────────────────────
class TestOpenMPRuntime(unittest.TestCase):
    """Verify that the OpenMP runtime is reachable and reports sensible values."""

    def test_omp_runtime_loaded(self):
        """omp_get_max_threads() must return a value (None means runtime missing)."""
        n = omp_get_max_threads()
        self.assertIsNotNone(
            n,
            msg="Could not load OpenMP runtime (libgomp / libomp). "
                "Install the OpenMP runtime library and rebuild.",
        )

    def test_max_threads_positive(self):
        """omp_get_max_threads() must return a positive integer."""
        n = omp_get_max_threads()
        if n is None:
            self.skipTest("OpenMP runtime not available")
        self.assertGreater(n, 0, msg=f"omp_get_max_threads() = {n}")

    def test_num_devices_non_negative(self):
        """omp_get_num_devices() must be ≥ 0 (0 = CPU only, > 0 = GPU present)."""
        nd = omp_get_num_devices()
        self.assertGreaterEqual(nd, 0, msg=f"omp_get_num_devices() = {nd}")

    def test_num_devices_reported(self):
        """Log the GPU device count (informational, never fails)."""
        nd = omp_get_num_devices()
        if nd == 0:
            print(f"\n  [OpenMP target] No GPU devices found — CPU fallback active")
        else:
            print(f"\n  [OpenMP target] {nd} GPU device(s) available for offload")


# ─────────────────────────────────────────────────────────────────────────────
class TestLutParallelConsistency(unittest.TestCase):
    """LUT results must be identical regardless of thread count.

    The outer AOD loop is parallelised with ``omp parallel for schedule(dynamic)``.
    Each thread owns a private ``SixsCtx`` to avoid data races, so results must
    be bit-for-bit equivalent regardless of the number of threads used.
    """

    @classmethod
    def setUpClass(cls):
        max_t = omp_get_max_threads()

        # Serial reference
        omp_set_num_threads(1)
        cls.lut_serial = compute_lut(_CFG)

        # Multi-threaded (use all available cores, or at least 2)
        cls.n_threads = max(2, max_t or 2)
        omp_set_num_threads(cls.n_threads)
        cls.lut_parallel = compute_lut(_CFG)

        # Restore default
        if max_t:
            omp_set_num_threads(max_t)

    def _assert_lut_equal(self, field):
        s = getattr(self.lut_serial,   field)
        p = getattr(self.lut_parallel, field)
        np.testing.assert_allclose(
            p, s, rtol=1e-5, atol=1e-7,
            err_msg=(
                f"{field}: serial (1 thread) vs parallel ({self.n_threads} threads) "
                f"mismatch — max abs diff = {np.abs(p - s).max():.2e}"
            ),
        )

    def test_R_atm_serial_vs_parallel(self):
        """R_atm: 1-thread result matches multi-thread result."""
        self._assert_lut_equal("R_atm")

    def test_T_down_serial_vs_parallel(self):
        """T_down: 1-thread result matches multi-thread result."""
        self._assert_lut_equal("T_down")

    def test_T_up_serial_vs_parallel(self):
        """T_up: 1-thread result matches multi-thread result."""
        self._assert_lut_equal("T_up")

    def test_s_alb_serial_vs_parallel(self):
        """s_alb: 1-thread result matches multi-thread result."""
        self._assert_lut_equal("s_alb")

    def test_lut_reproducible(self):
        """Calling compute_lut twice with the same config gives identical results."""
        lut_a = compute_lut(_CFG)
        lut_b = compute_lut(_CFG)
        np.testing.assert_array_equal(
            lut_a.R_atm, lut_b.R_atm,
            err_msg="compute_lut is not deterministic across repeated calls",
        )


# ─────────────────────────────────────────────────────────────────────────────
class TestSpatialFilter(unittest.TestCase):
    """Correctness tests for spatial_box_filter() and spatial_gaussian_filter().

    Both functions carry ``#pragma omp target teams distribute parallel for``
    directives.  These tests exercise the full GPU-offload path when a device
    is present and fall back to CPU otherwise.
    """

    # ── Box filter ────────────────────────────────────────────────────────────

    def test_box_uniform_preserved(self):
        """Box filter on a uniform array must return the same constant."""
        val  = 3.14159
        data = np.full((20, 20), val, dtype=np.float32)
        out  = spatial_box_filter(data, filter_half=3)
        np.testing.assert_allclose(out, val, atol=1e-5,
                                   err_msg="Box filter changed a uniform field")

    def test_box_zero_half_is_noop(self):
        """filter_half = 0 must return the input unchanged."""
        rng  = np.random.default_rng(42)
        data = rng.uniform(0.0, 1.0, (10, 10)).astype(np.float32)
        out  = spatial_box_filter(data, filter_half=0)
        np.testing.assert_array_equal(out, data)

    def test_box_center_pixel_3x3(self):
        """Center of a 3 × 3 box filter equals the mean of all 9 neighbours."""
        data = np.array([[1, 2, 1],
                         [2, 4, 2],
                         [1, 2, 1]], dtype=np.float32)
        out = spatial_box_filter(data, filter_half=1)
        expected_center = data.mean()          # 16 / 9
        self.assertAlmostEqual(float(out[1, 1]), expected_center, places=4,
                               msg=f"Center pixel {float(out[1,1]):.4f} "
                                   f"≠ mean {expected_center:.4f}")

    def test_box_nan_excluded_from_mean(self):
        """NaN input pixels must be excluded from the neighbourhood average."""
        data = np.ones((7, 7), dtype=np.float32)
        data[3, 3] = np.nan          # single NaN at centre
        out = spatial_box_filter(data, filter_half=1)
        # All non-NaN pixels around centre should average to ~1
        self.assertTrue(np.isfinite(float(out[3, 3])),
                        msg="NaN pixel produced non-finite output")
        self.assertAlmostEqual(float(out[3, 3]), 1.0, places=4,
                               msg="NaN exclusion changed mean for uniform field")

    def test_box_nan_does_not_propagate(self):
        """A single NaN must not spread to its neighbours."""
        data = np.ones((9, 9), dtype=np.float32)
        data[4, 4] = np.nan
        out = spatial_box_filter(data, filter_half=1)
        self.assertEqual(np.isnan(out).sum(), 0,
                         msg="NaN propagated to neighbouring pixels")

    def test_box_output_finite_for_clean_input(self):
        """Box filter on a NaN-free array must produce all finite values."""
        rng  = np.random.default_rng(0)
        data = rng.uniform(0.0, 1.0, (32, 32)).astype(np.float32)
        out  = spatial_box_filter(data, filter_half=4)
        self.assertTrue(np.all(np.isfinite(out)),
                        msg="Non-finite values in box filter output")

    def test_box_reproducible(self):
        """Identical input must produce identical output across multiple calls."""
        rng  = np.random.default_rng(7)
        data = rng.uniform(0.0, 1.0, (64, 64)).astype(np.float32)
        out1 = spatial_box_filter(data, filter_half=2)
        out2 = spatial_box_filter(data, filter_half=2)
        np.testing.assert_array_equal(out1, out2,
                                      err_msg="Box filter is not deterministic")

    def test_box_parallel_matches_serial(self):
        """Box filter result with 1 thread must equal result with N threads."""
        max_t = omp_get_max_threads()
        if not max_t or max_t < 2:
            self.skipTest("Fewer than 2 OpenMP threads available")
        rng  = np.random.default_rng(99)
        data = rng.uniform(0.0, 1.0, (128, 128)).astype(np.float32)

        omp_set_num_threads(1)
        out_serial = spatial_box_filter(data, filter_half=3)

        omp_set_num_threads(max_t)
        out_parallel = spatial_box_filter(data, filter_half=3)

        omp_set_num_threads(max_t)     # restore
        np.testing.assert_allclose(
            out_parallel, out_serial, rtol=1e-5, atol=1e-6,
            err_msg="Box filter: serial vs parallel result mismatch",
        )

    # ── Gaussian filter ───────────────────────────────────────────────────────

    def test_gaussian_uniform_preserved(self):
        """Gaussian filter on a uniform array must return the same constant."""
        val  = 2.71828
        data = np.full((20, 20), val, dtype=np.float32)
        out  = spatial_gaussian_filter(data, sigma=2.0)
        np.testing.assert_allclose(out, val, atol=1e-4,
                                   err_msg="Gaussian filter changed a uniform field")

    def test_gaussian_zero_sigma_is_noop(self):
        """sigma = 0 must return the input unchanged."""
        rng  = np.random.default_rng(13)
        data = rng.uniform(0.0, 1.0, (10, 10)).astype(np.float32)
        out  = spatial_gaussian_filter(data, sigma=0.0)
        np.testing.assert_array_equal(out, data)

    def test_gaussian_reduces_variance(self):
        """Gaussian smoothing must reduce the variance of a noisy field."""
        rng  = np.random.default_rng(3)
        data = rng.standard_normal((64, 64)).astype(np.float32)
        out  = spatial_gaussian_filter(data, sigma=3.0)
        self.assertLess(float(out.var()), float(data.var()),
                        msg="Gaussian filter did not reduce variance")

    def test_gaussian_nan_excluded(self):
        """NaN pixels must not propagate through the Gaussian filter."""
        data = np.ones((11, 11), dtype=np.float32)
        data[5, 5] = np.nan
        out = spatial_gaussian_filter(data, sigma=1.5)
        self.assertTrue(np.isfinite(float(out[5, 5])),
                        msg="NaN was not filled by Gaussian filter")
        self.assertEqual(np.isnan(out).sum(), 0,
                         msg="NaN propagated in Gaussian filter output")

    def test_gaussian_output_finite_for_clean_input(self):
        rng  = np.random.default_rng(1)
        data = rng.uniform(0.0, 1.0, (32, 32)).astype(np.float32)
        out  = spatial_gaussian_filter(data, sigma=2.0)
        self.assertTrue(np.all(np.isfinite(out)))

    def test_gaussian_reproducible(self):
        """Identical input must produce identical output across multiple calls."""
        rng  = np.random.default_rng(5)
        data = rng.uniform(0.0, 1.0, (64, 64)).astype(np.float32)
        out1 = spatial_gaussian_filter(data, sigma=2.0)
        out2 = spatial_gaussian_filter(data, sigma=2.0)
        np.testing.assert_array_equal(out1, out2,
                                      err_msg="Gaussian filter is not deterministic")

    def test_gaussian_parallel_matches_serial(self):
        """Gaussian filter result with 1 thread must equal result with N threads."""
        max_t = omp_get_max_threads()
        if not max_t or max_t < 2:
            self.skipTest("Fewer than 2 OpenMP threads available")
        rng  = np.random.default_rng(17)
        data = rng.uniform(0.0, 1.0, (128, 128)).astype(np.float32)

        omp_set_num_threads(1)
        out_serial = spatial_gaussian_filter(data, sigma=2.5)

        omp_set_num_threads(max_t)
        out_parallel = spatial_gaussian_filter(data, sigma=2.5)

        omp_set_num_threads(max_t)     # restore
        np.testing.assert_allclose(
            out_parallel, out_serial, rtol=1e-5, atol=1e-6,
            err_msg="Gaussian filter: serial vs parallel result mismatch",
        )

    # ── GPU-offload spot check ────────────────────────────────────────────────

    def test_gpu_offload_box_large_array(self):
        """Box filter on a large array gives consistent results (GPU path active
        when a device is present, CPU fallback otherwise)."""
        nd   = omp_get_num_devices()
        size = (512, 512)
        rng  = np.random.default_rng(21)
        data = rng.uniform(0.0, 1.0, size).astype(np.float32)

        out1 = spatial_box_filter(data, filter_half=5)
        out2 = spatial_box_filter(data, filter_half=5)

        self.assertTrue(np.all(np.isfinite(out1)),
                        msg="Non-finite values in large-array box filter output")
        np.testing.assert_array_equal(
            out1, out2,
            err_msg="Box filter (512×512) not deterministic "
                    f"({'GPU' if nd > 0 else 'CPU'} path)",
        )

    def test_gpu_offload_gaussian_large_array(self):
        """Gaussian filter on a large array gives consistent results."""
        nd   = omp_get_num_devices()
        size = (512, 512)
        rng  = np.random.default_rng(23)
        data = rng.uniform(0.0, 1.0, size).astype(np.float32)

        out1 = spatial_gaussian_filter(data, sigma=3.0)
        out2 = spatial_gaussian_filter(data, sigma=3.0)

        self.assertTrue(np.all(np.isfinite(out1)))
        np.testing.assert_array_equal(
            out1, out2,
            err_msg="Gaussian filter (512×512) not deterministic "
                    f"({'GPU' if nd > 0 else 'CPU'} path)",
        )


if __name__ == "__main__":
    unittest.main()
