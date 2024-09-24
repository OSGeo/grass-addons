#!/usr/bin/env python3

"""
MODULE:    Test of r.buildvrt.gdal

AUTHOR(S): Stefan Blumentrath

PURPOSE:   Test of r.buildvrt.gdal

COPYRIGHT: (C) 2024 by Stefan Blumentrath and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import os

from pathlib import Path

import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestBuildGDALVRT(TestCase):
    """The main test case for the r.buildvrt.gdal module"""

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region (and anything else needed)

        These are things needed by all test function but not modified by
        any of them.
        """
        cls.vrt_univar = """n=1500000
        null_cells=0
        cells=1500000
        min=0.25
        max=1498750.25
        range=1498750
        mean=375000
        mean_of_abs=375000
        stddev=330718.777396167
        variance=109374909722.416
        coeff_var=88.1916739723113
        sum=562500000000"""

        # Create external example data
        regions = {"s": (0, 1000), "n": (500, 1500)}
        tmp_dir = Path(gs.tempfile(create=False))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        cls.map_input_file = tmp_dir / "map_file.txt"
        gs.run_command(
            "r.external.out",
            format="GTiff",
            options="compress=LZW,PREDICTOR=3",
            directory=str(tmp_dir),
        )
        map_list = []
        for name, ns_extent in regions.items():
            gs.run_command(
                "g.region", n=ns_extent[1], s=ns_extent[0], w=0, e=1000, res=1
            )
            map_name = f"tmp_vrt_gtiff_{ns_extent[1]}_{ns_extent[0]}"
            map_list.append(map_name)
            gs.mapcalc(f"{map_name}=float(x()*y())")

        cls.map_input_file.write_text("\n".join(map_list), encoding="UTF8")

        # Set region
        gs.use_temp_region()
        gs.run_command("g.region", n=1500, s=0, w=0, e=1000, res=1)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        gs.del_temp_region()
        gs.run_command("g.remove", flags="f", type="raster", pattern="tmp_vrt_g*_*")

    def tearDown(self):
        """Remove the output created from the module

        This is executed after each test function run. If we had
        something to set up before each test function run, we would use setUp()
        function.

        Since we remove the raster map after running each test function,
        we can reuse the same name for all the test functions.
        """
        gs.run_command("g.remove", flags="f", type="raster", pattern="tmp_vrt_gda*")

    def test_r_buildvrt_gdal_no_flag(self):
        """Check that the output is created and readable"""
        # run the import module
        raster_maps = gs.list_strings(type="raster", pattern="tmp_vrt_gtiff*_*")

        self.assertModule(
            "r.buildvrt.gdal",
            verbose=True,
            input=",".join(raster_maps),
            output="tmp_vrt_gdal",
        )
        vrt_info = """north=1500
south=0
east=1000
west=0
nsres=1
ewres=1
rows=1500
cols=1000
cells=1500000
datatype=FCELL
ncats=0
min=0.25
max=1498750
map=tmp_vrt_gdal
maptype=GDAL-link
title=""
timestamp="none"
units="none"
vdatum="none"
semantic_label="none"
"""
        self.assertRasterFitsUnivar(
            "tmp_vrt_gdal", reference=self.vrt_univar, precision=2
        )
        self.assertRasterFitsInfo("tmp_vrt_gdal", reference=vrt_info, precision=2)

    def test_r_buildvrt_gdal_r_flag(self):
        """Check that the output is created and readable with r-flag"""
        # run the import module
        raster_maps = gs.list_strings(type="raster", pattern="tmp_vrt_gtiff*_*")

        self.assertModule(
            "r.buildvrt.gdal",
            flags="r",
            verbose=True,
            input=",".join(raster_maps),
            output="tmp_vrt_gdal_r",
        )
        self.assertRasterFitsUnivar(
            "tmp_vrt_gdal_r", reference=self.vrt_univar, precision=2
        )

    def test_r_buildvrt_gdal_vrt_dir(self):
        """Check that the output is created and readable with r-flag"""
        # run the import module
        raster_maps = gs.list_strings(type="raster", pattern="tmp_vrt_gtiff*_*")
        vrt_directory = gs.tempfile(create=False)
        self.assertModule(
            "r.buildvrt.gdal",
            verbose=True,
            input=",".join(raster_maps),
            output="tmp_vrt_gdal_dir",
            vrt_directory=vrt_directory,
        )
        self.assertRasterFitsUnivar(
            "tmp_vrt_gdal_dir", reference=self.vrt_univar, precision=2
        )
        self.assertFileExists(vrt_directory + "/tmp_vrt_gdal_dir.vrt")

    def test_r_buildvrt_fails_rm(self):
        """Check that module fails with both -m and -r"""
        raster_maps = gs.list_strings(type="raster", pattern="tmp_vrt_gtiff*_*")
        # run the import module
        self.assertModuleFail(
            "r.buildvrt.gdal",
            verbose=True,
            input=",".join(raster_maps),
            file=str(self.map_input_file),
            output="tmp_vrt_gdal_input_file",
        )

    def test_r_buildvrt_fails_rm(self):
        """Check that module fails with both -m and -r"""
        # run the import module
        self.assertModuleFail(
            "r.buildvrt.gdal",
            verbose=True,
            flags="rm",
            file=str(self.map_input_file),
            output="tmp_vrt_gdal_rm",
        )

    def test_r_buildvrt_gdal_vrt_file(self):
        """Check that the output is created and readable with file input"""
        # run the import module
        self.assertModule(
            "r.buildvrt.gdal",
            verbose=True,
            file=str(self.map_input_file),
            output="tmp_vrt_gdal_file",
        )
        self.assertRasterFitsUnivar(
            "tmp_vrt_gdal_file", reference=self.vrt_univar, precision=2
        )


if __name__ == "__main__":
    test()
