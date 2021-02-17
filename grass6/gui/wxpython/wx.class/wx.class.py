"""!
@package wx.class.py

@brief Interface implementation of i.class module without Xterm.
Many thanks to Markus Neteler for his help which allowed me to
know about i.class and its usage.
Classes:
- IClass
- BufferedWindow2
- IClassApp


(C) 2006-2010 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad K.M <rashadkm [at] gmail [dot] com>
"""

import os
import sys
import glob
import math
import tempfile
import copy
import time

gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','gui','wxpython','gui_modules')

sys.path.append(pypath)

pypath = os.path.join(gbase,'etc','python')
sys.path.append(pypath)

import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import wx
import wx.aui



try:
    import subprocess
except:
    CompatPath = os.path.join(globalvar.ETCWXDIR)
    sys.path.append(CompatPath)
    from compat import subprocess

gmpath = os.path.join(globalvar.ETCWXDIR, "icons")
sys.path.append(gmpath)

grassPath = os.path.join(globalvar.ETCDIR, "python")
sys.path.append(grassPath)

import render
import toolbars
from preferences import globalSettings as UserSettings
from icon  import Icons

from mapdisp_window import BufferedWindow
from mapdisp_window import MapWindow


from mapdisp import MapFrame
from debug import Debug

import gcmd
from grass.script import core as grass1

from grass.lib import gis as grasslib

from grass.lib import raster as raster


import toolbars






#from Numeric import *
from ctypes import *
import platform
grass = CDLL("libgrass_gis.7.0.svn.dll")
s = subprocess.Popen(['g.version.exe','-r'], stdout=subprocess.PIPE).communicate()[0]
for line in s.splitlines():
    if line.startswith('libgis Revision:'):
        version = '$' + line + '$'
grass.G__gisinit(version, '')


class IClass(MapFrame):

    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Imagery - wx.class"),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, toolbars=["map"],
                 tree=None, notebook=None, gismgr=None, page=None,
                 Map=None, auimgr=None):


        self._layerManager = gismgr
        self.Map        = Map   
        self.gismanager = gismgr    # GIS Manager object
        self.Map        = Map       # instance of render.Map
        self.tree       = tree      # GIS Manager layer tree object
        self.page       = page      # Notebook page holding the layer tree
        self.layerbook  = notebook  # GIS Manager layer tree notebook
        self.parent     = parent
        #
        # available cursors
        #

        self.counter = 0
        # available cursors
        #
        self.cursors = {
            # default: cross
            # "default" : wx.StockCursor(wx.CURSOR_DEFAULT),
            "default" : wx.StockCursor(wx.CURSOR_ARROW),
            "cross"   : wx.StockCursor(wx.CURSOR_CROSS),
            "hand"    : wx.StockCursor(wx.CURSOR_HAND),
            "pencil"  : wx.StockCursor(wx.CURSOR_PENCIL),
            "sizenwse": wx.StockCursor(wx.CURSOR_SIZENWSE)
        }

        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.SetName("MapWindow")

        #
        # set the size & system icon
        #
        self.SetClientSize(size)
        self.iconsize = (16, 16)

        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass_map.ico'), wx.BITMAP_TYPE_ICO))

        #
        # Fancy gui
        #
        # self._mgr = auimgr
        self._mgr = wx.aui.AuiManager(self)

        #
        # Add toolbars
        #
        self.toolbars = { 'map' : None,
                          'vdigit' : None,
                          'georect' : None, 
                          'nviz' : None }
      #  for toolb in toolbars:
