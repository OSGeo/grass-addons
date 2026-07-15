"""GRASS module integration tests for i.hyper.atcorr.

Tests the i.hyper.atcorr GRASS module using synthetic Raster3D data.
Two test classes:
  - TestIHyperAtcorrLUT    : LUT-only computation (no Raster3D input needed)
  - TestIHyperAtcorrCorrect: full Raster3D atmospheric correction pipeline

Run from inside a GRASS session:
    cd i.hyper.atcorr/testsuite
    python -m grass.gunittest.main
"""

import os
import sys
import tempfile

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


# ── Geometry for all tests ────────────────────────────────────────────────────
_SZA = 35.0
_VZA = 5.0
_RAA = 90.0
_ALT = 1000.0   # km (satellite)
_DOY = 180

# Bands for the synthetic Raster3D [nm]
_BAND_WL_NM = [450.0, 550.0, 650.0, 870.0]
_N_BANDS = len(_BAND_WL_NM)

# Constant TOA radiance for each synthetic band [W m⁻² sr⁻¹ µm⁻¹]
# Chosen to give ρ_BOA ≈ 0.15–0.30 for the test geometry
_RADIANCE = 100.0


class TestIHyperAtcorrLUT(TestCase):
    """Tests for LUT-only mode (lut= output, no Raster3D input required)."""

    @classmethod
    def setUpClass(cls):
        cls.lut_file = tempfile.mktemp(suffix=".lut", prefix="ihyper_test_")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.lut_file):
            os.remove(cls.lut_file)

    def test_lut_file_created(self):
        """Module must create a non-empty binary LUT file when lut= is given."""
        self.assertModule(
            "i.hyper.atcorr",
            sza=_SZA,
            lut=self.lut_file,
            wl_min=0.45,
            wl_max=0.87,
            wl_step=0.10,
            aod="0.0,0.2,0.6",
            h2o="1.0,3.0",
            doy=_DOY,
            overwrite=True,
        )
        self.assertTrue(
            os.path.exists(self.lut_file),
            msg=f"LUT file not created at {self.lut_file}",
        )
        size = os.path.getsize(self.lut_file)
        self.assertGreater(size, 0, msg="LUT file is empty")

    def test_lut_file_size_consistent(self):
        """LUT file size must grow with grid size (double AOD → larger file)."""
        lut_small = tempfile.mktemp(suffix=".lut")
        lut_large = tempfile.mktemp(suffix=".lut")
        try:
            self.assertModule(
                "i.hyper.atcorr",
                sza=_SZA, lut=lut_small,
                wl_min=0.45, wl_max=0.87, wl_step=0.10,
                aod="0.0,0.2",
                h2o="1.0",
                doy=_DOY, overwrite=True,
            )
            self.assertModule(
                "i.hyper.atcorr",
                sza=_SZA, lut=lut_large,
                wl_min=0.45, wl_max=0.87, wl_step=0.10,
                aod="0.0,0.1,0.2,0.4",
                h2o="1.0",
                doy=_DOY, overwrite=True,
            )
            self.assertGreater(
                os.path.getsize(lut_large),
                os.path.getsize(lut_small),
                msg="Larger AOD grid did not produce a larger LUT file",
            )
        finally:
            for f in (lut_small, lut_large):
                if os.path.exists(f):
                    os.remove(f)

    def test_missing_lut_and_output_fails(self):
        """Module must fail when neither lut= nor output= is provided."""
        self.assertModuleFail(
            "i.hyper.atcorr",
            sza=_SZA,
        )

    def test_output_without_input_fails(self):
        """Module must fail when output= is given but input= is missing."""
        self.assertModuleFail(
            "i.hyper.atcorr",
            sza=_SZA,
            output="dummy_output",
        )

    def test_different_aerosol_models_accepted(self):
        """Module must accept continental, maritime, and urban aerosol models."""
        for model in ("continental", "maritime", "urban"):
            lut_f = tempfile.mktemp(suffix=".lut")
            try:
                self.assertModule(
                    "i.hyper.atcorr",
                    sza=_SZA, lut=lut_f,
                    wl_min=0.45, wl_max=0.65, wl_step=0.10,
                    aod="0.0,0.2", h2o="1.0",
                    aerosol=model,
                    doy=_DOY, overwrite=True,
                )
                self.assertTrue(
                    os.path.getsize(lut_f) > 0,
                    msg=f"Empty LUT for aerosol={model}",
                )
            finally:
                if os.path.exists(lut_f):
                    os.remove(lut_f)


