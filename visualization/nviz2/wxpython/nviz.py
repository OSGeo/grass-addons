"""
@package nviz.py

@brief 2.5/3D visialization mode for Map Display Window

List of classes:
 - GLWindow

(C) 2008 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Martin Landa <landa.martin gmail.com> (Google SoC 2008)
"""

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

        glcanvas.GLCanvas.__init__(self, parent, id)
        # MapWindow.__init__(self, parent, id, pos, size, style,
        #                   Map, tree, gismgr)


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

        # initialize mouse position
        # self.lastx = self.x = 30
        # self.lasty = self.y = 30

        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        #        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        #        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        #        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

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
            self.nvizClass.LoadRaster("elevation", None, None);
            self.nvizClass.SetViewportDefault()
            self.nvizClass.SetLightsDefault()
            self.init = True
        self.OnDraw()

    def OnDraw(self):
        """Draw data layers"""
        Debug.msg(3, "GLCanvas.OnDraw()")

        self.nvizClass.Draw()
        self.SwapBuffers()

