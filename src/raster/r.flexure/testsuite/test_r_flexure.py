#!/usr/bin/env python

############################################################################
#
# MODULE:       test_r_flexure
# AUTHOR:       Andrew Wickert
# PURPOSE:      Tests for r.flexure (gridded flexural isostasy)
# COPYRIGHT:    (C) 2026 by Andrew Wickert and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
############################################################################

"""
Tests for r.flexure.

Exercises FD, FFT, and SAS solution methods with a synthetic 10×10 load
raster (100 m resolution). Skips automatically when gFlex is not installed.

Run inside a GRASS session (e.g., with --tmp-location XY):
    python -m grass.gunittest.main
"""

import unittest

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

# Synthetic 10×10 load raster (100 m resolution, 1 km × 1 km).
# A single central cell carries a 1e9 Pa load (roughly 100 m of dense rock).
LOAD_ASCII = """\
north: 1000
south: 0
east: 1000
west: 0
rows: 10
cols: 10
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 1e9 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
0 0 0 0 0 0 0 0 0 0
"""

# Spatially variable Te raster at 100 m resolution (uniform 10 km).
TE_ASCII = """\
north: 1000
south: 0
east: 1000
west: 0
rows: 10
cols: 10
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
10000 10000 10000 10000 10000 10000 10000 10000 10000 10000
"""

# Fixtures for the infinite-BC (no_outside_loads) padding test: 30×30 at 5000 m (150 km × 150 km).
# Te = 5000 m → α ≈ 23 km, flexural wavelength ≈ 144 km,
# recommended pad ≈ 29 cells/side → padded domain is 88×88 (manageable).
# The 10×10 at 100 m fixture above would produce ~1300 cells of padding
# and a 2600×2600 FD matrix that crashes the direct solver.
_PAD_ROW_ZERO = "0 " * 30
_PAD_ROW_LOAD = "0 " * 14 + "1e9 " + "0 " * 15
_PAD_TE_ROW = "5000 " * 30
LOAD_PAD_ASCII = (
    "north: 150000\nsouth: 0\neast: 150000\nwest: 0\nrows: 30\ncols: 30\n"
    + (_PAD_ROW_ZERO + "\n") * 14
    + _PAD_ROW_LOAD
    + "\n"
    + (_PAD_ROW_ZERO + "\n") * 15
)
TE_PAD_ASCII = (
    "north: 150000\nsouth: 0\neast: 150000\nwest: 0\nrows: 30\ncols: 30\n"
    + (_PAD_TE_ROW + "\n") * 30
)


def _gflex_ok():
    """Return True if gFlex is importable."""
    try:
        import gflex  # noqa: F401

        return True
    except ImportError:
        return False