#            self.AddToolbar(toolb)

        #
        # Add statusbar
        #

        self.statusbar = self.CreateStatusBar(number=4, style=0)
        self.statusbar.SetStatusWidths([-5, -2, -1, -1])
        self.statusbarWin = dict()
        self.statusbarWin['toggle'] = wx.Choice(self.statusbar, wx.ID_ANY,
                                                choices = globalvar.MAP_DISPLAY_STATUSBAR_MODE)
        self.statusbarWin['toggle'].SetSelection(UserSettings.Get(group='display',
                                                                  key='statusbarMode',
                                                                  subkey='selection'))
        self.statusbar.Bind(wx.EVT_CHOICE, self.OnToggleStatus, self.statusbarWin['toggle'])
        # auto-rendering checkbox
        self.statusbarWin['render'] = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                                  label=_("Render"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleRender, self.statusbarWin['render'])
        self.statusbarWin['render'].SetValue(UserSettings.Get(group='display',
                                                              key='autoRendering',
                                                              subkey='enabled'))
        self.statusbarWin['render'].SetToolTip(wx.ToolTip (_("Enable/disable auto-rendering")))
        # show region
        self.statusbarWin['region'] = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                                  label=_("Show computational extent"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleShowRegion, self.statusbarWin['region'])

        self.statusbarWin['region'].SetValue(False)
        self.statusbarWin['region'].Hide()
        self.statusbarWin['region'].SetToolTip(wx.ToolTip (_("Show/hide computational "
                                                             "region extent (set with g.region). "
                                                             "Display region drawn as a blue box inside the "
                                                             "computational region, "
                                                             "computational region inside a display region "
                                                             "as a red box).")))
        # set resolution
        self.statusbarWin['resolution'] = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                                      label=_("Constrain display resolution to computational settings"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleResolution, self.statusbarWin['resolution'])
        self.statusbarWin['resolution'].SetValue(UserSettings.Get(group='display', key='compResolution', subkey='enabled'))
        self.statusbarWin['resolution'].Hide()
        self.statusbarWin['resolution'].SetToolTip(wx.ToolTip (_("Constrain display resolution "
                                                                 "to computational region settings. "
                                                                 "Default value for new map displays can "
                                                                 "be set up in 'User GUI settings' dialog.")))
        # map scale
        self.statusbarWin['mapscale'] = wx.ComboBox(parent = self.statusbar, id = wx.ID_ANY,
                                                    style = wx.TE_PROCESS_ENTER,
                                                    size=(150, -1))
        self.statusbarWin['mapscale'].SetItems(['1:1000',
                                                '1:5000',
                                                '1:10000',
                                                '1:25000',
                                                '1:50000',
                                                '1:100000',
                                                '1:1000000'])
        self.statusbarWin['mapscale'].Hide()
        self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnChangeMapScale, self.statusbarWin['mapscale'])
        self.statusbar.Bind(wx.EVT_COMBOBOX, self.OnChangeMapScale, self.statusbarWin['mapscale'])

        # go to
        self.statusbarWin['goto'] = wx.TextCtrl(parent=self.statusbar, id=wx.ID_ANY,
                                                value="", style=wx.TE_PROCESS_ENTER,
                                                size=(300, -1))
        self.statusbarWin['goto'].Hide()
        #self.statusbar.Bind(wx.EVT_TEXT_ENTER, MapFrame.OnGoTo, self.statusbarWin['goto'])


        # projection
        self.statusbarWin['projection'] = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                                      label=_("Use defined projection"))
        self.statusbarWin['projection'].SetValue(False)
        size = self.statusbarWin['projection'].GetSize()
        self.statusbarWin['projection'].SetMinSize((size[0] + 150, size[1]))
        self.statusbarWin['projection'].SetToolTip(wx.ToolTip (_("Reproject coordinates displayed "
                                                                 "in the statusbar. Projection can be "
                                                                 "defined in GUI preferences dialog "
                                                                 "(tab 'Display')")))
        self.statusbarWin['projection'].Hide()

        # mask
        self.statusbarWin['mask'] = wx.StaticText(parent = self.statusbar, id = wx.ID_ANY,
                                                  label = '')
        self.statusbarWin['mask'].SetForegroundColour(wx.Colour(255, 0, 0))

        # on-render gauge
        self.statusbarWin['progress'] = wx.Gauge(parent=self.statusbar, id=wx.ID_ANY,
                                      range=0, style=wx.GA_HORIZONTAL)
        self.statusbarWin['progress'].Hide()
        self.StatusbarReposition() # reposition statusbar


        #
        # Init map display (buffered DC & set default cursor)
        #
        self.MapWindow2D = BufferedWindow2(self, id=wx.ID_ANY,
                                          Map=self.Map, tree=self.tree, lmgr=self.gismanager)
        # default is 2D display mode
        self.MapWindow = self.MapWindow2D
        #self.MapWindow.Bind(wx.EVT_MOTION, BufferedWindow2.OnMotion)
        self.MapWindow.SetCursor(self.cursors["default"])
        # used by Nviz (3D display mode)
        self.MapWindow3D = None 

        self.MapWindow.Bind(wx.EVT_LEFT_DCLICK,self.OnButtonDClick)
        self.MapWindow.Bind(wx.EVT_RIGHT_DCLICK,self.RDClick)

        #
        # initialize region values
        #
        self.width, self.height = self.GetClientSize()
        self.Map.ChangeMapSize(self.GetClientSize())
        self.Map.region = self.Map.GetRegion() 

        #
        # Bind various events
        #
        #self.Bind(wx.EVT_ACTIVATE, self.OnFocus)
        self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)
        #self.Bind(render.EVT_UPDATE_PRGBAR, self.OnUpdateProgress)

        #
        # Update fancy gui style
        #
        self._mgr.AddPane(self.MapWindow, wx.aui.AuiPaneInfo().CentrePane().
                   Dockable(False).BestSize((-1,-1)).
                   CloseButton(False).DestroyOnClose(True).
                   Layer(0))
        self._mgr.Update()

        #
        # Init print module and classes
        #
        #self.printopt = disp_print.PrintOptions(self, self.MapWindow)

        #
        # Initialization of digitization tool
        #
        self.digit = None

        #
        # Init zoom history
        #

        #
        # Re-use dialogs
        #
        self.dialogs = {}
        self.dialogs['attributes'] = None
        self.dialogs['category'] = None
        self.dialogs['barscale'] = None
        self.dialogs['legend'] = None

        self.decorationDialog = None # decoration/overlays

        #
        # Re-use dialogs
        #
        self.coords = []
        self.coor = []
        self.mapname = 'lsat7_2000_10@' + grass1.gisenv()['MAPSET']
        self.cmd= ['d.rast', str("map=" + self.mapname)]
        self.Map.AddLayer(type='raster', name=self.mapname, command=self.cmd)
        self.MapWindow.UpdateMap(render=True)  



        self.dialogs = {}
        self.dialogs['attributes'] = None
        self.dialogs['category'] = None
        self.dialogs['barscale'] = None
        self.dialogs['legend'] = None

        self.decorationDialog = None # decoration/overlays

        #self.Maximize()

        self.X = []
        self.Y = []
        self.tempX = [] 
        self.tempY = [] 

        self.npoints = 0

        self.VX = []
        self.VY = []
        self.perimeter_npoints = 0
        self.perimeterX = []
        self.perimeterY = []
        self.Region_perimeter= []

        # initialize

        self.data_type = []
        self.inrast = []
        self.infd = []
        self.Band_sum = []
        self.Bandbuf = []
        self.Band_histo = []
        self.Band_Product = []
        self.Band_min = []
        self.Band_max = []
        self.np = 0

        # find map in search path

        self.name = ['lsat7_2000_10','lsat7_2000_20','lsat7_2000_30','lsat7_2000_40','lsat7_2000_50','lsat7_2000_70']
        # determine the inputmap type (CELL/FCELL/DCELL) */
     #   for n in range(0,6):
      #      self.data_type = grass.G_raster_map_type(name[n], mapset)
       #     self.infd.append( grass.G_open_cell_old(name[n], mapset))






        # determine the inputmap type (CELL/FCELL/DCELL) */
        self.mapset ='landsat'
        self.mapset = c_char_p(self.mapset).value

        self.open_band_files()


        self.vnrows = 0
        self.vncols = 0
        self.hnrows = 0
        self.hncols = 0
        self.htop = self.hbottom = self.hleft = self.hright = 0
        self.view()
        self.viewhistogram()


        self.cellhd = grasslib.Cell_head()


        if (raster.Rast_get_cellhd('lsat7_2000_10', self.mapset, byref(self.cellhd)))==0 :
            print "error1"
