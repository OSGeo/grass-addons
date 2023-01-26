"""!
@package WMSMapDisplay.py

@brief Python code for displaying the fetched map
from wms server.

Classes:
 - ImagePanel
Functions:
 - NewImageFrame

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

import wx
import cStringIO


class ImagePanel(wx.Panel):
    def __init__(self, parent, id, tempFile):
        wx.Panel.__init__(self, parent, id)
        try:
            imageFile = tempFile
            data = open(imageFile, "rb").read()
            stream = cStringIO.StringIO(data)
            bmp = wx.BitmapFromImage(wx.ImageFromStream(stream))
            wx.StaticBitmap(self, -1, bmp, (5, 5))
            png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap()
            wx.StaticBitmap(
                self,
                -1,
                png,
                (10 + png.GetWidth(), 5),
                (png.GetWidth(), png.GetHeight()),
            )
        except IOError:
            message = "Image file %s not found" % imageFile
            grass.warning(message)
            raise SystemExit


def NewImageFrame(tempFile):
    NewWindowapp = wx.PySimpleApp()
    NewWindowframe = wx.Frame(None, -1, "Map Display", size=(400, 300))
    ImagePanel(NewWindowframe, -1, tempFile)
    NewWindowframe.Show(1)
    NewWindowapp.MainLoop()
