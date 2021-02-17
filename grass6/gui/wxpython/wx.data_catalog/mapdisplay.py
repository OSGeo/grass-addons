"""!
@package mapdisp.py

@brief GIS map display canvas, with toolbar for various display
management functions, and additional toolbars (vector digitizer, 3d
view).

Can be used either from Layer Manager or as p.mon backend.

Classes:
- MapFrame
- MapApp

Usage:
python mapdisp.py monitor-identifier /path/to/command/file

(C) 2006-2009 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton
@author Jachym Cepicky
@author Martin Landa <landa.martin gmail.com>
@author Mohammed Rashad K.M <rashadkm at gmail dot com> (only modified for DataCatalog)
"""

import os
import sys
import glob
import math
import tempfile
import copy
import time
import traceback


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
import menuform
import gselect
import disp_print
import gcmd

import histogram
import profile
import globalvar
import utils
import gdialogs
import goutput
grassversion = os.getenv("GRASS_VERSION")
if grassversion.rfind("6.4") != 0:
    import units
from grass.script import core as grass
from debug import Debug
from preferences import globalSettings as UserSettings
import dbm

if grassversion.rfind("6.4") != 0:
    import dbm_dialogs
if grassversion.rfind("6.4") != 0:
    from units import ConvertValue as UnitsConvertValue
from vdigit import GV_LINES as VDigit_Lines_Type
from vdigit import VDigitCategoryDialog
from vdigit import VDigitZBulkDialog
from vdigit import VDigitDuplicatesDialog
from vdigit import PseudoDC as VDigitPseudoDC

from tcp4ossim import zoomto 

from LayerTree import LayerTree

from threading import Thread



import images
imagepath = images.__path__[0]
sys.path.append(imagepath)

###
### global variables
###
# for standalone app
cmdfilename = None
if grassversion.rfind("6.4") != 0:
    from mapdisp_window import BufferedWindow
else:
    from mapdisp import BufferedWindow


from mapdisp_window import MapWindow
from mapdisp import MapFrame

