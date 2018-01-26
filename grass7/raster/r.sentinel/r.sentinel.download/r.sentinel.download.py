#!/usr/bin/env python2
#
############################################################################
#
# MODULE:      r.sentinel.download
# AUTHOR(S):   Martin Landa
# PURPOSE:     Downloads Sentinel data from  Copernicus Open Access Hub
#              using sentinelsat library.
# COPYRIGHT:   (C) 2018 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Downloads Sentinel data from Copernicus Open Access Hub using sentinelsat library.
#% keyword: raster
#% keyword: imagery
#% keyword: sentinel
#% keyword: download
#%end
#%option G_OPT_V_MAP
#% label: Name of input vector map to define Area of Interest (AOI)
#% description: If not given than current computational extent is used
#% required: no
#%end
#%option
#% key: clouds
#% type: integer
#% description: Maximum cloud cover percentage for Sentinel scene
#% answer: 30
#% required: no
#%end
#%option
#% key: producttype
#% type: string
#% description: Sentinel product type to filter
#% required: no
#% options: SLC,GRD,OCN,S2MSI1C,S2MSI2Ap
#% answer: S2MSI1C
#%end
#%option
#% key: limit
#% type: integer
#% description: Limit number of Sentinel products
#%end
#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#%end
#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#%end
#%option
#% key: user
#% type: string
#% description: Username for connecting SciHub
#% required: yes
#%end
#%option
#% key: password
#% type: string
#% description: Password for connecting SciHub
#% required: yes
#%end
#%option G_OPT_M_DIR
#% key: output
#% description: Name for output directory where to store downloaded Sentinel data
#% required: no
#%end
#%option G_OPT_V_OUTPUT
#% key: footprints
#% description: Name for output vector map with footprints
#% required: no
#%end
#%option
#% key: sort
#% description: Sort by values in given order
#% multiple: yes
#% options: ingestiondate,cloudcoverpercentage,footprint
#% answer: cloudcoverpercentage,ingestiondate,footprint
#%end
#%option
#% key: order
#% description: Sort order (see sort parameter)
#% options: asc,desc
#% answer: asc
#%end
#%flag
#% key: l
#% description: List filtered products and exist
#%end
#%rules
#% required: output,-l
#%end

import os
import sys
import logging
import zipfile

from collections import OrderedDict

import grass.script as gs

def get_aoi_box(vector=None):
    args = {}
    if vector:
        args['vector'] = vector
    info = gs.parse_command('g.region', flags='uplg', **args)

    return 'POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat}, {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))'.format(
        nw_lat=info['nw_lat'], nw_lon=info['nw_long'], ne_lat=info['ne_lat'], ne_lon=info['ne_long'],
        sw_lat=info['sw_lat'], sw_lon=info['sw_long'], se_lat=info['se_lat'], se_lon=info['se_long']
    )

