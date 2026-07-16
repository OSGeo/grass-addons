#!/usr/bin/env python3

##############################################################################
# MODULE:    Test of t.rast.import.netcdf with Sentinel-2 data
#
# AUTHOR(S): Stefan Blumentrath
#
# PURPOSE:   Test of t.rast.import.netcdf with Sentinel-2 data
#
# SPDX-FileCopyrightText: 2021-2025 Stefan Blumentrath
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

from datetime import datetime
from pathlib import Path

import grass.script as gs
import grass.temporal as tgis
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestNetCDFImport(TestCase):
    """The main (and only) test case for the t.rast.import.netcdf module."""

    # NetCDF URL to be used as input for sentinel data test
    input_sentinel = (
        "https://nbstds.met.no/thredds/fileServer/NBS/S2A/2025/11/10/S2A_MSIL2A_20251110T101251_N0511_R022_T34VDM_20251110T113613.nc",
        "https://nbstds.met.no/thredds/fileServer/NBS/S2A/2025/11/10/S2A_MSIL2A_20251110T101251_N0511_R022_T33VXK_20251110T113613.nc",
    )
    input_sentinel_dt = tuple(
        datetime.strptime(Path(url).stem.split("_")[2], "%Y%m%dT%H%M%S")
        for url in input_sentinel
    )
    # Input file name
    input_file = "url_list.txt"
    # STRDS to be used as output for sentinel data test
    output_sentinel = "S2"

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

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove the temporary region (and anything else we created)."""
        if Path(cls.input_file).exists():
            Path(cls.input_file).unlink()

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

        if self.output_sentinel in existing_strds:
            gs.info("cleaning up " + self.output_sentinel)
            self.runModule("t.remove", flags="rdf", inputs=self.output_sentinel)

    def test_sentinel_output_created(self) -> None:
        """Check that output is created."""
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
        # check t.info output
        tinfo_string = f"""temporal_type=absolute
            start_time='{self.input_sentinel_dt[0].strftime("%Y-%m-%d %H:%M:%S")}'
            end_time='{self.input_sentinel_dt[0].strftime("%Y-%m-%d %H:%M:%S")}'
            granularity='None'
            map_time=point
            nsres_max=10.0
            ewres_min=10.0
            ewres_max=10.0
            number_of_semantic_labels=2
            semantic_labels=S2_1,S2_2
            number_of_maps=2"""
        info = SimpleModule("t.info", flags="g", input=self.output_sentinel)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_sentinel_fast_link(self) -> None:
        """Check that output is created with fast links."""
        # run the import module
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=self.input_sentinel[0],
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
            nodata=-1,
        )
        # check t.info output
        tinfo_string = f"""name=S2
            temporal_type=absolute
            start_time='{self.input_sentinel_dt[0].strftime("%Y-%m-%d %H:%M:%S")}'
            end_time='{self.input_sentinel_dt[0].strftime("%Y-%m-%d %H:%M:%S")}'
            granularity='None'
            map_time=point
            nsres_min=10.0
            nsres_max=10.0
            number_of_semantic_labels=2
            semantic_labels=S2_1,S2_2
            number_of_maps=2"""
        info = SimpleModule("t.info", flags="g", input=self.output_sentinel)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_sentinel_output_appended(self) -> None:
        """Check that output is created if it is appended to existing STRDS."""
        # run the import module
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
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

        # check t.info output
        tinfo_string = f"""name=S2
            temporal_type=absolute
            start_time='{min(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            end_time='{max(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            granularity='None'
            map_time=point
            nsres_min=10.0
            nsres_max=10.0
            number_of_semantic_labels=2
            semantic_labels=S2_1,S2_2
            number_of_maps=4"""
        info = SimpleModule("t.info", flags="g", input=self.output_sentinel)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_sentinel_input_comma_separated(self) -> None:
        """Check that output is created with comma separated input of netCDF files."""
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=",".join(self.input_sentinel),
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )

        # check t.info output
        tinfo_string = f"""name=S2
            temporal_type=absolute
            start_time='{min(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            end_time='{max(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            granularity='None'
            map_time=point
            nsres_min=10.0
            nsres_max=10.0
            number_of_semantic_labels=2
            semantic_labels=S2_1,S2_2
            number_of_maps=4"""
        info = SimpleModule("t.info", flags="g", input=self.output_sentinel)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )

    def test_sentinel_input_file(self) -> None:
        """Check that output is created with a textfile as input."""
        Path(self.input_file).write_text(
            "\n".join(self.input_sentinel),
            encoding="utf8",
        )
        self.assertModule(
            "t.rast.import.netcdf",
            flags="fo",
            input=self.input_file,
            output=self.output_sentinel,
            semantic_labels="data/semantic_labels_sentinel2.conf",
            memory=2048,
            nprocs=2,
        )

        # check t.info output
        tinfo_string = f"""name=S2
            temporal_type=absolute
            start_time='{min(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            end_time='{max(self.input_sentinel_dt).strftime("%Y-%m-%d %H:%M:%S")}'
            granularity='None'
            map_time=point
            nsres_min=10.0
            nsres_max=10.0
            number_of_semantic_labels=2
            semantic_labels=S2_1,S2_2
            number_of_maps=4"""
        info = SimpleModule("t.info", flags="g", input=self.output_sentinel)
        self.assertModuleKeyValue(
            module=info,
            reference=tinfo_string,
            precision=2,
            sep="=",
        )


if __name__ == "__main__":
    test()
