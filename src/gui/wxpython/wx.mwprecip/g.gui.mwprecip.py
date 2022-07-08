#!/usr/bin/env python


# %module
# % description: The module for processing row data of microwave links to precipitation.
# % keyword: general
# % keyword: GUI
# % keyword: precipitation
# % keyword: microwave
# % keyword: link
# %end

VERSION = 1.3
import sys
import os
import tempfile
import time

import grass.script as grass

from grass.pygrass.utils import set_path

set_path(modulename="g.gui.mwprecip", dirname="etc")
from grass.script.setup import set_gui_path

set_gui_path()

from mw_util import *
from mw3 import *
from core.gcmd import GMessage, GError
from gui_core import gselect
from core.gthread import gThread
from gui_core.widgets import ColorTablesComboBox, PictureComboBox
from core import globalvar
from core.utils import GetColorTables
import wx.lib.scrolledpanel as scrolled
import logging


class DBconn(wx.ScrolledWindow):
    def __init__(self, parent, settings={}):
        wx.ScrolledWindow.__init__(
            self,
            parent,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.HSCROLL | wx.VSCROLL,
        )
        self.SetScrollRate(5, 5)
        self.settings = settings
        self.database = BaseInput(self, label="Name of database")
        self.user = BaseInput(self, label="User name")
        self.passwd = BaseInput(self, label="Password", style=wx.TE_PASSWORD)
        self.host = BaseInput(self, label="Host name")
        self.schema = BaseInput(self, label="Name of schema")
        self.port = BaseInput(self, label="Port")
        # self.saveLoad = SaveLoad(self)
        self.okBtt = wx.Button(self, wx.ID_OK)
        self.okBtt.Bind(wx.EVT_BUTTON, self.saveSettings)
        if len(settings) > 0:
            self.loadSettings()
        self._layout()

    def _layout(self):
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        panelSizer.Add(self.database, flag=wx.EXPAND | wx.ALL, border=5)
        panelSizer.Add(
            self.user, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.passwd, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.host, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.schema, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.port, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )

        panelSizer.Add(0, 10, 0, wx.EXPAND)
        # panelSizer.Add(self.saveLoad, flag=wx.EXPAND)
        panelSizer.Add(self.okBtt, flag=wx.EXPAND | wx.ALL, border=5)

        self.SetSizerAndFit(panelSizer)

    def getSettVal(self, key):
        if self.settings[key] is None:
            return ""
        elif self.settings[key] is "None":
            return ""
        elif self.settings[key] is "":
            return ""
        return self.settings[key]

    def loadSettings(self, sett=None):
        if sett:
            self.settings = sett

        if "database" in self.settings:
            self.database.SetValue(self.getSettVal("database"))
        if "schema" in self.settings:
            self.schema.SetValue(self.getSettVal("schema"))
        if "host" in self.settings:
            self.host.SetValue(self.getSettVal("host"))
        if "user" in self.settings:
            self.user.SetValue(self.getSettVal("user"))
        if "port" in self.settings:
            self.port.SetValue(self.getSettVal("port"))
        if "passwd" in self.settings:
            self.passwd.SetValue(self.getSettVal("passwd"))

    def saveSettings(self, sett=None):
        if sett is not None:
            self.settings = sett
        self.settings["database"] = self.database.GetValue()
        self.settings["schema"] = self.schema.GetValue()
        self.settings["host"] = self.host.GetValue()
        self.settings["user"] = self.user.GetValue()
        self.settings["port"] = self.port.GetValue()
        self.settings["passwd"] = self.passwd.GetValue()

        return self.settings


class PointInterpolationPanel(wx.ScrolledWindow):
    def __init__(self, parent, settings=None):
        wx.ScrolledWindow.__init__(
            self,
            parent,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.HSCROLL | wx.VSCROLL,
        )
        self.SetScrollRate(5, 5)
        self.settings = settings
        self.interpolState = wx.CheckBox(self, label="interpolate points along links")
        self.interpolState.Bind(wx.EVT_CHECKBOX, self.onCheckInterpol)
        self.interpolState.SetValue(False)
        self.rb1 = wx.RadioButton(self, label="Number of points", style=wx.RB_GROUP)
        self.rb2 = wx.RadioButton(self, label="Distance")
        self.val = BaseInput(self, label="Value")

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.interpolState, flag=wx.EXPAND)
        panelSizer.Add(self.rb1, flag=wx.EXPAND)
        panelSizer.Add(self.rb2, flag=wx.EXPAND)
        panelSizer.Add(self.val, flag=wx.EXPAND)
        self.SetSizerAndFit(panelSizer)
        self.onCheckInterpol()

    def onCheckInterpol(self, evt=None):
        if self.interpolState.GetValue():
            self.rb1.Enable()
            self.rb2.Enable()
            self.val.Enable()
        else:
            self.rb1.Disable()
            self.rb2.Disable()
            self.val.Disable()

    def loadSettings(self, sett=None):
        if sett:
            self.settings = sett
        if "pitypeDist" in self.settings:
            self.rb1.SetValue(self.settings["pitypeDist"])
        if "pivalue" in self.settings:
            self.val.SetValue(self.settings["pivalue"])

    def saveSettings(self, settings=None):
        if settings is not None:
            self.settings = settings
        self.settings["pitypeDist"] = self.rb1.GetValue()
        self.settings["pivalue"] = self.val.GetValue()
        return self.settings


