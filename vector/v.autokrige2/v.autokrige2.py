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
#import wx.lib.flatnotebook as FN # self.notebook attribute in Kriging Module's __init__


#classes in alphabetical order

class Log:
    """
    The log output is redirected to the status bar of the containing frame.
    """
    def __init__(self, parent):
        self.parent = parent

    def write(self, text_string):
        """Update status bar"""
        self.parent.SetStatusText(text_string.strip())

class KrigingModule(wx.Frame):
    """
    Kriging module for GRASS GIS.
    """
    def __init__(self, parent, *args, **kwargs):
        wx.Frame.__init__(self, parent, *args, **kwargs)
        # setting properties and all widgettery
        self.SetTitle("Kriging Module")
        self.panel = wx.Panel(parent=self)
        
        self.log = Log(self) # -> statusbar
        self.CreateStatusBar()
        # debug: remove before flight
        self.log.write("Are you reading this? This proves it is very beta version.")

        #self.notebook = FN.FlatNotebook(parent=self.panel, id=wx.ID_ANY,
        #                                style=FN.FNB_BOTTOM |
        #                                FN.FNB_NO_NAV_BUTTONS |
        #                                FN.FNB_FANCY_TABS | FN.FNB_NO_X_BUTTON)

        # use this block to add pages to the flat notebook widget        
        #dbmStyle = globalvar.FNPageStyle
        ## start block
        #self.browsePage = FN.FlatNotebook(self.panel, id=wx.ID_ANY,
        #                                  style=dbmStyle)
        #self.notebook.AddPage(self.browsePage, text=_("Browse data"))
        #self.browsePage.SetTabAreaColour(globalvar.FNPageColor)
        ## end block

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
    k = KrigingModule(parent=None, size=(600,300))
    k.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()

