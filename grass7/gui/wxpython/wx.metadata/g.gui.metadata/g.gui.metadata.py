#!/usr/bin/env python
# -*- coding: utf-8
"""
@module  g.gui.metadata
@brief   GUI components of metadata editor

Classes:
 - g.gui.metadata::MdMainFrame
 - g.gui.metadata::MdDataCatalog
 - g.gui.metadata::NotebookRight
 - g.gui.metadata::MDHelp
 - g.gui.metadata::TreeBrowser
 - g.gui.metadata::MdValidator
 - g.gui.metadata::MdEditConfigPanel
 - g.gui.metadata::MdToolbar

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

#%module
#% description: Tool for creating and modifying map's metadata.
#% keyword: general
#% keyword: GUI
#% keyword: metadata
#%end

import os
import sys
import glob
from lxml import etree

sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), 'etc', 'mdlib'))
sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), 'etc', 'pdf'))
import wx
from wx.lib.buttons import ThemedGenBitmapTextButton as BitmapBtnTxt
from wx import SplitterWindow, EVT_BUTTON
from wx.lib.pubsub import setupkwargs, pub

import grass.script as grass
import grass.script.setup as gsetup
import webbrowser


import mdgrass
import mdutil
from mdpdffactory import PdfCreator

from core.utils import _
from editor import MdMainEditor
from lmgr import datacatalog
from core.gcmd import RunCommand, GError, GMessage
import grass.temporal as tgis
from core.utils import GetListOfLocations, ListOfMapsets
#===============================================================================
# MAIN FRAME
#===============================================================================
class MdMainFrame(wx.Frame):

    '''Main frame of metadata editor
    '''

    def __init__(self, jinjaPath=None, xmlPath=None, init=False):
        '''
        @param jinjaPath: path to jinja profile
        @param xmlPath: path to xml with will be read by editor
        @var first,firstAfterChoice,second,secondAfterChoice,secondMultiEdit: initMultipleEditor() and onInitEditor() handler
        @var self. initMultipleEditor() and onInitEditor() handler
        @var self.templateEditor: true= Editor is in mode 'Template creator(widgets with chkbox)'
        @var nameTMPprofile: in case if 'profile editor is on' this var holds name oof temporaly jinja profile
        @var batch: if true multiple editing metadata of maps is ON
        '''
        wx.Frame.__init__(self, None, title="Metadata Editor", size=(650, 500))
        self.initDefaultPathStorageMetadata()

        self.jinjaPath = jinjaPath
        self.xmlPath = xmlPath
        self.first = True
        self.firstAfterChoice = False
        self.second = False
        self.secondAfterChoice = False
        self.secondMultiEdit = False
        self.md=None
        self.templateEditor = False
        self.sb = self.CreateStatusBar()

        self.cres = 0  # resizeFrame
        self.nameTMPteplate = None
        self.batch = False
        self.mdCreator=None
        self.editStatus=None
        self.onInitEditor()

        pub.subscribe(self.initNewMD, 'NEW_MD.create')
        pub.subscribe(self.onEditingMode, 'EDITING_MODE.update')
        pub.subscribe(self.setStatusbarText, 'STATUS_BAR_TEXT.update')
        pub.subscribe(self.onExportTemplate, 'EXPORT_TEMPLATE.create')
        pub.subscribe(self.onExportPDF, 'EXPORT_PDF.create')

        pub.subscribe(self.onExportXML, 'EXPORT_XML.create')
        pub.subscribe(self.onEditMapMetadata, 'EDIT_MAP_METADATA.create')
        pub.subscribe(self.onInitEditor, 'INIT_EDITOR.create')
        pub.subscribe(self.onTemplateEditor, 'TEMPLATE_EDITOR_STATUS.update')
        pub.subscribe(self.onHideLeftPanel, 'HIDE_LEFT_PANEL.update')
        pub.subscribe(self.onRefreshTreeBrowser, 'REFRESH_TREE_BROWSER.update')
        pub.subscribe(self.onChangeEditMapProfile, 'ISO_PROFILE.update')
        pub.subscribe(self.onUpdateGrassMetadata, 'GRASS_METADATA.update')
        pub.subscribe(self.setMdDestionation, 'MD_DESTINATION.update')
        pub.subscribe(self.onSetJaX, 'SET_JINJA_AND_XML.update')

    def onSetJaX(self, jinja, xml):
        '''Set profile ad xml paths
        '''
        self.jinjaPath = jinja
        self.xmlPath = xml

    def setMdDestionation(self, value):
        '''Set md
        '''
        self.mdDestination = value

    def initDefaultPathStorageMetadata(self):
        '''set working folder
        '''
        self.mdDestination = os.path.join(mdutil.pathToMapset(), 'metadata')
        if not os.path.exists(self.mdDestination):
            os.makedirs(self.mdDestination)

    def onUpdateGrassMetadata(self):
        '''Update r.support and v.support
        '''
        md = self.editor.saveMDfromGUI()
        self.mdCreator.updateGrassMd(md)
        GMessage('GRASS GIS metadata has been updated')

    def onChangeEditMapProfile(self):
        '''Update vars
        '''
        self.profileChoice = self.configPanelLeft.comboBoxProfile.GetValue()
        self.ntbRight.profile = self.profileChoice

    def onExportTemplate(self, outPath, outFileName):
        '''Export defined(pre-filled) template
        '''
        self.editor.exportTemplate(self.jinjaPath,
                                   outPath=outPath,
                                   xmlOutName=outFileName)

    def onExportPDF(self, outPath, outFileName):
        self.initNewMD()
        pdfFile=os.path.join(outPath,outFileName)

        if self.mdCreator is None and self.toolbar.extendEdit: #if editing map from grass database
            profileName=os.path.basename(self.jinjaPath)
            xmlFile=os.path.basename(self.xmlPath)
            doc = PdfCreator(self.md, pdfFile, map=None, type=None,filename=xmlFile,profile=profileName)
        else: #if editing map from external editor
            filename,type,map,profile=self.mdCreator.getMapInfo()
            doc = PdfCreator(self.md, pdfFile, map, type,filename,profile)
        try:
            path=doc.createPDF()
            GMessage('Metadata report has been exported to < %s >'%path)
        except:
            GError('Export pdf error %s'% sys.exc_info()[0])


    def onExportXML(self, outPath, outFileName):
        '''Save metadta xml file
        '''
        if outPath is None and outFileName is None:
            XMLhead, XMLtail = os.path.split(self.xmlPath)
            self.editor.exportToXml(self.jinjaPath,
                                    outPath=XMLhead,
                                    xmlOutName=XMLtail,
                                    msg=False)
        else:
            self.editor.exportToXml(self.jinjaPath,
                                    outPath=outPath,
                                    xmlOutName=outFileName,
                                    msg=True)

    def onRefreshTreeBrowser(self):
        '''Update changes from editor in tree browser
        '''
        path = os.path.dirname(os.path.realpath(__file__))
        name = 'refreshTreeBrowser.xml'
        self.editor.exportToXml(self.jinjaPath,
                                outPath=path,
                                xmlOutName=name,
                                msg=False)

        pathName = os.path.join(path, name)
        self.ntbRight.refreshXmlBrowser(pathName)
        os.remove(pathName)

    def setStatusbarText(self, text):
        '''Set status text
        '''
        self.sb.SetStatusText(text)

    def onTemplateEditor(self, value, template=None):
        '''Update local var
        '''
        self.templateEditor = value
        if template == None:
            self.nameTMPteplate = 'TMPtemplate'
        if template == False:
            self.nameTMPteplate = None

    def initNewMD(self):
        '''Init new md OWSLib  object
        '''
        self.md=self.editor.saveMDfromGUI()
        self.ntbRight.md = self.editor.md


    def resizeFrame(self, x1=1, y1=0):
        '''Some widgets need refresh frame for proper working
        '''
        self.cres += 1
        if (self.cres % 2 == 0) and x1 == 1 and y1 == 0:
            x1 = -1
        x, y = self.GetSize()
        self.SetSize((x + x1, y + y1))

    def onHideLeftPanel(self):
        '''In editing mode config panel is hidden
        '''
        self.toolbar.bttNew.Enable()
        self.Hsizer.Remove(self.leftPanel)
        self.Hsizer.Layout()
        self.leftPanel.SetSize((1, 1))

    def onEditingMode(self, editStatus):
        self.resizeFrame()
        self.editStatus=editStatus
        self.Layout()

        if editStatus:
            self.MdDataCatalogPanelLeft.Show()
            self.toolbar.bttLoad.Disable()
            self.toolbar.bttLoadXml.Disable()
        else:
            self.MdDataCatalogPanelLeft.Hide()
            self.toolbar.bttEdit.Disable()
            self.toolbar.bttCreateTemplate.Disable()
            self.toolbar.bttLoad.Enable()
            self.toolbar.bttLoadXml.Enable()
            self.sb.SetStatusText('')
            self.MdDataCatalogPanelLeft.UnselectAll()

    def onEditMapMetadata(self, multipleEditing=False):
        '''Initialize editor by selection of GRASS map in data catalog
        @param multipleEditing: if user selects more than one map mutlipleEditing=True
        @param numOfMap: holds information about number of selected maps for editing
        @param ListOfMapTypeDict: list of dict stored names of selected maps in dict. dict['cell/vector']=nameofmaps
        '''
        if not multipleEditing:
            self.ListOfMapTypeDict = self.MdDataCatalogPanelLeft.ListOfMapTypeDict

        self.profileChoice = self.configPanelLeft.comboBoxProfile.GetValue()
        self.numOfMap = len(self.ListOfMapTypeDict)

        if self.numOfMap == 0 and multipleEditing is False:
            GMessage('Select map in data catalog...')
            return

        # if editing just one map
        if self.numOfMap == 1 and multipleEditing is False:
            self.mdCreator = mdgrass.GrassMD(self.ListOfMapTypeDict[-1][self.ListOfMapTypeDict[-1].keys()[0]],
                                             self.ListOfMapTypeDict[-1].keys()[0])
            if self.profileChoice == 'INSPIRE':
                self.mdCreator.createGrassInspireISO()
            elif self.profileChoice == 'GRASS BASIC':
                self.mdCreator.createGrassBasicISO()
            elif self.profileChoice == 'TEMPORAL':
                self.mdCreator.createTemporalISO()

            self.jinjaPath = self.mdCreator.profilePathAbs
            self.xmlPath = self.mdCreator.saveXML(self.mdDestination, self.nameTMPteplate, self)
            self.onInitEditor()

        # if editing multiple maps or just one but with loading own custom profile
        if self.profileChoice == 'Load Custom' and self.numOfMap != 0:
        # load profile. IF for just one map ELSE for multiple editing
            if multipleEditing is False:
                dlg = wx.FileDialog(self, "Select profile", os.getcwd(), "", "*.xml", wx.OPEN)
                if dlg.ShowModal() == wx.ID_OK:
                    self.mdCreator = mdgrass.GrassMD(self.ListOfMapTypeDict[-1][self.ListOfMapTypeDict[-1].keys()[0]],
                                                     self.ListOfMapTypeDict[-1].keys()[0])
                    self.mdCreator.createGrassInspireISO()
                    self.jinjaPath = dlg.GetPath()
                    self.xmlPath = self.mdCreator.saveXML(self.mdDestination, self.nameTMPteplate, self)
                    # if multiple map are selected
                    if self.numOfMap > 1:
                        self.toolbar.xmlPath = self.xmlPath
                        self.toolbar.jinjaPath = self.jinjaPath
                        self.batch = True
                        self.ListOfMapTypeDict.pop()
                        self.initMultipleEditor()
                    else:
                        self.ListOfMapTypeDict.pop()
                        self.onInitEditor()
                else:  # do nothing
                    return False
            else:
                self.mdCreator = mdgrass.GrassMD(self.ListOfMapTypeDict[-1][self.ListOfMapTypeDict[-1].keys()[0]],
                                                 self.ListOfMapTypeDict[-1].keys()[0])
                self.mdCreator.createGrassInspireISO()
                self.xmlPath = self.mdCreator.saveXML(self.mdDestination, self.nameTMPteplate, self)
                self.toolbar.xmlPath = self.xmlPath
                self.toolbar.jinjaPath = self.jinjaPath
                self.ListOfMapTypeDict
                self.initMultipleEditor()
                self.ListOfMapTypeDict.pop()

        if not multipleEditing:
            self.onHideLeftPanel()

        if self.numOfMap == 0 and multipleEditing is True:
            multipleEditing = False
            self.toolbar.onNewSession(None)
            GMessage('All selected maps are edited')
            self.secondMultiEdit = True

        if self.batch and multipleEditing:
            XMLhead, XMLtail = os.path.split(self.xmlPath)
            self.batch = mdutil.yesNo(self, 'Do you want to save metadata of : %s without editing ? ' % XMLtail, 'Multiple editing')

            if self.batch:
                self.toolbar.batch = True
                self.toolbar.onSaveXML()
        return True

    def initMultipleEditor(self):
        '''initialize multiple editing mode
        '''
        if self.firstAfterChoice and not self.secondMultiEdit:
            self.splitter = SplitterWindow(self, style=wx.SP_3D |
                                           wx.SP_LIVE_UPDATE | wx.SP_BORDER)
            self.Hsizer.Add(self.splitter, proportion=1, flag=wx.EXPAND)

            self.firstAfterChoice = False
            self.secondAfterChoice = True
            self.toolbar.bttsave.SetLabel('next')
            self.toolbar.hideMultipleEdit()
            self.mainSizer.Layout()
            self.editor = MdMainEditor(self.splitter,
                                       self.jinjaPath,
                                       self.xmlPath,
                                       self.profileEditor)
            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)
            self.splitter.SplitVertically(self.editor, self.ntbRight, sashPosition=0.65)
            self.splitter.SetSashGravity(0.65)
            self.resizeFrame()
            self.Show()

        elif self.secondAfterChoice or self.secondMultiEdit:
            if self.secondMultiEdit:
                self.toolbar.bttsave.SetLabel('next')
                self.toolbar.hideMultipleEdit()
            self.second = False
            self.secondAfterChoice = True
            self.onInitEditor()

    def onInitEditor(self,):
        '''Initialize editor
        @var first: True= First initialize main frame
        @var firstAfterChoice: True=Init editor editor after set configuration and click onEdit in toolbar
        @var second: init editor after first initialize
        @var secondAfterChoice: init editor one more time
        '''
        if self.first:
            self.first = False
            self.firstAfterChoice = True
            self.toolbar = MdToolbar(self,
                                     self.jinjaPath,
                                     self.xmlPath,
                                     self.sb,
                                     self.mdDestination)

            self.leftPanel = wx.Panel(self, id=wx.ID_ANY)
            self.configPanelLeft = MdEditConfigPanel(self.leftPanel)
            self.MdDataCatalogPanelLeft = MdDataCatalog(self.leftPanel)

            self._layout()
            self.Show()

        elif self.firstAfterChoice:
            self.splitter = SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE | wx.SP_BORDER)
            self.secondMultiEdit = True
            self.firstAfterChoice = False
            self.second = True

            self.editor = MdMainEditor(parent=self.splitter,
                                       profilePath=self.jinjaPath,
                                       xmlMdPath=self.xmlPath,
                                       templateEditor=self.templateEditor)

            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)

            self.splitter.SplitVertically(self.editor, self.ntbRight, sashPosition=0.65)
            self.splitter.SetSashGravity(0.65)
            self.Hsizer.Add(self.splitter, proportion=1, flag=wx.EXPAND)
            self.splitter.SizeWindows()
            self.resizeFrame()
            self.Show()

        elif self.second:  # if next initializing of editor
            self.second = False
            self.secondAfterChoice = True
            self.splitter.Hide()
            self.toolbar.bttNew.Disable()
            self.toolbar.bttsave.Disable()

            self.Hsizer.Insert(0, self.leftPanel, proportion=1, flag=wx.EXPAND)
            self.resizeFrame()

        elif self.secondAfterChoice:
            self.secondAfterChoice = False
            self.second = True
            self.splitter.Show()
            self.toolbar.bttNew.Enable()
            self.toolbar.bttsave.Enable()

            ntbRightBCK = self.ntbRight
            self.ntbRight = NotebookRight(self.splitter, self.xmlPath)
            self.splitter.ReplaceWindow(ntbRightBCK, self.ntbRight)

            editorTMP = self.editor
            self.editor = MdMainEditor(parent=self.splitter,
                                       profilePath=self.jinjaPath,
                                       xmlMdPath=self.xmlPath,
                                       templateEditor=self.templateEditor)

            self.splitter.ReplaceWindow(editorTMP, self.editor)
            ntbRightBCK.Destroy()
            editorTMP.Destroy()
            self.resizeFrame()
            self.Show()
            self.splitter.SetSashGravity(0.35)
        else:
            GMessage('Select map in data catalog...')

            self.toolbar.xmlPath = self.xmlPath
            self.toolbar.jinjaPath = self.jinjaPath

    def _layout(self):

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)

        self.mainSizer.Add(self.toolbar)
        self.mainSizer.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(10000, 5)))
        self.mainSizer.AddSpacer(5, 5, 1, wx.EXPAND)

        self.leftPanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.leftPanel.SetSizer(self.leftPanelSizer)
        self.leftPanelSizer.Add(self.configPanelLeft, proportion=0, flag=wx.EXPAND)
        self.leftPanelSizer.AddSpacer(5, 5, 1, wx.EXPAND)
        self.leftPanelSizer.Add(self.MdDataCatalogPanelLeft, proportion=1, flag=wx.EXPAND)

        self.Hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mainSizer.Add(self.Hsizer, proportion=1, flag=wx.EXPAND)

        self.Hsizer.Add(self.leftPanel, proportion=1, flag=wx.EXPAND)

        self.resizeFrame(300, 0)
        self.Layout()
#===============================================================================
# DATA CATALOG
#===============================================================================
class MdDataCatalog(datacatalog.LocationMapTree):

    '''Data catalog for selecting GRASS maps for editing
    '''

    def __init__(self, parent):
        """Test Tree constructor."""
        super(MdDataCatalog, self).__init__(parent=parent,
                                            style=wx.TR_MULTIPLE | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS |
                                            wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_COLUMN_LINES)
        tgis.init(True)
        self.dbif = tgis.SQLDatabaseInterfaceConnection()
        self.dbif.connect()
        self.InitTreeItems()
        self.map = None
        self.mapType = None

    def __del__(self):
        """Close the database interface and stop the messenger and C-interface
           subprocesses.
        """
        if self.dbif.connected is True:
            self.dbif.close()
        tgis.stop_subprocesses()


    def InitTreeItems(self):

        """Add locations and layers to the tree"""
        self.rootTmp=self.root
        var=self.AppendItem(self.root,'Grass maps')
        self.root=var

        gisenv = grass.gisenv()
        location = gisenv['LOCATION_NAME']
        #GMessage(location)
        self.mapset = gisenv['MAPSET']
        #GMessage(self.mapset)
        self.initGrassTree(location=location, mapset=self.mapset)
        self.initTemporalTree(location=location, mapset=self.mapset)


    def initGrassTree(self,location , mapset):
        """Add locations, mapsets and layers to the tree."""

        self.ChangeEnvironment(location)

        varloc = self.AppendItem(self.root, location)
        self.AppendItem(varloc, mapset)

        # get list of all maps in location
        maplist = RunCommand('g.list', flags='mt', type='raster,vector', mapset=mapset,
                             quiet=True, read=True)
        maplist = maplist.splitlines()

        for ml in maplist:
            # parse
            parts1 = ml.split('/')
            parts2 = parts1[1].split('@')
            mapset = parts2[1]
            mlayer = parts2[0]
            ltype = parts1[0]

            # add mapset
            if self.itemExists(mapset, varloc) == False:
                varmapset = self.AppendItem(varloc, mapset)
            else:
                varmapset = self.getItemByName(mapset, varloc)

            # add type node if not exists
            if self.itemExists(ltype, varmapset) == False:
                vartype = self.AppendItem(varmapset, ltype)

            self.AppendItem(vartype, mlayer)

    def initTemporalTree(self,location , mapset ):
        varloc = self.AppendItem(self.rootTmp, 'Temporal maps')
        tDict = tgis.tlist_grouped('stds', group_type=True, dbif=self.dbif)
        # nested list with '(map, mapset, etype)' items
        allDatasets = [[[(map, mapset, etype) for map in maps]
                        for etype, maps in etypesDict.iteritems()]
                       for mapset, etypesDict in tDict.iteritems()]
        if allDatasets:
            allDatasets = reduce(lambda x, y: x + y, reduce(lambda x, y: x + y,
                                                            allDatasets))
            mapsets = tgis.get_tgis_c_library_interface().available_mapsets()
            allDatasets = [i for i in sorted(allDatasets,
                                             key=lambda l: mapsets.index(l[1]))]
        #print allDatasets
        #if not location:
        #    location = GetListOfLocations(self.gisdbase)
        #if not self.mapset:
        #    mapsets = ['*']

        first = True
        #for loc in location:
            #location = loc
            #self.ChangeEnvironment(location)
        loc=location
        varloc = self.AppendItem(varloc, loc)
        #self.ChangeEnvironment(loc)
        # add all mapsets
        self.AppendItem(varloc, mapset)

        # get list of all maps in location
        for ml in allDatasets:

            # add mapset
            if self.itemExists(ml[1], varloc) == False:
                varmapset = self.getItemByName(ml[1], varloc)
            else:
                varmapset = self.getItemByName(ml[1], varloc)
            # add type node if not exists
            if self.itemExists(ml[2], varmapset) == False:
                vartype = self.AppendItem(varmapset, ml[2])

            self.AppendItem(vartype, ml[0])


        #self.ExpandAll()

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.onChanged)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.onChanged)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRClickAllChildren)

    def OnRClickAllChildren(self, evt):
        if not self.IsExpanded(evt.Item):
            self.ExpandAllChildren(evt.Item)
        else:
            self.CollapseAllChildren(evt.Item)

    def onChanged(self, evt=None):
        '''
        @var ListOfMapTypeDict: list of dic with maps and map-type values
        @var MapTypeDict: keys= type of map(cell/vector), value=<map name>
        '''
        self.ListOfMapTypeDict = list()
        maps = list()
        if self.GetChildrenCount(evt.Item) == 0:  # is selected map
            for item in self.GetSelections():
                MapTypeDict = {}
                maps.append(self.GetItemText(item))
                map = self.GetItemText(item) #+ '@' + self.mapset @TODO to test
                mapType = self.GetItemParent(item)
                mapType = self.GetItemText(mapType)

                if mapType == 'vect':
                    mapType = 'vector'
                elif mapType == 'rast':
                    mapType = 'raster'
                MapTypeDict[mapType] = map

                self.ListOfMapTypeDict.append(MapTypeDict)
            pub.sendMessage('bttEdit.enable')
            pub.sendMessage('bttCreateTemplate.enable')

        else:
            self.Unselect()

            #pub.sendMessage('bttEdit.disable')
            #pub.sendMessage('bttCreateTemplate.disable')
            #GMessage('Please select map')

        if len(maps) == 0:
            pub.sendMessage('bttEdit.disable')
            pub.sendMessage('bttCreateTemplate.disable')
            return
        status = ''
        for map in maps:
            status += map + '  '

        if len(maps) > 1:
            pub.sendMessage('SET_PROFILE.update', profile='Load Custom')

            pub.sendMessage('comboBoxProfile.disable')
            pub.sendMessage('bttCreateTemplate.disable')
        else:
            pub.sendMessage('comboBoxProfile.enable')
            pub.sendMessage('bttCreateTemplate.enable')

        pub.sendMessage('STATUS_BAR_TEXT.update', text=status)

#===============================================================================
# NOTEBOOK ON THE RIGHT SIDE-xml browser+validator
#===============================================================================


class NotebookRight(wx.Notebook):

    '''Include pages with xml tree browser and validator of metadata
    '''

    def __init__(self, parent, path):

        wx.Notebook.__init__(self, parent=parent, id=wx.ID_ANY)
        # first panel
        self.notebookValidator = wx.Panel(self, wx.ID_ANY)
        self.validator = MdValidator(self.notebookValidator)
        self.xmlPath = path
        self.profile = None
        self.buttValidate = wx.Button(self.notebookValidator,
                                      id=wx.ID_ANY,
                                      size=(70, 50),
                                      label='validate')

        self.notebook_panel1 = wx.Panel(self, wx.ID_ANY)
        self.tree = TreeBrowser(self.notebook_panel1, self.xmlPath)
        self.buttRefresh = wx.Button(
            self.notebook_panel1,
            id=wx.ID_ANY,
            size=(70, 50),
            label='refresh')

        self.AddPage(self.notebookValidator, "Validator")
        self.AddPage(self.notebook_panel1, "Tree browser")
        # self.AddPage(self.notebook_panel2, "Help")

        self.buttValidate.Bind(wx.EVT_BUTTON, self.validate)
        self.buttRefresh.Bind(wx.EVT_BUTTON, self.onRefreshXmlBrowser)
        self._layout()

    def onActive(self):
        pass

    def onRefreshXmlBrowser(self, evt=None):
        pub.sendMessage('REFRESH_TREE_BROWSER.update')

    def refreshXmlBrowser(self, path):
        treeBCK = self.tree
        self.tree = TreeBrowser(self.notebook_panel1, path)
        self.panelSizer1.Replace(treeBCK, self.tree)
        # self.panelSizer1.Add(self.tree, flag=wx.EXPAND, proportion=1)
        self.panelSizer1.Layout()
        treeBCK.Destroy()

    def validate(self, evt):
        self.md = None
        pub.sendMessage('NEW_MD.create')
        pub.sendMessage('ISO_PROFILE.update')
        self.validator.validate(self.md, self.profile)

    def _layout(self):
        panelSizer0 = wx.BoxSizer(wx.VERTICAL)
        self.notebookValidator.SetSizer(panelSizer0)

        panelSizer0.Add(self.validator, flag=wx.EXPAND, proportion=1)
        panelSizer0.Add(self.buttValidate)

        self.panelSizer1 = wx.BoxSizer(wx.VERTICAL)
        self.notebook_panel1.SetSizer(self.panelSizer1)
        self.panelSizer1.Add(self.tree, flag=wx.EXPAND, proportion=1)
        self.panelSizer1.Add(self.buttRefresh)

        panelSizer2 = wx.BoxSizer(wx.VERTICAL)
        # self.notebook_panel2.SetSizer(panelSizer2)
        # panelSizer2.Add(self.notebook_panel2,flag=wx.EXPAND, proportion=1)
#===============================================================================
# HELP
#===============================================================================


class MDHelp(wx.Panel):

    """
    class MyHtmlPanel inherits wx.Panel and adds a button and HtmlWindow
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.html1 = wx.html.HtmlWindow(self, id=wx.ID_ANY)
        try:
            self.html1.LoadFile('help/help.html')
            # self.html1.LoadPage('http://inspire-geoportal.ec.europa.eu/EUOSME_GEOPORTAL/userguide/eurlex_en.htm')
        except:
            pass

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        self.mainSizer.Add(self.html1, proportion=1, flag=wx.EXPAND)
#===============================================================================
# TREE EDITOR
#===============================================================================