#9400694566

        self.Band_cellhd = self.cellhd
        self.dst = self.adjust_window_to_box(self.cellhd, self.vnrows, self.vncols)
        self.vcleft = self.vleft + (self.vncols - self.dst.cols) / 2
        self.vcright = self.vcleft + self.dst.cols - 1
        self.vctop = self.vtop + (self.vnrows - self.dst.rows) / 2
        self.vcbottom = self.vctop + self.dst.rows - 1
        self.vc_ns_res = self.cellhd.ns_res
        self.vc_ew_res = self.cellhd.ew_res


        for b in xrange(6):
            self.Band_sum.append(0.0)
            self.Band_histo.append([])
            for b2 in xrange(256):
                self.Band_Product.append([])
                self.Band_histo[b].append(0.0)
            for b2 in xrange(255):
                self.Band_Product[b].append(0)



#define AFTER_STD 1
#define BEFORE_STD 0

    def histograms(self, nbands, bsum, histo,np,inmin,inmax,b_or_a):

        nrows = self.hnrows
        ncols = self.hncols
        nbands = 6
        old_range = 0
        BORDER = 10
        MIN_HISTO_WIDTH = 1
        MAX_HISTO_WIDTH = 11



        if (b_or_a == 1):
            max_range = 1
            for b in xrange(nbands):
                if (inmax[b] - inmin[b] > max_range):
                    max_range = inmax[b] - inmin[b]
                old_range = max_range

        else:
            max_range = old_range

        try:
            histo_width = (ncols - BORDER * 2) / max_range
        except:
            histo_width = ncols
        if (histo_width % 2 == 0):
            histo_width = histo_width - 1
        if (histo_width < MIN_HISTO_WIDTH):
            histo_width = MIN_HISTO_WIDTH
        elif (histo_width > MAX_HISTO_WIDTH):
            histo_width = MAX_HISTO_WIDTH

        height = (nrows - BORDER * 2) / nbands
        width = (ncols - BORDER * 2) / histo_width * histo_width
        nbars = width / histo_width



        h_top = self.htop + BORDER
        h_left = self.hleft + BORDER
        h_right = h_left + width - 1

        grand_max = 0;
        for b in xrange(nbands):
            for x1 in xrange(256):
                if (histo[b][x1] > grand_max):
                    grand_max = histo[b][x1]


        LEGEND_SPACE =  3 * (width/30)
        if (grand_max > 0):
            scale = (height - LEGEND_SPACE) / grand_max;
        else:
            scale = 0;



        for b in xrange(nbands):

            h_bottom = h_top + height - 1
            bottom_adjusted = h_bottom - 2 * LEGEND_SPACE / 3
            mean = (self.Band_sum[b]/self.np)
            #std_dev = self.std_dev(b)
            cat = mean - (nbars - 1) / 2
            y1 = y2 = bottom_adjusted
            x1 = h_left
            x2 = h_left + histo_width - 1

            bar = 0
            nbars  = int(nbars)
            cat =  int(cat)
            while ((bar < nbars) and (cat < 256)):
                if (cat >= 0):
                    y2 = bottom_adjusted - (histo[b][cat] * scale + .5)
                xy1 = x1,y2
                xy2 = x2,y2
                self.coor.append(xy1)
                self.coor.append(xy2)
                y1 = y2
                x1 = x2
                bar = bar +1

                cat = cat +1
                x2 = x2+histo_width


                h_top = h_bottom + 1

            self.polypen = wx.Pen(colour="GREEN", width=1, style=wx.SOLID)
            pdc = wx.PaintDC(self.MapWindow)
            pdc.BeginDrawing()
            pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
            pdc.SetPen(self.polypen)
            if (len(self.coor) < 2):
                return
            i = 1
            while i < len(self.coor):
                pdc.DrawLinePoint(wx.Point(self.coor[i-1][0], self.coor[i-1][1]),
                                  wx.Point(self.coor[i][0], self.coor[i][1]))
                i += 1
            pdc.EndDrawing()
            self.coor = []



    def viewhistogram(self):

        SCREEN_TOP = 0
        SCREEN_BOTTOM=480
        SCREEN_LEFT =0
        SCREEN_RIGHT =640

