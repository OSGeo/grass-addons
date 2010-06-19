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
from toolbars import MapToolbar
from preferences import globalSettings as UserSettings
from icon  import Icons
from mapdisp_command import Command
from mapdisp_window import BufferedWindow
from mapdisp import MapFrame
from debug import Debug
import images
import gcmd
from grass.script import core as grass

imagepath = images.__path__[0]
sys.path.append(imagepath)


class NetworkPath(MapFrame):

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
        
        #
        # set the size & system icon
        #
        self.SetClientSize(self.GetSize())
        self.iconsize = (16, 16)
        self.SetName("MapWindow")

        self.counter = 0    
        self.points =[]

        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass_map.ico'), wx.BITMAP_TYPE_ICO))

        #
        # Fancy gui
        #
        # self._mgr = auimgr
        self._mgr = wx.aui.AuiManager(self)

        self._layerManager = None
        self.georectifying =None

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
        self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnGoTo, self.statusbarWin['goto'])

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
        self.MapWindow2D = BufferedWindow(self, id=wx.ID_ANY,Map=self.Map)
        # default is 2D display mode
        self.MapWindow = self.MapWindow2D
        self.MapWindow.Bind(wx.EVT_MOTION, self.OnMotion)
        self.MapWindow.SetCursor(self.cursors["default"])
        self.MapWindow.Bind(wx.EVT_LEFT_DCLICK,self.OnButtonDClick)
        # used by Nviz (3D display mode)
        self.MapWindow3D = None 

        #
        # initialize region values
        #
        self.__InitDisplay() 

        #
        # Bind various events
        #
        #self.Bind(wx.EVT_ACTIVATE, self.OnFocus)
        self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)
       # self.Bind(render.EVT_UPDATE_PRGBAR, self.OnUpdateProgress)
        
        #
        # Update fancy gui style
        #
        self._mgr.AddPane(self.MapWindow, wx.aui.AuiPaneInfo().CentrePane().
                          Dockable(False).BestSize((-1,-1)).
                          CloseButton(False).DestroyOnClose(True).
                          Layer(0))
        self._mgr.Update()


        
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

        self.Maximize()

    def OnButtonDClick(self,event): 


        precision = int(UserSettings.Get(group = 'projection', key = 'format',
                                             subkey = 'precision'))
        try:
            e, n = self.MapWindow.Pixel2Cell(event.GetPositionTuple())
        except AttributeError:
            return
        
        self.counter = self.counter + 1
        point =("%.*f|%.*f" %  (precision, e, precision, n))
        self.points.append(point + '|point')
        if self.counter == 2:
            f =open("tmp1",'w')
            for p in self.points:
                f.write("%s\n" % p)
            f.close()

            f =open("tmp2",'w')
            f.write("%d %d %d\n" %(1,1,2) )
            f.close()
            
            #print self.points        

            command =["g.remove",'vect=vnet_out,startend,tmp_vnet_path']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command =["v.in.ascii",'input=tmp1','output=startend']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command=["v.net", "input=myroads",'points=startend', 'out=vnet_out', 'op=connect', 'thresh=200']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command=["v.net.path", 'vnet_out','afcol=forward', 'abcol=backward', 'out=tmp_vnet_path','file=tmp2']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            self.mapname = 'tmp_vnet_path@' + grass.gisenv()['MAPSET']
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
