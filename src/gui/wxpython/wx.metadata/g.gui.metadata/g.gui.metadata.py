#!/usr/bin/env python

"""
@module  g.gui.metadata
@brief   GUI components of metadata editor

Classes:
 - g.gui.metadata::MdMainFrame
 - g.gui.metadata::MdDataCatalog
 - g.gui.metadata::NotebookRight
 - g.gui.metadata::MDHelp
 - g.gui.metadata::TreeBrowser
 - g.gui.metadata::MdValidator
 - g.gui.metadata::MdEditConfigPanel
 - g.gui.metadata::MdToolbar

(C) 2014-2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014) (GSoC 2015)
"""

# %module
# % description: Graphical ISO/INSPIRE metadata editor.
# % keyword: general
# % keyword: GUI
# % keyword: metadata
# %end

import os
import sys
import tempfile
import webbrowser
from functools import reduce

import grass.script as grass
import grass.temporal as tgis
from grass.pydispatch import dispatcher
from grass.pydispatch.signal import Signal
from grass.script.setup import set_gui_path

set_gui_path()
from core.debug import Debug

# from datacatalog.tree import LocationMapTree

grass.utils.set_path(modulename="wx.metadata", dirname="mdlib", path="..")

from mdlib import globalvar
from mdlib import mdgrass
from mdlib import mdutil
from mdlib.cswlib import CSWConnectionPanel
from mdlib.mdeditorfactory import MdMainEditor
from mdlib.mdpdffactory import PdfCreator

import wx
from wx import SplitterWindow
from wx.lib.buttons import ThemedGenBitmapTextButton as BitmapBtnTxt

# from pydispatch import dispatcher

# ===============================================================================
# MAIN FRAME
# ===============================================================================
MAINFRAME = None


