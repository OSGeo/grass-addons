#!/usr/bin/env python


"""!
@package rstream.py

@brief GUI for r.stream.* modules

See http://grass.osgeo.org/wiki/Wx.stream_GSoC_2011

Classes:
 - RStreamFrame

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

from rstream_panelOne import *


## #-------------Panels-------------


# Child panel class before customization


class TabPanel(wx.Panel):
    def __init__(self, parent):

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.txtOne = wx.TextCtrl(self, wx.ID_ANY, "")
        self.txtTwo = wx.TextCtrl(self, wx.ID_ANY, "")

        self.sizer.Add(self.txtOne, 0, wx.ALL, 5)
        self.sizer.Add(self.txtTwo, 0, wx.ALL, 5)

        self.SetSizer(self.sizer)


## #-------------Main Frame-------------


class RStreamFrame(wx.Frame):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        style=wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER,
        title=_("GRASS GIS Hydrological Modelling Utility"),
        **kwargs,
    ):
        """!Main window of r.stream's GUI

        @param parent parent window
        @param id window id
        @param title window title

        @param kwargs wx.Frames' arguments
        """
        self.parent = parent

        wx.Frame.__init__(
            self,
            parent=parent,
            id=id,
            title=title,
            name="RStream",
            size=(600, 900),
            **kwargs,
        )
        self.SetIcon(
            wx.Icon(os.path.join(globalvar.ETCICONDIR, "grass.ico"), wx.BITMAP_TYPE_ICO)
        )

        self.nb = FN.FlatNotebook(
            parent=self,
            id=wx.ID_ANY,
            style=FN.FNB_NO_NAV_BUTTONS | FN.FNB_FANCY_TABS | FN.FNB_NO_X_BUTTON,
        )

        # add pages to the notebook
        self.pages = [
            (TabPanelOne(self.nb, self.parent, self), "Network extraction"),
            (TabPanel(self.nb), "Network ordering"),
            (TabPanel(self.nb), "Tab 3"),
        ]

        for page, label in self.pages:
            self.nb.AddPage(page, label)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.nb, 1, wx.EXPAND)

        # button for close and other
        self.button = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_close = wx.Button(parent=self, id=wx.ID_CLOSE)
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
        self.button.Add(item=self.btn_close, flag=wx.ALL, border=5)
        self.sizer.Add(self.button)

        self.SetSizer(self.sizer)

    def OnClose(self, event):
        self.Destroy()
        self.Show()


def main():
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = RStreamFrame()
    frame.Show()

    app.MainLoop()


if __name__ == "__main__":
    main()
