"""Unit test: compare i.hyper.atcorr correction against Planet/ISOFIT reference.

Loads TOA radiance from ../radiance.json and the reference surface reflectance
produced by Planet's ISOFIT pipeline from ../expected_reflectance.json, then
runs our 6SV2.1-based atmospheric correction and reports per-wavelength
percentage agreement.

Design notes
------------
* expected_reflectance.json is the Planet/ISOFIT output, NOT the output of
  i.hyper.atcorr.  The two methods differ fundamentally:
  - ISOFIT: optimal estimation with surface priors, scene-specific retrieval
  - i.hyper.atcorr: algebraic 6SV inversion with fixed scene parameters

  Consequently this test does NOT assert a tight numerical agreement; it
  documents the discrepancy per wavelength.

* Masked bands (two tiers):
  1. ISOFIT sentinel  — ISOFIT set reflectance = -0.01 for opaque gas windows
                        (strong H2O at ~1362–1407 nm and ~1802–1967 nm).
  2. Low-signal bands — mean TOA reflectance < LOGSIG_THR across all sample
                        points.  Near-zero signal makes the algebraic inversion
                        numerically unstable; both methods are unreliable there.

  Both tiers are excluded from physical-bounds and match statistics.

* Pass/fail tests cover only data integrity and physical plausibility for
  high-signal bands.  Per-wavelength match statistics are always printed as a
  diagnostic report; no assertion is made on the match percentage because the
  scene parameters used to generate the ISOFIT reference are unknown.

Scene parameters
----------------
Default to the Kanpur/Tanager geometry from the i.hyper.atcorr documentation.
Override via environment variables:

    ATCORR_SZA    solar zenith angle (deg)         default 35.2
    ATCORR_VZA    view zenith angle (deg)           default 4.1
    ATCORR_RAA    relative azimuth (deg)            default 97.0
    ATCORR_ALT    altitude km (>900 = satellite)    default 1000.0
    ATCORR_DOY    day of year                       default 45
    ATCORR_AOD    AOD at 550 nm (scalar)            default 0.18
    ATCORR_H2O    column H2O g/cm² (scalar)         default 3.5
    ATCORR_ATMO   atmosphere model (1=US62,2=MIDSUM) default 2
    ATCORR_AEROSOL aerosol model (1=continental)    default 1
    ATCORR_OZONE  ozone Dobson units                default 310.0

Usage
-----
    python3 tests/test_reflectance.py           # tests + full per-band report
    python3 -m unittest tests.test_reflectance  # unittest only (no report)
"""

import json
import math
import os
import sys
import unittest

import numpy as np

# ── Locate project root and Python bindings ────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_PY   = os.path.join(_ROOT, "python")
if _PY not in sys.path:
    sys.path.insert(0, _PY)

import atcorr as ac

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

SCENE = {
    "sza":           float(os.environ.get("ATCORR_SZA",    "35.2")),
    "vza":           float(os.environ.get("ATCORR_VZA",    "4.1")),
    "raa":           float(os.environ.get("ATCORR_RAA",    "97.0")),
    "altitude_km":   float(os.environ.get("ATCORR_ALT",    "1000.0")),
    "doy":           int  (os.environ.get("ATCORR_DOY",    "45")),
    "aod_val":       float(os.environ.get("ATCORR_AOD",    "0.18")),
    "h2o_val":       float(os.environ.get("ATCORR_H2O",    "3.5")),
    "atmo_model":    int  (os.environ.get("ATCORR_ATMO",   "2")),
    "aerosol_model": int  (os.environ.get("ATCORR_AEROSOL","1")),
    "ozone_du":      float(os.environ.get("ATCORR_OZONE",  "310.0")),
}

AOD_GRID = np.array([0.0, 0.05, 0.1, 0.18, 0.2, 0.4, 0.8], dtype=np.float32)
H2O_GRID = np.array([0.5, 1.0, 2.0, 3.5, 5.0],              dtype=np.float32)

