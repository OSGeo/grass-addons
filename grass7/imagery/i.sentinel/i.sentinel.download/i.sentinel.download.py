#!/usr/bin/env python
#
############################################################################
#
# MODULE:      i.sentinel.download
# AUTHOR(S):   Martin Landa
# PURPOSE:     Downloads Sentinel data from Copernicus Open Access Hub
#              using sentinelsat library.
# COPYRIGHT:   (C) 2018-2019 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Downloads Sentinel satellite data from Copernicus Open Access Hub using sentinelsat library.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: download
#%end
#%option G_OPT_F_INPUT
#% key: settings
#% label: Full path to settings file (user, password)
#% description: '-' for standard input
#%end
#%option G_OPT_M_DIR
#% key: output
#% description: Name for output directory where to store downloaded Sentinel data
#% required: no
#% guisection: Output
#%end
#%option G_OPT_V_OUTPUT
#% key: footprints
#% description: Name for output vector map with footprints
#% required: no
#% guisection: Output
#%end
#%option G_OPT_V_MAP
#% label: Name of input vector map to define Area of Interest (AOI)
#% description: If not given then current computational extent is used
#% required: no
#% guisection: Region
#%end
#%option
#% key: area_relation
#% type: string
#% description: Spatial reation of footprint to AOI
#% options: Intersects,Contains,IsWithin
#% answer: Intersects
#% required: no
#% guisection: Region
#%end
#%option
#% key: clouds
#% type: integer
#% description: Maximum cloud cover percentage for Sentinel scene
#% required: no
#% guisection: Filter
#%end
#%option
#% key: producttype
#% type: string
#% description: Sentinel product type to filter
#% required: no
#% options: SLC,GRD,OCN,S2MSI1C,S2MSI2A,S2MSI2Ap
#% answer: S2MSI2A
#% guisection: Filter
#%end
#%option
#% key: start
#% type: string
#% description: Start date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: end
#% type: string
#% description: End date ('YYYY-MM-DD')
#% guisection: Filter
#%end
#%option
#% key: limit
#% type: integer
#% description: Limit number of Sentinel products
#% guisection: Filter
#%end
#%option
#% key: query
#% type: string
#% description: Extra search keywords to use in the query
#% guisection: Filter
#%end
#%option
#% key: uuid
#% type: string
#% multiple: yes
#% description: List of UUID to download
#% guisection: Filter
#%end
#%option
#% key: relativeorbitnumber
#% type: integer
#% multiple: no
#% description: Relative orbit number to download (Sentinel-1: from 1 to 175; Sentinel-2: from 1 to 143)
#% guisection: Filter
#%end
#%option
#% key: sort
#% description: Sort by values in given order
#% multiple: yes
#% options: ingestiondate,cloudcoverpercentage,footprint
#% answer: cloudcoverpercentage,ingestiondate,footprint
#% guisection: Sort
#%end
#%option
#% key: order
#% description: Sort order (see sort parameter)
#% options: asc,desc
#% answer: asc
#% guisection: Sort
#%end
#%flag
#% key: l
#% description: List filtered products and exit
#% guisection: Print
#%end
#%flag
#% key: b
#% description: Use the borders of the AOI polygon and not the region of the AOI
#%end
#%rules
#% requires: -b,map
#% required: output,-l
#% excludes: uuid,map,area_relation,clouds,producttype,start,end,limit,query,sort,order
#%end

import os
import sys
import logging

from collections import OrderedDict

import grass.script as gs

