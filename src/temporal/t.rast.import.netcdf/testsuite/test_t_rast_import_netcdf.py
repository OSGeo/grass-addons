#!/usr/bin/env python3

"""
MODULE:    Test of t.rast.import.netcdf

AUTHOR(S): Stefan Blumentrath <stefan dot blumentrath at nina dot no>

PURPOSE:   Test of t.rast.import.netcdf (example of a simple test of a module)

COPYRIGHT: (C) 2021 by Stefan Blumentrath and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import os

import grass.temporal as tgis

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

# Todo:
# Add tests for r.in.gdal (-r) and r.import with region settings
# Add tests for printing


class TestNetCDFImport(TestCase):
    """The main (and only) test case for the t.rast.import.netcdf module"""

    # NetCDF URL to be used as input for sentinel data test
    input_sentinel = [
        "https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T35WPU_20210228T201033_DTERRENGDATA.nc",
        "https://nbstds.met.no/thredds/fileServer/NBS/S2A/2021/02/28/S2A_MSIL1C_20210228T103021_N0202_R108_T32VNL_20210228T201033_DTERRENGDATA.nc",
    ]
    # STRDS to be used as output for sentinel data test
    output_sentinel = "S2"
    # NetCDF URL to be used as input for climate data test
    input_climate = "https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc"
    # Input file name
    input_file = "url_list.txt"
    # STRDS to be used as output for climate data test
    output_climate = "se_norge"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region (and anything else needed)

        These are things needed by all test function but not modified by
        any of them.
        """
        # Not needed
        tgis.init()

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        if os.path.exists(cls.input_file):
            os.remove(cls.input_file)

    def tearDown(self):
        """Remove the output created from the module

        This is executed after each test function run. If we had
        something to set up before each test function run, we would use setUp()
        function.

        Since we remove the raster map after running each test function,
        we can reuse the same name for all the test functions.
        """
        dataset_list = tgis.list_stds.get_dataset_list(
            type="strds", temporal_type="absolute", columns="name"
        )
        mapset = tgis.get_current_mapset()
        existing_strds = (
            [row["name"] for row in dataset_list[mapset]]
            if mapset in dataset_list
            else []
        )

        for strds in existing_strds:
            print("cleaning up " + strds)
            self.runModule("t.remove", flags="rdf", inputs=strds)

    def test_sentinel_output_created(self):
        """Check that the output is created"""
        # run the import module
        self.assertModule(
            "t.rast.import.netcdf",
            flags="lo",
            input=self.input_sentinel[0],
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )
        # check to see if output is in mapset
        # Adjust to STRDS
        # self.assertRasterExists(self.output, msg="Output was not created")

    def test_sentinel_fast_no_semantic_label(self):
        """Check that the output is created"""
        # run the import module
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=self.input_sentinel[0],
            output=self.output_sentinel,
            memory=2048,
            nprocs=2,
            nodata=-1,
        )
        # check to see if output is in mapset
        # Adjust to STRDS
        # self.assertRasterExists(self.output, msg="Output was not created")

    def test_sentinel_output_appended(self):
        """Check that the output is created"""
        # run the import module
        self.assertModule(
            "t.rast.import.netcdf",
            flags="lo",
            input=self.input_sentinel[0],
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )
        self.assertModule(
            "t.rast.import.netcdf",
            flags="loa",
            input=self.input_sentinel[1],
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )

    def test_sentinel_input_comma_separated(self):
        """Check that the output is created"""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="lo",
            input=",".join(self.input_sentinel),
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )

    def test_sentinel_input_file(self):
        """Check that the output is created"""
        with open(self.input_file, "w") as f:
            f.write("\n".join(self.input_sentinel))
        self.assertModule(
            "t.rast.import.netcdf",
            flags="lo",
            input=self.input_file,
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )

    def test_climate_output_created(self):
        """Check that the output is created"""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="lo",
            input=self.input_climate,
            output=self.output_climate,
            semantic_labels="data/semantic_labels_senorge.conf",
            start_time="2021-01-01",
            end_time="2021-01-03 12:12:12",
            memory=2048,
            nprocs=2,
        )

    def test_missing_parameter(self):
        """Check that the module fails when parameters are missing

        Checks absence of each of the three parameters. Each parameter absence
        is tested separately.

        Note that this does not cover all the possible combinations, but it
        tries to simulate most of possible user errors and it should cover
        most of the implementation.
        """
        self.assertModuleFail(
            "t.rast.import.netcdf",
            output=self.output_sentinel,
            msg="The input parameter should be required",
        )
        self.assertModuleFail(
            "t.rast.import.netcdf",
            input=self.input_sentinel[0],
            msg="The output parameter should be required",
        )


if __name__ == "__main__":
    test()
