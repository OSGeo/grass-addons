#!/usr/bin/env python
"""
@module  g.gui.cswbrowser
@brief   GUI csw browser

(C) 2015 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2015)
"""

# %module
# % description: Graphical CSW metadata browser.
# % keyword: general
# % keyword: GUI
# % keyword: metadata
# %end

import grass.script as gs


def main(giface=None):
    # The GUI is imported only after the parser has run, so that the
    # interface description can be created without wxPython installed.
    gs.utils.set_path(modulename="wx.metadata", dirname="mdlib", path="..")

    import wx

    from mdlib.cswlib import CswBrowserMainDialog

    app = wx.App()
    browser = CswBrowserMainDialog(giface)
    browser.Show()
    app.MainLoop()


if __name__ == "__main__":
    gs.parser()
    main()
