import os
from   math import ceil

from urllib2 import urlopen, HTTPError, URLError

import grass.script as grass
from grass.exceptions import CalledModuleError


class WFSBase:
    def __init__(self):
        # these variables are information for destructor
        self.temp_to_cleanup = []
        
        self.bbox     = None
        self.temp_map = None
        
    def __del__(self):
        
        # tries to remove temporary files/dirs, all temps should be
        # removoved before, implemented just in case of unexpected
        # stop of module
        for temp in self.temp_to_cleanup:
            if os.path.isdir(temp):
                grass.try_rmdir(temp)
            else:
                grass.try_remove(temp)
                
        # deletes enviromental variable which overrides region 
        if 'GRASS_REGION' in os.environ.keys():
            os.environ.pop('GRASS_REGION')
        
    def _debug(self, fn, msg):
        grass.debug("%s.%s: %s" %
                    (self.__class__.__name__, fn, msg))
        
    def _initializeParameters(self, options, flags):
        self._debug("_initialize_parameters", "started")
        
        # initialization of module parameters (options, flags)        
        self.o_url = options['url'].strip() + "?" 
        self.o_layers = options['layers'].strip()
        self.o_output = options['output']
        
        self.o_wds_version = options['wfs_version']        
        self.projection_name = "SRSNAME" 
 
        self.o_wfs_version = options['wfs_version']
       
        self.o_urlparams = options['urlparams'].strip()
        
        self.o_srs = int(options['srs'])
        if self.o_srs <= 0:
            grass.fatal(_("Invalid EPSG code %d") % self.o_srs)
        
        try:
            self.o_maximum_features = int(options['maximum_features'])
            if int(options['maximum_features']) < 1:
                grass.fatal(_('Invalid maximum number of features (must be >1)'))
        except ValueError:
            self.o_maximum_features = None

        # read projection info
        self.proj_location = grass.read_command('g.proj', 
                                                flags ='jf').rstrip('\n')

        self.proj_srs = grass.read_command('g.proj', 
                                           flags = 'jf', 
                                           epsg = str(self.o_srs) ).rstrip('\n')
        
        if not self.proj_srs or not self.proj_location:
            grass.fatal(_("Unable to get projection info"))
        
        # set region 
        self.o_region = options['region']
        if self.o_region:                 
            if not grass.find_file(name = self.o_region, element = 'windows', mapset = '.' )['name']:
                grass.fatal(_("Region <%s> not found") % self.o_region)
        
        if self.o_region:
            s = grass.read_command('g.region',
                                   quiet = True,
                                   flags = 'ug',
                                   region = self.o_region)
            self.region = grass.parse_key_val(s, val_type = float)
        else:
            self.region = grass.region()

        self.ogr_drv_format = "ESRI Shapefile"             
        self._debug("_initialize_parameters", "finished")

    def GetFeature(self, options, flags):
        """!Download data from WFS server and import data
            into GRASS as a vector map."""

        self._initializeParameters(options, flags)  

        if flags['r']:
            self.bbox = self._computeBbox()
        else:
            self.bbox = None

        self.temp_map = self._download()  

        self._createOutputMap() 
    
    def GetCapabilities(self, options): 
        """!Get capabilities from WFS server
        """
        # download capabilities file
        cap_url = options['url'] + "?service=WFS&request=GetCapabilities&version=" + options['wfs_version'] 
        try:
            cap = urlopen(cap_url)
        except IOError:
            grass.fatal(_("Unable to get capabilities from '%s'") % options['url'])
        
        cap_lines = cap.readlines()
        for line in cap_lines: 
            print(line)

    def _computeBbox(self):
        """!Get region extent for WFS query (bbox)
        """
        self._debug("_computeBbox", "started")
        
        bbox_region_items = {'maxy': 'n', 'miny': 's', 'maxx': 'e', 'minx': 'w'}  
        bbox = {}

        if self.proj_srs == self.proj_location: # TODO: do it better
            for bbox_item, region_item in bbox_region_items.iteritems():
                bbox[bbox_item] = self.region[region_item]
        
        # if location projection and wfs query projection are
        # different, corner points of region are transformed into wfs
        # projection and then bbox is created from extreme coordinates
        # of the transformed points
        else:
            for bbox_item, region_item  in bbox_region_items.iteritems():
                bbox[bbox_item] = None

            temp_region = self._temp()
            
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
                                        proj_out = self.proj_srs,
                                        proj_in = self.proj_location,
                                        input = temp_region) # TODO: stdin
            grass.try_remove(temp_region)
            if not points:
                grass.fatal(_("Unable to determine region, %s failed") % 'm.proj')
            
            points = points.splitlines()
            if len(points) != 4:
                grass.fatal(_("Region defintion: 4 points required"))
            
            for point in points:
                point = map(float, point.split("|"))
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
        # systems is fliped If self.flip_coords is 
        # True, coords in bbox need to be flipped in WFS query.

        self.flip_coords = False  
        hasLongLat = self.proj_srs.find("+proj=longlat")   
        hasLatLong = self.proj_srs.find("+proj=latlong")   

        if (hasLongLat != -1 or hasLatLong != -1):
            self.flip_coords = True

        return bbox

    def _createOutputMap(self): 
        """!Import downloaded data into GRASS, reproject data if needed
        using ogr2ogr
        """
        # reprojection of downloaded data
        if self.proj_srs != self.proj_location: # TODO: do it better
            grass.message(_("Reprojecting data..."))
            temp_warpmap = self._temp()
            
            if int(os.getenv('GRASS_VERBOSE', '2')) <= 2:
                nuldev = file(os.devnull, 'w+')
            else:
                nuldev = None
            
            temp_warpmap = self._temp(directory = True)

            ps = grass.Popen(['ogr2ogr',
                              '-overwrite',
                              '-s_srs', '%s' % self.proj_srs,
                              '-t_srs', '%s' % self.proj_location,
                              '-f',     '%s' % self.ogr_drv_format, 
                              temp_warpmap, self.temp_map], stdout = nuldev)
            ps.wait()
            
            if nuldev:
                nuldev.close()
            
            if ps.returncode != 0:
                grass.fatal(_('%s failed') % 'ogr2ogr')
        # downloaded data projection is same as projection of location
        else:
            temp_warpmap = self.temp_map
        
        grass.message(_("Importing vector map into GRASS..."))
        # importing temp_map into GRASS
        try:
            grass.run_command('v.in.ogr',
                              quiet = True,
                              overwrite = True,
                              input = temp_warpmap,
                              output = self.o_output)
        except CalledModuleError:
            grass.fatal(_('%s failed') % 'v.in.ogr')
        
        grass.try_rmdir(temp_warpmap)
        grass.try_remove(self.temp_map) 

    def _flipBbox(self, bbox):
        """ 
        flips items in dictionary 
        value flips between this keys:
        maxy -> maxx
        maxx -> maxy
        miny -> minx
        minx -> miny
        @return copy of bbox with fliped cordinates
        """  
        temp_bbox = dict(bbox)
        new_bbox = {}
        new_bbox['maxy'] = temp_bbox['maxx']
        new_bbox['miny'] = temp_bbox['minx']
        new_bbox['maxx'] = temp_bbox['maxy']
        new_bbox['minx'] = temp_bbox['miny']

        return new_bbox

    def _temp(self, directory = False):
        """!Create temp file/dir and append list self.temp_to_cleanup 
            with the file/dir path 
     
        @param directory if False create file, if True create directory

        @return string path to temp
        """
        if directory:
            temp = grass.tempdir()
        else:
            temp = grass.tempfile()

        if temp is None:
            grass.fatal(_("Unable to create temporary files"))
        
        # list of created temps for destructor
        self.temp_to_cleanup.append(temp)
        
        return temp
