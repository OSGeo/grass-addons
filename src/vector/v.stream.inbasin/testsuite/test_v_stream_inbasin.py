##############################################################################
# AUTHOR(S): Vaclav Petras <wenzeslaus gmail com>
#
# COPYRIGHT: (C) 2023 Vaclav Petras and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Test v.stream.inbasin tool using grass.gunittest with NC SPM dataset"""

import json

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class FunctionalityVStreamNetwork(TestCase):
    """Test case for v.stream.inbasin focused on functionality

    The test needs v.stream.network to run.
    """

    original = "streams@PERMANENT"
    ours = "functionality_streams"
    input_as_raster = "input_as_raster"
    output_as_raster = "output_as_raster"
    bad_difference = "bad_difference"
    subset_output = "selected_subset"
    point_output = "pour_point"
    coordinates = (639089, 223304)

    @classmethod
    def setUpClass(cls):
        cls.runModule("g.copy", vector=(cls.original, cls.ours))
        cls.runModule("v.stream.network", map=cls.ours)
        cls.runModule("g.region", vector=cls.ours, res=5)
        cls.runModule(
            "v.to.rast", input=cls.ours, output=cls.input_as_raster, use="val", value=1
        )
        cls.runModule(
            "v.stream.inbasin",
            input_streams=cls.ours,
            coordinates=cls.coordinates,
            output_streams=cls.subset_output,
            output_pour_point=cls.point_output,
            flags="s",
        )
        cls.runModule(
            "v.to.rast",
            input=cls.subset_output,
            output=cls.output_as_raster,
            use="val",
            value=1,
        )
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.bad_difference} = if(isnull({cls.input_as_raster}) && not(isnull({cls.input_as_raster})), 1, 0)",
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            type="vector",
            name=[cls.ours, cls.subset_output, cls.point_output],
            flags="f",
        )
        cls.runModule(
            "g.remove",
            type="raster",
            name=[cls.input_as_raster, cls.output_as_raster, cls.bad_difference],
            flags="f",
        )

    def test_geometry_is_subset(self):
        """Check that geometry is subset of the input by comparing raster versions"""
        self.assertRasterFitsInfo(self.bad_difference, {"max": 0, "min": 0})

    def test_geometry_statistics(self):
        """Check against values determined by running the tool"""
        info = gs.vector_info(self.subset_output)
        self.assertEqual(info["level"], 2)
        self.assertEqual(info["lines"], 918)
        self.assertEqual(info["nodes"], 915)
        self.assertEqual(info["primitives"], 918)

    def test_attribute_info(self):
        """Check attribute info against expected values"""
        info = gs.vector_info(self.subset_output)
        self.assertEqual(info["num_dblinks"], 1)
        self.assertEqual(info["attribute_layer_number"], "1")
        self.assertEqual(info["attribute_table"], self.subset_output)
        self.assertEqual(info["attribute_primary_key"], "cat")

    def compare_columns(self, old_vector, new_vector):
        original_columns = gs.vector_columns(old_vector)
        our_columns = gs.vector_columns(new_vector)
        for original_column in original_columns:
            self.assertIn(original_column, our_columns)
        for name, original_column in original_columns.items():
            for key, value in original_column.items():
                self.assertEqual(value, our_columns[name][key])

    def test_columns_preserved_from_original_streams(self):
        """Check that columns are preserved from original unchanged input"""
        self.compare_columns(self.original, self.ours)

    def test_columns_preserved_from_input(self):
        """Check that columns are preserved from input"""
        self.compare_columns(self.ours, self.subset_output)

    def test_point_geometry_statistics(self):
        """Check against values determined by running the tool"""
        self.assertVectorExists(self.point_output)
        info = gs.vector_info(self.point_output)
        self.assertEqual(info["level"], 2)
        self.assertEqual(info["points"], 1)
        self.assertEqual(info["nodes"], 0)
        self.assertEqual(info["primitives"], 1)

    def test_point_attribute_info(self):
        """Check attribute info against expected values"""
        self.assertVectorExists(self.point_output)
        info = gs.vector_info(self.point_output)
        self.assertEqual(info["num_dblinks"], 1)
        self.assertEqual(info["attribute_layer_number"], "1")
        self.assertEqual(info["attribute_table"], self.point_output)
        self.assertEqual(info["attribute_primary_key"], "cat")

    def test_pour_point_geometry(self):
        """Check pour point against coordinates determined by running the tool"""
        data = (
            gs.read_command("v.out.ascii", input=self.point_output).strip().split("|")
        )
        self.assertEqual(len(data), 3)
        self.assertAlmostEqual(float(data[0]), 639258.424, places=3)
        self.assertAlmostEqual(float(data[1]), 223266.931, places=3)

    def test_pour_point_attributes(self):
        """Check pour point against coordinates determined by running the tool"""
        records = json.loads(
            gs.read_command("v.db.select", map=self.point_output, format="json")
        )["records"]
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0]["x"], 639258.424, places=3)
        self.assertAlmostEqual(records[0]["y"], 223266.931, places=3)


