"""
@package nviz.py

@brief 2.5/3D visialization mode for Map Display Window

List of classes:
 - GLWindow
 - NvizToolWindow
 - ViewPositionWindow
 - RasterPropertiesDialog

(C) 2008 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Martin Landa <landa.martin gmail.com> (Google SoC 2008)
"""

import os
import sys
import time

from threading import Thread

import wx
try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False

try:
    from OpenGL.GL import *
    from OpenGL.GLUT import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False

import globalvar
import gcmd
from debug import Debug as Debug
from mapdisp import MapWindow as MapWindow
#try:
nvizPath = os.path.join(globalvar.ETCWXDIR, "nviz")
sys.path.append(nvizPath)
import grass6_wxnviz as wxnviz
haveNviz = True
#except ImportError:
#    haveNviz = False

class GLWindow(MapWindow, glcanvas.GLCanvas):
    """OpenGL canvas for Map Display Window"""
    def __init__(self, parent, id,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE,
                 Map=None, tree=None, gismgr=None):

        self.parent = parent # MapFrame
        self.Map = Map
        self.tree = tree
        self.gismgr = gismgr
        
        glcanvas.GLCanvas.__init__(self, parent, id)
        MapWindow.__init__(self, parent, id, pos, size, style,
                           Map, tree, gismgr)


        self.parent = parent # MapFrame

        # attribList=[wx.WX_GL_RGBA, wx.GLX_RED_SIZE, 1,
        #             wx.GLX_GREEN_SIZE, 1,
        #             wx.GLX_BLUE_SIZE, 1,
        #             wx.GLX_DEPTH_SIZE, 1,
        #             None])

        self.init = False

        #
        # create nviz instance
        #
        self.nvizClass = wxnviz.Nviz()

        #
        # set current display
        #
        self.nvizClass.SetDisplay(self)

        #
        # set default lighting model
        #
        self.nvizClass.SetLightsDefault()

        #
        # initialize mouse position
        #
        self.lastX = self.x = 30
        self.lastY = self.y = 30

        #
        # default values
        #
        self.view = { 'persp' : { 'value' : 40,
                                  'min' : 0,
                                  'max' : 100,
                                  'step' : 5,
                                  'update' : False,
                                  },
                      'pos' : { 'value' : (0.85, 0.85),
                                'update' : False,
                                },
                      'height' : { 'value': -1,
                                   'min' : -2245, # TODO: determine min/max height
                                   'max' : 3695, 
                                   'step' : 100,
                                   'update' : False,
                                   },
                      'twist' : { 'value' : 0,
                                  'min' : -180,
                                  'max' : 180,
                                  'step' : 5,
                                  'update' : False,
                                  },
                      'z-exag' : { 'value': 1.0,
                                   'min' : 0.0,
                                   'max' : 10,
                                   'step' : 1,
                                   'update' : False
                                   },
                      }

        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseAction)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseAction)

    def OnEraseBackground(self, event):
        pass # do nothing, to avoid flashing on MSW

    def OnSize(self, event):
        self.size = self.parent.GetClientSize()
        if self.GetContext():
            Debug.msg(3, "GLCanvas.OnPaint(): w=%d, h=%d" % \
                      (self.size.width, self.size.height))
            self.SetCurrent()
            self.nvizClass.ResizeWindow(self.size.width,
                                        self.size.height)
        
        event.Skip()

    def OnPaint(self, event):
        Debug.msg(3, "GLCanvas.OnPaint()")

        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.nvizClass.InitView()
            self.LoadDataLayers()
            self.view['height']['value'] = self.nvizClass.SetViewDefault()
            if hasattr(self.parent, "nvizToolWin"):
                self.parent.nvizToolWin.UpdateSettings()
            self.init = True
        self.UpdateMap()

    def OnMouseAction(self, event):
        # change position
        if event.Dragging() and event.LeftIsDown():
            self.lastX = self.lastY = self.x = self.y
            self.x, self.y = event.GetPosition()
            self.Refresh(False)

        # change perspective with mouse wheel
        wheel = event.GetWheelRotation()

        if wheel != 0:
            current  = event.GetPositionTuple()[:]
            Debug.msg (5, "GLWindow.OnMouseMotion(): wheel=%d" % wheel)
            if wheel > 0:
                value = -1 * self.view['persp']['step']
            else:
                value = self.view['persp']['step']
            self.view['persp']['value'] += value
            if self.view['persp']['value'] < 0:
                self.view['persp']['value'] = 0
            elif self.view['persp']['value'] > 100:
                self.view['persp']['value'] = 100

            if hasattr(self.parent, "nvizToolWin"):
                self.parent.nvizToolWin.UpdateSettings()

            self.nvizClass.SetView(self.view['pos']['value'][0], self.view['pos']['value'][1],
                                   self.view['height']['value'],
                                   self.view['persp']['value'],
                                   self.view['twist']['value'])

            # redraw map
            self.OnPaint(None)

            # update statusbar
            ### self.parent.StatusbarUpdate()

    def OnLeftDown(self, event):
        self.CaptureMouse()
        self.x, self.y = self.lastX, self.lastY = event.GetPosition()
        
    def OnLeftUp(self, event):
        self.ReleaseMouse()

    def UpdateMap(self, render=False):
        """
        Updates the canvas anytime there is a change to the
        underlaying images or to the geometry of the canvas.

        render:
         - None do not render (todo)
         - True render
         - False quick render

        @param render re-render map composition
        """
        start = time.clock()

        self.resize = False

        # if self.size is None:
        #    self.size = self.GetClientSize()
        
        #         w, h = self.size
        #         w = float(max(w, 1.0))
        #         h = float(max(h, 1.0))
        #         d = float(min(w, h))
        #         xScale = d / w
        #         yScale = d / h
        # print w, h, d, xScale, yScale
        # print self.y, self.lastY, self.x, self.lastX
        # print (self.y - self.lastY) * yScale, (self.x - self.lastX) * xScale 
        # print self.x * xScale
        
        #glRotatef((self.y - self.lastY) * yScale, 1.0, 0.0, 0.0);
        #glRotatef((self.x - self.lastX) * xScale, 0.0, 1.0, 0.0);

        if render is not None:
            self.parent.onRenderGauge.Show()
            if self.parent.onRenderGauge.GetRange() > 0:
                self.parent.onRenderGauge.SetValue(1)
                self.parent.onRenderTimer.Start(100)
            self.parent.onRenderCounter = 0

        if self.view['pos']['update'] or \
                self.view['height']['update'] or \
                self.view['persp']['update'] or \
                self.view['twist']['update']:
            self.nvizClass.SetView(self.view['pos']['value'][0], self.view['pos']['value'][1],
                                   self.view['height']['value'],
                                   self.view['persp']['value'],
                                   self.view['twist']['value'])
            for control in ('pos', 'height', 'persp', 'twist'):
                self.view[control]['update'] = False

        if self.view['z-exag']['update']:
            self.nvizClass.SetZExag(self.view['z-exag']['value'])
            self.view['z-exag']['update'] = False

        if render is True:
            self.nvizClass.Draw(False)
        elif render is False:
            self.nvizClass.Draw(True) # quick

        self.SwapBuffers()

        stop = time.clock()

        #
        # hide process bar
        #
        if self.parent.onRenderGauge.GetRange() > 0:
            self.parent.onRenderTimer.Stop()
        self.parent.onRenderGauge.Hide()

        #
        # update statusbar
        #
        ### self.Map.SetRegion()
        # self.parent.StatusbarUpdate()

        Debug.msg(3, "GLWindow.UpdateMap(): render=%s, -> time=%g" % \
                      (render, (stop-start)))

        print '# %.6f' % (stop-start)

    def EraseMap(self):
        """
        Erase the canvas
        """
        self.nvizClass.EraseMap()
        self.SwapBuffers()

    def LoadDataLayers(self):
        """Load raster/vector from current layer tree

        @todo volumes
        """
        for raster in self.Map.GetListOfLayers(l_type='raster', l_active=True):
            self.nvizClass.LoadRaster(str(raster.name), None, None)

    def Reset(self):
        """Reset (unload data)"""
        self.nvizClass.Reset()
        self.init = False

    def ZoomToMap(self, event):
        """
        Set display extents to match selected raster
        or vector map or volume.

        @todo vector, volume
        """
        layer = self.GetSelectedLayer()

        if layer is None:
            return

        Debug.msg (3, "GLWindow.ZoomToMap(): layer=%s, type=%s" % \
                       (layer.name, layer.type))

        self.nvizClass.SetViewportDefault()

    def ResetView(self):
        """Reset to default view"""
        self.view['pos']['value'] = (wxnviz.VIEW_DEFAULT_POS_X,
                                     wxnviz.VIEW_DEFAULT_POS_Y)
        self.view['height']['value'] = self.nvizClass.SetViewDefault()
        self.view['persp']['value'] = wxnviz.VIEW_DEFAULT_PERSP
        self.view['twist']['value'] = wxnviz.VIEW_DEFAULT_TWIST
        self.view['z-exag']['value'] = wxnviz.VIEW_DEFAULT_ZEXAG

        for control in ('pos', 'height', 'persp',
                        'twist', 'z-exag'):
            self.view[control]['update'] = True

