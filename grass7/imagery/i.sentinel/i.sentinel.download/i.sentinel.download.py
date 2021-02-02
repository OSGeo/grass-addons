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
#% key: sleep
#% description: Sleep time in minutes before retrying to download data from ESA LTA
#% guisection: Filter
#%end
#%option
#% key: retry
#% description: Maximum number of retries before skipping to the next scene at ESA LTA
#% answer: 5
#% guisection: Filter
#%end
#%option
#% key: datasource
#% description: Data-Hub to download S-2 scenes from
#% options: ESA_COAH,USGS_EE
#% answer: ESA_COAH
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
import time
from collections import OrderedDict

import grass.script as gs
try:
    import pandas
except ImportError as e:
    gs.fatal(_("Module requires pandas library: {}").format(e))


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


def get_bbox_from_S2_UTMtile(tile):
    import requests
    import xml.etree.ElementTree as ET
    # download and parse S2-UTM tilegrid kml
    tile_kml_url = 'https://sentinel.esa.int/documents/247904/1955685/' \
                   'S2A_OPER_GIP_TILPAR_MPC__20151209T095117_' \
                   'V20150622T000000_21000101T000000_B00.kml/' \
                   'ec05e22c-a2bc-4a13-9e84-02d5257b09a8'
    r = requests.get(tile_kml_url, allow_redirects=True)
    root = ET.fromstring(r.content)
    r = None
    # get center coordinates from tile
    nsmap = {"kml": "http://www.opengis.net/kml/2.2"}
    search_string = ".//*[kml:name='{}']//kml:Point//kml:coordinates".format(
        tile)
    kml_search = root.findall(search_string, nsmap)
    coord_str = kml_search[0].text
    lon = float(coord_str.split(',')[0])
    lat = float(coord_str.split(',')[1])
    # create a mini bbox around the center
    bbox = (lon-0.001, lat-0.001, lon+0.001, lat+0.001)
    return bbox


