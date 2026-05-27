"""Tests for r.richdem.dephier

Synthetic DEM (5 x 5, 1 m resolution):

    5 5 5 5 5
    5 3 3 3 5
    5 3 1 3 5   <- centre pit, elevation 1
    5 3 3 3 5
    5 5 5 5 5

Expected hierarchy properties:
  - One leaf depression: the inner 3 x 3 basin draining to the centre pit.
  - Pour-point elevation = 3 (lowest rim cell adjacent to a border cell).
  - Depression volume > 0 (centre cell is 2 m below the pour point).
  - Border cells drain directly to the DEM boundary (label 0 / OCEAN).
  - Flow directions are in [0, 7] for all non-pit cells.
"""

import unittest

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

try:
    import _richdem  # noqa: F401

    HAS_RICHDEM = True
except ImportError:
    HAS_RICHDEM = False

_DEM = "tmp_richdem_dephier_dem"
_LABELS = "tmp_richdem_dephier_labels"
_FLOWDIRS = "tmp_richdem_dephier_flowdirs"
_HIERARCHY = "tmp_richdem_dephier_hierarchy"

_DEM_EXPR = (
    "if(row()==3 && col()==3, 1,"
    " if(row()==1 || row()==5 || col()==1 || col()==5, 5, 3))"
)


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemDephier(TestCase):
    """Functional tests for r.richdem.dephier requiring the RichDEM extension."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=0, e=5, w=0, res=1)
        cls.runModule("r.mapcalc", expression=f"{_DEM} = {_DEM_EXPR}", overwrite=True)
        # Run once; individual tests query the outputs
        cls.runModule(
            "r.richdem.dephier",
            input=_DEM,
            output_labels=_LABELS,
            output_flowdirs=_FLOWDIRS,
            output_hierarchy=_HIERARCHY,
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[_DEM, _LABELS, _FLOWDIRS],
        )
        cls.runModule(
            "g.remove",
            flags="f",
            type="vector",
            name=[_HIERARCHY],
        )

    # --- output existence ---

    def test_labels_raster_created(self):
        """Depression-label raster is created."""
        self.assertRasterExists(_LABELS)

    def test_flowdirs_raster_created(self):
        """Flow-direction raster is created."""
        self.assertRasterExists(_FLOWDIRS)

    def test_hierarchy_vector_created(self):
        """Depression-hierarchy vector map is created."""
        self.assertVectorExists(_HIERARCHY)

    # --- labels raster ---

    def test_labels_depression_exists(self):
        """At least one cell has a non-zero depression label."""
        stats = gs.parse_command("r.univar", map=_LABELS, flags="g")
        self.assertGreater(
            float(stats["max"]),
            0.0,
            msg="All cells have label 0 (OCEAN); no depression was detected",
        )

    def test_labels_ocean_cells_exist(self):
        """Border cells drain directly to the boundary and have label 0."""
        stats = gs.parse_command("r.univar", map=_LABELS, flags="g")
        self.assertEqual(
            float(stats["min"]),
            0.0,
            msg="No cells have OCEAN label (0); boundary drainage may be broken",
        )

    # --- flow-direction raster ---

    def test_flowdirs_valid_range(self):
        """Flow directions are in the RichDEM D8 range [0, 8].

        Values 0-7 are D8 directions (counter-clockwise from east).
        Value 8 marks pit cells, which have no outflow direction.
        """
        stats = gs.parse_command("r.univar", map=_FLOWDIRS, flags="g")
        self.assertGreaterEqual(float(stats["min"]), 0.0)
        self.assertLessEqual(float(stats["max"]), 8.0)

    # --- hierarchy vector (layer 1) ---

    def test_hierarchy_has_leaf_depression(self):
        """Layer 1 contains at least one leaf depression."""
        rows = gs.read_command(
            "v.db.select",
            map=_HIERARCHY,
            layer=1,
            columns="type",
            where="type = 'leaf'",
            flags="c",  # column headers suppressed
        ).strip()
        self.assertTrue(
            len(rows) > 0,
            msg="No leaf depression found in hierarchy vector layer 1",
        )

    def test_hierarchy_depression_has_volume(self):
        """Leaf depression has a positive water-storage volume."""
        rows = (
            gs.read_command(
                "v.db.select",
                map=_HIERARCHY,
                layer=1,
                columns="dep_vol",
                where="type = 'leaf'",
                flags="c",
            )
            .strip()
            .splitlines()
        )
        dep_vols = [float(r) for r in rows if r]
        self.assertTrue(
            any(v > 0 for v in dep_vols),
            msg=f"All leaf depressions have dep_vol <= 0: {dep_vols}",
        )

    def test_hierarchy_expected_columns(self):
        """Layer-1 attribute table contains the expected schema columns."""
        required = {
            "cat",
            "dep_label",
            "type",
            "pit_cell",
            "out_cell",
            "parent",
            "lchild",
            "rchild",
            "odep",
            "geolink",
            "pit_elev",
            "out_elev",
            "ocean_parent",
            "cell_count",
            "dep_vol",
            "water_vol",
            "total_elevation",
        }
        cols = (
            gs.read_command("v.info", map=_HIERARCHY, layer=1, flags="c")
            .strip()
            .splitlines()
        )
        # v.info -c output: "type|name"
        found = {line.split("|")[1] for line in cols if "|" in line}
        missing = required - found
        self.assertEqual(
            missing,
            set(),
            msg=f"Missing columns in hierarchy table: {missing}",
        )

    def test_ocean_links_layer_exists(self):
        """Layer 2 (ocean_links) is present in the hierarchy vector."""
        info = gs.parse_command("v.info", map=_HIERARCHY, flags="e")
        # The number of layers is in 'num_dblinks'
        num_layers = int(info.get("num_dblinks", 0))
        self.assertGreaterEqual(
            num_layers,
            2,
            msg="Hierarchy vector does not have a layer-2 ocean_links table",
        )


if __name__ == "__main__":
    test()