class LocationMapTree(wx.TreeCtrl):
    def __init__(
        self,
        parent,
        style=wx.TR_HIDE_ROOT
        | wx.TR_EDIT_LABELS
        | wx.TR_LINES_AT_ROOT
        | wx.TR_HAS_BUTTONS
        | wx.TR_FULL_ROW_HIGHLIGHT
        | wx.TR_SINGLE,
    ):
        """Location Map Tree constructor."""
        super(LocationMapTree, self).__init__(parent, id=wx.ID_ANY, style=style)

        try:
            global GetListOfLocations, ListOfMapsets, RunCommand

            from core.gcmd import RunCommand
            from core.utils import GetListOfLocations, ListOfMapsets
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.showNotification = Signal("Tree.showNotification")
        self.parent = parent
        self.root = self.AddRoot(
            "Catalog"
        )  # will not be displayed when we use TR_HIDE_ROOT flag

        self._initVariables()
        self.MakeBackup()

        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRightClick)

        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

    def _initTreeItems(self, locations=[], mapsets=[]):
        """Add locations, mapsets and layers to the tree."""
        if not locations:
            locations = GetListOfLocations(self.gisdbase)
        if not mapsets:
            mapsets = ["*"]

        first = True
        for loc in locations:
            location = loc
            if first:
                self.ChangeEnvironment(location, "PERMANENT")
                first = False
            else:
                self.ChangeEnvironment(location)

            varloc = self.AppendItem(self.root, loc)
            # add all mapsets
            mapsets = ListOfMapsets()
            if mapsets:
                for mapset in mapsets:
                    self.AppendItem(varloc, mapset)
            else:
                self.AppendItem(varloc, _("No mapsets readable"))
                continue

            # get list of all maps in location
            maplist = RunCommand(
                "g.list",
                flags="mt",
                type="raster,raster_3d,vector",
                mapset=",".join(mapsets),
                quiet=True,
                read=True,
            )
            maplist = maplist.splitlines()
            for ml in maplist:
                # parse
                parts1 = ml.split("/")
                parts2 = parts1[1].split("@")
                mapset = parts2[1]
                mlayer = parts2[0]
                ltype = parts1[0]

                # add mapset
                if self.itemExists(mapset, varloc) is False:
                    varmapset = self.AppendItem(varloc, mapset)
                else:
                    varmapset = self.getItemByName(mapset, varloc)

                # add type node if not exists
                if self.itemExists(ltype, varmapset) is False:
                    vartype = self.AppendItem(varmapset, ltype)

                self.AppendItem(vartype, mlayer)

        self.RestoreBackup()
        Debug.msg(1, "Tree filled")

    def InitTreeItems(self):
        """Create popup menu for layers"""
        raise NotImplementedError()

    def _popupMenuLayer(self):
        """Create popup menu for layers"""
        raise NotImplementedError()

    def _popupMenuMapset(self):
        """Create popup menu for mapsets"""
        raise NotImplementedError()

    def _initVariables(self):
        """Init variables."""
        self.selected_layer = None
        self.selected_type = None
        self.selected_mapset = None
        self.selected_location = None

        self.gisdbase = grass.gisenv()["GISDBASE"]
        self.ctrldown = False

    def GetControl(self):
        """Returns control itself."""
        return self

    def DefineItems(self, item0):
        """Set selected items."""
        self.selected_layer = None
        self.selected_type = None
        self.selected_mapset = None
        self.selected_location = None
        items = []
        item = item0
        while self.GetItemParent(item):
            items.insert(0, item)
            item = self.GetItemParent(item)

        self.selected_location = items[0]
        length = len(items)
        if length > 1:
            self.selected_mapset = items[1]
            if length > 2:
                self.selected_type = items[2]
                if length > 3:
                    self.selected_layer = items[3]

    def getItemByName(self, match, root):
        """Return match item from the root."""
        item, cookie = self.GetFirstChild(root)
        while item.IsOk():
            if self.GetItemText(item) == match:
                return item
            item, cookie = self.GetNextChild(root, cookie)
        return None

    def itemExists(self, match, root):
        """Return true if match item exists in the root item."""
        item, cookie = self.GetFirstChild(root)
        while item.IsOk():
            if self.GetItemText(item) == match:
                return True
            item, cookie = self.GetNextChild(root, cookie)
        return False

    def UpdateTree(self):
        """Update whole tree."""
        self.DeleteAllItems()
        self.root = self.AddRoot("Tree")
        self.AddTreeItems()
        label = "Tree updated."
        self.showNotification.emit(message=label)

    def OnSelChanged(self, event):
        self.selected_layer = None

    def OnRightClick(self, event):
        """Display popup menu."""
        self.DefineItems(event.GetItem())
        if self.selected_layer:
            self._popupMenuLayer()
        elif self.selected_mapset and self.selected_type is None:
            self._popupMenuMapset()

    def OnDoubleClick(self, event):
        """Double click"""
        Debug.msg(1, "Double CLICK")

    def OnKeyDown(self, event):
        """Set key event and check if control key is down"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.ctrldown = True
            Debug.msg(1, "CONTROL ON")

    def OnKeyUp(self, event):
        """Check if control key is up"""
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.ctrldown = False
            Debug.msg(1, "CONTROL OFF")

    def MakeBackup(self):
        """Make backup for case of change"""
        gisenv = grass.gisenv()
        self.glocation = gisenv["LOCATION_NAME"]
        self.gmapset = gisenv["MAPSET"]

    def RestoreBackup(self):
        """Restore backup"""
        stringl = "LOCATION_NAME=" + self.glocation
        RunCommand("g.gisenv", set=stringl)
        stringm = "MAPSET=" + self.gmapset
        RunCommand("g.gisenv", set=stringm)

    def ChangeEnvironment(self, location, mapset=None):
        """Change gisenv variables -> location, mapset"""
        stringl = "LOCATION_NAME=" + location
        RunCommand("g.gisenv", set=stringl)
        if mapset:
            stringm = "MAPSET=" + mapset
            RunCommand("g.gisenv", set=stringm)

    def ExpandCurrentLocation(self):
        """Expand current location"""
        location = grass.gisenv()["LOCATION_NAME"]
        item = self.getItemByName(location, self.root)
        if item is not None:
            self.SelectItem(item)
            self.ExpandAllChildren(item)
            self.EnsureVisible(item)
        else:
            Debug.msg(1, "Location <%s> not found" % location)


class MdMainFrame(wx.Frame):
    """Main frame of metadata editor"""

    def __init__(self, jinjaPath=None, xmlPath=None, init=False):
        """
        @param jinjaPath: path to jinja profile
        @param xmlPath: path to xml with will be read by editor
        @var first,firstAfterChoice,second,secondAfterChoice,secondMultiEdit: initMultipleEditor() and onInitEditor() handler
        @var self. initMultipleEditor() and onInitEditor() handler
        @var self.templateEditor: true= Editor is in mode 'Template creator(widgets with chkbox)'
        @var nameTMPprofile: in case if 'profile editor is on' this var holds name oof temporaly jinja profile
        @var batch: if true multiple editing metadata of maps is ON
        """
        wx.Frame.__init__(self, None, title="Metadata Editor", size=(650, 500))

        try:
            global GError, GMessage

            from core.gcmd import GError, GMessage
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.initDefaultPathStorageMetadata()

        self.config = wx.Config("g.gui.metadata")
        self.jinjaPath = jinjaPath
        self.xmlPath = xmlPath
        self.first = True
        self.firstAfterChoice = False
        self.second = False
        self.secondAfterChoice = False
        self.secondMultiEdit = False
        self.md = None
        self.templateEditor = False
        self.sb = self.CreateStatusBar()

        self.cres = 0  # resizeFrame
        self.nameTMPteplate = None
        self.batch = False
        self.mdCreator = None
        self.editStatus = None
        self.initEditor()

        dispatcher.connect(
            self.initNewMD, signal="NEW_MD.create", sender=dispatcher.Any
        )
        dispatcher.connect(
            self.onEditingMode, signal="EDITING_MODE.update", sender=dispatcher.Any
        )
        dispatcher.connect(
            self.setStatusbarText,
            signal="STATUS_BAR_TEXT.update",
            sender=dispatcher.Any,
        )
        dispatcher.connect(
            self.onRefreshTreeBrowser,
            signal="REFRESH_TREE_BROWSER.update",
            sender=dispatcher.Any,
        )
        dispatcher.connect(
            self.onChangeEditMapProfile,
            signal="ISO_PROFILE.update",
            sender=dispatcher.Any,
        )
        dispatcher.connect(
            self.onUpdateGrassMetadata,
            signal="GRASS_METADATA.update",
            sender=dispatcher.Any,
        )

    def initConfigurePanel(self):
        self.configPanelLeft = wx.Panel(self.leftPanel, id=wx.ID_ANY)
        self.SetMinSize((240, -1))
        self.mapGrassEdit = True

        self.rbGrass = wx.RadioButton(
            self.configPanelLeft,
            id=wx.ID_ANY,
            label="Metadata map editor",
            style=wx.RB_GROUP,
        )
        self.rbExternal = wx.RadioButton(
            self.configPanelLeft, id=wx.ID_ANY, label="Metadata external editor"
        )
        self.comboBoxProfile = wx.ComboBox(
            self.configPanelLeft,
            choices=["INSPIRE", "GRASS BASIC", "TEMPORAL", "Load custom"],
        )
        dispatcher.connect(
            self.onSetProfile, signal="SET_PROFILE.update", sender=dispatcher.Any
        )
        self.comboBoxProfile.SetStringSelection("INSPIRE")

        self.Bind(wx.EVT_RADIOBUTTON, self.onSetRadioType, id=self.rbGrass.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSetRadioType, id=self.rbGrass.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSetRadioType, id=self.rbExternal.GetId())

    def onSetRadioType(self, evt=None):
        self.mapGrassEdit = self.rbGrass.GetValue()
        if self.mapGrassEdit is False:
            self.comboBoxProfile.Hide()
        else:
            self.comboBoxProfile.Show()
        self.onEditingMode(editStatus=self.mapGrassEdit)

    def onSetProfile(self, profile=None, multi=False):
        if profile is not None:
            self.comboBoxProfile.SetStringSelection(profile)
        if multi:
            self.comboBoxProfile.Disable()
        else:
            self.comboBoxProfile.Enable()
        if profile == "Load custom":
            self.bttCreateTemplate.Disable()
        else:
            self.bttCreateTemplate.Enable()

    def initToolbar(self):
        # self.toolbarPanel=wx.Panel(self, id=wx.ID_ANY)
        self.batch = False
        self.extendEdit = False
        self.toolbar = wx.ToolBar(self, 1, wx.DefaultPosition, (-1, -1))

        bitmapSave = wx.Image(
            os.path.join(os.environ["GISBASE"], "gui", "icons", "grass", "save.png"),
            wx.BITMAP_TYPE_PNG,
        ).ConvertToBitmap()
        bitmapNew = wx.Image(
            os.path.join(os.environ["GISBASE"], "gui", "icons", "grass", "create.png"),
            wx.BITMAP_TYPE_PNG,
        ).ConvertToBitmap()
        bitmapLoad = wx.Image(
            os.path.join(os.environ["GISBASE"], "gui", "icons", "grass", "open.png"),
            wx.BITMAP_TYPE_PNG,
        ).ConvertToBitmap()
        bitmaSettings = wx.Image(
            os.path.join(
                os.environ["GISBASE"], "gui", "icons", "grass", "settings.png"
            ),
            wx.BITMAP_TYPE_PNG,
        ).ConvertToBitmap()
        # -------------------------------------------------------------------- EDIT
        self.toolbar.AddSeparator()
        bitmapEdit = wx.Image(
            os.path.join(os.environ["GISBASE"], "gui", "icons", "grass", "edit.png"),
            wx.BITMAP_TYPE_PNG,
        ).ConvertToBitmap()

        # -------------------------------------------------------------------- EDIT
        self.bttEdit = BitmapBtnTxt(self.toolbar, -1, bitmapEdit, size=(40, -1))
        self.toolbar.AddControl(control=self.bttEdit)
        self.bttEdit.Disable()
        # -------------------------------------------------------------------- NEW SESION
        # self.toolbar.AddSeparator()
        self.bttNew = BitmapBtnTxt(self.toolbar, -1, bitmapNew, "", size=(40, -1))
        self.toolbar.AddControl(control=self.bttNew)
        self.bttNew.Disable()
        # -------------------------------------------------------------------- NEW TEMPLATE
        self.bttCreateTemplate = BitmapBtnTxt(
            self.toolbar, -1, bitmapNew, "template", size=(100, -1)
        )
        self.toolbar.AddControl(control=self.bttCreateTemplate)
        self.bttCreateTemplate.Disable()
        self.toolbar.AddSeparator()

        # ----------------------------------------------------------------- OPEN TEMPLATE
        self.bttLoad = BitmapBtnTxt(
            self.toolbar, -1, bitmapLoad, "profile", size=(100, -1)
        )
        self.toolbar.AddControl(control=self.bttLoad)
        self.bttLoad.Disable()
        # ---------------------------------------------------------------------- OPEN XML
        self.bttLoadXml = BitmapBtnTxt(self.toolbar, -1, bitmapLoad, "xml")
        self.toolbar.AddControl(control=self.bttLoadXml)
        self.bttLoadXml.Disable()
        self.toolbar.AddSeparator()
        # -------------------------------------------------------------------------- export xml
        self.bttSave = BitmapBtnTxt(self.toolbar, -1, bitmapSave, "xml")
        self.bttSave.Disable()
        self.toolbar.AddControl(control=self.bttSave)
        # -------------------------------------------------------------------------- export template
        self.bttSaveTemplate = BitmapBtnTxt(
            self.toolbar, -1, bitmapSave, "template", size=(100, -1)
        )
        self.bttSaveTemplate.Disable()
        self.toolbar.AddControl(control=self.bttSaveTemplate)
        # -------------------------------------------------------------------------- update grass
        self.bttUpdateGRASS = BitmapBtnTxt(
            self.toolbar, -1, bitmapSave, "GRASS", size=(100, -1)
        )
        self.bttUpdateGRASS.Disable()
        self.toolbar.AddControl(control=self.bttUpdateGRASS)
        # -------------------------------------------------------------------------- export pdf
        self.bttExportPdf = BitmapBtnTxt(
            self.toolbar, -1, bitmapSave, "pdf", size=(100, -1)
        )
        self.bttExportPdf.Disable()
        self.toolbar.AddControl(control=self.bttExportPdf)
        self.toolbar.AddSeparator()
        # -------------------------------------------------------------------------- publish csw
        self.bttExportCSW = BitmapBtnTxt(
            self.toolbar, -1, bitmapSave, "csw", size=(100, -1)
        )
        self.bttExportCSW.Disable()
        self.toolbar.AddControl(control=self.bttExportCSW)
        self.toolbar.AddSeparator()
        # -------------------------------------------------------------------------- Config
        self.bttConfig = BitmapBtnTxt(
            self.toolbar, -1, bitmaSettings, "", size=(40, -1)
        )
        self.toolbar.AddControl(control=self.bttConfig)
        self.toolbar.AddSeparator()

        self.toolbar.Realize()

        self.bttLoad.Bind(wx.EVT_BUTTON, self.onLoadTemplate)
        self.bttSave.Bind(wx.EVT_BUTTON, self.onSaveXML)
        self.bttLoadXml.Bind(wx.EVT_BUTTON, self.onLoadXml)
        self.bttSaveTemplate.Bind(wx.EVT_BUTTON, self.onSaveTemplate)

        self.bttNew.Bind(wx.EVT_BUTTON, self.onNewSession)
        self.bttEdit.Bind(wx.EVT_BUTTON, self.onEdit)
        self.bttExportCSW.Bind(wx.EVT_BUTTON, self.onExportCSW)
        self.bttCreateTemplate.Bind(wx.EVT_BUTTON, self.onCreateTemplate)
        self.bttExportPdf.Bind(wx.EVT_BUTTON, self.onExportPdf)
        self.bttConfig.Bind(wx.EVT_BUTTON, self.onSettings)

    def onExportCSW(self, evt):
        self.cswDialog = wx.Dialog(
            self,
            id=wx.ID_ANY,
            title="Csw publisher",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.DefaultSize,
            pos=wx.DefaultPosition,
        )

        self.cswPanel = CswPublisher(self.cswDialog, self)
        self.cswDialog.SetSize((1024, 760))

        self.cswPanel.publishBtt.Bind(wx.EVT_BUTTON, self._onExportCsw)
        dbSizer = wx.BoxSizer(wx.VERTICAL)
        dbSizer.Add(self.cswPanel, flag=wx.EXPAND, proportion=1)
        self.cswDialog.SetSizer(dbSizer)
        self.cswDialog.ShowModal()
        self.cswDialog.Destroy()

    def _onExportCsw(self, evt):
        self.exportXMLTemp()
        XMLhead, XMLtail = os.path.split(self.xmlPath)
        outPath = tempfile.gettempdir()
        path = os.path.join(outPath, XMLtail)
        self.cswPanel.publishCSW(str(path))

    def onExportPdf(self, evt):
        XMLhead, XMLtail = os.path.split(self.xmlPath)
        dlg = wx.FileDialog(
            self,
            message="Set output file",
            defaultDir=self.mdDestination,
            defaultFile=XMLtail.split(".")[0] + ".pdf",
            wildcard="*.pdf",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )

        if dlg.ShowModal() == wx.ID_OK:
            outPath = dlg.GetDirectory()
            outFileName = dlg.GetFilename()

            self.exportPDF(outPath=outPath, outFileName=outFileName)
            if mdutil.yesNo(self, "Do you want to open report?"):
                webbrowser.open(os.path.join(outPath, outFileName))

    def onSettings(self, evt):
        dlg = wx.DirDialog(
            self,
            message="Select metadata working directory",
            defaultPath=self.mdDestination,
            style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.mdDestination = dlg.GetPath()
            dlg.Destroy()

        GMessage("Metadata destination: %s" % self.mdDestination)

    def onCreateTemplate(self, evt):
        self.setTemplateEditorPath(value=True)
        if self.onEdit():
            self.bttCreateTemplate.Disable()
            self.bttSaveTemplate.Enable()

    def onEdit(self, evt=None):
        """
        @var : extendEdit if xml and jinja is loaded from file
        """
        if self.extendEdit:
            self.bttUpdateGRASS.Disable()

        if self.rbGrass.GetValue():
            ok = self.editMapMetadata()
            if not ok:
                return False
        else:
            self.initEditor()

        self.bttCreateTemplate.Disable()
        self.bttEdit.Disable()
        self.bttSave.Enable()
        self.bttExportCSW.Enable()
        self.bttExportPdf.Enable()

        try:  # if  multiediting mode ON
            if self.numOfMap > 1:
                XMLhead, XMLtail = os.path.split(self.xmlPath)
                self.batch = mdutil.yesNo(
                    self,
                    "Do you want to save metadata of: <%s> without editing ? "
                    % XMLtail,
                    "Multiple editing",
                )
            if self.batch:
                self.onSaveXML()
        except:
            pass
        return True

    def onNewSession(self, evt):
        self.initEditor()
        self.setTemplateEditorPath(value=False, template=False)
        # check current editing mode(grass or external xml editor)
        if self.rbGrass is False:
            self.bttLoad.Enable()
            self.bttLoadXml.Enable()
        self.sb.SetStatusText("")
        self.bttSave.Disable()
        self.bttExportPdf.Disable()
        self.bttUpdateGRASS.Disable()
        self.jinjaPath = None
        self.xmlPath = None
        self.bttSave.SetLabel("xml")
        self.showMultipleEdit()
        self.bttExportCSW.Disable()
        self.bttSaveTemplate.Disable()
        self.MdDataCatalogPanelLeft.onChanged(None)

    def onLoadXml(self, evt=None):
        dlg = wx.FileDialog(
            self,
            "Select XML metadata file",
            self.mdDestination,
            "",
            "*.xml",
            wx.FD_OPEN,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.xmlPath = dlg.GetPath()
            tx = self.sb.GetStatusText()
            self.sb.SetStatusText(tx + "  Selected XML: " + self.xmlPath)
            self.updateXMLorTemplate()
            dlg.Destroy()

    def onSaveTemplate(self, evt=None):
        dlg = wx.FileDialog(
            self, "Select output file", self.mdDestination, "", "*.xml", wx.FD_SAVE
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.onExportTemplate(
                outPath=dlg.GetDirectory(), outFileName=dlg.GetFilename()
            )

    def onLoadTemplate(self, evt):
        dlg = wx.FileDialog(
            self,
            "Select metadata ISO profile",
            self.mdDestination,
            "",
            "*.xml",
            wx.FD_OPEN,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.jinjaPath = dlg.GetPath()
            tx = self.sb.GetStatusText()
            self.sb.SetStatusText(tx + " Selected profile: " + self.jinjaPath)
            self.updateXMLorTemplate()
        dlg.Destroy()

    def onSaveXML(self, evt=None, path=None):
        self.XMLhead, self.XMLtail = os.path.split(self.xmlPath)
        if not self.batch:  # if  normal saving with user-task-dialog
            dlg = wx.FileDialog(
                self,
                message="Set output file",
                defaultDir=self.mdDestination,
                defaultFile=self.XMLtail,
                wildcard="*.xml",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            )

            if dlg.ShowModal() == wx.ID_OK:
                self.exportXML(
                    outPath=dlg.GetDirectory(), outFileName=dlg.GetFilename()
                )
                if self.bttSave.GetLabelText() == "next":
                    self.editMapMetadata(multipleEditing=True)
            else:
                if self.bttSave.GetLabelText() == "next":
                    ask = mdutil.yesNo(
                        self,
                        "File is not saved. Do you want to save it? ",
                        "Save dialog",
                    )
                    if ask:
                        self.onSaveXML()
                    self.editMapMetadata(multipleEditing=True)
                else:
                    GMessage("File not saved")
            dlg.Destroy()
        else:
            self.exportXML(outPath=None, outFileName=None)
            self.editMapMetadata(multipleEditing=True)

    def onUpdateGrassMetadata(self):
        """Update r.support and v.support"""
        md = self.editor.saveMDfromGUI()
        self.mdCreator.updateGrassMd(md)
        GMessage("GRASS GIS metadata has been updated")

    def onExportTemplate(self, outPath, outFileName):
        """Export defined(pre-filled) template"""
        self.editor.exportTemplate(
            self.jinjaPath, outPath=outPath, xmlOutName=outFileName
        )

    def updateXMLorTemplate(self, evt=None):
        """in case if path of template and xml path are initialized -> enable buttons for next step"""
        if self.jinjaPath is not None and self.xmlPath is not None:
            self.onHideLeftPanel()
            self.bttEdit.Enable()
            self.bttCreateTemplate.Enable()
            self.bttLoad.Disable()
            self.bttLoadXml.Disable()
            self.extendEdit = True

    def hideMultipleEdit(self):
        """Multiple editor is off"""
        self.bttLoad.Hide()
        self.bttLoadXml.Hide()
        self.bttNew.Hide()
        self.bttEdit.Hide()
        self.bttCreateTemplate.Hide()
        self.bttSaveTemplate.Hide()
        self.bttUpdateGRASS.Hide()
        self.bttExportPdf.Hide()

    def showMultipleEdit(self):
        """Multiple editor is on"""
        self.bttLoad.Show()
        self.bttLoadXml.Show()
        self.bttNew.Show()
        self.bttEdit.Show()
        self.bttCreateTemplate.Show()
        self.bttSaveTemplate.Show()
        self.bttUpdateGRASS.Show()
        self.bttExportPdf.Show()

    def initDefaultPathStorageMetadata(self):
        """set working folder"""
        self.mdDestination = os.path.join(mdutil.pathToMapset(), "metadata")
        if not os.path.exists(self.mdDestination):
            os.makedirs(self.mdDestination)

    def onChangeEditMapProfile(self):
        """Update vars"""
        self.profileChoice = self.comboBoxProfile.GetValue()
        self.ntbRight.profile = self.profileChoice

    def exportPDF(self, outPath, outFileName):
        self.initNewMD()
        pdfFile = os.path.join(outPath, outFileName)

        if (
            self.mdCreator is None and self.extendEdit
        ):  # if editing map from grass database
            profileName = os.path.basename(self.jinjaPath)
            xmlFile = os.path.basename(self.xmlPath)
            doc = PdfCreator(
                self.md,
                pdfFile,
                map=None,
                type=None,
                filename=xmlFile,
                profile=profileName,
            )
        else:  # if editing map from external editor
            filename, type, map, profile = self.mdCreator.getMapInfo()
            doc = PdfCreator(self.md, pdfFile, map, type, filename, profile)
        try:
            path = doc.createPDF()
            GMessage("Metadata report has been exported to < %s >" % path)
        except:
            GError("Export pdf error %s" % sys.exc_info()[0])

    def exportXMLTemp(self):
        XMLhead, XMLtail = os.path.split(self.xmlPath)
        outPath = tempfile.gettempdir()
        self.editor.exportToXml(
            self.jinjaPath, outPath=outPath, xmlOutName=XMLtail, msg=False
        )

    def exportXML(self, outPath, outFileName):
        """Save metadta xml file"""
        if outPath is None and outFileName is None:
            XMLhead, XMLtail = os.path.split(self.xmlPath)
            self.editor.exportToXml(
                self.jinjaPath, outPath=XMLhead, xmlOutName=XMLtail, msg=False
            )
        else:
            self.editor.exportToXml(
                self.jinjaPath, outPath=outPath, xmlOutName=outFileName, msg=True
            )

    def onRefreshTreeBrowser(self):
        """Update changes from editor in tree browser"""
        path = os.path.dirname(os.path.realpath(__file__))
        name = "refreshTreeBrowser.xml"
        self.editor.exportToXml(
            self.jinjaPath, outPath=path, xmlOutName=name, msg=False
        )

        pathName = os.path.join(path, name)
        self.ntbRight.refreshXmlBrowser(pathName)
        os.remove(pathName)

    def setStatusbarText(self, text):
        """Set status text"""
        self.sb.SetStatusText(text)

    def setTemplateEditorPath(self, value, template=None):
        """Setup name of temporal template"""
        self.templateEditor = value
        if template is None:
            self.nameTMPteplate = "TMPtemplate"
        elif template is False:
            self.nameTMPteplate = None

    def initNewMD(self):
        """Init new md OWSLib  object"""
        self.md = self.editor.saveMDfromGUI()
        self.ntbRight.md = self.editor.md

    def resizeFrame(self, x1=1, y1=0):
        """Some widgets need refresh frame for proper working"""
        self.cres += 1
        if (self.cres % 2 == 0) and x1 == 1 and y1 == 0:
            x1 = -1
        x, y = self.GetSize()
        self.SetSize((x + x1, y + y1))

    def onHideLeftPanel(self):
        """In editing mode config panel is hidden"""
        self.bttNew.Enable()
        self.Hsizer.Layout()
        self.leftPanel.SetSize((1, 1))

    def onEditingMode(self, editStatus):
        self.resizeFrame()
        self.editStatus = editStatus
        self.Layout()
        if editStatus:
            self.MdDataCatalogPanelLeft.Show()
            self.bttLoad.Disable()
            self.bttLoadXml.Disable()
        else:
            self.MdDataCatalogPanelLeft.Hide()
            self.bttEdit.Disable()
            self.bttCreateTemplate.Disable()
            self.bttLoad.Enable()
            self.bttLoadXml.Enable()
            self.sb.SetStatusText("")
            self.MdDataCatalogPanelLeft.UnselectAll()

    def chckProfileSelection(self, type):
        parent = self.MdDataCatalogPanelLeft.GetSelections()[0]
        while True:
            text = self.MdDataCatalogPanelLeft.GetItemText(parent)
            if text == "Temporal maps":
                baseType = "temporal"
                break
            elif text == "Spatial maps":
                baseType = "spatial"
                break
            parent = self.MdDataCatalogPanelLeft.GetItemParent(parent)
        if baseType == type:
            return True
        else:
            return False

    def editMapMetadata(self, multipleEditing=False):
        """Initialize editor by selection of GRASS map in data catalog
        @param multipleEditing: if user selects more than one map mutlipleEditing=True
        @param numOfMap: holds information about number of selected maps for editing
        @param ListOfMapTypeDict: list of dict stored names of selected maps in dict. dict['cell/vector']=nameofmaps
        """
        if not multipleEditing:
            self.ListOfMapTypeDict = self.MdDataCatalogPanelLeft.ListOfMapTypeDict

        self.profileChoice = self.comboBoxProfile.GetValue()
        self.numOfMap = len(self.ListOfMapTypeDict)

        if self.numOfMap == 0 and multipleEditing is False:
            GMessage("Select map in data catalog...")
            return

        # if editing just one map
        if (
            self.numOfMap == 1
            and multipleEditing is False
            and self.profileChoice != "Load custom"
        ):
            if self.profileChoice == "INSPIRE":
                if self.chckProfileSelection("spatial"):
                    self.mdCreator = mdgrass.GrassMD(
                        self.ListOfMapTypeDict[-1][
                            list(self.ListOfMapTypeDict[-1].keys())[0]
                        ],
                        list(self.ListOfMapTypeDict[-1].keys())[0],
                    )
                    self.mdCreator.createGrassInspireISO()
                    self.jinjaPath = self.mdCreator.profilePathAbs
                else:
                    GMessage("Cannot use this template for temporal metadata")
                    return

            elif self.profileChoice == "GRASS BASIC":
                if self.chckProfileSelection("spatial"):
                    self.mdCreator = mdgrass.GrassMD(
                        self.ListOfMapTypeDict[-1][
                            list(self.ListOfMapTypeDict[-1].keys())[0]
                        ],
                        list(self.ListOfMapTypeDict[-1].keys())[0],
                    )
                    self.mdCreator.createGrassBasicISO()
                    self.jinjaPath = self.mdCreator.profilePathAbs
                else:
                    GMessage("Cannot use this template for temporal metadata")
                    return

            elif self.profileChoice == "TEMPORAL":
                if self.chckProfileSelection("temporal"):
                    self.mdCreator = mdgrass.GrassMD(
                        self.ListOfMapTypeDict[-1][
                            list(self.ListOfMapTypeDict[-1].keys())[0]
                        ],
                        list(self.ListOfMapTypeDict[-1].keys())[0],
                    )
                    self.mdCreator.createTemporalISO()
                    self.jinjaPath = self.mdCreator.profilePathAbs
                else:
                    GMessage("Cannot use this template for spatial metadata")
                    return

            self.xmlPath = self.mdCreator.saveXML(
                self.mdDestination, self.nameTMPteplate, self
            )
            self.initEditor()
        # if editing multiple maps or just one but with loading own custom profile
        if self.profileChoice == "Load custom" and self.numOfMap != 0:
            # load profile. IF - just one map, ELSE - multiple editing
            if multipleEditing is False:
                dlg = wx.FileDialog(
                    self, "Select profile", os.getcwd(), "", "*.xml", wx.FD_OPEN
                )
                if dlg.ShowModal() == wx.ID_OK:
                    self.mdCreator = mdgrass.GrassMD(
                        self.ListOfMapTypeDict[-1][
                            list(self.ListOfMapTypeDict[-1].keys())[0]
                        ],
                        list(self.ListOfMapTypeDict[-1].keys())[0],
                    )

                    if self.chckProfileSelection(
                        "temporal"
                    ):  # if map is temporal, use temporal md pareser
                        self.mdCreator.createTemporalISO()
                    else:
                        self.mdCreator.createGrassInspireISO()

                    self.jinjaPath = dlg.GetPath()
                    self.xmlPath = self.mdCreator.saveXML(
                        self.mdDestination, self.nameTMPteplate, self
                    )

                    # if multiple map are selected
                    if self.numOfMap > 1:
                        self.xmlPath = self.xmlPath
                        self.jinjaPath = self.jinjaPath
                        self.batch = True
                        self.ListOfMapTypeDict.pop()
                        self.initMultipleEditor()
                    else:
                        self.ListOfMapTypeDict.pop()
                        self.initEditor()
                else:  # do nothing
                    return False
            else:
                self.mdCreator = mdgrass.GrassMD(
                    self.ListOfMapTypeDict[-1][
                        list(self.ListOfMapTypeDict[-1].keys())[0]
                    ],
                    list(self.ListOfMapTypeDict[-1].keys())[0],
                )
                self.mdCreator.createGrassInspireISO()
                self.xmlPath = self.mdCreator.saveXML(
                    self.mdDestination, self.nameTMPteplate, self
                )
                self.initMultipleEditor()
                self.ListOfMapTypeDict.pop()

        if not multipleEditing:
            self.onHideLeftPanel()

        if self.numOfMap == 0 and multipleEditing is True:
            multipleEditing = False
            self.onNewSession(None)
            GMessage("All selected maps are edited")
            self.secondMultiEdit = True

        if self.batch and multipleEditing:
            XMLhead, XMLtail = os.path.split(self.xmlPath)
            self.batch = mdutil.yesNo(
                self,
                "Do you want to save metadata of : %s without editing ? " % XMLtail,
                "Multiple editing",
            )

            if self.batch:
                self.batch = True
                self.onSaveXML()
        return True

    def initMultipleEditor(self):
        """initialize multiple editing mode"""
        if self.firstAfterChoice and not self.secondMultiEdit:
            self.splitter = SplitterWindow(
                self, style=wx.SP_3D | wx.SP_LIVE_UPDATE | wx.SP_BORDER
            )
            self.Hsizer.Add(self.splitter, proportion=1, flag=wx.EXPAND)

            self.firstAfterChoice = False
            self.secondAfterChoice = True
            self.bttSave.SetLabel("next")
            self.hideMultipleEdit()
            self.mainSizer.Layout()
            self.editor = MdMainEditor(
                self.splitter, self.jinjaPath, self.xmlPath, self.templateEditor
            )
            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)
            self.splitter.SplitVertically(self.editor, self.ntbRight, sashPosition=0.65)
            self.splitter.SetSashGravity(0.65)
            self.leftPanel.Hide()
            self.resizeFrame()
            self.Show()

        elif self.secondAfterChoice or self.secondMultiEdit:
            if self.secondMultiEdit:
                self.bttSave.SetLabel("next")
                self.hideMultipleEdit()
            self.second = False
            self.secondAfterChoice = True
            self.initEditor()

    def initEditor(
        self,
    ):
        """Initialize editor
        @var first: True= First initialize main frame
        @var firstAfterChoice: True=Init editor editor after set configuration and click onEdit in toolbar
        @var second: refresh editor after first initialize
        @var secondAfterChoice: init editor one more time
        """
        if self.first:
            self.first = False
            self.firstAfterChoice = True
            self.initToolbar()

            self.leftPanel = wx.Panel(self, id=wx.ID_ANY)
            self.initConfigurePanel()
            self.MdDataCatalogPanelLeft = MdDataCatalog(self.leftPanel)

            self._layout()
            self.Show()

        elif self.firstAfterChoice:
            self.splitter = SplitterWindow(
                self, style=wx.SP_3D | wx.SP_LIVE_UPDATE | wx.SP_BORDER
            )
            self.secondMultiEdit = True
            self.firstAfterChoice = False
            self.second = True

            self.editor = MdMainEditor(
                parent=self.splitter,
                profilePath=self.jinjaPath,
                xmlMdPath=self.xmlPath,
                templateEditor=self.templateEditor,
            )

            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)

            self.splitter.SplitVertically(self.editor, self.ntbRight, sashPosition=0.65)
            self.splitter.SetSashGravity(0.65)
            self.leftPanel.Hide()
            self.Hsizer.Add(self.splitter, proportion=1, flag=wx.EXPAND)
            self.splitter.UpdateSize()
            self.resizeFrame()
            self.Show()

        elif self.second:  # if next initializing of editor
            self.second = False
            self.secondAfterChoice = True
            self.splitter.Hide()
            self.leftPanel.Show()
            self.bttNew.Disable()
            self.bttSave.Disable()

            self.resizeFrame()

        elif self.secondAfterChoice:
            self.secondAfterChoice = False
            self.second = True
            self.leftPanel.Hide()
            self.splitter.Show()
            self.bttNew.Enable()
            self.bttSave.Enable()

            ntbRightBCK = self.ntbRight
            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)
            self.splitter.ReplaceWindow(ntbRightBCK, self.ntbRight)

            editorTMP = self.editor
            self.editor = MdMainEditor(
                parent=self.splitter,
                profilePath=self.jinjaPath,
                xmlMdPath=self.xmlPath,
                templateEditor=self.templateEditor,
            )

            self.splitter.ReplaceWindow(editorTMP, self.editor)
            ntbRightBCK.Destroy()
            editorTMP.Destroy()
            self.resizeFrame()
            self.Show()
            self.splitter.SetSashGravity(0.35)
        else:
            GMessage("Select map in data catalog...")

    def _layout(self):

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)

        # self.toolbarPanelSizer = wx.BoxSizer(wx.HORIZONTAL)
        # self.toolbarPanel.SetSizer(self.toolbarPanelSizer)
        # self.toolbarPanelSizer.Add(self.toolbar,proportion=1, flag=wx.EXPAND)

        self.mainSizer.Add(self.toolbar, flag=wx.EXPAND)

        self.mainSizer.Add(
            wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(10000, 5))
        )
        self.mainSizer.AddSpacer(5)

        self.configPanelLeftSizer = wx.BoxSizer(wx.VERTICAL)
        self.configPanelLeft.SetSizer(self.configPanelLeftSizer)
        self.configPanelLeftSizer.Add(
            self.rbGrass,
            proportion=0,
            flag=wx.LEFT,
            border=10,
        )
        self.configPanelLeftSizer.Add(
            self.rbExternal,
            proportion=0,
            flag=wx.LEFT,
            border=10,
        )
        self.configPanelLeftSizer.Add(
            self.comboBoxProfile,
            proportion=0,
            flag=wx.LEFT | wx.TOP | wx.BOTTOM,
            border=10,
        )
        self.configPanelLeft.SetSizerAndFit(self.configPanelLeftSizer)

        self.leftPanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftPanelSizer)
        self.leftPanelSizer.Add(self.configPanelLeft, proportion=0, flag=wx.EXPAND)
        self.leftPanelSizer.AddSpacer(5)
        self.leftPanelSizer.Add(
            self.MdDataCatalogPanelLeft, proportion=1, flag=wx.EXPAND
        )

        self.Hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.Hsizer, proportion=1, flag=wx.EXPAND)
        self.SetSizer(self.mainSizer)
        self.Hsizer.Add(self.leftPanel, proportion=1, flag=wx.EXPAND)

        self.resizeFrame(300, 0)
        self.Layout()


# ===============================================================================
# DATA CATALOG
# ===============================================================================
class MdDataCatalog(LocationMapTree):
    """Data catalog for selecting GRASS maps for editing"""

    def __init__(self, parent):
        """Test Tree constructor."""
        super(MdDataCatalog, self).__init__(
            parent=parent,
            style=wx.TR_MULTIPLE
            | wx.TR_HIDE_ROOT
            | wx.TR_HAS_BUTTONS
            | wx.TR_FULL_ROW_HIGHLIGHT,
        )

        try:
            global GError

            from core.gcmd import GError
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        try:
            tgis.init(True)
        except tgis.FatalError as e:
            sys.exit(1)
        self.dbif = tgis.SQLDatabaseInterfaceConnection()
        self.dbif.connect()
        self.InitTreeItems()
        self.map = None
        self.mapType = None
        self.baseType = None

    def __del__(self):
        """Close the database interface and stop the messenger and C-interface
        subprocesses.
        """
        if hasattr(self, "dbif") and self.dbif.connected is True:
            self.dbif.close()
        if tgis:
            tgis.stop_subprocesses()

    def InitTreeItems(self):
        """Add locations and layers to the tree"""
        self.rootTmp = self.root
        var = self.AppendItem(self.root, "Spatial maps")
        self.root = var

        gisenv = grass.gisenv()
        location = gisenv["LOCATION_NAME"]
        self.mapset = gisenv["MAPSET"]
        self.initGrassTree(location=location, mapset=self.mapset)
        self.initTemporalTree(location=location, mapset=self.mapset)

    def initGrassTree(self, location, mapset):
        """Add locations, mapsets and layers to the tree."""

        self.ChangeEnvironment(location)

        varloc = self.AppendItem(self.root, location)
        self.AppendItem(varloc, mapset)

        # get list of all maps in location
        maplist = RunCommand(
            "g.list",
            flags="mt",
            type="raster,vector",
            mapset=mapset,
            quiet=True,
            read=True,
        )
        maplist = maplist.splitlines()
        vartype = None
        for ml in maplist:
            # parse
            parts1 = ml.split("/")
            parts2 = parts1[1].split("@")
            mapset = parts2[1]
            mlayer = parts2[0]
            ltype = parts1[0]

            # add mapset
            if self.itemExists(mapset, varloc) is False:
                varmapset = self.AppendItem(varloc, mapset)
            else:
                varmapset = self.getItemByName(mapset, varloc)

            # add type node if not exists
            if varmapset is not None:
                if self.itemExists(ltype, varmapset) is False:
                    vartype = self.AppendItem(varmapset, ltype)

                if vartype is not None:
                    self.AppendItem(vartype, mlayer)

    def initTemporalTree(self, location, mapset):
        varloc = self.AppendItem(self.rootTmp, "Temporal maps")
        tDict = tgis.tlist_grouped("stds", group_type=True, dbif=self.dbif)
        # nested list with '(map, mapset, etype)' items
        allDatasets = [
            [
                [(map, mapset, etype) for map in maps]
                for etype, maps in list(etypesDict.items())
            ]
            for mapset, etypesDict in list(tDict.items())
        ]
        if allDatasets:
            allDatasets = reduce(
                lambda x, y: x + y, reduce(lambda x, y: x + y, allDatasets)
            )
            mapsets = tgis.get_tgis_c_library_interface().available_mapsets()
            allDatasets = [
                i for i in sorted(allDatasets, key=lambda l: mapsets.index(l[1]))
            ]

        loc = location
        varloc = self.AppendItem(varloc, loc)

        self.AppendItem(varloc, mapset)
        # get list of all maps in location
        vartype = None
        env = grass.gisenv()
        mapset = env["MAPSET"]
        try:
            for ml in allDatasets:
                # add mapset
                if ml[1] == mapset:  # chck current mapset
                    it = self.itemExists(ml[1], varloc)
                    if it is False:
                        varmapset = it
                    else:
                        varmapset = self.getItemByName(ml[1], varloc)
                    # add type node if not exists
                    if varmapset is not None:
                        if self.itemExists(ml[2], varmapset) is False:
                            vartype = self.AppendItem(varmapset, ml[2])

                    if vartype is not None:
                        self.AppendItem(vartype, ml[0])

        except Exception as e:
            GError("Initialize of temporal tree catalogue error: < %s >" % e)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChanged)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onChanged)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRClickAllChildren)

    def OnRClickAllChildren(self, evt):
        if not self.IsExpanded(evt.Item):
            self.ExpandAllChildren(evt.Item)
        else:
            self.CollapseAllChildren(evt.Item)

    def isMapExist(self, map, type):
        """Check if the map is in current mapset"""
        types = [
            "raster",
            "vector",
            "stvds",
            "strds",
        ]
        if type in types:
            return True
        else:
            return False

    def onChanged(self, evt=None):
        """
        @var ListOfMapTypeDict: list of dic with maps and map-type values
        @var MapTypeDict: keys= type of map(cell/vector), value=<map name>
        """
        self.ListOfMapTypeDict = list()
        maps = list()
        if evt is not None:
            item = evt.Item
        else:
            item = self.GetSelections()[0]
        name = self.GetItemText(item)
        parentItem = self.GetItemParent(item)
        mapType = self.GetItemText(parentItem)
        if self.GetChildrenCount(item) == 0 and self.isMapExist(
            name, mapType
        ):  # is selected map
            # check temporal selection
            for i in self.GetSelections():
                MapTypeDict = {}
                maps.append(self.GetItemText(i))
                map = self.GetItemText(i)
                mapType = self.GetItemParent(i)
                mapType = self.GetItemText(mapType)

                if mapType == "vect":
                    mapType = "vector"
                elif mapType == "rast":
                    mapType = "raster"

                MapTypeDict[mapType] = map

                self.ListOfMapTypeDict.append(MapTypeDict)
            MAINFRAME.bttEdit.Enable()
            MAINFRAME.bttCreateTemplate.Enable(True)

        else:
            self.Unselect()

        if len(maps) == 0:
            MAINFRAME.bttEdit.Disable()
            MAINFRAME.bttCreateTemplate.Enable(False)

            return
        status = ""
        for map in maps:
            status += map + "  "

        if len(maps) > 1:
            dispatcher.send(
                signal="SET_PROFILE.update", profile="Load custom", multi=True
            )
            MAINFRAME.bttUpdateGRASS.Disable()
            MAINFRAME.bttCreateTemplate.Disable()

        else:
            MAINFRAME.bttCreateTemplate.Enable(True)
            dispatcher.send(signal="SET_PROFILE.update", multi=False)

        dispatcher.send(signal="STATUS_BAR_TEXT.update", text=status)


# ===============================================================================
# NOTEBOOK ON THE RIGHT SIDE-xml browser+validator
# ===============================================================================
class NotebookRight(wx.Notebook):
    """Include pages with xml tree browser and validator of metadata"""

    def __init__(self, parent, path):
        wx.Notebook.__init__(self, parent=parent, id=wx.ID_ANY)
        # first panel
        self.notebookValidator = wx.Panel(self, wx.ID_ANY)
        self.validator = MdValidator(self.notebookValidator)
        self.xmlPath = path
        self.profile = None
        self.buttValidate = wx.Button(
            self.notebookValidator, id=wx.ID_ANY, size=(70, 50), label="validate"
        )

        self.notebook_panel1 = wx.Panel(self, wx.ID_ANY)
        self.tree = TreeBrowser(self.notebook_panel1, self.xmlPath)
        self.buttRefresh = wx.Button(
            self.notebook_panel1, id=wx.ID_ANY, size=(70, 50), label="refresh"
        )

        self.AddPage(self.notebookValidator, "Validator")
        self.AddPage(self.notebook_panel1, "Tree browser")
        # self.AddPage(self.notebook_panel2, "Help")

        self.buttValidate.Bind(wx.EVT_BUTTON, self.validate)
        self.buttRefresh.Bind(wx.EVT_BUTTON, self.onRefreshXmlBrowser)
        self._layout()

    def onActive(self):
        pass

    def onRefreshXmlBrowser(self, evt=None):
        dispatcher.send(signal="REFRESH_TREE_BROWSER.update")

    def refreshXmlBrowser(self, path):
        treeBCK = self.tree
        self.tree = TreeBrowser(self.notebook_panel1, path)
        self.panelSizer1.Replace(treeBCK, self.tree)
        # self.panelSizer1.Add(self.tree, flag=wx.EXPAND, proportion=1)
        self.panelSizer1.Layout()
        treeBCK.Destroy()

    def validate(self, evt):
        self.md = None

        dispatcher.send(signal="NEW_MD.create")
        dispatcher.send(signal="ISO_PROFILE.update")

        self.validator.validate(self.md, self.profile)

    def _layout(self):
        panelSizer0 = wx.BoxSizer(wx.VERTICAL)
        self.notebookValidator.SetSizer(panelSizer0)

        panelSizer0.Add(self.validator, flag=wx.EXPAND, proportion=1)
        panelSizer0.Add(self.buttValidate)

        self.panelSizer1 = wx.BoxSizer(wx.VERTICAL)
        self.notebook_panel1.SetSizer(self.panelSizer1)
        self.panelSizer1.Add(self.tree, flag=wx.EXPAND, proportion=1)
        self.panelSizer1.Add(self.buttRefresh)

        # panelSizer2 = wx.BoxSizer(wx.VERTICAL)
        # self.notebook_panel2.SetSizer(panelSizer2)
        # panelSizer2.Add(self.notebook_panel2,flag=wx.EXPAND, proportion=1)


# ===============================================================================
# HELP
# ===============================================================================


class MDHelp(wx.Panel):
    """
    class MyHtmlPanel inherits wx.Panel and adds a button and HtmlWindow
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.html1 = wx.html.HtmlWindow(self, id=wx.ID_ANY)
        try:
            self.html1.LoadFile("help/help.html")
            # self.html1.LoadPage('http://inspire-geoportal.ec.europa.eu/EUOSME_GEOPORTAL/userguide/eurlex_en.htm')
        except:
            pass

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        self.mainSizer.Add(self.html1, proportion=1, flag=wx.EXPAND)


