#!/usr/bin/env python3
"""Generate polarized, desert, and aircraft references with original 6SV2.1."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


NUMBER = re.compile(r"[-+]?\d*\.\d+(?:[Ee][-+]?\d+)?|[-+]?\d+(?:[Ee][-+]?\d+)")
REFERENCE_COMMIT = "7deb2289cfe23c9b1d1b48d7647f76604ef75fa4"


def snap_to_sixs_grid(wl: float) -> float:
    """Snap a monochromatic wavelength to 6SV's 0.0025-µm evaluation grid.

    main.f indexes the s(1501) filter-function array as
    ``iinf=(wlinf-.25)/0.0025+1.5`` then evaluates scattering at
    ``wl=.25+(i-1)*0.0025``.  The C port is continuous, so parity tests must
    evaluate both sides at the same grid node the reference actually used.
    """
    iinf = int((wl - 0.25) / 0.0025 + 1.5)
    return 0.25 + (iinf - 1) * 0.0025


PRECISION_PATCH = (
    Path(__file__).resolve().parent / "patches" / "6sv21-print-precision.patch"
)


def values(line: str) -> list[float]:
    return [float(value) for value in NUMBER.findall(line)]


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


def satellite_input(
    model: int,
    wavelength: float = 0.55,
    h2o: float = 1e-6,
    ozone_atm_cm: float = 1e-9,
    observer: float = -1000.0,
) -> str:
    aerosol = f"{model}\n"
    aerosol += "-1\n" if model == 0 else "0\n0.2\n"
    return f"""0
30 0 40 60 7 2
8
{h2o} {ozone_atm_cm}
{aerosol}0
{observer:g}
-1
{wavelength:.3f}
0
0
0
0.20
-1
"""


def aircraft_input(height: float, wavelength: float, h2o: float = 1.424) -> str:
    return f"""0
