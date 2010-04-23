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

try:
    import xml.etree.ElementTree as etree
except ImportError:
    import elementtree.ElementTree as etree 


gbase = os.getenv("GISBASE") 
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

version = os.getenv("GRASS_VERSION")
if version == "6.5.svn":
    import gui_modules.menu as menu
    import gui_modules.gmodeler as gmodeler

#import gui_modules.ogc_services as ogc_services

#from   gui_modules.help import MenuTreeWindow
#from   gui_modules.help import AboutWindow
from   icons.icon import Icons

#from gmconsole import GLog
from mapdisplay import MapFrame
from LayerTree import LayerTree
import wx.lib.flatnotebook as FN
from   icons.icon import Icons
from preferences import globalSettings as UserSettings
import render
import gc

class DataCatalog(wx.Frame):


    def __init__(self, parent=None, id=wx.ID_ANY, title=_("Data Catalog Beta"),
                 workspace=None,size=wx.DefaultSize,pos=wx.DefaultPosition):

       
        self.iconsize  = (16, 16)
        self.baseTitle = title

        wx.Frame.__init__(self, parent, id, title, pos=pos, size=size)
 

        #self.Maximize()

        self.dict = {}


        self.gisbase  = os.getenv("GISBASE")
        self.gisrc  = self.read_gisrc()
        self.viewInfo = True        #to display v/r.info on mapdisplay
        self.gisdbase = self.gisrc['GISDBASE'] 

        #backup location and mapset from gisrc which may be modified  by datacatalog
        self.iLocation = self.gisrc['LOCATION_NAME']
        self.iMapset = self.gisrc['MAPSET']
        

        #self.Map = render.Map()

        self.curr_pagenum  = -1           # currently selected page number for layer tree notebook
        self.encoding      = 'ISO-8859-1' # default encoding for display fonts
        self.workspaceFile = workspace    # workspace file
        self.menucmd       = dict()       # menuId / cmd
        self.georectifying = None         # reference to GCP class or None

        self.dialogs        = dict()
        self.dialogs['preferences'] = None
        self.dialogs['atm'] = list()



        self.g_catalog=None

        self.locationchange = True

        self.menucmd       = dict() 
        
        self.mapfile = []  
        self.mapname = None
        self.cmd = None
        self.newmap = None


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
        version = os.getenv("GRASS_VERSION")
        if version == "6.5.svn":
            self.menubar = menu.Menu(parent = self, data = menudata.ManagerData())
        else:
            self.menubar, self.menudata = self.__createMenuBar()
        #self.statusbar = self.CreateStatusBar(number=1)
        #self.cmdprompt, self.cmdinput = self.__createCommandPrompt()
        self.toolbar   = self.__createToolBar()

        #setting splitter window

        self.cmbPanel = wx.Panel(self,name="cmbpanel")


        self.maptree = None
        self.pg_panel = None
        self.cb_loclist = []
        self.cb_maplist = []
        self.cb_mapfile = []
        
        #creating controls
        #self.mInfo = wx.TextCtrl(self.pRight, wx.ID_ANY, style = wx.TE_MULTILINE|wx.HSCROLL|wx.TE_READONLY)
        #self.chkInfo = wx.CheckBox(self.cmbPanel, wx.ID_ANY,"display Info", wx.DefaultPosition, wx.DefaultSize)
        self.treeExpand = wx.CheckBox(self.cmbPanel, wx.ID_ANY,"Expand All", wx.DefaultPosition, wx.DefaultSize)
        self.cmbLocation = wx.ComboBox(self.cmbPanel, value = "Select Location",size=wx.DefaultSize, choices=self.loclist)
        self.cmbMapset = wx.ComboBox(self.cmbPanel, value = "Select Mapset", size=wx.DefaultSize)	
        #self.tree = wx.TreeCtrl(self.pLeft, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS|wx.TR_EDIT_LABELS)



        self.itemFont = wx.Font(pointSize=9,weight=0, family=wx.FONTFAMILY_DEFAULT ,style=wx.FONTSTYLE_ITALIC)

        
        self.notebook  = self.__createNoteBook()
        self.cmdprompt = self.__createCommandPrompt()

       # self._mgr = self.pg_panel._layerManager

#        self._mgr.AddPane(self.cmdprompt, wx.aui.AuiPaneInfo().CentrePane().Dockable(False).BestSize((-1,-1)).CloseButton(False).DestroyOnClose(True). Layer(0))

        self.current = self.notebook.GetCurrentPage()    
 

        self.goutput = goutput.GMConsole(self, pageid=1)
        self.goutput.Hide()

    
       # self.ltree = LayerTree(self.pLeft,wx.ID_ANY,gisdbase=self.gisdbase,frame=self.pg_panel)

        self.doBindings()
        self.doLayout()

        self.cmbSizer.Add(self.cmdprompt)

        self.Map =    self.GetMapDisplay()

        




    def GetMapDisplay(self):
        self.panel = self.notebook.GetCurrentPage()
        return self.panel.Map
                            

    def __createMenuBar(self):
        """!Creates menubar"""

        self.menubar = wx.MenuBar()
        version = os.getenv("GRASS_VERSION")
        if version == "6.5.svn":
            self.menudata = menudata.ManagerData()
        else:
            self.menudata = menudata.Data()        
        for eachMenuData in self.menudata.GetMenu():
            for eachHeading in eachMenuData:
                menuLabel = eachHeading[0]
                menuItems = eachHeading[1]
                self.menubar.Append(self.__createMenu(menuItems), menuLabel)

        self.SetMenuBar(self.menubar)

        return (self.menubar, self.menudata)

    def __createCommandPrompt(self):
        """!Creates command-line input area"""
        self.cmdprompt = wx.Panel(self)

        button = wx.Button(parent=self.cmdprompt, id=wx.ID_ANY, label="Cmd >",
                            size=(70,23))
        button.SetToolTipString(_("Click for erasing command prompt"))
	# label.SetFont(wx.Font(pointSize=11, family=wx.FONTFAMILY_DEFAULT,
        #                      style=wx.NORMAL, weight=wx.BOLD))
        self.cinput = wx.TextCtrl(parent=self.cmdprompt, id=wx.ID_ANY,
                            value="",
                            style= wx.TE_PROCESS_ENTER,
                            size=(250,20))

        #cinput.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL, 0, ''))

        wx.CallAfter(self.cinput.SetInsertionPoint, 0)

        self.Bind(wx.EVT_TEXT_ENTER, self.OnRunCmd,   self.cinput)
        self.Bind(wx.EVT_BUTTON,     self.OnCmdClear,      button)
        #self.Bind(wx.EVT_TEXT,       self.OnUpdateStatusBar, input)

        # layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(item=button, proportion=0,
                  flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER,
                  border=4)
        sizer.Add(item=self.cinput, proportion=1,
                  flag=wx.EXPAND | wx.ALL,
                  border=1)

        self.cmdprompt.SetSizer(sizer)
        #sizer.Fit(self.cmdprompt)
        self.cmdprompt.Layout()

        return self.cmdprompt


    def OnCmdClear(self,event):
        self.cinput.SetValue('')
        self.cinput.SetFocus()

    def __createMenu(self, menuData):
        """!Creates menu"""

        menu = wx.Menu()
        for eachItem in menuData:
            if len(eachItem) == 2:
                label = eachItem[0]
                subMenu = self.__createMenu(eachItem[1])
                menu.AppendMenu(wx.ID_ANY, label, subMenu)
            else:
                version = os.getenv("GRASS_VERSION")
                if version == "6.4.0svn":
                    self.__createMenuItem(menu, *eachItem)
                else:
                    self.__createMenuItem7(menu, *eachItem)
        self.Bind(wx.EVT_MENU_HIGHLIGHT_ALL, self.OnMenuHighlight)
        return menu