#VIEW_HISTO = makeview(2.5, 100.0, 0.0, 50.0);
#static View *makeview(double bottom, double top, double left, double right)


        top =100.0
        bottom =2.5
        left =0.0
        right =50.0
        top = 100 - top
        bottom = 100 - bottom


        self.htop = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * top / 100.0
        self.hbottom = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * bottom / 100.0
        self.hleft = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * left / 100.0
        self.hright = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * right / 100.0


        if self.htop < SCREEN_TOP:
            self.htop = SCREEN_TOP
        if self.hbottom > SCREEN_BOTTOM:
            self.hbottom = SCREEN_BOTTOM
        if self.hleft < SCREEN_LEFT:
            self.hleft = SCREEN_LEFT
        if self.hright > SCREEN_RIGHT:
            self.hright = SCREEN_RIGHT

        self.htop+=1
        self.hbottom-=1
        self.hleft+=1
        self.hright-=1

        self.hnrows = self.hbottom - self.htop + 1
        self.hncols = self.hright - self.hleft + 1


    def open_band_files(self):


        for n in xrange(6):

            self.data_type.append(raster.Rast_map_type(self.name[n], self.mapset))

            if self.data_type[n] == 0:
                ptype = POINTER(c_int)
            elif self.data_type[n] == 1:
                ptype = POINTER(c_float)
            elif self.data_type[n] == 2:
                ptype = POINTER(c_double)

            self.infd.append(raster.Rast_open_old(self.name[n], self.mapset))
            self.Bandbuf.append(raster.Rast_allocate_buf(self.data_type[n]))
            self.Bandbuf[n] = cast(c_void_p(self.Bandbuf[n]), ptype)




    def readbands(self,y):
        self.y = int(y)
        if self.y < 0:
            self.y = 0

        for n in range(0,6):
            raster.Rast_get_row(self.infd[n], self.Bandbuf[n], self.y, self.data_type[n])



    def prepare(self,nbands):

        i = 1


        self.nbands = nbands
        while(i < self.perimeter_npoints):

            y = self.perimeterY[i]
            self.readbands(y)

            x0 = int(self.perimeterX[i-1] - 1)
            x1 = int(self.perimeterX[i] - 1)
            if x0 > x1 :
                #print "error0"
                return -1
            x = x0
            while x <= x1:

                self.np +=1
                for b in range(0,self.nbands):
                    n = self.Bandbuf[b][x]
                    if ( (n <0) or (n > 255)):
                        print "error2"
                        return
                    self.Band_sum[b] = self.Band_sum[b] + n
                    self.Band_histo[b][n]= self.Band_histo[b][n] + 1
                    if self.np == 1:
                        self.Band_min.append(n)
                        self.Band_max.append(n)
                    if self.Band_min[b] > n:
                        self.Band_min[b] = n
                    if self.Band_max[b] < n:
                        self.Band_max[b] = n
                    b2 = 0
                    while b2<=b:
                        self.Band_Product[b][b2] += n * self.Bandbuf[b2][x]
                        b2 = b2 +1
                x = x + 1
            i = i + 2


    def Redraw(self):
        self.polypen = wx.Pen(colour="RED", width=2, style=wx.SOLID)
        pdc = wx.PaintDC(self.MapWindow)
        pdc.BeginDrawing()
        pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
        pdc.SetPen(self.polypen)
        if (len(self.coords) < 2):
            return
        i = 1
        while i < len(self.coords):
            pdc.DrawLinePoint(wx.Point(self.coords[i-1][0], self.coords[i-1][1]),
                              wx.Point(self.coords[i][0], self.coords[i][1]))
            i += 1
        pdc.EndDrawing()
        self.MapWindow.UpdateMap()

    def RDClick(self,event):
        self.outline()

        self.add_point(self.X[0] , self.Y[0])
        self.Redraw()


        self.prepare(6)
        self.histograms(6, self.Band_sum, self.Band_histo,self.np,self.Band_min,self.Band_max,0)




    def outline(self):
        for cur in range(0,self.npoints):
            x,y = self.coords[cur]
            tmpx = self.view_to_row(y)
            tmpy = self.view_to_col(x)
            tmp_n = self.row_to_northing(tmpy, 0.5)
            tmp_e = self.col_to_easting(tmpx, 0.5)
            self.tempY.append(raster.Rast_northing_to_row(tmp_n, byref(self.Band_cellhd)))
            self.tempX.append(raster.Rast_easting_to_col(tmp_e, byref(self.Band_cellhd)))

        first = -1
        prev = self.npoints -1


        for cur in range(0,self.npoints):

            if self.tempY[cur]!= self.tempY[prev]:
                first = cur
                break

        skip = 0
        VN = 0
        cur = 0

        if skip == 0:

            self.VX.append(self.tempX[cur])
            self.VY.append(self.tempY[cur])
            VN=VN + 1

        prev = cur   
        cur = cur + 1

        if cur >=self.npoints:
            cur = 0
        next = cur +1
        if next >= self.npoints:
            next = 0

        skip = ((self.tempY[prev] == self.tempY[cur]) and (self.tempY[next] == self.tempY[cur]))

        while cur != first:
            if skip == 0:

                self.VX.append(self.tempX[cur])
                self.VY.append(self.tempY[cur])
                VN=VN + 1


            cur = cur + 1
            prev = cur
            if cur >=self.npoints:
                cur = 0
            next = cur +1
            if next >= self.npoints:
                next = 0
            try:
                skip = ((self.tempY[prev] == self.tempY[cur]) and (self.tempY[next] == self.tempY[cur]))
            except:
                pass


        np = 0
        prev  = VN - 1
        for cur in range(0,self.npoints):
            try:
                np= np + abs(self.VY[prev] - self.VY[cur])
            except:
                pass

        PN = 0
        prev = VN - 1

        cur = 0

        while(cur< VN):
            self.edge(self.VX[prev], self.VY[prev],self.VX[cur],self.VY[cur])

            prev = cur
            cur = cur + 1

        prev =  VN - 1
        cur = 0
