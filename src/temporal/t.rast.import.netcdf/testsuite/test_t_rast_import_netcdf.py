#!/usr/bin/env python3

##############################################################################
# MODULE:    Test of t.rast.import.netcdf with chirps and seNorge data
#
# AUTHOR(S): Stefan Blumentrath
#
# PURPOSE:   Test of t.rast.import.netcdf with chirps and seNorge data
#
# SPDX-FileCopyrightText: 2021-2025 Stefan Blumentrath
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################


from pathlib import Path

import grass.script as gs
import grass.temporal as tgis
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestNetCDFImport(TestCase):
    """The main (and only) test case for the t.rast.import.netcdf module."""

    # NetCDF URL to be used as input for climate data test
    input_climate = "https://thredds.met.no/thredds/fileServer/senorge/seNorge_2018/Archive/seNorge2018_2021.nc"
    # STRDS to be used as output for climate data test
    output_climate = "se_norge"
    # NetCDF URL (CF-1.6) without subdataset and without defined CRS (=CRS84)
    input_chirps = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/chirps-v2.0.2011.days_p05.nc"
    output_chirps = "chirps_2011"

    @classmethod
    def setUpClass(cls) -> None:
        """Ensure expected computational region (and anything else needed) is set.

        These are things needed by all test function but not modified by
        any of them.
        """
        # Save current region to temporary file
        gs.use_temp_region()
        gs.run_command("g.region", raster="elevation", res="250", flags="a")

        tgis.init()

    def tearDown(self) -> None:
        """Remove the output created from the module.

        This is executed after each test function run. If we had
        something to set up before each test function run, we would use setUp()
        function.

        Since we remove the raster map after running each test function,
        we can reuse the same name for all the test functions.
        """
        dataset_list = tgis.list_stds.get_dataset_list(
            type="strds",
            temporal_type="absolute",
            columns="name",
        )
        mapset = tgis.get_current_mapset()
        existing_strds = (
            [row["name"] for row in dataset_list[mapset]]
            if mapset in dataset_list
            else []
        )

        for strds in existing_strds:
            gs.info("cleaning up " + strds)
            if strds in {self.output_climate, self.output_chirps}:
                self.runModule("t.remove", flags="rdf", inputs=strds)

    def test_climate_print_extended(self) -> None:
        """Check that extended metadata is printed."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="o",
            input=self.input_climate,
            print="extended",
            semantic_labels="data/semantic_labels_senorge.conf",
            start_time="2021-01-01",
            end_time="2021-01-03 12:12:12",
            memory=2048,
            nodata="-999.99,-999.98999",
            nprocs=2,
        )

    def test_climate_print_grass(self) -> None:
        """Check that grass metadata is printed."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="o",
            input=self.input_climate,
            print="grass",
            semantic_labels="data/semantic_labels_senorge.conf",
            start_time="2021-01-01",
            end_time="2021-01-03 12:12:12",
            memory=2048,
            nodata="-999.99,-999.98999",
            nprocs=2,
        )

    def test_climate_output_created(self) -> None:
        """Check that output is created with r.in.gdal."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="o",
            input=self.input_climate,
            output=self.output_climate,
            semantic_labels="data/semantic_labels_senorge.conf",
            start_time="2021-01-01",
            end_time="2021-01-03 12:12:12",
            memory=2048,
            nodata="-999.99,-999.98999",
            nprocs=2,
        )

        # check t.info output
        tinfo_string = """name=se_norge
            temporal_type=absolute
            semantic_type=mean
            start_time='2021-01-01 06:00:00'
            end_time='2021-01-04 06:00:00'
            granularity='24 hours'
            map_time=interval
            north=8000000.0
            south=6450000.0
            east=1120000.0
            west=-75000.0
            top=0.0
            bottom=0.0
            nsres_min=1000.0
            nsres_max=1000.0
            ewres_min=1000.0
            ewres_max=1000.0
            min_min=-25.763
            min_max=-15.533
            max_min=1.48
            max_max=4.4
            aggregation_type=None
            number_of_semantic_labels=2
            semantic_labels=temperature_avg,temperature_min
            number_of_maps=6"""
        info = SimpleModule("t.info", flags="g", input=self.output_climate)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_climate_output_no_labels_only_start(self) -> None:
        """Check that output is created without semantic labels and only start time."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=self.input_climate,
            output=self.output_climate,
            start_time="2021-12-19",
            memory=2048,
            nprocs=2,
        )

        # check t.info output
        tinfo_string = """name=se_norge
            temporal_type=absolute
            semantic_type=mean
            start_time='2021-12-19 06:00:00'
            end_time='2022-01-01 06:00:00'
            granularity='24 hours'
            map_time=interval
            north=8000000.0
            south=6450000.0
            east=1120000.0
            west=-75000.0
            top=0.0
            bottom=0.0
            nsres_min=1000.0
            nsres_max=1000.0
            ewres_min=1000.0
            ewres_max=1000.0
            min_min=None
            min_max=None
            max_min=None
            max_max=None
            aggregation_type=None
            number_of_semantic_labels=4
            semantic_labels=rr,tg,tn,tx
            number_of_maps=52"""
        info = SimpleModule("t.info", flags="g", input=self.output_climate)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_climate_output_no_labels_only_end(self) -> None:
        """Check that output is created without semantic labels and only end time."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=self.input_climate,
            output=self.output_climate,
            end_time="2021-01-03",
            memory=2048,
            nprocs=2,
        )

        # check t.info output
        tinfo_string = """name=se_norge
            temporal_type=absolute
            semantic_type=mean
            start_time='2021-01-01 06:00:00'
            end_time='2021-01-03 06:00:00'
            granularity='24 hours'
            map_time=interval
            north=8000000.0
            south=6450000.0
            east=1120000.0
            west=-75000.0
            top=0.0
            bottom=0.0
            nsres_min=1000.0
            nsres_max=1000.0
            ewres_min=1000.0
            ewres_max=1000.0
            min_min=None
            min_max=None
            max_min=None
            max_max=None
            aggregation_type=None
            number_of_semantic_labels=4
            semantic_labels=rr,tg,tn,tx
            number_of_maps=8"""
        info = SimpleModule("t.info", flags="g", input=self.output_climate)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_missing_parameter(self) -> None:
        """Check that the module fails when parameters are missing.

        Checks absence of each of the three parameters. Each parameter absence
        is tested separately.

        Note that this does not cover all the possible combinations, but it
        tries to simulate most of possible user errors and it should cover
        most of the implementation.
        """
        self.assertModuleFail(
            "t.rast.import.netcdf",
            output=self.output_climate,
            msg="The input parameter should be required",
        )
        self.assertModuleFail(
            "t.rast.import.netcdf",
            input=self.input_climate,
            msg="The output parameter should be required",
        )

    def test_no_crs_no_subdataset(self) -> None:
        """Check that the chirps dataset (no CRS, no subdataset) imports."""
        self.assertModule(
            "t.rast.import.netcdf",
            overwrite=True,
            flags="fr",
            input=self.input_chirps,
            output=self.output_chirps,
            start_time="2011-01-01",
            end_time="2011-01-03",
            color="precipitation_daily",
            memory=2048,
            nprocs=2,
            default_crs=4326,
            resample="bilinear",
        )

        # check t.info output
        tinfo_string = """name=chirps_2011
            temporal_type=absolute
            semantic_type=mean
            start_time='2011-01-01 00:00:00'
            end_time='2011-01-03 00:00:00'
            granularity='1 day'
            map_time=interval
            north=228500.0
            south=-35128500.0
            east=645000.0
            west=630000.0
            top=0.0
            bottom=0.0
            nsres_min=250.0
            nsres_max=250.0
            ewres_min=250.0
            ewres_max=250.0
            min_min=None
            min_max=None
            max_min=None
            max_max=None
            aggregation_type=None
            number_of_semantic_labels=1
            semantic_labels=convective_precipitation_rate
            number_of_maps=2"""
        info = SimpleModule("t.info", flags="g", input=self.output_chirps)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )


if __name__ == "__main__":
    test()