#    def __createMenuItem(self, menu, label, help, handler, gcmd, keywords, shortcut = '', kind = wx.ITEM_NORMAL):
    def __createMenuItem(self, menu, label, help, handler, gcmd, kind=wx.ITEM_NORMAL):
        """Creates menu items"""

        if not label:
            menu.AppendSeparator()
            return

        if len(gcmd) > 0:
            helpString = gcmd + ' -- ' + help
        else:
            helpString = help

        menuItem = menu.Append(wx.ID_ANY, label, helpString, kind)
        
        self.menucmd[menuItem.GetId()] = gcmd

        if len(gcmd) > 0 and \
                gcmd.split()[0] not in globalvar.grassCmd['all']:
            menuItem.Enable (False)

        rhandler = eval(handler)

        self.Bind(wx.EVT_MENU, rhandler, menuItem)

    def __createMenuItem7(self, menu, label, help, handler, gcmd, keywords, shortcut = '', kind = wx.ITEM_NORMAL):
        """!Creates menu items"""

        if not label:
            menu.AppendSeparator()
            return

        if len(gcmd) > 0:
            helpString = gcmd + ' -- ' + help
        else:
            helpString = help
        
        if shortcut:
            label += '\t' + shortcut
        
        menuItem = menu.Append(wx.ID_ANY, label, helpString, kind)

        self.menucmd[menuItem.GetId()] = gcmd

        if len(gcmd) > 0 and \
                gcmd.split()[0] not in globalvar.grassCmd['all']:
            menuItem.Enable (False)

        rhandler = eval(handler)

        self.Bind(wx.EVT_MENU, rhandler, menuItem)





    def OnXTermNoXMon(self, event):
        """!
        Run commands that need xterm
        """
        self.OnXTerm(event, need_xmon = False)
        
    def OnXTerm(self, event, need_xmon = True):
        """!
        Run commands that need interactive xmon

        @param need_xmon True to start X monitor
        """
        # unset display mode
        del os.environ['GRASS_RENDER_IMMEDIATE']
        
        if need_xmon:
            # open next available xmon
            xmonlist = []
            
            # make list of xmons that are not running
            ret = gcmd.RunCommand('d.mon',
                                  flags = 'L',
                                  read = True)
            
            for line in ret.split('\n'):               
                line = line.strip()
                if line.startswith('x') and 'not running' in line:
                    xmonlist.append(line[0:2])
            
            # find available xmon
            xmon = xmonlist[0]
            
            # bring up the xmon
            cmdlist = ['d.mon', xmon]
            p = gcmd.Command(cmdlist, wait=False)
        
        # run the command        
        command = self.GetMenuCmd(event)
        command = ' '.join(command)
        
        gisbase = os.environ['GISBASE']
        
        if sys.platform == "win32":
            runbat = os.path.join(gisbase,'etc','grass-run.bat')
            cmdlist = ["start", runbat, runbat, command]
        else:
            if sys.platform == "darwin":
                xtermwrapper = os.path.join(gisbase,'etc','grass-xterm-mac')
            else:
                xtermwrapper = os.path.join(gisbase,'etc','grass-xterm-wrapper')
            
            grassrun = os.path.join(gisbase,'etc','grass-run.sh')
            cmdlist = [xtermwrapper, '-e', grassrun, command]
        
        p = gcmd.Command(cmdlist, wait=False)
        
        # reset display mode
        os.environ['GRASS_RENDER_IMMEDIATE'] = 'TRUE'

    def OnRunCmd(self, event):
        """Run command"""
        cmdString = event.GetString()

        if cmdString[:2] == 'd.' and not self.current:
            self.NewDisplay(show=True)
        
        cmd = shlex.split(str(cmdString))
        if len(cmd) > 1:
            self.goutput.RunCmd(cmd, switchPage=True)
        else:
            self.goutput.RunCmd(cmd, switchPage=False)
        
        self.OnUpdateStatusBar(None)


    def OnUpdateStatusBar(self, event):
        #if event is None:
         #   self.statusbar.SetStatusText("")
        #else:
         #   self.statusbar.SetStatusText(_("Type GRASS command and run by pressing ENTER"))
        print "asdf4"


    def __createToolBar(self):
        """!Creates toolbar"""

        self.toolbar = self.CreateToolBar()
        self.toolbar.SetToolBitmapSize(globalvar.toolbarSize)

        for each in self.ToolbarData():
            self.AddToolbarButton(self.toolbar, *each)
        self.toolbar.Realize()

        return self.toolbar

    def OnMenuHighlight(self, event):
        """
        Default menu help handler
        """
         # Show how to get menu item info from this event handler
        id = event.GetMenuId()
        item = self.GetMenuBar().FindItemById(id)
        if item:
            text = item.GetText()
            help = item.GetHelp()

        # but in this case just call Skip so the default is done
        event.Skip()

        
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

       # self._lmgr=wx.aui.AuiManager(self)
        self.pg_panel = MapFrame(parent=self.notebook, id=wx.ID_ANY, Map=render.Map(),  size=globalvar.MAP_WINDOW_SIZE,frame=self,flag=True,gismgr=self)
        
        self.disp_idx = self.disp_idx + 1
        self.notebook.AddPage(self.pg_panel, text="Display "+ str(self.disp_idx), select = True)


       # self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
       # self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnPageClosed)


        self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnCBPageChanged)
        self.notebook.Bind(FN.EVT_FLATNOTEBOOK_PAGE_CLOSING, self.OnCBPageClosed)


        return self.notebook

    def OnPageChanged(self, event):
        """!Page in notebook changed"""
        pageno = event.GetSelection()
        self.page = self.notebook.GetPage(pageno)
        if page == self.goutput.pageid:
            # remove '(...)'
            self.notebook.SetPageText(page, _("Command output"))
        
        event.Skip()

    def OnCBPageClosed(self, event):
        """
        Page of notebook closed
        Also close associated map display
        """
        self.curr_page = self.notebook.GetCurrentPage()
        if UserSettings.Get(group='manager', key='askOnQuit', subkey='enabled'):
            maptree = self.curr_page.maptree
            
            if self.workspaceFile:
                message = _("Do you want to save changes in the workspace?")
            else:
                message = _("Do you want to store current settings "
                            "to workspace file?")
            
            # ask user to save current settings
            if maptree.GetCount() > 0:
                dlg = wx.MessageDialog(self,
                                       message=message,
                                       caption=_("Close Map Display %d") % (self.curr_pagenum + 1),
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
        
        self.notebook.GetPage(event.GetSelection()).maptree.Map.Clean()
        self.notebook.GetPage(event.GetSelection()).maptree.Close(True)
        self.disp_idx = self.disp_idx - 1
        
        self.curr_page = None
        
        event.Skip()

    def OnCBPageChanged(self, event):
        """!Page in notebook (display) changed"""


        old_pgnum = event.GetOldSelection()
        new_pgnum = event.GetSelection()

        self.oldpage = self.notebook.GetPage(old_pgnum)

       
        self.curr_page   = self.notebook.GetCurrentPage()
        self.curr_pagenum = self.notebook.GetSelection()



  #      self.cmbMapset.SetValue(self.cb_loclist[self.disp_idx])
 #       self.cmbLocation.SetValue(self.cb_loclist[self.disp_idx])
#        self.disp_idx


        index  = self.notebook.GetSelection()
        self.page = self.notebook.GetPage(index)

    

        

 #       print index
#        print self.cb_mapfile
        #import pdb
       # pdb.set_trace()

        try:
            a_loc = str(self.cb_loclist[index])
            a_map =  str(self.cb_maplist[index])
          
           # a_mapfile = self.cb_mapfile[index]

        except IndexError:
            a_loc = "Select Location"
            a_map = "Select Mapset"

        self.cmbLocation.SetValue(a_loc)
        self.cmbMapset.SetValue(a_map)



        try:
            self.gisrc['LOCATION_NAME'] = self.cb_loclist[index]
            self.gisrc['MAPSET'] = self.cb_maplist[index]


        except:
            pass
        #self.page.Map.Region = self.page.Map.GetRegion()

        self.update_grassrc(self.gisrc)
    
        
        event.Skip()



    def OnGeorectify(self, event):
        """
        Launch georectifier module
        """
        georect.GeorectWizard(self)


    def OnGModeler(self, event):
        """!Launch Graphical Modeler"""
        win = gmodeler.ModelFrame(parent = self)
        win.CentreOnScreen()
        
        win.Show()


    def OnRunModel(self, event):
        """!Run model"""
        filename = ''
        dlg = wx.FileDialog(parent = self, message=_("Choose model to run"),
                            defaultDir = os.getcwd(),
                            wildcard=_("GRASS Model File (*.gxm)|*.gxm"))
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        
        if not filename:
            return
        
        self.model = gmodeler.Model()
        self.model.LoadModel(filename)
        self.SetStatusText(_('Validating model...'), 0)
        result =  self.model.Validate()
        if result:
            dlg = wx.MessageDialog(parent = self,
                                   message = _('Model is not valid. Do you want to '
                                               'run the model anyway?\n\n%s') % '\n'.join(errList),
                                   caption=_("Run model?"),
                                   style = wx.YES_NO | wx.NO_DEFAULT |
                                   wx.ICON_QUESTION | wx.CENTRE)
            ret = dlg.ShowModal()
            if ret != wx.ID_YES:
                return
        
        self.SetStatusText(_('Running model...'), 0)
        self.model.Run(log = self.goutput,
                       onDone = self.OnDone)


        
    def OnMapsets(self, event):
        """
        Launch mapset access dialog
        """
        dlg = preferences.MapsetAccess(parent=self, id=wx.ID_ANY)
        dlg.CenterOnScreen()

        # if OK is pressed...
        if dlg.ShowModal() == wx.ID_OK:
            ms = dlg.GetMapsets()
            # run g.mapsets with string of accessible mapsets
            gcmd.RunCommand('g.mapsets',
                            parent = self,
                            mapset = '%s' % ','.join(ms))
            
    def OnRDigit(self, event):
        """
        Launch raster digitizing module
        """
        pass

    def OnPageChanged(self,event):
        self.current = self.notebook.GetPage(event.GetSelection())
        #self.current = self.notebook.GetCurrentPage()
        #self.current.Map = self.GetMapDisplay()
        event.Skip()



    def OnPageClosed(self, event):
        """
        Page of notebook closed
        Also close associated map display
        """


#        if UserSettings.Get(group='manager', key='askOnQuit', subkey='enabled'):
#            maptree = self.current.maptree
#           
#            if self.workspaceFile:
#                message = _("Do you want to save changes in the workspace?")
#            else:
#                message = _("Do you want to store current settings "
#                            "to workspace file?")
#            
#            # ask user to save current settings
#            if maptree.GetCount() > 0:
#                dlg = wx.MessageDialog(self,
#                                       message=message,
#                                       caption=_("Close Map Display %d") % (self.disp_idx),
#                                       style=wx.YES_NO | wx.YES_DEFAULT |
#                                       wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
#                ret = dlg.ShowModal()
#                if ret == wx.ID_YES:
#                    if not self.workspaceFile:
#                        self.OnWorkspaceSaveAs()
#                    else:
#                        self.SaveToWorkspaceFile(self.workspaceFile)
#                elif ret == wx.ID_CANCEL:
#
#                    event.Veto()
#                    dlg.Destroy()
#                    return
#                dlg.Destroy()


        self.notebook.GetPage(event.GetSelection()).maptree.Map.Clean()
        self.disp_idx = self.disp_idx - 1
        self.notebook.DeletePage(self.notebook.GetCurrentPage())
        self.current = self.notebook.GetCurrentPage()
        #self.current.Map.Clean()
        event.Skip()

        
    def GetLogWindow(self):
        """!Get widget for command output"""
        return self.gmconsole.goutput
    
    def GetMenuCmd(self, event):
        """!Get GRASS command from menu item

        Return command as a list"""
        layer = None
        
        if event:
            cmd = self.menucmd[event.GetId()]
        
        try:
            cmdlist = cmd.split(' ')
        except: # already list?
            cmdlist = cmd
            
        # check list of dummy commands for GUI modules that do not have GRASS
        # bin modules or scripts. 
        if cmd in ['vcolors']:
            return cmdlist

        try:
            layer = self.current.maptree.layer_selected
            name = self.current.maptree.GetPyData(layer)[0]['maplayer'].name
            type = self.current.maptree.GetPyData(layer)[0]['type']
        except:
            layer = None
        if layer and len(cmdlist) == 1: # only if no paramaters given
            if (type == 'raster' and cmdlist[0][0] == 'r' and cmdlist[0][1] != '3') or \
                    (type == 'vector' and cmdlist[0][0] == 'v'):
                input = menuform.GUI().GetCommandInputMapParamKey(cmdlist[0])
                if input:
                    cmdlist.append("%s=%s" % (input, name))

        return cmdlist

    def RunMenuCmd(self, event):
        """!Run command selected from menu"""
        print "asdf"
        #cmd = self.GetMenuCmd(event)
        #goutput.GMConsole(self, pageid=1).RunCmd(cmd, switchPage=True)

    def OnMenuCmd(self, event, cmd = ''):
        """!Parse command selected from menu"""
        if event:
            cmd = self.GetMenuCmd(event)
        menuform.GUI().ParseCommand(cmd, parentframe=self)

    def OnChangeLocation(self, event):
        """Change current location"""
        pass
                    
    def OnChangeMapset(self, event):
        """Change current mapset"""
        pass
        
    def OnNewVector(self, event):
        """!Create new vector map layer"""
        name, add = gdialogs.CreateNewVector(self, cmd = (('v.edit',  { 'tool' : 'create' }, 'map')))
        
        if name and add:
            # add layer to map layer tree
            self.current.maptree.AddLayer(ltype='vector',
                                            lname=name,
                                            lchecked=True,
                                            lopacity=1.0,
                                            lcmd=['d.vect', 'map=%s' % name])
           
    def OnMenuTree(self, event):
        """!Show dialog with menu tree"""
        dlg = MenuTreeWindow(self)
        dlg.CentreOnScreen()
        dlg.Show()
    
    def OnAboutGRASS(self, event):
        """!Display 'About GRASS' dialog"""
        win = AboutWindow(self)
        win.Centre()
        win.Show(True)  
        
    def OnWorkspace(self, event):
        """!Workspace menu (new, load)"""
        point = wx.GetMousePosition()
        menu = wx.Menu()

        # Add items to the menu
        new = wx.MenuItem(menu, wx.ID_ANY, Icons["workspaceNew"].GetLabel())
        new.SetBitmap(Icons["workspaceNew"].GetBitmap(self.iconsize))
        menu.AppendItem(new)
        self.Bind(wx.EVT_MENU, self.OnWorkspaceNew, new)

        load = wx.MenuItem(menu, wx.ID_ANY, Icons["workspaceLoad"].GetLabel())
        load.SetBitmap(Icons["workspaceLoad"].GetBitmap(self.iconsize))
        menu.AppendItem(load)
        self.Bind(wx.EVT_MENU, self.OnWorkspaceLoad, load)

        # create menu
        self.PopupMenu(menu)
        menu.Destroy()

#    def OnWorkspaceNew(self, event=None):
#        """!Create new workspace file
#
#        Erase current workspace settings first"""
#
#        Debug.msg(4, "GMFrame.OnWorkspaceNew():")
#        
#        # start new map display if no display is available
#        if not self.current:
#            self.NewDisplay()
#        
#        maptree = self.current.maptree
#        
#        # ask user to save current settings
#        if maptree.GetCount() > 0:
#             dlg = wx.MessageDialog(self, message=_("Current workspace is not empty. "
#                                                    "Do you want to store current settings "
#                                                    "to workspace file?"),
#                                    caption=_("Create new workspace?"),
#                                    style=wx.YES_NO | wx.YES_DEFAULT | \
#                                        wx.CANCEL | wx.ICON_QUESTION)
#             ret = dlg.ShowModal()
#             if ret == wx.ID_YES:
#                 self.OnWorkspaceSaveAs()
#             elif ret == wx.ID_CANCEL:
#                 dlg.Destroy()
#                 return
#             
#             dlg.Destroy()
#        
#        # delete all items
#        maptree.DeleteAllItems()
#        
#        # add new root element
#        maptree.root = maptree.AddRoot("Map Layers")
#        self.current.maptree.SetPyData(maptree.root, (None,None))
#        
#        # no workspace file loaded
#        self.workspaceFile = None
#        self.SetTitle(self.baseTitle)


    def OnWorkspaceNew(self, event = None):
        """!Create new workspace file

        Erase current workspace settings first
        """
        Debug.msg(4, "GMFrame.OnWorkspaceNew():")
        
        # start new map display if no display is available
        if not self.curr_page:
            self.NewDisplay()
        
        maptree = self.curr_page.maptree
        
        # ask user to save current settings
        if self.workspaceFile and self.workspaceChanged:
            self.OnWorkspaceSave()
        elif self.workspaceFile is None and maptree.GetCount() > 0:
             dlg = wx.MessageDialog(self, message=_("Current workspace is not empty. "
                                                    "Do you want to store current settings "
                                                    "to workspace file?"),
                                    caption=_("Create new workspace?"),
                                    style=wx.YES_NO | wx.YES_DEFAULT | \
                                        wx.CANCEL | wx.ICON_QUESTION)
             ret = dlg.ShowModal()
             if ret == wx.ID_YES:
                 self.OnWorkspaceSaveAs()
             elif ret == wx.ID_CANCEL:
                 dlg.Destroy()
                 return
             
             dlg.Destroy()
        
        # delete all items
        maptree.DeleteAllItems()
        
        # add new root element
        maptree.root = maptree.AddRoot("Map Layers")
        self.curr_page.maptree.SetPyData(maptree.root, (None,None))
        
        # no workspace file loaded
        self.workspaceFile = None
        self.workspaceChanged = False
        self.SetTitle(self.baseTitle)

        
    def OnWorkspaceOpen(self, event=None):
        """!Open file with workspace definition"""
        dlg = wx.FileDialog(parent=self, message=_("Choose workspace file"),
                            defaultDir=os.getcwd(), wildcard="*.gxw")

        filename = ''
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

        if filename == '':
            return

        Debug.msg(4, "GMFrame.OnWorkspaceOpen(): filename=%s" % filename)

        # delete current layer tree content
        self.OnWorkspaceClose()
        
        self.LoadWorkspaceFile(filename)

        self.workspaceFile = filename
        self.SetTitle(self.baseTitle + " - " +  os.path.basename(self.workspaceFile))

    def LoadWorkspaceFile(self, filename):
        """!Load layer tree definition stored in GRASS Workspace XML file (gxw)

        @todo Validate against DTD
        
        @return True on success
        @return False on error
        """
        # dtd
        dtdFilename = os.path.join(globalvar.ETCWXDIR, "xml", "grass-gxw.dtd")
        
        # parse workspace file
        try:
            gxwXml = workspace.ProcessWorkspaceFile(etree.parse(filename))
        except Exception, err:
            raise gcmd.GStdError(_("Reading workspace file <%(file)s> failed.\n"
                                   "Invalid file, unable to parse XML document."
                                   "\n\n%(err)s") % { 'file' : filename, 'err': err},
                                 parent = self)
        
        busy = wx.BusyInfo(message=_("Please wait, loading workspace..."),
                           parent=self)
        wx.Yield()

        #
        # load layer manager window properties
        #
        if UserSettings.Get(group='workspace', key='posManager', subkey='enabled') is False:
            if gxwXml.layerManager['pos']:
                self.SetPosition(gxwXml.layerManager['pos'])
            if gxwXml.layerManager['size']:
                self.SetSize(gxwXml.layerManager['size'])
        
        #
        # start map displays first (list of layers can be empty)
        #
        displayId = 0
        mapdisplay = []
        for display in gxwXml.displays:
            mapdisplay.append(self.NewDisplay())
            maptree = self.notebook.GetPage(displayId).maptree
            
            # set windows properties
            mapdisplay[-1].SetProperties(render=display['render'],
                                         mode=display['mode'],
                                         showCompExtent=display['showCompExtent'],
                                         constrainRes=display['constrainRes'],
                                         projection=display['projection']['enabled'])

            if display['projection']['enabled']:
                if display['projection']['epsg']:
                    UserSettings.Set(group = 'display', key = 'projection', subkey = 'epsg',
                                     value = display['projection']['epsg'])
                    if display['projection']['proj']:
                        UserSettings.Set(group = 'display', key = 'projection', subkey = 'proj4',
                                         value = display['projection']['proj'])
            
            # set position and size of map display
            if UserSettings.Get(group='workspace', key='posDisplay', subkey='enabled') is False:
                if display['pos']:
                    mapdisplay[-1].SetPosition(display['pos'])
                if display['size']:
                    mapdisplay[-1].SetSize(display['size'])
                    
            # set extent if defined
            if display['extent']:
                w, s, e, n = display['extent']
                maptree.Map.region = maptree.Map.GetRegion(w=w, s=s, e=e, n=n)
                
            mapdisplay[-1].Show()
            
            displayId += 1
    
        maptree = None 
        selected = [] # list of selected layers
        # 
        # load list of map layers
        #
        for layer in gxwXml.layers:
            display = layer['display']
            maptree = self.notebook.GetPage(display).maptree
            
            newItem = maptree.AddLayer(ltype=layer['type'],
                                       lname=layer['name'],
                                       lchecked=layer['checked'],
                                       lopacity=layer['opacity'],
                                       lcmd=layer['cmd'],
                                       lgroup=layer['group'],
                                       lnviz=layer['nviz'],
                                       lvdigit=layer['vdigit'])
            
            if layer.has_key('selected'):
                if layer['selected']:
                    selected.append((maptree, newItem))
                else:
                    maptree.SelectItem(newItem, select=False)
            
        for maptree, layer in selected:
            if not maptree.IsSelected(layer):
                maptree.SelectItem(layer, select=True)
                maptree.layer_selected = layer
                
        busy.Destroy()
        
        if maptree:
            # reverse list of map layers
            maptree.Map.ReverseListOfLayers()

        for mdisp in mapdisplay:
            mdisp.MapWindow2D.UpdateMap()

        return True

    def OnWorkspaceLoad(self, event=None):
        """!Load given map layers into layer tree"""
        dialog = gdialogs.LoadMapLayersDialog(parent=self, title=_("Load map layers into layer tree"))

        if dialog.ShowModal() == wx.ID_OK:
            # start new map display if no display is available
            if not self.current:
                self.NewDisplay()

            maptree = self.current.maptree
            busy = wx.BusyInfo(message=_("Please wait, loading workspace..."),
                               parent=self)
            wx.Yield()

            for layerName in dialog.GetMapLayers():
                if dialog.GetLayerType() == 'raster':
                    cmd = ['d.rast', 'map=%s' % layerName]
                elif dialog.GetLayerType() == 'vector':
                    cmd = ['d.vect', 'map=%s' % layerName]
                newItem = maptree.AddLayer(ltype=dialog.GetLayerType(),
                                           lname=layerName,
                                           lchecked=True,
                                           lopacity=1.0,
                                           lcmd=cmd,
                                           lgroup=None)

            busy.Destroy()

    def OnWorkspaceLoadGrcFile(self, event):
        """!Load map layers from GRC file (Tcl/Tk GUI) into map layer tree"""
        dlg = wx.FileDialog(parent=self, message=_("Choose GRC file to load"),
                            defaultDir=os.getcwd(), wildcard="*.grc")

        filename = ''
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

        if filename == '':
            return

        Debug.msg(4, "GMFrame.OnWorkspaceLoadGrcFile(): filename=%s" % filename)

        # start new map display if no display is available
        if not self.current:
            self.NewDisplay()

        busy = wx.BusyInfo(message=_("Please wait, loading workspace..."),
                           parent=self)
        wx.Yield()

        maptree = None
        for layer in workspace.ProcessGrcFile(filename).read(self):
            maptree = self.gm_cb.GetPage(layer['display']).maptree
            newItem = maptree.AddLayer(ltype=layer['type'],
                                       lname=layer['name'],
                                       lchecked=layer['checked'],
                                       lopacity=layer['opacity'],
                                       lcmd=layer['cmd'],
                                       lgroup=layer['group'])

            busy.Destroy()
            
        if maptree:
            # reverse list of map layers
            maptree.Map.ReverseListOfLayers()

    def OnWorkspaceSaveAs(self, event=None):
        """!Save workspace definition to selected file"""

        dlg = wx.FileDialog(parent=self, message=_("Choose file to save current workspace"),
                            defaultDir=os.getcwd(), wildcard="*.gxw", style=wx.FD_SAVE)

        filename = ''
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()

        if filename == '':
            return False

        # check for extension
        if filename[-4:] != ".gxw":
            filename += ".gxw"

        if os.path.exists(filename):
            dlg = wx.MessageDialog(self, message=_("Workspace file <%s> already exists. "
                                                   "Do you want to overwrite this file?") % filename,
                                   caption=_("Save workspace"), style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if dlg.ShowModal() != wx.ID_YES:
                dlg.Destroy()
                return False

        Debug.msg(4, "GMFrame.OnWorkspaceSaveAs(): filename=%s" % filename)

        self.SaveToWorkspaceFile(filename)
        self.workspaceFile = filename
        self.SetTitle(self.baseTitle + " - " + os.path.basename(self.workspaceFile))

    def OnWorkspaceSave(self, event=None):
        """!Save file with workspace definition"""

        if self.workspaceFile:
            dlg = wx.MessageDialog(self, message=_("Workspace file <%s> already exists. "
                                                   "Do you want to overwrite this file?") % \
                                       self.workspaceFile,
                                   caption=_("Save workspace"), style=wx.YES_NO | wx.YES_DEFAULT | wx.ICON_QUESTION)
            if dlg.ShowModal() == wx.ID_NO:
                dlg.Destroy()
            else:
                Debug.msg(4, "GMFrame.OnWorkspaceSave(): filename=%s" % self.workspaceFile)
                self.SaveToWorkspaceFile(self.workspaceFile)
        else:
            self.OnWorkspaceSaveAs()

    def SaveToWorkspaceFile(self, filename):
        """!Save layer tree layout to workspace file

        Return True on success, False on error
        """

        try:
            file = open(filename, "w")
        except IOError:
            wx.MessageBox(parent=self,
                          message=_("Unable to open workspace file <%s> for writing.") % filename,
                          caption=_("Error"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
            return False

        try:
            workspace.WriteWorkspaceFile(lmgr=self, file=file)
        except StandardError, e:
            file.close()
            wx.MessageBox(parent=self,
                          message=_("Writing current settings to workspace file failed (%s)." % e),
                          caption=_("Error"),
                          style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
            return False

        file.close()
        
        return True
    
    def OnWorkspaceClose(self, event=None):
        """!Close file with workspace definition

        If workspace has been modified ask user to save the changes.
        """

        Debug.msg(4, "GMFrame.OnWorkspaceClose(): file=%s" % self.workspaceFile)
        self.workspaceFile = None
        self.SetTitle(self.baseTitle)

        displays = []
        for page in range(0, self.notebook.GetPageCount()):
            displays.append(self.notebook.GetPage(page).maptree.mapdisplay)
        
        for display in displays:
            display.OnCloseWindow(event)
        
        self.disp_idx = 0
        self.curr_page = None
        

    def RulesCmd(self, event, cmd = ''):
        """
        Launches dialog for commands that need rules
        input and processes rules
        """
        if event:
            cmd = self.GetMenuCmd(event)
                
        if cmd[0] == 'r.colors' or cmd[0] == 'vcolors':
            ctable = colorrules.ColorTable(self, cmd=cmd[0])
            ctable.Show()
        else:
            dlg = rules.RulesText(self, cmd=cmd)
            dlg.CenterOnScreen()
            if dlg.ShowModal() == wx.ID_OK:
                gtemp = utils.GetTempfile()
                output = open(gtemp, "w")
                try:
                    output.write(dlg.rules)
                finally:
                    output.close()
    
                cmdlist = [cmd[0],
                           'input=%s' % dlg.inmap,
                           'output=%s' % dlg.outmap,
                           'rules=%s' % gtemp]
    
                if dlg.overwrite == True:
                    cmdlist.append('--o')
    
                dlg.Destroy()
    
                self.goutput.RunCmd(cmdlist)

    def OnPreferences(self, event):
        """!General GUI preferences/settings"""
        if not self.dialogs['preferences']:
            dlg = preferences.PreferencesDialog(parent=self)
            self.dialogs['preferences'] = dlg
            self.dialogs['preferences'].CenterOnScreen()

        self.dialogs['preferences'].ShowModal()
        
    def DispHistogram(self, event):
        """
        Init histogram display canvas and tools
        """
        self.histogram = histogram.HistFrame(self,
                                             id=wx.ID_ANY, pos=wx.DefaultPosition, size=(400,300),
                                             style=wx.DEFAULT_FRAME_STYLE)

        #show new display
        self.histogram.Show()
        self.histogram.Refresh()
        self.histogram.Update()

    def DispProfile(self, event):
        """
        Init profile canvas and tools
        """
        self.profile = profile.ProfileFrame(self,
                                           id=wx.ID_ANY, pos=wx.DefaultPosition, size=(400,300),
                                           style=wx.DEFAULT_FRAME_STYLE)
        self.profile.Show()
        self.profile.Refresh()
        self.profile.Update()
        
    def DispMapCalculator(self, event):
        """
        Init map calculator for interactive creation of mapcalc statements
        """
        
        self.mapcalculator = mapcalculator.MapCalcFrame(self, wx.ID_ANY, title='',
                                                        dimension=2)

    def Disp3DMapCalculator(self, event):
        """
        Init map calculator for interactive creation of mapcalc statements
        """
        
        self.mapcalculator = mapcalculator.MapCalcFrame(self, wx.ID_ANY, title='',
                                                        dimension=3)

    def AddToolbarButton(self, toolbar, label, icon, help, handler):
        """!Adds button to the given toolbar"""

        if not label:
            toolbar.AddSeparator()
            return
        tool = toolbar.AddLabelTool(id=wx.ID_ANY, label=label, bitmap=icon, shortHelp=help)
        self.Bind(wx.EVT_TOOL, handler, tool)

    def ToolbarData(self):

        return   (
                 ('newdisplay', Icons["newdisplay"].GetBitmap(),
                  Icons["newdisplay"].GetLabel(), self.OnNewDisplay),
                 ('', '', '', ''),
                 ('workspaceLoad', Icons["workspaceLoad"].GetBitmap(),
                  Icons["workspaceLoad"].GetLabel(), self.OnWorkspace),
                 ('workspaceOpen', Icons["workspaceOpen"].GetBitmap(),
                  Icons["workspaceOpen"].GetLabel(), self.OnWorkspaceOpen),
                 ('workspaceSave', Icons["workspaceSave"].GetBitmap(),
                  Icons["workspaceSave"].GetLabel(), self.OnWorkspaceSave),
                 ('', '', '', ''),
                 ('addrast', Icons["addrast"].GetBitmap(),
                  Icons["addrast"].GetLabel(), self.OnAddRaster),
                 ('addshaded', Icons["addshaded"].GetBitmap(),
                  _("Add various raster-based map layers"), self.OnAddRasterMisc),
                 ('addvect', Icons["addvect"].GetBitmap(),
                  Icons["addvect"].GetLabel(), self.OnAddVector),
                 ('addthematic', Icons["addthematic"].GetBitmap(),
                  _("Add various vector-based map layer"), self.OnAddVectorMisc),
                 ('addcmd',  Icons["addcmd"].GetBitmap(),
                  Icons["addcmd"].GetLabel(),  self.OnAddCommand),
                 ('addgrp',  Icons["addgrp"].GetBitmap(),
                  Icons["addgrp"].GetLabel(), self.OnAddGroup),
                 ('addovl',  Icons["addovl"].GetBitmap(),
                  Icons["addovl"].GetLabel(), self.OnAddOverlay),
                 ('delcmd',  Icons["delcmd"].GetBitmap(),
                  Icons["delcmd"].GetLabel(), self.OnDeleteLayer),
                 ('', '', '', ''),
                 ('attrtable', Icons["attrtable"].GetBitmap(),
                  Icons["attrtable"].GetLabel(), self.OnShowAttributeTable)
                  )

    def OnImportDxfFile(self, event):
        """!Convert multiple DXF layers to GRASS vector map layers"""
        dlg = gdialogs.MultiImportDialog(parent=self, type='dxf',
                                         title=_("Import DXF layers"))
        dlg.ShowModal()

    def OnImportGdalLayers(self, event):
        """!Convert multiple GDAL layers to GRASS raster map layers"""
        dlg = gdialogs.MultiImportDialog(parent=self, type='gdal',
                                         title=_("Import GDAL layers"))
        dlg.ShowModal()

    def OnLinkGdalLayers(self, event):
        """!Link multiple GDAL layers to GRASS raster map layers"""
        dlg = gdialogs.MultiImportDialog(parent=self, type='gdal',
                                         title=_("Link GDAL layers"),
                                         link = True)
        dlg.ShowModal()
        
    def OnImportOgrLayers(self, event):
        """!Convert multiple OGR layers to GRASS vector map layers"""
        dlg = gdialogs.MultiImportDialog(parent=self, type='ogr',
                                         title=_("Import OGR layers"))
        dlg.ShowModal()
    
    def OnLinkOgrLayers(self, event):
        """!Links multiple OGR layers to GRASS vector map layers"""
        dlg = gdialogs.MultiImportDialog(parent=self, type='ogr',
                                         title=_("Link OGR layers"),
                                         link = True)
        dlg.ShowModal()
        
    def OnImportWMS(self, event):
        """!Import data from OGC WMS server"""
        dlg = ogc_services.WMSDialog(parent = self, service = 'wms')
        dlg.CenterOnScreen()
        
        if dlg.ShowModal() == wx.ID_OK: # -> import layers
            layers = dlg.GetLayers()
            
            if len(layers.keys()) > 0:
                for layer in layers.keys():
                    cmd = ['r.in.wms',
                           'mapserver=%s' % dlg.GetSettings()['server'],
                           'layers=%s' % layer,
                           'output=%s' % layer]
                    styles = ','.join(layers[layer])
                    if styles:
                        cmd.append('styles=%s' % styles)
                    self.goutput.RunCmd(cmd, switchPage = True)
            else:
                self.goutput.WriteWarning(_("Nothing to import. No WMS layer selected."))
        
        dlg.Destroy()
        
    def OnShowAttributeTable(self, event):
        """
        Show attribute table of the given vector map layer
        """
        if not self.current:
            self.MsgNoLayerSelected()
            return
        
        layer = self.current.maptree.layer_selected
        # no map layer selected
        if not layer:
            self.MsgNoLayerSelected()
            return
        
        # available only for vector map layers
        try:
            maptype = self.current.maptree.GetPyData(layer)[0]['maplayer'].type
        except:
            maptype = None
        
        if not maptype or maptype != 'vector':
            wx.MessageBox(parent=self,
                          message=_("Attribute management is available only "
                                    "for vector maps."),
                          caption=_("Message"),
                          style=wx.OK | wx.ICON_INFORMATION | wx.CENTRE)
            return
        
        if not self.current.maptree.GetPyData(layer)[0]:
            return
        dcmd = self.current.maptree.GetPyData(layer)[0]['cmd']
        if not dcmd:
            return
        
        busy = wx.BusyInfo(message=_("Please wait, loading attribute data..."),
                           parent=self)
        wx.Yield()
        
        dbmanager = dbm.AttributeManager(parent=self, id=wx.ID_ANY,
                                         size=wx.Size(500, 300),
                                         item=layer, log=self.goutput)
        
        busy.Destroy()
        
        # register ATM dialog
        self.dialogs['atm'].append(dbmanager)
        
        # show ATM window
        dbmanager.Show()
        
    def OnNewDisplay(self, event=None):
        """!Create new layer tree and map display instance"""
        self.NewDisplay()

    def NewDisplay(self):
        """!Create new layer tree, which will
        create an associated map display frame

        @param show show map display window if True

        @return reference to mapdisplay intance
        """
        Debug.msg(1, "GMFrame.NewDisplay(): idx=%d" % self.disp_idx)

        #wx.MessageBox(parent=self,
        #              message=_("This part is under development. New display does not work when you change location and mapset"),
         #             caption=_("Data Catalog"),
         #             style=wx.OK | wx.ICON_INFORMATION | wx.CENTRE)

        # make a new page in the bookcontrol for the layer tree (on page 0 of the notebook)

        self.disp_idx = self.disp_idx + 1
#        self.curr_pagenum  = self.disp_idx
        self.locationchange = True

#        self.cb_loclist.append( str(self.cmbLocation.GetValue()) )
 #       self.cb_maplist.append( str(self.cmbMapset.GetValue()) )
    
        #print self.cb_maplist
        #print self.cb_loclist

        
        self.page = MapFrame(parent=self.notebook, id=wx.ID_ANY, Map=render.Map(),  size=globalvar.MAP_WINDOW_SIZE,frame=self)
        self.notebook.AddPage(self.page, text="Display "+ str(self.disp_idx), select = True)

        self.current = self.notebook.GetCurrentPage()


        

    # toolBar button handlers
    def OnAddRaster(self, event):
        """!Add raster map layer"""
        #create image list to use with layer tree
        il = wx.ImageList(16, 16, mask=False)

        trart = wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, (16, 16))
        self.folder_open = il.Add(trart)
        trart = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16))
        self.folder = il.Add(trart)

        bmpsize = (16, 16)
        trgif = Icons["addrast"].GetBitmap(bmpsize)
        self.rast_icon = il.Add(trgif)

        trgif = Icons["addrast3d"].GetBitmap(bmpsize)
        self.rast3d_icon = il.Add(trgif)

        trgif = Icons["addrgb"].GetBitmap(bmpsize)
        self.rgb_icon = il.Add(trgif)
        
        trgif = Icons["addhis"].GetBitmap(bmpsize)
        self.his_icon = il.Add(trgif)

        trgif = Icons["addshaded"].GetBitmap(bmpsize)
        self.shaded_icon = il.Add(trgif)

        trgif = Icons["addrarrow"].GetBitmap(bmpsize)
        self.rarrow_icon = il.Add(trgif)

        trgif = Icons["addrnum"].GetBitmap(bmpsize)
        self.rnum_icon = il.Add(trgif)

        trgif = Icons["addvect"].GetBitmap(bmpsize)
        self.vect_icon = il.Add(trgif)

        trgif = Icons["addthematic"].GetBitmap(bmpsize)
        self.theme_icon = il.Add(trgif)

        trgif = Icons["addchart"].GetBitmap(bmpsize)
        self.chart_icon = il.Add(trgif)

        trgif = Icons["addgrid"].GetBitmap(bmpsize)
        self.grid_icon = il.Add(trgif)

        trgif = Icons["addgeodesic"].GetBitmap(bmpsize)
        self.geodesic_icon = il.Add(trgif)

        trgif = Icons["addrhumb"].GetBitmap(bmpsize)
        self.rhumb_icon = il.Add(trgif)

        trgif = Icons["addlabels"].GetBitmap(bmpsize)
        self.labels_icon = il.Add(trgif)

        trgif = Icons["addcmd"].GetBitmap(bmpsize)
        self.cmd_icon = il.Add(trgif)

#        self.current.maptree.AssignImageList(il)

        
        self.AddRaster(event)
        
    def OnAddRasterMisc(self, event):
        """!Add raster menu"""
        # start new map display if no display is available
        if not self.current:
            self.NewDisplay()

        point = wx.GetMousePosition()
        rastmenu = wx.Menu()

        # add items to the menu
        if self.current.maptree.mapdisplay.toolbars['nviz']:
            addrast3d = wx.MenuItem(rastmenu, -1, Icons ["addrast3d"].GetLabel())
            addrast3d.SetBitmap(Icons["addrast3d"].GetBitmap (self.iconsize))
            rastmenu.AppendItem(addrast3d)
            self.Bind(wx.EVT_MENU, self.AddRaster3d, addrast3d)

        addshaded = wx.MenuItem(rastmenu, -1, Icons ["addshaded"].GetLabel())
        addshaded.SetBitmap(Icons["addshaded"].GetBitmap (self.iconsize))
        rastmenu.AppendItem(addshaded)
        self.Bind(wx.EVT_MENU, self.AddShaded, addshaded)

        addrgb = wx.MenuItem(rastmenu, -1, Icons["addrgb"].GetLabel())
        addrgb.SetBitmap(Icons["addrgb"].GetBitmap(self.iconsize))
        rastmenu.AppendItem(addrgb)
        self.Bind(wx.EVT_MENU, self.AddRGB, addrgb)

        addhis = wx.MenuItem(rastmenu, -1, Icons ["addhis"].GetLabel())
        addhis.SetBitmap(Icons["addhis"].GetBitmap (self.iconsize))
        rastmenu.AppendItem(addhis)
        self.Bind(wx.EVT_MENU, self.AddHIS, addhis)

        addrastarrow = wx.MenuItem(rastmenu, -1, Icons ["addrarrow"].GetLabel())
        addrastarrow.SetBitmap(Icons["addrarrow"].GetBitmap (self.iconsize))
        rastmenu.AppendItem(addrastarrow)
        self.Bind(wx.EVT_MENU, self.AddRastarrow, addrastarrow)

        addrastnums = wx.MenuItem(rastmenu, -1, Icons ["addrnum"].GetLabel())
        addrastnums.SetBitmap(Icons["addrnum"].GetBitmap (self.iconsize))
        rastmenu.AppendItem(addrastnums)
        self.Bind(wx.EVT_MENU, self.AddRastnum, addrastnums)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(rastmenu)
        rastmenu.Destroy()
        
        # show map display
        #self.curr_page.maptree.mapdisplay.Show()

    def OnAddVector(self, event):
        """!Add vector map layer"""
        # start new map display if no display is available
        if not self.current:
            self.NewDisplay()
        
        self.AddVector(event)
        
    def OnAddVectorMisc(self, event):
        """!Add vector menu"""
        # start new map display if no display is available
        if not self.current:
            self.NewDisplay()

        point = wx.GetMousePosition()
        vectmenu = wx.Menu()
        
        addtheme = wx.MenuItem(vectmenu, -1, Icons["addthematic"].GetLabel())
        addtheme.SetBitmap(Icons["addthematic"].GetBitmap(self.iconsize))
        vectmenu.AppendItem(addtheme)
        self.Bind(wx.EVT_MENU, self.AddThemeMap, addtheme)

        addchart = wx.MenuItem(vectmenu, -1, Icons["addchart"].GetLabel())
        addchart.SetBitmap(Icons["addchart"].GetBitmap(self.iconsize))
        vectmenu.AppendItem(addchart)
        self.Bind(wx.EVT_MENU, self.AddThemeChart, addchart)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(vectmenu)
        vectmenu.Destroy()

        # show map display
        #self.curr_page.maptree.mapdisplay.Show()

    def OnAddOverlay(self, event):
        """!Add overlay menu""" 
        # start new map display if no display is available
        if not self.curent:
            self.NewDisplay()

        point = wx.GetMousePosition()
        ovlmenu = wx.Menu()

        addgrid = wx.MenuItem(ovlmenu, wx.ID_ANY, Icons["addgrid"].GetLabel())
        addgrid.SetBitmap(Icons["addgrid"].GetBitmap(self.iconsize))
        ovlmenu.AppendItem(addgrid)
        self.Bind(wx.EVT_MENU, self.AddGrid, addgrid)
        
        addlabels = wx.MenuItem(ovlmenu, wx.ID_ANY, Icons["addlabels"].GetLabel())
        addlabels.SetBitmap(Icons["addlabels"].GetBitmap(self.iconsize))
        ovlmenu.AppendItem(addlabels)
        self.Bind(wx.EVT_MENU, self.OnAddLabels, addlabels)
        
        addgeodesic = wx.MenuItem(ovlmenu, wx.ID_ANY, Icons["addgeodesic"].GetLabel())
        addgeodesic.SetBitmap(Icons["addgeodesic"].GetBitmap(self.iconsize))
        ovlmenu.AppendItem(addgeodesic)
        self.Bind(wx.EVT_MENU, self.AddGeodesic, addgeodesic)
        
        addrhumb = wx.MenuItem(ovlmenu, wx.ID_ANY, Icons["addrhumb"].GetLabel())
        addrhumb.SetBitmap(Icons["addrhumb"].GetBitmap(self.iconsize))
        ovlmenu.AppendItem(addrhumb)
        self.Bind(wx.EVT_MENU, self.AddRhumb, addrhumb)

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(ovlmenu)
        ovlmenu.Destroy()

        # show map display
        self.curr_page.maptree.mapdisplay.Show()

    def AddRaster(self, event):
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('raster') 

    def AddRaster3d(self, event):
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('3d-raster')

    def AddRGB(self, event):
        """!Add RGB layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('rgb')

    def AddHIS(self, event):
        """!Add HIS layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('his')

    def AddShaded(self, event):
        """!Add shaded relief map layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('shaded')

    def AddRastarrow(self, event):
        """!Add raster flow arrows map"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('rastarrow')

    def AddRastnum(self, event):
        """!Add raster map with cell numbers"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('rastnum')

    def AddVector(self, event):
        """!Add vector layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('vector')

    def AddThemeMap(self, event):
        """!Add thematic map layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('thememap')

    def AddThemeChart(self, event):
        """!Add thematic chart layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('themechart')

    def OnAddCommand(self, event):
        """!Add command line layer"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('command')

    def OnAddGroup(self, event):
        """!Add layer group"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('group')

    def AddGrid(self, event):
        """!Add layer grid"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('grid')

    def AddGeodesic(self, event):
        """!Add layer geodesic"""
        self.curr_page.maptree.AddLayer('geodesic')

    def AddRhumb(self, event):
        """!Add layer rhumb"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('rhumb')

    def OnAddLabels(self, event):
        """!Add layer vector labels"""
        if not self.current:
            self.NewDisplay()

        self.current.maptree.AddLayer('labels')

    def OnDeleteLayer(self, event):
        """
        Delete selected map display layer in GIS Manager tree widget
        """
        if UserSettings.Get(group='manager', key='askOnRemoveLayer', subkey='enabled'):
            layerName = ''
            for item in self.current.maptree.GetSelections():
                name = str(self.current.maptree.GetItemText(item))
                idx = name.find('(opacity')
                if idx > -1:
                    layerName += '<' + name[:idx].strip(' ') + '>,\n'
                else:
                    layerName += '<' + name + '>,\n'
            layerName = layerName.rstrip(',\n')
            
            if len(layerName) > 2: # <>
                message = _("Do you want to remove map layer(s)\n%s\n"
                            "from layer tree?") % layerName
            else:
                message = _("Do you want to remove selected map layer(s) "
                            "from layer tree?")

            dlg = wx.MessageDialog (parent=self, message=message,
                                    caption=_("Remove map layer"),
                                    style=wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)

            if dlg.ShowModal() in [wx.ID_NO, wx.ID_CANCEL]:
                dlg.Destroy()
                return

            dlg.Destroy()

        for layer in self.current.maptree.GetSelections():
            self.current.maptree.Delete(layer) 



        item = self.current.maptree.item
        try:
            self.current.maptree.item.properties.Close(True)
        except:
            pass

        #if item != self.current.maptree.root:
           # Debug.msg (3, "LayerTree.OnDeleteLayer(): name=%s" % \
            #               (self.current.maptree.GetItemText(item)))
       # else:
         #   self.current.maptree.root = None

        # unselect item
        self.current.maptree.Unselect()
        self.current.maptree.layer_selected = None

        #try:
       # if self.current.maptree.GetPyData(item)[0]['type'] != 'group':
        nb =        self.notebook.GetCurrentPage()
        #print nb.maptree
        index = self.notebook.GetSelection()
        try:
            nb.Map.DeleteLayer( self.ltree.layer[index])
            nb.maptree.layer.remove(self.ltree.layer[index])
        except:
            pass
        
        #except:
         #   pass

        # redraw map if auto-rendering is enabled
        self.current.maptree.rerender = True
        self.current.maptree.reorder = True
        #if self.mapdisplay.statusbarWin['render'].GetValue():
        #    print "*** Delete OnRender *****"
        #    self.mapdisplay.OnRender(None)


  #      if self.mapdisplay.toolbars['vdigit']:
   #         self.mapdisplay.toolbars['vdigit'].UpdateListOfLayers (updateTool=True)

        # update progress bar range (mapwindow statusbar)
 #       self.mapdisplay.statusbarWin['progress'].SetRange(len(self.Map.GetListOfLayers(l_active=True)))

        #self.current.Map.UpdateMap(render=True)

        
    def OnKey(self, event):
        """!Check hotkey"""
        try:
            kc = chr(event.GetKeyCode())
        except ValueError:
            event.Skip()
            return
        
        if event.AltDown():
            if kc == 'R':
                self.OnAddRaster(None)
            elif kc == 'V':
                self.OnAddVector(None)
        
        event.Skip()
        
    def OnCloseWindow(self, event):
        """!Cleanup when wxGUI is quit"""
        count = self.notebook.GetPageCount()
        index = 0
        while index < count:
            self.current = self.notebook.GetPage(index)
            self.current.Map.Clean()
            index = index+1

        self.notebook.DeleteAllPages()
        self.Destroy()


        
    def MsgNoLayerSelected(self):
        """!Show dialog message 'No layer selected'"""
        wx.MessageBox(parent=self,
                      message=_("No map layer selected. Operation cancelled."),
                      caption=_("Message"),
                      style=wx.OK | wx.ICON_INFORMATION | wx.CENTRE)
          


    def OnMapsetChange(self,event):
        """
        Create the tree nodes based on selected location and mapset.
        Also update gisrc and grassrc files.
        """
       
        self.page = self.notebook.GetCurrentPage()
        
        self.page.maptree.AddTreeNodes(self.cmbLocation.GetValue(),self.cmbMapset.GetValue())	
        self.gisrc['LOCATION_NAME'] = str(self.cmbLocation.GetValue())
        self.gisrc['MAPSET'] = str(self.cmbMapset.GetValue())
        self.update_grassrc(self.gisrc)
        

        self.page = self.notebook.GetPage(self.notebook.GetSelection())
        self.page.Map.__init__()	
        self.page.Map.region = self.page.Map.GetRegion()
        if version == "6.5.svn":
            self.page.Map.projinfo = self.page.Map._projInfo()
        else:
            self.page.Map.projinfo = self.page.Map.ProjInfo()

        self.page.Map.wind = self.page.Map.GetWindow()
        
        if self.locationchange == True:
            self.cb_loclist.append( str(self.cmbLocation.GetValue()) )
            self.cb_maplist.append( str(self.cmbMapset.GetValue()) )

            #self.cb_mapfile.append( self.page.Map)
            self.locationchange = False

    

    
        
             



        
    def OnRunScript():
        print "for grass7"

    def OnQuit():
        print "for grass7"

    def OnLocationChange(self,event):
        """
        Populate mapset combobox with selected location.
        """



        self.cmbMapset.Clear()
        self.cmbMapset.SetValue("Select Mapset")
        #self.ltree.DeleteAllItems()


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

        #Event bindings for tree -(display,popup,label edit.)
        #self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.ltree.OnDisplay,self.ltree)
        #self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,self.ltree.OnTreePopUp,self.ltree)
        #self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.ltree.OnEndRename,self.ltree)
       # self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.ltree.OnBeginRename,self.ltree)

	    #Event bindings for tree menu
        #self.Bind(wx.EVT_MENU,self.ltree.OnCopy,id=self.ltree.ID_COPY)
        #self.Bind(wx.EVT_MENU,self.ltree.OnRename,id=self.ltree.ID_REN)
        #self.Bind(wx.EVT_MENU,self.ltree.OnDelete,id=self.ltree.ID_DEL)
        #self.Bind(wx.EVT_MENU,self.ltree.OnOssim,id=self.ltree.ID_OSSIM)


        self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)

	    #Event bindings for v/r.info checkbox
	    #self.Bind(wx.EVT_CHECKBOX, self.OnToggleInfo,self.chkInfo)
	    #self.Bind(wx.EVT_CHECKBOX, self.OnToggleExpand,self.treeExpand)

    def OnToggleExpand(self,event):
        if self.treeExpand.IsChecked():
            if not self.gmconsole:
                self.gmconsole = GLog(parent=self)
               # self.gmconsole.show()
#                sys.exit(0)
            else:
                self.gmconsole.Raise()
        else:
            self.gmconsole.Destroy()
 
    def doLayout(self):

	    #combo panel sizers
        self.cmbSizer.Add(self.cmbLocation)
        self.cmbSizer.Add(self.cmbMapset)
        self.cmbSizer.Add(self.treeExpand)
        #splitter window sizers
        self.mSizer.Add(self.cmbPanel,flag=wx.EXPAND)
        #self.mSizer.Add(self.win, 1, wx.EXPAND)
        #self.leftSizer.Add(self.ltree,1,wx.EXPAND)
        self.mSizer.Add(self.notebook,1,wx.EXPAND)

        self.cmbPanel.SetSizer(self.cmbSizer)
        self.SetSizer(self.mSizer)
       # self.pLeft.SetSizer(self.leftSizer)
        #self.pRight.SetSizer(self.rightSizer)



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
        version = os.getenv("GRASS_VERSION")
        if version == "7.0.svn":
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
    





