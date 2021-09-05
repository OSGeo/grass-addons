#!/usr/bin/env python3

############################################################################
#
# NAME:      r_random_walk_test
#
# AUTHOR:    Corey T. White
#
# PURPOSE:   This is a test file for r.random.walk
#
# COPYRIGHT: (C) 2021 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# Dependencies
import importlib
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
# importlib.import_module("r.random.walk")
# from r.random.walk import (
#     take_step,
#     walker_is_stuck,
#     avoid_boundary,
#     starting_position,
#     out_of_bounds,
# )

# Tests
class TestRandomWalk(TestCase):
    # Setup variables to be used for outputs
    random_walk = "test_random_walk"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    @classmethod
    def tearDown(self):
        """
        Remove the outputs created from the centroids module
        This is executed after each test run.
        """
        self.runModule("g.remove", flags="f", type="raster", name=self.random_walk)

    def test_random_walk_no_overlap_output(self):
        """Test that random.walk are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "r.random.walk",
            output=self.random_walk,
            steps=1000,
            overwrite=True,
            seed=0,
            flags="s",
        )

    def test_random_walk_with_overlap_output(self):
        """Test that random.walk are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "r.random.walk",
            output=self.random_walk,
            steps=1000,
            overwrite=True,
            seed=0,
            flags="sr",
        )

    def test_random_walk_with_overlap_8_dir_output(self):
        """Test that random.walk are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "r.random.walk",
            output=self.random_walk,
            steps=1000,
            directions="8",
            seed=0,
            flags="sr",
            overwrite=True,
        )

    # def test_take_step_dir_4(self):
    #     """
    #     Tests 4 directional step
    #     """
    #     step = take_step([0, 0], 4, black_list=[])
    #     self.assertTrue(
    #         step == [1, 0]
    #         or step == [0, 1]  # North
    #         or step == [-1, 0]  # East
    #         or step == [0, -1],  # South  # West
    #         f"Step outside of 4 directional bounds, {step}",
    #     )

    # def test_take_step_dir_8(self):
    #     """
    #     Tests 8 directional step
    #     """
    #     step = take_step([0, 0], 8)
    #     self.assertTrue(
    #         step == [1, 0]
    #         or step == [0, 1]  # N
    #         or step == [-1, 0]  # E
    #         or step == [0, -1]  # S
    #         or step == [1, 1]  # W
    #         or step == [-1, 1]  # NE
    #         or step == [-1, -1]  # SE
    #         or step == [1, -1],  # SW  # NW
    #         f"Step outside of 8 directional bounds, {step}",
    #     )

    # def test_take_step_dir_4_blacklist(self):
    #     """
    #     Tests 4 directional step blacklist
    #     """
    #     step = take_step([0, 0], 4, black_list=[0, 1, 2])
    #     self.assertTrue(
    #         step != [1, 0]
    #         and step != [0, 1]  # North
    #         and step != [-1, 0]  # East
    #         and step == [0, -1],  # South  # West
    #         f"Used step from blacklist or outside of 4 directional bounds, {step}",
    #     )

    # def test_walker_is_not_stuck(self):
    #     """
    #     Test if walker is stuck and should return False the walker is not stuck
    #     """
    #     tested_directions = [0, 1, 2]
    #     output = walker_is_stuck(tested_directions, 4)
    #     self.assertFalse(output)

    # def test_walker_is_stuck(self):
        """
        Test if walker is stuck and should return True the walker is stuck
        """
        tested_directions = [0, 1, 2, 3]
        output = walker_is_stuck(tested_directions, 4)
        self.assertTrue(output)


if __name__ == "__main__":
    test()