# ===============================================================================
# TREE EDITOR
# ===============================================================================


class TreeBrowser(wx.TreeCtrl):
    """Filling text tree by xml file.
    @note: to enable editing mode of init xml uncomment blocks below
    """

    def __init__(self, parent, xmlPath=False, xmlEtree=False):
        wx.TreeCtrl.__init__(
            self,
            parent=parent,
            id=wx.ID_ANY,
            style=wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT,
        )
        try:
            global etree

            from lxml import etree
        except ModuleNotFoundError as e:
            msg = e.msg
            grass.fatal(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        tree = self
        if xmlPath:
            xml = etree.parse(xmlPath)
            self.xml = xml.getroot()

            self.root = tree.AddRoot(self.xml.tag)
        else:
            self.xml = xmlEtree
            self.root = xmlEtree.getroot()

        root = self.fillTree()
        self.Expand(root)

        # =======================================================================
        # self.Bind(wx.EVT_CLOSE, self.OnClose)
        # self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEdit)
        # =======================================================================
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRClickAllChildren)

    def fillTree(self):
        root = self.root
        xml = self.xml
        tree = self

        def add(parent, elem):
            for e in elem:
                if str(e).find("<!--") != -1:  # skip comments
                    continue
                tag = etree.QName(e)
                item = tree.AppendItem(parent, tag.localname, data=None)
                if self.GetChildrenCount(item) == 0:
                    self.SetItemBackgroundColour(item, (242, 242, 242))
                if e.text:
                    text = e.text.strip()
                else:
                    text = e.text
                if text:
                    val = tree.AppendItem(item, text)
                    tree.SetItemData(val, e)

                add(item, e)

        add(root, xml)
        return root

    # =========================================================================
    # def OnEdit(self, evt):
    #     elm = self.GetPyData(evt.Item)
    #
    # print evt.Label
    #     if elm is not None:
    #         elm.text = evt.Label
    #         self.xml.write(self.fpath, encoding="UTF-8", xml_declaration=True)
    # self.validate()
    # =========================================================================

    # =========================================================================
    # def OnClose(self, evt):
    #     self.Destroy()
    # =========================================================================

    def OnRClickAllChildren(self, evt):
        if not self.IsExpanded(evt.Item):
            self.ExpandAllChildren(evt.Item)
        else:
            self.CollapseAllChildren(evt.Item)


