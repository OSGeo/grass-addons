"""
@package catalog.py

GRASS DataCatalog.

@breif A GRASS GIS data manager used to copy,rename,delete,
display maps in different mapsets and locations.

Classes:
 - DataCatalog
 - CatalogApp

(C) 2007 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad K.M <rashadkm at gmail dot com>

"""

import sys
import os
import time
import traceback
import re
import string
import getopt
import platform
import shlex


#os.system("export integ=True")
os.environ['integrated-gui'] = "True"

try:
    import xml.etree.ElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree 


gbase = os.getenv("GISBASE") 
grassversion = os.getenv("GRASS_VERSION")
if grassversion == "7.0.svn":
    pypath = os.path.join(gbase,'etc','gui','wxpython')
else:
    pypath = os.path.join(gbase,'etc','wxpython')
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


#To run DataCatalog from any directory set this pathname for access to gui_modules 
gbase = os.getenv("GISBASE") 
if grassversion == "7.0.svn":
    pypath = os.path.join(gbase,'etc','gui','wxpython','gui_modules')
else:
    pypath = os.path.join(gbase,'etc','wxpython','gui_modules')

sys.path.append(pypath)


import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import wx
import gcmd
import glob
import render
import gui_modules.gdialogs as gdialogs
import gui_modules.goutput as goutput
import gui_modules.histogram as histogram
from   gui_modules.debug import Debug
import gui_modules.menuform as menuform
import gui_modules.menudata as menudata

import gui_modules.utils as utils
import gui_modules.preferences as preferences
import gui_modules.mapdisp as mapdisp
import gui_modules.histogram as histogram
import gui_modules.profile as profile
import gui_modules.rules as rules
import gui_modules.mcalc_builder as mapcalculator
import gui_modules.gcmd as gcmd
import gui_modules.georect as georect
import gui_modules.dbm as dbm
import gui_modules.workspace as workspace
import gui_modules.colorrules as colorrules

#import gui_modules.vclean as vclean
import gui_modules.nviz_tools as nviz_tools

if grassversion.rfind("6.4") != 0:
    import gui_modules.menu as menu
    import gui_modules.gmodeler as gmodeler

#import gui_modules.ogc_services as ogc_services

#from   gui_modules.help import MenuTreeWindow
#from   gui_modules.help import AboutWindow
from   icons.icon import Icons

#from gmconsole import GLog
from mapdisplay import MapFrame
import wx.lib.flatnotebook as FN
from   icons.icon import Icons
from preferences import globalSettings as UserSettings
import render
import gc
if grassversion.rfind("6.4") != 0:
    from   gui_modules.ghelp import MenuTreeWindow
    from   gui_modules.ghelp import AboutWindow
    from   gui_modules.toolbars import LayerManagerToolbar
    from   gui_modules.ghelp import InstallExtensionWindow
from wxgui import GMFrame
from grass.script import core as grass