class MapFrame(wx.Panel,MapFrame):
    """
    Main frame for map display window. Drawing takes place in child double buffered
    drawing window.
    """

    def __init__(self, parent=None, id=wx.ID_ANY, title=_("GRASS GIS - Map display"),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, toolbars=["map"],
                 tree=None, notebook=None, gismgr=None, page=None,
                 Map=None, auimgr=None,frame=None,flag=False):
        """
        Main map display window with toolbars, statusbar and
        DrawWindow

        @param toolbars array of activated toolbars, e.g. ['map', 'digit']
        @param tree reference to layer tree
        @param notebook control book ID in Layer Manager
        @param mgr Layer Manager
        @param page notebook page with layer tree
        @param Map instance of render.Map
        """
        self.gismanager = frame   # Layer Manager object
        self._layerManager = gismgr
        self.Map        = Map       # instance of render.Map
        self.tree       = tree      # Layer Manager layer tree object
        self.page       = page      # Notebook page holding the layer tree
        self.layerbook  = notebook  # Layer Manager layer tree notebook
        self.parent     = parent
        self.frame = frame
        self.statusFlag = flag
        self.statusbar = None


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

        #wx.Frame.__init__(self, parent, id, title, pos, size, style)


        wx.Panel.__init__(self, parent, id, pos, size, style)
        self.SetName("MapWindow")


        self._mgr = wx.aui.AuiManager(self)
        self._layerManager = self.frame


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
        if self.statusFlag:
            self.statusbar = self.frame.CreateStatusBar(number=4, style=0)
            self.statusbar.SetStatusWidths([-5, -2, -1, -1])
        else:
            self.statusbar = self.frame.GetStatusBar()
            self.statusbar.SetStatusWidths([-5, -2, -1, -1])

        if grassversion.rfind("6.4") == 0:
            self.autoRender = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                          label=_("Render"))
            self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleRender, self.autoRender)
            self.autoRender.SetValue(UserSettings.Get(group='display', key='autoRendering', subkey='enabled'))
            self.autoRender.SetToolTip(wx.ToolTip (_("Enable/disable auto-rendering")))

            self.maskInfo = wx.StaticText(parent = self.statusbar, id = wx.ID_ANY,
                                                      label = '')
            self.maskInfo.SetForegroundColour(wx.Colour(255, 0, 0))

            self.toggleStatus = wx.Choice(self.statusbar, wx.ID_ANY,
                                      choices = globalvar.MAP_DISPLAY_STATUSBAR_MODE)
            self.toggleStatus.SetSelection(UserSettings.Get(group='display', key='statusbarMode', subkey='selection'))
            self.statusbar.Bind(wx.EVT_CHOICE, self.OnToggleStatus, self.toggleStatus)

            self.onRenderGauge = wx.Gauge(parent=self.statusbar, id=wx.ID_ANY,
                                          range=0, style=wx.GA_HORIZONTAL)
            self.onRenderGauge.Hide()

            self.mapScale = wx.TextCtrl(parent=self.statusbar, id=wx.ID_ANY,
                                        value="", style=wx.TE_PROCESS_ENTER,
                                        size=(150, -1))
            self.mapScale.Hide()
            self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnChangeMapScale, self.mapScale)

            self.compResolution = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                             label=_("Constrain display resolution to computational settings"))
            self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleResolution, self.compResolution)
            self.compResolution.SetValue(UserSettings.Get(group='display', key='compResolution', subkey='enabled'))
            self.compResolution.Hide()
            self.compResolution.SetToolTip(wx.ToolTip (_("Constrain display resolution "
                                                     "to computational region settings. "
                                                     "Default value for new map displays can "
                                                     "be set up in 'User GUI settings' dialog.")))


            self.showRegion = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                      label=_("Show computational extent"))
            self.showRegion.SetValue(False)
            self.showRegion.Hide()
            self.showRegion.SetToolTip(wx.ToolTip (_("Show/hide computational "
                                                 "region extent (set with g.region). "
                                                 "Display region drawn as a blue box inside the "
                                                 "computational region, "
                                                 "computational region inside a display region "
                                                 "as a red box).")))


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
        self.statusbarWin['mapscale'] = wx.TextCtrl(parent=self.statusbar, id=wx.ID_ANY,
                                                    value="", style=wx.TE_PROCESS_ENTER,
                                                    size=(150, -1))
        self.statusbarWin['mapscale'].Hide()
        self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnChangeMapScale, self.statusbarWin['mapscale'])

        # go to
        self.statusbarWin['goto'] = wx.TextCtrl(parent=self.statusbar, id=wx.ID_ANY,
                                                value="", style=wx.TE_PROCESS_ENTER,
                                                size=(300, -1))
        self.statusbarWin['goto'].Hide()
        if grassversion.rfind("6.4") != 0:
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

        self.maskInfo = wx.StaticText(parent = self.statusbar, id = wx.ID_ANY,
                                                  label = '')
        self.maskInfo.SetForegroundColour(wx.Colour(255, 0, 0))

        #
        # Init map display (buffered DC & set default cursor)
        #

        self.gisrc  = self.read_gisrc()
        self.viewInfo = True        #to display v/r.info on mapdisplay
        self.gisdbase = self.gisrc['GISDBASE'] 

        parent1 = self.GetParent()

        frame = parent1.GetParent()

        self.lmgr= frame



        self.maptree = LayerTree(self, id=wx.ID_ANY, pos=wx.DefaultPosition,
                                                      size=wx.DefaultSize, style=wx.TR_HAS_BUTTONS
                                                      |wx.TR_LINES_AT_ROOT|wx.TR_HIDE_ROOT,
                                                      gisdbase=self.gisdbase,Map = self.Map,lmgr=self.gismanager,frame=frame,idx=0,
                                                      notebook=self.layerbook,auimgr=None,showMapDisplay=True)



        self.tree=self.maptree
        if grassversion.rfind("6.4") == 0:
            self.MapWindow2D = BufferedWindow(self, id=wx.ID_ANY,Map=self.Map, tree=self.tree, gismgr=self.gismanager)
        else:
            self.MapWindow2D = BufferedWindow(self, id=wx.ID_ANY,   Map=self.Map, tree=self.tree, lmgr=self._layerManager)

        self.tree.MapWindow = self.MapWindow2D
        # default is 2D display mode
        self.MapWindow = self.MapWindow2D
