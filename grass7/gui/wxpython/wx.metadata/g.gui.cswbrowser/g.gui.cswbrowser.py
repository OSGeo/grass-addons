#!/usr/bin/env python
import sys, os
import grass.script as grass
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), 'etc', 'mdlib'))
from cswlib import *
import wx
class CswBrowserMainDialog(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Metadata browser", size=(1024, 760))

        self.mainNotebook = wx.Notebook(self, wx.ID_ANY)
        self.config = wx.Config("g.gui.cswbrowser")

        self.BrowserPanel = CSWBrowserPanel(self.mainNotebook, self)
        self.connectionPanel = CSWConnectionPanel(self.mainNotebook, self)
        # self.dirpath = os.path.join(os.getenv('GRASS_ADDON_BASE'), 'g.gui.cswbrowser')
        self.mainNotebook.AddPage(self.BrowserPanel, text='Find')
        self.mainNotebook.AddPage(self.connectionPanel, text='Configure')
        self._layout()

    def _layout(self):
        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.mainsizer.Add(self.mainNotebook, 1, wx.EXPAND, )
        self.SetSizer(self.mainsizer)

def main():
    app = wx.App()
    a = CswBrowserMainDialog()
    a.Show()
    app.MainLoop()

if __name__ == '__main__':
    grass.parser()
    main()

