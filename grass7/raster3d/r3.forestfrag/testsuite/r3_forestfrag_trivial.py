#!/usr/bin/env python

############################################################################
#
# MODULE:        r3_forestfrag_trivial
# AUTHOR:        Vaclav Petras
# PURPOSE:       Test using a small example computed by hand
# COPYRIGHT:     (C) 2016 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


FOREST = """\
version: grass7
order: nsbt
north: 10
south: 8
east: 20
west: 18
top: 7
bottom: 5
rows: 3
cols: 3
levels: 3
1 0 0 
1 0 0 
0 0 0 
1 1 0 
0 1 1 
1 0 1 
0 1 1 
0 0 0 
0 0 0 
"""

# output contains all cells but we check just the middle one
PF = """\
version: grass7
order: nsbt
north: 10
south: 8
east: 20
west: 18
top: 7
bottom: 5
rows: 3
cols: 3
levels: 3
N N N
N N N
N N N
N N N
N 0.370 N
N N N
N N N
N N N
N N N
"""

PFF = """\
version: grass7
order: nsbt
north: 10
south: 8
east: 20
west: 18
top: 7
bottom: 5
rows: 3
cols: 3
levels: 3
N N N
N N N
N N N
N N N
N 0.235 N
N N N
N N N
N N N
N N N
"""

FRAG = """\
version: grass7
order: nsbt
north: 10
south: 8
east: 20
west: 18
top: 7
bottom: 5
rows: 3
cols: 3
levels: 3
N N N
N N N
N N N
N N N
N 1 N
N N N
N N N
N N N
N N N
"""


class TestForestFragTrivial(TestCase):
    # TODO: replace by unified handing of maps
    to_remove = []
    forest = 'r3ff_test_forest_trivial'
    forest_frag = 'r3ff_test_forest_frag_trivial'
    forest_frag_ref = 'r3ff_test_forest_frag_trivial_ref'
    pf_ref = 'r3ff_test_forest_frag_trivial_ref_pf'
    pff_ref = 'r3ff_test_forest_frag_trivial_ref_pff'

    def setUp(self):
        self.use_temp_region()
        self.runModule('r3.in.ascii', input='-', stdin_=FOREST,
                       output=self.forest)
        self.to_remove.append(self.forest)
        self.runModule('g.region', raster_3d=self.forest)
        self.runModule('r3.in.ascii', input='-', stdin_=PF,
                       output=self.pf_ref,
                       null_value='N')
        self.to_remove.append(self.pf_ref)
        self.runModule('r3.in.ascii', input='-', stdin_=PFF,
                       output=self.pff_ref,
                       null_value='N')
        self.to_remove.append(self.pff_ref)
        self.runModule('r3.in.ascii', input='-', stdin_=FRAG,
                       output=self.forest_frag_ref,
                       null_value='N')
        self.to_remove.append(self.forest_frag_ref)
        

    def tearDown(self):
        self.del_temp_region()
        if self.to_remove:
            self.runModule('g.remove', flags='f', type='raster',
                           name=','.join(self.to_remove), verbose=True)

    def test_simple_window(self):
        pf = self.forest_frag + '_pf'
        pff = self.forest_frag + '_pff'
        self.assertModule('r3.forestfrag', input=self.forest,
                          output=self.forest_frag, size=3,
                          pf=pf, pff=pff, flags='t')
        self.assertRaster3dExists(self.forest_frag)
        self.to_remove.append(self.forest_frag)
        self.assertRaster3dExists(pf)
        self.to_remove.append(pf)
        self.assertRaster3dExists(pff)
        self.to_remove.append(pff)

        # check the basic properties
        ref_univar = dict(null_cells=0, cells=27)
        self.assertRaster3dFitsUnivar(raster=self.forest_frag,
                                    reference=ref_univar, precision=0)
        # the null cells requirements for pf and pff are fuzzy
        ref_univar = dict(cells=27)
        self.assertRaster3dFitsUnivar(raster=pf,
                                    reference=ref_univar, precision=0)
        self.assertRaster3dFitsUnivar(raster=pff,
                                    reference=ref_univar, precision=0)
        self.assertRaster3dMinMax(pf, refmin=0, refmax=1)
        self.assertRaster3dMinMax(pff, refmin=0, refmax=1)
        self.assertRaster3dMinMax(self.forest_frag, refmin=0, refmax=6)

        # to check just the middle cell
        # the current implementation of assertRasters3dNoDifference
        # ignores nulls, so it just works regardless of region
        # there is no zoom for 3D
        # self.runModule('g.region', zoom=self.pff_ref)

        # check the values
        self.assertRasters3dNoDifference(actual=pf,
                                         reference=self.pf_ref,
                                         precision=0.001)

        self.assertRasters3dNoDifference(actual=pff,
                                         reference=self.pff_ref,
                                         precision=0.001)

        self.assertRasters3dNoDifference(actual=self.forest_frag,
                                         reference=self.forest_frag_ref,
                                         precision=0)  # it's CELL type


if __name__ == '__main__':
    test()
