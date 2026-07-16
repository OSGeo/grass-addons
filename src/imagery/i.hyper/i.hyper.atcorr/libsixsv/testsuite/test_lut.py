"""Unit tests for LUT computation, slicing, and reflectance inversion.

Tests compute_lut(), lut_slice(), and invert() from libsixsv.so via the
ctypes wrappers in _support.py.

Run with::

    make test-fortran
    # or directly:
    LIB_SIXSV=./libsixsv.so python3 -m pytest test_lut.py -v
"""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import LutConfig, compute_lut, invert, lut_slice

# ── Shared small LUT grid used by most tests ──────────────────────────────────
_WL  = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32)
_AOD = np.array([0.0, 0.2, 0.6],          dtype=np.float32)
_H2O = np.array([1.0, 3.0],               dtype=np.float32)

_BASE_CFG = dict(
    wl=_WL, aod=_AOD, h2o=_H2O,
    sza=35.0, vza=5.0, raa=90.0,
    altitude_km=1000.0,
    atmo_model=1,     # US Standard 1962
    aerosol_model=1,  # continental
    ozone_du=300.0,
)


def _make_lut(**kwargs):
    cfg = LutConfig(**{**_BASE_CFG, **kwargs})
    return cfg, compute_lut(cfg)


class TestLutShape(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_shape(self):
        self.assertEqual(self.lut.R_atm.shape,
                         (len(_AOD), len(_H2O), len(_WL)))

    def test_T_down_shape(self):
        self.assertEqual(self.lut.T_down.shape,
                         (len(_AOD), len(_H2O), len(_WL)))

    def test_T_up_shape(self):
        self.assertEqual(self.lut.T_up.shape,
                         (len(_AOD), len(_H2O), len(_WL)))

    def test_s_alb_shape(self):
        self.assertEqual(self.lut.s_alb.shape,
                         (len(_AOD), len(_H2O), len(_WL)))


class TestLutPhysicalBounds(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_non_negative(self):
        self.assertTrue(np.all(self.lut.R_atm >= 0.0),
                        msg=f"Negative R_atm: min = {self.lut.R_atm.min():.4f}")

    def test_R_atm_less_than_one(self):
        self.assertTrue(np.all(self.lut.R_atm < 1.0),
                        msg=f"R_atm ≥ 1: max = {self.lut.R_atm.max():.4f}")

    def test_T_down_positive(self):
        self.assertTrue(np.all(self.lut.T_down > 0.0))

    def test_T_down_le_one(self):
        self.assertTrue(np.all(self.lut.T_down <= 1.0 + 1e-5),
                        msg=f"T_down > 1: max = {self.lut.T_down.max():.4f}")

    def test_T_up_positive(self):
        self.assertTrue(np.all(self.lut.T_up > 0.0))

    def test_T_up_le_one(self):
        self.assertTrue(np.all(self.lut.T_up <= 1.0 + 1e-5),
                        msg=f"T_up > 1: max = {self.lut.T_up.max():.4f}")

    def test_s_alb_non_negative(self):
        self.assertTrue(np.all(self.lut.s_alb >= 0.0))

    def test_s_alb_less_than_one(self):
        self.assertTrue(np.all(self.lut.s_alb < 1.0),
                        msg=f"s_alb ≥ 1: max = {self.lut.s_alb.max():.4f}")

    def test_all_finite(self):
        for name in ("R_atm", "T_down", "T_up", "s_alb"):
            arr = getattr(self.lut, name)
            self.assertTrue(np.all(np.isfinite(arr)),
                            msg=f"Non-finite values in {name}")


class TestLutMonotonicity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_non_decreasing_with_aod(self):
        """R_atm must be non-decreasing as AOD increases (at each H2O/WL)."""
        for i_h in range(len(_H2O)):
            for i_w, wl in enumerate(_WL):
                r = self.lut.R_atm[:, i_h, i_w]
                for k in range(len(_AOD) - 1):
                    self.assertGreaterEqual(
                        r[k + 1], r[k] - 1e-4,
                        msg=(f"R_atm decreased with AOD at "
                             f"h2o={_H2O[i_h]:.1f} wl={wl:.2f}: "
                             f"{r[k]:.4f} → {r[k+1]:.4f}"),
                    )

    def test_T_total_non_increasing_with_aod(self):
        """T_down × T_up must be non-increasing as AOD increases."""
        for i_h in range(len(_H2O)):
            for i_w, wl in enumerate(_WL):
                T = self.lut.T_down[:, i_h, i_w] * self.lut.T_up[:, i_h, i_w]
                for k in range(len(_AOD) - 1):
                    self.assertLessEqual(
                        T[k + 1], T[k] + 1e-4,
                        msg=(f"T_total increased with AOD at "
                             f"h2o={_H2O[i_h]:.1f} wl={wl:.2f}: "
                             f"{T[k]:.4f} → {T[k+1]:.4f}"),
                    )


class TestLutAerosolModels(unittest.TestCase):

    def test_rayleigh_only_R_atm_at_blue(self):
        """Rayleigh-only (aerosol=0) R_atm at 450 nm must be in [0.05, 0.20]."""
        _, lut = _make_lut(aerosol_model=0)
        R_blue = float(lut.R_atm[0, 0, 0])
        self.assertGreater(R_blue, 0.05,
                           msg=f"R_atm(Rayleigh, 450nm) too low: {R_blue:.4f}")
        self.assertLess(R_blue, 0.20,
                        msg=f"R_atm(Rayleigh, 450nm) too high: {R_blue:.4f}")

    def test_continental_maritime_differ(self):
        """Continental and maritime aerosol models must give different R_atm."""
        _, lut_c = _make_lut(aerosol_model=1)
        _, lut_m = _make_lut(aerosol_model=2)
        diff = np.abs(lut_c.R_atm[-1] - lut_m.R_atm[-1]).max()
        self.assertGreater(diff, 1e-4,
                           msg="Continental and maritime R_atm identical")

    def test_no_aerosol_lower_R_atm_at_blue(self):
        """Rayleigh-only R_atm ≤ continental at maximum AOD, 450 nm."""
        _, lut_c = _make_lut(aerosol_model=1)
        _, lut_n = _make_lut(aerosol_model=0)
        self.assertLessEqual(float(lut_n.R_atm[-1, 0, 0]),
                             float(lut_c.R_atm[-1, 0, 0]) + 1e-4)


class TestLutSlice(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_slice_shape_is_1d(self):
        sl = lut_slice(self.cfg, self.lut, float(_AOD[1]), float(_H2O[0]))
        for name in ("R_atm", "T_down", "T_up", "s_alb"):
            arr = getattr(sl, name)
            self.assertEqual(len(arr), len(_WL))

    def test_slice_at_first_grid_node_matches_lut(self):
        sl = lut_slice(self.cfg, self.lut, float(_AOD[0]), float(_H2O[0]))
        np.testing.assert_allclose(sl.R_atm, self.lut.R_atm[0, 0, :], atol=1e-4)

    def test_slice_at_last_grid_node_matches_lut(self):
        sl = lut_slice(self.cfg, self.lut, float(_AOD[-1]), float(_H2O[-1]))
        np.testing.assert_allclose(sl.R_atm, self.lut.R_atm[-1, -1, :], atol=1e-4)

    def test_slice_between_nodes_physical(self):
        aod_mid = float((_AOD[0] + _AOD[1]) / 2)
        h2o_mid = float((_H2O[0] + _H2O[1]) / 2)
        sl = lut_slice(self.cfg, self.lut, aod_mid, h2o_mid)
        self.assertTrue(np.all(sl.R_atm >= 0.0))
        self.assertTrue(np.all(sl.R_atm < 1.0))
        self.assertTrue(np.all(sl.T_down > 0.0))
        self.assertTrue(np.all(sl.s_alb >= 0.0))

    def test_slice_R_atm_increases_with_aod(self):
        r_vals = [
            float(lut_slice(self.cfg, self.lut, float(a), float(_H2O[0])).R_atm[0])
            for a in _AOD
        ]
        for k in range(len(r_vals) - 1):
            self.assertGreaterEqual(
                r_vals[k + 1], r_vals[k] - 1e-4,
                msg=f"R_atm decreased: {r_vals[k]:.4f} → {r_vals[k+1]:.4f}",
            )


class TestInversion(unittest.TestCase):

    def test_no_atmosphere_identity(self):
        """With R_atm=0, T=1, s_alb=0: rho_boa must equal rho_toa."""
        rho_toa = np.array([0.1, 0.2, 0.3, 0.5], dtype=np.float32)
        rho_boa = invert(rho_toa, 0.0, 1.0, 1.0, 0.0)
        np.testing.assert_allclose(rho_boa, rho_toa, atol=1e-5)

    def test_atmosphere_reduces_bright_surface(self):
        # T_down=0.95, T_up=0.95: T_total=0.9025 > (1 - R_atm/rho_toa)=0.80
        # so BOA correction brings rho_boa below rho_toa=0.5
        rho_boa = invert(0.5, 0.10, 0.95, 0.95, 0.05)
        self.assertLess(float(rho_boa), 0.5)

    def test_bright_surface_stays_bright(self):
        rho_boa = invert(0.80, 0.08, 0.85, 0.90, 0.05)
        self.assertGreater(float(rho_boa), 0.5)

    def test_dark_surface_stays_dark(self):
        rho_boa = invert(0.05, 0.03, 0.92, 0.95, 0.02)
        self.assertLess(float(rho_boa), 0.15)

    def test_full_pipeline_physical_range(self):
        """Full pipeline: compute LUT → slice → invert; rho_boa ∈ [-0.05, 1]."""
        cfg, lut_ = _make_lut()
        sl = lut_slice(cfg, lut_, 0.2, 2.0)
        rho_toa = np.array([0.12, 0.10, 0.09, 0.08], dtype=np.float32)
        rho_boa = invert(rho_toa, sl.R_atm, sl.T_down, sl.T_up, sl.s_alb)
        self.assertTrue(np.all(np.isfinite(rho_boa)))
        self.assertTrue(np.all(rho_boa >= -0.05))
        self.assertTrue(np.all(rho_boa < 1.0))

    def test_vectorised_over_pixels(self):
        rho_toa = np.random.uniform(0.05, 0.50, 100).astype(np.float32)
        rho_boa = invert(rho_toa, 0.05, 0.90, 0.92, 0.08)
        self.assertEqual(len(rho_boa), 100)
        self.assertTrue(np.all(np.isfinite(rho_boa)))


class TestPolarization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cfg_s, cls.lut_s = _make_lut(enable_polar=0)
        cls.cfg_p, cls.lut_p = _make_lut(enable_polar=1)

    def test_scalar_QU_are_none(self):
        self.assertIsNone(self.lut_s.R_atmQ)
        self.assertIsNone(self.lut_s.R_atmU)

    def test_polar_QU_not_none(self):
        self.assertIsNotNone(self.lut_p.R_atmQ)
        self.assertIsNotNone(self.lut_p.R_atmU)

    def test_polar_QU_shape_matches_R_atm(self):
        expected = self.lut_p.R_atm.shape
        self.assertEqual(self.lut_p.R_atmQ.shape, expected)
        self.assertEqual(self.lut_p.R_atmU.shape, expected)

    def test_polar_R_atm_geq_scalar_at_blue(self):
        """Vector R_atm ≥ scalar R_atm at 450 nm (Rayleigh polarization raises I)."""
        R_vec = self.lut_p.R_atm[:, :, 0]
        R_sca = self.lut_s.R_atm[:, :, 0]
        self.assertTrue(
            np.all(R_vec >= R_sca - 1e-4),
            msg=f"R_atm(polar) < R_atm(scalar) at 450 nm; "
                f"max diff = {(R_sca - R_vec).max():.4f}",
        )

    def test_polar_Q_positive_at_blue(self):
        Q_blue = float(self.lut_p.R_atmQ[0, 0, 0])
        self.assertGreater(Q_blue, 0.0,
                           msg=f"R_atmQ = {Q_blue:.4f} ≤ 0 at 450 nm")

    def test_polar_blue_improvement_1_to_10_pct(self):
        R_vec = float(self.lut_p.R_atm[0, 0, 0])
        R_sca = float(self.lut_s.R_atm[0, 0, 0])
        if R_sca > 0:
            pct = 100.0 * (R_vec - R_sca) / R_sca
            self.assertGreater(pct, 1.0,
                               msg=f"Polarization correction {pct:.2f}% < 1%")
            self.assertLess(pct, 10.0,
                            msg=f"Polarization correction {pct:.2f}% > 10%")

    def test_polar_effect_decreases_from_blue_to_nir(self):
        diff_blue = float(self.lut_p.R_atm[0, 0, 0] - self.lut_s.R_atm[0, 0, 0])
        diff_nir  = float(self.lut_p.R_atm[0, 0, -1] - self.lut_s.R_atm[0, 0, -1])
        self.assertGreaterEqual(diff_blue, diff_nir)


if __name__ == "__main__":
    unittest.main()