# Minimum total two-way transmittance T_down*T_up for a band to be usable.
# Below this threshold the algebraic inversion diverges (gas absorption bands).
# Standard practice: bands with >95% atmospheric absorption are discarded.
T_TOTAL_THR = 0.05

# ISOFIT bad-band sentinel value
ISOFIT_SENTINEL = -0.01

# Data files
_RAD_JSON = os.path.join(_ROOT, "radiance.json")
_REF_JSON = os.path.join(_ROOT, "expected_reflectance.json")


# ══════════════════════════════════════════════════════════════════════════════
# Data loading and correction
# ══════════════════════════════════════════════════════════════════════════════

def _load_data():
    """Return (wl_nm [N], rad [P,N], ref [P,N]) and verify coordinate alignment."""
    with open(_RAD_JSON) as f:
        rad_doc = json.load(f)
    with open(_REF_JSON) as f:
        ref_doc = json.load(f)

    rad_ds = rad_doc["datasets"][0]
    ref_ds = ref_doc["datasets"][0]

    wl_nm = np.array(rad_ds["wavelength_nm"], dtype=np.float64)
    rad   = np.array([p["values"] for p in rad_ds["points"]], dtype=np.float64)
    ref   = np.array([p["values"] for p in ref_ds["points"]], dtype=np.float64)

    for i, (rp, ep) in enumerate(zip(rad_ds["points"], ref_ds["points"])):
        if abs(rp["x"] - ep["x"]) > 1.0 or abs(rp["y"] - ep["y"]) > 1.0:
            raise AssertionError(
                f"Point {i} coordinate mismatch: "
                f"rad=({rp['x']:.1f},{rp['y']:.1f}) "
                f"ref=({ep['x']:.1f},{ep['y']:.1f})"
            )

    return wl_nm, rad, ref


def _compute_correction(wl_nm):
    """Build LUT, extract scalar slice, return (slice, E0[N], d2)."""
    wl_um = (wl_nm / 1000.0).astype(np.float32)
    cfg = ac.LutConfig(
        wl           = wl_um,
        aod          = AOD_GRID,
        h2o          = H2O_GRID,
        sza          = SCENE["sza"],
        vza          = SCENE["vza"],
        raa          = SCENE["raa"],
        altitude_km  = SCENE["altitude_km"],
        atmo_model   = SCENE["atmo_model"],
        aerosol_model= SCENE["aerosol_model"],
        ozone_du     = SCENE["ozone_du"],
    )
    lut = ac.compute_lut(cfg)
    slc = ac.lut_slice(cfg, lut, SCENE["aod_val"], SCENE["h2o_val"])

    E0 = np.array([ac.solar_E0(float(w)) for w in wl_um], dtype=np.float64)
    d2 = ac.earth_sun_dist2(SCENE["doy"])

    return slc, E0, d2


def _t_total(slc):
    """Per-band total two-way transmittance T_down × T_up [N]."""
    return slc.T_down.astype(np.float64) * slc.T_up.astype(np.float64)


def _invert(rad, slc, E0, d2):
    """Convert radiance [P,N] → (rho_toa [P,N], rho_boa [P,N])."""
    cos_sza = math.cos(math.radians(SCENE["sza"]))
    rho_toa = math.pi * rad * d2 / (E0 * cos_sza + 1e-30)
    rho_boa = ac.invert(
        rho_toa,
        slc.R_atm.astype(np.float64),
        slc.T_down.astype(np.float64),
        slc.T_up.astype(np.float64),
        slc.s_alb.astype(np.float64),
    )
    return rho_toa, rho_boa