# ===============================================================================
# INSPIRE VALIDATOR PANEL
# ===============================================================================


class MdValidator(wx.Panel):
    """wx panel of notebook which supports validating two natively implemented profiles"""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.text = wx.TextCtrl(
            parent,
            id=wx.ID_ANY,
            size=(0, 55),
            style=wx.VSCROLL
            | wx.TE_MULTILINE
            | wx.TE_NO_VSCROLL
            | wx.TAB_TRAVERSAL
            | wx.RAISED_BORDER
            | wx.HSCROLL,
        )
        self._layout()

    def _layout(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        self.mainSizer.Add(self.text, proportion=1, flag=wx.EXPAND)

    def validate(self, md, profile):
        """For externally loaded xml file is by default inspire validator"""
        if profile == "INSPIRE" or profile == "Load custom":
            result = mdutil.isnpireValidator(md)
            str1 = "INSPIRE VALIDATOR\n"

        if profile == "GRASS BASIC":
            result = mdutil.grassProfileValidator(md)
            str1 = "GRASS BASIC PROFILE VALIDATOR\n"

        if profile == "TEMPORAL":
            result = mdutil.isnpireValidator(md)
            str1 = "INSPIRE VALIDATOR\n"

        str1 += "Status of validation: " + result["status"] + "\n"
        str1 += "Numbers of errors: " + result["num_of_errors"] + "\n"

        if result["status"] != "succeded":
            str1 += "Errors:\n"
            for item in result["errors"]:
                str1 += "\t" + str(item) + "\n"

        self.text.SetValue(str1)


# ===============================================================================
# CSW
# ===============================================================================
class CswPublisher(CSWConnectionPanel):
    def __init__(self, parent, main):
        super(CswPublisher, self).__init__(parent, main, cswBrowser=False)
        self.publishBtt = wx.Button(self.panelLeft, label="Publish")
        self.configureSizer.Add(40, 10, 1, wx.EXPAND)
        self.configureSizer.Add(self.publishBtt, 0, wx.EXPAND)
        self.publishBtt.SetBackgroundColour((255, 127, 80))


# ----------------------------------------------------------------------


def main():
    global MAINFRAME
    app = wx.App(False)
    MAINFRAME = MdMainFrame()
    app.MainLoop()


if __name__ == "__main__":
    grass.parser()
    main()
