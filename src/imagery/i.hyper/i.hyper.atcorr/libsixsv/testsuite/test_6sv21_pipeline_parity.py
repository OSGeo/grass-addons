"""End-to-end LUT parity against a pinned original 6SV2.1 simulation."""

import json
from pathlib import Path

import numpy as np

from _support import LutConfig, compute_lut


FIXTURE = json.loads(
    (Path(__file__).parent / "data" / "6sv21_satellite_continental.json").read_text()
)
ROWS = FIXTURE["rows"]


def corrected_lut():
    cfg = LutConfig(
        wl=[row["wavelength_nm"] / 1000.0 for row in ROWS],
        aod=[0.2],
        h2o=[2.0],
        sza=30.0,
        vza=0.0,
        raa=0.0,
        altitude_km=1000.0,
        atmo_model=1,
        aerosol_model=1,
        ozone_du=300.0,
        enable_polar=1,
    )
    return compute_lut(cfg)


def test_satellite_continental_coefficients_match_6sv21():
    lut = corrected_lut()
    for name, rtol in (
        ("R_atm", 0.012),
        ("T_down", 0.007),
        ("T_up", 0.007),
        ("s_alb", 0.012),
    ):
        actual = getattr(lut, name)[0, 0]
        expected_name = {
            "R_atm": "R_atm_effective",
            "T_up": "T_up_effective",
        }.get(name, name)
        expected = np.array([row["fortran"][expected_name] for row in ROWS])
        np.testing.assert_allclose(actual, expected, rtol=rtol, atol=2e-5, err_msg=name)


def test_fortran_toa_reflectance_recovers_surface_reflectance():
    lut = corrected_lut()
    rho_toa = np.array([row["apparent_reflectance"] for row in ROWS])
    y = (rho_toa - lut.R_atm[0, 0]) / (lut.T_down[0, 0] * lut.T_up[0, 0])
    recovered = y / (1.0 + lut.s_alb[0, 0] * y)
    np.testing.assert_allclose(recovered, 0.2, rtol=0.011, atol=2e-4)
