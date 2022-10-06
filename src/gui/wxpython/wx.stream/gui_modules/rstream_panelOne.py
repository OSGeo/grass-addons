#!/usr/bin/env python


"""!
@package rstream.py

@brief GUI for r.stream.* modules

See http://grass.osgeo.org/wiki/Wx.stream_GSoC_2011

Classes:
 - CoorWindow
 - TabPanelOne

(C) 2011 by Margherita Di Leo, and the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Margherita Di Leo (GSoC student 2011)
"""

import os
import sys

sys.path.append(
    os.path.join(os.getenv("GISBASE"), "etc", "gui", "wxpython", "gui_modules")
)

import wx
import wx.lib.flatnotebook as FN

from debug import Debug as Debug
from preferences import globalSettings as UserSettings

import grass.script as grass
import gselect
import gcmd
import dbm
import globalvar
import utils
import menuform

import rstream_ImageViewer
from rstream_ImageViewer import ImgFrame


# -------------------------------------------------------------


class CoorWindow(wx.Dialog):
    """!Get coordinates from map display and generates preview"""

    def __init__(
        self,
        parent,
        mapwindow,
        rad2,
        rad3,
        elev,
        acc,
        thre,
        net,
        drain,
        id=wx.ID_ANY,
        **kwargs,
    ):
        wx.Dialog.__init__(self, parent, id, **kwargs)
        self.parent = parent
        self.radioval2 = rad2
        self.radioval3 = rad3
        self.r_elev = elev
        self.r_acc = acc
        self.thre = thre
        # self.stre = stre
        self.v_net = net
        self.r_drain = drain

        text_static = wx.StaticText(self, label="Coordinates:")

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetWeight(wx.BOLD)

        text_static.SetFont(font)

        self.text_values = wx.StaticText(self, label=" " * 40)

        self.buttonCoor = wx.Button(self, label="Get coordinates")
        self.buttonCoor.Bind(wx.EVT_BUTTON, self.OnButtonCoor)

        self.buttonGenPrev = wx.Button(self, label="Generate preview")
        self.buttonGenPrev.Bind(wx.EVT_BUTTON, self.OnGenPrev)

        self.buttonClose = wx.Button(self, label="Close")
        self.buttonClose.Bind(wx.EVT_BUTTON, self.OnClose)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        buttonSizer.Add(self.buttonCoor, 0, wx.ALL, 10)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.buttonGenPrev, 0, wx.ALL, 10)
        buttonSizer.Add((0, 0), 1, wx.EXPAND)
        buttonSizer.Add(self.buttonClose, 0, wx.ALL, 10)

        mainSizer.Add(buttonSizer, 0, wx.EXPAND)

        textSizer = wx.BoxSizer(wx.HORIZONTAL)
        textSizer.Add(text_static, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        textSizer.Add(
            self.text_values, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15
        )

        mainSizer.Add(textSizer, 0, wx.EXPAND)

        width, height = self.GetTextExtent("M" * 50)
        self.SetSize((width, -1))

        self.SetSizer(mainSizer)
        mainSizer.Layout()

        self.mapwin = mapwindow.GetWindow()

    def OnGenPrev(self, event):

        # read current region
        infoRegion = grass.read_command("g.region", flags="p")
        dictRegion = grass.parse_key_val(infoRegion, ":")
        original_rows = int(dictRegion["rows"])
        original_cols = int(dictRegion["cols"])
        original_nsres = float(dictRegion["nsres"])
        original_ewres = float(dictRegion["ewres"])
        original_e = float(dictRegion["east"])
        original_n = float(dictRegion["north"])
        original_s = float(dictRegion["south"])
        original_w = float(dictRegion["west"])

        # new_ewres = 1/4 original_ewres
        # new_nsres = 1/4 original_nsres
        # TODO testing about time, to adjust optimal dimension of preview

        new_ewres = original_ewres / 4
        new_nsres = original_nsres / 4

        mid_new_ewres = new_ewres / 2
        mid_new_nsres = new_nsres / 2

        x = float(self.x)
        y = float(self.y)

        tentative_new_n = y + mid_new_nsres
        tentative_new_s = y - mid_new_nsres
        tentative_new_e = x + mid_new_ewres
        tentative_new_w = x - mid_new_ewres

        if tentative_new_n >= original_n:
            new_n = original_n
            new_s = original_n - nsres

        elif tentative_new_s <= original_s:
            new_s = original_s
            new_n = original_s + nsres

        else:
            new_n = tentative_new_n
            new_s = tentative_new_s

        # ---

        if tentative_new_e >= original_e:
            new_e = original_e
            new_w = original_e - ewres

        elif tentative_new_w <= original_w:
            new_w = original_w
            new_e = original_w + ewres

        else:
            new_w = tentative_new_w
            new_e = tentative_new_e

        # set new temporary region

        grass.run_command("g.region", flags="ap", n=new_n, s=new_s, w=new_w, e=new_e)

        # run stream extraction on the smaller region

        # MFD

        if self.radioval2 == "True":
            grass.message("Creating flow accumulation map with MFD algorithm..")
            grass.run_command(
                "r.watershed",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                convergence=5,
                flags="a",
                overwrite=True,
            )

            grass.run_command(
                "r.stream.extract",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                threshold=self.thre,
                stream_vect=self.v_net,
                direction=self.r_drain,
                overwrite=True,
            )

        # SFD
        elif self.radioval3 == "True":
            grass.message("Creating flow accumulation map with SFD algorithm..")
            grass.run_command(
                "r.watershed",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                drainage=self.r_drain,
                convergence=5,
                flags="sa",
                overwrite=True,
            )

            grass.run_command(
                "r.stream.extract",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                threshold=self.thre,
                stream_vect=self.v_net,
                direction=self.r_drain,
                overwrite=True,
            )

        else:

            grass.run_command(
                "r.stream.extract",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                threshold=self.thre,
                stream_vect=self.v_net,
                direction=self.r_drain,
                overwrite=True,
            )

        # Create temporary files to be visualized in the preview
        img_tmp = grass.tempfile() + ".png"
        grass.run_command("d.mon", start="png", output=img_tmp)
        grass.run_command("d.rast", map=self.r_elev)
        grass.run_command("d.vect", map=self.v_net)
        print("Exported in file " + img_tmp_)

        directory = os.path.dirname(img_tmp)
        print(directory)

        # set region to original region

        grass.run_command(
            "g.region",
            flags="ap",
            n=original_n,
            s=original_s,
            w=original_w,
            e=original_e,
        )

        os.chdir(directory)
        # Call ImageViewer
        ImgVvr = wx.PySimpleApp()
        frame = ImgFrame(directory)
        ImgVvr.MainLoop()

    def OnButtonCoor(self, event):

        if self.mapwin.RegisterMouseEventHandler(
            wx.EVT_LEFT_DOWN, self.OnMouseAction, wx.StockCursor(wx.CURSOR_CROSS)
        ):
            self.mapwin.Raise()
        else:
            self.text.SetLabel("Cannot get coordinates")

    def OnClose(self, event):
        self.Destroy()
        self.Show()

    def OnMouseAction(self, event):
        coor = self.mapwin.Pixel2Cell(event.GetPositionTuple()[:])

        self.x, self.y = coor
        self.x, self.y = "%0.3f" % self.x, "%0.3f" % self.y

        self.text_values.SetLabel("Easting=%s, Northing=%s" % (self.x, self.y))
        self.mapwin.UnregisterMouseEventHandler(wx.EVT_LEFT_DOWN)
        event.Skip()


# -------------------------------------------------------------


class TabPanelOne(wx.Panel):
    """!Main panel for layout, network extraction and preview"""

    def __init__(self, parent, layerManager, MapFrame):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)

        self.layerManager = layerManager
        self.mapdisp = MapFrame
        self.radioval2 = False
        self.radioval3 = False
        self.parent = parent
        self.thre = 0
        self.r_elev = "r_elev"
        self.r_acc = "r_acc"
        # self.r_stre = 'r_stre'
        self.v_net = "v_net"
        self.r_drain = "r_drain"

        self.panel = wx.Panel(self)
        self._layout()

    def _layout(self):

        self.select = wx.GridBagSizer(20, 5)

        # ----------------------------
        # ---------Input maps---------

        # Ask user for digital elevation model
        self.text1 = wx.StaticText(
            parent=self.panel, id=wx.ID_ANY, label="INPUT : Elevation map (required)"
        )
        self.select.Add(
            item=self.text1, flag=wx.LEFT, pos=(1, 0), span=wx.DefaultSpan, border=0
        )

        # Add the box for choosing the map
        self.select1 = gselect.Select(
            parent=self.panel,
            id=wx.ID_ANY,
            size=(250, -1),
            type="raster",
            multiple=False,
        )
        self.select.Add(item=self.select1, pos=(2, 0), span=wx.DefaultSpan)

        # binder
        self.select1.Bind(wx.EVT_TEXT, self.OnSelectElev)

        # ----------------------------

        # Ask user for Flow accumulation
        self.text2 = wx.StaticText(
            parent=self.panel,
            id=wx.ID_ANY,
            label="INPUT/OUTPUT : Flow accumulation (required)",
        )
        self.select.Add(item=self.text2, flag=wx.LEFT, pos=(3, 0), span=wx.DefaultSpan)

        # Flow accum can be either existent or to be calculated
        # RadioButton
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        self.cb1 = wx.RadioButton(
            parent=self.panel,
            id=wx.ID_ANY,
            label="Custom (select existing map)",
            style=wx.RB_GROUP,
        )
        self.hbox1.Add(item=self.cb1, flag=wx.LEFT)
        self.cb2 = wx.RadioButton(
            parent=self.panel, id=wx.ID_ANY, label="Create by MFD algorithm"
        )
        self.hbox1.Add(item=self.cb2, flag=wx.LEFT)
        self.cb3 = wx.RadioButton(
            parent=self.panel, id=wx.ID_ANY, label="Create by SFD algorithm"
        )
        self.hbox1.Add(item=self.cb3, flag=wx.LEFT)

        self.select.Add(item=self.hbox1, pos=(4, 0))

        # Box to insert name of acc map
        self.select2 = gselect.Select(
            parent=self.panel,
            id=wx.ID_ANY,
            size=(250, -1),
            type="raster",
            multiple=False,
        )  # select existing map
        self.select.Add(item=self.select2, pos=(5, 0), span=wx.DefaultSpan)
        self.textOne = wx.TextCtrl(parent=self.panel, id=wx.ID_ANY, style=wx.TE_LEFT)
        self.select.Add(
            item=self.textOne, flag=wx.LEFT | wx.EXPAND, pos=(6, 0), span=wx.DefaultSpan
        )

        # linking buttons and text
        self.texts = {
            "Custom (select existing map)": self.select2,
            "Create by MFD algorithm": self.textOne,
            "Create by SFD algorithm": self.textOne,
        }

        self.selectedText = self.select2  # default is select existing map

        # Disable
        self.textOne.Enable(False)

        # RadioButton binders
        self.cb1.Bind(wx.EVT_RADIOBUTTON, self.OnSelectExistAcc)
        self.cb2.Bind(wx.EVT_RADIOBUTTON, self.OnSelectMFDAcc)
        self.cb3.Bind(wx.EVT_RADIOBUTTON, self.OnSelectSFDAcc)

        # ----------------------------

        # Ask user for Mask
        self.text3 = wx.StaticText(
            parent=self.panel, id=wx.ID_ANY, label="INPUT : Mask (optional)"
        )
        self.select.Add(item=self.text3, flag=wx.LEFT, pos=(7, 0), span=wx.DefaultSpan)

        # Add the box for choosing the map
        self.select3 = gselect.Select(
            parent=self.panel,
            id=wx.ID_ANY,
            size=(250, -1),
            type="raster",
            multiple=False,
        )
        self.select.Add(item=self.select3, pos=(8, 0), span=wx.DefaultSpan)

        # binder
        self.select3.Bind(wx.EVT_TEXT, self.OnSelectMask)

        # ----------------------------

        # Ask user for threshold
        self.text4 = wx.StaticText(
            parent=self.panel, id=wx.ID_ANY, label="INPUT : Threshold (required)"
        )
        self.select.Add(item=self.text4, flag=wx.LEFT, pos=(9, 0), span=wx.DefaultSpan)

        # Box to insert threshold
        self.txtTwo = wx.TextCtrl(parent=self.panel, id=wx.ID_ANY, style=wx.TE_LEFT)
        self.select.Add(
            item=self.txtTwo, flag=wx.LEFT, pos=(10, 0), span=wx.DefaultSpan
        )

        # binder
        self.txtTwo.Bind(wx.EVT_TEXT, self.OnSelecTh)

        # ----------------------------
        # ---------Output maps---------

        # Flow direction map
        self.text5 = wx.StaticText(
            parent=self.panel,
            id=wx.ID_ANY,
            label="OUTPUT : Flow direction map (required)",
        )
        self.select.Add(
            item=self.text5, flag=wx.LEFT | wx.EXPAND, pos=(11, 0), span=wx.DefaultSpan
        )

        # Box to insert name of new flow dir map (to be created)
        self.txtThr = wx.TextCtrl(parent=self.panel, id=wx.ID_ANY, style=wx.TE_LEFT)
        self.select.Add(
            item=self.txtThr, flag=wx.LEFT | wx.EXPAND, pos=(12, 0), span=wx.DefaultSpan
        )

        # binder
        self.txtThr.Bind(wx.EVT_TEXT, self.OnSelecFd)

        # ----------------------------

        # Streams map
        self.text6 = wx.StaticText(
            parent=self.panel, id=wx.ID_ANY, label="OUTPUT : Streams (required)"
        )
        self.select.Add(
            item=self.text6, flag=wx.LEFT | wx.EXPAND, pos=(13, 0), span=wx.DefaultSpan
        )

        # Box to insert name of new streams map (to be created)
        self.txtFou = wx.TextCtrl(parent=self.panel, id=wx.ID_ANY, style=wx.TE_LEFT)
        self.select.Add(
            item=self.txtFou, flag=wx.LEFT | wx.EXPAND, pos=(14, 0), span=wx.DefaultSpan
        )

        # binder
        self.txtFou.Bind(wx.EVT_TEXT, self.OnSelecStr)

        # ----------------------------

        # Network map
        self.text7 = wx.StaticText(
            parent=self.panel, id=wx.ID_ANY, label="OUTPUT : Network (required)"
        )
        self.select.Add(
            item=self.text7, flag=wx.LEFT | wx.EXPAND, pos=(15, 0), span=wx.DefaultSpan
        )

        # Box to insert name of new streams map (to be created)
        self.txtFiv = wx.TextCtrl(parent=self.panel, id=wx.ID_ANY, style=wx.TE_LEFT)
        self.select.Add(
            item=self.txtFiv, flag=wx.LEFT | wx.EXPAND, pos=(16, 0), span=wx.DefaultSpan
        )

        # binder
        self.txtFiv.Bind(wx.EVT_TEXT, self.OnSelecNet)

        # ----------------------------

        self.panel.SetSizer(self.select)
        self.btnPanel = wx.Panel(self)

        # -------------Buttons-------------

        self.createButtonBar(self.btnPanel)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.sizer.Add(self.btnPanel, 0, wx.EXPAND)
        self.SetSizer(self.sizer)

    # -------------input maps-------------

    def OnSelectElev(self, event):
        """!Gets elevation map and assign it to var"""
        self.r_elev = event.GetString()

    def OnSelectMFDAcc(self, event):
        """!Gets new flow accum map and assign it to var"""
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

    def OnSelectSFDAcc(self, event):
        """!Gets new flow accum map and assign it to var"""
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

    def OnSelectExistAcc(self, event):
        """!Gets existing flow acc map and assign it to var"""
        self.textOne.Enable(False)
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

    def OnSelectMask(self, event):
        """!Gets mask map and assign it to var"""
        self.r_mask = event.GetString()

    def OnSelecTh(self, event):
        """!Gets threshold and assign it to var"""
        self.thre = event.GetString()

    # -------------output maps-------------

    def OnSelecFd(self, event):
        """!Gets flow direction map and assign it to var"""
        self.r_drain = event.GetString()

    def OnSelecStr(self, event):
        """!Gets stream map and assign it to var"""
        pass
        # self.r_stre = event.GetString()

    def OnSelecNet(self, event):
        """!Gets network map and assign it to var"""
        self.v_net = event.GetString()

    # -------------Buttons-------------

    def buttonData(self):
        return (("Update Preview", self.OnPreview), ("Run Analysis", self.OnRun))

    def createButtonBar(self, panel, yPos=0):
        xPos = 0
        for eachLabel, eachHandler in self.buttonData():
            pos = (xPos, yPos)
            button = self.buildOneButton(panel, eachLabel, eachHandler, pos)
            xPos += button.GetSize().width

    def buildOneButton(self, parent, label, handler, pos=(0, 0)):
        button = wx.Button(parent, wx.ID_ANY, label, pos)
        self.Bind(wx.EVT_BUTTON, handler, button)
        return button

    # -------------Preview funct-------------

    def OnPreview(self, event):
        """!Allows to watch a preview of the analysis on a small region"""

        self.radioval2 = self.cb2.GetValue()
        self.radioval3 = self.cb3.GetValue()

        # message box
        self.msg = wx.MessageDialog(
            parent=self.panel,
            message="Please select the center of preview window on the map",
            caption="Preview utility",
            style=wx.OK | wx.CANCEL,
            pos=wx.DefaultPosition,
        )
        self.retCode = self.msg.ShowModal()
        if self.retCode == wx.ID_OK:
            # Raise a new Map Display
            self.mapdisp = self.layerManager.NewDisplay()

            # Display the elevation map
            self.mapdisp.Map.AddLayer(
                type="raster", command=["d.rast", "map=%s" % self.r_elev]
            )

            self.mapdisp.OnRender(None)

            # Call CoorWindow
            coorWin = CoorWindow(
                parent=self,
                mapwindow=self.mapdisp,
                rad2=self.radioval2,
                rad3=self.radioval3,
                elev=self.r_elev,
                acc=self.r_acc,
                thre=self.thre,
                # stre      = self.stre,
                net=self.v_net,
                drain=self.r_drain,
            )

            coorWin.Show()

    # -------------Network extraction-------------

    def OnRun(self, event):

        self.radioval2 = self.cb2.GetValue()
        self.radioval3 = self.cb3.GetValue()

        # MFD
        if self.radioval2 == "True":
            grass.message("Creating flow accumulation map with MFD algorithm..")
            grass.run_command(
                "r.watershed",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                convergence=5,
                flags="a",
                overwrite=True,
            )

        # SFD
        if self.radioval3 == "True":
            grass.message("Creating flow accumulation map with SFD algorithm..")
            grass.run_command(
                "r.watershed",
                elevation=self.r_elev,
                accumulation=self.r_acc,
                drainage=self.r_drain,
                convergence=5,
                flags="sa",
                overwrite=True,
            )

        grass.message("Network extraction..")
        grass.run_command(
            "r.stream.extract",
            elevation=self.r_elev,
            accumulation=self.r_acc,
            threshold=self.thre,
            # stream_rast = self.r_stre,
            stream_vect=self.v_net,
            direction=self.r_drain,
            overwrite=True,
        )
