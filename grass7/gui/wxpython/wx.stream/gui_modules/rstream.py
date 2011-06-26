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

sys.path.append(os.path.join(os.getenv('GISBASE'), 'etc', 'gui', 'wxpython', 'gui_modules'))

import globalvar

import wx

class RStreamFrame(wx.Frame):
    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = _("GRASS GIS Hydrological Modelling Utility"), **kwargs):
        """!Main window of r.stream's GUI
        
        @param parent parent window
        @param id window id
        @param title window title
        
        @param kwargs wx.Frames' arguments
        """
        self.parent = parent
        
        wx.Frame.__init__(self, parent = parent, id = id, title = title, name = "RStream", **kwargs)

def main():
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = RStreamFrame()
    frame.Show()
    
    app.MainLoop()

if __name__ == "__main__":
    main()