def get_aoi_box(vector=None):
    args = {}
    if vector:
        args['vector'] = vector

    # are we in LatLong location?
    s = gs.read_command("g.proj", flags='j')
    kv = gs.parse_key_val(s)
    if '+proj' not in kv:
        gs.fatal('Unable to get AOI bounding box: unprojected location not supported')
    if kv['+proj'] != 'longlat':
        info = gs.parse_command('g.region', flags='uplg', **args)
        return 'POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat}, {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))'.format(
            nw_lat=info['nw_lat'], nw_lon=info['nw_long'], ne_lat=info['ne_lat'], ne_lon=info['ne_long'],
            sw_lat=info['sw_lat'], sw_lon=info['sw_long'], se_lat=info['se_lat'], se_lon=info['se_long']
            )
    else:
        info = gs.parse_command('g.region', flags='upg', **args)
        return 'POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat}, {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))'.format(
            nw_lat=info['n'], nw_lon=info['w'], ne_lat=info['n'], ne_lon=info['e'],
            sw_lat=info['s'], sw_lon=info['w'], se_lat=info['s'], se_lon=info['e']
            )


def get_aoi(vector=None):
    args = {}
    if vector:
        args['input'] = vector

    if gs.vector_info_topo(vector)['areas'] <= 0:
        gs.fatal(_("No areas found in AOI map <{}>...").format(vector))
    elif gs.vector_info_topo(vector)['areas'] > 1:
        gs.warning(_("More than one area found in AOI map <{}>. \
                      Using only the first area...").format(vector))

    # are we in LatLong location?
    s = gs.read_command("g.proj", flags='j')
    kv = gs.parse_key_val(s)
    if '+proj' not in kv:
        gs.fatal('Unable to get AOI: unprojected location not supported')
    geom_dict = gs.parse_command('v.out.ascii', format='wkt', **args)
    num_vertices = len(str(geom_dict.keys()).split(','))
    geom = [key for key in geom_dict][0]
    if kv['+proj'] != 'longlat':
        gs.message(_("Generating WKT from AOI map ({} vertices)...").format(num_vertices))
        if num_vertices > 500:
            gs.fatal(_("AOI map has too many vertices to be sent via HTTP GET (sentinelsat). \
                        Use 'v.generalize' to simplify the boundaries"))
        coords = geom.replace('POLYGON((', '').replace('))', '').split(', ')
        poly = 'POLYGON(('
        poly_coords = []
        for coord in coords:
            coord_latlon = gs.parse_command(
                'm.proj', coordinates=coord.replace(' ', ','), flags='od')
            for key in coord_latlon:
                poly_coords.append((' ').join(key.split('|')[0:2]))
        poly += (', ').join(poly_coords) + '))'
        # Note: poly must be < 2000 chars incl. sentinelsat request (see RFC 2616 HTTP/1.1)
        if len(poly) > 1850:
            gs.fatal(_("AOI map has too many vertices to be sent via HTTP GET (sentinelsat). \
                        Use 'v.generalize' to simplify the boundaries"))
        else:
            gs.message(_("Sending WKT from AOI map to ESA..."))
        return poly
    else:
        return geom