class TreeBrowser(wx.TreeCtrl):

    '''Filling text tree by xml file.
    @note: to enable editing mode of init xml uncomment blocks below
    '''

    def __init__(self, parent, xmlPath=False, xmlEtree=False):
        wx.TreeCtrl.__init__(self, parent=parent, id=wx.ID_ANY,
                             style=wx.TR_HAS_BUTTONS | wx.TR_FULL_ROW_HIGHLIGHT)
        tree = self
        if xmlPath:
            xml = etree.parse(xmlPath)
            self.xml = xml.getroot()

            self.root = tree.AddRoot(self.xml.tag)
        else:
            self.xml = xmlEtree
            self.root = xmlEtree.getroot()

        root = self.fillTree()
        self.Expand(root)

        #=======================================================================
        # self.Bind(wx.EVT_CLOSE, self.OnClose)
        # self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEdit)
        #=======================================================================
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnRClickAllChildren)

    def fillTree(self):
        root = self.root
        xml = self.xml
        tree = self

        def add(parent, elem):
            for e in elem:
                if str(e).find("<!--") != -1:  # skip comments
                    continue
                tag = etree.QName(e)
                item = tree.AppendItem(parent, tag.localname, data=None)
                if self.GetChildrenCount(item) == 0:
                    self.SetItemBackgroundColour(item, (242, 242, 242))
                if e.text:
                    text = e.text.strip()
                else:
                    text = e.text
                if text:
                    val = tree.AppendItem(item, text)
                    tree.SetPyData(val, e)

                add(item, e)

        add(root, xml)
        return root

    #=========================================================================
    # def OnEdit(self, evt):
    #     elm = self.GetPyData(evt.Item)
    #
    # print evt.Label
    #     if elm is not None:
    #         elm.text = evt.Label
    #         self.xml.write(self.fpath, encoding="UTF-8", xml_declaration=True)
    # self.validate()
    #=========================================================================

    #=========================================================================
    # def OnClose(self, evt):
    #     self.Destroy()
    #=========================================================================

    def OnRClickAllChildren(self, evt):
        if not self.IsExpanded(evt.Item):
            self.ExpandAllChildren(evt.Item)
        else:
            self.CollapseAllChildren(evt.Item)