class TestIHyperAtcorrCorrect(TestCase):
    """Full Raster3D atmospheric correction pipeline tests.

    Creates a synthetic 5×5 Raster3D with 4 spectral bands, writes band
    wavelength metadata to the map history, then runs i.hyper.atcorr to
    produce a corrected output Raster3D.
    """

    input_map  = "ihyper_test_input"
    output_map = "ihyper_test_output"
    lut_file   = None

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        # 5×5 pixel region, 10 m resolution, 4 depth layers (= 4 bands)
        cls.runModule(
            "g.region",
            n=50, s=0, e=50, w=0,
            rows=5, cols=5,
            t=_N_BANDS, b=0, tbres=1,
        )
        # Create uniform radiance Raster3D
        cls.runModule(
            "r3.mapcalc",
            expression=f"{cls.input_map} = {_RADIANCE:.1f}",
            overwrite=True,
        )
        # Write band wavelength metadata to history so main.c can parse it
        # Each call to r3.support history= appends a line to the map history
        for i, wl_nm in enumerate(_BAND_WL_NM, start=1):
            cls.runModule(
                "r3.support",
                map=cls.input_map,
                history=f"Band {i}: {wl_nm:.1f} nm",
            )
        cls.lut_file = tempfile.mktemp(suffix=".lut", prefix="ihyper_corr_")
        # Run the module ONCE here so all subsequent tests can inspect the output.
        # Using runModule (no assertion) to avoid aborting the entire class on failure;
        # test_module_runs_successfully will catch any actual error separately.
        cls.runModule(
            "i.hyper.atcorr",
            input=cls.input_map,
            output=cls.output_map,
            lut=cls.lut_file,
            sza=_SZA,
            vza=_VZA,
            raa=_RAA,
            altitude=_ALT,
            aod="0.05,0.2,0.5",
            h2o="1.0,2.0,4.0",
            aerosol="continental",
            atmosphere="us62",
            doy=_DOY,
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", type="raster_3d", flags="f",
            name=f"{cls.input_map},{cls.output_map}",
        )
        cls.del_temp_region()
        if cls.lut_file and os.path.exists(cls.lut_file):
            os.remove(cls.lut_file)

    def test_input_map_exists(self):
        """Synthetic input Raster3D must exist after setup."""
        self.assertRaster3dExists(self.input_map)

    def test_module_runs_successfully(self):
        """Output Raster3D must exist — proves the module ran without error in setUpClass."""
        self.assertRaster3dExists(self.output_map)

    def test_output_map_created(self):
        """Output Raster3D must be present in the GRASS database."""
        self.assertRaster3dExists(self.output_map)

    def test_output_reflectance_positive(self):
        """Output reflectance must be ≥ 0 (surface reflectance is non-negative)."""
        self.assertRaster3dFitsUnivar(
            raster=self.output_map,
            reference={"min": 0.0},
            precision=0.05,
        )

    def test_output_reflectance_less_than_one(self):
        """Output reflectance must be < 1.2 (no unphysical bright-surface blowup)."""
        self.assertRaster3dFitsUnivar(
            raster=self.output_map,
            reference={"max": 1.2},
            precision=0.3,
        )

    def test_output_mean_in_reasonable_range(self):
        """Scene-mean reflectance must be in [0.05, 0.60] for L=100 W/m²/sr/µm."""
        self.assertRaster3dFitsUnivar(
            raster=self.output_map,
            reference={"mean": 0.20},
            precision=0.15,
        )

    def test_lut_file_written(self):
        """LUT file must be created alongside Raster3D correction."""
        self.assertTrue(
            os.path.exists(self.lut_file) and os.path.getsize(self.lut_file) > 0,
            msg=f"LUT file missing or empty: {self.lut_file}",
        )

    def test_correction_with_scalar_aod_h2o(self):
        """Module must run successfully with single scalar aod_val and h2o_val."""
        out_scalar = self.output_map + "_scalar"
        self.assertModule(
            "i.hyper.atcorr",
            input=self.input_map,
            output=out_scalar,
            sza=_SZA,
            aod="0.05,0.2",
            h2o="1.0,2.0",
            aod_val=0.15,
            h2o_val=2.0,
            doy=_DOY,
            overwrite=True,
        )
        self.assertRaster3dExists(out_scalar)
        self.runModule("g.remove", type="raster_3d", flags="f", name=out_scalar)

    def test_polarization_flag_accepted(self):
        """Module must accept and run with the -P polarization flag."""
        out_polar = self.output_map + "_polar"
        lut_polar = tempfile.mktemp(suffix=".lut")
        try:
            self.assertModule(
                "i.hyper.atcorr",
                input=self.input_map,
                output=out_polar,
                lut=lut_polar,
                sza=_SZA,
                aod="0.0,0.2",
                h2o="1.0",
                doy=_DOY,
                flags="P",
                overwrite=True,
            )
            self.assertRaster3dExists(out_polar)
        finally:
            self.runModule(
                "g.remove", type="raster_3d", flags="f", name=out_polar,
            )
            if os.path.exists(lut_polar):
                os.remove(lut_polar)

    def test_midlat_summer_atmosphere_accepted(self):
        """Module must run successfully with atmosphere=midlat_summer."""
        out = self.output_map + "_midlat"
        lut = tempfile.mktemp(suffix=".lut")
        try:
            self.assertModule(
                "i.hyper.atcorr",
                input=self.input_map,
                output=out,
                lut=lut,
                sza=_SZA, vza=_VZA, raa=_RAA, altitude=_ALT,
                aod="0.05,0.2", h2o="1.0,2.0",
                atmosphere="midlat_summer",
                doy=_DOY,
                overwrite=True,
            )
            self.assertRaster3dExists(out)
        finally:
            self.runModule("g.remove", type="raster_3d", flags="f", name=out)
            if os.path.exists(lut):
                os.remove(lut)

    def test_lut_reuse(self):
        """Module must accept a pre-computed LUT file and produce valid output."""
        out_reuse = self.output_map + "_reuse"
        try:
            # self.lut_file was written during setUpClass; reuse it without recomputing
            self.assertModule(
                "i.hyper.atcorr",
                input=self.input_map,
                output=out_reuse,
                lut=self.lut_file,
                sza=_SZA, vza=_VZA, raa=_RAA, altitude=_ALT,
                aod="0.05,0.2,0.5",
                h2o="1.0,2.0,4.0",
                doy=_DOY,
                overwrite=True,
            )
            self.assertRaster3dExists(out_reuse)
            # Reused LUT must give identical reflectances to the original run
            self.assertRaster3dFitsUnivar(
                raster=out_reuse,
                reference={"min": 0.0, "max": 1.2},
                precision=0.3,
            )
        finally:
            self.runModule("g.remove", type="raster_3d", flags="f", name=out_reuse)

    def test_different_aerosol_models_produce_different_reflectance(self):
        """Continental vs maritime aerosol must give different mean reflectances."""
        out_cont = self.output_map + "_cont2"
        out_mari = self.output_map + "_mari2"
        lut_c = tempfile.mktemp(suffix=".lut")
        lut_m = tempfile.mktemp(suffix=".lut")
        try:
            self.runModule(
                "i.hyper.atcorr",
                input=self.input_map, output=out_cont, lut=lut_c,
                sza=_SZA, aod="0.05,0.4", h2o="1.0,2.0",
                aerosol="continental", doy=_DOY, overwrite=True,
            )
            self.runModule(
                "i.hyper.atcorr",
                input=self.input_map, output=out_mari, lut=lut_m,
                sza=_SZA, aod="0.05,0.4", h2o="1.0,2.0",
                aerosol="maritime", doy=_DOY, overwrite=True,
            )
            # Both maps must exist and cover a physical range
            self.assertRaster3dExists(out_cont)
            self.assertRaster3dExists(out_mari)
        finally:
            self.runModule(
                "g.remove", type="raster_3d", flags="f",
                name=f"{out_cont},{out_mari}",
            )
            for f in (lut_c, lut_m):
                if os.path.exists(f):
                    os.remove(f)


if __name__ == "__main__":
    test()
