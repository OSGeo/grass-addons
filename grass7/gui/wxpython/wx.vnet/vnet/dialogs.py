"""!
@package vnet.dialog

@brief Dialog for vector network analysis front-end

Classes:
 - dialog::VNETDialog
 - dialog::SettingsDialog
 - dialog::AddLayerDialog

(C) 2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Stepan Turek <stepan.turek seznam.cz> (GSoC 2012, mentor: Martin Landa)
"""

import os
import wx
import sys
import wx.lib.colourselect as csel

from core             import globalvar
from vnet.toolbars    import MainToolbar, PointListToolbar
from vnet.widgets     import PointsList
from gui_core.gselect import Select, LayerSelect, ColumnSelect
from gui_core.widgets import GNotebook
from core.settings    import UserSettings
from grass.script     import core as grass
from core          import utils
from core.gcmd        import RunCommand, GMessage
import unicodedata
import wx
import wx.aui
import wx.lib.flatnotebook  as FN

from copy import copy
class VNETDialog(wx.Dialog):
    def __init__(self, parent,
                 id=wx.ID_ANY, title = "Vector network analysis",
                 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):
        """!Dialolog for vector network analysis"""

        wx.Dialog.__init__(self, parent, id, style=style, title = title)

        self.parent  = parent  #mapdisp.frame MapFrame
        self.mapWin = parent.MapWindow
        self.inputData = {}
        self.cmdParams = {}

        self.tmp_result = "vnet_tmp_result"
        self.tmpMaps = [self.tmp_result]


        # registration graphics for drawing
        self.pointsToDraw = self.mapWin.RegisterGraphicsToDraw(graphicsType = "point", 
                                                               setStatusFunc = self.SetNodeStatus)
        self.pointsToDraw.SetPropertyVal("size", 10) # TODO settings

        # getting attribute table columns only whith numbers (costs)
        self.columnTypes = ['integer', 'double precision'] 

        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass_map.ico'), wx.BITMAP_TYPE_ICO))
        
        # initialozation of v.net.* analysis parameters
        self._initvnetParams()

        # toolbars
        self.toolbars = {}
        self.toolbars['mainToolbar'] = MainToolbar(parent = self)

        #
        # Fancy gui
        #
        self._mgr = wx.aui.AuiManager(self)

        # Columns in points list
        self.cols =   [
                        ['type', ["", _("Start point"), _("End point")], ""] #TODO init dynamically
                      ]

        self.mainPanel = wx.Panel(parent=self)
        self.notebook = GNotebook(parent = self.mainPanel,
                                  style = FN.FNB_FANCY_TABS | FN.FNB_BOTTOM |
                                          FN.FNB_NO_NAV_BUTTONS | FN.FNB_NO_X_BUTTON)


        self._createListPanel()
        self.notebook.AddPage(page = self.listPanel, 
                              text=_('Points list'), 
                              name = 'list')

        self._createSelectsPanel()
        self.notebook.AddPage(page = self.settingsPanel,
                              text=_('Data'), 
                              name = 'data')

        self._addPanes()
        self._doDialogLayout()

        self._mgr.Update()

        self.handlerRegistered = False
        self.tmpResultLayer = None 

        #TODO if 'vnet' not in UserSettings.userSettings: 

        # initializes default settings

        initSettings = [
                        ['resStyle', 'width', 5],
                        ['resStyle', 'color', (192,0,0)],
                        ['analysisSettings', 'maxDist', 10000],
                        ['analysisSettings', 'resultId', 1]
                      ]
        for init in initSettings:

            UserSettings.Append(dict = UserSettings.userSettings, 
                                group ='vnet', 
                                key = init[0],
                                subkey =init[1], 
                                value = init[2])

        # set options for drawing the map  
        self.UpdateCmdList(self.tmp_result)

        # adds 2 points into list
        for i in range(2):
            self.list.AddItem(None)
            self.list.EditCellIndex(i, 1, self.cols[1][1][1 + i]) 
            self.list.CheckItem(i, True)

        self.Bind(wx.EVT_CLOSE, self.OnCloseDialog)

        dlgSize = (300, 500)
        self.SetMinSize(dlgSize)
        self.SetInitialSize(dlgSize)

    def  __del__(self):
        """!Removes temp layer with analysis result, unregisters handlers and graphics"""

        self.mapWin.UnregisterGraphicsToDraw(self.pointsToDraw)

        for tmpMap in self.tmpMaps:
            RunCommand('g.remove', vect = tmpMap)

        if self.tmpResultLayer:
            self.mapWin.UpdateMap(render=True, renderVector=True)

        if self.handlerRegistered:
            self.mapWin.UnregisterMouseEventHandler(wx.EVT_LEFT_DOWN, 
                                                  self.OnMapClickHandler)

    def _addPanes(self):

        self._mgr.AddPane(self.toolbars['mainToolbar'],
                              wx.aui.AuiPaneInfo().
                              Name("pointlisttools").Caption(_("Point list toolbar")).
                              ToolbarPane().Top().
                              Dockable(False).
                              CloseButton(False).Layer(0))

        self._mgr.AddPane(self.mainPanel,
                              wx.aui.AuiPaneInfo().
                              Name("tabs").CaptionVisible(visible = False).
                              Center().
                              Dockable(False).
                              CloseButton(False).Layer(0))

    def _doDialogLayout(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(item = self.notebook, proportion = 1,
                  flag = wx.EXPAND)
        
        self.mainPanel.SetSizer(sizer)
        sizer.Fit(self)
        
        self.Layout()

    def _createListPanel(self):

        self.listPanel = wx.Panel(parent=self)

        self.list = NodesList(parent = self.listPanel, dialog = self, cols = self.cols)
        self.toolbars['pointsList'] = PointListToolbar(parent = self.listPanel, list = self.list)

        listsizer = wx.BoxSizer(wx.VERTICAL)

        listsizer.Add(item = self.toolbars['pointsList'], proportion = 0)
        listsizer.Add(item = self.list, proportion = 1, flag = wx.EXPAND)

        self.listPanel.SetSizer(listsizer)

    def _createSelectsPanel(self):

        self.settingsPanel = wx.Panel(parent=self)

        self.inputData['input'] = Select(parent = self.settingsPanel, type = 'vector', size = (-1, -1))
        vectSelTitle = wx.StaticText(parent = self.settingsPanel)
        vectSelTitle.SetLabel("Choose vector map for analysis:")

        self.inputData['alayer'] = LayerSelect(parent = self.settingsPanel, size = (-1, -1))
        aLayerSelTitle = wx.StaticText(parent = self.settingsPanel)
        aLayerSelTitle.SetLabel("Arc layer number or name:")

        self.inputData['nlayer'] = LayerSelect(parent = self.settingsPanel, size = (-1, -1))
        nLayerSelTitle = wx.StaticText(parent = self.settingsPanel)
        nLayerSelTitle.SetLabel("Node layer number or name:")

        self.inputData['afcolumn'] = ColumnSelect(parent = self.settingsPanel, size = (-1, -1))
        afcolumnSelTitle = wx.StaticText(parent = self.settingsPanel)
        afcolumnSelTitle.SetLabel("Arc forward/both direction(s) cost column:")

        self.inputData['abcolumn'] = ColumnSelect(parent = self.settingsPanel, size = (-1, -1))
        abcolumnSelTitle = wx.StaticText(parent = self.settingsPanel)
        abcolumnSelTitle.SetLabel("Arc backward direction cost column:")

        self.inputData['ncolumn'] = ColumnSelect(parent = self.settingsPanel, size = (-1, -1))
        ncolumnSelTitle = wx.StaticText(parent = self.settingsPanel)
        ncolumnSelTitle.SetLabel("Node direction cost column:")

        self.inputData['input'].Bind(wx.EVT_TEXT, self.OnVectSel) # TODO optimalization
        self.inputData['alayer'].Bind(wx.EVT_TEXT, self.OnALayerSel)
        self.inputData['nlayer'].Bind(wx.EVT_TEXT, self.OnNLayerSel)

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(self.settingsPanel, -1, "Layer for analysis")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        mainSizer.Add(item = bsizer, proportion = 0,
                                 flag = wx.EXPAND  | wx.TOP | wx.LEFT | wx.RIGHT, border = 5) 

        bsizer.Add(item = self._doSelLayout(title = vectSelTitle, sel = self.inputData['input']), proportion = 0,
                                 flag = wx.EXPAND)

        bsizer.Add(item = self._doSelLayout(title = aLayerSelTitle, sel = self.inputData['alayer']), proportion = 0,
                                 flag = wx.EXPAND)

        bsizer.Add(item = self._doSelLayout(title = nLayerSelTitle, sel = self.inputData['nlayer']), proportion = 0,
                                 flag = wx.EXPAND)

        box = wx.StaticBox(self.settingsPanel, -1, "Costs")
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        mainSizer.Add(item = bsizer, proportion = 0,
                                 flag = wx.EXPAND  | wx.TOP | wx.LEFT | wx.RIGHT, border = 5)       

        bsizer.Add(item = self._doSelLayout(title = afcolumnSelTitle, sel = self.inputData['afcolumn']), proportion = 0,
                                 flag = wx.EXPAND)

        bsizer.Add(item = self._doSelLayout(title = abcolumnSelTitle, sel = self.inputData['abcolumn']), proportion = 0,
                                 flag = wx.EXPAND)

        bsizer.Add(item = self._doSelLayout(title = ncolumnSelTitle, sel = self.inputData['ncolumn']), proportion = 0,
                                 flag = wx.EXPAND)

        self.settingsPanel.SetSizer(mainSizer)

    def _doSelLayout(self, title, sel): 

        selSizer = wx.BoxSizer(orient = wx.VERTICAL)

        selTitleSizer = wx.BoxSizer(wx.HORIZONTAL)
        selTitleSizer.Add(item = title, proportion = 1,
                          flag = wx.LEFT | wx.TOP | wx.EXPAND, border = 5)

        selSizer.Add(item = selTitleSizer, proportion = 0,
                                 flag = wx.EXPAND)
        selSizer.Add(item = sel, proportion = 0,
                     flag = wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER_VERTICAL,
                     border = 5)
        return selSizer


    def OnVectSel(self, event):

        self.inputData['alayer'].InsertLayers(vector = self.inputData['input'].GetValue())
        self.inputData['nlayer'].InsertLayers(vector = self.inputData['input'].GetValue())

        self.OnALayerSel(event) 
        self.OnNLayerSel(event)


    def OnALayerSel(self, event):

        self.inputData['afcolumn'].InsertColumns(vector = self.inputData['input'].GetValue(), 
                                                 layer = self.inputData['alayer'].GetValue(), 
                                                 type = self.columnTypes)
        self.inputData['abcolumn'].InsertColumns(vector = self.inputData['input'].GetValue(), 
                                                 layer = self.inputData['alayer'].GetValue(), 
                                                 type = self.columnTypes)


    def OnNLayerSel(self, event):

        self.inputData['ncolumn'].InsertColumns(vector = self.inputData['input'].GetValue(), 
                                                layer = self.inputData['nlayer'].GetValue(), 
                                                type = self.columnTypes)
 
    def OnCloseDialog(self, event):
        """!Cancel dialog"""

        self.parent.dialogs['vnet'] = None
        self.Destroy()

    def SetNodeStatus(self, item, itemIndex):
        """!Before point is drawn, decides properties of drawing style"""
        key = self.list.GetItemData(itemIndex)
        gcp = self.list.itemDataMap[key]

        if not self.list.IsChecked(key):
                wxPen = "unused"
                item.hide = False
        else:
            wxPen = "default"

        if key == self.list.selected:
            wxPen = "selected"

        item.SetPropertyVal('label', str(itemIndex + 1))
        item.SetPropertyVal('penName', wxPen)       


    def OnMapClickHandler(self, event):
        """!Takes coordinates from map window."""

        if event == 'unregistered':
            ptListToolbar = self.toolbars['pointsList']
            if ptListToolbar:
                ptListToolbar.ToggleTool(vars(ptListToolbar)["insertPoint"], False)  # TODO 
            self.handlerRegistered = False
            return

        if not self.list.itemDataMap:
            self.list.AddItem(None)

        e, n = self.mapWin.GetLastEN()

        index = self.list.selected
        key = self.list.GetItemData(index)

        self.pointsToDraw.GetItem(key).SetCoords([e, n])

        self.mapWin.UpdateMap(render=False, renderVector=False)

    def OnAnalyze(self, event):
        """!Takes coordinates from map window."""

        inType = self.vnetParams[self.currAnModule]["inputType"]

        cmdParams = [self.currAnModule]
        cmdParams.extend(self._getInputParams())
        cmdParams.append("output=" + self.tmp_result)

        catPts = self._getPtByCat()

        if inType == "cats":
            self._catsInType(cmdParams, catPts)
        elif inType == "stdin":
            self._stdinInType(cmdParams, catPts)

    def _stdinInType(self, cmdParams, catPts):

        if len(self.pointsToDraw.GetAllItems()) < 1:
            return

        catPts = self._getPtByCat()
        cats = self.vnetParams[self.currAnModule]["cmdParams"]["cats"]

        cmdPts = []
        for cat in cats:
            if  len(catPts[cat[0]]) < 1:
                GMessage(parent = self,
                         message=_("Pleas choose 'to' and 'from' point."))
                return
            cmdPts.append(catPts[cat[0]][0])


        resId = int(UserSettings.Get(group ='vnet', 
                                     key = 'analysisSettings', 
                                     subkey = 'resultId'))

        inpPoints = str(resId) + " " + str(cmdPts[0][0]) + " " + str(cmdPts[0][1]) + \
                                 " " + str(cmdPts[1][0]) + " " + str(cmdPts[1][1])

        cmdParams.append("stdin=" + inpPoints)

        dmax = int(UserSettings.Get(group = 'vnet', 
                                    key ='analysisSettings', 
                                    subkey ='maxDist'))

        cmdParams.append("dmax=" + str(dmax))
        cmdParams.append("input=" + self.inputData['input'].GetValue())

        self._executeCommand(cmdParams)
        self._addTempLayer()

    def RemoveTmpMap(self, map):

        RunCommand('g.remove', vect = map)
        self.tmpMaps.remove(map)

    def _catsInType(self, cmdParams, catPts):

        cats = RunCommand("v.category",
                           input = self.inputData['input'].GetValue(),
                           option = "report",
                           flags = "g",
                           read = True)     


        cats = cats.splitlines()
        for cat in cats:#TODO
            cat = cat.split()
            if "all" in cat:
                maxCat = int(cat[4])
                break

        layerNum = self.inputData["nlayer"].GetValue().strip()
        if not layerNum:
            layerNum = 1 #TODO


        pt_ascii, catsNums = self._getAsciiPts (catPts = catPts, 
                                                maxCat = maxCat, 
                                                layerNum = layerNum)

        tmpInPts = "vnet_in_pts"
        self.tmpMaps.append(tmpInPts)

        ret, msg =  RunCommand("v.edit",
                                map = tmpInPts,
                                stdin = pt_ascii,
                                input = "-",
                                tool = 'create',
                                flags = "n",
                                overwrite = True,
                                getErrorMsg = True)
        print msg

        dmax = int(UserSettings.Get(group = 'vnet', 
                                    key ='analysisSettings', 
                                    subkey ='maxDist'))

        tmpInPtsConnected = "vnet_in_pts_connected"
        self.tmpMaps.append(tmpInPtsConnected)

        ret, msg =  RunCommand("v.net",
                                points = tmpInPts,
                                stdin = pt_ascii,
                                output = tmpInPtsConnected,
                                input =  self.inputData["input"].GetValue(),
                                operation = 'connect',
                                thresh = dmax,
                                alayer =  self.inputData["alayer"].GetValue(),
                                nlayer=  self.inputData["nlayer"].GetValue(),
                                overwrite = True,
                                getErrorMsg = True,
                                quiet = True)
        print msg

        self.RemoveTmpMap(tmpInPts)

        cmdParams.append("input=" + tmpInPtsConnected)
        for catName, catNum in catsNums.iteritems():
            if catNum[0] == catNum[1]:
                cmdParams.append(catName + "=" + str(catNum[0]))
            else:
                cmdParams.append(catName + "=" + str(catNum[0]) + "-" + str(catNum[1]))

        self._executeCommand(cmdParams)
        self.RemoveTmpMap(tmpInPtsConnected)

        if self.currAnModule == "v.net.alloc": #TODO ugly hack
            self.UpdateCmdList(self.tmp_result, True)
        else: 
            self.UpdateCmdList(self.tmp_result, False)

        self._addTempLayer()

    def _getInputParams(self):

        inParams = []
        for col in self.vnetParams[self.currAnModule]["cmdParams"]["cols"]:

            if "inputField" in self.attrCols[col]:
                colInptF = self.attrCols[col]["inputField"]
            else:
                colInptF = col

            inParams.append(col + '=' + self.inputData[colInptF].GetValue())

        for layer in ['alayer', 'nlayer']:  #TODO input
            inParams.append(layer + "=" + self.inputData[layer].GetValue())

        return inParams

    def _getPtByCat(self):

        cats = self.vnetParams[self.currAnModule]["cmdParams"]["cats"]

        ptByCats = {}
        for cat in self.vnetParams[self.currAnModule]["cmdParams"]["cats"]:
            ptByCats[cat[0]] = []
 
        for i in range(len(self.list.itemDataMap)):
            key = self.list.GetItemData(i)
            if self.list.IsChecked(key):
                for cat in cats:
                    if cat[1] == self.list.itemDataMap[key][1] or len(ptByCats) == 1: 
                        ptByCats[cat[0]].append(self.pointsToDraw.GetItem(key).GetCoords())
                        continue

        return ptByCats

    def _getAsciiPts (self, catPts, maxCat, layerNum):

        catsNums = {}
        pt_ascii = ""
        catNum = maxCat

        if layerNum:
            nlayer = layerNum
        else:
            nlayer = 1 #TODO ugly hack

        for catName, pts in catPts.iteritems():

            catsNums[catName] = [catNum + 1]
            for pt in pts:
                catNum += 1
                pt_ascii += "P 1 1\n"
                pt_ascii += str(pt[0]) + " " + str(pt[1]) +  "\n"
                pt_ascii += str(nlayer) + " " + str(catNum) + "\n"

            catsNums[catName].append(catNum)

        return pt_ascii, catsNums

    def _executeCommand(self, cmd):

        cmd  = utils.CmdToTuple(cmd)

        for c, v in cmd[1].items():
            if not v.strip():
                cmd[1].pop(c)

        ret, msg = RunCommand(cmd[0],
                             getErrorMsg = True,
                             quiet = True,
                             overwrite = True, #TODO init test 
                             **cmd[1])

    def _addTempLayer(self):

        if self.tmpResultLayer:
            self.mapWin.Map.DeleteLayer(layer = self.tmpResultLayer)

        self.tmpResultLayer = self.mapWin.Map.AddLayer(type = "vector",  command = self.cmdlist, 
                                                       l_active=True,    name = self.tmp_result, 
                                                       l_hidden = False, l_opacity = 1.0, 
                                                       l_render = True,  pos = 1)

        self.mapWin.UpdateMap(render=True, renderVector=True)

    def _adaptPointsList(self):

        prevParamsCats = self.vnetParams[self.prevAnModule]["cmdParams"]["cats"]
        currParamsCats = self.vnetParams[self.currAnModule]["cmdParams"]["cats"]

    
        for key in range(len(self.list.itemDataMap)):            
            iCat = 0
            for ptCat in prevParamsCats:
                if self.list.itemDataMap[key][1] ==  ptCat[1]:
                    self.list.EditCellKey(key, 1, currParamsCats[iCat][1])
                iCat += 1

        colValues = [""]
        for ptCat in currParamsCats:
            colValues.append(ptCat[1])

        self.list.ChangeColType(1, colValues)

        self.prevAnModule = self.currAnModule
  

    def UpdateCmdList(self, layerName, colorsByCats = False):
        """!Displays vnet settings dialog"""

        col = UserSettings.Get(group='vnet', key='resStyle', subkey= "color")
        width = UserSettings.Get(group='vnet', key='resStyle', subkey= "width")

        self.cmdlist = ['d.vect', 'map=%s' % layerName, 
                        "layer=1",'width=' + str(width)]

        if colorsByCats:
            self.cmdlist.append('flags=c')
        else:
            self.cmdlist.append('color=' + str(col[0]) + ':' + str(col[1]) + ':' + str(col[2]))

    def OnInsertPoint(self, event):
        if self.handlerRegistered == False:
            self.mapWin.RegisterMouseEventHandler(wx.EVT_LEFT_DOWN, 
                                                  self.OnMapClickHandler,
                                                  wx.StockCursor(wx.CURSOR_CROSS))
            self.handlerRegistered = True

        else:
            self.mapWin.UnregisterMouseEventHandler(wx.EVT_LEFT_DOWN, 
                                                  self.OnMapClickHandler)
            self.handlerRegistered = False

    def OnSaveTmpLayer(self, event):

        dlg = AddLayerDialog(parent = self)

        if dlg.ShowModal() == wx.ID_OK:

            ret, std, msg = RunCommand("g.rename",
                             overwrite = dlg.overwrite.GetValue(),
                             vect = [self.tmp_result, dlg.vectSel.GetValue()],
                             read = True,
                             getErrorMsg = True)

            self.UpdateCmdList(dlg.vectSel.GetValue())
            if  self.mapWin.tree.FindItemByData(key = 'name', value =  dlg.vectSel.GetValue()) is None:
                self.mapWin.tree.AddLayer(ltype = "vector", 
                                          lname = dlg.vectSel.GetValue(),
                                          lcmd = self.cmdlist,
                                          lchecked = True)
            self.UpdateCmdList(self.tmp_result)

    def OnSettings(self, event):
        """!Displays vnet settings dialog"""
        dlg = SettingsDialog(parent=self, id=wx.ID_ANY, title=_('Settings'))
        
        if dlg.ShowModal() == wx.ID_OK:
            pass
        
        dlg.Destroy()

    def OnAnalysisChanged(self, event):

        # finds module name according to value in anChoice
        for module, params in self.vnetParams.iteritems():
            chLabel = self.toolbars['mainToolbar'].anChoice.GetValue()
            if params["label"] == chLabel:
                self.currAnModule = module
                break

        if  len(self.vnetParams[self.currAnModule]["cmdParams"]["cats"]) > 1: 
            self._adaptPointsList()

    def _initvnetParams(self):
        """!Initializes parameters for different v.net.* analysis """

        self.attrCols = {
                          'afcolumn' : {"label" : "Arc forward/both direction(s) cost column:"}, #TODO add dynamic generation of data tab
                          'abcolumn' : {"label" : "Arc backward direction cost column:"},
                          'acolumn' : {
                                       "label" : "Arcs' cost column (for both directions:",
                                       "inputField" : 'afcolumn'
                                      },
                          'ncolumn' : {"label" : "Node cost column:"}
                        }

        self.vnetParams = {
                                   "v.net.path" : {
                                                     "label" : _("Shortest path %s") % "(v.net.path)",  
                                                     "cmdParams" : {
                                                                      "cats" :  [
                                                                                    ["st_pt", _("Start point")], 
                                                                                    ["end_pt", _("End point")] 
                                                                                ],
                                                                      "cols" :  [
                                                                                 'afcolumn',
                                                                                 'abcolumn',
                                                                                 'ncolumn'
                                                                                ],
                                                                      "other" : {
                                                                                 "dmax" : int,
                                                                                 "id"  : int 
                                                                                }
                                                                   },
                                                     "inputType" : "stdin",
                                                  },

                                    "v.net.salesman" : {
                                                        "label" : _("Salesman %s") % "(v.net.salesman)",  
                                                        "cmdParams" : {
                                                                        "cats" : [["ccats", None]],
                                                                        "cols" : [
                                                                                  'afcolumn',
                                                                                  'abcolumn'
                                                                                 ],
                                                                      },
                                                        "inputType" : "cats"
                                                       },
                                    "v.net.flow" : {
                                                     "label" : _("Flow %s") % "(v.net.flow)",  
                                                     "cmdParams" : {
                                                                      "cats" : [
                                                                                ["source_cats", _("Source point")], 
                                                                                ["sink_cats", _("Sink point")]
                                                                               ],                                                   
                                                                      "cols" : [
                                                                                'afcolumn',
                                                                                'abcolumn',
                                                                                'ncolumn'
                                                                               ]
                                                                  },
                                                     "inputType" : "cats"
                                                   },
                                    "v.net.alloc" : {
                                                     "label" : _("Allocate subnets for nearest centres %s") % "(v.net.alloc)",  
                                                     "cmdParams" : {
                                                                      "cats" : [["ccats", None]],                           
                                                                      "cols" : [
                                                                                 'afcolumn',
                                                                                 'abcolumn',
                                                                                 'ncolumn'
                                                                               ]
                                                                  },
                                                     "inputType" : "cats"
                                                   },
                                    "v.net.steiner" : {
                                                     "label" : _("Create Steiner tree for the network and given terminals %s") % "(v.net.steiner)",  
                                                     "cmdParams" : {
                                                                      "cats" : [["tcats", None]],                           
                                                                      "cols" : [
                                                                                 'acolumn',
                                                                               ]
                                                                  },
                                                     "inputType" : "cats"
                                                   }
                                }

        self.vnetModulesOrder = ["v.net.path", 
                                 "v.net.salesman",
                                 #"v.net.flow",
                                 "v.net.alloc",
                                 #"v.net.steiner"
                                 ] # order in the choice of analysis
        self.currAnModule = self.vnetModulesOrder[0]
        self.prevAnModule = self.vnetModulesOrder[0]
class NodesList(PointsList):
    def __init__(self, parent, dialog, cols, id=wx.ID_ANY):
        """! List with points for analysis
        """

        self.dialog = dialog # VNETDialog class

        PointsList.__init__(self, parent = parent, cols = cols, id =  id)      

    def AddItem(self, event):
        """!
        Appends an point to list
        """       
        PointsList.AddItem(self, event)   
 
        self.dialog.pointsToDraw.AddItem(coords = [0,0], 
                                         label = str(self.selectedkey + 1))

        self.dialog.mapWin.UpdateMap(render=True, renderVector=True)


    def DeleteItem(self, event):
        """!
        Deletes selected point in list
        """

        key = self.GetItemData(self.selected)
        PointsList.DeleteItem(self, event)

        if self.selected != wx.NOT_FOUND:
            item = self.dialog.pointsToDraw.GetItem(key)
            self.dialog.pointsToDraw.DeleteItem(item)

    def OnItemSelected(self, event):
        """
        Item selected
        """

        PointsList.OnItemSelected(self, event)
        self.dialog.mapWin.UpdateMap(render=False, renderVector=False)
        self.dialog._getPtByCat()
        event.Skip()

    def OnCheckItem(self, index, flag):
        """!Item is checked/unchecked"""

        key = self.GetItemData(index)
        checkedVal = self.itemDataMap[key][1]

        currModule = self.dialog.currAnModule
        cats = self.dialog.vnetParams[currModule]["cmdParams"]["cats"]

        if len(cats) <= 1:
            return 

        if checkedVal == "":
                self.CheckItem(key, False)
                return

        if currModule != "v.net.path":
            return

        iItem = 0
        for item in self.itemDataMap:
            if item[1] == checkedVal and key != iItem and flag:
                checkedKey = self.GetItemData(iItem)
                self.CheckItem(checkedKey, False)
            iItem += 1


class SettingsDialog(wx.Dialog):
    def __init__(self, parent, id, title, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE):
        """!Settings for v.net analysis dialog"""
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)

        maxValue = 1e8
        self.parent = parent

        self.panel = wx.Panel(parent = self, id = wx.ID_ANY)

        self.colorLabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = _("Line color:"))
        col = UserSettings.Get(group ='vnet', key ='resStyle', subkey = "color")        
        self.colorField = csel.ColourSelect(parent = self.panel, id = wx.ID_ANY,
                                            colour = wx.Colour(col[0],
                                                               col[1],
                                                               col[2], 
                                                               255))

        self.widthLabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label =_("Line width:"))
        self.widthField = wx.SpinCtrl(parent = self.panel, id = wx.ID_ANY, min = 1, max = 10)
        width = int(UserSettings.Get(group = 'vnet', key = 'resStyle', subkey = 'width'))
        self.widthField.SetValue(width)

        self.idLabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label =_("Id of line:"))
        self.resIdFiled = wx.SpinCtrl(parent = self.panel, id = wx.ID_ANY, min = 1, max = maxValue)
        resId = int(UserSettings.Get(group ='vnet', key ='analysisSettings', subkey = 'resultId'))
        self.resIdFiled.SetValue(resId)

        self.maxDistlabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = _("Maximum distance \n to the network:"))
        self.maxDistField = wx.SpinCtrl(parent = self.panel, id = wx.ID_ANY, min = 0, max = maxValue) #TODO
        maxDist = int(UserSettings.Get(group = 'vnet', key = 'analysisSettings', subkey ='maxDist'))
        self.maxDistField.SetValue(maxDist)

        # buttons
        #btnSave = wx.Button(self.panel, wx.ID_SAVE)
        self.btnApply = wx.Button(self.panel, wx.ID_APPLY)
        self.btnClose = wx.Button(self.panel, wx.ID_CLOSE)
        self.btnApply.SetDefault()

        # bindings
        self.btnApply.Bind(wx.EVT_BUTTON, self.OnApply)
        self.btnApply.SetToolTipString(_("Apply changes for the current session"))
        #btnSave.Bind(wx.EVT_BUTTON, self.OnSave)
        #btnSave.SetToolTipString(_("Apply and save changes to user settings file (default for next sessions)"))
        self.btnClose.Bind(wx.EVT_BUTTON, self.OnClose)
        self.btnClose.SetToolTipString(_("Close dialog"))

        self._layout()
        self.SetMinSize(self.GetBestSize())

    def _layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        styleBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                label =" %s " % _("Analysis outcome line style:"))
        styleBoxSizer = wx.StaticBoxSizer(styleBox, wx.VERTICAL)

        gridSizer = wx.GridBagSizer(vgap = 1, hgap = 1)

        row = 0
        gridSizer.Add(item = self.colorLabel, flag = wx.ALIGN_CENTER_VERTICAL, pos =(row, 0))
        gridSizer.Add(item = self.colorField,
                      flag = wx.ALIGN_RIGHT | wx.ALL, border = 5,
                      pos =(row, 1))

        row += 1
        gridSizer.Add(item =  self.widthLabel, flag=wx.ALIGN_CENTER_VERTICAL, pos=(row, 0))
        gridSizer.Add(item = self.widthField,
                      flag = wx.ALIGN_RIGHT | wx.ALL, border = 5,
                      pos = (row, 1))

        styleBoxSizer.Add(item = gridSizer, flag = wx.EXPAND)


        analysisBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                   label = " %s " % _("Analysis settings:"))
        analysisBoxSizer = wx.StaticBoxSizer(analysisBox, wx.VERTICAL)

        row = 0
        gridSizer = wx.GridBagSizer(vgap = 1, hgap = 1)
        gridSizer.Add(item = self.idLabel, flag = wx.ALIGN_CENTER_VERTICAL, pos = (row, 0))
        gridSizer.Add(item = self.resIdFiled,
                      flag = wx.ALIGN_RIGHT | wx.ALL, border = 5,
                      pos = (row, 1))

        row += 1
        gridSizer.Add(item = self.maxDistlabel, flag = wx.ALIGN_CENTER_VERTICAL, pos = (row, 0))
        gridSizer.Add(item = self.maxDistField,
                      flag = wx.ALIGN_RIGHT | wx.ALL, border = 5,
                      pos = (row, 1))

        analysisBoxSizer.Add(item = gridSizer, flag = wx.EXPAND)

        # sizers
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(self.btnApply, flag = wx.LEFT | wx.RIGHT, border = 5)
        #btnSizer.Add(btnSave, flag=wx.LEFT | wx.RIGHT, border=5)
        btnSizer.Add(self.btnClose, flag = wx.LEFT | wx.RIGHT, border = 5)

        sizer.Add(item = styleBoxSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 1)
        sizer.Add(item = analysisBoxSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 1)
        sizer.Add(item = btnSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 0)    

        self.panel.SetSizer(sizer)
        sizer.Fit(self)

    def UpdateSettings(self):

        UserSettings.Set(group ='vnet', key ='resStyle', subkey ='width',
                         value = self.widthField.GetValue())

        UserSettings.Set(group = 'vnet', key ='resStyle', subkey ='color',
                         value = self.colorField.GetColour())

        UserSettings.Set(group = 'vnet', key ='analysisSettings', subkey ='resultId',
                         value = self.resIdFiled.GetValue())

        UserSettings.Set(group ='vnet', key ='analysisSettings', subkey ='maxDist',
                         value = self.maxDistField.GetValue())

        if self.parent.tmpResultLayer:

            self.parent.UpdateCmdList(self.parent.tmp_result)

            self.parent.tmpResultLayer.SetCmd(self.parent.cmdlist)
            self.parent.mapWin.UpdateMap(render=True, renderVector=True)#TODO optimalization
     

    #def OnSave(self, event): TODO
    #   """!Button 'Save' pressed"""
    #    self.UpdateSettings()
    #    fileSettings = {}
    #    UserSettings.ReadSettingsFile(settings=fileSettings)
    #    fileSettings['vnet'] = UserSettings.Get(group='vnet')
    #    file = UserSettings.SaveToFile(fileSettings)
    #    self.parent.parent.goutput.WriteLog(_('Vnet fron end settings saved to file \'%s\'.') % file) TODO
    #    self.Close()

    def OnApply(self, event):
        """!Button 'Apply' pressed"""
        self.UpdateSettings()
        #self.Close()

    def OnClose(self, event):
        """!Button 'Cancel' pressed"""
        self.Close()