#===============================================================================
# INSPIRE VALIDATOR PANEL
#===============================================================================


class MdValidator(wx.Panel):

    '''wx panel of notebook which supports validating two natively implemented profiles
    '''

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.text = wx.TextCtrl(parent, id=wx.ID_ANY, size=(0, 55),
                                style=wx.VSCROLL |
                                wx.TE_MULTILINE | wx.TE_NO_VSCROLL |
                                wx.TAB_TRAVERSAL | wx.RAISED_BORDER | wx.HSCROLL)
        self._layout()

    def _layout(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        self.mainSizer.Add(self.text, proportion=1, flag=wx.EXPAND)

    def validate(self, md, profile):
        '''For externally loaded xml file is by default inspire validator
        '''
        if profile == 'INSPIRE' or profile == 'Load Custom':
            result = mdutil.isnpireValidator(md)
            str1 = 'INSPIRE VALIDATOR\n'

        if profile == 'GRASS BASIC':
            result = mdutil.grassProfileValidator(md)
            str1 = 'GRASS BASIC PROFILE VALIDATOR\n'

        if profile == 'TEMPORAL':
            result = mdutil.isnpireValidator(md)
            str1 = 'INSPIRE VALIDATOR\n'

        str1 += 'Status of validation: ' + result["status"] + '\n'
        str1 += 'Numbers of errors: ' + result["num_of_errors"] + '\n'

        if result["status"] != 'succeded':
            str1 += 'Errors:\n'
            for item in result["errors"]:
                str1 += '\t' + str(item) + '\n'

        self.text.SetValue(str1)

#===============================================================================
# CONFIGURATION PANEL ON THE LEFT SIDE
#===============================================================================


class MdEditConfigPanel(wx.Panel):

    '''Configuration pane for selection editing mode.
    @var mapGrassEdit: True = editing metadata of GRASS maps, false= editing externally loaded xml and profile
    '''

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)
        self.SetMinSize((240, -1))
        self.mapGrassEdit = True

        self.rbGrass = wx.RadioButton(self, id=wx.ID_ANY, label='Metadata map editor', style=wx.RB_GROUP)
        self.rbExternal = wx.RadioButton(self, id=wx.ID_ANY, label='Metadata external editor')

        self.comboBoxProfile = wx.ComboBox(self, choices=['INSPIRE', 'GRASS BASIC', 'TEMPORAL','Load Custom'])
        pub.subscribe(self.onComboboxDisable, "comboBoxProfile.disable")
        pub.subscribe(self.onComboboxEnable, "comboBoxProfile.enable")
        pub.subscribe(self.onSetProfile, "SET_PROFILE.update")
        self.comboBoxProfile.SetStringSelection('INSPIRE')#TODO

        self.Bind(wx.EVT_RADIOBUTTON, self.onSetRadioType, id=self.rbGrass.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSetRadioType, id=self.rbExternal.GetId())
        self.comboBoxProfile.Bind(wx.EVT_COMBOBOX, self.onChangeComboBoxProfile)

        self._layout()

    def onChangeComboBoxProfile(self, evt):
        pass

    def onComboboxDisable(self):
        self.comboBoxProfile.Disable()

    def onComboboxEnable(self):
        self.comboBoxProfile.Enable()

    def onSetProfile(self, profile):
        self.comboBoxProfile.SetStringSelection(profile)

    def SetVal(self, event):
        state1 = str()
        state2 = str(self.rb2.GetValue())

        self.statusbar.SetStatusText(state1, 0)
        self.statusbar.SetStatusText(state2, 1)

    def onSetRadioType(self, evt=None):
        self.mapGrassEdit = self.rbGrass.GetValue()
        if self.mapGrassEdit is False:
            self.comboBoxProfile.Hide()
        else:
            self.comboBoxProfile.Show()
        pub.sendMessage('EDITING_MODE.update', editStatus=self.mapGrassEdit)

    def _layout(self):
        self.mainsizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Add(self.rbGrass)
        self.mainsizer.Add(self.rbExternal)
        self.mainsizer.Add(self.comboBoxProfile)
