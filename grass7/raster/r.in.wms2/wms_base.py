import os
from   math import ceil

from urllib2 import urlopen, HTTPError, URLError
from httplib import HTTPException

import grass.script as grass

class WMSBase:
    def __init__(self):
        # these variables are information for destructor
        self.temp_files_to_cleanup = []
        self.cleanup_mask   = False
        self.cleanup_layers = False
        
        self.params = {}
        self.tile_size = {'bbox' : None}

        self.temp_map = None
        
    def __del__(self):
        # removes temporary mask, used for import transparent or warped temp_map
        if self.cleanup_mask:
            # clear temporary mask, which was set by module      
            if grass.run_command('r.mask',
                                 quiet = True,
                                 flags = 'r') != 0:  
                grass.fatal(_('%s failed') % 'r.mask')
            
            # restore original mask, if exists 
            if grass.find_file(self.params['output'] + self.original_mask_suffix, element = 'cell', mapset = '.' )['name']:
                if grass.run_command('g.copy',
                                     quiet = True,
                                     rast =  self.params['output'] + self.original_mask_suffix + ',MASK') != 0:
                    grass.fatal(_('%s failed') % 'g.copy')
        
        # tries to remove temporary files, all files should be
        # removed before, implemented just in case of unexpected
        # stop of module
        for temp_file in self.temp_files_to_cleanup:
            grass.try_remove(temp_file)
        
        # remove temporary created rasters
        if self.cleanup_layers: 
            maps = []
            for suffix in ('.red', '.green', '.blue', '.alpha', self.original_mask_suffix):
                rast = self.params['output'] + suffix
                if grass.find_file(rast, element = 'cell', mapset = '.')['file']:
                    maps.append(rast)
            
            if maps:
                grass.run_command('g.remove',
                                  quiet = True,
                                  flags = 'f',
                                  rast  = ','.join(maps))
        
        # deletes environmental variable which overrides region 
        if 'GRASS_REGION' in os.environ.keys():
            os.environ.pop('GRASS_REGION')
        
    def _debug(self, fn, msg):
        grass.debug("%s.%s: %s" %
                    (self.__class__.__name__, fn, msg))
        
    def _initializeParameters(self, options, flags):
        self._debug("_initialize_parameters", "started")
        
        # initialization of module parameters (options, flags)

        self.params['driver'] = options['driver']

        self.flags = flags

        if self.flags['o'] and 'WMS' not in self.params['driver']:
            grass.warning(_("Flag '%s' is relevant only for WMS.") % 'o')
        elif self.flags['o']:
            self.params['transparent'] = 'FALSE'
        else:
            self.params['transparent'] = 'TRUE'   

        for key in ['url', 'layers', 'styles', 'output', 'method']:
            self.params[key] = options[key].strip()

        if self.params['styles'] != "" and 'OnEarth_GRASS' in self.params['driver']:
            grass.warning(_("Parameter '%s' is not relevant for %s driver.") % ('styles', 'OnEarth_GRASS'))

        for key in ['password', 'username', 'urlparams']:
            self.params[key] = options[key] 
            if self.params[key] != "" and 'GRASS' not in self.params['driver']:
                grass.warning(_("Parameter '%s' is relevant only for %s drivers.") % (key, '*_GRASS'))
        
        if (self.params ['password'] and self.params ['username'] == '') or \
           (self.params ['password'] == '' and self.params ['username']):
                grass.fatal(_("Please insert both %s and %s parameters or none of them." % ('password', 'username')))

        self.params['bgcolor'] = options['bgcolor'].strip()
        if self.params['bgcolor'] != "" and 'WMS_GRASS' not in self.params['driver']:
            grass.warning(_("Parameter '%s' is relevant only for %s driver.") % ('bgcolor', 'WMS_GRASS'))
                
        self.params['wms_version'] = options['wms_version']  
        if self.params['wms_version'] == "1.3.0":
            self.params['proj_name'] = "CRS"
        else:
            self.params['proj_name'] = "SRS"
    
        if  options['format'] == "geotiff":
            self.params['format'] = "image/geotiff"
        elif options['format'] == "tiff":
            self.params['format'] = "image/tiff"
        elif options['format'] == "png":
            self.params['format'] = "image/png"
        elif  options['format'] == "jpeg":
            self.params['format'] = "image/jpeg"
            if not flags['o'] and \
              'WMS' in self.params['driver']:
                grass.warning(_("JPEG format does not support transparency"))
        elif self.params['format'] == "gif":
            self.params['format'] = "image/gif"
        else:
            self.params['format'] = self.params['format']
        
        #TODO: get srs from Tile Service file in OnEarth_GRASS driver 
        self.params['srs'] = int(options['srs'])
        if self.params['srs'] <= 0:
            grass.fatal(_("Invalid EPSG code %d") % self.params['srs'])
        
        # read projection info
        self.proj_location = grass.read_command('g.proj', 
                                                flags ='jf').rstrip('\n')

        if self.params['srs'] in [3857, 900913]:
            # HACK: epsg 3857 def: http://spatialreference.org/ref/sr-org/7483/
            # g.proj can return: ...+a=6378137 +rf=298.257223563... (WGS84 elipsoid def instead of sphere), it can make 20km shift in Y, when raster is transformed
            # needed to be tested on more servers
            self.proj_srs = '+proj=merc +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +no_defs +a=6378137 +b=6378137 +nadgrids=@null +to_meter=1 +wktext'
        else:
            self.proj_srs = grass.read_command('g.proj', 
                                               flags = 'jf', 
                                               epsg = str(self.params['srs']) ).rstrip('\n')

        if not self.proj_srs or not self.proj_location:
            grass.fatal(_("Unable to get projection info"))
        
        # set region 
        self.params['region'] = options['region']
        if self.params['region']:                 
            if not grass.find_file(name = self.params['region'], element = 'windows', mapset = '.' )['name']:
                grass.fatal(_("Region <%s> not found") % self.params['region'])
        
        if self.params['region']:
            s = grass.read_command('g.region',
                                   quiet = True,
                                   flags = 'ug',
                                   region = self.params['region'])
            self.region = grass.parse_key_val(s, val_type = float)
        else:
            self.region = grass.region()
        
        min_tile_size = 100
        maxcols = int(options['maxcols'])
        if maxcols <= min_tile_size:
            grass.fatal(_("Maxcols must be greater than 100"))
        
        maxrows = int(options['maxrows'])
        if maxrows <= min_tile_size:
            grass.fatal(_("Maxrows must be greater than 100"))
        
        # setting optimal tile size according to maxcols and maxrows constraint and region cols and rows      
        self.tile_size['cols'] = int(self.region['cols'] / ceil(self.region['cols'] / float(maxcols)))
        self.tile_size['rows'] = int(self.region['rows'] / ceil(self.region['rows'] / float(maxrows)))
        
        # suffix for existing mask (during overriding will be saved
        # into raster named:self.params['output'] + this suffix)
        self.original_mask_suffix = "_temp_MASK"
        
        # check names of temporary rasters, which module may create 
        maps = []
        for suffix in ('.red', '.green', '.blue', '.alpha', self.original_mask_suffix ):
            rast = self.params['output'] + suffix
            if grass.find_file(rast, element = 'cell', mapset = '.')['file']:
                maps.append(rast)
        
        if len(maps) != 0:
            grass.fatal(_("Please change output name, or change names of these rasters: %s, "
                          "module needs to create this temporary maps during runing") % ",".join(maps))
        
        # default format for GDAL library
        self.gdal_drv_format = "GTiff"
        
        self._debug("_initialize_parameters", "finished")

    def GetMap(self, options, flags):
        """!Download data from WMS server and import data
        (using GDAL library) into GRASS as a raster map."""

        self._initializeParameters(options, flags)  

        self.bbox     = self._computeBbox()
        
        self.temp_map = self._download()

        if not self.temp_map:
            return

        self._createOutputMap() 
    
    def _fetchCapabilities(self, options): 
        """!Download capabilities from WMS server
        """
        # download capabilities file
        cap_url = options['url']

        if 'WMTS' in options['driver']:
            cap_url += "?SERVICE=WMTS&REQUEST=GetCapabilities&VERSION=1.0.0"
        elif 'OnEarth' in options['driver']:
            cap_url += "?REQUEST=GetTileService"
        else:
            cap_url += "?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=" + options['wms_version'] 

        try:
            cap = urlopen(cap_url)
        except (IOError, HTTPError, HTTPException):
            grass.fatal(_("Unable to get capabilities from '%s'") % options['url'])
        
        return cap

    def GetCapabilities(self, options): 
        """!Get capabilities from WMS server
        """
        cap  = self._fetchCapabilities(options)
        cap_lines = cap.readlines()
        for line in cap_lines: 
            print line 
        
    def _computeBbox(self):
        """!Get region extent for WMS query (bbox)
        """
        self._debug("_computeBbox", "started")
        
        bbox_region_items = {'maxy' : 'n', 'miny' : 's', 'maxx' : 'e', 'minx' : 'w'}  
        bbox = {}

        if self.proj_srs == self.proj_location: # TODO: do it better
            for bbox_item, region_item in bbox_region_items.iteritems():
                bbox[bbox_item] = self.region[region_item]
        
        # if location projection and wms query projection are
        # different, corner points of region are transformed into wms
        # projection and then bbox is created from extreme coordinates
        # of the transformed points
        else:
            for bbox_item, region_item  in bbox_region_items.iteritems():
                bbox[bbox_item] = None

            temp_region = self._tempfile()
            
            try:
                temp_region_opened = open(temp_region, 'w')
                temp_region_opened.write("%f %f\n%f %f\n%f %f\n%f %f\n"  %\
                                       (self.region['e'], self.region['n'],\
                                        self.region['w'], self.region['n'],\
                                        self.region['w'], self.region['s'],\
                                        self.region['e'], self.region['s'] ))
            except IOError:
                 grass.fatal(_("Unable to write data into tempfile"))
            finally:           
                temp_region_opened.close()            

            points = grass.read_command('m.proj', flags = 'd',
                                        proj_output = self.proj_srs,
                                        proj_input = self.proj_location,
                                        input = temp_region) # TODO: stdin
            grass.try_remove(temp_region)
            if not points:
                grass.fatal(_("Unable to determine region, %s failed") % 'm.proj')
            
            points = points.splitlines()
            if len(points) != 4:
                grass.fatal(_("Region definition: 4 points required"))
            
            for point in points:
                try:
                    point = map(float, point.split("|"))
                except ValueError:
                    grass.fatal(_('Reprojection of region using m.proj failed.'))
                if not bbox['maxy']:
                    bbox['maxy'] = point[1]
                    bbox['miny'] = point[1]
                    bbox['maxx'] = point[0]
                    bbox['minx'] = point[0]
                    continue
                
                if   bbox['maxy'] < point[1]:
                    bbox['maxy'] = point[1]
                elif bbox['miny'] > point[1]:
                    bbox['miny'] = point[1]
                
                if   bbox['maxx'] < point[0]:
                    bbox['maxx'] = point[0]
                elif bbox['minx'] > point[0]:
                    bbox['minx'] = point[0]  
        
        self._debug("_computeBbox", "finished -> %s" % bbox)

        # Ordering of coordinates axis of geographic coordinate
        # systems in WMS 1.3.0 is flipped. If  self.tile_size['flip_coords'] is 
        # True, coords in bbox need to be flipped in WMS query.

        return bbox

    def _createOutputMap(self): 
        """!Import downloaded data into GRASS, reproject data if needed
        using gdalwarp
        """
        # reprojection of raster
        if self.proj_srs != self.proj_location: # TODO: do it better
            grass.message(_("Reprojecting raster..."))
            temp_warpmap = self._tempfile()
            
            if int(os.getenv('GRASS_VERBOSE', '2')) <= 2:
                nuldev = file(os.devnull, 'w+')
            else:
                nuldev = None
            
            #"+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs"
            # RGB rasters - alpha layer is added for cropping edges of projected raster
            if self.temp_map_bands_num == 3:
                ps = grass.Popen(['gdalwarp',
                                  '-s_srs', '%s' % self.proj_srs,
                                  '-t_srs', '%s' % self.proj_location,
                                  '-r', self.params['method'], '-dstalpha',
                                  self.temp_map, temp_warpmap], stdout = nuldev)
            # RGBA rasters
            else:
                ps = grass.Popen(['gdalwarp',
                                  '-s_srs', '%s' % self.proj_srs,
                                  '-t_srs', '%s' % self.proj_location,
                                  '-r', self.params['method'],
                                  self.temp_map, temp_warpmap], stdout = nuldev)
            ps.wait()
            
            if nuldev:
                nuldev.close()
            
            if ps.returncode != 0:
                grass.fatal(_('%s failed') % 'gdalwarp')
        # raster projection is same as projection of location
        else:
            temp_warpmap = self.temp_map
        
        grass.message(_("Importing raster map into GRASS..."))
        # importing temp_map into GRASS
        if grass.run_command('r.in.gdal',
                             quiet = True,
                             input = temp_warpmap,
                             output = self.params['output']) != 0:
            grass.fatal(_('%s failed') % 'r.in.gdal')
        
        # information for destructor to cleanup temp_layers, created
        # with r.in.gdal
        self.cleanup_layers = True
        
        # setting region for full extend of imported raster
        if grass.find_file(self.params['output'] + '.red', element = 'cell', mapset = '.')['file']:
            region_map = self.params['output'] + '.red'
        else:
            region_map = self.params['output']
        os.environ['GRASS_REGION'] = grass.region_env(rast = region_map)
          
        # mask created from alpha layer, which describes real extend
        # of warped layer (may not be a rectangle), also mask contains
        # transparent parts of raster
        if grass.find_file( self.params['output'] + '.alpha', element = 'cell', mapset = '.' )['name']:
            # saving current mask (if exists) into temp raster
            if grass.find_file('MASK', element = 'cell', mapset = '.' )['name']:
                if grass.run_command('g.copy',
                                     quiet = True,
                                     rast = 'MASK,' + self.params['output'] + self.original_mask_suffix) != 0:    
                    grass.fatal(_('%s failed') % 'g.copy')
            
            # info for destructor
            self.cleanup_mask = True
            if grass.run_command('r.mask',
                                 quiet = True,
                                 overwrite = True,
                                 maskcats = "0",
                                 flags = 'i',
                                 input = self.params['output'] + '.alpha') != 0: 
                grass.fatal(_('%s failed') % 'r.mask')
        
        #TODO one band + alpha band?
        if grass.find_file(self.params['output'] + '.red', element = 'cell', mapset = '.')['file']:
            if grass.run_command('r.composite',
                                 quiet = True,
                                 red = self.params['output'] + '.red',
                                 green = self.params['output'] +  '.green',
                                 blue = self.params['output'] + '.blue',
                                 output = self.params['output'] ) != 0:
                grass.fatal(_('%s failed') % 'r.composite')
        
        grass.try_remove(temp_warpmap)
        grass.try_remove(self.temp_map) 

    def _tempfile(self):
        """!Create temp_file and append list self.temp_files_to_cleanup 
            with path of file 
     
        @return string path to temp_file
        """
        temp_file = grass.tempfile()
        if temp_file is None:
            grass.fatal(_("Unable to create temporary files"))
        
        # list of created tempfiles for destructor
        self.temp_files_to_cleanup.append(temp_file)
        
        return temp_file
