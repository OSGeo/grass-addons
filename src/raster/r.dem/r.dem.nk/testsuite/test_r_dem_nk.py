#!/usr/bin/env python3

"""MODULE:    Test of r.dem.nk

AUTHOR(S): Corey T. White

PURPOSE:   Integration tests for r.dem.nk (Nuth & Kääb coregistration)

COPYRIGHT: (C) 2026 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestRDemNk(TestCase):
    """Test case for r.dem.nk"""

    tmp = gs.tempname(12)

    @classmethod
    def setUpClass(cls):
        gs.use_temp_region()
        # Small region for quick test (avoid edges for slope/aspect)
        gs.run_command("g.region", n=1000, s=0, e=1000, w=0, res=10)

        cls.lidar = f"lidar_{cls.tmp}"
        cls.sfm = f"sfm_{cls.tmp}"
        cls.stable = f"stable_{cls.tmp}"

        # Create a DEM with enough relief to avoid near-zero slopes.
        # Using both linear gradient and sinusoidal components.
        gs.mapcalc(
            (
                "{lidar} = 100 + 0.7*col() + 0.4*row() "
                "+ 2.0*sin(col()/4.0) + 1.5*cos(row()/5.0)"
            ).format(lidar=cls.lidar),
            overwrite=True,
        )

        # Stable terrain mask: exclude the outer 1-cell border.
        gs.mapcalc(
            (
                "{stable} = if(row() > 1 && row() < rows() "
                "&& col() > 1 && col() < cols(), 1, null())"
            ).format(stable=cls.stable),
            overwrite=True,
        )

        # Create a synthetic SfM raster as a shifted+biased version of LiDAR.
        # SfM(x,y) = LiDAR(x-dx, y-dy) + dz
        cls.dx = 3.2  # meters east
        cls.dy = -1.7  # meters north
        cls.dz = 5.0  # meters vertical

        # Build lidar_shift by resampling lidar to a region shifted by (-dx, -dy),
        # then resample back to base region.
        reg = gs.parse_command("g.region", flags="g")
        n = float(reg["n"])
        s = float(reg["s"])
        e = float(reg["e"])
        w = float(reg["w"])
        res = float(reg.get("nsres") or reg.get("res"))

        lidar_shift = f"lidar_shift_{cls.tmp}"
        sfm_nodz = f"sfm_nodz_{cls.tmp}"

        gs.run_command(
            "g.region",
            n=n - cls.dy,
            s=s - cls.dy,
            e=e - cls.dx,
            w=w - cls.dx,
            res=res,
        )
        gs.run_command(
            "r.resamp.interp",
            input=cls.lidar,
            output=lidar_shift,
            method="bilinear",
            overwrite=True,
        )
        gs.run_command("g.region", n=n, s=s, e=e, w=w, res=res)
        gs.run_command(
            "r.resamp.interp",
            input=lidar_shift,
            output=sfm_nodz,
            method="bilinear",
            overwrite=True,
        )

        gs.mapcalc(
            "{sfm} = {sfm_nodz} + {dz}".format(
                sfm=cls.sfm, sfm_nodz=sfm_nodz, dz=cls.dz
            ),
            overwrite=True,
        )

        # Cleanup construction helpers in mapset (kept only for test runtime)
        gs.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=",".join([lidar_shift, sfm_nodz]),
            quiet=True,
        )

    @classmethod
    def tearDownClass(cls):
        gs.run_command(
            "g.remove",
            flags="f",
            quiet=True,
            type="raster",
            pattern=f"*{cls.tmp}*",
        )
        gs.del_temp_region()

    def test_residual_improves(self):
        """Final residual mean/stddev should improve significantly."""
        out = f"out_{self.tmp}"

        # Baseline residual before coregistration (masked stable).
        resid0 = f"resid0_{self.tmp}"
        gs.mapcalc(
            "{r} = if({m}, {sfm} - {lidar}, null())".format(
                r=resid0, m=self.stable, sfm=self.sfm, lidar=self.lidar
            ),
            overwrite=True,
        )

        stats0 = gs.parse_command("r.univar", flags="g", map=resid0)
        mean0 = float(stats0["mean"])
        std0 = float(stats0["stddev"])

        nk = SimpleModule(
            "r.dem.nk",
            sfm=self.sfm,
            lidar=self.lidar,
            stable_mask=self.stable,
            output=out,
            interp="bilinear",
            slope_min=0.0,
            slope_max=89.0,
            iters=1,
            sigma=2.5,
            overwrite=True,
            quiet=True,
        )
        self.assertModule(nk)

        self.assertRasterExists(out)
        self.assertRasterExists(f"{out}_resid")

        stats1 = gs.parse_command("r.univar", flags="g", map=f"{out}_resid")
        mean1 = float(stats1["mean"])
        std1 = float(stats1["stddev"])

        # Baseline should reflect the applied dz and shift.
        self.assertGreater(abs(mean0), 1.0)
        self.assertGreater(std0, 0.2)

        # After coregistration, residuals should be near zero.
        self.assertLess(abs(mean1), 0.5)
        self.assertLess(std1, 0.5)
        # and should improve compared to baseline.
        self.assertLess(abs(mean1), abs(mean0))
        self.assertLess(std1, std0)

        gs.run_command(
            "g.remove",
            flags="f",
            quiet=True,
            type="raster",
            name=",".join([out, f"{out}_resid", resid0]),
        )

    def test_keep_intermediates(self):
        """-k should write slope/aspect/mask helper rasters."""
        out = f"outk_{self.tmp}"
        nk = SimpleModule(
            "r.dem.nk",
            flags="k",
            sfm=self.sfm,
            lidar=self.lidar,
            stable_mask=self.stable,
            output=out,
            interp="nearest",
            slope_min=0.0,
            slope_max=89.0,
            iters=0,
            sigma=2.5,
            overwrite=True,
            quiet=True,
        )
        self.assertModule(nk)

        self.assertRasterExists(out)
        self.assertRasterExists(f"{out}_resid")
        self.assertRasterExists(f"{out}_slope")
        self.assertRasterExists(f"{out}_aspect")
        self.assertRasterExists(f"{out}_mask")

        gs.run_command(
            "g.remove",
            flags="f",
            quiet=True,
            type="raster",
            name=",".join(
                [
                    out,
                    f"{out}_resid",
                    f"{out}_slope",
                    f"{out}_aspect",
                    f"{out}_mask",
                ]
            ),
        )


if __name__ == "__main__":
    test()