#===============================================================================
# TOOLBAR
#===============================================================================


class MdToolbar(wx.Panel):

    '''Main toolbar of editor
    '''

    def __init__(self, parent, jinjaPath, xmlPath, sb, mdDestionation):
        wx.Panel.__init__(self, parent, id=wx.ID_ANY)
        self.mdDestination = mdDestionation
        self.batch = False
        self.jinjaPath = jinjaPath
        self.statusBar = sb
        self.xmlPath = xmlPath
        self.extendEdit = False
        self.toolbar = wx.ToolBar(self, 1, wx.DefaultPosition, (-1, -1))

        bitmapSave = wx.Image(
            os.path.join(os.environ['GISBASE'], 'gui', 'icons', 'grass', 'save.png'),
            wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bitmapNew = wx.Image(
            os.path.join(os.environ['GISBASE'], 'gui', 'icons', 'grass', 'create.png'),
            wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bitmapLoad = wx.Image(
            os.path.join(os.environ['GISBASE'], 'gui', 'icons', 'grass', 'open.png'),
            wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bitmaSettings = wx.Image(
            os.path.join(os.environ['GISBASE'], 'gui', 'icons', 'grass', 'settings.png'),
            wx.BITMAP_TYPE_PNG).ConvertToBitmap()
    #-------------------------------------------------------------------- EDIT
        self.toolbar.AddSeparator()
        bitmapEdit = wx.Image(
            os.path.join(os.environ['GISBASE'], 'gui', 'icons', 'grass', 'edit.png'),
            wx.BITMAP_TYPE_PNG).ConvertToBitmap()

    #-------------------------------------------------------------------- EDIT

        self.bttEdit = BitmapBtnTxt(self.toolbar, -1, bitmapEdit,size=(40, -1))
        self.toolbar.AddControl(control=self.bttEdit)
        self.bttEdit.Disable()
    #-------------------------------------------------------------------- NEW SESION
        #self.toolbar.AddSeparator()
        self.bttNew = BitmapBtnTxt(self.toolbar, -1, bitmapNew, '', size=(40, -1))
        self.toolbar.AddControl(control=self.bttNew)
        self.bttNew.Disable()
    #-------------------------------------------------------------------- NEW TEMPLATE
        self.bttCreateTemplate = BitmapBtnTxt(self.toolbar, -1, bitmapNew, "template", size=(100, -1))
        self.toolbar.AddControl(control=self.bttCreateTemplate)
        self.bttCreateTemplate.Disable()
        self.toolbar.AddSeparator()

    #----------------------------------------------------------------- OPEN TEMPLATE
        self.bttLoad = BitmapBtnTxt(self.toolbar, -1, bitmapLoad, "profile", size=(100, -1))
        self.toolbar.AddControl(control=self.bttLoad)
        self.bttLoad.Disable()
    #---------------------------------------------------------------------- OPEN XML
        self.bttLoadXml = BitmapBtnTxt(self.toolbar, -1, bitmapLoad, "xml")
        self.toolbar.AddControl(control=self.bttLoadXml)
        self.bttLoadXml.Disable()
        self.toolbar.AddSeparator()
    #-------------------------------------------------------------------------- export xml
        self.bttsave = BitmapBtnTxt(self.toolbar, -1, bitmapSave, "xml")
        self.bttsave.Disable()
        self.toolbar.AddControl(control=self.bttsave)
    #-------------------------------------------------------------------------- export template
        self.bttSaveTemplate = BitmapBtnTxt(self.toolbar, -1, bitmapSave, "template", size=(100, -1))
        self.bttSaveTemplate.Disable()
        self.toolbar.AddControl(control=self.bttSaveTemplate)
    #-------------------------------------------------------------------------- update grass
        self.bttUpdateGRASS = BitmapBtnTxt(self.toolbar, -1, bitmapSave, "GRASS", size=(100, -1))
        self.bttUpdateGRASS.Disable()
        self.toolbar.AddControl(control=self.bttUpdateGRASS)
    #-------------------------------------------------------------------------- export pdf
        self.bttExportPdf = BitmapBtnTxt(self.toolbar, -1, bitmapSave, "pdf", size=(100, -1))
        self.bttExportPdf.Disable()
        self.toolbar.AddControl(control=self.bttExportPdf)
        self.toolbar.AddSeparator()
    #-------------------------------------------------------------------------- Config
        self.bttConfig = BitmapBtnTxt(self.toolbar, -1, bitmaSettings, "", size=(40, -1))
        self.toolbar.AddControl(control=self.bttConfig)
        self.toolbar.AddSeparator()

        self.toolbar.Realize()
        self._layout()

        self.bttLoad.Bind(wx.EVT_BUTTON, self.OnLoadTemplate)

        pub.subscribe(self.onBttSaveEnable, "bttLoad.enable")
        pub.subscribe(self.onBttSaveDisable, "bttLoad.disable")

        self.bttsave.Bind(wx.EVT_BUTTON, self.onSaveXML)
        pub.subscribe(self.onBttLoadEnable, "bttSave.enable")
        pub.subscribe(self.onBttLoadDisable, "bttSave.disable")

        self.bttLoadXml.Bind(wx.EVT_BUTTON, self.onLoadXml)
        pub.subscribe(self.onBttLoadXmlEnable, "bttLoadXml.enable")
        pub.subscribe(self.onBttLoadXmlDisable, "bttLoadXml.disable")

        self.bttNew.Bind(wx.EVT_BUTTON, self.onNewSession)
        pub.subscribe(self.onBttNewEnable, "bttNew.enable")
        pub.subscribe(self.onBttNewDisable, "bttNew.disable")

        self.bttEdit.Bind(wx.EVT_BUTTON, self.onEdit)
        pub.subscribe(self.onBtEditEnable, "bttEdit.enable")
        pub.subscribe(self.onBttEditDisable, "bttEdit.disable")

        self.bttCreateTemplate.Bind(wx.EVT_BUTTON, self.onCreateTemplate)
        pub.subscribe(self.onBttCreateTemplateEnable, "bttCreateTemplate.enable")
        pub.subscribe(self.onBttCreateTemplateDisable, "bttCreateTemplate.disable")

        self.bttSaveTemplate.Bind(wx.EVT_BUTTON, self.onSaveTemplate)
        pub.subscribe(self.onBttSaveTemplateEnable, "bttSaveTemplate.enable")
        pub.subscribe(self.onBttSaveTemplateDisable, "bttSaveTemplate.disable")

        self.bttUpdateGRASS.Bind(wx.EVT_BUTTON, self.onUpdateGRASS)
        pub.subscribe(self.onBttUpdateGRASSEnable, "bttSaveTemplate.enable")
        pub.subscribe(self.onBttUpdateGRASSDisable, "bttSaveTemplate.disable")

        self.bttExportPdf.Bind(wx.EVT_BUTTON, self.onExportPdf)
        pub.subscribe(self.onBttExportPdfEnable, "bttExportPdf.enable")
        pub.subscribe(self.onBttExportPdfDisable, "bttExportPdf.disable")
        self.bttConfig.Bind(wx.EVT_BUTTON, self.onSettings)

    def onBttSaveDisable(self):
        self.bttSave.Disable()

    def onBttSaveEnable(self):
        self.bttSave.Enable()

    def onBttLoadDisable(self):
        self.bttLoad.Disable()

    def onBttLoadEnable(self):
        self.bttLoad.Enable()

    def onBttLoadXmlDisable(self):
        self.bttLoadXml.Disable()

    def onBttLoadXmlEnable(self):
        self.bttLoadXml.Enable()

    def onBttNewDisable(self):
        self.bttNew.Disable()

    def onBttNewEnable(self):
        self.bttNew.Enable()

    def onBttEditDisable(self):
        self.bttEdit.Disable()

    def onBtEditEnable(self):
        self.bttEdit.Enable()

    def onBttCreateTemplateDisable(self):
        self.bttCreateTemplate.Disable()

    def onBttCreateTemplateEnable(self):
        self.bttCreateTemplate.Enable()

    def onBttSaveTemplateDisable(self):
        self.bttSaveTemplate.Disable()

    def onBttSaveTemplateEnable(self):
        self.bttSaveTemplate.Enable()

    def onBttUpdateGRASSDisable(self):
        self.bttUpdateGRASS.Disable()

    def onBttUpdateGRASSEnable(self):
        self.bttUpdateGRASS.Enable()

    def onBttExportPdfDisable(self):
        self.bttExportPdf.Disable()

    def onBttExportPdfEnable(self):
        self.bttExportPdf.Enable()

    def onUpdateGRASS(self, evt):
        pub.sendMessage('GRASS_METADATA.update')

    def onExportPdf(self,evt):
        self.xmlPath=self.GetParent().xmlPath
        XMLhead, XMLtail = os.path.split(self.xmlPath)
        dlg = wx.FileDialog(self,
                            message="Set output file",
                            defaultDir=self.mdDestination,
                            defaultFile=XMLtail.split('.')[0]+'.pdf',
                            wildcard="*.pdf",
                            style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            outPath=dlg.GetDirectory()
            outFileName=dlg.GetFilename()
            pub.sendMessage('EXPORT_PDF.create',
                            outPath=outPath,
                            outFileName=outFileName)
            if mdutil.yesNo(self,'Do you want to open report?'):
                webbrowser.open(os.path.join(outPath,outFileName))


    def onSettings(self, evt):
        dlg = wx.DirDialog(self,
                           message="Select metadata working directory",
                           defaultPath=self.mdDestination,
                           style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)

        if dlg.ShowModal() == wx.ID_OK:
            self.mdDestination = dlg.GetPath()
            pub.sendMessage('MD_DESTINATION.update', value=self.mdDestination)
            dlg.Destroy()

        GMessage('Metadata destination: %s' % self.mdDestination)

    def hideMultipleEdit(self):
        '''Multiple editor is off
        '''

        self.bttLoad.Hide()
        self.bttLoadXml.Hide()
        self.bttNew.Hide()
        self.bttEdit.Hide()
        self.bttCreateTemplate.Hide()
        self.bttSaveTemplate.Hide()
        self.bttUpdateGRASS.Hide()
        self.bttExportPdf.Hide()

    def showMultipleEdit(self):
        '''Multiple editor is on
        '''
        self.bttLoad.Show()
        self.bttLoadXml.Show()
        self.bttNew.Show()
        self.bttEdit.Show()
        self.bttCreateTemplate.Show()
        self.bttSaveTemplate.Show()
        self.bttUpdateGRASS.Show()
        self.bttExportPdf.Show()

    def onCreateTemplate(self, evt):
        pub.sendMessage('TEMPLATE_EDITOR_STATUS.update', value=True)
        self.onEdit(evt=None)
        self.bttCreateTemplate.Disable()
        self.bttSaveTemplate.Enable()

    def onEdit(self, evt=None):
        '''
        @var : extendEdit if xml and jinja is loaded from file
        '''
        if self.extendEdit:
            pub.sendMessage('SET_JINJA_AND_XML.update', jinja=self.jinjaPath, xml=self.xmlPath)
            self.bttUpdateGRASS.Disable()

        if self.GetParent().configPanelLeft.rbGrass.GetValue():
            ok = self.GetParent().onEditMapMetadata()
            if not ok:
                return
        else:
            pub.sendMessage('INIT_EDITOR.create')

        self.bttCreateTemplate.Disable()
        self.bttEdit.Disable()
        self.bttsave.Enable()
        self.bttExportPdf.Enable()
        if not self.extendEdit:
            self.bttUpdateGRASS.Enable()

        try:  # if  multiediting mode ON
            if self.GetParent().numOfMap > 1:
                XMLhead, XMLtail = os.path.split(self.xmlPath)
                self.batch = mdutil.yesNo(self, 'Do you want to save metadata of : %s without editing ? ' % XMLtail, 'Multiple editing')
            if self.batch:
                self.onSaveXML()
        except:
            pass

    def onNewSession(self, evt):
        pub.sendMessage('INIT_EDITOR.create')
        pub.sendMessage('TEMPLATE_EDITOR_STATUS.update', value=False, template=False)
        # check current editing mode(grass or external xml editor)
        if self.GetParent().configPanelLeft.rbGrass is False:
            self.bttLoad.Enable()
            self.bttLoadXml.Enable()
        self.statusBar.SetStatusText('')
        self.bttsave.Disable()
        self.bttExportPdf.Disable()
        self.bttUpdateGRASS.Disable()
        self.jinjaPath = None
        self.xmlPath = None
        self.bttsave.SetLabel('xml')
        self.showMultipleEdit()

        self.bttSaveTemplate.Disable()

    def onChangeXmlorTemplate(self, evt=None):
        '''in case if path of template and xml path are initialized -> enable buttons for next step
        '''
        if self.jinjaPath is not None and self.xmlPath is not None:
            pub.sendMessage('HIDE_LEFT_PANEL.update')

            self.bttEdit.Enable()
            self.bttCreateTemplate.Enable()
            self.bttLoad.Disable()
            self.bttLoadXml.Disable()
            self.extendEdit = True

    def onLoadXml(self, evt=None):
        dlg = wx.FileDialog(self,
                            "Select XML metadata file",
                            self.mdDestination,
                            "",
                            "*.xml",
                            wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            self.xmlPath = dlg.GetPath()
            tx = self.statusBar.GetStatusText()
            self.statusBar.SetStatusText(tx + '  Selected XML: ' + self.xmlPath)
            self.onChangeXmlorTemplate()
            dlg.Destroy()

    def onSaveTemplate(self, evt=None):
        self.xmlPath=self.GetParent().xmlPath

        dlg = wx.FileDialog(self,
                            "Select output file",
                            self.mdDestination,
                            "",
                            "*.xml",
                            wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            pub.sendMessage('EXPORT_TEMPLATE.create',
                            outPath=dlg.GetDirectory(),
                            outFileName=dlg.GetFilename())

    def OnLoadTemplate(self, evt):
        dlg = wx.FileDialog(self,
                            "Select metadata ISO profile",
                            self.mdDestination,
                            "",
                            "*.xml",
                            wx.OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            self.jinjaPath = dlg.GetPath()
            tx = self.statusBar.GetStatusText()
            self.statusBar.SetStatusText(tx + ' Selected profile: ' + self.jinjaPath)
            self.onChangeXmlorTemplate()

        dlg.Destroy()

    def onSaveXML(self, evt=None):
        self.xmlPath=self.GetParent().xmlPath
        self.XMLhead, self.XMLtail = os.path.split(self.xmlPath)
        if not self.batch:  # if normal saving with user-task-dialog

            dlg = wx.FileDialog(self,
                                message="Set output file",
                                defaultDir=self.mdDestination,
                                defaultFile=self.XMLtail,
                                wildcard="*.xml",
                                style=wx.SAVE | wx.FD_OVERWRITE_PROMPT)

            if dlg.ShowModal() == wx.ID_OK:
                pub.sendMessage('EXPORT_XML.create', outPath=dlg.GetDirectory(), outFileName=dlg.GetFilename())
                if self.bttsave.GetLabelText() == 'next':
                    pub.sendMessage('EDIT_MAP_METADATA.create', multipleEditing=True)

            else:
                if self.bttsave.GetLabelText() == 'next':
                    ask = mdutil.yesNo(self, 'File is not saved. Do you want to save it? ', 'Save dialog')
                    if ask:
                        self.onSaveXML()
                    pub.sendMessage('EDIT_MAP_METADATA.create', multipleEditing=True)

                else:
                    GMessage('File not saved')
            dlg.Destroy()

        else:
            pub.sendMessage('EXPORT_XML.create', outPath=None, outFileName=None)
            pub.sendMessage('EDIT_MAP_METADATA.create', multipleEditing=True)

    def _layout(self):
        self.mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.mainsizer)
        self.mainsizer.Add(self.toolbar)

#----------------------------------------------------------------------
def main():
    app = wx.App(False)
    MdMainFrame()
    app.MainLoop()

if __name__ == '__main__':
    options, flags = grass.parser()
    main()
