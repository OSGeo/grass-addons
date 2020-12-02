"""!
@package rdigit.wxdigit

@brief wxGUI raster digitizer (base class)

List of classes:

 - wxvdigit::IRDigit

(C) 2007-2011 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Mohammed Rashad <rashadkm gmail.com>
"""

import grass.script.core as grass
#from pygrass.modules import Module
from core.gconsole import GConsole
from core.gcmd        import GError, RunCommand, CommandThread
from core.debug       import Debug
from core.settings    import UserSettings

import sys
import os
import tempfile

try:
    from grass.lib.gis    import *
    from grass.lib.vector import *
    from grass.lib.raster import *
except ImportError:
    pass

class RasterObject:
  def __init__(self,cat,coords,ft):
    self.catId = cat
    self.coords = coords
    self.ftype = ft

class IRDigit:
    def __init__(self, mapwindow):
        """!Base class for vector digitizer (ctypes interface)
        
        @param mapwindow reference for map window (BufferedWindow)
        """
        self.mapWindow = mapwindow
        self.objects = list()
        self.toolbar = mapwindow.parent.toolbars['rdigit']
        self.polyfile = tempfile.NamedTemporaryFile(delete=False)
        
        Debug.msg(2, "IRDigit.__init__() %s ", self.polyfile.name)
 
        self.cat = 1
        self.saveMap = True
        self.outputName = None
        
    def __del__(self):
        Debug.msg(1, "IRDigit.__del__()")
        
        if self.saveMap == True:
            for obj in self.objects:
                if obj.ftype == GV_BOUNDARY:
                    self.polyfile.write("AREA\n");
                    for coor in obj.coords:
                        east, north = coor
                        locbuf = " %s %s\n" % (east,north)
                        self.polyfile.write(locbuf);

                elif obj.ftype == GV_LINE:    
                    self.polyfile.write("LINE\n");
                    for coor in obj.coords:
                        east, north = coor
                        locbuf = " %s %s\n" % (east,north)            
                        self.polyfile.write(locbuf);
                        
                catbuf = "=%d a\n" % (obj.catId)
                self.polyfile.write(catbuf);

            self.polyfile.close()
            region_settings = grass.parse_command('g.region', flags = 'p', delimiter = ':')
            RunCommand('r.in.poly', input=self.polyfile.name, 
                                    rows=region_settings['rows'], output=self.getOutputName(),overwrite=True)
            
            os.unlink(self.polyfile.name)

    def setOutputName(self, name):
      if name:
        self.outputName = name

    def getOutputName(self):
      return self.outputName

    def DeleteArea(self, cat):
      self.objectsCopy = self.objects
      self.objects = []
      for obj in self.objectsCopy:
        if obj.catId != cat:
          self.objects.append(obj)
    
    def AddFeature(self, ftype, points):
        """!Add new feature
        
        @param ftype feature type (point, line, centroid, boundary)
        @param points tuple of points ((x, y), (x, y), ...)
        
        @return tuple (number of added features, feature ids)
        """
        if ftype == 'point':
            vtype = GV_POINT
        elif ftype == 'line':
            vtype = GV_LINE
        elif ftype == 'boundary':
            vtype = GV_BOUNDARY
        elif ftype == 'area':
            vtype = GV_AREA
        elif ftype == 'circle':
            vtype = 'circle'         
        else:
            GError(parent = self.mapWindow,
                   message = _("Unknown feature type '%s'") % ftype)
            return (-1, None)
         
        
        if vtype & GV_LINES and len(points) < 2:
            GError(parent = self.mapWindow,
                   message = _("Not enough points for line"))
            return (-1, None)
            
        self.toolbar.EnableUndo()
        return self._addFeature(vtype, points)

    def _checkMap(self):
        """!Check if map is open
        """
        if not self.polyfile.name:
            self._NoMap()
            return False
            
        return True
        
    def NoMap(self, name = None):
        """!No map for editing"""
        if name:
            message = _('Unable to open vector map <%s>.') % name
        else:
            message = _('No vector map open for editing.3')
        GError(message + ' ' + _('Operation canceled.'),
               parent  = self.parent,
               caption = self.caption)        

    def _addFeature(self, ftype, coords):
        """!Add new feature(s) to the vector map

        @param ftype feature type (GV_POINT, GV_LINE, GV_BOUNDARY, ...)
        @coords tuple of coordinates ((x, y), (x, y), ...)
        @param threshold threshold for snapping
        """
        if not self._checkMap():
            return (-1, None)
        
        obj = RasterObject(self.cat, coords,ftype)
        self.objects.append(obj)
        self.cat = self.cat + 1 

        Debug.msg(2, "IRDigit._addFeature(): npoints=%d, ftype=%d, catId=%d",
                  len(coords), ftype,self.cat)        
           
        return self.cat - 1
    

