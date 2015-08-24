#!/usr/bin/env python
"""
@module  g.gui.cswbrowser
@brief   GUI csw browser

(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""

import sys
import os

from grass.pygrass.utils import get_lib_path

def load_mdlib(libs):
    for lib in libs:
        path = get_lib_path(modname=os.path.join('wx.metadata','mdlib') ,libname=lib)
        if path is not None and path not in sys.path:
            sys.path.append(path)
        elif path is  None:
            grass.fatal("Fatal error: library < %s > not found "%lib)
load_mdlib(['cswlib'])
import wx
from cswlib import CSWBrowserPanel, CSWConnectionPanel
import grass.script as grass

class CswBrowserMainDialog(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="Metadata browser", size=(1024, 760))

        self.mainNotebook = wx.Notebook(self, wx.ID_ANY)
        self.config = wx.Config("g.gui.cswbrowser")

        self.BrowserPanel = CSWBrowserPanel(self.mainNotebook, self)
        self.connectionPanel = CSWConnectionPanel(self.mainNotebook, self)
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
