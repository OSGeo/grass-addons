import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRTimeOfConcentrationRegression(TestCase):
    """
    Regression test for r.timeofconcentration

    what it checks:
    verifies run-to-run stability: for a fixed region and inputs, repeated
    executions must produce identical output statistics. each scenario runs the
    module 'reps' times; run 1 becomes the baseline, and runs 2–reps must match
    its r.univar statistics (min, max, mean, stddev, sum) and non-null count.

    scenarios:
    1) baseline: flow accumulation threshold=10
    2) thr300: threshold=300
    3) smin: threshold=10, slope_min=0.01

    setup:
    - region is set to a fixed bbox (nc spm sample data)
    - flow direction (fdr) is derived from elevation using r.watershed
    - no external data are required beyond the nc sample data 'elevation'
      raster

    outputs:
    - no files are written; progress messages go through gs.message()
    - temporary rasters created by the test are removed via class cleanups

    how to run:
        python3 test_r_timeofconcentration.py
    """

    elev = "elevation"
    fdr = "fdr"
    acc_tmp = "acc_tmp"
    tc_base = "tc_base"
    tc_thr300 = "tc_thr300"
    tc_smin = "tc_smin"
    keys = ("min", "max", "mean", "stddev", "sum")
    places = 5
    reps = 3

    @classmethod
    def setUpClass(cls):
        # temp region for the whole test class
        cls.use_temp_region()
        cls.addClassCleanup(cls.del_temp_region)

        gs.message(
            _("running {n} scenarios with {r} runs each").format(n=3, r=cls.reps)
        )

        # fixed bbox; optionally pin resolution for precaution (e.g., res=10)
        cls.runModule(
            "g.region",
            w=642994.5376035355,
            e=644732.0679188052,
            s=221350.83582163436,
            n=223653.82393179316,
            # res=10,
        )

        # derive fdr once for all scenarios
        cls.runModule(
            "r.watershed",
            elevation=cls.elev,
            accumulation=cls.acc_tmp,
            drainage=cls.fdr,
            overwrite=True,
        )

        # ensure rasters are cleaned even if tests abort
        # tearDown class doesn't do it
        def _cleanup_maps():
            maps = [cls.acc_tmp, cls.fdr, cls.tc_base, cls.tc_thr300, cls.tc_smin]
            cls.runModule(
                "g.remove",
                flags="f",
                type="raster",
                name=",".join(maps),
                quiet=True,
            )

        cls.addClassCleanup(_cleanup_maps)

    def stats(self, rast):
        ge = gs.parse_command("r.univar", flags="ge", map=rast)
        g = gs.parse_command("r.univar", flags="g", map=rast)
        out = {k: float(ge[k]) for k in self.keys if k in ge}
        out["n"] = int(g["n"])
        return out

    def assert_same(self, base, cur, tag):
        for k in self.keys:
            self.assertAlmostEqual(
                base[k],
                cur[k],
                places=self.places,
                msg=_("{tag} {key} differs").format(tag=tag, key=k),
            )
        self.assertEqual(
            base["n"],
            cur["n"],
            msg=_("{tag} n differs").format(tag=tag),
        )

    def scenario(self, idx, label, kwargs, outmap):
        gs.message(
            _("running scenario {i}: run {r}/{R}").format(i=idx, r=1, R=self.reps)
        )
        self.assertModule(
            "r.timeofconcentration", time_concentration=outmap, overwrite=True, **kwargs
        )
        # sanity: output exists
        try:
            self.assertRasterExists(outmap)
        except AttributeError:
            ff = gs.find_file(name=outmap, element="cell")
            self.assertTrue(
                bool(ff and ff.get("name")),
                msg=_("output raster {m} missing").format(m=outmap),
            )
        base = self.stats(outmap)

        for i in range(2, self.reps + 1):
            gs.message(
                _("running scenario {idx}: run {r}/{R}").format(
                    idx=idx, r=i, R=self.reps
                )
            )
            self.assertModule(
                "r.timeofconcentration",
                time_concentration=outmap,
                overwrite=True,
                **kwargs,
            )
            try:
                self.assertRasterExists(outmap)
            except AttributeError:
                ff = gs.find_file(name=outmap, element="cell")
                self.assertTrue(
                    bool(ff and ff.get("name")),
                    msg=_("output raster {m} missing").format(m=outmap),
                )
            cur = self.stats(outmap)
            self.assert_same(base, cur, tag="{lbl} run{r}".format(lbl=label, r=i))

        gs.message(_("scenario {i} passed").format(i=idx))

    def test_01_baseline(self):
        self.scenario(
            1,
            "baseline",
            dict(elevation=self.elev, direction=self.fdr, threshold=10),
            self.tc_base,
        )

    def test_02_thr300(self):
        self.scenario(
            2,
            "thr300",
            dict(elevation=self.elev, direction=self.fdr, threshold=300),
            self.tc_thr300,
        )

    def test_03_smin(self):
        self.scenario(
            3,
            "smin",
            dict(elevation=self.elev, direction=self.fdr, threshold=10, slope_min=0.01),
            self.tc_smin,
        )


if __name__ == "__main__":
    test()