class NvizToolWindow(wx.Frame):
    """Experimental window for Nviz tools

    @todo integrate with Map display
    """
    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Nviz tools"),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, mapWindow=None):
        
        self.parent = parent # MapFrame
        self.mapWindow = mapWindow
        self.settings = mapWindow.view # GLWindow.view

        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # dialog body
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.win = {} # window ids

        # notebook
        self.notebook = wx.Notebook(parent=self, id=wx.ID_ANY, style=wx.BK_DEFAULT)

        self.__createViewPage()

        mainSizer.Add(item=self.notebook, proportion=1,
                      flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        
    def __createViewPage(self):
        """Create view settings page"""
        panel = wx.Panel(parent=self.notebook, id=wx.ID_ANY)
        self.notebook.AddPage(page=panel,
                              text=" %s " % _("View"))
        
        pageSizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.GridBagSizer(vgap=3, hgap=3)

        # position
        posSizer = wx.GridBagSizer(vgap=3, hgap=3)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("W")),
                     pos=(1, 0), flag=wx.ALIGN_CENTER)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("N")),
                     pos=(0, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_BOTTOM)
        viewPos = ViewPositionWindow(panel, id=wx.ID_ANY, size=(175, 175),
                                     settings=self.settings, mapwindow=self.mapWindow)
        self.win['pos'] = viewPos.GetId()
        posSizer.Add(item=viewPos,
                     pos=(1, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_CENTER_VERTICAL)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("S")),
                     pos=(2, 1), flag=wx.ALIGN_CENTER | wx.ALIGN_TOP)
        posSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("E")),
                     pos=(1, 2), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=posSizer, pos=(0, 0))
                  
        # perspective
        self.CreateControl(panel, 'persp')
        gridSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Perspective:")),
                      pos=(1, 0), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=self.FindWindowById(self.win['persp']['slider']), pos=(2, 0))
        gridSizer.Add(item=self.FindWindowById(self.win['persp']['spin']), pos=(3, 0),
                      flag=wx.ALIGN_CENTER)        

        # twist
        self.CreateControl(panel, 'twist')
        gridSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Twist:")),
                      pos=(1, 1), flag=wx.ALIGN_CENTER)
        gridSizer.Add(item=self.FindWindowById(self.win['twist']['slider']), pos=(2, 1))
        gridSizer.Add(item=self.FindWindowById(self.win['twist']['spin']), pos=(3, 1),
                      flag=wx.ALIGN_CENTER)        

        # height + z-exag
        self.CreateControl(panel, 'height', sliderHor=False)
        self.CreateControl(panel, 'z-exag', sliderHor=False)
        heightSizer = wx.GridBagSizer(vgap=3, hgap=3)
        heightSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Height:")),
                      pos=(0, 0), flag=wx.ALIGN_LEFT, span=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['height']['slider']),
                        flag=wx.ALIGN_RIGHT, pos=(1, 0))
        heightSizer.Add(item=self.FindWindowById(self.win['height']['spin']),
                        flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP |
                        wx.BOTTOM | wx.RIGHT, pos=(1, 1))
        heightSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY, label=_("Z-exag:")),
                      pos=(0, 2), flag=wx.ALIGN_LEFT, span=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['z-exag']['slider']),
                        flag=wx.ALIGN_RIGHT, pos=(1, 2))
        heightSizer.Add(item=self.FindWindowById(self.win['z-exag']['spin']),
                        flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_LEFT | wx.TOP |
                        wx.BOTTOM | wx.RIGHT, pos=(1, 3))

        gridSizer.Add(item=heightSizer, pos=(0, 1), flag=wx.ALIGN_RIGHT)

        # view setup + reset
        viewSizer = wx.BoxSizer(wx.HORIZONTAL)

        viewSizer.Add(item=wx.StaticText(panel, id=wx.ID_ANY,
                                         label=_("Look at:")),
                      flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=5)
        
        viewType = wx.Choice (parent=panel, id=wx.ID_ANY, size=(125, -1),
                              choices = [_("top"),
                                         _("north"),
                                         _("south"),
                                         _("east"),
                                         _("west"),
                                         _("north-west"),
                                         _("north-east"),
                                         _("south-east"),
                                         _("south-west")])
        viewType.SetSelection(0)
        viewType.Bind(wx.EVT_CHOICE, self.OnLookAt)
        # self.win['lookAt'] = viewType.GetId()
        viewSizer.Add(item=viewType, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                      border=5)

        reset = wx.Button(panel, id=wx.ID_ANY, label=_("Reset"))
        reset.SetToolTipString(_("Reset to default view"))
        # self.win['reset'] = reset.GetId()
        reset.Bind(wx.EVT_BUTTON, self.OnResetView)

        viewSizer.Add(item=reset, proportion=1,
                      flag=wx.EXPAND | wx.ALL | wx.ALIGN_RIGHT,
                      border=5)

        gridSizer.AddGrowableCol(3)
        gridSizer.Add(item=viewSizer, pos=(4, 0), span=(1, 2),
                      flag=wx.EXPAND)

        # body
        pageSizer.Add(item=gridSizer, proportion=1,
                      flag=wx.EXPAND | wx.ALL,
                      border=5)

        panel.SetSizer(pageSizer)

    def CreateControl(self, parent, name, sliderHor=True):
        """Add control (Slider + SpinCtrl)"""
        self.win[name] = {}
        if sliderHor:
            style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | \
                wx.SL_BOTTOM
            size = (200, -1)
        else:
            style = wx.SL_VERTICAL | wx.SL_AUTOTICKS | \
                wx.SL_BOTTOM | wx.SL_INVERSE
            size = (-1, 200)
        slider = wx.Slider(parent=parent, id=wx.ID_ANY,
                           value=self.settings[name]['value'],
                           minValue=self.settings[name]['min'],
                           maxValue=self.settings[name]['max'],
                           style=style,
                           size=size)

        slider.Bind(wx.EVT_SCROLL, self.OnChangeValue)
        self.win[name]['slider'] = slider.GetId()

        spin = wx.SpinCtrl(parent=parent, id=wx.ID_ANY, size=(65, -1),
                           initial=self.settings[name]['value'],
                           min=self.settings[name]['min'],
                           max=self.settings[name]['max'])
        #         spin = wx.SpinButton(parent=parent, id=wx.ID_ANY)
        #         spin.SetValue (self.settings[name]['value'])
        #         spin.SetRange(self.settings[name]['min'],
        #                      self.settings[name]['max'])

        spin.Bind(wx.EVT_SPINCTRL, self.OnChangeValue)
        self.win[name]['spin'] = spin.GetId()


    def UpdateSettings(self):
        """Update dialog settings"""
        for control in ('height',
                        'persp',
                        'twist',
                        'z-exag'):
            for win in self.win[control].itervalues():
                self.FindWindowById(win).SetValue(self.settings[control]['value'])

        self.FindWindowById(self.win['pos']).Draw()
        self.FindWindowById(self.win['pos']).Refresh(False)
        
        self.Refresh(False)
        
    def OnChangeValue(self, event):
        # find control
        winName = ''
        for name in self.win.iterkeys():
            if type(self.win[name]) is type({}):
                for win in self.win[name].itervalues():
                    if win == event.GetId():
                        winName = name
                        break
            else:
                if self.win[name] == event.GetId():
                    winName = name
                    break

        if winName == '':
            return

        self.settings[winName]['value'] = event.GetInt()
        for win in self.win[winName].itervalues():
            self.FindWindowById(win).SetValue(self.settings[winName]['value'])


        self.settings[winName]['update'] = True

        self.mapWindow.Refresh(False)

    def OnResetView(self, event):
        """Reset to default view"""
        self.mapWindow.ResetView()
        self.UpdateSettings()
        self.mapWindow.Refresh(False)

    def OnLookAt(self, event):
        """Look at"""
        sel = event.GetSelection()
        if sel == 0: # top
            self.settings['pos']['value'] = (0.5, 0.5)
        elif sel == 1: # north
            self.settings['pos']['value'] = (0.5, 0.0)
        elif sel == 2: # south
            self.settings['pos']['value'] = (0.5, 1.0)
        elif sel == 3: # east
            self.settings['pos']['value'] = (1.0, 0.5)
        elif sel == 4: # west
            self.settings['pos']['value'] = (0.0, 0.5)
        elif sel == 5: # north-west
            self.settings['pos']['value'] = (0.0, 0.0)
        elif sel == 6: # north-east
            self.settings['pos']['value'] = (1.0, 0.0)
        elif sel == 7: # south-east
            self.settings['pos']['value'] = (1.0, 1.0)
        elif sel == 8: # south-west
            self.settings['pos']['value'] = (0.0, 1.0)

        self.settings['pos']['update'] = True
        self.UpdateSettings()
        self.mapWindow.Refresh(False)