30 0 10 60 4 28
8
{h2o} 0.344
1
0
0.20
0
{-height:g}
-1 -1
-1
-1
{wavelength:.3f}
0
0
0
0.20
-1
0
"""


def enmap_rgb_input(
    wavelength: float, aod: float = 0.07, h2o: float = 0.921, ozone_atm_cm: float = 0.3
) -> str:
    """Satellite deck for the EnMAP Tyrol scene (2022-06-12, DOY 163).

    Geometry from tyrol_austria_L1C/hyper.json: asol=24.23299,
    phi0=169.297249, avis=10.269471, phiv=14.339058, month=6, day=12.
    Atmospheric state: AOD_550=0.07, H2O=0.921 g/cm2, ozone=300 DU (0.3
    atm-cm).  Continental aerosol (model 1), US62 atmosphere (idatm=8).
    """
    return f"""0
{24.23299} {169.297249} {10.269471} {14.339058} 6 12
8
{h2o} {ozone_atm_cm}
1
0
{aod}
0
-1000
-1
{wavelength:.6f}
0
0
0
0.20
-1
"""


def run(executable: Path, input_text: str) -> dict[str, float]:
    result = subprocess.run(
        [executable], input=input_text, capture_output=True, text=True, check=True
    )
    parsed: dict[str, float] = {}
    for line in result.stdout.splitlines():
        if "apparent reflectance" in line and "appar. rad." in line:
            parsed["apparent_reflectance"] = values(line)[-2]
        elif "reflectance I" in line:
            parsed["R_atm"] = values(line)[-1]
        elif "reflectance Q" in line:
            polar = values(line)[-3:]
            parsed["R_rayleighQ"], parsed["R_aerosolQ"], parsed["R_atmQ"] = polar
        elif "reflectance U" in line:
            polar = values(line)[-3:]
            parsed["R_rayleighU"], parsed["R_aerosolU"], parsed["R_atmU"] = polar
        elif "global gas. trans." in line:
            parsed["gas_down"], parsed["gas_up"], parsed["gas_total"] = values(line)[
                -3:
            ]
        elif "total  sca." in line:
            parsed["sca_down"], parsed["sca_up"], _ = values(line)[-3:]
        elif "spherical albedo" in line:
            parsed["s_alb"] = values(line)[-1]
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
    parser.add_argument("executable", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--check", action="store_true", help="compare with the committed fixture"
    )
    args = parser.parse_args()
    verify_checkout(args.executable)

    cases = []
    for model, name in (
        (0, "rayleigh"),
        (1, "continental"),
        (2, "maritime"),
        (5, "desert_bdm"),
    ):
        reference = run(args.executable, satellite_input(model))
        for component in ("Q", "U"):
            reference[f"R_atm{component}_effective"] = (
                reference[f"R_atm{component}"] * reference["gas_total"]
            )
        cases.append(
            {
                "name": f"polar_{name}_550",
                "kind": "satellite_polar",
                "model": model,
                "wavelength_um": 0.55,
                "fortran": reference,
            }
        )
    reference = run(args.executable, satellite_input(5, 0.865))
    for component in ("Q", "U"):
        reference[f"R_atm{component}_effective"] = (
            reference[f"R_atm{component}"] * reference["gas_total"]
        )
    cases.append(
        {
            "name": "polar_desert_bdm_865",
            "kind": "satellite_polar",
            "model": 5,
            "wavelength_um": 0.865,
            "fortran": reference,
        }
    )
    reference = run(
        args.executable,
        satellite_input(1, 0.94, h2o=1.424, ozone_atm_cm=0.344),
    )
    no_h2o = run(
        args.executable,
        satellite_input(1, 0.94, h2o=1e-6, ozone_atm_cm=0.344),
    )
    half_h2o = run(
        args.executable,
        satellite_input(1, 0.94, h2o=0.5 * 1.424, ozone_atm_cm=0.344),
    )
    for component in ("Q", "U"):
        mixed = reference[f"R_atm{component}"]
        rayleigh = reference[f"R_rayleigh{component}"]
        reference[f"R_atm{component}_effective"] = (mixed - rayleigh) * half_h2o[
            "gas_total"
        ] + rayleigh * no_h2o["gas_total"]
    cases.append(
        {
            "name": "polar_continental_940_gas",
            "kind": "satellite_polar_gas",
            "model": 1,
            "wavelength_um": 0.94,
            "h2o_g_cm2": 1.424,
            "ozone_du": 344.0,
            "fortran": reference,
        }
    )
    for wl_band, name in (
        (0.477565, "enmap_rgb_478"),
        (0.571548, "enmap_rgb_572"),
        (0.65996, "enmap_rgb_660"),
    ):
        wl = snap_to_sixs_grid(wl_band)
        reference = run(args.executable, enmap_rgb_input(wl))
        no_h2o = run(
            args.executable,
            enmap_rgb_input(wl, h2o=1e-6),
        )
        half_h2o = run(
            args.executable,
            enmap_rgb_input(wl, h2o=0.5 * 0.921),
        )
        for component in ("Q", "U"):
            mixed = reference[f"R_atm{component}"]
            rayleigh = reference[f"R_rayleigh{component}"]
            reference[f"R_atm{component}_effective"] = (mixed - rayleigh) * half_h2o[
                "gas_total"
            ] + rayleigh * no_h2o["gas_total"]
        cases.append(
            {
                "name": name,
                "kind": "satellite_polar",
                "model": 1,
                "wavelength_um": wl,
                "h2o_g_cm2": 0.921,
                "ozone_du": 300.0,
                "aod": 0.07,
                "fortran": reference,
            }
        )
    cases.append(
        {
            "name": "satellite_continuum_3750",
            "kind": "satellite_continuum",
            "model": 1,
            "wavelength_um": 3.75,
            "h2o_g_cm2": 1.424,
            "ozone_du": 344.0,
            "fortran": run(
                args.executable,
                satellite_input(1, 3.75, h2o=1.424, ozone_atm_cm=0.344),
            ),
        }
    )
    cases.append(
        {
            "name": "ground_continental_550",
            "kind": "ground",
            "model": 1,
            "wavelength_um": 0.55,
            "h2o_g_cm2": 1.424,
            "ozone_du": 344.0,
            "fortran": run(
                args.executable,
                satellite_input(1, 0.55, h2o=1.424, ozone_atm_cm=0.344, observer=0.0),
            ),
        }
    )
    for height in (3.0, 10.0):
        for wavelength in (0.55, 0.94):
            reference = run(args.executable, aircraft_input(height, wavelength))
            no_h2o = run(args.executable, aircraft_input(height, wavelength, 1e-6))
            half_h2o = run(
                args.executable, aircraft_input(height, wavelength, 0.5 * 1.424)
            )
            for component in ("Q", "U"):
                mixed = reference[f"R_atm{component}"]
                rayleigh = reference[f"R_rayleigh{component}"]
                reference[f"R_atm{component}_effective"] = (
                    mixed - rayleigh
                ) * half_h2o["gas_total"] + rayleigh * no_h2o["gas_total"]
            cases.append(
                {
                    "name": f"aircraft_{height:g}km_{int(wavelength * 1000)}",
                    "kind": "aircraft",
                    "height_km": height,
                    "wavelength_um": wavelength,
                    "fortran": reference,
                }
            )

    document = {
        "source": "https://github.com/NakamuraTakashi/6SV2.1",
        "commit": "7deb2289cfe23c9b1d1b48d7647f76604ef75fa4",
        "cases": cases,
    }
    text = json.dumps(document, indent=2) + "\n"
    if args.check:
        fixture = Path(__file__).parent / "data" / "6sv21_extended_parity.json"
        if json.loads(fixture.read_text(encoding="ascii")) != document:
            raise SystemExit("generated reference differs from committed fixture")
        print("fixture check: PASS")
        return
    if args.output:
        args.output.write_text(text, encoding="ascii")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
