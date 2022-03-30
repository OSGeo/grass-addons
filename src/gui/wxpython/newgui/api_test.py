"""!
@package api_test.py


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


import wx


try:
    import wx.lib.agw.customtreectrl as CT
except ImportError:
    import wx.lib.customtreectrl as CT
import wx.lib.buttons as buttons

try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin

from ctypes import *
import grass.script as grass
from core import globalvar
from core.gcmd import GError, GMessage
from mapdisp import statusbar as sb
from mapwindow import BufferedWindow2
from gui_core.mapdisp import MapFrameBase
import gettext
import core.render as render
from render2 import Map, MapLayer
from core.gcmd import RunCommand, GMessage
from core.debug import Debug
from lmgr.layertree import LMIcons
from gui_core.toolbars import BaseIcons
from icons.icon import MetaIcon
from core.utils import GetLayerNameFromCmd


class ToolBarNames:
    NEWDISPLAY = {"monitor-create": [wx.NewId(), _("Start new map display")]}
    WORKSPACENEW = {"create": [wx.NewId(), _("Create new workspace (Ctrl+N)")]}
    WORKSPACEOPEN = {"open": [wx.NewId(), _("Open existing workspace file (Ctrl+O")]}
    WORKSPACESAVE = {"save": [wx.NewId(), _("Save current workspace to file (Ctrl+S)")]}
    ADDRASTER = {"layer-raster-add": [wx.NewId(), _("Add raster map layer")]}
    ADDVECTOR = {"layer-vector-add": [wx.NewId(), _("Add vector map layer")]}


class MySingleMapFrame(MapFrameBase):
    """! Frame with one map window.

    It is base class for frames which needs only one map.

    Derived class should have \c self.MapWindow or
    it has to override GetWindow() methods.

    @note To access maps use getters only
    (when using class or when writing class itself).
    """

    def __init__(
        self,
        parent=None,
        giface=None,
        id=wx.ID_ANY,
        title=None,
        style=wx.DEFAULT_FRAME_STYLE,
        Map=Map(),
        auimgr=None,
        name=None,
        **kwargs,
    ):
        """!

        @param parent gui parent
        @param id wx id
        @param title window title
        @param style \c wx.Frame style
        @param Map instance of render.Map
        @param name frame name
        @param kwargs arguments passed to MapFrameBase
        """

        MapFrameBase.__init__(
            self,
            parent=parent,
            id=id,
            title=title,
            style=style,
            auimgr=auimgr,
            name=name,
            **kwargs,
        )

        self.Map = Map  # instance of render.Map

        vbox = wx.BoxSizer(wx.HORIZONTAL)
        p = wx.Panel(self, -1)

        # self.ltree = LayerTree(self, self.Map)

        #
        # initialize region values
        #

        self._initMap(Map=self.Map)

        self._lmgr = LayerManager(p, self.Map)

        self.MapWindow = BufferedWindow2(p, giface=giface, id=id, Map=self.Map)

        self.toolbar = None

        vbox.Add(self._lmgr, 1, wx.EXPAND | wx.ALL, 20)
        vbox.Add(self.MapWindow, 1, wx.EXPAND | wx.ALL, 20)
        p.SetSizer(vbox)

    def CreateWxToolBar(self):
        self.toolbar = self.CreateToolBar()

    def AddToolBarItem(self, tname, func):
        if self.toolbar is None:
            raise "ToolBar not created"
        label = tname.keys()[0]

        tid = tname.values()[0][0]
        tooltip = tname.values()[0][1]

        self.toolbar.AddLabelTool(tid, label, self.GetIcon(label), shortHelp=tooltip)
        wx.EVT_TOOL(self, tid, func)

    def GetIcon(self, tname):
        return MetaIcon(img=tname).GetBitmap()

    def GetLayerByIndex(self, index):
        return self.GetLayerManager().GetLayerByIndex(index)

    def GetCurrentIndex(self):
        return self.GetLayerManager().GetCurrentIndex()

    def GetLayerManager(self):
        return self._lmgr

    def SetLayerManager(self, lmgr):
        self._lmgr = lmgr

    def AddLayer(self, layer):
        self.GetLayerManager().AddLayer(layer)

    def GetMap(self):
        """!Returns map (renderer) instance"""
        return self.Map

    def GetWindow(self):
        """!Returns map window"""
        return self.MapWindow

    def GetWindows(self):
        """!Returns list of map windows"""
        return [self.MapWindow]

    def OnRender(self, event):
        """!Re-render map composition (each map layer)"""
        self.GetWindow().UpdateMap(render=True, renderVector=True)

        # update statusbar
        # rashad
        # self.StatusbarUpdate()


class LayerManager(wx.Panel):
    def __init__(
        self,
        parent,
        Map,
        id=wx.ID_ANY,
        style=wx.SUNKEN_BORDER,
        ctstyle=CT.TR_HAS_BUTTONS
        | CT.TR_HAS_VARIABLE_ROW_HEIGHT
        | CT.TR_HIDE_ROOT
        | CT.TR_ROW_LINES
        | CT.TR_FULL_ROW_HIGHLIGHT
        | CT.TR_MULTIPLE,
        **kwargs,
    ):

        wx.Panel.__init__(self, parent=parent, id=id, style=style)

        self._layerList = []
        self._activeLayer = None
        self._activeIndex = 0
        self._Map = Map

        self.ltree = LayerTree(self, Map, id=id, style=style, ctstyle=ctstyle, **kwargs)
        self.ltree.SetSize((300, 500))

    def AddLayer(self, layer, active=True):
        self.ltree.AddLayer(layer, True)

    def GetLayerByIndex(self, index):
        self.ltree.GetLayerByIndex(index)

    def GetCurrentIndex(self):
        self.ltree.GetCurrentIndex()


class LayerTree(treemixin.DragAndDrop, CT.CustomTreeCtrl):
    """copied from lmgr.layertree.py"""

    def __init__(self, parent, Map, id, style, ctstyle, **kwargs):

        if globalvar.hasAgw:
            super(LayerTree, self).__init__(parent, id, agwStyle=ctstyle, **kwargs)
        else:
            super(LayerTree, self).__init__(parent, id, style=ctstyle, **kwargs)

        # wx.Window.__init__(self, parent = parent, id =-2)
        # self.panel = wx.Panel(self, )
        self._layerList = []
        self._activeLayer = None
        self._activeIndex = 0
        self._Map = Map
        self.root = self.AddRoot(_("Map Layers"))
        self.SetPyData(self.root, (None, None))

        il = wx.ImageList(16, 16, mask=False)

        trart = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (16, 16))
        self.folder_open = il.Add(trart)
        trart = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16))
        self.folder = il.Add(trart)

        bmpsize = (16, 16)
        trgif = BaseIcons["addRast"].GetBitmap(bmpsize)
        self.rast_icon = il.Add(trgif)

        trgif = LMIcons["addRast3d"].GetBitmap(bmpsize)
        self.rast3d_icon = il.Add(trgif)

        trgif = LMIcons["addRgb"].GetBitmap(bmpsize)
        self.rgb_icon = il.Add(trgif)

        trgif = LMIcons["addHis"].GetBitmap(bmpsize)
        self.his_icon = il.Add(trgif)

        trgif = LMIcons["addShaded"].GetBitmap(bmpsize)
        self.shaded_icon = il.Add(trgif)

        trgif = LMIcons["addRArrow"].GetBitmap(bmpsize)
        self.rarrow_icon = il.Add(trgif)

        trgif = LMIcons["addRNum"].GetBitmap(bmpsize)
        self.rnum_icon = il.Add(trgif)

        trgif = BaseIcons["addVect"].GetBitmap(bmpsize)
        self.vect_icon = il.Add(trgif)

        trgif = LMIcons["addThematic"].GetBitmap(bmpsize)
        self.theme_icon = il.Add(trgif)

        trgif = LMIcons["addChart"].GetBitmap(bmpsize)
        self.chart_icon = il.Add(trgif)

        trgif = LMIcons["addGrid"].GetBitmap(bmpsize)
        self.grid_icon = il.Add(trgif)

        trgif = LMIcons["addGeodesic"].GetBitmap(bmpsize)
        self.geodesic_icon = il.Add(trgif)

        trgif = LMIcons["addRhumb"].GetBitmap(bmpsize)
        self.rhumb_icon = il.Add(trgif)

        trgif = LMIcons["addLabels"].GetBitmap(bmpsize)
        self.labels_icon = il.Add(trgif)

        trgif = LMIcons["addCmd"].GetBitmap(bmpsize)
        self.cmd_icon = il.Add(trgif)

        trgif = LMIcons["wsImport"].GetBitmap(bmpsize)
        self.ws_icon = il.Add(trgif)

        self.AssignImageList(il)

    def AddLayer(self, layer, active=True, multiple=True, lchecked=True):
        self._Map.AddMapLayer(layer)
        self._layerList.append(layer)
        self._activeIndex = len(self._layerList) - 1
        if layer.name and not multiple:
            # check for duplicates
            item = self.GetFirstVisibleItem()
            while item and item.IsOk():
                if self.GetLayerInfo(item, key="type") == "vector":
                    name = self.GetLayerInfo(item, key="maplayer").GetName()
                    if name == lname:
                        return
                item = self.GetNextVisible(item)

        self.first = True

        # deselect active item
        if self._activeLayer:
            self.SelectItem(self._activeLayer, select=False)

        Debug.msg(3, "LayerTree().AddLayer(): ltype=%s" % (layer.type))

        if layer.type == "command":
            # generic command item
            ctrl = wx.TextCtrl(
                self,
                id=wx.ID_ANY,
                value="",
                pos=wx.DefaultPosition,
                size=(self.GetSize()[0] - 100, 25),
                # style = wx.TE_MULTILINE|wx.TE_WORDWRAP)
                style=wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP,
            )
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnCmdChanged)
            # ctrl.Bind(wx.EVT_TEXT,       self.OnCmdChanged)
        elif layer.type == "group":
            # group item
            ctrl = None
            grouptext = _("Layer group:") + str(self.groupnode)
            self.groupnode += 1
        else:
            btnbmp = LMIcons["layerOptions"].GetBitmap((16, 16))
            ctrl = buttons.GenBitmapButton(
                self, id=wx.ID_ANY, bitmap=btnbmp, size=(24, 24)
            )
            ctrl.SetToolTipString(_("Click to edit layer settings"))
        # rashad            self.Bind(wx.EVT_BUTTON, self.OnLayerContextMenu, ctrl)
        # add layer to the layer tree
        if self._activeLayer and self._activeLayer != self.GetRootItem():
            if self.GetLayerInfo(
                self._activeLayer, key="type"
            ) == "group" and self.IsExpanded(self._activeLayer):
                # add to group (first child of self._activeLayer) if group expanded
                layeritem = self.PrependItem(
                    parent=self._activeLayer, text="", ct_type=1, wnd=ctrl
                )
            else:
                # prepend to individual layer or non-expanded group
                if lgroup == -1:
                    # -> last child of root (loading from workspace)
                    layeritem = self.AppendItem(
                        parentId=self.root, text="", ct_type=1, wnd=ctrl
                    )
                elif lgroup > -1:
                    # -> last child of group (loading from workspace)
                    parent = self.FindItemByIndex(index=lgroup)
                    if not parent:
                        parent = self.root
                    layeritem = self.AppendItem(
                        parentId=parent, text="", ct_type=1, wnd=ctrl
                    )
                elif lgroup is None:
                    # -> previous sibling of selected layer
                    parent = self.GetItemParent(self._activeLayer)
                    layeritem = self.InsertItem(
                        parentId=parent,
                        input=self.GetPrevSibling(self._activeLayer),
                        text="",
                        ct_type=1,
                        wnd=ctrl,
                    )
        else:  # add first layer to the layer tree (first child of root)
            layeritem = self.PrependItem(parent=self.root, text="", ct_type=1, wnd=ctrl)

        # layer is initially unchecked as inactive (beside 'command')
        # use predefined value if given
        if lchecked is not None:
            checked = lchecked
        else:
            checked = True

        self.forceCheck = True
        self.CheckItem(layeritem, checked=checked)

        # add text and icons for each layer layer.type
        label = _("(double click to set properties)") + " " * 15
        if layer.type == "raster":
            self.SetItemImage(layeritem, self.rast_icon)
            self.SetItemText(layeritem, "%s %s" % (_("raster"), label))
        elif layer.type == "3d-raster":
            self.SetItemImage(layeritem, self.rast3d_icon)
            self.SetItemText(layeritem, "%s %s" % (_("3D raster"), label))
        elif layer.type == "rgb":
            self.SetItemImage(layeritem, self.rgb_icon)
            self.SetItemText(layeritem, "%s %s" % (_("RGB"), label))
        elif layer.type == "his":
            self.SetItemImage(layeritem, self.his_icon)
            self.SetItemText(layeritem, "%s %s" % (_("HIS"), label))
        elif layer.type == "shaded":
            self.SetItemImage(layeritem, self.shaded_icon)
            self.SetItemText(layeritem, "%s %s" % (_("shaded relief"), label))
        elif layer.type == "rastnum":
            self.SetItemImage(layeritem, self.rnum_icon)
            self.SetItemText(layeritem, "%s %s" % (_("raster cell numbers"), label))
        elif layer.type == "rastarrow":
            self.SetItemImage(layeritem, self.rarrow_icon)
            self.SetItemText(layeritem, "%s %s" % (_("raster flow arrows"), label))
        elif layer.type == "vector":
            self.SetItemImage(layeritem, self.vect_icon)
            self.SetItemText(layeritem, "%s %s" % (_("vector"), label))
        elif layer.type == "thememap":
            self.SetItemImage(layeritem, self.theme_icon)
            self.SetItemText(
                layeritem, "%s %s" % (_("thematic area (choropleth) map"), label)
            )
        elif layer.type == "themechart":
            self.SetItemImage(layeritem, self.chart_icon)
            self.SetItemText(layeritem, "%s %s" % (_("thematic charts"), label))
        elif layer.type == "grid":
            self.SetItemImage(layeritem, self.grid_icon)
            self.SetItemText(layeritem, "%s %s" % (_("grid"), label))
        elif layer.type == "geodesic":
            self.SetItemImage(layeritem, self.geodesic_icon)
            self.SetItemText(layeritem, "%s %s" % (_("geodesic line"), label))
        elif layer.type == "rhumb":
            self.SetItemImage(layeritem, self.rhumb_icon)
            self.SetItemText(layeritem, "%s %s" % (_("rhumbline"), label))
        elif layer.type == "labels":
            self.SetItemImage(layeritem, self.labels_icon)
            self.SetItemText(layeritem, "%s %s" % (_("vector labels"), label))
        elif layer.type == "command":
            self.SetItemImage(layeritem, self.cmd_icon)
        elif layer.type == "group":
            self.SetItemImage(layeritem, self.folder, CT.TreeItemIcon_Normal)
            self.SetItemImage(layeritem, self.folder_open, CT.TreeItemIcon_Expanded)
            self.SetItemText(layeritem, grouptext)
        elif layer.type == "wms":
            self.SetItemImage(layeritem, self.ws_icon)
            self.SetItemText(layeritem, "%s %s" % (_("wms"), label))

        self.first = False

        if layer.type != "group":
            if layer.cmd and len(layer.cmd) > 1:
                cmd = layer.cmd
                render = False
                name, found = layer.name, True
            else:
                cmd = []
                if layer.type == "command" and layer.name:
                    for c in lname.split(";"):
                        cmd.append(c.split(" "))

                render = False
                name = None

            if ctrl:
                ctrlId = ctrl.GetId()
            else:
                ctrlId = None

            # add a data object to hold the layer's command (does not apply to generic command layers)
            self.SetPyData(
                layeritem,
                (
                    {
                        "cmd": cmd,
                        "type": layer.type,
                        "ctrl": ctrlId,
                        "label": None,
                        "maplayer": None,
                        "vdigit": None,
                        "nviz": None,
                        "propwin": None,
                    },
                    None,
                ),
            )

            # find previous map layer instance
            prevItem = self.GetFirstChild(self.root)[0]
            prevMapLayer = None
            pos = -1
            while prevItem and prevItem.IsOk() and prevItem != layeritem:
                if self.GetLayerInfo(prevItem, key="maplayer"):
                    prevMapLayer = self.GetLayerInfo(prevItem, key="maplayer")

                prevItem = self.GetNextSibling(prevItem)

                if prevMapLayer:
                    pos = self.Map.GetLayerIndex(prevMapLayer)
                else:
                    pos = -1

        #            maplayer = self.Map.AddLayer(pos = pos,
        #                                         ltype = ltype, command = self.GetLayerInfo(prevItem, key = 'cmd'), name = name,
        #                                         active = checked, hidden = False,
        #                                         opacity = lopacity, render = render)
        #            self.SetLayerInfo(layer, key = 'maplayer', value = maplayer)
        #
        #            # run properties dialog if no properties given
        #            if len(cmd) == 0:
        #                self.PropertiesDialog(layer, show = True)

        else:  # group
            self.SetPyData(
                layeritem,
                (
                    {
                        "cmd": None,
                        "type": ltype,
                        "ctrl": None,
                        "label": None,
                        "maplayer": None,
                        "propwin": None,
                    },
                    None,
                ),
            )

        # select new item
        self.SelectItem(layeritem, select=True)

        # use predefined layer name if given
        if layer.name:
            if layer.type == "group":
                self.SetItemText(layeritem, layer.name)
            elif layer.type == "command":
                ctrl.SetValue(layer.name)
            else:
                self.SetItemText(layeritem, "ELEVATIOM@PERMANENT")
        else:
            if layer.type == "group":
                self.OnRenameLayer(None)

        return layeritem

    def GetLayerByIndex(self, index):
        if index > -1 and index < len(self._layerList):
            return self._layerList[index]

    def GetCurrentIndex(self):
        return self._activeIndex
