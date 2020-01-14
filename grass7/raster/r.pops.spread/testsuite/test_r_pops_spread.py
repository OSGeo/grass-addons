from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import call_module


class TestSpread(TestCase):

    viewshed = 'test_viewshed_from_elevation'

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule('g.region', raster='lsat7_2002_30',  res=85.5, flags='a')
        cls.runModule('i.vi', red='lsat7_2002_30', output='ndvi', viname='ndvi', 
                      nir='lsat7_2002_40', green='lsat7_2002_20', blue='lsat7_2002_10')
        cls.runModule('r.mapcalc', expression="host = if (ndvi > 0, graph(ndvi, 0, 0, 1, 20), 0)")
        cls.runModule('v.to.rast', input='railroads', output='infection_', use='val', value=1)
        cls.runModule('r.null', map='infection_', null=0)
        cls.runModule('r.mapcalc', expression='infection = if(ndvi > 0, infection_, 0)')
        cls.runModule('r.mapcalc', expression='max_host = 100')
        cls.runModule('r.circle', flags='b', output='circle', coordinates=[639445, 218237], max=2000)
        cls.runModule('r.mapcalc', expression='treatment = if(isnull(circle), 0, 0.8)')

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule('g.remove', flags='f', type='raster',
                      name=['max_host', 'infection_', 'infection', 'host',
                            'ndvi', 'circle', 'treatment'])

    def tearDown(cls):
        """Remove maps after each test method"""
        # TODO: eventually, removing maps should be handled through testing framework fucntions
        cls.runModule('g.remove', flags='f', type='raster',
                      pattern='average*,single*,stddev*,probability*,dead*')
                     
                      
    def test_outputs(self):
        start = 2019
        end = 2022
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_time=start, end_time=end, seasonality=[1, 12], step='week',
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5)
        self.assertRasterExists('average')
        self.assertRasterExists('stddev')
        self.assertRasterExists('probability')
        self.assertRasterExists('average' + '_{}_12_31'.format(end))
        self.assertRasterExists('probability' + '_{}_12_31'.format(end))
        self.assertRasterExists('single' + '_{}_12_31'.format(end))
        self.assertRasterExists('stddev' + '_{}_12_31'.format(end))

        values = 'null_cells=0\nmin=0\nmax=18\nmean=1.79448'
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = 'null_cells=0\nmin=0\nmax=100\nmean=34.0552'
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)
        values = 'null_cells=0\nmin=0\nmax=8.0895\nmean=0.949804'
        self.assertRasterFitsUnivar(raster='stddev', reference=values, precision=0.001)


    def test_outputs_mortality(self):
        start = 2019
        end = 2022
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_time=start, end_time=end, seasonality=[1, 12], step='week',
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5,
                          flags='m', mortality_rate=0.5, mortality_time_lag=1, mortality_series='dead')
        self.assertRasterExists('dead' + '_{}_12_31'.format(end))

        values = 'null_cells=0\nmin=0\nmax=6\nmean=0.672013'
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = 'null_cells=0\nmin=0\nmax=100\nmean=26.7338'
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)
        values = 'null_cells=0\nmin=0\nmax=15\nmean=0.701079'
        self.assertRasterFitsUnivar(raster='dead' + '_{}_12_31'.format(end), reference=values, precision=0.001)


    def test_outputs_mortality_treatment(self):
        start = 2019
        end = 2022
        self.assertModule('r.pops.spread', host='host', total_plants='max_host', infected='infection',
                          average='average', average_series='average', single_series='single',
                          stddev='stddev', stddev_series='stddev',
                          probability='probability', probability_series='probability',
                          start_time=start, end_time=end, seasonality=[1, 12], step='week',
                          reproductive_rate=1, natural_dispersal_kernel='exponential', natural_distance=50,
                          natural_direction='W', natural_direction_strength=3,
                          anthropogenic_dispersal_kernel='cauchy', anthropogenic_distance=1000,
                          anthropogenic_direction_strength=0, percent_natural_dispersal=0.95,
                          random_seed=1, runs=5, nprocs=5,
                          flags='m', mortality_rate=0.5, mortality_time_lag=1, mortality_series='dead',
                          treatments='treatment', treatment_date='2020-12-01', treatment_length=0,
                          treatment_application='ratio_to_all')

        values = 'null_cells=0\nmin=0\nmax=6\nmean=0.546419'
        self.assertRasterFitsUnivar(raster='average', reference=values, precision=0.001)
        values = 'null_cells=0\nmin=0\nmax=100\nmean=22.5336'
        self.assertRasterFitsUnivar(raster='probability', reference=values, precision=0.001)


if __name__ == '__main__':
    test()
