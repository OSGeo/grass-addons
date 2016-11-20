#!/usr/bin/env python

############################################################################
#
# MODULE:        r_forestfrag_ncspm
# AUTHOR:        Vaclav Petras
# PURPOSE:       Test using NC SPM data
# COPYRIGHT:     (C) 2016 by Vaclav Petras and the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
import grass.script.raster as gr


class TestForestFrag(TestCase):
    # TODO: replace by unified handing of maps
    to_remove = []
    landclass = 'landclass96'  # in full NC SPM
    forest = 'rff_test_forest'
    forest_frag = 'rff_test_forest_frag'

    def setUp(self):
        self.use_temp_region()
        self.runModule('g.region', raster=self.landclass)
        gr.mapcalc("{f} = if({c} == 5, 1, 0)".format(c=self.landclass,
                                                     f=self.forest))
        self.to_remove.append(self.forest)

    def tearDown(self):
        self.del_temp_region()
        if self.to_remove:
            self.runModule('g.remove', flags='f', type='raster',
                           name=','.join(self.to_remove), verbose=True)

    def test_3x3(self):
        self.assertModule('r.forestfrag', input=self.forest,
                          output=self.forest_frag, window=3)
        self.assertRasterExists(self.forest_frag)
        self.to_remove.append(self.forest_frag)
        self.assertRasterMinMax(self.forest_frag, refmin=0, refmax=6)
        # we don't have a check sum test for raster, so we just test all
        ref = dict(north=228527.25, south=215018.25,
                   east=644971, west=629980,
                   nsres=28.5, ewres=28.5, rows=474, cols=526,
                   cells=249324, datatype='CELL', ncats=6)
        self.assertRasterFitsInfo(raster=self.forest_frag,
                                  reference=ref, precision=0.0006)
        ref = dict(n=249323, null_cells=1, cells=249324, min=0, max=5,
                   range=5, mean=2.2925, mean_of_abs=2.2925,
                   stddev=2.3564, variance=5.5527, coeff_var=102.7879,
                   sum=571572)
        self.assertRasterFitsUnivar(raster=self.forest_frag,
                                    reference=ref, precision=0.0006)

if __name__ == '__main__':
    test()
