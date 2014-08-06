# -*- coding: utf-8 -*-
"""
Test of r3.gradient

@author Anna Petrasova
"""
from grass.gunittest import TestCase, test


r3univar_test_grad_x = """
n=600
null_cells=0
cells=600
min=0.00902566899999995
max=0.0993248405000001
range=0.0902991715000001
mean=0.0641879624599999
mean_of_abs=0.0641879624599999
stddev=0.0243482677445681
variance=0.000592838142161176
coeff_var=37.9327631091908
sum=38.512777476
"""


r3univar_test_grad_y = """
n=600
null_cells=0
cells=600
min=-0.0990409449999998
max=-0.00774536350000012
range=0.0912955814999997
mean=-0.0563959154616667
mean_of_abs=0.0563959154616667
stddev=0.0244377519801364
variance=0.000597203721842658
coeff_var=-43.3324856597942
sum=-33.837549277"""


r3univar_test_grad_z = """
n=600
null_cells=0
cells=600
min=0.00643308800000026
max=0.0967259644999999
range=0.0902928764999997
mean=0.0336457494116667
mean_of_abs=0.0336457494116667
stddev=0.0186882020765464
variance=0.000349248896853835
coeff_var=55.5440208743464
sum=20.187449647
"""


class GradientTest(TestCase):

    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.use_temp_region()
        cls.runModule('g.region', res3=10, n=100, s=0, w=0, e=120, b=0, t=50)
        cls.runModule('r3.in.ascii', input='data/test_map_1', output='test_map_1_ref', overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """!Remove the temporary region"""
        cls.del_temp_region()
        cls.runModule('g.remove', rast3d=['test_map_1_ref', 'test_grad_x',
                                          'test_grad_y', 'test_grad_z'])

    def test_gradient_runs(self):
        self.assertModuleFail('r3.gradient', input='test_map_1_ref',
                              output=['test_grad_x', 'test_grad_y'], overwrite=True)
        self.assertModule('r3.gradient', input='test_map_1_ref',
                          output=['test_grad_x', 'test_grad_y', 'test_grad_z'], overwrite=True)

    def test_gradient(self):
        self.runModule('r3.gradient', input='test_map_1_ref',
                       output=['test_grad_x', 'test_grad_y', 'test_grad_z'], overwrite=True)
        self.assertRaster3dFitsUnivar(raster='test_grad_x', reference=r3univar_test_grad_x, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_y', reference=r3univar_test_grad_y, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_z', reference=r3univar_test_grad_z, precision=1e-8)

    def test_gradient_block(self):
        self.assertModule('r3.gradient', input='test_map_1_ref', block_size=[200, 2, 50],
                          output=['test_grad_x', 'test_grad_y', 'test_grad_z'], overwrite=True)
        self.assertRaster3dFitsUnivar(raster='test_grad_x', reference=r3univar_test_grad_x, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_y', reference=r3univar_test_grad_y, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_z', reference=r3univar_test_grad_z, precision=1e-8)

    def test_gradient_procs(self):
        self.assertModule('r3.gradient', input='test_map_1_ref', block_size=[200, 2, 50], nprocs=3,
                          output=['test_grad_x', 'test_grad_y', 'test_grad_z'], overwrite=True)
        self.assertRaster3dFitsUnivar(raster='test_grad_x', reference=r3univar_test_grad_x, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_y', reference=r3univar_test_grad_y, precision=1e-8)
        self.assertRaster3dFitsUnivar(raster='test_grad_z', reference=r3univar_test_grad_z, precision=1e-8)


if __name__ == '__main__':
    test()
