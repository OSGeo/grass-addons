
import base64
import grass.script as grass 
from urllib2 import urlopen, HTTPError
from httplib import HTTPException

try:
    from osgeo import gdal
    from osgeo import gdalconst 
except:
    grass.fatal(_("Unable to load GDAL python bindings"))

import urllib2
import xml.etree.ElementTree as etree

import numpy as Numeric
Numeric.arrayrange = Numeric.arange

from math import pi, floor
from wms_base import WMSBase

class WMSDrv(WMSBase):
    def _download(self):
        """!Downloads data from WMS server using own driver
        
        @return temp_map with downloaded data
        """ 
        grass.message(_("Downloading data from WMS server..."))

        # initialize correct manager according to chosen OGC service
        if self.params['driver'] == 'WMTS_GRASS':
            req_mgr = WMTSRequestMgr(self.params, self.bbox, self.region, self.proj_srs, self._fetchCapabilities(self.params))
        elif self.params['driver'] == 'WMS_GRASS':
            req_mgr = WMSRequestMgr(self.params, self.bbox, self.region, self.tile_size, self.proj_srs)

        # get information about size in pixels and bounding box of raster, where all tiles will be joined
        map_region = req_mgr.GetMapRegion()

        init = True
        temp_map = None

        # iterate through all tiles and download them
        while True:

            # get url for request the tile and information for placing the tile into raster with other tiles
            tile = req_mgr.GetNextTile()

            # if last tile has been already downloaded 
            if not tile:
                break

            # url for request the tile
            query_url = tile[0]

            # the tile size and offset in pixels for placing it into raster where tiles are joined
            tileRef = tile[1]

            grass.debug(query_url)
            try: 
                request = urllib2.Request(query_url)
                if self.params['username']:
                    base64string = base64.encodestring('%s:%s' % (self.params['username'], self.params['password'])).replace('\n', '')
                    request.add_header("Authorization", "Basic %s" % base64string) 
                wms_data = urllib2.urlopen(request)
            except (IOError, HTTPException), e:
                if HTTPError == type(e) and e.code == 401:
                    grass.fatal(_("Authorization failed"))           
                else:
                    grass.fatal(_("Unable to fetch data from server")) 

            temp_tile = self._tempfile()
                
            # download data into temporary file
            try:
                temp_tile_opened = open(temp_tile, 'w')
                temp_tile_opened.write(wms_data.read())
            except IOError:
                grass.fatal(_("Unable to write data into tempfile"))
            finally:
                temp_tile_opened.close()
                
            tile_dataset_info = gdal.Open(temp_tile, gdal.GA_ReadOnly) 
            if tile_dataset_info is None:
                # print error xml returned from server
                try:
                    error_xml_opened = open(temp_tile, 'r')
                    err_str = error_xml_opened.read()     
                except IOError:
                    grass.fatal(_("Unable to read data from tempfile"))
                finally:
                    error_xml_opened.close()

                if  err_str is not None:
                    grass.fatal(_("WMS server error: %s") %  err_str)
                else:
                    grass.fatal(_("WMS server unknown error") )
                
            band = tile_dataset_info.GetRasterBand(1) 
            cell_type_func = band.__swig_getmethods__["DataType"]#??
            bands_number_func = tile_dataset_info.__swig_getmethods__["RasterCount"]
                
            temp_tile_pct2rgb = None
            if bands_number_func(tile_dataset_info) == 1 and band.GetRasterColorTable() is not None:
                # expansion of color table into bands 
                temp_tile_pct2rgb = self._tempfile()
                tile_dataset = self._pct2rgb(temp_tile, temp_tile_pct2rgb)
            else: 
                tile_dataset = tile_dataset_info
                
            # initialization of temp_map_dataset, where all tiles are merged
            if init:
                temp_map = self._tempfile()
                    
                driver = gdal.GetDriverByName(self.gdal_drv_format)
                metadata = driver.GetMetadata()
                if not metadata.has_key(gdal.DCAP_CREATE) or \
                       metadata[gdal.DCAP_CREATE] == 'NO':
                    grass.fatal(_('Driver %s does not supports Create() method') % drv_format)  
                    
                self.temp_map_bands_num = bands_number_func(tile_dataset)
                temp_map_dataset = driver.Create(temp_map, map_region['cols'], map_region['rows'],
                                                 self.temp_map_bands_num, cell_type_func(band))
                init = False
                
            # tile is written into temp_map
            tile_to_temp_map = tile_dataset.ReadRaster(0, 0, tileRef['sizeX'], tileRef['sizeY'],
                                                             tileRef['sizeX'], tileRef['sizeY'])
                
            temp_map_dataset.WriteRaster(tileRef['t_cols_offset'], tileRef['t_rows_offset'],
                                         tileRef['sizeX'],  tileRef['sizeY'], tile_to_temp_map) 
                
            tile_dataset = None
            tile_dataset_info = None
            grass.try_remove(temp_tile)
            grass.try_remove(temp_tile_pct2rgb)    
        
        if not temp_map:
            return temp_map
        # georeferencing and setting projection of temp_map
        projection = grass.read_command('g.proj', 
                                        flags = 'wf',
                                        epsg =self.params['srs']).rstrip('\n')
        temp_map_dataset.SetProjection(projection)

        pixel_x_length = (map_region['maxx'] - map_region['minx']) / int(map_region['cols'])
        pixel_y_length = (map_region['miny'] - map_region['maxy']) / int(map_region['rows'])

        geo_transform = [map_region['minx'] , pixel_x_length  , 0.0 , map_region['maxy'] , 0.0 , pixel_y_length] 
        temp_map_dataset.SetGeoTransform(geo_transform )
        temp_map_dataset = None
        
        return temp_map
    
    def _pct2rgb(self, src_filename, dst_filename):
        """!Create new dataset with data in dst_filename with bands according to src_filename 
        raster color table - modified code from gdal utility pct2rgb
        
        @return new dataset
        """  
        out_bands = 4
        band_number = 1
        
        # open source file
        src_ds = gdal.Open(src_filename)
        if src_ds is None:
            grass.fatal(_('Unable to open %s ' % src_filename))
            
        src_band = src_ds.GetRasterBand(band_number)
        
        # Build color table
        lookup = [ Numeric.arrayrange(256), 
                   Numeric.arrayrange(256), 
                   Numeric.arrayrange(256), 
                   Numeric.ones(256)*255 ]
        
        ct = src_band.GetRasterColorTable()	
        if ct is not None:
            for i in range(min(256,ct.GetCount())):
                entry = ct.GetColorEntry(i)
                for c in range(4):
                    lookup[c][i] = entry[c]
        
        # create the working file
        gtiff_driver = gdal.GetDriverByName(self.gdal_drv_format)
        tif_ds = gtiff_driver.Create(dst_filename,
                                     src_ds.RasterXSize, src_ds.RasterYSize, out_bands)
        
        # do the processing one scanline at a time
        for iY in range(src_ds.RasterYSize):
            src_data = src_band.ReadAsArray(0,iY,src_ds.RasterXSize,1)
            
            for iBand in range(out_bands):
                band_lookup = lookup[iBand]
                
                dst_data = Numeric.take(band_lookup,src_data)
                tif_ds.GetRasterBand(iBand+1).WriteArray(dst_data,0,iY)
        
        return tif_ds       

