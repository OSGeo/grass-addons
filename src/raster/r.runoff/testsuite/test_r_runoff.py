import os
import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRRunoffOutlets(TestCase):
    """
    outlet-based verification for r.runoff (depth-only + routed tp).

    steps:
    1)  Import CN and PCP from ASCII (cn.txt, pcp.txt) into rasters 'cn' and
        'pcp' (assuming test is being run on NC sample dataset and elevation
        raster exists in the workspace.
    2)  Derive flow direction and streams with r.watershed (threshold=10).
    3)  Compute tc with r.timeofconcentration (length_min=100).
    4)  Run r.runoff with routing (duration=1, lambda=0.2) to produce
        runoff_depth and ttp.
    5)  Sample three outlets and compare runoff_depth (mm) and ttp (h) to
        standard values calculated manually.
    """

    # inputs (files in testsuite folder)
    cn_txt = "cn.txt"
    pcp_txt = "pcp.txt"

    # rasters created in-mapset
    elev = "elevation"
    cn = "cn"
    pcp = "pcp"
    fdr = "fdr"
    strm = "str"
    tc = "tc"
    qd = "runoff_depth"
    tp = "ttp"

    # (x, y, expected_Q_mm, expected_tp_h)
    outlets = [
        (644725.19049303, 223429.84212000752, 15.08, 0.64),
        (644194.7613471923, 223105.18360157238, 54.51, 0.69),
        (644585.0175849941, 223267.60257913248, 2.87, 0.63),
    ]

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.addClassCleanup(cls.del_temp_region)

        # import cn/pcp ascii from the testsuite directory
        here = os.path.dirname(__file__)
        cn_path = os.path.join(here, cls.cn_txt)
        pcp_path = os.path.join(here, cls.pcp_txt)

        # check for files
        if not os.path.exists(cn_path):
            raise RuntimeError(f"missing test input: {cn_path}")
        if not os.path.exists(pcp_path):
            raise RuntimeError(f"missing test input: {pcp_path}")

        # import as GRASS ASCII rasters
        cls.runModule("r.in.ascii", input=pcp_path, output=cls.pcp, overwrite=True)
        cls.runModule("r.in.ascii", input=cn_path, output=cls.cn, overwrite=True)

        # set region to rainfall grid
        cls.runModule("g.region", raster=cls.pcp)

        # prereqs: direction, streams, tc
        cls.runModule(
            "r.watershed",
            elevation=cls.elev,
            drainage=cls.fdr,
            stream=cls.strm,
            threshold=10,
            overwrite=True,
        )
        cls.runModule(
            "r.timeofconcentration",
            elevation=cls.elev,
            direction=cls.fdr,
            streams=cls.strm,
            time_concentration=cls.tc,
            length_min=100,
            overwrite=True,
        )

        # cleanup at the end
        def _cleanup():
            rasters = [
                cls.cn,
                cls.pcp,
                cls.fdr,
                cls.strm,
                cls.tc,
                cls.qd,
                cls.tp,
            ]
            existing = [r for r in rasters if gs.find_file(r, element="cell")["name"]]
            if existing:
                cls.runModule(
                    "g.remove",
                    type="raster",
                    name=",".join(existing),
                    flags="f",
                    quiet=True,
                )

        cls.addClassCleanup(_cleanup)

    def _sample(self, rast, x, y):
        out = gs.read_command("r.what", map=rast, coordinates=f"{x},{y}", flags="n")
        lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
        if not lines:
            self.fail(f"no r.what output for {rast} at {x},{y}")
        parts = lines[-1].split("|")
        if len(parts) < 4:
            self.fail(f"unexpected r.what output for {rast} at {x},{y}: {lines[-1]}")
        val = parts[3]
        if val in ("*", "", "NULL", "null"):
            self.fail(f"NULL at {rast} {x},{y}: {lines[-1]}")
        return float(val)

    def test_runoff_depth_and_ttp_at_outlets(self):
        # routed run
        self.assertModule(
            "r.runoff",
            rainfall=self.pcp,
            duration=1,
            curve_number=self.cn,
            direction=self.fdr,
            lambda_=0.2,
            time_concentration=self.tc,
            runoff_depth=self.qd,
            time_to_peak=self.tp,
            overwrite=True,
        )

        q_abs_tol = 0.10  # mm absolute tolerance
        tp_abs_tol = 0.05  # hours (3 minutes)

        for x, y, q_exp, tp_exp in self.outlets:
            q_got = self._sample(self.qd, x, y)
            tp_got = self._sample(self.tp, x, y)

            # runoff depth checks
            self.assertLessEqual(
                abs(q_got - q_exp),
                q_abs_tol,
                msg=(
                    f"runoff_depth diff > {q_abs_tol} mm at {x},{y}: "
                    f"got {q_got}, expected {q_exp}"
                ),
            )
            self.assertEqual(
                round(q_got, 2),
                round(q_exp, 2),
                msg=(
                    f"runoff_depth mismatch at {x},{y}: "
                    f"got {round(q_got, 2)} (raw {q_got}), "
                    f"expected {round(q_exp, 2)}"
                ),
            )

            # ttp checks
            self.assertLessEqual(
                abs(tp_got - tp_exp),
                tp_abs_tol,
                msg=(
                    f"ttp diff > {tp_abs_tol} h at {x},{y}: "
                    f"got {tp_got}, expected {tp_exp}"
                ),
            )
            self.assertEqual(
                round(tp_got, 2),
                round(tp_exp, 2),
                msg=(
                    f"ttp mismatch at {x},{y}: "
                    f"got {round(tp_got, 2)} (raw {tp_got}), "
                    f"expected {round(tp_exp, 2)}"
                ),
            )


if __name__ == "__main__":
    test()