class BaselinePanel(wx.ScrolledWindow):
    def __init__(self, parent, settings={}):
        wx.ScrolledWindow.__init__(
            self,
            parent,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.HSCROLL | wx.VSCROLL,
        )
        self.SetScrollRate(5, 5)
        self.settings = settings

        self.noDryWin = wx.RadioButton(
            self, label="Compute without dry window", style=wx.RB_GROUP
        )
        self.dryWin = wx.RadioButton(self, label="Compute from dry windows")
        self.fromFile = wx.RadioButton(self, label="Direct text input")

        self.baselTypeTxt = wx.StaticText(self, label="Select statistic method")
        self.baselType = wx.ComboBox(
            self, id=wx.ID_ANY, value="quantile", choices=["avg", "mode", "quantile"]
        )
        self.baselType.Bind(wx.EVT_ACTIVATE, self.onChangeStatistic)
        self.baselType.Bind(wx.EVT_COMBOBOX, self.onChangeStatistic)
        self.round = BaseInput(
            self, 'Round data to "n" of decimal places'
        )  # TODO MODE disable
        self.quantile = BaseInput(self, "Set quantile in %")  # TODO quantile disable
        self.aw = BaseInput(self, "Antena wetting value")
        self.aw.SetValue("0")
        self.dryInterval = TextInput(self, "Set interval(s) of dry period")
        self.fromFileVal = TextInput(self, "Set baseline values in csv format")
        self.onChangeMethod()
        self.onChangeStatistic()

        self.fromFile.Bind(wx.EVT_RADIOBUTTON, self.onChangeMethod)
        self.dryWin.Bind(wx.EVT_RADIOBUTTON, self.onChangeMethod)
        self.noDryWin.Bind(wx.EVT_RADIOBUTTON, self.onChangeMethod)
        if len(settings) > 0:
            self.loadSettings()

        self._layout()

    def onChangeStatistic(self, evt=None):
        if self.baselType.GetValue() == "avg":
            self.round.Disable()
            self.quantile.Disable()

        if self.baselType.GetValue() == "mode":
            self.round.Enable()
            self.quantile.Disable()
        if self.baselType.GetValue() == "quantile":
            self.round.Disable()
            self.quantile.Enable()

    def loadSettings(self, sett=None):
        if sett is not None:
            self.settings = sett
        if "fromFile" in self.settings:
            self.fromFile.SetValue(self.settings["fromFile"])
        if "dryWin" in self.settings:
            self.dryWin.SetValue(self.settings["dryWin"])
        if "noDryWin" in self.settings:
            self.noDryWin.SetValue(self.settings["noDryWin"])
        if "quantile" in self.settings:
            self.quantile.SetValue(self.settings["quantile"])
        if "baselType" in self.settings:
            self.baselType.SetValue(self.settings["baselType"])
        if "round" in self.settings:
            self.round.SetValue(self.settings["round"])
        if "aw" in self.settings:
            self.aw.SetValue(self.settings["aw"])
        if "dryInterval" in self.settings:
            self.dryInterval.SetPath(self.settings["dryInterval"])
        if "fromFileVal" in self.settings:
            self.fromFileVal.SetPath(self.settings["fromFileVal"])
        self.onChangeMethod()

    def saveSettings(self, evt=None, sett=None):
        if sett:
            self.settings = sett
        self.settings["fromFile"] = self.fromFile.GetValue()
        self.settings["dryWin"] = self.dryWin.GetValue()
        self.settings["noDryWin"] = self.noDryWin.GetValue()

        self.settings["baselType"] = self.baselType.GetValue()
        self.settings["round"] = self.round.GetValue()
        self.settings["quantile"] = self.quantile.GetValue()
        self.settings["aw"] = self.aw.GetValue()
        self.settings["dryInterval"] = self.dryInterval.GetPath()
        self.settings["fromFileVal"] = self.fromFileVal.GetPath()
        return self.settings

    def onChangeMethod(self, evt=None):
        if self.fromFile.GetValue() is True:
            self.baselType.Disable()
            self.round.Disable()
            self.aw.Disable()
            self.dryInterval.Disable()
            self.quantile.Disable()
            self.fromFileVal.Enable()

        elif self.dryWin.GetValue() is True:
            self.baselType.Enable()
            self.round.Enable()
            self.aw.Enable()
            self.quantile.Enable()
            self.dryInterval.Enable()
            self.fromFileVal.Disable()

        elif self.noDryWin.GetValue() is True:
            self.baselType.Enable()
            self.round.Enable()
            self.aw.Enable()
            self.quantile.Enable()
            self.dryInterval.Disable()
            self.fromFileVal.Disable()
        self.onChangeStatistic()

    def _layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.noDryWin, flag=wx.EXPAND)
        sizer.Add(self.dryWin, flag=wx.EXPAND)
        sizer.Add(self.fromFile, flag=wx.EXPAND)
        sizer.Add(self.baselTypeTxt, flag=wx.EXPAND)
        sizer.Add(self.baselType, flag=wx.EXPAND)
        sizer.Add(self.round, flag=wx.EXPAND)
        sizer.Add(self.quantile, flag=wx.EXPAND)
        sizer.Add(self.aw, flag=wx.EXPAND)
        sizer.Add(self.dryInterval, flag=wx.EXPAND)
        sizer.Add(width=0, height=10, proportion=0, flag=wx.EXPAND)
        sizer.Add(self.fromFileVal, flag=wx.EXPAND)
        sizer.Add(width=0, height=10, proportion=0, flag=wx.EXPAND)
        # sizer.Add(self.SLpanel, flag=wx.EXPAND)
        # sizer.Add(self.okBtt, flag=wx.EXPAND)
        self.SetSizer(sizer)


"""
class DataMgrRG(wx.Panel):
    def __init__(self, parent, settings=None):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.sett = settings
"""