class SentinelDownloader(object):
    def __init__(self, user, password, api_url='https://scihub.copernicus.eu/dhus'):
        try:
            from sentinelsat import SentinelAPI
        except ImportError as e:
            gs.fatal(_("Module requires sentinelsat library: {}").format(e))
        try:
            import pandas
        except ImportError as e:
            gs.fatal(_("Module requires pandas library: {}").format(e))

        # init logger
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler(
            sys.stderr
        ))

        # connect SciHub via API
        self._api = SentinelAPI(user, password,
                                api_url=api_url
        )

        self._products_df_sorted = None

    def filter(self, area, area_relation,
               clouds=None, producttype=None, limit=None, query={},
               start=None, end=None, sortby=[], asc=True, relativeorbitnumber=None):
        args = {}
        if clouds:
            args['cloudcoverpercentage'] = (0, int(clouds))
        if relativeorbitnumber:
            args['relativeorbitnumber'] = relativeorbitnumber
            if producttype.startswith('S2') and int(relativeorbitnumber) > 143:
                gs.warning("This relative orbit number is out of range")
            elif int(relativeorbitnumber) > 175:
                gs.warning("This relative orbit number is out of range")
        if producttype:
            args['producttype'] = producttype
            if producttype.startswith('S2'):
                args['platformname'] = 'Sentinel-2'
            else:
                args['platformname'] = 'Sentinel-1'
        if not start:
            start = 'NOW-60DAYS'
        else:
            start = start.replace('-', '')
        if not end:
            end = 'NOW'
        else:
            end = end.replace('-', '')
        if query:
            redefined = [value for value in args.keys() if value in query.keys()]
            if redefined:
                gs.warning("Query overrides already defined options ({})".format(
                    ','.join(redefined)
                ))
            args.update(query)
        gs.verbose("Query: area={} area_relation={} date=({}, {}) args={}".format(
            area, area_relation, start, end, args
        ))
        products = self._api.query(
            area=area, area_relation=area_relation,
            date=(start, end),
            **args
        )
        products_df = self._api.to_dataframe(products)
        if len(products_df) < 1:
            gs.message(_('No product found'))
            return

        # sort and limit to first sorted product
        if sortby:
            self._products_df_sorted = products_df.sort_values(
                sortby,
                ascending=[asc] * len(sortby)
            )
        else:
            self._products_df_sorted = products_df

        if limit:
            self._products_df_sorted = self._products_df_sorted.head(int(limit))

        gs.message(_('{} Sentinel product(s) found').format(len(self._products_df_sorted)))

    def list(self):
        if self._products_df_sorted is None:
            return

        for idx in range(len(self._products_df_sorted['uuid'])):
            if 'cloudcoverpercentage' in self._products_df_sorted:
                ccp = '{0:2.0f}%'.format(self._products_df_sorted['cloudcoverpercentage'][idx])
            else:
                ccp = 'cloudcover_NA'

            print('{0} {1} {2} {3} {4}'.format(
                self._products_df_sorted['uuid'][idx],
                self._products_df_sorted['identifier'][idx],
                self._products_df_sorted['beginposition'][idx].strftime("%Y-%m-%dT%H:%M:%SZ"),
                ccp,
                self._products_df_sorted['producttype'][idx],
            ))

    def download(self, output):
        if self._products_df_sorted is None:
            return

        if not os.path.exists(output):
            os.makedirs(output)
        gs.message(_('Downloading data into <{}>...').format(output))
        for idx in range(len(self._products_df_sorted['uuid'])):
            gs.message('{} -> {}.SAFE'.format(
                self._products_df_sorted['uuid'][idx],
                os.path.join(output, self._products_df_sorted['identifier'][idx])
            ))
            # download
            self._api.download(self._products_df_sorted['uuid'][idx], output)

    def save_footprints(self, map_name):
        if self._products_df_sorted is None:
            return

        try:
            from osgeo import ogr, osr
        except ImportError as e:
            gs.fatal(_("Option <footprints> requires GDAL library: {}").format(e))

        gs.message(_("Writing footprints into <{}>...").format(map_name))
        driver = ogr.GetDriverByName("GPKG")
        tmp_name = gs.tempfile() + '.gpkg'
        data_source = driver.CreateDataSource(tmp_name)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)

        # features can be polygons or multi-polygons
        layer = data_source.CreateLayer(str(map_name), srs, ogr.wkbMultiPolygon)

        # attributes
        attrs = OrderedDict([
            ("uuid", ogr.OFTString),
            ("ingestiondate", ogr.OFTString),
            ("cloudcoverpercentage", ogr.OFTInteger),
            ("producttype", ogr.OFTString),
            ("identifier", ogr.OFTString)
        ])
        for key in attrs.keys():
            field = ogr.FieldDefn(key, attrs[key])
            layer.CreateField(field)

        # features
        for idx in range(len(self._products_df_sorted['uuid'])):
            wkt = self._products_df_sorted['footprint'][idx]
            feature = ogr.Feature(layer.GetLayerDefn())
            newgeom = ogr.CreateGeometryFromWkt(wkt)
            # convert polygons to multi-polygons
            newgeomtype = ogr.GT_Flatten(newgeom.GetGeometryType())
            if newgeomtype == ogr.wkbPolygon:
                multigeom = ogr.Geometry(ogr.wkbMultiPolygon)
                multigeom.AddGeometryDirectly(newgeom)
                feature.SetGeometry(multigeom)
            else:
                feature.SetGeometry(newgeom)
            for key in attrs.keys():
                if key == 'ingestiondate':
                    value = self._products_df_sorted[key][idx].strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    value = self._products_df_sorted[key][idx]
                feature.SetField(key, value)
            layer.CreateFeature(feature)
            feature = None

        data_source = None

        # coordinates of footprints are in WKT -> fp precision issues
        # -> snap
        gs.run_command('v.import', input=tmp_name, output=map_name,
                       layer=map_name, snap=1e-10, quiet=True
        )

    def set_uuid(self, uuid_list):
        """Set products by uuid.

        TODO: Find better implementation

        :param uuid: uuid to download
        """
        from sentinelsat.sentinel import SentinelAPIError

        self._products_df_sorted = { 'uuid': [] }
        for uuid in uuid_list:
            try:
                odata = self._api.get_product_odata(uuid, full=True)
            except SentinelAPIError as e:
                gs.error('{0}. UUID {1} skipped'.format(e, uuid))
                continue

            for k, v in odata.items():
                if k == 'id':
                    k = 'uuid'
                elif k == 'Sensing start':
                    k = 'beginposition'
                elif k == 'Product type':
                    k = 'producttype'
                elif k == 'Cloud cover percentage':
                    k = 'cloudcoverpercentage'
                elif k == 'Identifier':
                    k = 'identifier'
                elif k == 'Ingestion Date':
                    k = 'ingestiondate'
                elif k == 'footprint':
                    pass
                else:
                    continue
                if k not in self._products_df_sorted:
                    self._products_df_sorted[k] = []
                self._products_df_sorted[k].append(v)

