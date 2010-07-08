"""!
@package wx.net.path.py

@brief Interface implementation of v.net.path.
Inspired by http://grass.itc.it/gdp/html_grass64/v.net.path.html
Hacked from mapdisp and mapdisp_window from gui_modules

Classes:
- NetworkPath
- NetApp


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

gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','wxpython','gui_modules')

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
from mapdisp import Command
from mapdisp import BufferedWindow
from mapdisp import MapFrame
from debug import Debug
import images
import gcmd
from grass.script import core as grass

import toolbars

imagepath = images.__path__[0]
sys.path.append(imagepath)


class NetworkPath(MapFrame):

    def __init__(self, parent=None, id=wx.ID_ANY, title=_("GRASS GIS - Map display"),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, toolbars=["map"],
                 tree=None, notebook=None, gismgr=None, page=None,
                 Map=None, auimgr=None):


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
        for toolb in toolbars:
            self.AddToolbar(toolb)

        #
        # Add statusbar
        #
        self.statusbar = self.CreateStatusBar(number=4, style=0)
        self.statusbar.SetStatusWidths([-5, -2, -1, -1])
        self.toggleStatus = wx.Choice(self.statusbar, wx.ID_ANY,
                                      choices = globalvar.MAP_DISPLAY_STATUSBAR_MODE)
        self.toggleStatus.SetSelection(UserSettings.Get(group='display', key='statusbarMode', subkey='selection'))
        self.statusbar.Bind(wx.EVT_CHOICE, self.OnToggleStatus, self.toggleStatus)
        # auto-rendering checkbox
        self.autoRender = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                      label=_("Render"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleRender, self.autoRender)
        self.autoRender.SetValue(UserSettings.Get(group='display', key='autoRendering', subkey='enabled'))
        self.autoRender.SetToolTip(wx.ToolTip (_("Enable/disable auto-rendering")))
        # show region
        self.showRegion = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                      label=_("Show computational extent"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleShowRegion, self.showRegion)
        
        self.showRegion.SetValue(False)
        self.showRegion.Hide()
        self.showRegion.SetToolTip(wx.ToolTip (_("Show/hide computational "
                                                 "region extent (set with g.region). "
                                                 "Display region drawn as a blue box inside the "
                                                 "computational region, "
                                                 "computational region inside a display region "
                                                 "as a red box).")))
        # set resolution
        self.compResolution = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                         label=_("Constrain display resolution to computational settings"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleResolution, self.compResolution)
        self.compResolution.SetValue(UserSettings.Get(group='display', key='compResolution', subkey='enabled'))
        self.compResolution.Hide()
        self.compResolution.SetToolTip(wx.ToolTip (_("Constrain display resolution "
                                                     "to computational region settings. "
                                                     "Default value for new map displays can "
                                                     "be set up in 'User GUI settings' dialog.")))
        # map scale
        self.mapScale = wx.TextCtrl(parent=self.statusbar, id=wx.ID_ANY,
                                    value="", style=wx.TE_PROCESS_ENTER,
                                    size=(150, -1))
        self.mapScale.Hide()
        self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnChangeMapScale, self.mapScale)

        # mask
        self.maskInfo = wx.StaticText(parent = self.statusbar, id = wx.ID_ANY,
                                                  label = '')
        self.maskInfo.SetForegroundColour(wx.Colour(255, 0, 0))
        

        # on-render gauge
        self.onRenderGauge = wx.Gauge(parent=self.statusbar, id=wx.ID_ANY,
                                      range=0, style=wx.GA_HORIZONTAL)
        self.onRenderGauge.Hide()
        
        self.StatusbarReposition() # reposition statusbar

        #
        # Init map display (buffered DC & set default cursor)
        #
        self.MapWindow2D = BufferedWindow(self, id=wx.ID_ANY,
                                          Map=self.Map, tree=self.tree, gismgr=self.gismanager)
        # default is 2D display mode
        self.MapWindow = self.MapWindow2D
        self.MapWindow.Bind(wx.EVT_MOTION, self.OnMotion)
        self.MapWindow.SetCursor(self.cursors["default"])
        # used by Nviz (3D display mode)
        self.MapWindow3D = None 

        self.MapWindow.Bind(wx.EVT_LEFT_DCLICK,self.OnButtonDClick)

        #
        # initialize region values
        #
        self.__InitDisplay() 

        #
        # Bind various events
        #
        #self.Bind(wx.EVT_ACTIVATE, self.OnFocus)
        self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)
        self.Bind(render.EVT_UPDATE_PRGBAR, self.OnUpdateProgress)
        
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
        self.MapWindow.ZoomHistory(self.Map.region['n'],
                                   self.Map.region['s'],
                                   self.Map.region['e'],
                                   self.Map.region['w'])

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
	self.mapname = 'roads@' + grass.gisenv()['MAPSET']
	self.cmd= ['d.vect', str("map=" + self.mapname),'width=4']
	self.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
	self.MapWindow.UpdateMap(render=True)  

        self.dialogs = {}
        self.dialogs['attributes'] = None
        self.dialogs['category'] = None
        self.dialogs['barscale'] = None
        self.dialogs['legend'] = None

        self.decorationDialog = None # decoration/overlays

        #self.Maximize()
	self.points = []





    def OnButtonDClick(self,event): 

	self.mapname = 'graph@' + grass.gisenv()['MAPSET']
	self.Map.RemoveLayer(name=self.mapname)
	self.MapWindow.UpdateMap(render=True)

       # precision = int(UserSettings.Get(group = 'projection', key = 'format',
          #                                   subkey = 'precision'))
        try:
            e, n = self.MapWindow.Pixel2Cell(event.GetPositionTuple())
	    print e,n
        except AttributeError:
            return
        
        self.counter = self.counter + 1
        point =("%f|%f" %  ( e,  n))
        self.points.append(point + '|point')
        if self.counter == 2:
            f =open("tmp1",'w')
            for p in self.points:
               f.write("%s\n" % p)
            f.close()

            f =open("tmp2",'w')
            f.write("%d %d %d\n" %(1,1,2) )
            f.close()


            command =["g.remove",'vect=path,vnet,startend']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()
    

#            command =["v.in.ascii",'input=tmp1','output=startend']
            z =gcmd.RunCommand('v.in.ascii',input='tmp1',output='startend')

  	    if z == 1:
		print "error executing v.in.ascii"
		return 1

            #command=["v.net", "input=roads",'points=startend', 'output=vnet', 'op=connect', 'thresh=200']
            y=gcmd.RunCommand('v.net', input='roads',points='startend', output='vnet', op='connect', thresh='200')
	    if y == 1:
		print "error executing v.net"
		return 1


            #command=["v.net.path", 'input=vnet', 'output=path','file=tmp2']
            x= gcmd.RunCommand('v.net.path', input='vnet', output='path', file='tmp2')
	    if x == 1:
		print "error executing v.net.path"
		return 1


            self.mapname = 'path@'+ grass.gisenv()['MAPSET']
            self.cmd= ['d.vect', str("map=" + self.mapname),'col=red','width=2']
            self.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
            self.MapWindow.UpdateMap(render=True)
            self.counter =0
            self.points=[]



    def __InitDisplay(self):
        """
        Initialize map display, set dimensions and map region
        """
        self.width, self.height = self.GetClientSize()

        Debug.msg(2, "MapFrame.__InitDisplay():")
        self.Map.ChangeMapSize(self.GetClientSize())
        self.Map.region = self.Map.GetRegion() # g.region -upgc
        # self.Map.SetRegion() # adjust region to match display window
    
    def GetLayerManager(self):
        return self

    def AddToolbar(self, name):
        """!Add defined toolbar to the window
        """
        # default toolbar
        self.toolbars['map'] = toolbars.MapToolbar(self, self.Map)

        self._mgr.AddPane(self.toolbars['map'].toolbar,
                              wx.aui.AuiPaneInfo().
                              Name("maptoolbar").Caption(_("Map Toolbar")).
                              ToolbarPane().Top().
                              LeftDockable(False).RightDockable(False).
                              BottomDockable(False).TopDockable(True).
                              CloseButton(False).Layer(2).
                              BestSize((self.toolbars['map'].GetToolbar().GetSize())))
	

class PathApp(wx.App):
    """
    MapApp class
    """

    def OnInit(self):
        if __name__ == "__main__":
            Map = render.Map() 
        else:
            Map = None


        self.frame = NetworkPath(parent=None, id=wx.ID_ANY, Map=Map,
                               size=globalvar.MAP_WINDOW_SIZE)

        self.frame.Show()
        return 1

# end of class

if __name__ == "__main__":


    path_app = PathApp(0)

    path_app.MainLoop()


    sys.exit(0)