class ExactCoordinatesVStreamInbasin(TestCase):
    """Test case for v.stream.inbasin using exact coordinates (without -s flag)"""

    streams = "exact_streams"
    draindir = "exact_draindir"
    basins_vect = "exact_basins_vect"
    output_basin = "exact_output_basin"
    output_streams = "exact_output_streams"
    output_pour_point = "exact_output_pour_point"
    coordinates = (639258, 223267)

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", vector="streams@PERMANENT", res=10)
        cls.runModule("g.copy", vector=("streams@PERMANENT", cls.streams))
        cls.runModule("v.stream.network", map=cls.streams)
        cls.runModule(
            "r.watershed",
            elevation="elevation@PERMANENT",
            drainage=cls.draindir,
            quiet=True,
        )
        cls.runModule(
            "v.buffer",
            input=cls.streams,
            output=cls.basins_vect,
            distance=50,
            quiet=True,
        )
        cls.runModule(
            "v.stream.inbasin",
            input_streams=cls.streams,
            input_basins=cls.basins_vect,
            draindir=cls.draindir,
            coordinates=cls.coordinates,
            output_basin=cls.output_basin,
            output_streams=cls.output_streams,
            output_pour_point=cls.output_pour_point,
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            type="vector",
            name=[
                cls.streams,
                cls.basins_vect,
                cls.output_basin,
                cls.output_streams,
                cls.output_pour_point,
            ],
            flags="f",
        )
        cls.runModule(
            "g.remove",
            type="raster",
            name=[cls.draindir],
            flags="f",
        )
        cls.del_temp_region()

    def test_output_basin_exists(self):
        """Check that output basin was created and has areas"""
        self.assertVectorExists(self.output_basin)
        info = gs.vector_info(self.output_basin)
        self.assertGreater(info["areas"], 0)

    def test_output_streams_exists(self):
        """Check that output streams vector exists and has lines"""
        self.assertVectorExists(self.output_streams)
        info = gs.vector_info(self.output_streams)
        self.assertGreater(info["lines"], 0)

    def test_exact_pour_point(self):
        """Check that pour point coordinates match the exact input coordinates"""
        self.assertVectorExists(self.output_pour_point)
        records = json.loads(
            gs.read_command("v.db.select", map=self.output_pour_point, format="json")
        )["records"]
        self.assertEqual(len(records), 1)
        self.assertAlmostEqual(records[0]["x"], self.coordinates[0], places=1)
        self.assertAlmostEqual(records[0]["y"], self.coordinates[1], places=1)

    def test_without_input_basins(self):
        """Check running exact coordinates without input_basins"""
        basin_out = "exact_no_subbasins_basin"
        streams_out = "exact_no_subbasins_streams"
        self.assertModule(
            "v.stream.inbasin",
            input_streams=self.streams,
            draindir=self.draindir,
            coordinates=self.coordinates,
            output_basin=basin_out,
            output_streams=streams_out,
        )
        self.assertVectorExists(basin_out)
        self.assertVectorExists(streams_out)
        basin_info = gs.vector_info(basin_out)
        streams_info = gs.vector_info(streams_out)
        self.assertGreater(basin_info["areas"], 0)
        self.assertGreater(streams_info["lines"], 0)
        gs.run_command(
            "g.remove",
            type="vector",
            name=[basin_out, streams_out],
            flags="f",
            quiet=True,
        )


if __name__ == "__main__":
    test()