def _build_masks(ref, slc):
    """Return (isofit_mask, ttot_mask, combined_mask), all [N] boolean.

    Tier 1 — ISOFIT sentinel: ISOFIT set all 14 points to -0.01 for
    opaque gas-absorption windows (strong H2O at ~1362–1407 nm and
    ~1802–1967 nm).

    Tier 2 — Low transmittance: T_down × T_up < T_TOTAL_THR (default 5%).
    In these gas-absorption/edge bands the algebraic 6SV inversion is
    numerically unreliable regardless of signal level.  Both methods
    (ISOFIT and 6SV) are unreliable in such bands.
    """
    # Tier 1
    isofit_mask = np.all(ref == ISOFIT_SENTINEL, axis=0)

    # Tier 2
    ttot = _t_total(slc)
    ttot_mask = ttot < T_TOTAL_THR

    combined = isofit_mask | ttot_mask
    return isofit_mask, ttot_mask, combined


# ══════════════════════════════════════════════════════════════════════════════
# Per-wavelength statistics
# ══════════════════════════════════════════════════════════════════════════════

def _per_wavelength_stats(computed, expected, combined_mask):
    """Compute per-band match statistics (NaN for masked bands).

    Returns dict with [N] arrays:
        mean_abs_err, mean_rel_err_pct, std_rel_err_pct,
        pct_within_10, pct_within_20, pct_within_50
    """
    n_pts, n_bands = computed.shape
    out = {k: np.full(n_bands, np.nan) for k in
           ("mean_abs_err", "mean_rel_err_pct", "std_rel_err_pct",
            "pct_within_10", "pct_within_20", "pct_within_50")}

    for b in range(n_bands):
        if combined_mask[b]:
            continue
        c = computed[:, b]
        e = expected[:, b]
        # Only compare against ISOFIT values that are physically plausible
        valid = (np.abs(e) > 1e-4) & (e > -0.05)
        if valid.sum() == 0:
            continue

        abs_err = np.abs(c[valid] - e[valid])
        rel_err = abs_err / np.abs(e[valid])

        out["mean_abs_err"][b]      = abs_err.mean()
        out["mean_rel_err_pct"][b]  = rel_err.mean() * 100.0
        out["std_rel_err_pct"][b]   = rel_err.std()  * 100.0
        out["pct_within_10"][b]     = (rel_err < 0.10).mean() * 100.0
        out["pct_within_20"][b]     = (rel_err < 0.20).mean() * 100.0
        out["pct_within_50"][b]     = (rel_err < 0.50).mean() * 100.0

    return out


# ══════════════════════════════════════════════════════════════════════════════
# Report printer
# ══════════════════════════════════════════════════════════════════════════════