###################################################################
###################################################################
        next = cur + 1
        if next>=VN :
            next = 0

        if (((self.VY[prev]<self.VY[cur]) and (self.VY[next]<self.VY[cur])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[next]>self.VY[cur]))) :
            skip = 1

        elif (((self.VY[prev]<self.VY[cur]) and (self.VY[cur]<self. VY[next])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[cur]>self. VY[next]))):
            skip = 0
        else:
            skip = 0
            next +=1
            if next >= VN :
                next = 0

            if (((self.VY[prev]<self.VY[cur]) and (self.VY[next]<self.VY[cur])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[next]>self.VY[cur]))):
                skip = 1

        if skip == 0:
            self.edge_point(self.VX[cur], self.VY[cur])

        cur = next
        prev = cur - 1

###################################################################

        while cur!=0 :
            next = cur + 1
            if next>=VN :
                next = 0

            if (((self.VY[prev]<self.VY[cur]) and (self.VY[next]<self.VY[cur])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[next]>self.VY[cur]))) :
                skip = 1

            elif (((self.VY[prev]<self.VY[cur]) and (self.VY[cur]<self. VY[next])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[cur]>self. VY[next]))):
                skip = 0
            else:
                skip = 0
                next +=1
                if next >= VN :
                    next = 0

                if (((self.VY[prev]<self.VY[cur]) and (self.VY[next]<self.VY[cur])) or ((self.VY[prev]>self.VY[cur]) and (self.VY[next]>self.VY[cur]))):
                    skip = 1

            if skip == 0:
                self.edge_point(self.VX[cur], self.VY[cur])

            cur = next
            prev = cur - 1


        for i in range(0,len(self.perimeterX)):
            a = self.perimeterX[i]
            b = self.perimeterY[i]
            xy = a,b
            self.Region_perimeter.append(xy)


        self.Region_perimeter.sort()





    def edge(self, x0, y0, x1, y1):


        if y0 == y1:
            return 0

        x =x0


        m = float((x0 -x1)/(y0-y1))

        if y0 < y1 :
            y0+=1 
            while y0 < y1 :
                x = x+m
                x0 = x +0.5
                self.edge_point(x0,y0)
                y0 = y0 + 1
        else:
            y0 = y0 - 1
            while y0 > y1 :
                x = x - m
                x0 = x + 0.5
                self.edge_point(x0,y0)
                y0 = y0 - 1


    def edge_point(self, x , y):
        n = self.perimeter_npoints  = self.perimeter_npoints + 1
        self.perimeterX.append(x)
        self.perimeterY.append(y)



    def row_to_northing(self, row, location):
        return (self.dst.north - (row + location) * self.dst.ns_res)

    def col_to_easting(self, col, location):
        return (self.dst.west + (col + location) * self.dst.ew_res)


    def view_to_row(self, y):
        return (y - self.vctop)


    def view_to_col(self, x):
        return (x - self.vcleft)




    def adjust_window_to_box(self,src, rows, cols):
        dst = grasslib.Cell_head()
        dst = src
        ns = src.ns_res
        ns = (src.ns_res * src.rows) / rows
        ew = (src.ew_res * src.cols) / cols

        if ns > ew:
            ew = ns
        else:
            ns = ew

        dst.ns_res = ns
        dst.ew_res = ew

        r = int(abs(round(((dst.north - dst.south) / dst.ns_res),0)))
        c = int(abs(round(( (dst.east - dst.west) / dst.ew_res),0)))
        dst.rows = r
        dst.cols = c
        return dst


    def view(self):
        SCREEN_TOP = 0
        SCREEN_BOTTOM=480
        SCREEN_LEFT =0
        SCREEN_RIGHT =640


        top =97.5
        bottom =51.0
        left =50.0
        right =100.0
        top = 100 - top
        bottom = 100 - bottom


        self.vtop = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * top / 100.0
        self.vbottom = SCREEN_TOP + (SCREEN_BOTTOM - SCREEN_TOP) * bottom / 100.0
        self.vleft = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * left / 100.0
        self.vright = SCREEN_LEFT + (SCREEN_RIGHT - SCREEN_LEFT) * right / 100.0


        if self.vtop < SCREEN_TOP:
            self.vtop = SCREEN_TOP
        if self.vbottom > SCREEN_BOTTOM:
            self.vbottom = SCREEN_BOTTOM
        if self.vleft < SCREEN_LEFT:
            self.vleft = SCREEN_LEFT
        if self.vright > SCREEN_RIGHT:
            self.vright = SCREEN_RIGHT

        self.vtop+=1
        self.vbottom-=1
        self.vleft+=1
        self.vright-=1

        self.vnrows = self.vbottom - self.vtop + 1
        self.vncols = self.vright - self.vleft + 1






    def OnButtonDClick(self,event): 

        x,y = event.GetPositionTuple()
        self.add_point(x,y)
        self.Redraw()

        #self.outline()




    def add_point(self,x, y):

        last = 0
        last = self.npoints - 1
        if last >= 0 	and x == self.X[last] and y == self.Y[last]:
            return 1

        if self.npoints >= 100 :
            print "Can't mark another point."
            return 0

        xy=x,y

        last+=1
        self.X.append(x)
        self.Y.append(y)
        self.coords.append(xy)
        self.npoints+=1;

        return 1

