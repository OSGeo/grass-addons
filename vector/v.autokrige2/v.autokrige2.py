#!/usr/bin/python
# -*- coding:utf-8 -*-
"""
MODULE:    v.autokrige2

AUTHOR(S): Anne Ghisla <a.ghisla AT gmail.com>

PURPOSE:   Performs ordinary kriging

DEPENDS:  R (version?), package automap (geoR? gstat?)

COPYRIGHT: (C) 2009 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#list of parameters

#import directives. to be completed.
import wx
import sys

#classes in alphabetical order
class KrigingModule(wx.Frame):
    """
    Kriging module for GRASS GIS.
    """
    def __init__(self, parent, id=wx.ID_ANY, size=None, 
                 style = wx.DEFAULT_FRAME_STYLE, title=None, log=None):
        self.parent = parent
        self.size = size
        wx.Frame.__init__(self, parent, id, style=style, size=self.size)
        
        # setting properties
        self.SetTitle("Kriging Module")

#main
def main(argv=None):
    if argv is None:
        argv = sys.argv

    """if len(argv) != 2:
        print >> sys.stderr, __doc__
        sys.exit()"""

    # Command line arguments of the script to be run are preserved by the
    # hotswap.py wrapper but hotswap.py and its options are removed that
    # sys.argv looks as if no wrapper was present.
    #print "argv:", `argv`

    # commmented, as I don't know if the module will need it.
    ##some applications might require image handlers
    #wx.InitAllImageHandlers()

    app = wx.PySimpleApp()
    k = KrigingModule(parent=None, id=wx.ID_ANY, size=(300,300))
    k.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()