def main():
    user = password = None
    api_url = 'https://scihub.copernicus.eu/dhus'

    if options['settings'] == '-':
        # stdin
        import getpass
        user = raw_input(_('Insert username: '))
        password = getpass.getpass(_('Insert password: '))
        url = raw_input(_('Insert API URL (leave empty for {}): ').format(api_url))
        if url:
            api_url = url
    else:
        try:
            with open(options['settings'], 'r') as fd:
                lines = list(filter(None, (line.rstrip() for line in fd))) # non-blank lines only
                if len(lines) < 2:
                    gs.fatal(_("Invalid settings file"))
                user = lines[0].strip()
                password = lines[1].strip()
                if len(lines) > 2:
                    api_url = lines[2].strip()
        except IOError as e:
            gs.fatal(_("Unable to open settings file: {}").format(e))

    if user is None or password is None:
        gs.fatal(_("No user or password given"))

    if flags['b']:
        map_box = get_aoi(options['map'])
    else:
        map_box = get_aoi_box(options['map'])

    sortby = options['sort'].split(',')
    if options['producttype'] in ('SLC', 'GRD', 'OCN'):
        if options['clouds']:
            gs.info("Option <{}> ignored: cloud cover percentage "
                    "is not defined for product type {}".format(
                        "clouds", options['producttype']
                    ))
            options['clouds'] = None
        try:
            sortby.remove('cloudcoverpercentage')
        except ValueError:
            pass
    try:
        downloader = SentinelDownloader(user, password, api_url)

        if options['uuid']:
            downloader.set_uuid(options['uuid'].split(','))
        else:
            query = {}
            if options['query']:
                for item in options['query'].split(','):
                    k, v = item.split('=')
                    query[k] = v
            downloader.filter(area=map_box,
                              area_relation=options['area_relation'],
                              clouds=options['clouds'],
                              producttype=options['producttype'],
                              limit=options['limit'],
                              query=query,
                              start=options['start'],
                              end=options['end'],
                              sortby=sortby,
                              asc=options['order'] == 'asc',
                              relativeorbitnumber=options['relativeorbitnumber']
            )
    except Exception as e:
        gs.fatal(_('Unable to connect Copernicus Open Access Hub: {}').format(e))

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
