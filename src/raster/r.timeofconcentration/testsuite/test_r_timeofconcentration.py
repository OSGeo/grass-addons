import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRTimeOfConcentrationOutlets(TestCase):
    """
    outlet-based Tc verification.

    For these five outlets, flow-path length was computed with r.lfp and the
    Kirpich equation was solved manually on a calculator to obtain Tc. This
    test runs r.timeofconcentration on the NC dataset, samples Tc at the same
    outlet coordinates, and checks that the raster values match the manual Tc
    within the allowed tolerance (honoring length_min, slope_min, and
    vertical_units, and rounding off error in the manual calculation).
    """

    elev = "elevation"
    fdr = "toc_fdr"
    streams = "toc_streams"
    tcmap = "toc_out"
    Lmap = "toc_L"
    DZmap = "toc_DZ"
    Smap = "toc_S"

    # (x, y, expected_tc)
    outlets = [
        (644725.2656813094, 223429.86091688852, 6.87),
        (644726.739122, 221924.00112902367, 0.84),
        (644726.7327240475, 222778.60964092897, 0.74),
        (643609.8453361894, 222825.7149632604, 1.00),
        (643499.3692589527, 222777.12340402367, 0.32),
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.addClassCleanup(cls.del_temp_region)

        # full nc region
        cls.runModule("g.region", raster=cls.elev)

        # external derivation of direction + streams
        cls.runModule(
            "r.watershed",
            elevation=cls.elev,
            drainage=cls.fdr,
            stream=cls.streams,
            threshold=10,
            overwrite=True,
        )

        def _cleanup():
            cls.runModule(
                "g.remove",
                type="raster",
                name=",".join(
                    [
                        cls.fdr,
                        cls.streams,
                        cls.tcmap,
                        cls.Lmap,
                        cls.DZmap,
                        cls.Smap,
                    ]
                ),
                flags="f",
                quiet=True,
            )

        cls.addClassCleanup(_cleanup)

    def sample_tc(self, x, y):
        out = gs.read_command(
            "r.what",
            map=self.tcmap,
            coordinates=f"{x},{y}",
            flags="n",
        )
        lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
        if not lines:
            self.fail(f"no output from r.what for {x},{y}")

        data_line = lines[-1]
        parts = data_line.split("|")
        if len(parts) < 4:
            self.fail(f"unexpected r.what output for {x},{y}: {data_line}")

        val = parts[3]
        if val in ("*", "", "NULL", "null"):
            self.fail(f"no tc value at {x},{y} (got {data_line})")

        return float(val)

    def test_tc_at_outlets(self):
        # run with diagnostics so we can inspect when it fails
        self.assertModule(
            "r.timeofconcentration",
            elevation=self.elev,
            direction=self.fdr,
            streams=self.streams,
            time_concentration=self.tcmap,
            length=self.Lmap,
            drop=self.DZmap,
            sbar=self.Smap,
            overwrite=True,
        )

        max_diff = 1.0 / 60.0  # 1 minute

        for x, y, exp_tc in self.outlets:
            got = self.sample_tc(x, y)
            diff = abs(got - exp_tc)

            # 1) hard hydrologic bound
            self.assertLessEqual(
                diff,
                max_diff,
                msg=(
                    f"tc difference > 1 minute at {x},{y}: "
                    f"got {got}, expected {exp_tc}, diff={diff} h"
                ),
            )

            # 2) round-to-2dp agreement
            got_r = round(got, 2)
            exp_r = round(exp_tc, 2)
            self.assertEqual(
                got_r,
                exp_r,
                msg=(
                    f"tc mismatch at {x},{y}: got {got_r} (raw {got}), "
                    f"expected {exp_r} (raw {exp_tc})"
                ),
            )


if __name__ == "__main__":
    test()
