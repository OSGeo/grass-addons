import os
import sys

sys.path.append(os.path.join(os.getenv('GISBASE'), 'etc', 'gui', 'wxpython', 'gui_modules'))

import globalvar

import wx

class RStreamFrame(wx.Frame):
    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = _("GRASS GIS r.stream Utility"), **kwargs):
        """!Main window of r.stream GUI
        
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

