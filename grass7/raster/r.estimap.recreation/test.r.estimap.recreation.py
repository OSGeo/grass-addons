#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Name       Tests on ...
Purpose    Test for no difference between the input and output raster maps
after recoding based on a set of pre-defind rules

License    (C) 2018 by the GRASS Development Team
           This program is free software under the GNU General Public License
           (>=v2). Read the file COPYING that comes with GRASS for details.

:authors: Nikos Alexandris
"""

"""Libraries"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
import grass.script as g

import restimap as restimap
import tempfile

"""Globals"""

# PRECISION=[0.1, 0.01, 0.001]

CORINE_LAND_COVER_CLASSES="""
north:                    1
south:                    0
east:                     45
west:                     0
rows:                     1
cols:                     45
null:                     -1
type: int
multiplier: 1

1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45"""
# print "CORINE land cover classes:", CORINE_LAND_COVER_CLASSES
corine_input='corine_input'

CORINE_LAND_COVER_CLASSES_MINIMUM=1
# print "Minimum category integer for CORINE land cover class :", CORINE_LAND_COVER_CLASSES_MINIMUM

CORINE_LAND_COVER_CLASSES_MAXIMUM=48
# print "Maximum category integer for CORINE land cover class:", CORINE_LAND_COVER_CLASSES_MAXIMUM

CORINE_LAND_COVER_CLASSES_SUITABILITY_SCORES="""
north:                    1
south:                    0
east:                     45
west:                     0
rows:                     1
cols:                     45
null:                     -1
type: dcell
multiplier: 1

0 0.1 0 0 0 0 0 0 0 1 0.1 0.3 0.3 0.4 0.5 0.5 0.5 0.6 0.3 0.3 0.6 0.6 1 0.8 1 0.8 0.8 0.8 0.8 1 0.8 0.7 0 0.8 1 0.8 1 0.8 1 1 1 1 0.8 1 0.3"""
# print "Suitability scores map:", CORINE_LAND_COVER_CLASSES_SUITABILITY_SCORES

suitability_map='suitability_map'
corine_recoded='corine_recoded'

"""Test Case Class"""

# def recode_map(raster, rules, colors, output):

class TestCORINE(TestCase):

    gisenv = SimpleModule('g.gisenv', get='MAPSET')
    TestCase.runModule(gisenv, expecting_stdout=True)
    print "Mapset: ", gisenv.outputs.stdout.strip()

    # TODO: replace by unified handing of maps
    to_remove = []

    # glist = SimpleModule('g.list',
    #                 type='raster',
    #                 mapset='.',
    #                 flags='p')

    # TestCase.runModule(glist, expecting_stdout=True)
    # print glist.outputs.stdout.strip()

    filename = tempfile.TemporaryFile(mode='w+b',
                                      suffix='',
                                      prefix='tmp',
                                      dir=None)
    print "Filename:", filename

    corine_input = 'corine_land_cover_classes.ascii'
    suitability_map = 'suitability_scores_for_corine.ascii'
    suitability_rules = 'suitability_of_corine_land_cover_classes.scores'

    @classmethod
    def setUpClass(cls):
        """
        """

        try:
            print "Trying to open file and write content"
            ascii_file = open(cls.filename, "w")
            ascii_file.write("Purchase Amount")
        except IOError as e:
            print "IOError:", e
            return
        finally:
            print "Success -- Closing file"
            ascii_file.close()

        # use a temporary region
        print "Use a temporary region"
        cls.use_temp_region()

        # # create input raster maps
        print "Import CORINE land cover class nomenclature"
        print "Input map name:", cls.corine_input
        cls.runModule('r.in.ascii',
                      input=cls.corine_input,
                      output=corine_input,
                      overwrite=True,
                      verbose=True)

        print "Import suitability scores map"
        cls.runModule('r.in.ascii',
                      input=cls.suitability_map,
                      output=suitability_map,
                      overwrite=True,
                      verbose=True)

        # append them in list "to_remove"
        print "Add imported maps in list to remove"
        cls.to_remove.append(corine_input)
        cls.to_remove.append(suitability_map)

        # set region to map(s)
        cls.runModule('g.region', raster=corine_input, flags='p')

    def test_recode_map(self):
        """
        """
        restimap.recode_map(raster=corine_input,
                rules=cls.suitability_rules,
                output=corine_recoded)

    @classmethod
    def tearDownClass(cls):

        """
        Remove temporary region and test raster maps
        """
        cls.del_temp_region()
        print
        print "Removing test raster maps:\n"
        print ', '.join(cls.to_remove)
        if cls.to_remove:
            cls.runModule('g.remove', flags='f', type='raster',
                name=','.join(cls.to_remove), verbose=True)

    def tearDown(self):
        """
        ...
        """
        pass

    def test_corine_range(self):
        """
        Test for range of Hue, Intensity and Saturation
        """
        self.assertRasterMinMax(map=corine,
                refmin=CORINE_MINIMUM,
                refmax=CORINE_MAXIMUM,
                msg=None)

    def test_difference(self):
        """
        Test for no or minimal differences between
        """
        # assertRastersNoDifference(actual, reference, precision, statistics=None, msg=None)

        self.assertRastersNoDifference(actual=corine_recoded,
                reference=corine_input,
                precision=precision)

        info = SimpleModule('r.info', flags='r', map=corine_input)
        TestCase.runModule(info, expecting_stdout=True)
        corine_input_line = [corine_input] + info.outputs.stdout.splitlines()

        info = SimpleModule('r.info', flags='r', map=corine_recoded)
        TestCase.runModule(info, expecting_stdout=True)
        corine_recoded_line = [corine_recoded] + info.outputs.stdout.splitlines()

        # inform

        for row in corine_input_line, corine_recoded_line:
            print("{: >20} {: >25} {: >20}".format(*row))

        print

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
