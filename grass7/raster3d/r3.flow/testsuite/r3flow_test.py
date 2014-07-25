# -*- coding: utf-8 -*-
"""
Test of r3.flow

@author Anna Petrasova
"""
from grass.gunittest import TestCase, test


class FlowlineTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.use_temp_region()
        cls.runModule("g.region", res=10, res3=10, n=80, s=0, w=0, e=120, b=0, t=50)
        cls.runModule("r3.mapcalc", expression="map_1 = 100", overwrite=True)
        cls.runModule("r3.mapcalc", expression="map_2 = -20", overwrite=True)
        cls.runModule("r3.mapcalc", expression="map_3 = 0.01", overwrite=True)
        cls.runModule("r3.mapcalc", expression="map_4 = col() + row() + depth()", overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """!Remove the temporary region"""
        cls.del_temp_region()
        cls.runModule('g.remove', rast3d=['map_1', 'map_2', 'map_3', 'map_4'])

    def test_interpolation(self):
        self.assertModuleKeyValue('test.r3flow', test='interpolation',
                                  coordinates=[100, 55, 11], input=['map_1', 'map_2', 'map_3'],
                                  reference={'return': 0, 'values': [100, -20, 0.01]},
                                  precision=1e-10, sep='=')
        self.assertModuleKeyValue('test.r3flow', test='interpolation',
                                  coordinates=[5, 5, 5], input=['map_1', 'map_2', 'map_3'],
                                  reference={'return': 0, 'values': [100, -20, 0.01]},
                                  precision=1e-10, sep='=')
        self.assertModuleKeyValue('test.r3flow', test='interpolation',
                                  coordinates=[10, 10, 60], input=['map_1', 'map_2', 'map_3'],
                                  reference={'return': -1},
                                  precision=1e-10, sep='=')
        self.assertModuleKeyValue('test.r3flow', test='interpolation',
                                  coordinates=[25, 69, 17], input=['map_4', 'map_4', 'map_4'],
                                  reference={'return': 0, 'values': [7.8, 7.8, 7.8]},
                                  precision=1e-10, sep='=')
        self.assertModuleKeyValue('test.r3flow', test='interpolation',
                                  coordinates=[81, 30, 25], input=['map_4', 'map_4', 'map_4'],
                                  reference={'return': 0, 'values': [18.1, 18.1, 18.1]},
                                  precision=1e-10, sep='=')


if __name__ == '__main__':
    test()
