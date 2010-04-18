"""
@package wxgui.py

@brief Main Python app for GRASS wxPython GUI. Main menu, layer management
toolbar, notebook control for display management and access to
command console.

Classes:
 - GMFrame
 - GMApp

(C) 2006-2009 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton (Arizona State University)
@author Jachym Cepicky (Mendel University of Agriculture)
@author Martin Landa <landa.martin gmail.com>
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
from grass.script import core as grass

import gui_modules.utils as utils
import gui_modules.preferences as preferences
import gui_modules.wxgui_utils as wxgui_utils
import mapdisplay as mapdisp
import gui_modules.menudata as menudata
import gui_modules.menuform as menuform
import gui_modules.histogram as histogram
import gui_modules.profile as profile
import gui_modules.rules as rules
import gui_modules.mcalc_builder as mapcalculator
import gui_modules.gcmd as gcmd
import gui_modules.georect as georect
import gui_modules.dbm as dbm
import gui_modules.workspace as workspace
import gui_modules.goutput as goutput
import gui_modules.gdialogs as gdialogs
import gui_modules.colorrules as colorrules
import gui_modules.ogc_services as ogc_services
import gui_modules.prompt as prompt
from   gui_modules.debug import Debug
from   gui_modules.help import MenuTreeWindow
from   gui_modules.help import AboutWindow
from   icons.icon import Icons

import glob
import render
#from mapwindow import BufferedWindow
from right import RightTree
import LayerTree

UserSettings = preferences.globalSettings

class GMFrame(wx.Panel):
    """
    GIS Manager frame with notebook widget for controlling
    GRASS GIS. Includes command console page for typing GRASS
    (and other) commands, tree widget page for managing GIS map layers.
    """
    def __init__(self, parent, id=wx.ID_ANY, title=_("GRASS GIS Layer Manager"),
                 workspace=None,frame=None):
        self.parent    = parent
        self.baseTitle = title
        self.iconsize  = (16, 16)

        wx.Panel.__init__(self, parent=parent, id=id, size=(550, 450),
                          style=wx.DEFAULT_FRAME_STYLE)
                          
        #self.SetTitle(self.baseTitle)
        #self.SetName("LayerManager")

        #self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass.ico'), wx.BITMAP_TYPE_ICO))

        #self._auimgr = wx.aui.AuiManager(self)
        self.frame = frame



        if UserSettings.Get(group='general', key='defWindowPos', subkey='enabled') is True:
            dim = UserSettings.Get(group='general', key='defWindowPos', subkey='dim')
            try:
               x, y = map(int, dim.split(',')[0:2])
               w, h = map(int, dim.split(',')[2:4])
               self.SetPosition((x, y))
               self.SetSize((w, h))
            except:
                pass

      

