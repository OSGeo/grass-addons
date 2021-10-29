#!/usr/bin/env python3

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPotential(TestCase):

    output = 'suitability'
    result = 'result'

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule('g.region', raster="lsat7_2002_30@PERMANENT")
        cls.runModule('r.unpack', input='data/result.pack', output=cls.result)
        cls.runModule('r.mapcalc',
                      expression="ndvi_2002 = double(lsat7_2002_40@PERMANENT - lsat7_2002_30@PERMANENT) / double(lsat7_2002_40@PERMANENT + lsat7_2002_30@PERMANENT)")
        cls.runModule('r.mapcalc', expression="urban_2002 = if(ndvi_2002 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))")
        cls.runModule('r.slope.aspect', elevation='elevation', slope='slope')
        cls.runModule('r.grow.distance', input='lakes', distance='lakes_dist')
        cls.runModule('r.mapcalc', expression="lakes_dist_km = lakes_dist/1000.")
        cls.runModule('v.to.rast', input='streets_wake', output='streets', use='val')
        cls.runModule('r.grow.distance', input='streets', distance='streets_dist')
        cls.runModule('r.mapcalc', expression="streets_dist_km = streets_dist/1000.")
        cls.runModule('r.futures.devpressure', input='urban_2002', output='devpressure', method='gravity', size=15, flags='n')

    @classmethod
    def tearDownClass(cls):
        cls.runModule('g.remove', flags='f', type='raster',
                      name=['slope', 'lakes_dist', 'lakes_dist_km', 'streets',
                            'streets_dist', 'streets_dist_km', 'devpressure',
                            'ndvi_2002', 'urban_2002', cls.result])
        cls.del_temp_region()

    def tearDown(self):
        self.runModule('g.remove', flags='f', type='raster', name=self.output)

    def test_potsurface_run(self):
        """Test if result is in expected limits"""
        self.assertModule('r.futures.potsurface', input='data/potential.csv',
                          output=self.output, subregions='zipcodes')
        self.assertRastersNoDifference(actual=self.output, reference=self.result, precision=1e-6)


if __name__ == '__main__':
    test()