#        self.MapWindow.Bind(wx.EVT_MOTION, MapWindow.OnMotion)
        #self.MapWindow.Bind(wx.EVT_LEFT_DOWN, self.OnClick) 
        self.MapWindow.SetCursor(self.cursors["default"])
        # used by Nviz (3D display mode)
        self.MapWindow3D = None 

        #
        # initialize region values
        #
        self.__InitDisplay() 

        #
        # Bind various events
        #
        self.Bind(wx.EVT_ACTIVATE, self.OnFocus)
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
        self.printopt = disp_print.PrintOptions(self, self.MapWindow)

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

        pos = wx.Point(700,10)



        self.onRenderGauge = wx.Gauge(parent=self.statusbar, id=wx.ID_ANY,
                                      range=0, style=wx.GA_HORIZONTAL)

        self.compResolution = wx.CheckBox(parent=self.statusbar, id=wx.ID_ANY,
                                         label=_("Constrain display resolution to computational settings"))
        self.statusbar.Bind(wx.EVT_CHECKBOX, self.OnToggleResolution, self.compResolution)
        self.compResolution.SetValue(UserSettings.Get(group='display', key='compResolution', subkey='enabled'))
        self.compResolution.Hide()
        self.compResolution.SetToolTip(wx.ToolTip (_("Constrain display resolution "
                                                     "to computational region settings. "
                                                     "Default value for new map displays can "
                                                     "be set up in 'User GUI settings' dialog.")))




        self.p = wx.Panel(self)
        #hb = wx.BoxSizer(wx.HORIZONTAL)

        self.p.Bind(wx.EVT_PAINT,self.onPaint)


        self.p.Bind(wx.EVT_LEFT_DOWN,self.OnButtonDClick)


        self.p.Bind(wx.EVT_MOTION, self.move)
        self.moveFlag = False

        self._mgr.AddPane(self.p, wx.aui.AuiPaneInfo().Right().
                                        Dockable(True).BestSize((400,300)).
                                        CloseButton(True).DestroyOnClose(True).
                                        Layer(0).Caption("KeyMap"))




        self._mgr.AddPane(self.maptree, wx.aui.AuiPaneInfo().Left().
                                        Dockable(False).BestSize((400,300)).
                                        CloseButton(False).DestroyOnClose(True).
                                        Layer(0).Caption("Map Tree"))


        self.previous = [0,0]
        self.current  = [0,0]


        self._mgr.Update()

        #r.rightSizer.Add(self.maptree)

    def OnButtonDClick(self,event): 

        try:
            e, n = event.GetPositionTuple()
            #print e,n

        except AttributeError:
            return

        self.paintwindow((e-50),(n-37),100,75,"/tmp/keymap.ppm")
        begin = e,n
        if self.moveFlag == False:
            self.moveFlag=True
            self.current = event.GetPositionTuple()[:]


        else:
            self.moveFlag = False
            self.previous = event.GetPositionTuple()[:]
            #print self.current
            #print self.previous
            move = (self.current[0] - self.previous[0],
                 self.current[1] - self.previous[1])
            self.MapWindow.DragMap(move)





    def move(self,event):
        #print "here"
        if self.moveFlag == True:
            e,n = event.GetPosition()
            self.paintwindow((e-50),(n-37),100,75,"/tmp/keymap.ppm")



    def onPaint(self,event):
        #print "here"
        if self.MapWindow.mapfile is not None:
            cmd = 'cp ' + self.MapWindow.mapfile + ' '+ '/tmp/keymap.ppm'
            os.system(cmd)
            self.paintwindow(50,50,100,75,"/tmp/keymap.ppm")

    def paintwindow(self,x,y,length,breadth,imageFile):
        #imageFile = "/home/rashad/keymap.png"
        #self.dc = wx.PaintDC(self.p)

        try:
            png = wx.Image(_(imageFile), wx.BITMAP_TYPE_ANY).Scale(210,160,wx.IMAGE_QUALITY_HIGH)
        except:
            pass

        #self.hbitmap = wx.StaticBitmap(self.p, -1, png, (10, 5), (50,50))
        #self.hbitmap.SetCursor(wx.StockCursor(wx.CURSOR_MAGNIFIER))


        self.wxbmp=png.ConvertToBitmap()
        #self.wxbmp.Bind(wx.EVT_MOTION, self.move)
        #self.dc.DrawBitmap(self.wxbmp, 0,0, True)
        #self.dc.SetPen(wx.Pen("RED",style=wx.TRANSPARENT))
        self.dc = wx.PaintDC(self.p)
        self.dc.Clear()
        self.dc.BeginDrawing()
        self.dc.SetPen(wx.Pen("RED"))
        self.dc.SetBrush(wx.Brush("WHITE",style=wx.TRANSPARENT))

        self.dc.DrawBitmap(self.wxbmp, 0,0, True)
        # set x, y, w, h for rectangle
        #self.dc.DrawLine(10,10,30, 30)
        self.dc.EndDrawing()

        #self.dc.SetBrush(wx.Brush("RED"))
        self.dc.DrawRectangle(x, y, length, breadth)

    def read_gisrc(self):
        """
        Read variables gisrc file
        """

        rc = {}

        gisrc = os.getenv("GISRC")

        if gisrc and os.path.isfile(gisrc):
            try:
                f = open(gisrc, "r")
                for line in f.readlines():
                    key, val = line.split(":", 1)
                    rc[key.strip()] = val.strip()
            finally:
                f.close()

        return rc