class BaseRequestMgr:
    """!Base class for request managers. 
    """
    def _isGeoProj(self, proj):
        """!Is it geographic projection? 
        """       
        if (proj.find("+proj=latlong")  != -1 or \
            proj.find("+proj=longlat")  != -1):

            return True
        return False

    def find(self, etreeElement, tag, ns = None):
        """!Wraper for etree element find method. 
        """
        if not ns:
            res = etreeElement.find(tag)
        else:
            res = etreeElement.find(ns(tag))

        if res is None:
            grass.fatal(_("Unable to parse capabilities file. \n Tag '%s' was not found.") % tag)

        return res

    def findall(self, etreeElement, tag, ns = None):
        """!Wraper for etree element findall method. 
        """
        if not ns:
            res = etreeElement.findall(tag)
        else:
            res = etreeElement.findall(ns(tag))

        if not res:
            grass.fatal(_("Unable to parse capabilities file. \n Tag '%s' was not found.") % tag)

        return res

class WMSRequestMgr(BaseRequestMgr):
    def __init__(self, params, bbox, region, tile_size, proj_srs, cap_file = None):
        """!Initialize data needed for iteration through tiles.
        """
        self.version = params['wms_version']
        proj = params['proj_name'] + "=EPSG:"+ str(params['srs'])
        self.url = params['url'] + ("?SERVICE=WMS&REQUEST=GetMap&VERSION=%s&LAYERS=%s&WIDTH=%s&HEIGHT=%s&STYLES=%s&BGCOLOR=%s&TRANSPARENT=%s" % \
                  (params['wms_version'], params['layers'], tile_size['cols'], tile_size['rows'], params['styles'], \
                   params['bgcolor'], params['transparent']))
        self.url += "&" +proj+ "&" + "FORMAT=" + params['format']
        
        self.bbox = bbox
        self.proj_srs = proj_srs
        self.tile_rows = tile_size['rows']
        self.tile_cols = tile_size['cols']

        if params['urlparams'] != "":
            self.url += "&" + params['urlparams']
        
        cols = int(region['cols'])
        rows = int(region['rows'])
        
        # computes parameters of tiles 
        self.num_tiles_x = cols / self.tile_cols 
        self.last_tile_x_size = cols % self.tile_cols
        self.tile_length_x =  float(self.tile_cols) / float(cols) * (self.bbox['maxx'] - self.bbox['minx']) 
        
        self.last_tile_x = False
        if self.last_tile_x_size != 0:
            self.last_tile_x = True
            self.num_tiles_x = self.num_tiles_x + 1
        
        self.num_tiles_y = rows / self.tile_rows 
        self.last_tile_y_size = rows % self.tile_rows
        self.tile_length_y =  float(self.tile_rows) / float(rows) * (self.bbox['maxy'] - self.bbox['miny']) 
        
        self.last_tile_y = False
        if self.last_tile_y_size != 0:
            self.last_tile_y = True
            self.num_tiles_y = self.num_tiles_y + 1
        
        self.tile_bbox = dict(self.bbox)
        self.tile_bbox['maxx'] = self.bbox['minx']  + self.tile_length_x

        self.i_x = 0 
        self.i_y = 0

        self.map_region = self.bbox
        self.map_region['cols'] = cols
        self.map_region['rows'] = rows

    def GetMapRegion(self):
        """!Get size in pixels and bounding box of raster where all tiles will be merged.
        """
        return self.map_region

    def GetNextTile(self):
        """!Get url for request the tile from server and information for merging the tile with other tiles
        """

        tileRef = {}

        if self.i_x >= self.num_tiles_x:
            return None
            
        tileRef['sizeX'] = self.tile_cols
        if self.i_x == self.num_tiles_x - 1 and self.last_tile_x:
            tileRef['sizeX'] = self.last_tile_x_size
         
        # set bbox for tile (N, S)
        if self.i_y != 0:
            self.tile_bbox['miny'] -= self.tile_length_y 
            self.tile_bbox['maxy'] -= self.tile_length_y
        else:
            self.tile_bbox['maxy'] = self.bbox['maxy']
            self.tile_bbox['miny'] = self.bbox['maxy'] - self.tile_length_y

        tileRef['sizeY'] = self.tile_rows
        if self.i_y == self.num_tiles_y - 1 and self.last_tile_y:
            tileRef['sizeY'] = self.last_tile_y_size 

        if self._isGeoProj(self.proj_srs) and self.version == "1.3.0":                
            query_bbox = self._flipBbox(self.tile_bbox, self.proj_srs)
        else:
            query_bbox = self.tile_bbox
        query_url = self.url + "&" + "BBOX=%s,%s,%s,%s" % ( query_bbox['minx'],  query_bbox['miny'],  query_bbox['maxx'],  query_bbox['maxy'])

        tileRef['t_cols_offset'] = int(self.tile_cols * self.i_x)
        tileRef['t_rows_offset'] = int(self.tile_rows * self.i_y)

        if self.i_y >= self.num_tiles_y - 1:
            self.i_y = 0
            self.i_x += 1
            # set bbox for next tile (E, W)      
            self.tile_bbox['maxx'] += self.tile_length_x 
            self.tile_bbox['minx'] += self.tile_length_x 
        else:
            self.i_y += 1

        return query_url, tileRef

    def _flipBbox(self, bbox, proj, version):
        """ 
        Flips coordinates if WMS standard is 1.3.0 and 
        projection is geographic.

        value flips between this keys:
        maxy -> maxx
        maxx -> maxy
        miny -> minx
        minx -> miny
        @return copy of bbox with flipped coordinates
        """  

        temp_bbox = dict(bbox)
        new_bbox = {}
        new_bbox['maxy'] = temp_bbox['maxx']
        new_bbox['miny'] = temp_bbox['minx']
        new_bbox['maxx'] = temp_bbox['maxy']
        new_bbox['minx'] = temp_bbox['miny']

        return new_bbox