class SentinelDownloader(object):
    def __init__(self, user, password, api_url='https://scihub.copernicus.eu/dhus'):

        self._apiname = api_url
        self._user = user
        self._password = password

        # init logger
        root = logging.getLogger()
        root.addHandler(logging.StreamHandler(
            sys.stderr
        ))
        if self._apiname == 'https://scihub.copernicus.eu/dhus':
            try:
                from sentinelsat import SentinelAPI
            except ImportError as e:
                gs.fatal(_("Module requires sentinelsat library: {}").format(e))
            # connect SciHub via API
            self._api = SentinelAPI(self._user, self._password,
                                    api_url=api_url
                                    )
        elif self._apiname == 'USGS_EE':
            try:
                import landsatxplore.api
            except ImportError as e:
                gs.fatal(_("Module requires landsatxplore library: {}").format(e))

            self._api = landsatxplore.api.API(self._user, self._password)

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
        id_kw = ('uuid', 'entityId')
        identifier_kw = ('identifier', 'displayId')
        cloud_kw = ('cloudcoverpercentage', 'cloudCover')
        time_kw = ('beginposition', 'acquisitionDate')
        kw_idx = 1 if self._apiname == 'USGS_EE' else 0
        for idx in range(len(self._products_df_sorted[id_kw[kw_idx]])):
            if cloud_kw[kw_idx] in self._products_df_sorted:
                ccp = '{0:2.0f}%'.format(
                    float(self._products_df_sorted[cloud_kw[kw_idx]][idx]))
            else:
                ccp = 'cloudcover_NA'

            print_str = '{0} {1}'.format(
                self._products_df_sorted[id_kw[kw_idx]][idx],
                self._products_df_sorted[identifier_kw[kw_idx]][idx])
            if kw_idx == 1:
                time_string = self._products_df_sorted[time_kw[kw_idx]][idx]
            else:
                time_string = self._products_df_sorted[
                    time_kw[kw_idx]][idx].strftime("%Y-%m-%dT%H:%M:%SZ")
            print_str += ' {0} {1}'.format(time_string, ccp)
            if kw_idx == 0:
                print_str += ' {0}'.format(
                    self._products_df_sorted['producttype'][idx])

            print(print_str)

    def download(self, output, sleep=False, maxretry=False):
        if self._products_df_sorted is None:
            return

        if not os.path.exists(output):
            os.makedirs(output)
        gs.message(_('Downloading data into <{}>...').format(output))

        if self._apiname == 'USGS_EE':
            from landsatxplore.earthexplorer import EarthExplorer
            from zipfile import ZipFile
            ee = EarthExplorer(self._user, self._password)
            for idx in range(len(self._products_df_sorted['entityId'])):
                scene = self._products_df_sorted['entityId'][idx]
                identifier = self._products_df_sorted['displayId'][idx]
                zip_file = os.path.join(output, '{}.zip'.format(identifier))
                gs.message('Downloading {}...'.format(identifier))
                ee.download(scene_id=scene, output_dir=output)
                # extract .zip to get "usual" .SAFE
                with ZipFile(zip_file, 'r') as zip:
                    safe_name = zip.namelist()[0].split('/')[0]
                    outpath = os.path.join(output, safe_name)
                    zip.extractall(path=output)
                gs.message(_('Downloaded to <{}>'.format(outpath)))
                try:
                    os.remove(zip_file)
                except Exception as e:
                    gs.warning(_('Unable to remove {0}:{1}'.format(
                        zip_file, e)))
                ee.logout()

        else:
            for idx in range(len(self._products_df_sorted['uuid'])):
                gs.message('{} -> {}.SAFE'.format(
                    self._products_df_sorted['uuid'][idx],
                    os.path.join(output, self._products_df_sorted['identifier'][idx])
                ))
                # download
                out = self._api.download(self._products_df_sorted['uuid'][idx],
                                         output)
                if sleep:
                    x = 1
                    online = out['Online']
                    while not online:
                        # sleep is in minutes so multiply by 60
                        time.sleep(int(sleep) * 60)
                        out = self._api.download(self._products_df_sorted['uuid'][idx],
                                                 output)
                        x += 1
                        if x > maxretry:
                            online = True

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

        # Sentinel-1 data does not have cloudcoverpercentage
        prod_types = [type for type in self._products_df_sorted["producttype"]]
        s1_types = ["SLC", "GRD"]
        if any(type in prod_types for type in s1_types):
            del attrs["cloudcoverpercentage"]

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

        self._products_df_sorted = {'uuid': []}
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

    def filter_USGS(self, area, area_relation, clouds=None, producttype=None,
                    limit=None, query={}, start=None, end=None, sortby=[],
                    asc=True, relativeorbitnumber=None):
        if area_relation != 'Intersects':
            gs.fatal(_(
                'USGS Earth Explorer only supports area_relation'
                ' "Intersects"'))
        if relativeorbitnumber:
            gs.fatal(_(
                'USGS Earth Explorer does not support "relativeorbitnumber"'
                ' option.'))
        if producttype and producttype != 'S2MSI1C':
            gs.fatal(_(
                'USGS Earth Explorer only supports producttype S2MSI1C'))
        if query:
            if not any(key in query for key in ['identifier', 'filename']):
                gs.fatal(_(
                    'USGS Earth Explorer only supports query options'
                    ' "filename" or "identifier".'))
            if "filename" in query:
                esa_id = query['filename'].replace('.SAFE','')
            else:
                esa_id = query['identifier']
            utm_tile = esa_id.split('_')[-2]
            acq_date = esa_id.split('_')[2].split('T')[0]
            acq_date_string = '{0}-{1}-{2}'.format(
                acq_date[:4], acq_date[4:6], acq_date[6:])
            acq_time = esa_id.split('_')[2].split('T')[1]
            start_date = end_date = acq_date_string
            # build the USGS style S2-identifier
            bbox = get_bbox_from_S2_UTMtile(utm_tile.replace('T',''))
        else:
            # get coordinate pairs from wkt string
            str_1 = 'POLYGON(('
            str_2 = '))'
            coords = area[area.find(str_1)+len(str_1):area.rfind(str_2)].split(',')
            # add one space to first pair for consistency
            coords[0] = ' ' + coords[0]
            lons = [float(pair.split(' ')[1]) for pair in coords]
            lats = [float(pair.split(' ')[2]) for pair in coords]
            bbox = (min(lons), min(lats), max(lons), max(lats))
            start_date = start
            end_date = end
        usgs_args = {
                     'dataset': 'SENTINEL_2A',
                     'bbox': bbox,
                     'start_date': start_date,
                     'end_date': end_date
        }
        if clouds:
            usgs_args['max_cloud_cover'] = clouds
        if limit:
            usgs_args['max_results'] = limit
        scenes = self._api.search(**usgs_args)
        if len(scenes) < 1:
            gs.message(_('No product found'))
            return
        scenes_df = pandas.DataFrame.from_dict(scenes)
        if query:
            # check if the UTM-Tile is correct, remove otherwise
            for idx, row in scenes_df.iterrows():
                usgs_id = row['displayId']
                if usgs_id.split('_')[1] != utm_tile:
                    scenes_df.drop([idx])
        self._api.logout()
        # sort and limit to first sorted product
        if sortby:
            # replace sortby keywords with USGS keywords
            for idx, keyword in enumerate(sortby):
                if keyword == 'cloudcoverpercentage':
                    sortby[idx] = 'cloudCover'
                    # turn cloudcover to float to make it sortable
                    scenes_df['cloudCover'] = pandas.to_numeric(
                        scenes_df['cloudCover'])
                elif keyword == 'ingestiondate':
                    sortby[idx] = 'acquisitionDate'
                # what does sorting by footprint mean
                elif keyword == 'footprint':
                    sortby[idx] = 'displayId'
            self._products_df_sorted = scenes_df.sort_values(
                sortby,
                ascending=[asc] * len(sortby), ignore_index=True
            )
        else:
            self._products_df_sorted = scenes_df

        gs.message(_('{} Sentinel product(s) found').format(len(self._products_df_sorted)))

def main():
    user = password = None
    if options['datasource'] == 'ESA_COAH':
        api_url = 'https://scihub.copernicus.eu/dhus'
    else:
        api_url = 'USGS_EE'

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
            filter_args = {
                'area': map_box,
                'area_relation': options['area_relation'],
                'clouds': options['clouds'],
                'producttype': options['producttype'],
                'limit': options['limit'],
                'query': query,
                'start': options['start'],
                'end': options['end'],
                'sortby': sortby,
                'asc': True if options['order'] == 'asc' else False,
                'relativeorbitnumber': options['relativeorbitnumber']
                }
            if options['datasource'] == 'ESA_COAH':
                downloader.filter(**filter_args)
            elif options['datasource'] == 'USGS_EE':
                downloader.filter_USGS(**filter_args)
    except Exception as e:
        gs.fatal(_('Unable to connect to {0}: {1}').format(
            options['datasource'], e))

    if options['footprints']:
        downloader.save_footprints(options['footprints'])

    if flags['l']:
        downloader.list()
        return

    downloader.download(options['output'], options['sleep'],
                        int(options['retry']))

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
