"""!
@package vnet.dialog

@brief Dialog for vector network analysis front-end

Classes:
 - dialog::VNETDialog
 - dialog::SettingsDialog
 - dialog::AddLayerDialog

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Stepan Turek <stepan.turek seznam.cz> (GSoC 2012)
@author Martin Landa <landa.martin gmail.com> (mentor)
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
from core.gcmd        import RunCommand, GMessage

import wx
import wx.aui
import wx.lib.flatnotebook  as FN
from copy import copy
class VNETDialog(wx.Dialog):
    def __init__(self, parent,
                 id=wx.ID_ANY, title = "Vector network analysis",
                 style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER):
        """!Dialolog for vector network analasis"""

        wx.Dialog.__init__(self, parent, id, style=style, title = title)

        self.parent  = parent  #mapdisp.frame MapFrame
        self.mapWin = parent.MapWindow
        self.inputData = {}

        # registration graphics for drawing
        self.pointsToDraw = self.mapWin.RegisterGraphicsToDraw(graphicsType = "point", 
                                                               setStatusFunc = self.SetNodeStatus)
        self.pointsToDraw.SetPropertyVal("size", 10) # TODO settings

        # getting attribute table columns only whith numbers (costs)
        self.columnTypes = ['integer', 'double precision'] 

        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass_map.ico'), wx.BITMAP_TYPE_ICO))
        
        # toolbars
        self.toolbars = {}
        self.toolbars['mainToolbar'] = MainToolbar(parent = self)

        #
        # Fancy gui
        #
        self._mgr = wx.aui.AuiManager(self)

        # Columns in points list
        self.cols =   [
                        ['type', ["", "Start point", "End point"], ""]
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
                        ['analasisSettings', 'maxDist', 10000],
                        ['analasisSettings', 'resultId', 1]
                      ]
        for init in initSettings:

            UserSettings.Append(dict = UserSettings.userSettings, 
                                group ='vnet', 
                                key = init[0],
                                subkey =init[1], 
                                value = init[2])

        # name of temporary map   
        self.tmp_result = "tmp_map" 

        # set options for drawing the map  
        self.UpdateCmdList(self.tmp_result)

        # adds 2 points into list
        for i in range(2):
            self.list.AddItem(None)
            self.list.EditCell(i, 1, self.cols[1][1][1 + i]) 
            self.list.CheckItem(i, True)

        self.Bind(wx.EVT_CLOSE, self.OnCloseDialog)

        dlgSize = (300,450)
        self.SetMinSize(dlgSize)
        self.SetInitialSize(dlgSize)

    def  __del__(self):
        """!Removes temp layer with analasis result, unregisters handlers and graphics"""


        self.mapWin.UnregisterGraphicsToDraw(self.pointsToDraw)

        RunCommand('g.remove', vect = self.tmp_result)
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
        vectSelTitle.SetLabel("Choose vector layers for analysis:")

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

        self.inputData['input'].Bind(wx.EVT_TEXT, self.OnVectSel)
        self.inputData['alayer'].Bind(wx.EVT_TEXT, self.OnVectSel)
        self.inputData['nlayer'].Bind(wx.EVT_TEXT, self.OnVectSel)

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

        self.inputData['alayer'].InsertLayers(vector = self.inputData['input'].GetValue())#TODO split
        self.inputData['nlayer'].InsertLayers(vector = self.inputData['input'].GetValue())

        self.inputData['afcolumn'].InsertColumns(vector = self.inputData['input'].GetValue(), 
                                                 layer = self.inputData['alayer'].GetValue(), 
                                                 type = self.columnTypes)
        self.inputData['abcolumn'].InsertColumns(vector = self.inputData['input'].GetValue(), 
                                                 layer = self.inputData['alayer'].GetValue(), 
                                                 type = self.columnTypes)

    def OnCloseDialog(self, event):
        """!Cancel dialog"""

        self.parent.dialogs['vnet'] = None
        self.Destroy()

    def SetNodeStatus(self, item, itemIndex):
        """!Before point is drawed, decides properties of drawing style"""
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

        if len(self.pointsToDraw.GetAllItems()) < 1:
            return

        startPtLabel = self.cols[1][1][1]            
        endPtLabel = self.cols[1][1][2]

        inputCoords = { startPtLabel : None,
                        endPtLabel : None}

        for i in range(len(self.list.itemDataMap)):
            key = self.list.GetItemData(i)
            if self.list.IsChecked(key):
                for k, v in inputCoords.iteritems():
                    if k == self.list.itemDataMap[key][1]:       
                        inputCoords[k] = self.pointsToDraw.GetItem(key).GetCoords        ()

        if None in inputCoords.values():
            GMessage(parent       = self,
                     message=_("Pleas choose 'to' and 'from' point."))
            return            

        resId = int(UserSettings.Get(group='vnet', 
                                     key='analasisSettings', 
                                     subkey='resultId'))

        s = str(resId) + " " + str(inputCoords[startPtLabel][0]) + " " + str(inputCoords[startPtLabel][1]) + \
                         " " + str(inputCoords[endPtLabel][0]) + " " + str(inputCoords[endPtLabel][1])

        coordsTempFile = grass.tempfile()#TODO stdin
        coordsTempFileOpened = open(coordsTempFile, 'w')
        coordsTempFileOpened.write(s)
        coordsTempFileOpened.close()

        params = {}
        for k, v in self.inputData.iteritems():
            if not v.GetValue():
                params[k] = None
            else:
                params[k] = v.GetValue()
 
        ret, std, msg = RunCommand('v.net.path',
                                    input = params['input'],
                                    output = self.tmp_result,
                                    overwrite = True,
                                    alayer = params['alayer'], 
                                    nlayer = params['nlayer'], 
                                    afcolumn = params['afcolumn'],
                                    abcolumn = params['abcolumn'],
                                    file = coordsTempFile,
                                    dmax = int(UserSettings.Get(group='vnet', 
                                                                key='analasisSettings', 
                                                                subkey='maxDist')),
                                    read = True,
                                    getErrorMsg = True)

        grass.try_remove(coordsTempFile)

        if self.tmpResultLayer:
            self.mapWin.Map.DeleteLayer(layer = self.tmpResultLayer)

        self.tmpResultLayer = self.mapWin.Map.AddLayer(type = "vector",  command = self.cmdlist, 
                                                       l_active=True,    name = self.tmp_result, 
                                                       l_hidden = False, l_opacity = 1.0, 
                                                       l_render = True,  pos = 1)

        self.mapWin.UpdateMap(render=True, renderVector=True)

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

            ret, std, msg = RunCommand("g.copy",
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

    def UpdateCmdList(self, layerName):
        """!Displays vnet settings dialog"""

        col = UserSettings.Get(group='vnet', key='resStyle', subkey= "color")
        width = UserSettings.Get(group='vnet', key='resStyle', subkey= "width")

        self.cmdlist = ['d.vect', 'map=%s' % layerName, \
                        'color=' + str(col[0]) + ':' + str(col[1]) + ':' + str(col[2]), \
                        'width=' + str(width)]# TODO settings

class NodesList(PointsList):
    def __init__(self, parent, dialog, cols, id=wx.ID_ANY):
        """! List with points for analasis
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

        event.Skip()

    def OnCheckItem(self, index, flag):
        """!Item is checked/unchecked"""

        key = self.GetItemData(index)
        checkedVal = self.itemDataMap[key][1]

        if checkedVal == "":
                self.CheckItem(key, False)
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
        """!Settings for v.net analasis dialog"""
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
        resId = int(UserSettings.Get(group ='vnet', key ='analasisSettings', subkey = 'resultId'))
        self.resIdFiled.SetValue(resId)

        self.maxDistlabel = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = _("Maximum distance \n to the network:"))
        self.maxDistField = wx.SpinCtrl(parent = self.panel, id = wx.ID_ANY, min = 0, max = maxValue) #TODO
        maxDist = int(UserSettings.Get(group = 'vnet', key = 'analasisSettings', subkey ='maxDist'))
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
                                label =" %s " % _("Analasis outcome line style:"))
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


        analasisBox = wx.StaticBox(parent = self.panel, id = wx.ID_ANY,
                                   label = " %s " % _("Analasis settings:"))
        analasisBoxSizer = wx.StaticBoxSizer(analasisBox, wx.VERTICAL)

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

        analasisBoxSizer.Add(item = gridSizer, flag = wx.EXPAND)

        # sizers
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add(self.btnApply, flag = wx.LEFT | wx.RIGHT, border = 5)
        #btnSizer.Add(btnSave, flag=wx.LEFT | wx.RIGHT, border=5)
        btnSizer.Add(self.btnClose, flag = wx.LEFT | wx.RIGHT, border = 5)

        sizer.Add(item = styleBoxSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 1)
        sizer.Add(item = analasisBoxSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 1)
        sizer.Add(item = btnSizer, flag = wx.EXPAND | wx.ALL, border = 5, proportion = 0)    

        self.panel.SetSizer(sizer)
        sizer.Fit(self)

    def UpdateSettings(self):

        UserSettings.Set(group ='vnet', key ='resStyle', subkey ='width',
                         value = self.widthField.GetValue())

        UserSettings.Set(group = 'vnet', key ='resStyle', subkey ='color',
                         value = self.colorField.GetColour())

        UserSettings.Set(group = 'vnet', key ='analasisSettings', subkey ='resultId',
                         value = self.resIdFiled.GetValue())

        UserSettings.Set(group ='vnet', key ='analasisSettings', subkey ='maxDist',
                         value = self.maxDistField.GetValue())

        if self.parent.tmpResultLayer:

            self.parent.UpdateCmdList(self.parent.tmp_result)

            self.parent.tmpResultLayer.SetCmd(self.parent.cmdlist)
            self.parent.mapWin.UpdateMap(render=True, renderVector=True)#TODO necessary
     

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
                 title =_("Add analasis result into layer tree"), style=wx.DEFAULT_DIALOG_STYLE):
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