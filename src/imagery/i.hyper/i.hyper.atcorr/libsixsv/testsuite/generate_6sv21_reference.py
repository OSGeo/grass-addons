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
REFERENCE_COMMIT = "7deb2289cfe23c9b1d1b48d7647f76604ef75fa4"
PRECISION_PATCH = HERE / "patches" / "6sv21-print-precision.patch"


def verify_checkout(executable: Path) -> None:
    result = subprocess.run(
        ["git", "-C", executable.parent, "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout.strip() != REFERENCE_COMMIT:
        raise SystemExit(
            f"reference executable must come from commit {REFERENCE_COMMIT}"
        )
    source_diff = subprocess.run(
        ["git", "-C", executable.parent, "diff", "HEAD", "--", ":(glob)**/*.f"],
        capture_output=True,
        text=True,
        check=False,
    )
    expected = (
        PRECISION_PATCH.read_text(encoding="ascii").rstrip()
        if PRECISION_PATCH.exists()
        else ""
    )
    if source_diff.stdout.rstrip() not in ("", expected):
        raise SystemExit(
            "reference Fortran sources have uncommitted changes "
            "(only the committed 6sv21-print-precision.patch is allowed)"
        )
    newest_source = max(path.stat().st_mtime for path in executable.parent.glob("*.f"))
    if not executable.exists() or executable.stat().st_mtime < newest_source:
        raise SystemExit("reference executable is older than its Fortran sources")


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
            parsed["gas_down"], parsed["gas_up"], parsed["gas_total"] = values(line)[
                -3:
            ]
        elif "total  sca." in line:
            parsed["sca_down"], parsed["sca_up"], _ = values(line)[-3:]
        elif "spherical albedo" in line:
            parsed["s_alb"] = values(line)[-1]
        elif "reflectance I" in line:
            parsed["R_atm"] = values(line)[-1]
    parsed["T_down"] = parsed["gas_down"] * parsed["sca_down"]
    parsed["T_up"] = parsed["gas_up"] * parsed["sca_up"]
    parsed["T_up_effective"] = (
        parsed["sca_up"] * parsed["gas_total"] / parsed["gas_down"]
    )
    surface = 0.2
    parsed["R_atm_effective"] = parsed["apparent_reflectance"] - (
        parsed["T_down"]
        * parsed["T_up_effective"]
        * surface
        / (1.0 - parsed["s_alb"] * surface)
    )
    return parsed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path, help="path to sixsV2.1")
    parser.add_argument(
        "--check", action="store_true", help="compare with committed fixture"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the regenerated fixture (with --check: update in place)",
    )
    args = parser.parse_args()
    verify_checkout(args.executable)

    expected = json.loads(FIXTURE.read_text())
    rows = [run_case(args.executable, row["wavelength_nm"]) for row in expected["rows"]]
    print("wl  radiance  R_atm   T_down  T_up    s_alb")
    for row in rows:
        print(
            f"{row['wavelength_nm']:3d} {row['radiance_um']:9.3f} "
            f"{row['R_atm']:.5f} {row['T_down']:.5f} "
            f"{row['T_up']:.5f} {row['s_alb']:.5f}"
        )

    document = {
        "source": "https://github.com/NakamuraTakashi/6SV2.1",
        "commit": "7deb2289cfe23c9b1d1b48d7647f76604ef75fa4",
        "configuration": expected.get(
            "configuration",
            {
                "sza": 30.0,
                "vza": 0.0,
                "raa": 0.0,
                "atmosphere": "US62",
                "aerosol": "continental",
                "aod_550": 0.2,
                "h2o_g_cm2": 2.0,
                "ozone_du": 300.0,
                "sensor_altitude_km": 1000.0,
                "surface_reflectance": 0.2,
            },
        ),
        "rows": [
            {
                "wavelength_nm": row["wavelength_nm"],
                "radiance_um": row["radiance_um"],
                "apparent_reflectance": row["apparent_reflectance"],
                "fortran": {
                    "R_atm": row["R_atm"],
                    "R_atm_effective": row["R_atm_effective"],
                    "T_down": row["T_down"],
                    "T_up": row["T_up"],
                    "T_up_effective": row["T_up_effective"],
                    "s_alb": row["s_alb"],
                },
                "before": fixture_row.get("before"),
            }
            for row, fixture_row in zip(rows, expected["rows"], strict=True)
        ],
    }
    if args.output:
        text = json.dumps(document, indent=1) + "\n"
        args.output.write_text(text, encoding="ascii")

    if args.check:
        for actual, fixture_row in zip(rows, expected["rows"], strict=True):
            reference = fixture_row["fortran"]
            for name in (
                "R_atm",
                "R_atm_effective",
                "T_down",
                "T_up",
                "T_up_effective",
                "s_alb",
            ):
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