def _print_report(wl_nm, stats, isofit_mask, ttot_mask):
    n = len(wl_nm)
    combined = isofit_mask | ttot_mask

    W = 108
    sep = "─" * W
    print()
    print(sep)
    print("  i.hyper.atcorr (6SV2.1 algebraic)  vs  Planet/ISOFIT — per-wavelength comparison")
    print(f"  SZA={SCENE['sza']}°  VZA={SCENE['vza']}°  RAA={SCENE['raa']}°  "
          f"DOY={SCENE['doy']}  AOD={SCENE['aod_val']}  H2O={SCENE['h2o_val']} g/cm²  "
          f"atmo={SCENE['atmo_model']}  aerosol={SCENE['aerosol_model']}")
    print(f"  {n} bands  ·  14 sample points  ·  "
          f"ISOFIT-masked: {isofit_mask.sum()}  "
          f"low-transmittance-masked: {(ttot_mask & ~isofit_mask).sum()}  "
          f"(T_total < {T_TOTAL_THR*100:.0f}%)")
    print(sep)
    hdr = (f"{'Band':>4}  {'WL(nm)':>8}  {'MeanAbsErr':>10}  "
           f"{'MeanRel%':>8}  {'StdRel%':>7}  "
           f"{'Pct<10%':>7}  {'Pct<20%':>7}  {'Pct<50%':>7}  Note")
    print(hdr)
    print(sep)

    for b in range(n):
        wl = wl_nm[b]
        if isofit_mask[b]:
            note = "ISOFIT-masked (opaque gas window)"
            print(f"{b:>4}  {wl:>8.1f}  {'—':>10}  {'—':>8}  {'—':>7}  "
                  f"{'—':>7}  {'—':>7}  {'—':>7}  {note}")
            continue
        if ttot_mask[b]:
            ttot_val = float(combined[b])  # placeholder — recomputed below in summary
            note = f"low-transmittance (T_total<{T_TOTAL_THR*100:.0f}%)"
            print(f"{b:>4}  {wl:>8.1f}  {'—':>10}  {'—':>8}  {'—':>7}  "
                  f"{'—':>7}  {'—':>7}  {'—':>7}  {note}")
            continue

        mae  = stats["mean_abs_err"][b]
        mre  = stats["mean_rel_err_pct"][b]
        sre  = stats["std_rel_err_pct"][b]
        p10  = stats["pct_within_10"][b]
        p20  = stats["pct_within_20"][b]
        p50  = stats["pct_within_50"][b]

        if np.isnan(mre):
            note = "all-ISOFIT-invalid"
        elif mre > 100:
            note = "*** LARGE DISCREPANCY"
        elif mre > 50:
            note = "** high discrepancy"
        elif mre > 20:
            note = "* elevated"
        else:
            note = ""

        print(f"{b:>4}  {wl:>8.1f}  {mae:>10.4f}  {mre:>8.2f}  {sre:>7.2f}  "
              f"{p10:>7.1f}  {p20:>7.1f}  {p50:>7.1f}  {note}")

    # ── Region summary ──────────────────────────────────────────────────────────
    regions = [
        ("VIS      376–700 nm",   (wl_nm >= 376)  & (wl_nm <= 700)),
        ("NIR      700–1000 nm",  (wl_nm > 700)   & (wl_nm <= 1000)),
        ("SWIR-1  1000–1300 nm",  (wl_nm > 1000)  & (wl_nm <= 1300)),
        ("SWIR-1b 1300–1450 nm",  (wl_nm > 1300)  & (wl_nm <= 1450)),
        ("SWIR-2  1450–1800 nm",  (wl_nm > 1450)  & (wl_nm <= 1800)),
        ("SWIR-2b 1800–2500 nm",  (wl_nm > 1800)  & (wl_nm <= 2500)),
    ]
    print()
    print(sep)
    print(f"  Summary by spectral region  (active bands only — excluding both mask tiers)")
    print(sep)
    print(f"  {'Region':<24}  {'Active':>6}  {'Excl.':>6}  "
          f"{'MeanRel%':>8}  {'Pct<10%':>7}  {'Pct<20%':>7}  {'Pct<50%':>7}")
    print(sep)

    for name, sel in regions:
        active_sel = sel & ~combined
        masked_sel = sel & combined
        valid_sel  = active_sel & ~np.isnan(stats["mean_rel_err_pct"])
        if valid_sel.sum() == 0:
            print(f"  {name:<24}  {active_sel.sum():>6}  {masked_sel.sum():>6}  "
                  f"{'—':>8}  {'—':>7}  {'—':>7}  {'—':>7}")
            continue
        mre = np.nanmean(stats["mean_rel_err_pct"][valid_sel])
        p10 = np.nanmean(stats["pct_within_10"][valid_sel])
        p20 = np.nanmean(stats["pct_within_20"][valid_sel])
        p50 = np.nanmean(stats["pct_within_50"][valid_sel])
        print(f"  {name:<24}  {active_sel.sum():>6}  {masked_sel.sum():>6}  "
              f"{mre:>8.2f}  {p10:>7.1f}  {p20:>7.1f}  {p50:>7.1f}")

    all_valid = ~combined & ~np.isnan(stats["mean_rel_err_pct"])
    if all_valid.sum() > 0:
        mre = np.nanmean(stats["mean_rel_err_pct"][all_valid])
        p10 = np.nanmean(stats["pct_within_10"][all_valid])
        p20 = np.nanmean(stats["pct_within_20"][all_valid])
        p50 = np.nanmean(stats["pct_within_50"][all_valid])
        print(sep)
        print(f"  {'OVERALL (active bands)':<24}  {all_valid.sum():>6}  "
              f"{combined.sum():>6}  {mre:>8.2f}  {p10:>7.1f}  {p20:>7.1f}  {p50:>7.1f}")
    print(sep)
    print()


