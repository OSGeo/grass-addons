#!/usr/bin/env python3

"""
MODULE:    Test of  m.crawl.thredds

AUTHOR(S): Stefan Blumentrath <stefan.blumentrath at nina.no>

PURPOSE:   Test of  m.crawl.thredds examples

COPYRIGHT: (C) 2021 by Stefan Blumentrath and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import grass.script as gscript

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestThreddsCrawling(TestCase):
    """The main (and only) test case for the m.crawl.thredds module"""

    # Input URLs to available Thredds Data Serves
    thredds_seNorge = "https://thredds.met.no/thredds/catalog/senorge/seNorge_2018/Archive/catalog.xml"
    # thredds_NBS = "https://nbstds.met.no/thredds/catalog/NBS/S2A/2021/02/28/catalog.xml"
    # Output file
    output = "seNorge_result"

    @classmethod
    def setUpClass(cls):
        """Not needed for the module"""
        pass

    @classmethod
    def tearDownClass(cls):
        """Not needed for the module"""
        pass

    def tearDown(self):
        """Remove the output created from the module"""
        gscript.utils.try_remove(self.output)

    def test_output_created(self):
        """Check that the output is created"""
        # run the module
        self.assertModule(
            "m.crawl.thredds",
            input=self.thredds_seNorge,
            output=self.output,
        )
        # check to see if output is in mapset
        self.assertFileExists(self.output, msg="Output was not created")

    def test_output_created_parameters(self):
        """Check that the output is created"""
        # run the module
        self.assertModule(
            "m.crawl.thredds",
            input=self.thredds_seNorge,
            output=self.output,
            nprocs=2,
            # modified_before="2021-06-01T00:00:00.0000Z",
            modified_after="2021-02-01",
            print=["service", "dataset_size"],
            services="wms,httpserver,opendap",
        )
        # check to see if output is in mapset
        self.assertFileExists(self.output, msg="Output was not created")

    def test_missing_parameter(self):
        """Check that the module fails when parameters are missing or invalid"""
        self.assertModuleFail(
            "m.crawl.thredds",
            input=self.thredds_seNorge,
            output=self.output,
            nprocs=2,
            modified_before="2021-01-01T00:00:00.0000Z",
            modified_after="2021-02-01",
            print=["service", "dataset_size"],
            services="nonexistingservice",
            msg="Only services provided by the server are valid.",
        )
        self.assertModuleFail(
            "m.crawl.thredds",
            input=self.thredds_seNorge,
            output=self.output,
            nprocs=2,
            modified_before="2021-02-01",
            modified_after="2021-02-02",
            print=["service", "dataset_size"],
            msg="modified_after should be before modified_before.",
        )


if __name__ == "__main__":
    test()
