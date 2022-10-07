#!/usr/bin/env python


"""!
@package rstream.py

@brief GUI for r.stream.* modules

See http://grass.osgeo.org/wiki/Wx.stream_GSoC_2011

Classes:
 - ImgFrame
 - ListImg
 - ImgPanel

(C) 2011 by Margherita Di Leo, and the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Margherita Di Leo (GSoC student 2011)
"""


import wx
import glob


class ImgPanel(wx.Panel):
    """!Display selected image in the main window"""

    def __init__(self, parent, img):
        """ """
        wx.Panel.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.staticBitmap = wx.StaticBitmap(self, -1, img)
        self.PhotoMaxSize = 240
        self.sizer.Add(self.staticBitmap, 1, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.sizer.Layout()


class ListImg(wx.Listbook):
    """!Load png files *from current folder* and convert to bitmap"""

    def __init__(self, parent):
        """ """
        wx.Listbook.__init__(self, parent, style=wx.BK_BOTTOM)
        self.pages = []
        pathname = "*.png"
        self.ImL = wx.ImageList(32, 32)
        for imID, filename in enumerate(glob.glob(pathname)):
            bmp = wx.Bitmap(filename, wx.BITMAP_TYPE_PNG)
            img = bmp.ConvertToImage()
            img.Rescale(32, 32)
            bmp_scaled = img.ConvertToBitmap()
            self.ImL.Add(bmp_scaled)
            self.pages.append(ImgPanel(self, bmp))
            self.AddPage(self.pages[-1], "", imageId=imID)
        self.AssignImageList(self.ImL)

        # Binders
        self.Bind(wx.EVT_LISTBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_LISTBOOK_PAGE_CHANGING, self.OnPageChanging)

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()


class ImgFrame(wx.Frame):
    """!Main frame"""

    def __init__(self):
        """ """

        wx.Frame.__init__(self, None, wx.ID_ANY, "Image Viewer", size=(800, 600))

        panel = wx.Panel(self)

        previews = ListImg(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(previews, 1, wx.ALL | wx.EXPAND, 5)
        panel.SetSizer(sizer)
        self.Layout()

        self.Show()


if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = ImgFrame()
    app.MainLoop()