class BufferedWindow2(BufferedWindow):
    """!A Buffered window class.

    When the drawing needs to change, you app needs to call the
    UpdateMap() method. Since the drawing is stored in a bitmap, you
    can also save the drawing to file by calling the
    SaveToFile(self,file_name,file_type) method.
    """
    def __init__(self, parent, id = wx.ID_ANY,
                 Map = None, tree = None, lmgr = None,
                 style = wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        MapWindow.__init__(self, parent, id, Map, tree, lmgr, **kwargs)
        wx.Window.__init__(self, parent, id, style = style, **kwargs)

        # flags
        self.resize = False # indicates whether or not a resize event has taken place
        self.dragimg = None # initialize variable for map panning

        self.tree = tree
        self.Map = Map
        # variables for drawing on DC
        self.pen = None      # pen for drawing zoom boxes, etc.
        self.polypen = None  # pen for drawing polylines (measurements, profiles, etc)
        # List of wx.Point tuples defining a polyline (geographical coordinates)
        self.polycoords = []
        # ID of rubber band line
        self.lineid = None
        # ID of poly line resulting from cumulative rubber band lines (e.g. measurement)
        self.plineid = None

        # event bindings
        self.Bind(wx.EVT_PAINT,        self.OnPaint)
        self.Bind(wx.EVT_SIZE,         self.OnSize)
        self.Bind(wx.EVT_IDLE,         self.OnIdle)
        ### self.Bind(wx.EVT_MOTION,       self.MouseActions)
       # self.Bind(wx.EVT_MOUSE_EVENTS, self.MouseActions)

#        if grassversion.rfind("6.4") != 0:
       #     self.Bind(wx.EVT_MOTION,       self.OnMotion)




        self.processMouse = True

        # render output objects
        self.mapfile = None   # image file to be rendered
        self.img     = None   # wx.Image object (self.mapfile)
        # used in digitization tool (do not redraw vector map)
        self.imgVectorMap = None
        # decoration overlays
        self.overlays = {}
        # images and their PseudoDC ID's for painting and dragging
        self.imagedict = {}   
        self.select = {}      # selecting/unselecting decorations for dragging
        self.textdict = {}    # text, font, and color indexed by id
        self.currtxtid = None # PseudoDC id for currently selected text

        # zoom objects
        self.zoomhistory  = [] # list of past zoom extents
        self.currzoom     = 0 # current set of extents in zoom history being used
        self.zoomtype     = 1   # 1 zoom in, 0 no zoom, -1 zoom out
        self.hitradius    = 10 # distance for selecting map decorations
        self.dialogOffset = 5 # offset for dialog (e.g. DisplayAttributesDialog)

        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        ### self.OnSize(None)
#        if grassversion.rfind("6.4") != 0:
        self.pdc = wx.PseudoDC()
        # used for digitization tool
        self.pdcVector = None
        # decorations (region box, etc.)
        self.pdcDec = wx.PseudoDC()
        # pseudoDC for temporal objects (select box, measurement tool, etc.)
        self.pdcTmp = wx.PseudoDC()

        # redraw all pdc's, pdcTmp layer is redrawn always (speed issue)
        self.redrawAll = True

        # will store an off screen empty bitmap for saving to file
        self._buffer = ''

        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
#        self.Bind(wx.EVT_KEY_DOWN , Bufferedwindow.OnKeyDown)

        # vars for handling mouse clicks
        self.dragid   = -1
        self.lastpos  = (0, 0)


    def OnPaint(self, event):
        """!
        Draw PseudoDC's to buffered paint DC

        self.pdc for background and decorations
        self.pdcVector for vector map which is edited
        self.pdcTmp for temporaly drawn objects (self.polycoords)

        If self.redrawAll is False on self.pdcTmp content is re-drawn
        """
        Debug.msg(4, "BufferedWindow.OnPaint(): redrawAll=%s" % self.redrawAll)



        dc = wx.BufferedPaintDC(self, self.buffer)

        ### dc.SetBackground(wx.Brush("White"))
        dc.Clear()

        # use PrepareDC to set position correctly
        self.PrepareDC(dc)

        # create a clipping rect from our position and size
        # and update region
        rgn = self.GetUpdateRegion().GetBox()
        dc.SetClippingRect(rgn)

        switchDraw = False
        if self.redrawAll is None:
            self.redrawAll = True
            switchDraw = True

        if self.redrawAll: # redraw pdc and pdcVector
            # draw to the dc using the calculated clipping rect
            self.pdc.DrawToDCClipped(dc, rgn)

            # draw vector map layer
            if self.pdcVector:
                # decorate with GDDC (transparency)
                try:
                    gcdc = wx.GCDC(dc)
                    self.pdcVector.DrawToDCClipped(gcdc, rgn)
                except NotImplementedError, e:
                    print >> sys.stderr, e
                    self.pdcVector.DrawToDCClipped(dc, rgn)

            self.bufferLast = None
        else: # do not redraw pdc and pdcVector
            if self.bufferLast is None:
                # draw to the dc
                self.pdc.DrawToDC(dc)

                if self.pdcVector:
                    # decorate with GDDC (transparency)
                    try:
                        gcdc = wx.GCDC(dc)
                        self.pdcVector.DrawToDC(gcdc)
                    except NotImplementedError, e:
                        print >> sys.stderr, e
                        self.pdcVector.DrawToDC(dc)

                # store buffered image
                # self.bufferLast = wx.BitmapFromImage(self.buffer.ConvertToImage())
                self.bufferLast = dc.GetAsBitmap(wx.Rect(0, 0, self.Map.width, self.Map.height))

            pdcLast = self.PseudoDC(vdigit = False)
            pdcLast.DrawBitmap(self.bufferLast, 0, 0, False)
            pdcLast.DrawToDC(dc)

        # draw decorations (e.g. region box)
        try:
            gcdc = wx.GCDC(dc)
            self.pdcDec.DrawToDC(gcdc)
        except NotImplementedError, e:
            print >> sys.stderr, e
            self.pdcDec.DrawToDC(dc)

        # draw temporary object on the foreground
        ### self.pdcTmp.DrawToDCClipped(dc, rgn)
        self.pdcTmp.DrawToDC(dc)

        if switchDraw:
            self.redrawAll = False

        self.polypen = wx.Pen(colour="RED", width=1, style=wx.SOLID)

        self.pdc.BeginDrawing()
        self.pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
        self.pdc.SetPen(self.polypen)
        if (len(self.parent.coords) < 2):
            return
        i = 1
        while i < len(self.parent.coords):
            self.pdc.DrawLinePoint(wx.Point(self.parent.coords[i-1][0], self.parent.coords[i-1][1]),
                              wx.Point(self.parent.coords[i][0], self.parent.coords[i][1]))
            i += 1
        self.pdc.EndDrawing()  

        self.polypen = wx.Pen(colour="GREEN", width=1, style=wx.SOLID)
        self.pdc.BeginDrawing()
        self.pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
        self.pdc.SetPen(self.polypen)
        if (len(self.parent.coor) < 2):
            return
        i = 1
        while i < len(self.parent.coor):
            self.pdc.DrawLinePoint(wx.Point(self.parent.coor[i-1][0], self.parent.coor[i-1][1]),
                              wx.Point(self.parent.coor[i][0], self.parent.coor[i][1]))
            i += 1
        self.pdc.EndDrawing()
        self.Refresh()

    def UpdateMap(self, render=True, renderVector=True):
        """!
        Updates the canvas anytime there is a change to the
        underlaying images or to the geometry of the canvas.

        @param render re-render map composition
        @param renderVector re-render vector map layer enabled for editing (used for digitizer)
        """
        start = time.clock()

        self.resize = False

        # if len(self.Map.GetListOfLayers()) == 0:
        #    return False

        if self.img is None:
            render = True

        #
        # initialize process bar (only on 'render')
        #
        if render is True or renderVector is True:
            self.parent.statusbarWin['progress'].Show()
            if self.parent.statusbarWin['progress'].GetRange() > 0:
                self.parent.statusbarWin['progress'].SetValue(1)

        #
        # render background image if needed
        #

        # update layer dictionary if there has been a change in layers
        if self.tree and self.tree.reorder == True:
            self.tree.ReorderLayers()

        # reset flag for auto-rendering
        if self.tree:
            self.tree.rerender = False

        if render:
            # update display size
            self.Map.ChangeMapSize(self.GetClientSize())
            if self.parent.statusbarWin['resolution'].IsChecked():
                # use computation region resolution for rendering
                windres = True
            else:
                windres = False
            self.mapfile = self.Map.Render(force=True, mapWindow=self.parent,
                                           windres=windres)
        else:
            self.mapfile = self.Map.Render(force=False, mapWindow=self.parent)

        self.img = self.GetImage() # id=99

        #
        # clear pseudoDcs
        #
        for pdc in (self.pdc,
                    self.pdcDec,
                    self.pdcTmp):
            pdc.Clear()
            pdc.RemoveAll()

        #
        # draw background map image to PseudoDC
        #
        if not self.img:
            self.Draw(self.pdc, pdctype='clear')
        else:
            try:
                id = self.imagedict[self.img]['id']
            except:
                return False

            self.Draw(self.pdc, self.img, drawid=id)

        #
        # render vector map layer
        #



        # render overlays
        #
        for img in self.GetOverlay():
            # draw any active and defined overlays
            if self.imagedict[img]['layer'].IsActive():
                id = self.imagedict[img]['id']
                self.Draw(self.pdc, img=img, drawid=id,
                          pdctype=self.overlays[id]['pdcType'], coords=self.overlays[id]['coords'])

        for id in self.textdict.keys():
            self.Draw(self.pdc, img=self.textdict[id], drawid=id,
                      pdctype='text', coords=[10, 10, 10, 10])

        # optionally draw computational extent box
        self.DrawCompRegionExtent()

        #
        # redraw pdcTmp if needed
        #
        if len(self.polycoords) > 0:
            self.DrawLines(self.pdcTmp)


        # 
        # clear measurement
        #


        stop = time.clock()

        #
        # hide process bar
        #
        self.parent.statusbarWin['progress'].Hide()

        #
        # update statusbar 
        #
        ### self.Map.SetRegion()
        self.parent.StatusbarUpdate()
        if grass1.find_file(name = 'MASK', element = 'cell')['name']:
            # mask found
            self.parent.statusbarWin['mask'].SetLabel(_('MASK'))
        else:
            self.parent.statusbarWin['mask'].SetLabel('')

        Debug.msg (2, "BufferedWindow.UpdateMap(): render=%s, renderVector=%s -> time=%g" % \
                   (render, renderVector, (stop-start)))

        return True

    def OnMotion(self, event):
        """!Mouse moved
        Track mouse motion and update status bar
        """
        if self.parent.statusbarWin['toggle'].GetSelection() == 0: # Coordinates
            precision = int(UserSettings.Get(group = 'projection', key = 'format',
                                             subkey = 'precision'))
            format = UserSettings.Get(group = 'projection', key = 'format',
                                      subkey = 'll')
            try:
                e, n = self.Pixel2Cell(event.GetPositionTuple())
            except (TypeError, ValueError):
                self.parent.statusbar.SetStatusText("", 0)
                return

            if self.parent.toolbars['vdigit'] and \
                    self.parent.toolbars['vdigit'].GetAction() == 'addLine' and \
                    self.parent.toolbars['vdigit'].GetAction('type') in ('line', 'boundary') and \
                    len(self.polycoords) > 0:
                # for linear feature show segment and total length
                distance_seg = self.Distance(self.polycoords[-1],
                                             (e, n), screen=False)[0]
                distance_tot = distance_seg
                for idx in range(1, len(self.polycoords)):
                    distance_tot += self.Distance(self.polycoords[idx-1],
                                                  self.polycoords[idx],
                                                  screen=False )[0]
                self.parent.statusbar.SetStatusText("%.*f, %.*f (seg: %.*f; tot: %.*f)" % \
                                                 (precision, e, precision, n,
                                                  precision, distance_seg,
                                                  precision, distance_tot), 0)
            else:
                if self.parent.statusbarWin['projection'].IsChecked():
                    if not UserSettings.Get(group='projection', key='statusbar', subkey='proj4'):
                        self.parent.statusbar.SetStatusText(_("Projection not defined (check the settings)"), 0)
                    else:
                        proj, coord  = utils.ReprojectCoordinates(coord = (e, n),
                                                                  projOut = UserSettings.Get(group='projection',
                                                                                             key='statusbar',
                                                                                             subkey='proj4'),
                                                                  flags = 'd')

                        if coord:
                            e, n = coord
                            if proj in ('ll', 'latlong', 'longlat') and format == 'DMS':
                                self.parent.statusbar.SetStatusText(utils.Deg2DMS(e, n, precision = precision),
                                                                    0)
                            else:
                                self.parent.statusbar.SetStatusText("%.*f; %.*f" % \
                                                                        (precision, e, precision, n), 0)
                        else:
                            self.parent.statusbar.SetStatusText(_("Error in projection (check the settings)"), 0)
                else:
                    if self.parent.Map.projinfo['proj'] == 'll' and format == 'DMS':
                        self.parent.statusbar.SetStatusText(utils.Deg2DMS(e, n, precision = precision),
                                                            0)
                    else:
                        self.parent.statusbar.SetStatusText("%.*f; %.*f" % \
                                                                (precision, e, precision, n), 0)
        event.Skip()

    def OnLeftUp(self, event):
        """!Left mouse button released
        """
        Debug.msg (5, "BufferedWindow.OnLeftUp(): use=%s" % \
                       self.mouse["use"])

        self.mouse['end'] = event.GetPositionTuple()[:]

        if self.mouse['use'] in ["zoom", "pan"]:
            # set region in zoom or pan
            begin = self.mouse['begin']
            end = self.mouse['end']

            if self.mouse['use'] == 'zoom':
                # set region for click (zero-width box)
                if begin[0] - end[0] == 0 or \
                        begin[1] - end[1] == 0:
                    # zoom 1/2 of the screen (TODO: settings)
                    begin = (end[0] - self.Map.width / 4,
                             end[1] - self.Map.height / 4)
                    end   = (end[0] + self.Map.width / 4,
                             end[1] + self.Map.height / 4)

            self.Zoom(begin, end, self.zoomtype)

            # redraw map
            self.UpdateMap(render=True)

            # update statusbar
            self.parent.StatusbarUpdate()



class IClassApp(wx.App):
    """
    MapApp class
    """

    def OnInit(self):
        if __name__ == "__main__":
            Map = render.Map() 
        else:
            Map = None


        self.frame = IClass(parent=None, id=wx.ID_ANY, Map=Map,
                               size=globalvar.MAP_WINDOW_SIZE)

        self.frame.Show()
        return 1

# end of class

if __name__ == "__main__":


    iclass_app = IClassApp(0)

    iclass_app.MainLoop()


    sys.exit(0)