class SentinelDownloader(object):
    def __init__(self, user, password):
        try:
            from sentinelsat import SentinelAPI
        except ImportError as e:
            gs.fatal("Module requires sentinelsat library: {}".format(e))
        try:
            import pandas
        except ImportError as e:
            gs.fatal("Module requires pandas library: {}".format(e))

        # init logger
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler(
            sys.stderr
        ))

        # connect SciHub via API
        self._api = SentinelAPI(options['user'], options['password'],
                                api_url='https://scihub.copernicus.eu/dhus'
        )

        self._products_df_sorted = None
        
    def filter(self, area,
               clouds=None, producttype=None, limit=None,
               start=None, end=None, sortby=[], asc=True):
        args = {}
        if clouds:
            args['cloudcoverpercentage'] = (0, clouds)
        if producttype:
            args['producttype'] = producttype
        if not start:
            start = 'NOW-60DAYS'
        else:
            start = start.replace('-', '')
        if not end:
            end = 'NOW'
        else:
            end = end.replace('-', '')
        products = self._api.query(
            area=area,
            platformname='Sentinel-2',
            date=(start, end),
            **args
        )
        products_df = self._api.to_dataframe(products)
        if len(products_df) < 1:
            gs.message('No product found')
            return

        # sort and limit to first sorted product
        if sortby:
            self._products_df_sorted = products_df.sort_values(
                sortby,
                ascending=[asc] * len(sortby)
            )

        if limit:
            self._products_df_sorted = self._products_df_sorted.head(int(limit))

        gs.message('{} Sentinel product(s) found'.format(len(self._products_df_sorted)))

    def list(self):
        if self._products_df_sorted is None:
            return

        for idx in range(len(self._products_df_sorted)):
            print ('{0} {1} {2:2.0f}% {3}'.format(
                self._products_df_sorted['uuid'][idx],
                self._products_df_sorted['beginposition'][idx].strftime("%Y-%m-%dT%H:%M:%SZ"),
                self._products_df_sorted['cloudcoverpercentage'][idx],
                self._products_df_sorted['producttype'][idx],
            ))

    def download(self, output):
        if self._products_df_sorted is None:
            return

        if not os.path.exists(output):
            os.makedirs(output)
        gs.message('Downloading data into <{}>...'.format(output))
        for idx in range(len(self._products_df_sorted)):
            gs.message('{} -> {}.SAFE'.format(
                self._products_df_sorted['uuid'][idx],
                os.path.join(output, self._products_df_sorted['identifier'][idx])
            ))
            # download
            self._api.download(self._products_df_sorted['uuid'][idx], output)

            # unzip
            if os.path.exists(os.path.join(output, self._products_df_sorted['identifier'][idx])):
                continue
            filename = self._products_df_sorted['identifier'][idx] + '.zip'
            with zipfile.ZipFile(os.path.join(output, filename), 'r') as zip_ref:
                zip_ref.extractall(output)

    def save_footprints(self, map_name):
        if self._products_df_sorted is None:
            return

        try:
            from osgeo import ogr, osr
        except ImportError as e:
            gs.fatal("Option <footprints> requires GDAL library: {}".format(e))

        gs.message("Writing footprints into <{}>...".format(map_name))
        driver = ogr.GetDriverByName("GPKG")
        tmp_name = gs.tempfile() + '.gpkg'
        data_source = driver.CreateDataSource(tmp_name)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        layer = data_source.CreateLayer(str(map_name), srs, ogr.wkbPolygon)

        # attributes
        attrs = OrderedDict([
            ("uuid", ogr.OFTString),
            ("ingestiondate", ogr.OFTString),
            ("cloudcoverpercentage", ogr.OFTInteger),
            ("producttype", ogr.OFTString)
        ])
        for key in attrs.keys():
            field = ogr.FieldDefn(key, attrs[key])
            layer.CreateField(field)

        # features
        for idx in range(len(self._products_df_sorted)):
            wkt = self._products_df_sorted['footprint'][idx]
            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetGeometry(ogr.CreateGeometryFromWkt(wkt))
            for key in attrs.keys():
                if key == 'ingestiondate':
                    value = self._products_df_sorted[key][idx].strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    value = self._products_df_sorted[key][idx]
                feature.SetField(key, value)
            layer.CreateFeature(feature)
            feature = None

        data_source = None

        gs.run_command('v.import', input=tmp_name, output=map_name,
                       layer=map_name, quiet=True
        )

def main():
    map_box = get_aoi_box(options['map'])

    downloader = SentinelDownloader(options['user'], options['password'])

    downloader.filter(area=map_box,
                      clouds=options['clouds'],
                      producttype=options['producttype'],
                      limit=options['limit'],
                      start=options['start'],
                      end=options['end'],
                      sortby=options['sort'].split(','),
                      asc=options['order'] == 'asc'
    )

    if options['footprints']:
        downloader.save_footprints(options['footprints'])

    if flags['l']:
        downloader.list()
        return

    downloader.download(options['output'])

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