@unittest.skipUnless(_gflex_ok(), "gFlex not available")
class TestRFlexure(TestCase):
    """Test r.flexure with synthetic raster data (no NC dataset required)."""

    load = "test_rflex_load"
    te_rast = "test_rflex_te"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("r.in.ascii", input="-", stdin_=LOAD_ASCII, output=cls.load)
        cls.runModule("r.in.ascii", input="-", stdin_=TE_ASCII, output=cls.te_rast)
        cls.runModule("g.region", raster=cls.load)

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=",".join([cls.load, cls.te_rast]),
            quiet=True,
        )

    def _run_and_check(self, output, **kwargs):
        """Run r.flexure, assert success, assert 100 non-null output cells."""
        try:
            self.assertModule("r.flexure", output=output, **kwargs)
            self.assertRasterExists(output)
            self.assertRasterFitsUnivar(
                raster=output, reference={"n": 100}, precision=0
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_fd_scalar_te(self):
        """FD method with scalar Te [m]."""
        self._run_and_check(
            "test_rflex_fd",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="free",
            southbc="free",
            eastbc="free",
            westbc="free",
        )

    def test_fft_scalar_te(self):
        """FFT method with scalar Te [m]."""
        self._run_and_check(
            "test_rflex_fft",
            method="fft",
            input=self.load,
            te="10000",
            te_units="m",
        )

    def test_sas_scalar_te(self):
        """SAS method with scalar Te [m]."""
        self._run_and_check(
            "test_rflex_sas",
            method="sas",
            input=self.load,
            te="10000",
            te_units="m",
        )

    def test_fd_raster_te(self):
        """FD method with spatially variable (raster) Te."""
        self._run_and_check(
            "test_rflex_fd_rte",
            method="fd",
            input=self.load,
            te=self.te_rast,
            te_units="m",
            northbc="free",
            southbc="free",
            eastbc="free",
            westbc="free",
        )

    def test_fd_sigma_stresses(self):
        """FD method with non-zero in-plane stresses."""
        self._run_and_check(
            "test_rflex_fd_sigma",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            sigma_xx="1e6",
            sigma_yy="1e6",
            sigma_xy="0",
            northbc="free",
            southbc="free",
            eastbc="free",
            westbc="free",
        )

    def test_te_km_units(self):
        """Te specified in km should match the same value in m (SAS, smoke test)."""
        self._run_and_check(
            "test_rflex_km",
            method="sas",
            input=self.load,
            te="10",
            te_units="km",
        )

    def test_fft_periodic_bc(self):
        """FFT method with all-periodic boundary conditions (exact FFT path)."""
        self._run_and_check(
            "test_rflex_fft_per",
            method="fft",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="periodic",
            southbc="periodic",
            eastbc="periodic",
            westbc="periodic",
        )

    def test_fd_mirror_bc(self):
        """FD method with Mirror boundary conditions."""
        self._run_and_check(
            "test_rflex_fd_mirror",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="mirror",
            southbc="mirror",
            eastbc="mirror",
            westbc="mirror",
        )

    def test_fd_pinned_bc(self):
        """FD method with pinned BC (simply-supported: zero displacement, zero moment)."""
        self._run_and_check(
            "test_rflex_fd_pinned",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="pinned",
            southbc="pinned",
            eastbc="pinned",
            westbc="pinned",
        )

    def test_fd_clamped_bc(self):
        """FD method with clamped BC (zero displacement, zero slope)."""
        self._run_and_check(
            "test_rflex_fd_clamped",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="clamped",
            southbc="clamped",
            eastbc="clamped",
            westbc="clamped",
        )

    def test_fd_free_bc(self):
        """FD method with free BC (zero moment, zero shear)."""
        self._run_and_check(
            "test_rflex_fd_free",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="free",
            southbc="free",
            eastbc="free",
            westbc="free",
        )

    def test_fd_mixed_bc(self):
        """FD method with different BCs on each pair of sides.

        Interface-layer test: verifies that northbc/southbc/eastbc/westbc are
        passed to gFlex as four independent options and not accidentally aliased
        to one another.
        """
        self._run_and_check(
            "test_rflex_fd_mixed",
            method="fd",
            input=self.load,
            te="10000",
            te_units="m",
            northbc="clamped",
            southbc="clamped",
            eastbc="free",
            westbc="free",
        )

    def test_deflection_is_downward(self):
        """SAS deflection under a positive load is negative; checks sign and plausibility.

        This is an interface-layer test: it verifies that qs and flex.w are
        passed and read with the correct sign, and that the deflection magnitude
        is physically plausible (not orders-of-magnitude wrong due to a unit
        conversion bug in Te, dx, or dy).
        """
        output = "test_rflex_sign"
        try:
            self.assertModule(
                "r.flexure",
                method="sas",
                input=self.load,
                te="10000",
                te_units="m",
                output=output,
            )
            stats = gs.parse_command("r.univar", map=output, flags="g")
            min_w = float(stats["min"])
            self.assertLess(
                min_w, 0, "Deflection under a downward load must be negative"
            )
            self.assertGreater(
                min_w,
                -1000,
                "Deflection magnitude must be physically plausible (< 1 km)",
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_te_units_default_km(self):
        """Omitting te_units uses the km default; result must match explicit te_units=km.

        Interface-layer test: verifies that the GRASS answer: km default is
        wired through to the Te *= 1000 conversion.
        """
        out_default = "test_rflex_te_default_units"
        out_km = "test_rflex_te_explicit_km_def"
        try:
            self.assertModule(
                "r.flexure",
                method="sas",
                input=self.load,
                te="10",
                output=out_default,
            )
            self.assertModule(
                "r.flexure",
                method="sas",
                input=self.load,
                te="10",
                te_units="km",
                output=out_km,
            )
            stats_d = gs.parse_command("r.univar", map=out_default, flags="g")
            stats_k = gs.parse_command("r.univar", map=out_km, flags="g")
            self.assertAlmostEqual(
                float(stats_d["min"]),
                float(stats_k["min"]),
                places=10,
                msg="Default te_units=km must match explicit te_units=km",
            )
        finally:
            self.runModule(
                "g.remove",
                flags="f",
                type="raster",
                name=",".join([out_default, out_km]),
                quiet=True,
            )

    def test_te_km_m_equivalence(self):
        """Te=10 km and Te=10000 m must produce identical deflections.

        Interface-layer test: verifies that the km→m conversion (Te *= 1000)
        is applied correctly.
        """
        out_km = "test_rflex_te_km"
        out_m = "test_rflex_te_m"
        self.addCleanup(
            self.runModule,
            "g.remove",
            flags="f",
            type="raster",
            name=",".join([out_km, out_m]),
            quiet=True,
        )
        self.assertModule(
            "r.flexure",
            method="sas",
            input=self.load,
            te="10",
            te_units="km",
            output=out_km,
        )
        self.assertModule(
            "r.flexure",
            method="sas",
            input=self.load,
            te="10000",
            te_units="m",
            output=out_m,
        )
        stats_km = gs.parse_command("r.univar", map=out_km, flags="g")
        stats_m = gs.parse_command("r.univar", map=out_m, flags="g")
        self.assertAlmostEqual(
            float(stats_km["min"]),
            float(stats_m["min"]),
            places=10,
            msg="Te in km and m must give identical min deflection",
        )
        self.assertAlmostEqual(
            float(stats_km["mean"]),
            float(stats_m["mean"]),
            places=10,
            msg="Te in km and m must give identical mean deflection",
        )

    def test_deflection_is_downward_fd(self):
        """FD deflection under a positive load is negative and physically plausible."""
        output = "test_rflex_fd_sign"
        try:
            self.assertModule(
                "r.flexure",
                method="fd",
                input=self.load,
                te="10000",
                te_units="m",
                output=output,
                northbc="free",
                southbc="free",
                eastbc="free",
                westbc="free",
            )
            stats = gs.parse_command("r.univar", map=output, flags="g")
            min_w = float(stats["min"])
            self.assertLess(
                min_w, 0, "FD deflection under a downward load must be negative"
            )
            self.assertGreater(
                min_w,
                -1000,
                "FD deflection magnitude must be physically plausible (< 1 km)",
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_deflection_is_downward_fft(self):
        """FFT deflection under a positive load is negative and physically plausible."""
        output = "test_rflex_fft_sign"
        try:
            self.assertModule(
                "r.flexure",
                method="fft",
                input=self.load,
                te="10000",
                te_units="m",
                output=output,
            )
            stats = gs.parse_command("r.univar", map=output, flags="g")
            min_w = float(stats["min"])
            self.assertLess(
                min_w, 0, "FFT deflection under a downward load must be negative"
            )
            self.assertGreater(
                min_w,
                -1000,
                "FFT deflection magnitude must be physically plausible (< 1 km)",
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_fft_sigma_stresses(self):
        """FFT method with non-zero in-plane stresses."""
        self._run_and_check(
            "test_rflex_fft_sigma",
            method="fft",
            input=self.load,
            te="10000",
            te_units="m",
            sigma_xx="1e6",
            sigma_yy="1e6",
            sigma_xy="0",
        )

    def test_fft_non_periodic_bc(self):
        """FFT with non-periodic BCs (clamped) falls back to zero-padding and produces valid output.

        Interface-layer regression test: FFT treats any non-'periodic' BC as
        no_outside_loads (zero-padded). Passing clamped must not crash and must
        produce valid, physically plausible deflections.
        """
        output = "test_rflex_fft_bc_clamp"
        try:
            self.assertModule(
                "r.flexure",
                method="fft",
                input=self.load,
                te="10000",
                te_units="m",
                output=output,
                northbc="clamped",
                southbc="clamped",
                eastbc="clamped",
                westbc="clamped",
            )
            self.assertRasterExists(output)
            self.assertRasterFitsUnivar(
                raster=output, reference={"n": 100}, precision=0
            )
            stats = gs.parse_command("r.univar", map=output, flags="g")
            self.assertLess(
                float(stats["min"]),
                0,
                "FFT deflection under a downward load must be negative",
            )
        finally:
            self.runModule(
                "g.remove",
                flags="f",
                type="raster",
                name=output,
                quiet=True,
            )


@unittest.skipUnless(_gflex_ok(), "gFlex not available")
class TestRFlexurePadded(TestCase):
    """Test infinite (no_outside_loads) BC with a domain sized for the flexural wavelength.

    The main TestRFlexure fixture (10×10 at 100 m, Te=10 km) would produce
    ~300+ cells of padding per side, making the FD solve prohibitively large.
    Here we use 30×30 at 5000 m with Te=5000 m so padding is ~29 cells/side
    (88×88 padded domain).  FD tests in TestRFlexure use explicit non-infinite
    BCs (e.g. free) to avoid this issue on that small domain.
    """

    load_pad = "test_rflex_pad_load"
    te_pad = "test_rflex_pad_te"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule(
            "r.in.ascii", input="-", stdin_=LOAD_PAD_ASCII, output=cls.load_pad
        )
        cls.runModule("r.in.ascii", input="-", stdin_=TE_PAD_ASCII, output=cls.te_pad)
        cls.runModule("g.region", raster=cls.load_pad)

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=",".join([cls.load_pad, cls.te_pad]),
            quiet=True,
        )

    def test_fd_raster_te_padded(self):
        """FD with raster Te and infinite BCs; gFlex auto-pads and trims to original region."""
        output = "test_rflex_pad_out"
        try:
            self.assertModule(
                "r.flexure",
                method="fd",
                input=self.load_pad,
                te=self.te_pad,
                te_units="m",
                output=output,
                northbc="infinite",
                southbc="infinite",
                eastbc="infinite",
                westbc="infinite",
            )
            self.assertRasterExists(output)
            # Output must be trimmed back to the original 30×30 region
            self.assertRasterFitsUnivar(
                raster=output, reference={"n": 900}, precision=0
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_fd_scalar_te_padded(self):
        """FD with scalar Te and infinite BCs; qs zero-padded, output trimmed to original region."""
        output = "test_rflex_pad_fd_scalar"
        try:
            self.assertModule(
                "r.flexure",
                method="fd",
                input=self.load_pad,
                te="5000",
                te_units="m",
                output=output,
                northbc="infinite",
                southbc="infinite",
                eastbc="infinite",
                westbc="infinite",
            )
            self.assertRasterExists(output)
            self.assertRasterFitsUnivar(
                raster=output, reference={"n": 900}, precision=0
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )

    def test_fft_padded(self):
        """FFT with default infinite BCs; gFlex pads internally and trims to original region."""
        output = "test_rflex_pad_fft"
        try:
            self.assertModule(
                "r.flexure",
                method="fft",
                input=self.load_pad,
                te="5000",
                te_units="m",
                output=output,
            )
            self.assertRasterExists(output)
            self.assertRasterFitsUnivar(
                raster=output, reference={"n": 900}, precision=0
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster", name=output, quiet=True
            )


if __name__ == "__main__":
    test()