class AddLayerDialog(wx.Dialog):
    """!Adds layer with analysis result into layer tree"""
   
    def __init__(self, parent,id=wx.ID_ANY,
                 title =_("Add analysis result into layer tree"), style=wx.DEFAULT_DIALOG_STYLE):
        """!Dialog for editing item cells in list"""

        wx.Dialog.__init__(self, parent, id, title = _(title), style = style)

        self.panel = wx.Panel(parent = self)
       
        # text fields and it's captions
        self.vectSel = Select(parent = self.panel, type = 'vector', size = (-1, -1))
        self.vectSellabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY,
                                          label = _("Layer name:")) 

        self.overwrite = wx.CheckBox(parent = self.panel, id=wx.ID_ANY,
                                     label = _("Overwrite existing layer"))

        # buttons
        self.btnCancel = wx.Button(self.panel, wx.ID_CANCEL)
        self.btnOk = wx.Button(self.panel, wx.ID_OK)
        self.btnOk.SetDefault()

        self._layout()

    def _layout(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox (parent = self.panel, id = wx.ID_ANY,
                            label = "Added layer")

        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # source coordinates
        gridSizer = wx.GridBagSizer(vgap = 5, hgap = 5)

        row = 0
        gridSizer.Add(item = self.vectSellabel, 
                      flag = wx.ALIGN_CENTER_VERTICAL,
                      pos = (row, 0))

        gridSizer.Add(item = self.vectSel, 
                      pos = (row, 1))

        boxSizer.Add(item = gridSizer, proportion = 1,
                     flag = wx.EXPAND | wx.ALL, border = 5)

        sizer.Add(item = boxSizer, proportion = 1,
                  flag = wx.EXPAND | wx.ALL, border = 5)

        row +=1 
        gridSizer.Add(item = self.overwrite, pos =(row, 0))

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()

        sizer.Add(item = btnSizer, proportion = 0,
                  flag = wx.ALIGN_RIGHT | wx.ALL, border = 5)

        self.panel.SetSizer(sizer)
        sizer.Fit(self)