class DataMgrMW(wx.ScrolledWindow):
    def __init__(self, parent, settings={}):
        wx.ScrolledWindow.__init__(
            self,
            parent,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.HSCROLL | wx.VSCROLL,
        )
        self.SetScrollRate(5, 5)
        self.settings = settings

        self.stBoxTWIN = wx.StaticBox(self, wx.ID_ANY, "Time windows MW")

        # =================DATA=========================
        self.linksAll = wx.RadioButton(self, label="All", style=wx.RB_GROUP)
        self.linksOnly = wx.RadioButton(self, label="Use links")
        self.linksIngnore = wx.RadioButton(self, label="Ignore links")
        self.linksAll.Bind(wx.EVT_RADIOBUTTON, self.refreshLinkSet)
        self.linksIngnore.Bind(wx.EVT_RADIOBUTTON, self.refreshLinkSet)
        self.linksOnly.Bind(wx.EVT_RADIOBUTTON, self.refreshLinkSet)
        self.vectorMap = wx.RadioButton(self, label="Vector map")
        self.vectorMap.Bind(wx.EVT_RADIOBUTTON, self.refreshLinkSet)

        # self.links = BaseInput(self,'Set links according to radio above',True)
        self.links = BaseInput(self, "Set links according to radio above")
        self.mapLabel = wx.StaticText(self, label="Select vector map")
        self.map = gselect.Select(self, type="vector", multiple=False)

        self.start = BaseInput(self, label="Start time")
        self.end = BaseInput(self, label="End time")
        self.getStartBtt = wx.Button(self, label="Get min")
        self.getEndBtt = wx.Button(self, label="Get max")
        self.sumStep = wx.ComboBox(
            self, id=wx.ID_ANY, value="minute", choices=["minute", "hour", "day"]
        )

        self.stBoxGauge = wx.StaticBox(self, wx.ID_ANY, "Rain gauge")
        self.inpRainGauge = FileInput(self, "Select folder with raingauges data")
        self.inpRainGauge.pathInput.Bind(wx.EVT_TEXT, self.disableLinksInp)
        # self.sb1 = wx.StaticBox(self, wx.ID_ANY, 'Baseline')
        # self.type = self.rb1 = wx.RadioButton(self, label='Number of points', style=wx.RB_GROUP)
        if len(settings) > 0:
            self.loadSettings()
        self._layout()

    def disableLinksInp(self, evt=None):
        if self.inpRainGauge.GetPath() is not None:
            self.linksAll.Disable()
            self.linksOnly.Disable()
            self.linksIngnore.Disable()
            self.links.Disable()
            self.vectorMap.Disable()
            self.mapLabel.Disable()
            self.map.Disable()
        else:
            self.linksAll.Enable()
            self.linksOnly.Enable()
            self.linksIngnore.Enable()
            self.vectorMap.Enable()
            self.mapLabel.Enable()
            self.map.Enable()

            if not self.linksAll.GetValue():
                self.links.Enable()

    def refreshLinkSet(self, evt=None):
        if self.linksAll.GetValue():
            self.links.Disable()
        else:
            self.links.Enable()

        if self.vectorMap.GetValue():
            self.links.Hide()

            self.mapLabel.Show()
            self.map.Show()

        else:
            self.links.Show()
            self.mapLabel.Hide()
            self.map.Hide()

        self.Fit()
        self.Parent.Fit()

    def saveSettings(self, evt=None, sett=None):
        if sett:
            self.settings = sett
        if self.vectorMap.GetValue():
            self.settings["linksMap"] = self.map.GetValue()
        else:
            self.settings["linksMap"] = None

        self.settings["linksOnly"] = self.linksOnly.GetValue()
        self.settings["linksIngnore"] = self.linksIngnore.GetValue()

        self.settings["links"] = self.links.GetValue()
        self.settings["start"] = self.start.GetValue()
        self.settings["end"] = self.end.GetValue()
        self.settings["sumStep"] = self.sumStep.GetValue()
        self.settings["inpRainGauge"] = self.inpRainGauge.GetPath()
        return self.settings

    def loadSettings(self, sett=None):
        if sett:
            self.settings = sett
        if "linksMap" in self.settings:
            self.map.SetValue(self.settings["linksMap"])
        if "linksOnly" in self.settings:
            self.linksOnly.SetValue(self.settings["linksOnly"])
        if "linksIgnore" in self.settings:
            self.linksIngnore.SetValue(self.settings["linksIngnore"])
        if "links" in self.settings:
            self.links.SetValue(self.settings["links"])
        if "start" in self.settings:
            self.start.SetValue(self.settings["start"])
        if "end" in self.settings:
            self.end.SetValue(self.settings["end"])
        if "sumStep" in self.settings:
            self.sumStep.SetValue(self.settings["sumStep"])
        if "inpRainGauge" in self.settings:
            self.inpRainGauge.SetPath(self.settings["inpRainGauge"])

    def _layout(self):
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizerAndFit(panelSizer)

        linksSizer = wx.BoxSizer(wx.HORIZONTAL)
        linksSizer.Add(self.linksAll, flag=wx.EXPAND, proportion=1)
        linksSizer.Add(self.linksOnly, flag=wx.EXPAND, proportion=1)
        linksSizer.Add(self.linksIngnore, flag=wx.EXPAND, proportion=1)
        linksSizer.Add(self.vectorMap, flag=wx.EXPAND, proportion=1)

        stBoxSizerTWIN = wx.StaticBoxSizer(self.stBoxTWIN, orient=wx.VERTICAL)
        stBoxSizerTWIN.Add(linksSizer, flag=wx.EXPAND, proportion=1)
        stBoxSizerTWIN.Add(self.links, flag=wx.EXPAND, proportion=1)
        stBoxSizerTWIN.Add(self.mapLabel, flag=wx.EXPAND)
        stBoxSizerTWIN.Add(self.map, flag=wx.EXPAND, proportion=1)
        stBoxSizerTWIN.Add(width=5, height=5, proportion=1, flag=wx.EXPAND)
        stBoxSizerTWIN.Add(self.start, flag=wx.EXPAND, proportion=1)
        stBoxSizerTWIN.Add(self.getStartBtt)
        stBoxSizerTWIN.Add(width=5, height=5, proportion=1, flag=wx.EXPAND)
        stBoxSizerTWIN.Add(self.end, flag=wx.EXPAND, proportion=1)
        stBoxSizerTWIN.Add(self.getEndBtt)
        stBoxSizerTWIN.Add(width=5, height=5, proportion=1, flag=wx.EXPAND)
        stBoxSizerTWIN.Add(wx.StaticText(self, id=wx.ID_ANY, label="Time increment"))
        stBoxSizerTWIN.Add(self.sumStep, flag=wx.EXPAND)

        gaugeSizer = wx.BoxSizer(wx.HORIZONTAL)
        gaugeSizer.Add(self.inpRainGauge, flag=wx.EXPAND, proportion=1)

        stBoxSizerRGAUGE = wx.StaticBoxSizer(self.stBoxGauge, orient=wx.VERTICAL)
        stBoxSizerRGAUGE.Add(gaugeSizer, flag=wx.EXPAND, proportion=1)

        panelSizer.Add(stBoxSizerTWIN, flag=wx.EXPAND)
        panelSizer.Add(stBoxSizerRGAUGE, flag=wx.EXPAND)

        self.SetSizerAndFit(panelSizer)
        self.refreshLinkSet()