class ViewPositionWindow(wx.Window):
    """Position control window (for NvizToolWindow)"""
    def __init__(self, parent, id, mapwindow,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize, settings={}):
        self.settings = settings
        self.mapWindow = mapwindow

        wx.Window.__init__(self, parent, id, pos, size)

        self.SetBackgroundColour("WHITE")

        self.pdc = wx.PseudoDC()

        self.pdc.SetBrush(wx.Brush(colour='dark green', style=wx.SOLID))
        self.pdc.SetPen(wx.Pen(colour='dark green', width=2, style=wx.SOLID))

        self.Draw()

        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

    def Draw(self, pos=None):
        w, h = self.GetClientSize()

        if pos is None:
            x, y = self.settings['pos']['value']
            x = x * w
            y = y * h
        else:
            x, y = pos

        self.pdc.Clear()
        self.pdc.BeginDrawing()
        self.pdc.DrawLine(w / 2, h / 2, x, y)
        self.pdc.DrawCircle(x, y, 5)
        self.pdc.EndDrawing()

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self)
        dc.SetBackground(wx.Brush("White"))
        dc.Clear()

        self.PrepareDC(dc)
        self.pdc.DrawToDC(dc)

    def OnMouse(self, event):
        if event.LeftIsDown():
            x, y = event.GetPosition()
            self.Draw(pos=(x, y))
            self.Refresh(False)
            w, h = self.GetClientSize()
            x = float(x) / w
            y = float(y) / h
            self.settings['pos']['value'] = (x, y)
            self.settings['pos']['update'] = True

            self.mapWindow.Refresh(eraseBackground=False)
            # self.mapWindow.UpdateMap()
            # self.mapWindow.OnPaint(None)