class WMTSRequestMgr(BaseRequestMgr):
    def __init__(self, params, bbox, region, proj_srs, cap_file = None):
        """!Initializes data needed for iteration through tiles.
        """

        self.proj_srs = proj_srs
        self.meters_per_unit = None

        # constant defined in WMTS standard (in meters)
        self.pixel_size = 0.00028

        # parse capabilities file
        cap_tree = etree.parse(cap_file)
        root = cap_tree.getroot()

        # get layer tile matrix sets with same projection
        mat_sets = self._getMatSets(root, params)

        # TODO: what if more tile matrix sets are returned?
        params['tile_matrix_set'] = mat_sets[0].find(self._ns_ows('Identifier')).text

        # find tile matrix with resolution closest and smaller to wanted resolution 
        tile_mat  = self._findTileMats(mat_sets[0].findall(self._ns_wmts('TileMatrix')), region, bbox)

        # initialize data needed for iteration through tiles
        self._computeRequestData(tile_mat, params, bbox)

    def GetMapRegion(self):
        """!Get size in pixels and bounding box of raster where all tiles will be merged.
        """
        return self.map_region

    def _getMatSets(self, root, params):
        """!Get matrix sets which are available for chosen layer and have required EPSG.
        """
        contents = self.find(root, 'Contents', self._ns_wmts)
        layers = self.findall(contents, 'Layer', self._ns_wmts)

        ch_layer = None
        for layer in layers:
            layer_id = layer.find(self._ns_ows('Identifier')).text
            if layer_id and layer_id == params['layers']:
                ch_layer = layer 
                break  

        if ch_layer is None:
            grass.fatal(_("Layer '%s' was not found in capabilities file") % params['layers'])

        mat_set_links = self.findall(ch_layer, 'TileMatrixSetLink', self._ns_wmts)

        suitable_mat_sets = []
        tileMatrixSets = self.findall(contents, 'TileMatrixSet', self._ns_wmts)

        for link in  mat_set_links:
            mat_set_link_id = link.find(self._ns_wmts('TileMatrixSet')).text
            if not mat_set_link_id:
                continue
            for mat_set in tileMatrixSets:
                mat_set_id = mat_set.find(self._ns_ows('Identifier')).text 
                if mat_set_id and mat_set_id != mat_set_link_id:
                    continue
                mat_set_srs = mat_set.find(self._ns_ows('SupportedCRS')).text
                if mat_set_srs and mat_set_srs.lower() == ("EPSG:"+ str(params['srs'])).lower():
                    suitable_mat_sets.append(mat_set)

        if not suitable_mat_sets:
            grass.fatal(_("Layer '%s' is not available with %s code.") % (params['layers'],  "EPSG:" + str(params['srs'])))

        return suitable_mat_sets

    def _findTileMats(self, tile_mats, region, bbox):
        """!Find tile matrix set with closest and smaller resolution to requested resolution
        """        
        scale_dens = []

        scale_dens.append((bbox['maxy'] - bbox['miny']) / region['rows'] * self._getMetersPerUnit()  / self.pixel_size)
        scale_dens.append((bbox['maxx'] - bbox['minx']) / region['cols'] * self._getMetersPerUnit() / self.pixel_size)

        scale_den = min(scale_dens)

        first = True
        for t_mat in tile_mats:
            mat_scale_den = float(t_mat.find(self._ns_wmts('ScaleDenominator')).text)
            if first:
                best_scale_den = mat_scale_den
                best_t_mat = t_mat
                first = False
                continue
                
            best_diff = best_scale_den - scale_den
            mat_diff = mat_scale_den - scale_den
            if (best_diff < mat_diff  and  mat_diff < 0) or \
               (best_diff > mat_diff  and  best_diff > 0):
                best_t_mat = t_mat
                best_scale_den = mat_scale_den

        return best_t_mat

    def _getMetersPerUnit(self):
        """!Get coefficient which allows to convert units of request projection into meters 
        """  
        if self.meters_per_unit:
            return self.meters_per_unit

        # for geographic projection
        if self._isGeoProj(self.proj_srs):
            proj_params = proj_srs.split(' ')
            for param in proj_parmas:
                if '+a' in param:
                    a = float(param.split('=')[1])
                    break
            equator_perim = 2 * pi * a
            # meters per degree on equator
            self.meters_per_unit = equator_perim / 360 

        # other units
        elif '+to_meter' in self.proj_srs:
            proj_params = self.proj_srs.split(' ')
            for param in proj_params:
                if '+to_meter' in param:
                    self.meters_per_unit = 1/float(param.split('=')[1])
                    break
        # coordinate system in meters        
        else:
            self.meters_per_unit = 1

        return self.meters_per_unit

    def _computeRequestData(self, tile_mat, params, bbox):
        """!Initialize data needed for iteration through tiles.
        """  
        scale_den = float(tile_mat.find(self._ns_wmts('ScaleDenominator')).text)

        pixel_span = scale_den * self.pixel_size / self._getMetersPerUnit()

        tl_corner = tile_mat.find(self._ns_wmts('TopLeftCorner')).text.split(' ')

        self.t_cols = int(tile_mat.find(self._ns_wmts('TileWidth')).text)
        t_length_x = pixel_span * self.t_cols
        
        self.t_rows = int(tile_mat.find(self._ns_wmts('TileHeight')).text)
        t_length_y = pixel_span * self.t_rows
    
        t_mat_min_x = float(tl_corner[0])
        t_mat_max_y = float(tl_corner[1])
        
        epsilon = 2e-15

        self.t_num_bbox = {}
        self.t_num_bbox['min_col'] = int(floor((bbox['minx'] - t_mat_min_x) / t_length_x + epsilon))
        self.t_num_bbox['max_col'] = int(floor((bbox['maxx'] - t_mat_min_x) / t_length_x - epsilon))

        self.t_num_bbox['min_row'] = int(floor((t_mat_max_y - bbox['maxy']) / t_length_y + epsilon))
        self.t_num_bbox['max_row'] = int(floor((t_mat_max_y - bbox['miny']) / t_length_y - epsilon))

        matWidth = int(tile_mat.find(self._ns_wmts('MatrixWidth')).text)
        matHeight = int(tile_mat.find(self._ns_wmts('MatrixHeight')).text)

        self.intersects = False
        for col in ['min_col', 'max_col']:
            for row in ['min_row', 'max_row']:
                if (0 <= self.t_num_bbox[row] and self.t_num_bbox[row] <= matHeight) and \
                   (0 <= self.t_num_bbox[col] and self.t_num_bbox[col] <= matWidth):
                    self.intersects = True
                    
        if not self.intersects:
            grass.warning(_('Region is out of server data extend.'))
            self.map_region = None
            return

        if self.t_num_bbox['min_col'] < 0:
            self.t_num_bbox['min_col']  = 0

        if self.t_num_bbox['max_col'] > (matWidth - 1):
            self.t_num_bbox['max_col']  = matWidth - 1

        if self.t_num_bbox['min_row'] < 0:
            self.t_num_bbox['min_row']  = 0

        if self.t_num_bbox['max_row'] > (matHeight - 1):
            self.t_num_bbox['max_row'] = matHeight - 1

        num_tiles = (self.t_num_bbox['max_col'] - self.t_num_bbox['min_col'] + 1) * (self.t_num_bbox['max_row'] - self.t_num_bbox['min_row'] + 1) 
        grass.message(_('Fetching %d tiles with %d x %d pixel size per tile...') % (num_tiles, self.t_cols, self.t_rows))

        self.url = params['url'] + ("?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&" \
                                    "LAYER=%s&STYLE=%s&FORMAT=%s&TILEMATRIXSET=%s&TILEMATRIX=%s" % \
                                   (params['layers'], params['styles'], params['format'],
                                    params['tile_matrix_set'], tile_mat.find(self._ns_ows('Identifier')).text ))

        if params['urlparams'] != "":
            self.url += "&" + params['urlparams']

        self.map_region = {}
        self.map_region['minx'] = self.t_num_bbox['min_col'] * t_length_x + t_mat_min_x
        self.map_region['maxy'] = t_mat_max_y - (self.t_num_bbox['min_row']) * t_length_y

        self.map_region['maxx'] = (self.t_num_bbox['max_col'] + 1) * t_length_x + t_mat_min_x
        self.map_region['miny'] = t_mat_max_y - (self.t_num_bbox['max_row'] + 1) * t_length_y

        self.map_region['cols'] = self.t_cols * (self.t_num_bbox['max_col'] -  self.t_num_bbox['min_col'] + 1)
        self.map_region['rows'] = self.t_rows * (self.t_num_bbox['max_row'] -  self.t_num_bbox['min_row'] + 1)

        self.i_col = self.t_num_bbox['min_col']
        self.i_row = self.t_num_bbox['min_row'] 

        self.tileRef = {
                          'sizeX' : self.t_cols,
                          'sizeY' : self.t_rows
                        }

    def GetNextTile(self):
        """!Get url for request the tile from server and information for merging the tile with other tiles
        """
        if not self.intersects or self.i_col > self.t_num_bbox['max_col']:
            return None 
                
        query_url = self.url + "&TILECOL=%i&TILEROW=%i" % (int(self.i_col), int(self.i_row)) 

        self.tileRef['t_cols_offset'] = int(self.t_cols * (self.i_col - self.t_num_bbox['min_col']))
        self.tileRef['t_rows_offset'] = int(self.t_rows * (self.i_row - self.t_num_bbox['min_row']))

        if self.i_row >= self.t_num_bbox['max_row']:
            self.i_row =  self.t_num_bbox['min_row']
            self.i_col += 1
        else:
            self.i_row += 1 

        return query_url, self.tileRef

    def _ns_wmts(self, tag):
        """!Helper method - XML namespace
        """       
        return "{http://www.opengis.net/wmts/1.0}" + tag

    def _ns_ows(self, tag):
        """!Helper method - XML namespace
        """
        return "{http://www.opengis.net/ows/1.1}" + tag
