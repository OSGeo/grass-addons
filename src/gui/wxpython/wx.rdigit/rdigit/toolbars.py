"""!
@package rdigit.toolbars

@brief wxGUI raster digitizer toolbars

List of classes:
 - toolbars::RDigitToolbar

(C) 2007-2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Mohammed Rashad <rashadkm gmail.com>
"""

import wx
from grass.script import core as grass
from gui_core.toolbars import BaseToolbar, BaseIcons
from dialogs_core import CreateNewRaster
from vdigit.preferences import VDigitSettingsDialog
from core.debug import Debug
from core.settings import UserSettings
from core.gcmd import GError
from icons.icon import MetaIcon
from iclass.digit import IClassVDigit


class RDigitToolbar(BaseToolbar):
    """!Toolbar for digitization"""

    def __init__(
        self, parent, MapWindow, digitClass, tools=[], layerTree=None, log=None
    ):
        self.MapWindow = MapWindow
        self.Map = MapWindow.GetMap()  # Map class instance
        self.layerTree = layerTree  # reference to layer tree associated to map display
        self.log = log  # log area
        self.tools = tools
        self.digitClass = digitClass
        BaseToolbar.__init__(self, parent)
        self.digit = None

        # currently selected map layer for editing (reference to MapLayer instance)
        self.mapLayer = None
        self.mapName = None

        self.comboid = self.combo = None
        self.undo = -1
        self.redo = -1

        # only one dialog can be open
        self.settingsDialog = None

        # create toolbars (two rows optionally)
        self.InitToolbar(self._toolbarData())
        self.Bind(wx.EVT_TOOL, self._toolChosen)

        # default action (digitize new point, line, etc.)
        self.action = {"desc": "", "type": "", "id": -1}

        # list of available raster maps
        self.UpdateListOfLayers(updateTool=True)

        self.layerNameList = []
        layers = self.Map.GetListOfLayers(
            l_type="raster", l_mapset=grass.gisenv()["MAPSET"]
        )

        for layer in layers:
            if layer.name not in self.layerNameList:  # do not duplicate layer
                self.layerNameList.append(layer.GetName())

        # realize toolbar
        self.Realize()
        # workaround for Mac bug. May be fixed by 2.8.8, but not before then.
        if self.combo:
            self.combo.Hide()
            self.combo.Show()

        # disable undo/redo
        if self.undo > 0:
            self.EnableTool(self.undo, False)
        if self.redo > 0:
            self.EnableTool(self.redo, False)

        # toogle to pointer by default
        self.OnTool(None)

        self.FixSize(width=105)

    def _toolbarData(self):
        """!Toolbar data"""
        data = []

        icons = {
            "addLine": MetaIcon(
                img="line-create",
                label=_("Digitize new line"),
                desc=_(
                    "Left: new point; Ctrl+Left: undo last point; Right: close line"
                ),
            ),
            "addBoundary": MetaIcon(
                img="polygon-create",
                label=_("Digitize new boundary"),
                desc=_(
                    "Left: new point; Ctrl+Left: undo last point; Right: close line"
                ),
            ),
            "addCircle": MetaIcon(
                img="draw-circle",
                label=_("Digitize new Cirlce"),
                desc=_(
                    "Left: new point; Ctrl+Left: undo last point; Right: close line"
                ),
            ),
            "deleteLine": MetaIcon(
                img="line-delete",
                label=_("Delete feature(s)"),
                desc=_("Left: Select; Ctrl+Left: Unselect; Right: Confirm"),
            ),
            "deleteArea": MetaIcon(
                img="polygon-delete",
                label=_("Delete area(s)"),
                desc=_("Left: Select; Ctrl+Left: Unselect; Right: Confirm"),
            ),
            "deleteCircle": MetaIcon(
                img="delete-circle",
                label=_("Digitize new Cirlce"),
                desc=_(
                    "Left: new point; Ctrl+Left: undo last point; Right: close line"
                ),
            ),
            "settings": BaseIcons["settings"].SetLabel(_("Digitization settings")),
            "quit": BaseIcons["quit"].SetLabel(
                label=_("Quit digitizer"), desc=_("Quit digitizer and save changes")
            ),
            "help": BaseIcons["help"].SetLabel(
                label=_("Vector Digitizer manual"),
                desc=_("Show Vector Digitizer manual"),
            ),
            "undo": MetaIcon(
                img="undo", label=_("Undo"), desc=_("Undo previous changes")
            ),
            "redo": MetaIcon(
                img="redo", label=_("Redo"), desc=_("Redo previous changes")
            ),
        }

        if not self.tools or "selector" in self.tools:
            data.append((None,))

        if not self.tools or "addLine" in self.tools:
            data.append(("addLine", icons["addLine"], self.OnAddLine, wx.ITEM_CHECK))

        if not self.tools or "addBoundary" in self.tools:
            data.append(
                ("addBoundary", icons["addBoundary"], self.OnAddBoundary, wx.ITEM_CHECK)
            )

        #        if not self.tools or 'addCircle' in self.tools:
        #            data.append(("addCircle", icons["addCircle"],
        #                         self.OnAddCircle,
        #                         wx.ITEM_CHECK))

        data.append((None,))

        if not self.tools or "deleteLine" in self.tools:
            data.append(
                ("deleteLine", icons["deleteLine"], self.OnDeleteLine, wx.ITEM_CHECK)
            )
        if not self.tools or "deleteArea" in self.tools:
            data.append(
                ("deleteArea", icons["deleteArea"], self.OnDeleteArea, wx.ITEM_CHECK)
            )
        #        if not self.tools or 'deleteCircle' in self.tools:
        #            data.append(("deleteCircle", icons["deleteCircle"],
        #                         self.OnDeleteCircle,
        #                         wx.ITEM_CHECK))

        #        if not self.tools or 'undo' in self.tools or \
        #                'redo' in self.tools:
        #            data.append((None, ))
        #        if not self.tools or 'undo' in self.tools:
        #            data.append(("undo", icons["undo"],
        #                         self.OnUndo))
        #        if not self.tools or 'redo' in self.tools:
        #            data.append(("redo", icons["redo"],
        #                         self.OnRedo))
        #        if not self.tools or 'settings' in self.tools or \
        #                'help' in self.tools or \
        #                'quit' in self.tools:
        #            data.append((None, ))

        if not self.tools or "help" in self.tools:
            data.append(("help", icons["help"], self.OnHelp))
        if not self.tools or "quit" in self.tools:
            data.append(("quit", icons["quit"], self.OnExit))

        return self._getToolbarData(data)

    def _toolChosen(self, event):
        """!Tool selected -> untoggles selected tools in other
        toolbars

        @todo implement iclass front-end
        """
        self.parent.MapWindow.UnregisterAllHandlers()

        if hasattr(self.parent, "UpdateTools"):
            self.parent.UpdateTools(event)
        self.OnTool(event)

    def OnTool(self, event):
        """!Tool selected -> untoggles previusly selected tool in
        toolbar"""
        # set cursor
        cursor = self.parent.cursors["cross"]
        self.MapWindow.SetCursor(cursor)

        # pointer
        self.parent.OnPointer(None)

        aId = self.action.get("id", -1)
        BaseToolbar.OnTool(self, event)

        # clear tmp canvas
        if self.action["id"] != aId or aId == -1:
            self.MapWindow.polycoords = []
            self.MapWindow.ClearLines(pdc=self.MapWindow.pdcTmp)
        #            if self.digit and \
        #                    len(self.MapWindow.digit.GetDisplay().GetSelected()) > 0:
        #                # cancel action
        #                self.MapWindow.OnMiddleDown(None)
        #
        # set no action
        if self.action["id"] == -1:
            self.action = {"desc": "", "type": "", "id": -1}

        # set focus
        self.MapWindow.SetFocus()

    def OnAddLine(self, event):
        """!Add line to the raster map layer"""

        Debug.msg(2, "RDigitToolbar.OnAddLine()")

        self.action = {"desc": "addLine", "type": "line", "id": self.addLine}
        self.MapWindow.mouse["box"] = "line"

    def OnAddBoundary(self, event):
        """!Add boundary to the raster map layer"""

        Debug.msg(2, "RDigitToolbar.OnAddBoundary()")

        if self.action["desc"] != "addLine" or self.action["type"] != "boundary":
            self.MapWindow.polycoords = []  # reset temp line
        self.action = {"desc": "addLine", "type": "boundary", "id": self.addBoundary}
        self.MapWindow.mouse["box"] = "line"

    def OnAddCircle(self, event):
        """!Add cirlce to the raster map layer"""

        Debug.msg(2, "RDigitToolbar.OnAddCircle()")

        if self.action["desc"] != "addCircle":
            self.MapWindow.polycoords = []  # reset temp line
        self.action = {"desc": "addCircle", "type": "circle", "id": self.addCircle}
        self.MapWindow.mouse["box"] = "line"

    def OnExit(self, event=None):
        """!Quit digitization tool"""

        # stop editing of the currently selected map layer
        if self.mapLayer:
            self.StopEditing()

        # close dialogs if still open
        if self.settingsDialog:
            self.settingsDialog.OnCancel(None)

        # set default mouse settings
        self.MapWindow.mouse["use"] = "pointer"
        self.MapWindow.mouse["box"] = "point"
        self.MapWindow.polycoords = []

        # disable the toolbar
        self.parent.RemoveToolbar("rdigit")

    def OnDeleteLine(self, event):
        """!Delete line"""

        Debug.msg(2, "RDigittoolbar.OnDeleteLine():")

        self.action = {"desc": "deleteLine", "id": self.deleteLine}
        self.MapWindow.mouse["box"] = "box"

    def OnDeleteArea(self, event):
        """!Delete Area"""

        Debug.msg(2, "RDigittoolbar.OnDeleteArea():")

        self.action = {"desc": "deleteArea", "id": self.deleteArea}
        self.MapWindow.mouse["box"] = "line"

    def OnDeleteCircle(self, event):
        """!Delete Circle"""

        Debug.msg(2, "RDigittoolbar.OnDeleteCircle():")

        self.action = {"desc": "deleteCircle", "id": self.deleteCircle}
        self.MapWindow.mouse["box"] = "line"

    def OnUndo(self, event):
        """!Undo previous changes"""
        self.digit.Undo()

        event.Skip()

    def OnRedo(self, event):
        """!Undo previous changes"""
        self.digit.Undo(level=1)

        event.Skip()

    def EnableUndo(self, enable=True):
        """!Enable 'Undo' in toolbar

        @param enable False for disable
        """
        self._enableTool(self.undo, enable)

    def EnableRedo(self, enable=True):
        """!Enable 'Redo' in toolbar

        @param enable False for disable
        """
        self._enableTool(self.redo, enable)

    def _enableTool(self, tool, enable):
        if not self.FindById(tool):
            return

        if enable:
            if self.GetToolEnabled(tool) is False:
                self.EnableTool(tool, True)
        else:
            if self.GetToolEnabled(tool) is True:
                self.EnableTool(tool, False)

    def OnHelp(self, event):
        """!Show digitizer help page in web browser"""
        helpInProgress = True
        # log = self.parent.GetLayerManager().GetLogWindow()
        # log.RunCmd(['g.manual', 'entry=wxGUI.Vector_Digitizer'])

    def GetListOfLayers(self):
        return self.layerNameList

    def GetMapName(self):
        return self.mapName

    def OnSelectMap(self, event):
        """!Select raster map layer for editing
        If there is a raster map layer already edited, this action is
        firstly terminated. The map layer is closed. After this the
        selected map layer activated for editing.
        """

        selectedMapName = None
        selection = -1
        if event.GetSelection() == 0:  # create new raster map layer
            if self.mapLayer:
                openRasterMap = self.mapLayer.GetName(fullyQualified=False)["name"]
            else:
                openRasterMap = None
            dlg = CreateNewRaster(self.parent, exceptMap=openRasterMap, disableAdd=True)

            if dlg and dlg.GetName():
                # add layer to map layer tree(layer tree is map manager)

                mapName = str(dlg.GetName() + "@" + grass.gisenv()["MAPSET"])
                self.combo.Append(mapName)
                self.mapName = selectedMapName = mapName
                self.layerNameList.append(mapName)
                vectLayers = self.GetListOfLayers()
                selection = vectLayers.index(mapName)
            else:
                self.combo.SetValue(_("Select raster map"))
                if dlg:
                    dlg.Destroy()
                return
        else:
            selection = event.GetSelection() - 1  # first option is 'New raster map'
            selectedMapName = self.combo.GetValue()

        # skip currently selected map FIXME
        # if self.layers[selection] == self.mapLayer:
        # return

        if selection == -1:  # FIXME
            # deactive map layer for editing
            self.StopEditing()

        # select the given map layer for editing FIXME
        if selectedMapName:
            self.combo.SetValue(selectedMapName)

            self.StartEditing(selectedMapName)
            self.digit.setOutputName(selectedMapName)

        event.Skip()

    def StartEditing(self, mapLayer):
        """!Start editing selected raster map layer.

        @param mapLayer MapLayer to be edited
        """
        # deactive layer FIXME
        # self.Map.ChangeLayerActive(mapLayer, False)

        # clean map canvas
        self.MapWindow.EraseMap()

        #        # unset background map if needed
        #        if mapLayer:
        #            if UserSettings.Get(group = 'vdigit', key = 'bgmap',
        #                                subkey = 'value', internal = True) == mapLayer:
        #                UserSettings.Set(group = 'vdigit', key = 'bgmap',
        #                                 subkey = 'value', value = '', internal = True)
        #
        #            self.parent.SetStatusText(_("Please wait, "
        #                                        "opening raster map <%s> for editing...") % mapLayer,
        #                                        0)
        #
        self.MapWindow.pdcVector = wx.PseudoDC()
        self.digit = self.MapWindow.digit = self.digitClass(mapwindow=self.MapWindow)

        self.mapLayer = mapLayer

        self.EnableAll()
        self.EnableUndo(False)
        self.EnableRedo(False)

        Debug.msg(4, "RDigitToolbar.StartEditing(): layer=%s" % mapLayer)

        # change cursor
        if self.MapWindow.mouse["use"] == "pointer":
            self.MapWindow.SetCursor(self.parent.cursors["cross"])

        if not self.MapWindow.resize:
            self.MapWindow.UpdateMap(render=True)

        # respect opacity
        opacity = 100  # FIXME mapLayer.GetOpacity(float = True)

        if opacity < 1.0:
            alpha = int(opacity * 255)
            self.digit.GetDisplay().UpdateSettings(alpha=alpha)

        return True

    def StopEditing(self):
        """!Stop editing of selected raster map layer.

        @return True on success
        @return False on failure
        """
        if self.combo:
            self.combo.SetValue(_("Select raster map"))

        # save changes
        if self.mapLayer:
            Debug.msg(4, "RDigitToolbar.StopEditing(): layer=%s" % self.mapLayer)

            dlg = wx.MessageDialog(
                parent=self.parent,
                message=_("Do you want to save changes " "in raster map <%s>?")
                % self.mapLayer,
                caption=_("Save changes?"),
                style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
            )
            if dlg.ShowModal() == wx.ID_NO:
                # revert changes
                self.digit.saveMap = False
            dlg.Destroy()

            # FIXME self.digit.CloseMap()

        # FIXME self.Map.ChangeLayerActive(self.mapLayer, True)

        # change cursor
        self.MapWindow.SetCursor(self.parent.cursors["default"])
        self.MapWindow.pdcVector = None

        del self.digit
        del self.MapWindow.digit

        self.mapLayer = None

        self.MapWindow.redrawAll = True

        return True

    def UpdateListOfLayers(self, updateTool=False):
        """!Update list of available raster map layers.
        This list consists only editable layers (in the current mapset)

        @param updateTool True to update also toolbar
        """
        Debug.msg(4, "RDigitToolbar.UpdateListOfLayers(): updateTool=%d" % updateTool)

        layerNameSelected = None
        # name of currently selected layer
        if self.mapLayer:
            layerNameSelected = self.mapLayer

        # select raster map layer in the current mapset
        layerNameList = []
        self.layers = self.Map.GetListOfLayers(
            l_type="raster", l_mapset=grass.gisenv()["MAPSET"]
        )

        for layer in self.layers:
            if layer.name not in layerNameList:  # do not duplicate layer
                layerNameList.append(layer.GetName())

        if updateTool:  # update toolbar
            if not self.mapLayer:
                value = _("Select raster map")
            else:
                value = layerNameSelected

            if not self.comboid:
                if not self.tools or "selector" in self.tools:
                    self.combo = wx.ComboBox(
                        self,
                        id=wx.ID_ANY,
                        value=value,
                        choices=[
                            _("New raster map"),
                        ]
                        + layerNameList,
                        size=(80, -1),
                        style=wx.CB_READONLY,
                    )
                    self.comboid = self.InsertControl(0, self.combo)
                    self.parent.Bind(wx.EVT_COMBOBOX, self.OnSelectMap, self.comboid)
            else:
                self.combo.SetItems(
                    [
                        _("New raster map"),
                    ]
                    + layerNameList
                )

            self.Realize()

        return layerNameList

    def GetLayer(self):
        """!Get selected layer for editing -- MapLayer instance"""
        return self.mapLayer
