#!/usr/bin/env python

############################################################################
#
# MODULE:        r_forestfrag_trivial
# AUTHOR:        Vaclav Petras
# PURPOSE:       Test using example from the Riitters et al. 2000 paper
# COPYRIGHT:     (C) 2016 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# This test led to discovery of #3067 (r68717) which was an r.mapcalc
# row indexing bug.

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


FOREST_RIITTERS = """\
north: 10
south: 8
east: 20
west: 18
rows: 3
cols: 3
1 0 1
1 1 0
1 1 0
"""

FRAG_RIITTERS = """\
north: 10
south: 8
east: 20
west: 18
rows: 3
cols: 3
null: N
N N N
N 4 N
N N N
"""

PF_RIITTERS = """\
north: 10
south: 8
east: 20
west: 18
rows: 3
cols: 3
null: N
N N N
N 0.67 N
N N N
"""

PFF_RIITTERS = """\
north: 10
south: 8
east: 20
west: 18
rows: 3
cols: 3
null: N
N N N
N 0.45 N
N N N
"""


class TestForestFragTrivial(TestCase):
    # TODO: replace by unified handing of maps
    to_remove = []
    forest = 'rff_test_forest_trivial'
    forest_frag = 'rff_test_forest_frag_trivial'
    forest_frag_ref = 'rff_test_forest_frag_trivial_ref'

    def setUp(self):
        self.use_temp_region()

    def tearDown(self):
        self.del_temp_region()
        if 0 and self.to_remove:
            self.runModule('g.remove', flags='f', type='raster',
                           name=','.join(self.to_remove), verbose=True)

    def forest_frag_general(self, forest, window, reference):
        self.runModule('r.in.ascii', input='-', stdin_=forest,
                       output=self.forest)
        self.to_remove.append(self.forest)
        self.runModule('g.region', raster=self.forest)
        self.assertRasterMinMax(self.forest,
                                refmin=0, refmax=1)
        self.runModule('r.in.ascii', input='-', stdin_=reference,
                       output=self.forest_frag_ref)
        self.to_remove.append(self.forest_frag_ref)
        pf_ref = self.forest_frag_ref + '_pf'
        self.runModule('r.in.ascii', input='-', stdin_=PF_RIITTERS,
                       output=pf_ref)
        self.to_remove.append(pf_ref)
        pff_ref = self.forest_frag_ref + '_pff'
        self.runModule('r.in.ascii', input='-', stdin_=PFF_RIITTERS,
                       output=pff_ref)
        self.to_remove.append(pff_ref)
        # just check if the reference is all right
        theoretical_min = 0
        theoretical_max = 6
        self.assertRasterMinMax(self.forest_frag_ref,
                                refmin=theoretical_min,
                                refmax=theoretical_max)
        ref_univar = dict(null_cells=8)
        self.assertRasterFitsUnivar(raster=self.forest_frag_ref,
                                    reference=ref_univar, precision=0)

        # actually run the module
        pf = self.forest_frag + '_pf'
        pff = self.forest_frag + '_pff'
        self.assertModule('r.forestfrag', input=self.forest,
                          output=self.forest_frag, window=window,
                          pf=pf, pff=pff)
        self.assertRasterExists(self.forest_frag)
        self.to_remove.append(self.forest_frag)
        self.assertRasterExists(pf)
        self.to_remove.append(pf)
        self.assertRasterExists(pff)
        self.to_remove.append(pff)

        # check the basic properties
        self.assertRasterMinMax(self.forest_frag,
                                refmin=theoretical_min,
                                refmax=theoretical_max)
        ref_univar = dict(null_cells=0)
        self.assertRasterFitsUnivar(raster=self.forest_frag,
                                    reference=ref_univar, precision=0)

        self.runModule('g.region', zoom=pff_ref)

        # check cell by cell

        self.assertRastersNoDifference(actual=pf,
                                       reference=pf_ref,
                                       precision=0.01)

        self.assertRastersNoDifference(actual=pff,
                                       reference=pff_ref,
                                       precision=0.01)

        self.assertRastersNoDifference(actual=self.forest_frag,
                                       reference=self.forest_frag_ref,
                                       precision=0)  # it's CELL type


    def test_riitters(self):
        self.forest_frag_general(FOREST_RIITTERS, 3, FRAG_RIITTERS)


if __name__ == '__main__':
    test()
