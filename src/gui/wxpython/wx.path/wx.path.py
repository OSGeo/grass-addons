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
import time

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

grassversion = os.getenv("GRASS_VERSION")
if grassversion.rfind("6.4") != 0:
    from mapdisp_window import BufferedWindow
    from mapdisp_window import MapWindow as MapWindow
else:
    from mapdisp import BufferedWindow
    from mapdisp import MapWindow as MapWindow


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
#        self.statusbar.Bind(wx.EVT_TEXT_ENTER, self.OnGoTo, self.statusbarWin['goto'])

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

        if grassversion.rfind("6.4") != 0:
            self.Bind(wx.EVT_MOTION, self.MapWindow.OnMotion)
       # else:
#            self.Bind(wx.EVT_MOTION,       self.MapWindow.OnMotion2)   
       # self.MapWindow.Bind(wx.EVT_MOTION, self.MapWindow.OnMotion)
        self.MapWindow.SetCursor(self.cursors["default"])
        # used by Nviz (3D display mode)
        self.MapWindow3D = None 

        self.MapWindow.Bind(wx.EVT_LEFT_DCLICK,self.OnButtonDClick)

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
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
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
        wx.MessageBox("Currently Works for spearfish data. \nIf you need this to work with other grass data.\
please let me know. I will modify the code and update svn")
        self.mapname = 'roads@' + grass.gisenv()['MAPSET']
        self.cmd= ['d.vect', str("map=" + self.mapname),'width=1']
        self.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
        self.MapWindow.UpdateMap(render=True)  

        self.dialogs = {}
        self.dialogs['attributes'] = None
        self.dialogs['category'] = None
        self.dialogs['barscale'] = None
        self.dialogs['legend'] = None

        self.decorationDialog = None # decoration/overlays

        #self.Maximize()
        self.coords = []
        self.points = []

    def OnMotion2(self, event):
        """
        Mouse moved
        Track mouse motion and update status bar
        """
        # update statusbar if required
        if self.toggleStatus.GetSelection() == 0: # Coordinates
            e, n = self.MapWindow.Pixel2Cell(event.GetPositionTuple())
            if self.toolbars['vdigit'] and \
                    self.toolbars['vdigit'].GetAction() == 'addLine' and \
                    self.toolbars['vdigit'].GetAction('type') in ('line', 'boundary') and \
                    len(self.MapWindow.polycoords) > 0:
                # for linear feature show segment and total length
                distance_seg = self.MapWindow.Distance(self.MapWindow.polycoords[-1],
                                                       (e, n), screen=False)[0]
                distance_tot = distance_seg
                for idx in range(1, len(self.MapWindow.polycoords)):
                    distance_tot += self.MapWindow.Distance(self.MapWindow.polycoords[idx-1],
                                                            self.MapWindow.polycoords[idx],
                                                            screen=False )[0]
                self.statusbar.SetStatusText("%.2f, %.2f (seg: %.2f; tot: %.2f)" % \
                                                 (e, n, distance_seg, distance_tot), 0)
            else:
                if self.Map.projinfo['proj'] == 'll':
                    self.statusbar.SetStatusText("%s" % utils.Deg2DMS(e, n), 0)
                else:
                    self.statusbar.SetStatusText("%.2f, %.2f" % (e, n), 0)

            event.Skip()


    def StatusbarReposition(self):
        """Reposition checkbox in statusbar"""
        # reposition checkbox
        widgets = 0

    def StatusbarUpdate(self):
        """Update statusbar content"""

        widgets = 0

    def OnButtonDClick(self,event): 

        try:
            e, n = self.MapWindow.Pixel2Cell(event.GetPositionTuple())
            print e,n
        except AttributeError:
            return

        self.counter = self.counter + 1
        coord =("%f %f" %  ( e, n))
        self.coords.append(coord)

        if self.counter == 2:
            self.points.append("1 ")
            for p in self.coords:
                self.points.append(p)
            f =open("tmp",'w')
            for p in self.points:
                f.write("%s " % p)
            f.close()



            command=["v.net.path", 'input=roads', 'output=path','file=tmp','--overwrite']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()


            self.mapname = 'path@'+ grass.gisenv()['MAPSET']
            self.cmd= ['d.vect', str("map=" + self.mapname),'col=red','width=2']
            self.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
            self.MapWindow.UpdateMap(render=True)
            self.counter =0
            self.coords=[]
            self.points=[]



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
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        ### self.Bind(wx.EVT_MOTION,       self.MouseActions)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.MouseActions)

        if grassversion.rfind("6.4") != 0:
            self.Bind(wx.EVT_MOTION, self.OnMotion)
        #else:
            #self.Bind(wx.EVT_MOTION,       self.MapWindow.OnMotion2)        




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
        if grassversion.rfind("6.4") != 0:
            self.DefinePseudoDC()
        else:
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
        if grass.find_file(name = 'MASK', element = 'cell')['name']:
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
