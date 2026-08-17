"""6SV2.1 parity for polarized aerosols, BDM, and aircraft profiles."""

import json
from pathlib import Path

import numpy as np
import pytest

from _support import LutConfig, compute_lut


CASES = json.loads(
    (Path(__file__).parent / "data" / "6sv21_extended_parity.json").read_text()
)["cases"]


def compute_case(case):
    satellite = case["kind"] in ("satellite_polar", "satellite_polar_gas")
    model = case.get("model", 1)
    altitude = 1000.0
    if case["kind"] == "aircraft":
        altitude = case["height_km"]
    elif case["kind"] == "ground":
        altitude = 0.0
    cfg = LutConfig(
        wl=[case["wavelength_um"]],
        aod=[0.0 if model == 0 else 0.2],
        h2o=[case.get("h2o_g_cm2", 1e-6 if satellite else 1.424)],
        sza=30.0,
        vza=40.0 if satellite else 10.0,
        raa=300.0,
        altitude_km=altitude,
        atmo_model=1,
        aerosol_model=model,
        ozone_du=case.get("ozone_du", 1e-6 if satellite else 344.0),
        enable_polar=case["kind"] != "satellite_continuum",
    )
    return compute_lut(cfg)


@pytest.mark.parametrize(
    "case",
    [
        case
        for case in CASES
        if case["kind"] in ("satellite_polar", "satellite_polar_gas")
    ],
    ids=lambda case: case["name"],
)
def test_polarized_aerosol_and_bdm_parity(case):
    lut = compute_case(case)
    expected = case["fortran"]
    gas = case.get("kind") == "satellite_polar_gas"
    for name in ("R_atm", "R_atmQ", "R_atmU"):
        expected_name = "R_atm_effective" if name == "R_atm" else name
        if name in ("R_atmQ", "R_atmU"):
            expected_name += "_effective"
        # Gas-absorption cases (940 nm) keep the loose tolerance for R/T; the
        # scattering-only cases are accurate to a few parts in 1e-6. s_alb is a
        # pure scattering quantity, so it is tight in all cases.
        rtol = 0.01 if gas else 2e-5
        np.testing.assert_allclose(
            getattr(lut, name).item(), expected[expected_name], rtol=rtol, atol=2e-5
        )
    for name in ("T_down", "T_up", "s_alb"):
        expected_name = "T_up_effective" if name == "T_up" else name
        rtol = 0.003 if (gas and name != "s_alb") else 2e-5
        np.testing.assert_allclose(
            getattr(lut, name).item(), expected[expected_name], rtol=rtol, atol=3e-4
        )


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case["kind"] == "aircraft"],
    ids=lambda case: case["name"],
)
def test_aircraft_partial_column_parity(case):
    lut = compute_case(case)
    expected = case["fortran"]
    gas = case["wavelength_um"] > 0.6
    for name in ("R_atm", "R_atmQ", "R_atmU"):
        expected_name = "R_atm_effective" if name == "R_atm" else name
        if name in ("R_atmQ", "R_atmU"):
            expected_name += "_effective"
        rtol = 0.01 if gas else 1e-4
        np.testing.assert_allclose(
            getattr(lut, name).item(), expected[expected_name], rtol=rtol, atol=3e-6
        )
    for name in ("T_down", "T_up", "s_alb"):
        expected_name = "T_up_effective" if name == "T_up" else name
        rtol = 0.002 if gas else 2e-5
        np.testing.assert_allclose(
            getattr(lut, name).item(), expected[expected_name], rtol=rtol, atol=7e-4
        )


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case["kind"] == "satellite_continuum"],
    ids=lambda case: case["name"],
)
def test_water_continuum_parity(case):
    lut = compute_case(case)
    expected = case["fortran"]
    for name, expected_name, rtol in (
        ("R_atm", "R_atm_effective", 0.15),
        ("T_down", "T_down", 0.03),
        ("T_up", "T_up_effective", 0.04),
        ("s_alb", "s_alb", 0.03),
    ):
        np.testing.assert_allclose(
            getattr(lut, name).item(), expected[expected_name], rtol=rtol, atol=3e-5
        )


@pytest.mark.parametrize(
    "case",
    [case for case in CASES if case["kind"] == "ground"],
    ids=lambda case: case["name"],
)
def test_ground_observer_parity(case):
    lut = compute_case(case)
    expected = case["fortran"]
    np.testing.assert_allclose(lut.R_atm.item(), expected["R_atm"], atol=1e-7)
    np.testing.assert_allclose(lut.R_atmQ.item(), expected["R_atmQ"], atol=1e-7)
    np.testing.assert_allclose(lut.R_atmU.item(), expected["R_atmU"], atol=1e-7)
    np.testing.assert_allclose(lut.T_down.item(), expected["T_down"], rtol=1e-4)
    np.testing.assert_allclose(lut.T_up.item(), 1.0, atol=1e-7)
