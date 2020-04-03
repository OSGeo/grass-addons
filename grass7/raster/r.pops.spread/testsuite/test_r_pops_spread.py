#!/usr/bin/env python3

"""Test of r.pops.spread.

.. moduleauthor:: Anna Petrasova
.. moduleauthor:: Vaclav Petras
"""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import call_module


class TestSpread(TestCase):

    viewshed = 'test_viewshed_from_elevation'

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule('g.region', raster='lsat7_2002_30',  res=85.5, flags='a')
        cls.runModule('r.mapcalc',
            expression="ndvi = double(lsat7_2002_40 - lsat7_2002_30) / double(lsat7_2002_40 + lsat7_2002_30)")
        cls.runModule('r.mapcalc', expression="host = round(if(ndvi > 0, graph(ndvi, 0, 0, 1, 20), 0))")
        cls.runModule('r.mapcalc', expression="host_nulls = if(host == 0, null(), host)")
        cls.runModule('v.to.rast', input='railroads', output='infection_', use='val', value=1)
        cls.runModule('r.null', map='infection_', null=0)
        cls.runModule('r.mapcalc', expression='infection = if(ndvi > 0, infection_, 0)')
        cls.runModule('r.mapcalc', expression='infection_nulls = if(infection == 0, null(), infection)')
        cls.runModule('r.mapcalc', expression='max_host = 100')
        cls.runModule('r.circle', flags='b', output='circle', coordinates=[639445, 218237], max=2000)
        cls.runModule('r.mapcalc', expression='treatment = if(isnull(circle), 0, 0.8)')

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule('g.remove', flags='f', type='raster',
                      name=['max_host', 'infection_', 'infection', 'infection_nulls',
                            'host', 'host_nulls', 'ndvi', 'circle', 'treatment'])

    def tearDown(cls):
        """Remove maps after each test method"""
        # TODO: eventually, removing maps should be handled through testing framework fucntions
        cls.runModule('g.remove', flags='f', type='raster',
                      pattern='average*,single*,stddev*,probability*,dead*')
                     
                      
    def test_outputs(self):
        start = '2019-01-01'
        end = '2022-12-31'
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_date=start, end_date=end, seasonality=[1, 12], step_unit='week',
                          step_num_units=1,
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5)
        self.assertRasterExists('average')
        self.assertRasterExists('stddev')
        self.assertRasterExists('probability')
        end = end[:4]
        self.assertRasterExists('average' + '_{}_12_31'.format(end))
        self.assertRasterExists('probability' + '_{}_12_31'.format(end))
        self.assertRasterExists('single' + '_{}_12_31'.format(end))
        self.assertRasterExists('stddev' + '_{}_12_31'.format(end))

        ref_float = dict(datatype="DCELL")
        ref_int = dict(datatype="CELL")
        self.assertRasterFitsInfo(raster="average", reference=ref_float)
        self.assertRasterFitsInfo(raster="stddev", reference=ref_float)
        self.assertRasterFitsInfo(raster="probability", reference=ref_float)
        self.assertRasterFitsInfo(
            raster="single" + "_{}_12_31".format(end),
            reference=ref_int
        )
        self.assertRasterFitsInfo(
            raster="average" + "_{}_12_31".format(end),
            reference=ref_float
        )
        self.assertRasterFitsInfo(
            raster="probability" + "_{}_12_31".format(end),
            reference=ref_float
        )
        self.assertRasterFitsInfo(
            raster="stddev" + "_{}_12_31".format(end),
            reference=ref_float
        )

        values = dict(null_cells=0, min=0, max=18, mean=1.777)
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=100, mean=33.767)
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=7.440, mean=0.947)
        self.assertRasterFitsUnivar(raster='stddev', reference=values, precision=0.001)


    def test_nulls_in_input(self):
        """Same as test_outputs() but using inputs with null values."""
        start = '2019-01-01'
        end = '2022-12-31'
        self.assertModule('r.pops.spread', host='host_nulls', total_plants='max_host', infected='infection_nulls',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_date=start, end_date=end, seasonality=[1, 12], step_unit='week',
                          step_num_units=1,
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5)
        self.assertRasterExists('average')
        self.assertRasterExists('stddev')
        self.assertRasterExists('probability')
        end = end[:4]
        self.assertRasterExists('average' + '_{}_12_31'.format(end))
        self.assertRasterExists('probability' + '_{}_12_31'.format(end))
        self.assertRasterExists('single' + '_{}_12_31'.format(end))
        self.assertRasterExists('stddev' + '_{}_12_31'.format(end))

        values = dict(null_cells=0, min=0, max=18, mean=1.777)
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=100, mean=33.767)
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=7.440, mean=0.947)
        self.assertRasterFitsUnivar(raster='stddev', reference=values, precision=0.001)


    def test_outputs_mortality(self):
        start = '2019-01-01'
        end = '2022-12-31'
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_date=start, end_date=end, seasonality=[1, 12], step_unit='week',
                          step_num_units=1,
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5,
                          flags='m', mortality_rate=0.5, mortality_time_lag=1, mortality_series='dead')
        end = end[:4]
        self.assertRasterExists('dead' + '_{}_12_31'.format(end))

        values = dict(null_cells=0, min=0, max=6, mean=0.652)
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=100, mean=25.893)
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=15, mean=0.752)
        self.assertRasterFitsUnivar(raster='dead' + '_{}_12_31'.format(end), reference=values, precision=0.001)


    def test_outputs_mortality_treatment(self):
        start = '2019-01-01'
        end = '2022-12-31'
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_date=start, end_date=end, seasonality=[1, 12], step_unit='week',
                          step_num_units=1,
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5,
                          flags='m', mortality_rate=0.5, mortality_time_lag=1, mortality_series='dead',
                          treatments='treatment', treatment_date='2020-12-01', treatment_length=0,
                          treatment_application='ratio_to_all')

        values = dict(null_cells=0, min=0, max=5.6, mean=0.519)
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = dict(null_cells=0, min=0, max=100, mean=21.492)
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)


if __name__ == '__main__':
    test()
