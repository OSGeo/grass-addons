#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test GPOT implementation
"""
from __future__ import (absolute_import, division, generators, nested_scopes,
                        print_function, unicode_literals, with_statement)

import os

from numpy.testing import assert_almost_equal

import gpot as gpot
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import call_module
from grass.gunittest.main import test
# ==================================================================
# Start testing the library
from grass.pygrass.raster import RasterRow

# ==================================================================
# Define value and results to be tested as scalar and as raster
GRND_CONDUCTIVITY = [2.17, 2.48, 2.66, 3.39, 4.13, 4.87]
Us = [1.0274630179071e-06, 8.9903014066873e-07, 8.3819351460844e-07,
      6.5769756603494e-07, 5.3985345008679e-07, 6.4095126250551e-07, ]
Uc = [1.0417333376003e-04, 9.1151667040024e-05, 8.4983509120022e-05,
      6.6683225445209e-05, 5.4735141467133e-05, 6.4626301329975e-05, ]
GMAX = [8.78102488885101, 8.91521113405854, 8.98562231568097,
        9.22931537948381, 9.42773116917176, 9.26798647784601, ]
ENRG = [7.8201953800014, 8.5483188164961, 8.9481702027677,
        10.4223290667456, 11.7173041500822, 14.2980012600415, ]
PWR = [892.71636758007, 975.83548133517, 1021.48061675430,
       1189.76359209425, 1337.59179795458, 1632.19192466227, ]
GRND_TEMP = 10.
GRND_CAPACITY = 2.5
FLUID_TEMP = -2.
HEATING_SEASON = 180 * 24 * 60 * 60
LIFETIME = 50 * 365 * 24 * 60 * 60

BH_DEPTH = 100.
BH_RADIUS = 0.075
BH_THERM_RESISTANCE = 0.1

PIPE_RADIUS = 0.016
NUM_PIPES = 4
GROUT_CONDUCTIVITY = 2.




def assert_raster_no_difference(reference, actual, precision):
    with RasterRow(reference) as ref, RasterRow(actual) as act:
        for i_row, (r_row, a_row) in enumerate(zip(ref, act)):
            diff = abs(r_row - a_row) > precision
            if diff.any():
                cols = diff.nonzero()
                msg = ("The two rows are different!\nrow:{i_row}, "
                       "cols={cols}\nref: {ref}\nact:{act}")
                raise AssertionError(msg.format(i_row=i_row, cols=cols,
                                                ref=r_row[cols],
                                                act=a_row[cols]))


class TestBHEresistence(TestCase):
    def test_resistence(self):
        """Test function that return the thermal resistence of a BHE"""
        res = gpot.get_borehole_resistence(borehole_radius=BH_RADIUS,
                                           pipe_radius=PIPE_RADIUS,
                                           number_pipes=NUM_PIPES,
                                           grout_conductivity=GROUT_CONDUCTIVITY)
        assert_almost_equal(0.067780287314088528, res)


class TestGPot(TestCase):
    def test_norm_time(self):
        """Test time normalization function
        """
        for time, result in zip((HEATING_SEASON, LIFETIME),
                                (0.00011302806712962963, 1.1147973744292237e-06)):
            res = gpot.norm_time(time, borehole_radius=BH_RADIUS,
                                 ground_conductivity=2.,
                                 ground_capacity=GRND_CAPACITY)
            assert_almost_equal(result, res)


class TestRasterGPot(TestCase):
    precision = 1e-7
    base = 'gpottest_'
    dirpath = os.path.join('testsuite', 'data')

    # define names
    grnd_conductivity = base + 'ground_conductivity'
    norm_time_hs_comp = base + 'normtime_heatingseason_comp'
    norm_time_hs_ref = base + 'normtime_heatingseason_ref'
    norm_time_lt_comp = base + 'normtime_lifetime_comp'
    norm_time_lt_ref = base + 'normtime_lifetime_ref'
    gmax_comp = base + 'gmax_comp'
    gmax_ref = base + 'gmax_ref'
    power_comp = base + 'power_comp'
    power_ref = base + 'power_ref'
    energy_comp = base + 'energy_comp'
    energy_ref = base + 'energy_ref'
    length_comp = base + 'length_comp'
    length_ref = base + 'length_ref'

    # define paths
    grnd_conductivity_file = os.path.join(dirpath, 'ground_capacity_xs.ascii')
    norm_time_hs_ref_file = os.path.join(dirpath, 'norm_time_heatseason_xs.ascii')
    norm_time_lt_ref_file = os.path.join(dirpath, 'norm_time_lifetime_xs.ascii')
    gmax_ref_file = os.path.join(dirpath, 'gmax_xs.ascii')
    power_ref_file = os.path.join(dirpath, 'power_xs.ascii')
    energy_ref_file = os.path.join(dirpath, 'energy_xs.ascii')
    length_ref_file = os.path.join(dirpath, 'length_xs.ascii')

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        call_module('r.in.ascii', input=cls.grnd_conductivity_file,
                    output=cls.grnd_conductivity, overwrite=True)
        call_module('r.in.ascii', input=cls.norm_time_hs_ref_file,
                    output=cls.norm_time_hs_ref, overwrite=True)
        call_module('r.in.ascii', input=cls.norm_time_lt_ref_file,
                    output=cls.norm_time_lt_ref, overwrite=True)
        call_module('r.in.ascii', input=cls.gmax_ref_file,
                    output=cls.gmax_ref, overwrite=True)
        call_module('r.in.ascii', input=cls.power_ref_file,
                    output=cls.power_ref, overwrite=True)
        call_module('r.in.ascii', input=cls.energy_ref_file,
                    output=cls.energy_ref, overwrite=True)
        call_module('g.region', raster=cls.grnd_conductivity)

    @classmethod
    def tearDownClass(cls):
        # TODO: clean
        cls.del_temp_region()

    def test_norm_time_hs(self):
        """Test time normalization function applied to raster for heating season
        """
        # heating season
        gpot.r_norm_time(self.norm_time_hs_comp, HEATING_SEASON,
                         borehole_radius=BH_RADIUS,
                         ground_conductivity=self.grnd_conductivity,
                         ground_capacity=GRND_CAPACITY,
                         execute=True, overwrite=True)
        # check against reference data
        assert_raster_no_difference(actual=self.norm_time_hs_comp,
                                    reference=self.norm_time_hs_ref,
                                    precision=self.precision)

    def test_norm_time_lt(self):
        """Test time normalization function applied to raster for lifetime
        """
        # lifetime
        gpot.r_norm_time(self.norm_time_lt_comp, LIFETIME,
                         borehole_radius=BH_RADIUS,
                         ground_conductivity=self.grnd_conductivity,
                         ground_capacity=GRND_CAPACITY,
                         execute=True, overwrite=True)
        # check against reference data
        assert_raster_no_difference(actual=self.norm_time_lt_comp,
                                    reference=self.norm_time_lt_ref,
                                    precision=self.precision)
#        self.assertRastersNoDifference(actual=norm_time_hs_comp,
#                                       reference=norm_time_hs_ref,
#                                       precision=self.precision)

    def test_norm_thermal_alteration(self):
        """Test normarl thermal alteration"""
        # out, tc, uc, us, execute=True, **kwargs)
        gpot.r_norm_thermal_alteration(out=self.gmax_comp,
                                       tc=HEATING_SEASON/(365. * 24 * 60 * 60),
                                       uc=self.norm_time_hs_ref,
                                       us=self.norm_time_lt_ref,
                                       execute=True, overwrite=True)
        assert_raster_no_difference(actual=self.gmax_comp,
                                    reference=self.gmax_ref,
                                    precision=self.precision)

    def test_power(self):
        """Test power function"""
        gpot.r_power(out=self.power_comp,
                     tc=180./365.,
                     ground_conductivity=self.grnd_conductivity,
                     ground_temperature=10.,
                     fluid_limit_temperature=-2.,
                     borehole_length=100., borehole_resistence=0.1,
                     gmax=self.gmax_ref,
                     execute=True, overwrite=True)
        assert_raster_no_difference(actual=self.power_comp,
                                    reference=self.power_ref,
                                    precision=self.precision)

    def test_energy(self):
        """Test energy function"""
        gpot.r_energy(out=self.energy_comp, power=self.power_ref,
                      execute=True, overwrite=True)
        assert_raster_no_difference(actual=self.energy_comp,
                                    reference=self.energy_ref,
                                    precision=self.precision)


if __name__ == '__main__':
    test()
