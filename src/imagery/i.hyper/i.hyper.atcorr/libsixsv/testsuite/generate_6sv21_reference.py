#!/usr/bin/env python3
"""Run the pinned original 6SV2.1 executable for the pipeline parity cases."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "data" / "6sv21_satellite_continental.json"
NUMBER = re.compile(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|[-+]?\d+(?:[Ee][-+]?\d+)")


def sixs_input(wavelength_nm: int) -> str:
    wavelength_um = wavelength_nm / 1000.0
    return f"""0
30.0 0.0 0.0 0.0 7 2
8
2.0 0.300
1
0
0.2
0
-1000
-1
{wavelength_um:.3f}
0
0
0
0.20
-1
"""


def values(line: str) -> list[float]:
    return [float(value) for value in NUMBER.findall(line)]


def run_case(executable: Path, wavelength_nm: int) -> dict[str, float]:
    result = subprocess.run(
        [executable],
        input=sixs_input(wavelength_nm),
        capture_output=True,
        text=True,
        check=True,
    )
    parsed: dict[str, float] = {"wavelength_nm": wavelength_nm}
    for line in result.stdout.splitlines():
        if "apparent reflectance" in line and "appar. rad." in line:
            parsed["apparent_reflectance"], parsed["radiance_um"] = values(line)[-2:]
        elif "global gas. trans." in line:
            parsed["gas_down"], parsed["gas_up"], _ = values(line)[-3:]
        elif "total  sca." in line:
            parsed["sca_down"], parsed["sca_up"], _ = values(line)[-3:]
        elif "spherical albedo" in line:
            parsed["s_alb"] = values(line)[-1]
        elif "reflectance I" in line:
            parsed["R_atm"] = values(line)[-1]
    parsed["T_down"] = parsed["gas_down"] * parsed["sca_down"]
    parsed["T_up"] = parsed["gas_up"] * parsed["sca_up"]
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path, help="path to sixsV2.1")
    parser.add_argument(
        "--check", action="store_true", help="compare with committed fixture"
    )
    args = parser.parse_args()

    expected = json.loads(FIXTURE.read_text())
    rows = [run_case(args.executable, row["wavelength_nm"]) for row in expected["rows"]]
    print("wl  radiance  R_atm   T_down  T_up    s_alb")
    for row in rows:
        print(
            f"{row['wavelength_nm']:3d} {row['radiance_um']:9.3f} "
            f"{row['R_atm']:.5f} {row['T_down']:.5f} "
            f"{row['T_up']:.5f} {row['s_alb']:.5f}"
        )

    if args.check:
        for actual, fixture_row in zip(rows, expected["rows"], strict=True):
            reference = fixture_row["fortran"]
            for name in ("R_atm", "T_down", "T_up", "s_alb"):
                np.testing.assert_allclose(
                    actual[name], reference[name], rtol=2e-5, atol=2e-5
                )
            np.testing.assert_allclose(
                actual["radiance_um"], fixture_row["radiance_um"], atol=5e-4
            )
            np.testing.assert_allclose(
                actual["apparent_reflectance"],
                fixture_row["apparent_reflectance"],
                atol=5e-7,
            )
        print("fixture check: PASS")


if __name__ == "__main__":
    main()
