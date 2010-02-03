"""
@package gmconsole.py

@brief window to ouptut grass command ouput.

Classes:
 - GLog


(C) 2006-2009 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton (Arizona State University)
@author Jachym Cepicky (Mendel University of Agriculture)
@author Martin Landa <landa.martin gmail.com>
@author Mohammed Rashad K.M <rashadkm at gmail dot com> (modified for DataCatalog)
"""

import sys
import os
import time
import traceback
import re
import string
import getopt
import platform

### XML 
try:
    import xml.etree.ElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree # Python <= 2.4

### i18N
import gettext
gettext.install('grasswxpy', os.path.join(os.getenv("GISBASE"), 'locale'), unicode=True)

pypath = "/usr/local/grass-7.0.svn/etc/wxpython"
sys.path.append(pypath)

import gui_modules
gmpath = gui_modules.__path__[0]
sys.path.append(gmpath)

import images
imagepath = images.__path__[0]
sys.path.append(imagepath)

import icons
gmpath = icons.__path__[0]
sys.path.append(gmpath)

import gui_modules.globalvar as globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()

import wx
import wx.aui
import wx.combo
import wx.html
import wx.stc
import wx.lib.customtreectrl as CT
import wx.lib.flatnotebook as FN

grassPath = os.path.join(globalvar.ETCDIR, "python")
sys.path.append(grassPath)

import gui_modules.preferences as preferences


UserSettings = preferences.globalSettings

class GLog(wx.Frame):
    """
    GIS Manager frame with notebook widget for controlling
    GRASS GIS. Includes command console page for typing GRASS
    (and other) commands, tree widget page for managing GIS map layers.
    """
    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Command Output")):
 

        wx.Frame.__init__(self, parent=parent, id=id, size=(550, 450),
                          style=wx.DEFAULT_FRAME_STYLE,title="Command Output")
                          
       
        self.SetName("LayerManager")
        self.notebook  = self.__createNoteBook()
        self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)
        self.Show()
        self.SetBackgroundColour("white")
        self.goutput.Redirect()


    def OnCloseWindow(self,event):
        self.Destroy()
 
    def __createNoteBook(self):
        """!Creates notebook widgets"""
        nbStyle = FN.FNB_FANCY_TABS | \
            FN.FNB_BOTTOM | \
            FN.FNB_NO_NAV_BUTTONS | \
            FN.FNB_NO_X_BUTTON
        
        self.notebook = FN.FlatNotebook(parent=self, id=wx.ID_ANY, style=nbStyle)
        self.goutput = goutput.GMConsole(self, pageid=1)
        self.outpage = self.notebook.AddPage(self.goutput, text=_("Command output"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook.SetSize(wx.Size(600,600))
        sizer.Add(item=self.goutput, proportion=1,flag=wx.EXPAND | wx.ALL, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.Centre()
        return self.notebook  




   