class GrassLayers(wx.Panel):
    def __init__(self, parent, settings={}):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.settings = settings
        self.colorRules = TextInput(self, label="Color table")
        self.colorsName = ColorTablesComboBox(
            parent=self, size=globalvar.DIALOG_COMBOBOX_SIZE, choices=GetColorTables()
        )
        self.layout()

    def loadSettings(self, sett=None):
        if sett:
            self.settings = sett
        if "colorRules" in self.settings:
            self.colorRules.SetValue(self.settings["colorRules"])
        if "colorName" in self.settings:
            self.colorsName.SetValue(self.settings["colorName"])

    def saveSettings(self, evt=None, sett=None):
        if sett:
            self.settings = sett
        self.settings["colorName"] = self.colorsName.GetValue()
        self.settings["colorRules"] = self.colorRules.GetPath()
        return self.settings

    def layout(self):
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.colorsName, flag=wx.EXPAND)
        panelSizer.Add(self.colorRules, flag=wx.EXPAND)
        self.SetSizerAndFit(panelSizer)


class GeometryPanel(wx.Panel):
    def __init__(self, parent, settings={}):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.settings = settings
        self.label = wx.StaticText(self, label="Create vector geometry map")
        self.linksExp = wx.RadioButton(self, label="Links", style=wx.RB_GROUP)
        self.nodesExp = wx.RadioButton(self, label="Nodes")
        self.mapName = BaseInput(self, "Map name")
        self.bttExport = wx.Button(self, label="Export")

        self.layout()

    def layout(self):
        panelSizer = wx.BoxSizer(wx.VERTICAL)

        panelSizer.Add(self.label, flag=wx.EXPAND | wx.ALL, border=5)
        panelSizer.Add(
            self.linksExp, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.nodesExp, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(
            self.mapName, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=5
        )
        panelSizer.Add(self.bttExport, flag=wx.EXPAND | wx.ALL, border=5)
        self.SetSizerAndFit(panelSizer)

    def GetOptions(self):
        if self.linksExp.GetValue():
            type = "links"
        else:
            type = "nodes"
        return type, self.mapName.GetValue()


class ExportData(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.chkid = wx.CheckBox(self, label="linkid")
        self.chkid.SetValue(True)
        self.chkid.Disable()
        self.chktime = wx.CheckBox(self, label="time")
        self.chktime.SetValue(True)
        self.chktime.Disable()

        self.chkprecip = wx.CheckBox(self, label="precipitation")
        self.chkrx = wx.CheckBox(self, label="rx")
        self.chktx = wx.CheckBox(self, label="tx")
        self.chkfreq = wx.CheckBox(self, label="frequency")
        self.chkpol = wx.CheckBox(self, label="polarization")
        self.okBtt = wx.Button(self, label="export")
        self.layout()
        self.chkprecip.Bind(wx.EVT_CHECKBOX, self.onChckPrec)

    def onChckPrec(self, evt):
        if self.chkprecip.GetValue():
            self.chkrx.Disable()
            self.chktx.Disable()
            self.chkfreq.Disable()
            self.chkpol.Disable()

            self.chkrx.SetValue(False)
            self.chktx.SetValue(False)
            self.chkfreq.SetValue(False)
            self.chkpol.SetValue(False)
        else:
            self.chkrx.Enable()
            self.chktx.Enable()
            self.chkfreq.Enable()
            self.chkpol.Enable()

    def layout(self):
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        mainSizer.Add(self.chkid, wx.EXPAND)
        mainSizer.Add(self.chktime, wx.EXPAND)
        mainSizer.Add(self.chkprecip, wx.EXPAND)
        mainSizer.Add(self.chkrx, wx.EXPAND)
        mainSizer.Add(self.chktx, wx.EXPAND)
        mainSizer.Add(self.chkfreq, wx.EXPAND)
        mainSizer.Add(self.chkpol, wx.EXPAND)
        mainSizer.Add(self.okBtt, wx.EXPAND)

        self.SetSizerAndFit(mainSizer)


class MWMainFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, style=wx.DEFAULT_FRAME_STYLE)
        self.SetIcon(
            wx.Icon(os.path.join(globalvar.ICONDIR, "grass.ico"), wx.BITMAP_TYPE_ICO)
        )

        # logging.getLogger().addHandler(logging.StreamHandler())
        self.initConsoleLogger()
        self.worker = None
        self.logger = None
        context = StaticContext()
        self.workPath = context.getTmpPath()
        self.initWorkingFoldrs()
        self.settings = {}
        self.settingsLst = []
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.mainPanel = wx.Panel(self, id=wx.ID_ANY)
        self.loggerCurrentProfile = ""
        menubar = wx.MenuBar()
        settMenu = wx.Menu()
        databaseItem = settMenu.Append(wx.ID_ANY, "Database", "Set database")
        geometry = settMenu.Append(wx.ID_ANY, "Geometry", "Create vector geometry")
        about = settMenu.Append(wx.ID_ANY, "About", "About")

        workingPath = settMenu.Append(wx.ID_ANY, "Working Dir", "Set working directory")
        quitItem = settMenu.Append(wx.ID_EXIT, "Quit", "Quit application")
        menubar.Append(settMenu, "&Menu")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.onQuit, quitItem)
        self.Bind(wx.EVT_MENU, self.onSetDatabase, databaseItem)
        self.Bind(wx.EVT_MENU, self.onSetWorkPath, workingPath)
        self.Bind(wx.EVT_MENU, self.onAbout, about)

        # self.Bind(wx.EVT_MENU, self.onSetBaseline, baselineItem)
        self.Bind(wx.EVT_MENU, self.onSetGeometry, geometry)

        # def initNotebook(self):

        self.ntb = wx.Notebook(self.mainPanel, id=wx.ID_ANY)
        self.dataMgrMW = DataMgrMW(self.ntb)
        self.dataMgrMW.getEndBtt.Bind(wx.EVT_BUTTON, self.getMaxTime)
        self.dataMgrMW.getStartBtt.Bind(wx.EVT_BUTTON, self.getMinTime)

        self.baselinePnl = BaselinePanel(self.ntb)

        # self.dataMgrRG = DataMgrMW(self.ntb )
        # self.pointInter = PointInterpolationPanel(self.ntb)
        self.ntb.AddPage(page=self.dataMgrMW, text="MW data")
        self.ntb.AddPage(page=self.baselinePnl, text="Baseline")
        # self.ntb.AddPage(page=self.dataMgrRG, text='RG data')
        # self.ntb.AddPage(page=self.pointInter, text='Points Interpolation')

        self.grassLayers = GrassLayers(self.ntb, self.settings)
        self.ntb.AddPage(page=self.grassLayers, text="Colors")

        # def initProfileSett(self):
        self.loadScheme = wx.StaticText(
            self.mainPanel, label="Load settings", id=wx.ID_ANY
        )
        self.profilSelection = wx.ComboBox(self.mainPanel, style=wx.CB_READONLY)
        self.schema = BaseInput(self.mainPanel, "Name of new working profile")
        self.schema.text.Bind(wx.EVT_TEXT, self.OnSchemeTxtChange)
        self.newScheme = wx.Button(self.mainPanel, label="Save profile")
        self.newScheme.Bind(wx.EVT_BUTTON, self.OnSaveSettings)
        self.newScheme.Disable()
        self.profilSelection.Bind(wx.EVT_COMBOBOX, self.OnLoadSettings)

        # def initRunBtt(self):
        self.computeBtt = wx.Button(self.mainPanel, label="Compute")
        self.computeBtt.Disable()
        self.exportDataBtt = wx.Button(self.mainPanel, label="Export data")
        self.computeBtt.Bind(wx.EVT_BUTTON, self.startProcess)
        self.exportDataBtt.Disable()
        self.exportDataBtt.Bind(wx.EVT_BUTTON, self.exportData)

        self.findProject()
        self.layout()

    def initFileLogger(self, path):
        fileHandler = logging.FileHandler(filename=path, mode="w")
        fileHandler.setLevel(logging.INFO)
        fileFormater = logging.Formatter(
            "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        )
        fileHandler.setFormatter(fileFormater)
        logging.getLogger("").addHandler(fileHandler)
        logging.getLogger("mwprecip.GUI")

    def initConsoleLogger(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
        ch.setFormatter(formatter)
        root.addHandler(ch)

    def onAbout(self, evt):
        dir = os.path.dirname(os.path.realpath(__file__))
        GMessage(
            "wx.mwprecip\n\nVersion: {} \nDirectory: {}".format(
                VERSION,
                dir,
            ),
            self,
        )

    def getMinTime(self, evt=None):
        if not self.OnSaveSettings(toFile=False):
            return
        interface = Gui2Model(
            self, self.settings, self.workPath
        )  # TODO optimalize init
        if interface.checkConn():
            interface.initConnection()
            self.dataMgrMW.start.SetValue(interface.dbConn.minTimestamp())

    def getMaxTime(self, evt=None):
        if not self.OnSaveSettings(toFile=False):
            return
        interface = Gui2Model(self, self.settings, self.workPath)
        if interface.checkConn():
            interface.initConnection()
            self.dataMgrMW.end.SetValue(interface.dbConn.maxTimestamp())

    def GetConnection(self):
        if not self.OnSaveSettings(toFile=False):
            return
        interface = Gui2Model(self, self.settings, self.workPath)
        if interface.checkConn():
            interface.initConnection()
            return interface.dbConn

    def OnSchemeTxtChange(self, evt=None):
        if self.schema.GetValue() is not None:
            self.newScheme.Enable()
            self.computeBtt.Enable()
            self.exportDataBtt.Enable()
        else:
            self.newScheme.Disable()
            self.computeBtt.Disable()
            self.exportDataBtt.Disable()

    def OnLoadSettings(self, evt=None):
        currSelId = self.profilSelection.GetSelection()
        self.schema.SetValue(self.profilSelection.GetValue())
        self.settings = self.settingsLst[currSelId]

        try:
            self.dataMgrMW.loadSettings(self.settings)
        except:
            pass
        # try:
        #    self.dataMgrRG.loadSettings(self.settings)
        # except:
        #    pass
        try:
            self.databasePnl.loadSettings(self.settings)
        except:
            pass
        try:
            self.baselinePnl.loadSettings(self.settings)
        except:
            pass
        try:
            self.grassLayers.loadSettings(self.settings)
        except:
            pass

    def OnSaveSettings(self, evt=None, toFile=True):
        try:
            self.settings = self.dataMgrMW.saveSettings(sett=self.settings)
        except:
            pass
        try:
            self.settings = self.databasePnl.saveSettings(sett=self.settings)
        except:
            pass
        try:
            self.settings = self.baselinePnl.saveSettings(sett=self.settings)
        except:
            pass
        try:
            self.settings = self.grassLayers.saveSettings(sett=self.settings)
        except:
            pass

        self.settings["workSchema"] = self.profilSelection.GetValue()
        if self.schema.GetValue() is not None:
            self.settings["workSchema"] = self.schema.GetValue()
        else:
            GMessage("Set working profile")
            return False
        tmpPath = os.path.join(self.workPath, "save", self.settings["workSchema"])

        if toFile:
            saveDict(tmpPath, self.settings)

        self.findProject()
        return True

    def initWorkingFoldrs(self):
        savePath = os.path.join(self.workPath, "save")
        if not os.path.exists(savePath):
            os.makedirs(savePath)

    def findProject(self):
        try:
            projectDir = os.path.join(self.workPath, "save")
        except:
            GMessage('Cannot find "save" folder', self)
            return
        filePathList = getFilesInFoldr(projectDir, True)
        if filePathList != 0:
            self.profilSelection.Clear()
            for path in filePathList:
                tmpDict = readDict(path)
                self.settingsLst.append(tmpDict)
                self.profilSelection.Append(str(tmpDict["workSchema"]))
        else:
            return

    def onSetGeometry(self, evt):
        self.geDialog = wx.Dialog(
            self,
            id=wx.ID_ANY,
            title="Geometry creator",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.DefaultSize,
            pos=wx.DefaultPosition,
        )

        if self.settings:
            self.geometryPnl = GeometryPanel(self.geDialog, self.settings)
        else:
            self.geometryPnl = GeometryPanel(self.geDialog)

        self.geometryPnl.bttExport.Bind(wx.EVT_BUTTON, self._onSetGeomDLG)
        dbSizer = wx.BoxSizer(wx.VERTICAL)
        dbSizer.Add(self.geometryPnl, flag=wx.EXPAND)
        self.geDialog.SetSizer(dbSizer)
        self.geDialog.DoLayoutAdaptation()
        self.geDialog.SetSize((300, -1))
        self.geDialog.ShowModal()
        self.geDialog.Destroy()

    def _onSetGeomDLG(self, evt):
        type, name = self.geometryPnl.GetOptions()
        if name == "":
            GMessage("Please set name of map", self)
        else:
            self.createGeometry(type, name)
            # self.addMapToLay()#TODO giface

    def addMapToLay(self, map):
        # TODO giface
        """

        tree = self._giface.GetLayerTree()
        if tree:
            tree.AddLayer(ltype='vector', lname=map,
                          lcmd=['d.vect', 'map=%s' % map],
                          lchecked=True)
        """
        pass

    def onSetWorkPath(self, evt):
        dlg = wx.DirDialog(
            self,
            message="Select working directory",
            defaultPath=self.workPath,
            style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON,
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.workPath = dlg.GetPath()
            dlg.Destroy()
            self.initWorkingFoldrs()
            self.profilSelection.Clear()
            self.settingsLst = []
            self.findProject()

        GMessage("Working path destination: %s" % self.workPath, self)

    def onSetDatabase(self, evt):
        self.dbDialog = wx.Dialog(
            self,
            id=wx.ID_ANY,
            title="DB connection settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=(300, -1),
            pos=wx.DefaultPosition,
        )

        if self.settings:
            self.databasePnl = DBconn(self.dbDialog, self.settings)
        else:
            self.databasePnl = DBconn(self.dbDialog)

        self.databasePnl.okBtt.Bind(wx.EVT_BUTTON, self._onSetDatabaseDLG)
        dbSizer = wx.BoxSizer(wx.VERTICAL)
        dbSizer.Add(self.databasePnl, flag=wx.EXPAND)
        self.dbDialog.SetSizer(dbSizer)
        self.dbDialog.DoLayoutAdaptation()
        self.dbDialog.SetMinSize((300, -1))
        self.dbDialog.ShowModal()
        self.dbDialog.Destroy()

    def _onSetDatabaseDLG(self, evt):
        self.settings = self.databasePnl.saveSettings()
        # print self.settings
        self.dbDialog.Destroy()

    def createGeometry(self, type, name):
        interface = Gui2Model(self, self.settings, self.workPath)
        if interface.checkConn():
            interface.initConnection()
            interface.initVectorGrass(type=type, name=name)

    def exportData(self, evt):
        self.exportDialog = wx.Dialog(
            self,
            id=wx.ID_ANY,
            title="Database connection settings",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
            size=wx.DefaultSize,
            pos=wx.DefaultPosition,
        )

        self.exportDialog.SetSize((500, 500))
        self.exportDMgr = ExportData(self.exportDialog)

        self.exportDMgr.okBtt.Bind(wx.EVT_BUTTON, self._onExport)
        dbSizer = wx.BoxSizer(wx.VERTICAL)
        dbSizer.Add(self.exportDMgr, flag=wx.EXPAND)
        self.exportDialog.SetSizer(dbSizer)
        self.exportDialog.SetBestFittingSize()
        self.exportDialog.ShowModal()
        self.exportDialog.Destroy()

    def _onExport(self, evt=None):
        path = OnSaveAs(self)
        if not self.OnSaveSettings(toFile=False):
            return
        if (
            not self.exportDMgr.chkprecip.GetValue()
        ):  # if export only data from sql without computing
            attrTmp1 = ["link.linkid"]
            attrTmp2 = []
            attrTmp3 = []
            if self.exportDMgr.chkfreq.GetValue():
                attrTmp1.append("link.frequency")
            if self.exportDMgr.chkpol.GetValue():
                attrTmp1.append("link.polarization")

            attrTmp2.append("record.time")
            if self.exportDMgr.chkrx.GetValue():
                attrTmp2.append("record.rxpower")
            if self.exportDMgr.chktx.GetValue():
                attrTmp2.append("record.txpower")

            attrTmp4 = "WHERE"
            if len(attrTmp1) > 0:
                attrTmp3.append("link")
            if len(attrTmp2) > 0:
                attrTmp3.append("record")

            if len(attrTmp1) > 0 and len(attrTmp2) > 0:
                attrTmp4 = "WHERE link.linkid=record.linkid AND"
                attrTmp0 = attrTmp1 + attrTmp2
                attrTmp0 = ",".join(attrTmp0)
            elif len(attrTmp1) > 0:
                attrTmp0 = ",".join(attrTmp1)
            elif len(attrTmp2) > 0:
                attrTmp0 = ",".join(attrTmp2)

            if len(attrTmp3) > 1:
                attrTmp3 = ",".join(attrTmp3)
            else:
                attrTmp3 = attrTmp3[0]

            sql = "SELECT %s FROM %s %s record.time>'%s' and record.time< '%s'  " % (
                attrTmp0,
                attrTmp3,
                attrTmp4,
                self.dataMgrMW.start.GetValue(),
                self.dataMgrMW.end.GetValue(),
            )
            conn = self.GetConnection()
            res = conn.connection.executeSql(sql, True, True)
            lines = ""
            for r in res:
                lines += (
                    str(r)[1:][:-1].replace("datetime.datetime", "").replace("'", "")
                    + "\n"
                )
            io0 = open(path, "w+")
            io0.writelines(lines)
            io0.close()
            GMessage("Data exported<%s>" % path, self)

        else:
            exportData = {"getData": True, "dataOnly": False}
            if YesNo(self, "Export data only?"):
                exportData["dataOnly"] = True
            self.settings["dataExport"] = exportData
            # if rain gauges
            if self.dataMgrMW.inpRainGauge.GetPath() is not None:
                self.settings["IDtype"] = "gaugeid"
            else:
                self.settings["IDtype"] = "linkid"

            interface = Gui2Model(self, self.settings, self.workPath)
            if not interface.initConnection():
                return
            interface.initVectorGrass()
            interface.initTimeWinMW()
            interface.initBaseline()
            interface.Run()
            if interface.connStatus:
                conn = interface.dbConn
                sql = "SELECT * FROM %s.%s" % (
                    interface.dbConn.schema,
                    interface.dbConn.computedPrecip,
                )
                res = conn.connection.executeSql(sql, True, True)

                lines = ""
                for r in res:
                    lines += str(r)[1:][:-1] + "\n"

                print(conn.pathworkSchemaDir)
                io0 = open(path, "w+")
                io0.writelines(lines)
                io0.close()
                os.remove(os.path.join(interface.dbConn.pathworkSchemaDir, "precip"))
                GMessage("Data exported<%s>" % path, self)
            else:
                GMessage("Data not exported", self)

        self.exportDialog.Destroy()

    def startProcess(self, evt=None):
        profilePath = os.path.join(self.workPath, "logs")
        if not os.path.exists(profilePath):
            os.mkdir(profilePath)
        self.initFileLogger(
            os.path.join(profilePath, "%s.log" % self.settings["workSchema"])
        )
        print("file logger initialized")

        self.thread = gThread()
        self.thread.Run(callable=self.runComp, ondone=self.onFinish)
        self.computeBtt.Enable()
        self.exportDataBtt.Enable()

    def runComp(self, evt=None):
        self.computeBtt.Disable()
        self.exportDataBtt.Disable()
        self.OnSaveSettings(toFile=False)

        exportData = {"getData": False, "dataOnly": False}
        self.settings["dataExport"] = exportData

        if self.dataMgrMW.inpRainGauge.GetPath() is not None:
            self.settings["IDtype"] = "gaugeid"
        else:
            self.settings["IDtype"] = "linkid"

        self.worker = Gui2Model(self, self.settings, self.workPath)
        if self.worker.checkConn():
            if not self.worker.initConnection():
                return
            self.worker.initVectorGrass()

            self.worker.initTimeWinMW()
            self.worker.initBaseline()
            self.worker.Run()

    def onFinish(self, evt):
        # self.computeBtt.SetLabel('Compute')
        self.computeBtt.Enable()
        self.exportDataBtt.Enable()
        GMessage("Finish", self)

    def layout(self):
        self.panelSizer.Add(self.loadScheme, flag=wx.EXPAND)
        self.panelSizer.Add(self.profilSelection, flag=wx.EXPAND)
        self.panelSizer.Add(self.schema, flag=wx.EXPAND)
        self.panelSizer.Add(self.newScheme, flag=wx.EXPAND)

        self.panelSizer.Add(width=0, height=10, proportion=0, flag=wx.EXPAND)
        self.panelSizer.Add(self.ntb, flag=wx.EXPAND)

        self.panelSizer.Add(width=0, height=10, proportion=0, flag=wx.EXPAND)
        self.panelSizer.Add(self.computeBtt, flag=wx.EXPAND)
        self.panelSizer.Add(self.exportDataBtt, flag=wx.EXPAND)

        self.mainSizer.Add(self.mainPanel, flag=wx.EXPAND)
        self.mainPanel.SetSizerAndFit(self.panelSizer)
        self.SetSizerAndFit(self.mainSizer)
        self.Fit()

    def onQuit(self, e):
        self.Close()


class Gui2Model:
    def __init__(self, wxParent, settings, path):
        self.settings = settings
        self.dbConn = None
        self.connStatus = False
        self.conninfo = None
        self.workPath = path

    def checkConn(self):
        try:
            self.conninfo = {"name": self.settings["database"]}
            return True
        except:
            GMessage("name of database is missing")
            self.connStatus = False
            return False

    def initConnection(self, info=False):
        if self.conninfo is None:
            self.checkConn()
        conninfo = self.conninfo

        if "workSchema" in self.settings:
            conninfo["workSchema"] = self.settings["workSchema"]
        if "schema" in self.settings:
            conninfo["dataSchema"] = self.settings["schema"]
        if "host" in self.settings:
            conninfo["host"] = self.settings["host"]
        if "user" in self.settings:
            conninfo["user"] = self.settings["user"]
        if "port" in self.settings:
            conninfo["port"] = self.settings["port"]
        if "passwd" in self.settings:
            conninfo["password"] = self.settings["passwd"]

        conninfo["workPath"] = self.workPath

        if not info:  # prepare for computing
            self.dbConn = Database(**conninfo)
            self.connStatus = True
            self.dbConn.firstPreparation()
            self.dbConn.prepareDB()
            self.dbConn.prepareDir()
            return self.dbConn
        else:  # just get info about curr database state
            self.dbConn = Database(**conninfo)
            self.connStatus = True
            return self.dbConn

    def initVectorGrass(self, type=None, name=None):
        convertor = VectorLoader(self.dbConn)
        if name is not None:
            self.dbConn.nodeVecMapName = name
            self.dbConn.linkVecMapName = name

        if type == "nodes" or type is None:
            # create native vector map(nodes)
            pointsSQL = convertor.selectNodes()
            # print pointsSQL
            pointsASCII = convertor.getASCIInodes(pointsSQL)
            convertor.grass_vinASCII(pointsASCII, self.dbConn.nodeVecMapName)
        # create native vector map(links)
        if type == "links" or type is None:
            linksSQL = convertor.selectLinks()
            linksASCII = convertor.getASCIIlinks(linksSQL)
            convertor.grass_vinASCII(linksASCII, self.dbConn.linkVecMapName)

    def initPInterpolation(self):
        run = 0
        if "pitypeDist" in self.settings:
            pitypeDist = self.settings["pitypeDist"]
            run += 1
        if "pivalue" in self.settings:
            pivalue = self.settings["pivalue"]
            run += 1
        else:
            self.errMsg("Missing value for interpolating points along lines")
        if run == 2:
            PointInterpolation(self.dbConn, pivalue, pitypeDist)

    def initBaseline(self):
        baselInit = {}
        if "baselType" in self.settings:
            baselInit["statFce"] = self.settings["baselType"]
        if "quantile" in self.settings:
            baselInit["quantile"] = self.settings["quantile"]
        if "round" in self.settings:
            baselInit["roundMode"] = self.settings["round"]
        if "aw" in self.settings:
            baselInit["aw"] = self.settings["aw"]

        methodSel = False

        if "fromFile" in self.settings:
            if self.settings["fromFile"]:
                baselInit["type"] = "values"
                if "fromFileVal" in self.settings:
                    baselInit["pathToFile"] = self.settings["fromFileVal"]
                    methodSel = True
                else:
                    self.errMsg("Path to file with baseline values is not defined")

        if "dryWin" in self.settings:
            if self.settings["dryWin"]:
                baselInit["type"] = "fromDryWin"
                if "dryInterval" in self.settings:
                    baselInit["pathToFile"] = self.settings["dryInterval"]
                    methodSel = True
                else:
                    self.errMsg("Dry interval is not defined")

        if "noDryWin" in self.settings:
            if self.settings["noDryWin"]:
                baselInit["type"] = "noDryWin"
                methodSel = True

        if not methodSel:
            self.errMsg("Baseline method is not selected")

        self.baseline = Baseline(**baselInit)

    def initTimeWinMW(self):
        winInit = {}
        if "linksOnly" in self.settings:
            winInit["linksOnly"] = self.settings["linksOnly"]

        if "linksMap" in self.settings:
            winInit["linksMap"] = self.settings["linksMap"]
        if "linksIngnore" in self.settings:
            winInit["linksIgnored"] = self.settings["linksIngnore"]
        if "links" in self.settings:
            winInit["links"] = self.settings["links"]
        if "start" in self.settings:
            winInit["startTime"] = self.settings["start"]
        if "end" in self.settings:
            winInit["endTime"] = self.settings["end"]
        if "sumStep" in self.settings:
            winInit["sumStep"] = self.settings["sumStep"]
        if "IDtype" in self.settings:
            winInit["IDtype"] = self.settings["IDtype"]

        winInit["database"] = self.dbConn

        self.twin = TimeWindows(**winInit)

    def Run(self):
        comp = Computor(
            self.baseline, self.twin, self.dbConn, self.settings["dataExport"]
        )
        state, msg = comp.GetStatus()
        if state:
            self.initGrassLayerMgr()
            self.initTemporalMgr()
        return
        # self.initgrassManagement()

    def initGrassLayerMgr(self):
        grassLayerMgr = {}
        if "colorRules" in self.settings:
            grassLayerMgr["rules"] = self.settings["colorRules"]

        if "colorName" in self.settings:
            grassLayerMgr["color"] = self.settings["colorName"]

        grassLayerMgr["database"] = self.dbConn
        GrassLayerMgr(**grassLayerMgr)

    def initTemporalMgr(self):
        GrassTemporalMgr(self.dbConn, self.twin)

    def errMsg(self, label):
        print(label)
        GError(label)


class MyApp(wx.App):
    def OnInit(self):
        frame = MWMainFrame(None, -1, "MW manager")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


def main():
    grass.set_raise_on_error(False)

    options, flags = grass.parser()

    app = MyApp(0)  # Create an instance of the application class
    app.MainLoop()  # Tell it to start processing events


if __name__ == "__main__":
    main()
