"""!
@package frame.py


(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad <rashadkm gmail.com>
"""

import os
import sys
import copy
import tempfile
import gettext

if __name__ == "__main__":
    sys.path.append(os.path.join(os.environ['GISBASE'], "etc", "gui", "wxpython"))
import wx


from api_test           import MySingleMapFrame
from api_test       import ToolBarNames
from render2        import MapLayer
from lmgr.toolbars         import LMWorkspaceToolbar
class MyFrame(MySingleMapFrame):
    """!main frame
    """

    def __init__(self, parent = None, giface = None, title = _("GRASS UI"),
              size = (875, 600), name = 'Frame', **kwargs):
        """!
        @param parent (no parent is expected)
        @param title window title
        @param size default size
        """
        #self.Map = Map()
        #self.giface = giface

        MySingleMapFrame.__init__(self, parent = parent, title = title, size = size, name = name, **kwargs)


        self.cmd = ["d.rast", "map=aspect@PERMANENT"]
        self.rlayer = MapLayer(ltype = 'raster', cmd = self.cmd, Map = self.GetMap(), name = "elevation")
        self.AddLayer(self.rlayer)
        #LMWorkspaceToolbar(self)
        self.CreateWxToolBar()
        self.AddToolBarItem(ToolBarNames.NEWDISPLAY, self.dummyfunc)
        self.AddToolBarItem(ToolBarNames.WORKSPACENEW,self.dummyfunc)
        self.AddToolBarItem(ToolBarNames.ADDRASTER,self.dummyfunc)
        self.AddToolBarItem(ToolBarNames.ADDVECTOR,self.dummyfunc)
        #print self.GetLayerByIndex(0).name
        #print self.GetCurrentIndex()

    def dummyfunc(self,event):
        xx = 1
        print xx

def main():

    gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode = True)

    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = MyFrame()
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