class DataCatalog(GMFrame):


    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Data Catalog Beta"),
                 workspace=None,size=wx.DefaultSize,pos=wx.DefaultPosition):

        self.iconsize  = (16, 16)
        self.baseTitle = title
        self.parent = parent

        wx.Frame.__init__(self, parent, id, title, pos=pos, size=size)
        self.SetName("LayerManager")

        self._auimgr=wx.aui.AuiManager(self)

        self.gisbase  = os.getenv("GISBASE")
        self.gisrc  = self.read_gisrc()
        self.viewInfo = True        #to display v/r.info on mapdisplay
        self.gisdbase = self.gisrc['GISDBASE'] 

        #backup location and mapset from gisrc which may be modified  by datacatalog
        self.iLocation = self.gisrc['LOCATION_NAME']
        self.iMapset = self.gisrc['MAPSET']



        # initialize variables
        self.disp_idx      = 0            # index value for map displays and layer trees
        self.curr_page     = ''           # currently selected page for layer tree notebook
        self.curr_pagenum  = ''           # currently selected page number for layer tree notebook
        self.workspaceFile = workspace    # workspace file
        self.workspaceChanged = False     # track changes in workspace
        self.georectifying = None         # reference to GCP class or None
        # list of open dialogs
        self.dialogs        = dict()
        self.dialogs['preferences'] = None
        self.dialogs['atm'] = list()

        #print os.getenv("integrated-gui")

        # creating widgets
        if grassversion.rfind("6.4") != 0:
            self.menubar = menu.Menu(parent = self, data = menudata.ManagerData())
            self.SetMenuBar(self.menubar)
            self.menucmd = self.menubar.GetCmd()
        self.statusbar = self.CreateStatusBar(number=1)
        self.notebook  = self.__createNoteBook()
        if grassversion.rfind("6.4") != 0:
            self.toolbar = LayerManagerToolbar(parent = self)
        else:
            self.toolbar   = self.__createToolBar()
        self.SetToolBar(self.toolbar)



        self.locationchange = True




     #creating sizers    
        self.cmbSizer = wx.BoxSizer(wx.HORIZONTAL) 
        self.mSizer = wx.BoxSizer(wx.VERTICAL)

        #these two sizers are applied to splitter window
        self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.rightSizer = wx.BoxSizer(wx.HORIZONTAL)

        #populate location combobox
        self.loclist = self.GetLocations()
        self.loclist.sort()

        #self.pg_panel4 = None
        if grassversion.rfind("6.4") != 0:
            self.menubar = menu.Menu(parent = self, data = menudata.ManagerData())
        else:
            self.menubar, self.menudata = self.__createMenuBar()
        self.SetMenuBar(self.menubar)
        self.menucmd = self.menubar.GetCmd()
        self.statusbar = self.CreateStatusBar(number=4, style=0)
        self.notebook  = self.__createNoteBook()
        self.toolbar = LayerManagerToolbar(parent = self)
        self.SetToolBar(self.toolbar)

        #setting splitter window

        self.cmbPanel = wx.Panel(self,name="cmbpanel")


        self.maptree = None
        self.pg_panel = None
        self.cb_loclist = []
        self.cb_maplist = []
        self.cb_mapfile = []

        #creating controls

        self.mInfo = wx.TextCtrl(self.cmbPanel, wx.ID_ANY, style = wx.TE_READONLY,size=(300,30))
        #
        # start radiobutton to activate - deactivate the mouse actions to send position to ossimplanet
        #
        self.options = ['on', 'off']
        self.radiobox = wx.RadioBox(self.cmbPanel, wx.ID_ANY, choices=self.options, style=wx.HORIZONTAL)
        self.radiobox.SetSelection(1)
        self.treeExpand = wx.CheckBox(self.cmbPanel, wx.ID_ANY,"Expand All", wx.DefaultPosition, wx.DefaultSize)
        self.cmbLocation = wx.ComboBox(self.cmbPanel, value = "Select Location",size=wx.DefaultSize, choices=self.loclist)
        self.cmbMapset = wx.ComboBox(self.cmbPanel, value = "Select Mapset", size=wx.DefaultSize)	


        self.itemFont = wx.Font(pointSize=9,weight=0, family=wx.FONTFAMILY_DEFAULT ,style=wx.FONTSTYLE_ITALIC)

        self.notebook  = self.__createNoteBook()
        self.curr_page = self.notebook.GetCurrentPage()    


        self.cmbLocation.SetValue(grass.gisenv()['LOCATION_NAME'])
        self.cmbMapset.SetValue(grass.gisenv()['MAPSET'])


        self.doBindings()
        self.doLayout()


    def OnCloseWindow(self, event):
        """!Cleanup when wxGUI is quit"""
        if not self.curr_page:
            self._auimgr.UnInit()
            self.Destroy()
            return
        os.environ['integrated-gui'] = "False"
        maptree = self.curr_page.maptree
        if self.workspaceChanged and \
                UserSettings.Get(group='manager', key='askOnQuit', subkey='enabled'):
            if self.workspaceFile:
                message = _("Do you want to save changes in the workspace?")
            else:
                message = _("Do you want to store current settings "
                            "to workspace file?")

            # ask user to save current settings
            if maptree.GetCount() > 0:
                dlg = wx.MessageDialog(self,
                                       message=message,
                                       caption=_("Quit GRASS GUI"),
                                       style=wx.YES_NO | wx.YES_DEFAULT |
                                       wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
                ret = dlg.ShowModal()
                if ret == wx.ID_YES:
                    if not self.workspaceFile:
                        self.OnWorkspaceSaveAs()
                    else:
                        self.SaveToWorkspaceFile(self.workspaceFile)
                elif ret == wx.ID_CANCEL:
                    event.Veto()
                    dlg.Destroy()
                    return
                dlg.Destroy()

        # don't ask any more...
        UserSettings.Set(group = 'manager', key = 'askOnQuit', subkey = 'enabled',
                         value = False)

        for page in range(self.gm_cb.GetPageCount()):
            self.gm_cb.GetPage(0).maptree.mapdisplay.OnCloseWindow(event)

        self.gm_cb.DeleteAllPages()

        self._auimgr.UnInit()
        self.Destroy()



    def __createNoteBook(self):
        """!Creates notebook widgets"""

        #create main notebook widget
        nbStyle = FN.FNB_FANCY_TABS | \
            FN.FNB_BOTTOM | \
            FN.FNB_NO_NAV_BUTTONS | \
            FN.FNB_NO_X_BUTTON


        self.disp_idx = -1


        # create displays notebook widget and add it to main notebook page
        cbStyle = globalvar.FNPageStyle
        self.notebook = FN.FlatNotebook(parent=self, id=wx.ID_ANY, style=cbStyle)

        self.notebook.SetTabAreaColour(globalvar.FNPageColor)

        self.pg_panel = MapFrame(parent=self.notebook, id=wx.ID_ANY, Map=render.Map(), size=globalvar.MAP_WINDOW_SIZE,flag=False,frame=self)

        self.disp_idx = self.disp_idx + 1
        self.notebook.AddPage(self.pg_panel, text="Display "+ str(self.disp_idx), select = True)

        self.goutput = goutput.GMConsole(self, pageid=1)
        self.outpage = self.notebook.AddPage(self.goutput, text=_("Command console"))

        self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnCBPageChanged)
        self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnCBPageClosed)


        return self.notebook



    def NewDisplay(self, show=True):
        """!Create new layer tree, which will
        create an associated map display frame

        @param show show map display window if True

        @return reference to mapdisplay intance
        """
        Debug.msg(1, "GMFrame.NewDisplay(): idx=%d" % self.disp_idx)

        self.disp_idx = self.disp_idx + 1

        self.page = MapFrame(parent=self.notebook, id=wx.ID_ANY, Map=render.Map(), size=globalvar.MAP_WINDOW_SIZE,frame=self)
        self.notebook.InsertPage(self.disp_idx,self.page, text="Display "+ str(self.disp_idx), select = True)

    def OnCloseWindow(self, event):
        """!Cleanup when wxGUI is quit"""
        if not self.curr_page:
            self._auimgr.UnInit()
            self.Destroy()
            return

        maptree = self.curr_page.maptree
        if self.workspaceChanged and \
                UserSettings.Get(group='manager', key='askOnQuit', subkey='enabled'):
            if self.workspaceFile:
                message = _("Do you want to save changes in the workspace?")
            else:
                message = _("Do you want to store current settings "
                            "to workspace file?")

            # ask user to save current settings
            if maptree.GetCount() > 0:
                dlg = wx.MessageDialog(self,
                                       message=message,
                                       caption=_("Quit GRASS GUI"),
                                       style=wx.YES_NO | wx.YES_DEFAULT |
                                       wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
                ret = dlg.ShowModal()
                if ret == wx.ID_YES:
                    if not self.workspaceFile:
                        self.OnWorkspaceSaveAs()
                    else:
                        self.SaveToWorkspaceFile(self.workspaceFile)
                elif ret == wx.ID_CANCEL:
                    event.Veto()
                    dlg.Destroy()
                    return
                dlg.Destroy()

        # don't ask any more...
        UserSettings.Set(group = 'manager', key = 'askOnQuit', subkey = 'enabled',
                         value = False)

        for page in range(self.notebook.GetPageCount()):
            self.notebook.GetPage(0).maptree.mapdisplay.OnCloseWindow(event)

        self.notebook.DeleteAllPages()

        self._auimgr.UnInit()
        self.Destroy()

    def OnMapsetChange(self,event):
        """
        Create the tree nodes based on selected location and mapset.
        Also update gisrc and grassrc files.
        """

        self.page = self.notebook.GetCurrentPage()

        self.gisrc['LOCATION_NAME'] = str(self.cmbLocation.GetValue())
        self.gisrc['MAPSET'] = str(self.cmbMapset.GetValue())
        self.update_grassrc(self.gisrc)


        self.page = self.notebook.GetPage(self.notebook.GetSelection())
        self.page.Map.__init__()	
        self.page.Map.region = self.page.Map.GetRegion()

        if grassversion != "6.4.0svn":
            self.page.Map.projinfo = self.page.Map._projInfo()
        else:
            self.page.Map.projinfo = self.page.Map.ProjInfo()

        self.page.Map.wind = self.page.Map.GetWindow()

        if self.locationchange == True:
            self.cb_loclist.append( str(self.cmbLocation.GetValue()) )
            self.cb_maplist.append( str(self.cmbMapset.GetValue()) )


    def OnLocationChange(self,event):
        """
        Populate mapset combobox with selected location.
        """
        self.cmbMapset.Clear()
        self.cmbMapset.SetValue("Select Mapset")

        maplists = self.GetMapsets(self.cmbLocation.GetValue())
        for mapsets in maplists:
            self.cmbMapset.Append(str(mapsets))

    def GetMapsets(self,location):
        """
        Read and returns all mapset int GRASS data directory.
        """

        maplist = []
        for mapset in glob.glob(os.path.join(self.gisdbase, location, "*")):
            if os.path.isdir(mapset) and os.path.isfile(os.path.join(self.gisdbase, location, mapset, "WIND")):
                maplist.append(os.path.basename(mapset))
        return maplist

    def GetLocations(self):
        """
        Read and returns all locations int GRASS data directory.
        """
        loclist = []
        for location in glob.glob(os.path.join(self.gisdbase, "*")):
            if os.path.join(location, "PERMANENT") in glob.glob(os.path.join(location, "*")):
                loclist.append(os.path.basename(location))
        return loclist


    def doBindings(self):

        #Event bindings for combo boxes
        self.Bind(wx.EVT_COMBOBOX,self.OnMapsetChange,self.cmbMapset)
        self.Bind(wx.EVT_COMBOBOX,self.OnLocationChange,self.cmbLocation)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)


    def doLayout(self):

        #combo panel sizers
        self.cmbSizer.Add(self.cmbLocation)
        self.cmbSizer.Add(self.cmbMapset)
        self.cmbSizer.Add(self.mInfo)
        self.cmbSizer.Add(self.radiobox)
        self.mSizer.Add(self.cmbPanel,flag=wx.EXPAND)
        self.mSizer.Add(self.notebook,1,wx.EXPAND)

        self.cmbPanel.SetSizer(self.cmbSizer)
        self.SetSizer(self.mSizer)



    def read_gisrc(self):
        """
        Read variables gisrc file
        """

        rc = {}

        gisrc = os.getenv("GISRC")

        if gisrc and os.path.isfile(gisrc):
            try:
                f = open(gisrc, "r")
                for line in f.readlines():
                    key, val = line.split(":", 1)
                    rc[key.strip()] = val.strip()
            finally:
                f.close()

        return rc

    def update_grassrc(self,gisrc):
        """
        Update $HOME/.grassrc(6/7) and gisrc files
        """
        rc = os.getenv("GISRC")
        grassversion = os.getenv("GRASS_VERSION")
        if grassversion == "7.0.svn":
            grassrc = os.path.join(os.getenv('HOME'), ".grassrc7.%s" % os.uname()[1])
            if not os.access(grassrc, os.R_OK):
                grassrc = os.path.join(os.getenv('HOME'), ".grassrc7")

        else:
            grassrc = os.path.join(os.getenv('HOME'), ".grassrc6.%s" % os.uname()[1])
            if not os.access(grassrc, os.R_OK):
                grassrc = os.path.join(os.getenv('HOME'), ".grassrc6")

        if rc and os.path.isfile(rc):
            try:
                f = open(rc, 'w')
                for key, val in gisrc.iteritems():
                    f.write("%s: %s\n" % (key, val))
            finally:
                f.close()

        if grassrc and os.path.isfile(grassrc):
            try:
                g = open(grassrc, 'w')
                for key, val in gisrc.iteritems():
                    g.write("%s: %s\n" % (key, val))
            finally:
                g.close()



#End of DataCatalog class



class CatalogApp(wx.App):

    def OnInit(self):
        self.catalog = DataCatalog()
        self.catalog.Show()
        self.catalog.Maximize()
        return 1


# end of class MapApp

# Run the program
if __name__ == "__main__":


    #gc.enable()
    #gc.set_debug(gc.DEBUG_LEAK)
    #print gc.garbage
    #gc.collect()


    g_catalog = CatalogApp(0)

    g_catalog.MainLoop()

    #sys.exit(0)	