class RasterPropertiesDialog(wx.Dialog):
    """Nviz raster properties

    @todo integrate into Nviz tools window or d.rast dialog ?
    """
    def __init__(self, parent, map,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):

        self.map = map

        wx.Dialog.__init__(self, parent=parent, id=wx.ID_ANY,
                           style=style, pos=pos)
        self.SetTitle(_("Properties of raster map <%s>") % self.map)

        self.panel = wx.Panel(self, id=wx.ID_ANY)

        bodySizer = wx.BoxSizer(wx.VERTICAL)

        #
        # surface attributes box
        #
        bodySizer.Add(item=self.__surfaceAttributes(), proportion=1,
                      flag=wx.ALL | wx.EXPAND, border=3)

        #
        # button (see menuform)
        #
        btnsizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        # cancel
        btn_cancel = wx.Button(parent=self.panel, id=wx.ID_CANCEL)
        btn_cancel.SetToolTipString(_("Cancel the command settings and ignore changes"))
        btnsizer.Add(item=btn_cancel, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        btn_apply = wx.Button(parent=self.panel, id=wx.ID_APPLY)
        btn_ok = wx.Button(parent=self.panel, id=wx.ID_OK)
        btn_ok.SetDefault()
        
        btnsizer.Add(item=btn_apply, proportion=0,
                     flag=wx.ALL | wx.ALIGN_CENTER,
                     border=10)
        btnsizer.Add(item=btn_ok, proportion=0,
                     flag=wx.ALL | wx.ALIGN_CENTER,
                     border=10)
        
        btn_apply.Bind(wx.EVT_BUTTON, self.OnApply)
        btn_ok.Bind(wx.EVT_BUTTON, self.OnOK)

        bodySizer.Add(item=btnsizer, proportion=0, flag=wx.ALIGN_CENTER)

        self.panel.SetSizer(bodySizer)
        bodySizer.Fit(self.panel)
        
    def __surfaceAttributes(self):
        """Sourface attributes section"""
        box = wx.StaticBox (parent=self.panel, id=wx.ID_ANY,
                            label=" %s " % (_("Surface attributes")))
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        gridSizer = wx.GridBagSizer(vgap=3, hgap=3)

        # labels
        col = 0
        for type in (_("Attribute"),
                     _("Use"),
                     _("Map"),
                     _("Constant")):
            gridSizer.Add(item=wx.StaticText(parent=self.panel, id=wx.ID_ANY,
                                             label=type),
                          pos=(0, col))
            col += 1

        # type 
        row = 1
        for attr in (_("Topography"),
                     _("Color"),
                     _("Mask"),
                     _("Transparency"),
                     _("Shininess"),
                     _("Emission")):
            gridSizer.Add(item=wx.StaticText(parent=self.panel, id=wx.ID_ANY,
                                             label=attr + ':'),
                          pos=(row, 0), flag=wx.ALIGN_CENTER_VERTICAL)
            use = wx.Choice (parent=self.panel, id=wx.ID_ANY, size=(100, -1),
                             choices = [_("map"),
                                        _("constant")])
            gridSizer.Add(item=use, flag=wx.ALIGN_CENTER_VERTICAL,
                          pos=(row, 1))


            row += 1

        sizer.Add(item=gridSizer, proportion=1,
                  flag=wx.ALL | wx.EXPAND, border=3)

        return sizer

    def OnCancel(self, event):
        """Cancel button pressed"""
        self.Close()

    def OnOK(self, event):
        """OK button pressed
        
        Update map and close dialog
        """
        pass
    
    def OnApply(self, event):
        """Apply button pressed
        
        Update map (don't close dialog)
        """
        pass
