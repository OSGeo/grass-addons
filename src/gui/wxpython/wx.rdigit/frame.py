"""!
@package frame.py

@brief wxIClass frame with toolbar for digitizing training areas and
for spectral signature analysis.

Classes:
 - frame::RDigitMapFrame
 - frame::MapManager

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad <rashadkm gmail.com>
"""

import os
import sys
import copy
import tempfile

if __name__ == "__main__":
    sys.path.append(os.path.join(os.environ["GISBASE"], "etc", "gui", "wxpython"))

import wx

from ctypes import *
import grass.script as grass
from core import globalvar
from core.gcmd import GError, GMessage
from mapdisp import statusbar as sb
from mapdisp.mapwindow import BufferedWindow
from gui_core.mapdisp import SingleMapFrame
from core.render import Map, MapLayer
from core.gcmd import RunCommand, GMessage
from iclass.dialogs import IClassMapDialog

from toolbars import RDigitMapToolbar, RDigitMapManagerToolbar

from rdigit.mapwindow import RDigitWindow
from rdigit.toolbars import RDigitToolbar
from rdigit.main import haveRDigit, RDigit


class RDigitMapFrame(SingleMapFrame):
    """! RDigitMapFrame main frame
    This is the raster digitizer main window. It holds a minimal layer manager from wxIClass
    """

    def __init__(
        self,
        parent=None,
        giface=None,
        title=_("Raster Digitizer"),
        toolbars=["digitMap", "rdigit"],
        size=(875, 600),
        name="RDigitWindow",
        **kwargs,
    ):
        """!
        @param parent (no parent is expected)
        @param title window title
        @param toolbars dictionary of active toolbars (defalult value represents all toolbars)
        @param size default size
        """
        SingleMapFrame.__init__(
            self, parent=parent, title=title, name=name, Map=Map(), **kwargs
        )
        self._giface = giface

        self.MapWindow = RDigitWindow(
            parent=self, giface=self._giface, id=wx.ID_ANY, frame=self, Map=self.Map
        )
        self.outMapName = None

        self.mapManager = MapManager(self, mapWindow=self.MapWindow, Map=self.GetMap())
        self.SetSize(size)
        # MapWindowRDigit

        # Add toolbars
        toolbarsCopy = toolbars[:]
        if sys.platform == "win32":
            self.AddToolbar(toolbarsCopy.pop(1))
            toolbarsCopy.reverse()
        else:
            self.AddToolbar(toolbarsCopy.pop(0))
        for toolb in toolbarsCopy:
            self.AddToolbar(toolb)

        self.GetMapToolbar().Bind(wx.EVT_CHOICE, self.OnUpdateActive)

        # items for choice
        self.statusbarItems = [
            sb.SbCoordinates,
            sb.SbRegionExtent,
            sb.SbCompRegionExtent,
            sb.SbShowRegion,
            sb.SbAlignExtent,
            sb.SbResolution,
            sb.SbDisplayGeometry,
            sb.SbMapScale,
            sb.SbGoTo,
            sb.SbProjection,
        ]

        # create statusbar and its manager
        statusbar = self.CreateStatusBar(number=4, style=0)
        statusbar.SetStatusWidths([-5, -2, -1, -1])
        self.statusbarManager = sb.SbManager(mapframe=self, statusbar=statusbar)

        # fill statusbar manager
        self.statusbarManager.AddStatusbarItemsByClass(
            self.statusbarItems, mapframe=self, statusbar=statusbar
        )
        self.statusbarManager.AddStatusbarItem(
            sb.SbMask(self, statusbar=statusbar, position=2)
        )
        self.statusbarManager.AddStatusbarItem(
            sb.SbRender(self, statusbar=statusbar, position=3)
        )
        self.statusbarManager.Update()

        self.changes = False

        self._addPanes()
        self._mgr.Update()

        self.mapManager.SetToolbar(self.toolbars["digitMap"])

        # default action
        self.OnPan(event=None)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnCloseWindow(self, event):
        self.Destroy()

    def GetWindow(self):
        return self.MapWindow

    def GetMap(self):
        return self.Map

    def OnHelp(self, event):
        """!Show help page"""
        helpInProgress = True

    def GetToolbar(self, name):
        if name in self.toolbars:
            return self.toolbars[name]

        return None

    def AddToolbar(self, name):
        """!Add toolbars to the frame"""
        if name == "digitMap":
            self.toolbars[name] = RDigitMapToolbar(self)

            self._mgr.AddPane(
                self.toolbars[name],
                wx.aui.AuiPaneInfo()
                .Name(name)
                .Caption(_("Map Toolbar"))
                .ToolbarPane()
                .Top()
                .LeftDockable(False)
                .RightDockable(False)
                .BottomDockable(False)
                .TopDockable(True)
                .CloseButton(False)
                .Layer(2)
                .Row(1)
                .BestSize((self.toolbars[name].GetBestSize())),
            )

        elif name == "rdigit":
            self.toolbars[name] = RDigitToolbar(
                parent=self,
                MapWindow=self.MapWindow,
                digitClass=RDigit,
                layerTree=self.mapManager,
            )

            self._mgr.AddPane(
                self.toolbars[name],
                wx.aui.AuiPaneInfo()
                .Name("rdigittoolbar")
                .Caption(_("Raster Digitizer Toolbar"))
                .ToolbarPane()
                .Top()
                .Row(1)
                .LeftDockable(False)
                .RightDockable(False)
                .BottomDockable(False)
                .TopDockable(True)
                .CloseButton(False)
                .Layer(0)
                .BestSize((self.toolbars["rdigit"].GetBestSize())),
            )
            self.MapWindow.SetToolbar(self.toolbars[name])
            # self._mgr.GetPane('rdigittoolbar').Hide()

    def _addPanes(self):
        """!Add mapwindows and toolbars to aui manager"""

        self._addPaneMapWindow()
        self._addPaneToolbar(name="digitMap")

    def _addPaneToolbar(self, name):

        self.toolbars[name] = RDigitMapManagerToolbar(self, self.mapManager)
        self._mgr.AddPane(
            self.toolbars[name],
            wx.aui.AuiPaneInfo()
            .ToolbarPane()
            .Movable()
            .Name(name)
            .CloseButton(False)
            .Center()
            .Layer(0)
            .BestSize((self.toolbars[name].GetBestSize())),
        )

    def _addPaneMapWindow(self):

        self._mgr.AddPane(
            self.MapWindow,
            wx.aui.AuiPaneInfo()
            .CentrePane()
            .Dockable(False)
            .BestSize((-1, -1))
            .Name("window")
            .CloseButton(False)
            .DestroyOnClose(True)
            .Layer(0),
        )

        #        self._mgr.AddPane(self.MapWindowRDigit, wx.aui.AuiPaneInfo().CentrePane().
        #                          Dockable(True).BestSize((-1,-1)).Name('rdigit').
        #                          CloseButton(False).DestroyOnClose(True).
        #                          Layer(0))

        self._mgr.GetPane("window").Show()
        self._mgr.GetPane("rdigit").Hide()

    def IsStandalone(self):
        """!Check if Map display is standalone"""
        return True

    def OnUpdateActive(self, event):
        """!
        @todo move to DoubleMapFrame?
        """
        self.StatusbarUpdate()

    def GetMapToolbar(self):
        """!Returns toolbar with zooming tools"""
        return self.toolbars["digitMap"]

    def AddRasterMap(self, name, firstMap=True, secondMap=True):
        """!Add raster map to Map"""
        cmdlist = ["d.rast", "map=%s" % name]
        if firstMap:
            self.GetFirstMap().AddLayer(
                type="raster",
                command=cmdlist,
                l_active=True,
                name=name,
                l_hidden=False,
                l_opacity=1.0,
                l_render=False,
            )
            self.GetWindow().UpdateMap(render=True, renderVector=False)

    def OnZoomMenu(self, event):
        """!Popup Zoom menu"""
        zoommenu = wx.Menu()
        zoommenu.Destroy()

    def OnZoomIn(self, event):
        super(RDigitMapFrame, self).OnZoomIn(event)

    def OnZoomOut(self, event):
        super(RDigitMapFrame, self).OnZoomOut(event)

    def OnPan(self, event):
        super(RDigitMapFrame, self).OnPan(event)

    def GetOutputMap(self):
        return self.outMapName

    def RemoveToolbar(self, name):
        self.outMapName = self.toolbars["rdigit"].GetMapName()
        self.mapManager.AddLayer(name=self.outMapName)
        self._mgr.GetPane("window").Show()
        self._mgr.Update()


