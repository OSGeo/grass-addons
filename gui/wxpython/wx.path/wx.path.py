"""!
@package wx.net.path.py

@brief Interface implementation of v.net.path.
Inspired by http://grass.itc.it/gdp/html_grass64/v.net.path.html
Hacked from mapdip and mapdisp_window from gui_modules

Classes:
- MapFrame
- MapApp


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
from mapdisp_command import Command
from mapdisplay_window import BufferedWindow
from debug import Debug
import images
imagepath = images.__path__[0]
sys.path.append(imagepath)


class NetworkPath(wx.Frame):

    def __init__(self, parent=None, id=wx.ID_ANY, title=_("v.net.path [vector, networking]"),
                 style=wx.DEFAULT_FRAME_STYLE, toolbars=["map"],Map=None,size=wx.DefaultSize):


        self.Map        = Map   
        #
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
        

        wx.Frame.__init__(self, parent, id, title, style = style)
        

        self.SetName('MapWindow')

        self.Maximize()

        wx.MessageBox('Development has only started. currently works with spearfish data (myroads vector file). Kindly bear with me, Thankyou', 'Info')



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
        self.statusbar = self.CreateStatusBar(number=1, style=0)
        self.statusbar.SetStatusWidths([-5, -2, -1, -1])

        #
        # Init map display (buffered DC & set default cursor)
        #
        self.MapWindow2D = BufferedWindow(self, id=wx.ID_ANY, Map=self.Map)
        # default is 2D display mode
        self.MapWindow = self.MapWindow2D
        self.MapWindow.Bind(wx.EVT_MOTION, self.OnMotion)
        # used by Nviz (3D display mode)

        #
        # initialize region values
        #
        self.__InitDisplay() 

        #
        # Bind various events
        #
        #self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)

        
        #
        # Update fancy gui style
        #
        self._mgr.AddPane(self.MapWindow, wx.aui.AuiPaneInfo().CentrePane().
                          Dockable(False).BestSize((-1,-1)).
                          CloseButton(False).DestroyOnClose(True).
                          Layer(0))
        self._mgr.Update()


        # Init zoom history
        #
        self.MapWindow.ZoomHistory(self.Map.region['n'],
                                   self.Map.region['s'],
                                   self.Map.region['e'],
                                   self.Map.region['w'])



    def AddToolbar(self, name):
        self.toolbars['map'] = MapToolbar(self, self.Map)
        self._mgr.AddPane(self.toolbars['map'],
                              wx.aui.AuiPaneInfo().
                              Name("maptoolbar").Caption(_("Map Toolbar")).
                              ToolbarPane().Top().
                              LeftDockable(False).RightDockable(False).
                              BottomDockable(False).TopDockable(True).
                              CloseButton(False).Layer(2).
                              BestSize((self.toolbars['map'].GetSize())))
	
     

        self._mgr.Update()



    def __InitDisplay(self):
        """
        Initialize map display, set dimensions and map region
        """
        self.width, self.height = self.GetClientSize()

        Debug.msg(2, "MapFrame.__InitDisplay():")
        self.Map.ChangeMapSize(self.GetClientSize())
        self.Map.region = self.Map.GetRegion() # g.region -upgc
        # self.Map.SetRegion() # adjust region to match display window



    def OnMotion(self, event):
        """
        Mouse moved
        Track mouse motion and update status bar
        """
        # update statusbar if required

        precision = int(UserSettings.Get(group = 'projection', key = 'format',
                                             subkey = 'precision'))
        try:
                e, n = self.MapWindow.Pixel2Cell(event.GetPositionTuple())
        except AttributeError:
                return

        self.statusbar.SetStatusText("%.*f; %.*f" %  (precision, e, precision, n), 0)
                
        event.Skip()

    def OnDraw(self, event):
        """
        Re-display current map composition
        """
        self.MapWindow.UpdateMap(render=False)
        

        

    def OnPointer(self, event):
        """
        Pointer button clicked
        """
        self.MapWindow.SetCursor(self.cursors["default"])

    def OnZoomIn(self, event):
        """
        Zoom in the map.
        Set mouse cursor, zoombox attributes, and zoom direction
        """
        if self.toolbars['map']:
            self.toolbars['map'].OnTool(event)
            self.toolbars['map'].action['desc'] = ''
        
        self.MapWindow.mouse['use'] = "zoom"
        self.MapWindow.mouse['box'] = "box"
        self.MapWindow.zoomtype = 1
        self.MapWindow.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)
        
        # change the cursor
        self.MapWindow.SetCursor(self.cursors["cross"])

    def OnZoomOut(self, event):
        """
        Zoom out the map.
        Set mouse cursor, zoombox attributes, and zoom direction
        """
        if self.toolbars['map']:
            self.toolbars['map'].OnTool(event)
            self.toolbars['map'].action['desc'] = ''
        
        self.MapWindow.mouse['use'] = "zoom"
        self.MapWindow.mouse['box'] = "box"
        self.MapWindow.zoomtype = -1
        self.MapWindow.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)
        
        # change the cursor
        self.MapWindow.SetCursor(self.cursors["cross"])

    def OnZoomBack(self, event):
        """
        Zoom last (previously stored position)
        """
        self.MapWindow.ZoomBack()

    def OnPan(self, event):
        """
        Panning, set mouse to drag
        """
        if self.toolbars['map']:
            self.toolbars['map'].OnTool(event)
            self.toolbars['map'].action['desc'] = ''
        
        self.MapWindow.mouse['use'] = "pan"
        self.MapWindow.mouse['box'] = "pan"
        self.MapWindow.zoomtype = 0
        
        # change the cursor
        self.MapWindow.SetCursor(self.cursors["hand"])

    def OnErase(self, event):
        """
        Erase the canvas
        """
        self.MapWindow.EraseMap()

    def OnZoomRegion(self, event):
        """
        Zoom to region
        """
        self.Map.getRegion()
        self.Map.getResolution()
        self.UpdateMap()
        # event.Skip()




        
    def GetRender(self):
        """!Returns current instance of render.Map()
        """
        return self.Map

    def GetWindow(self):
        """!Get map window"""
        return self.MapWindow
    



    def GetOptData(self, dcmd, type, params, propwin):
        """
        Callback method for decoration overlay command generated by
        dialog created in menuform.py
        """
        # Reset comand and rendering options in render.Map. Always render decoration.
        # Showing/hiding handled by PseudoDC
        self.Map.ChangeOverlay(ovltype=type, type='overlay', name='', command=dcmd,
                               l_active=True, l_render=False)
        self.params[type] = params
        self.propwin[type] = propwin

    def OnZoomToMap(self, event):
        """!
        Set display extents to match selected raster (including NULLs)
        or vector map.
        """
        self.MapWindow.ZoomToMap()

    def OnZoomToRaster(self, event):
        """!
        Set display extents to match selected raster map (ignore NULLs)
        """
        self.MapWindow.ZoomToMap(ignoreNulls = True)



        

# end of class MapFrame

        
class MapToolbar(toolbars.AbstractToolbar):
    """!Map Display toolbar
    """
    def __init__(self, parent, mapcontent):
        """!Map Display constructor

        @param parent reference to MapFrame
        @param mapcontent reference to render.Map (registred by MapFrame)
        """
        self.mapcontent = mapcontent # render.Map
        toolbars.AbstractToolbar.__init__(self, parent = parent) # MapFrame
        
        self.InitToolbar(self.ToolbarData())
        
        # optional tools

        
        self.action = { 'id' : self.pointer }
        self.defaultAction = { 'id' : self.pointer,
                               'bind' : self.parent.OnPointer }
        
        self.OnTool(None)
        
        self.EnableTool(self.zoomback, False)
        
        self.FixSize(width = 90)
        
    def ToolbarData(self):
        """!Toolbar data"""

        self.pointer = wx.NewId()

        self.pan = wx.NewId()
        self.zoomin = wx.NewId()
        self.zoomout = wx.NewId()
        self.zoomback = wx.NewId()
        self.zoommenu = wx.NewId()
        self.zoomextent = wx.NewId()

        
        # tool, label, bitmap, kind, shortHelp, longHelp, handler
        return (

            (self.pointer, "pointer", Icons["pointer"].GetBitmap(),
             wx.ITEM_CHECK, Icons["pointer"].GetLabel(), Icons["pointer"].GetDesc(),
             self.parent.OnPointer),

            (self.pan, "pan", Icons["pan"].GetBitmap(),
             wx.ITEM_CHECK, Icons["pan"].GetLabel(), Icons["pan"].GetDesc(),
             self.parent.OnPan),
            (self.zoomin, "zoom_in", Icons["zoom_in"].GetBitmap(),
             wx.ITEM_CHECK, Icons["zoom_in"].GetLabel(), Icons["zoom_in"].GetDesc(),
             self.parent.OnZoomIn),
            (self.zoomout, "zoom_out", Icons["zoom_out"].GetBitmap(),
             wx.ITEM_CHECK, Icons["zoom_out"].GetLabel(), Icons["zoom_out"].GetDesc(),
             self.parent.OnZoomOut),
            (self.zoomextent, "zoom_extent", Icons["zoom_extent"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_extent"].GetLabel(), Icons["zoom_extent"].GetDesc(),
             self.parent.OnZoomToMap),
            (self.zoomback, "zoom_back", Icons["zoom_back"].GetBitmap(),
             wx.ITEM_NORMAL, Icons["zoom_back"].GetLabel(), Icons["zoom_back"].GetDesc(),
             self.parent.OnZoomBack)        
            )
    

class PathApp(wx.App):
    """
    MapApp class
    """

    def OnInit(self):
        if __name__ == "__main__":
            Map = render.Map() 
        else:
            Map = None
        self.mapname = 'roads@PERMANENT'
        self.cmd= ['d.vect', str("map=" + self.mapname)]
        Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)

        self.frame = NetworkPath(parent=None, id=wx.ID_ANY, Map=Map,
                               size=globalvar.MAP_WINDOW_SIZE)

        self.frame.Show()
        return 1

# end of class

if __name__ == "__main__":


    gm_map = PathApp(0)

    gm_map.MainLoop()


    sys.exit(0)