# ══════════════════════════════════════════════════════════════════════════════
# Test class — integrity and physical plausibility only
# ══════════════════════════════════════════════════════════════════════════════

class TestReflectanceMatch(unittest.TestCase):
    """Integrity tests for the 6SV2.1 vs ISOFIT per-wavelength comparison.

    Match quality is NOT asserted here because the exact ISOFIT scene
    parameters are unknown.  Run the script directly for the full diagnostic.
    """

    @classmethod
    def setUpClass(cls):
        cls.wl_nm, cls.rad, cls.ref = _load_data()
        cls.slc, E0, d2 = _compute_correction(cls.wl_nm)
        cls.rho_toa, cls.computed = _invert(cls.rad, cls.slc, E0, d2)
        cls.isofit_mask, cls.ttot_mask, cls.combined = _build_masks(
            cls.ref, cls.slc
        )
        cls.stats = _per_wavelength_stats(cls.computed, cls.ref, cls.combined)

    # ── Data integrity ─────────────────────────────────────────────────────────

    def test_data_shape(self):
        """Both datasets must have 14 points × 426 wavelengths."""
        self.assertEqual(self.rad.shape,  (14, 426))
        self.assertEqual(self.ref.shape,  (14, 426))
        self.assertEqual(len(self.wl_nm), 426)

    def test_wavelength_range(self):
        """Wavelength grid must span 376–2499 nm."""
        self.assertAlmostEqual(float(self.wl_nm[0]),  376.44, delta=0.5)
        self.assertAlmostEqual(float(self.wl_nm[-1]), 2499.0, delta=1.0)

    def test_wavelength_monotone(self):
        """Wavelengths must be strictly increasing."""
        diffs = np.diff(self.wl_nm)
        self.assertTrue(
            np.all(diffs > 0),
            f"Non-monotone wavelengths at indices {np.where(diffs <= 0)[0]}"
        )

    def test_radiance_positive(self):
        """TOA radiance must be >= 0 for all sample points and bands."""
        self.assertTrue(
            np.all(self.rad >= -0.01),
            f"Negative radiance found: min={self.rad.min():.4f}"
        )

    def test_isofit_sentinel_in_gas_windows(self):
        """ISOFIT sentinel bands must lie in known gas-absorption windows."""
        bad_wl = self.wl_nm[self.isofit_mask]
        for wl in bad_wl:
            in_window = (1330 <= wl <= 1450) or (1770 <= wl <= 2000)
            self.assertTrue(
                in_window,
                f"ISOFIT-masked band at {wl:.1f} nm outside known H2O windows "
                "(1330–1450 nm and 1770–2000 nm)"
            )

    def test_masked_fraction_reasonable(self):
        """At most 35% of bands should require masking (both tiers combined).

        With T_TOTAL_THR=5% this catches all gas absorption edges; a sensor
        with 5nm FWHM typically has ~20-30% of its bands affected.
        """
        frac = self.combined.mean()
        self.assertLessEqual(
            frac, 0.35,
            f"Too many masked bands: {self.combined.sum()} / {len(self.combined)} "
            f"= {frac*100:.1f}%"
        )

    # ── Physical plausibility for high-signal bands ────────────────────────────

    def test_computed_physical_highsignal(self):
        """Computed BOA reflectance is physically plausible for active bands.

        For active (non-masked) bands the algebraic 6SV inversion can produce
        values slightly above 1.0 in partial gas-absorption edges where
        T_total is between 5% and ~20%.  We therefore check that:
          * No more than 5% of (point, band) pairs fall outside [-0.2, 1.5]
          * No values fall below -0.5 (would indicate a sign error)
        """
        active = ~self.combined
        c = self.computed[:, active]
        n_total = c.size

        below = c < -0.5
        self.assertFalse(
            bool(np.any(below)),
            f"Computed BOA reflectance below -0.5 in active bands: "
            f"min={c.min():.4f}"
        )

        outliers = (c < -0.2) | (c > 1.5)
        outlier_frac = float(outliers.mean())
        self.assertLessEqual(
            outlier_frac, 0.05,
            f"Too many active-band outliers outside [-0.2, 1.5]: "
            f"{outliers.sum()} / {n_total} = {outlier_frac*100:.1f}% "
            f"(expected ≤5% from gas-absorption edge effects)"
        )

    def test_lut_computation_succeeds(self):
        """LUT computation must succeed and return finite values."""
        slc, E0, d2 = _compute_correction(self.wl_nm)
        for name, arr in (
            ("R_atm",  slc.R_atm),
            ("T_down", slc.T_down),
            ("T_up",   slc.T_up),
            ("s_alb",  slc.s_alb),
        ):
            self.assertTrue(
                np.all(np.isfinite(arr)),
                f"LUT slice {name} contains non-finite values"
            )
            if name in ("T_down", "T_up"):
                self.assertTrue(
                    np.all(arr > 0),
                    f"LUT slice {name} has non-positive values"
                )

    def test_e0_positive(self):
        """Solar irradiance E0 must be positive for all sensor wavelengths."""
        wl_um = (self.wl_nm / 1000.0).astype(np.float32)
        E0 = np.array([ac.solar_E0(float(w)) for w in wl_um])
        self.assertTrue(
            np.all(E0 > 0),
            f"Solar irradiance E0 <= 0 at wavelengths: "
            f"{self.wl_nm[E0 <= 0]}"
        )

    def test_earth_sun_dist_reasonable(self):
        """Earth-Sun distance squared must be close to 1 AU² (within 4%)."""
        d2 = ac.earth_sun_dist2(SCENE["doy"])
        self.assertAlmostEqual(
            d2, 1.0, delta=0.04,
            msg=f"Earth-Sun dist² = {d2:.4f} far from 1.0 for DOY={SCENE['doy']}"
        )

    # ── Statistics availability ────────────────────────────────────────────────

    def test_active_bands_have_statistics(self):
        """Every active (non-masked) band must have finite mean_rel_err_pct."""
        active = ~self.combined
        mre = self.stats["mean_rel_err_pct"][active]
        finite = np.isfinite(mre)
        n_missing = (~finite).sum()
        self.assertLessEqual(
            n_missing, 5,
            f"{n_missing} active bands have no valid match statistics "
            f"(likely all ISOFIT values are physically implausible there)"
        )

    def test_pct_fields_in_range(self):
        """Percentage fields must be in [0, 100] for all active bands."""
        active = ~self.combined
        for key in ("pct_within_10", "pct_within_20", "pct_within_50"):
            vals = self.stats[key][active]
            valid = vals[np.isfinite(vals)]
            if len(valid) == 0:
                continue
            self.assertTrue(
                np.all((valid >= 0) & (valid <= 100)),
                f"{key} out of [0,100]: min={valid.min():.2f} max={valid.max():.2f}"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Main: run tests then print full per-wavelength report
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None   # preserve declaration order
    suite  = loader.loadTestsFromTestCase(TestReflectanceMatch)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print full report (reuses the class-level state computed by setUpClass)
    TestReflectanceMatch.setUpClass()
    _print_report(
        TestReflectanceMatch.wl_nm,
        TestReflectanceMatch.stats,
        TestReflectanceMatch.isofit_mask,
        TestReflectanceMatch.ttot_mask,
    )

    sys.exit(0 if result.wasSuccessful() else 1)