class MapManager:
    """! Class for managing map renderer.

    It is connected with iClassMapManagerToolbar.
    """

    def __init__(self, frame, mapWindow, Map):
        """!

        It is expected that \a mapWindow is conected with \a Map.
        @param frame application main window
        @param mapWindow map window instance
        @param Map map renderer instance
        """
        self.map = Map
        self.frame = frame
        self.mapWindow = mapWindow
        self.toolbar = None
        self.layerName = {}

    def SetToolbar(self, toolbar):
        self.toolbar = toolbar

    def AddLayer(self, name, alias=None, resultsLayer=False):
        """!Adds layer to Map and update toolbar

        @param name layer (raster) name
        @param resultsLayer True if layer is temp. raster showing the results of computation
        """
        if resultsLayer and name in [
            l.GetName() for l in self.map.GetListOfLayers(l_name=name)
        ]:
            self.frame.Render(self.mapWindow)
            return

        cmdlist = ["d.rast", "map=%s" % name]
        self.map.AddLayer(
            type="raster",
            command=cmdlist,
            l_active=True,
            name=name,
            l_hidden=False,
            l_opacity=1.0,
            l_render=True,
        )
        # self.frame.Render(self.GetWindow().Render())
        self.frame.GetWindow().UpdateMap(render=True, renderVector=False)

        if alias is not None:
            alias = self._addSuffix(alias)
            self.layerName[alias] = name
            name = alias
        else:
            self.layerName[name] = name

        self.toolbar.choice.Insert(name, 0)
        self.toolbar.choice.SetSelection(0)

    def RemoveLayer(self, name, idx):
        """!Removes layer from Map and update toolbar"""
        name = self.layerName[name]
        self.map.RemoveLayer(name=name)
        del self.layerName[name]
        self.toolbar.choice.Delete(idx)
        if not self.toolbar.choice.IsEmpty():
            self.toolbar.choice.SetSelection(0)

        self.frame.GetWindow().UpdateMap(render=True, renderVector=False)
        # self.frame.Render(self.mapWindow)

    def SelectLayer(self, name):
        """!Moves selected layer to top"""
        layers = self.map.GetListOfLayers(l_type="raster")
        idx = None
        for i, layer in enumerate(layers):
            if self.layerName[name] == layer.GetName():
                idx = i
                break

        if idx is not None:  # should not happen
            layers.append(layers.pop(idx))

            choice = self.toolbar.choice
            idx = choice.FindString(name)
            choice.Delete(idx)
            choice.Insert(name, 0)
            choice.SetSelection(0)

            # layers.reverse()
            self.map.ReorderLayers(layers)
            self.frame.GetWindow().UpdateMap(render=True, renderVector=False)


def test():
    import gettext
    import core.render as render

    gettext.install(
        "grasswxpy", os.path.join(os.getenv("GISBASE"), "locale"), unicode=True
    )

    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()

    frame = RDigitMapFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    test()
