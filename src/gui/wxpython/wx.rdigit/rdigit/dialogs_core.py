import os
import sys
import re
from bisect import bisect

import wx

# import wx.lib.filebrowsebutton as filebrowse
# import wx.lib.mixins.listctrl as listmix
# from wx.lib.newevent import NewEvent

from gui_core.dialogs import ElementDialog

from grass.script import core as grass
from grass.lib import gis as gis
from grass.lib import raster as grast

from core import globalvar
from core.gcmd import GError, RunCommand, GMessage
from gui_core.gselect import (
    ElementSelect,
    LocationSelect,
    MapsetSelect,
    Select,
    OgrTypeSelect,
    GdalSelect,
    MapsetSelect,
)
from gui_core.forms import GUI
from gui_core.widgets import SingleSymbolPanel, EVT_SYMBOL_SELECTION_CHANGED, GListCtrl
from core.utils import GetLayerNameFromCmd, GetValidLayerName
from core.settings import UserSettings, GetDisplayVectSettings
from core.debug import Debug
import ctypes


class NewRasterDialog(ElementDialog):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        title=_("Create new vector map"),
        disableAdd=False,
        showType=False,
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        *kwargs,
    ):
        """!Dialog for creating new vector map

        @param parent parent window
        @param id window id
        @param title window title
        @param disableAdd disable 'add layer' checkbox
        @param showType True to show feature type selector (used for creating new empty OGR layers)
        @param style window style
        @param kwargs other argumentes for ElementDialog

        @return dialog instance
        """
        ElementDialog.__init__(self, parent, title, label=_("Name for new raster map:"))

        self.element = Select(
            parent=self.panel,
            id=wx.ID_ANY,
            size=globalvar.DIALOG_GSELECT_SIZE,
            type="raster",
            mapsets=[
                grass.gisenv()["MAPSET"],
            ],
        )

        # determine output format
        if showType:
            self.ftype = GdalSelect(parent=self, panel=self.panel)
        else:
            self.ftype = None

        self.addbox = wx.CheckBox(
            parent=self.panel,
            label=_("Add created map into layer tree"),
            style=wx.NO_BORDER,
        )
        if disableAdd:
            self.addbox.SetValue(True)
            self.addbox.Enable(False)
        else:
            self.addbox.SetValue(
                UserSettings.Get(group="cmd", key="addNewLayer", subkey="enabled")
            )

        self.PostInit()

        self._layout()
        self.SetMinSize(self.GetSize())

    def OnMapName(self, event):
        """!Name for vector map layer given"""
        self.OnElement(event)

    def _layout(self):
        """!Do layout"""
        self.dataSizer.Add(
            item=self.element, proportion=0, flag=wx.EXPAND | wx.ALL, border=1
        )
        if self.ftype:
            self.dataSizer.AddSpacer(1)
            self.dataSizer.Add(
                item=self.ftype, proportion=0, flag=wx.EXPAND | wx.ALL, border=1
            )

        self.dataSizer.AddSpacer(5)

        self.dataSizer.Add(
            item=self.addbox, proportion=0, flag=wx.EXPAND | wx.ALL, border=1
        )

        self.panel.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def GetName(self, full=False):
        """!Get name of vector map to be created

        @param full True to get fully qualified name
        """
        name = self.GetElement()
        if full:
            if "@" in name:
                return name
            else:
                return name + "@" + grass.gisenv()["MAPSET"]

        return name.split("@", 1)[0]

    def GetKey(self):
        """!Get key column name"""

    def IsChecked(self, key):
        """!Get dialog properties

        @param key window key ('add', 'table')

        @return True/False
        @return None on error
        """
        if key == "add":
            return self.addbox.IsChecked()

        return None

    def GetFeatureType(self):
        """!Get feature type for OGR

        @return feature type as string
        @return None for native format
        """
        if self.ftype:
            return self.ftype.GetType()

        return None


def CreateNewRaster(
    parent, title=_("Create new vector map"), exceptMap=None, disableAdd=False
):
    """!Create new vector map layer

    @param cmd (prog, **kwargs)
    @param title window title
    @param exceptMap list of maps to be excepted
    @param disableAdd disable 'add layer' checkbox

    @return dialog instance
    @return None on error
    """
    vExternalOut = grass.parse_command("r.external.out", flags="p", delimiter=":")

    UsingGDAL = "Not using GDAL" not in vExternalOut

    if not UsingGDAL:
        showType = False
    else:
        showType = True

    dlg = NewRasterDialog(parent, title=title, disableAdd=disableAdd, showType=showType)

    if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        return None

    outmap = dlg.GetName()
    # key    = dlg.GetKey()
    if outmap == exceptMap:
        GError(parent=parent, message=_("Unable to create raster map <%s>.") % outmap)
        dlg.Destroy()
        return None

    if outmap == "":  # should not happen
        dlg.Destroy()
        return None

    if not UsingGDAL:
        listOfRasters = grass.list_grouped("rast")[grass.gisenv()["MAPSET"]]
    else:
        listOfRasters = RunCommand(
            "r.external",
            quiet=True,
            parent=parent,
            read=True,
            flags="l",
            out=outmap,
            source=vExternalOut["directory"],
        ).splitlines()

    if (
        not UserSettings.Get(group="cmd", key="overwrite", subkey="enabled")
        and outmap in listOfRasters
    ):
        dlgOw = wx.MessageDialog(
            parent,
            message=_(
                "Raster map <%s> already exists "
                "in the current mapset. "
                "Do you want to overwrite it?"
            )
            % outmap,
            caption=_("Overwrite?"),
            style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION,
        )
        if dlgOw.ShowModal() == wx.ID_YES:
            overwrite = True
        else:
            dlgOw.Destroy()
            dlg.Destroy()
            return None

    if UserSettings.Get(group="cmd", key="overwrite", subkey="enabled"):
        overwrite = True

    if UsingGDAL:
        # create link for OGR layers
        RunCommand(
            "r.external",
            overwrite=overwrite,
            parent=parent,
            directory=vExternalOut["directory"],
            layer=outmap,
        )

    # return fully qualified map name
    if "@" not in outmap:
        outmap += "@" + grass.gisenv()["MAPSET"]

    # if log:
    #    log.WriteLog(_("New raster map <%s> created") % outmap)
    return dlg
