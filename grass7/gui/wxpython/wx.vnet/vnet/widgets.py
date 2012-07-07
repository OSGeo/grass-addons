"""!
@package vnet.widgets

@brief Base class for list of points. 

Classes:
 - widgets::PointsList
 - widgets::EditItem

(C) 2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Stepan Turek <stepan.turek seznam.cz> (GSoC 2012, mentor: Martin Landa)
"""

import os
import wx
from copy import copy, deepcopy

import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ColumnSorterMixin, ListCtrlAutoWidthMixin

from core import globalvar


class PointsList(wx.ListCtrl,
                 CheckListCtrlMixin,
                 ListCtrlAutoWidthMixin,
                 ColumnSorterMixin):

    def __init__(self, parent, cols, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_HRULES |
                 wx.LC_SINGLE_SEL):
        """!Creates list for points. 

        PointsList class was extracted from GCPList class in GCP manager. 

        Important parameters:
        @param cols is list containing list items. which represents columns.
                This columns will be added in order as they are in list. 
                Class will add as first column "use" with number of point and checkbox.
                Structure of list item must be this:
               -1. item: column name 
               -2. item: If column is editable by user, it must contain convert function to convert
                         inserted string to it's type for sorting. Use None for non editable 
                         columns.
               -3. item: Default value for column cell. Value should be given in it's  type 
                         in order to sorting would work properly.
  
        Example of cols parameter:
                 column name, convert function, default val
        @code
         cols =   [
             wx.ListCtrl, float, 0.0],
                   ['source N', float, 0.0],
                   ['target E', float, 0.0],
                   ['target N', float, 0.0],
                   ['Forward error', None, 0],
                   ['Backward error', None, 0]
                   ['type', ["", "Start point", "End point"], ""] # Select from 3 choices ("Start point", "End point"), 
                                                                  # choice "" is default.
                  ]
        @endcode

        List self.itemDataMap stores data for sorting comparison, it can be used 
        for getting present data in list. If you do not know what you are doing,
        do not modify it. 
 
        """

        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

        # Mixin settings
        CheckListCtrlMixin.__init__(self)
        ListCtrlAutoWidthMixin.__init__(self)
        # TextEditMixin.__init__(self)

        # inserts first column with points numbers and checkoboxes
        cols.insert(0, ['use', False, '0', 0])

        # initialization of dict whith data
        self.cols_data = {}
        self.cols_data["colsNames"] = []
        self.cols_data["colsEditable"] = []        
        self.cols_data["itemDefaultVals"] = []

        for col in cols:
            self.cols_data["colsNames"].append(col[0])
            self.cols_data["colsEditable"].append(col[1])
            self.cols_data["itemDefaultVals"].append(col[2])

        # tracks whether list items are checked or not
        self.CheckList = [] 

        self._CreateCols()

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)

        self.selected = wx.NOT_FOUND
        self.selectedkey = -1


        # CheckListCtrlMixin must set an ImageList first
        self.il = self.GetImageList(wx.IMAGE_LIST_SMALL)

        # images for column sorting
        SmallUpArrow = wx.BitmapFromImage(self.getSmallUpArrowImage())            
        SmallDnArrow = wx.BitmapFromImage(self.getSmallDnArrowImage())            
        self.sm_dn = self.il.Add(SmallDnArrow)
        self.sm_up = self.il.Add(SmallUpArrow)

        # initialize column sorter
        self.itemDataMap = []
        ncols = self.GetColumnCount()
        ColumnSorterMixin.__init__(self, ncols)

        # init to ascending sort on first click
        self._colSortFlag = [1] * ncols

        self.ResizeColumns()
        self.SetColumnWidth(0, 50)

    def _CreateCols(self):
        """! Creates columns in list"""
        if 0:
            # normal, simple columns
            idx_col = 0
            for col in self.cols_data["colsNames"]:
                self.InsertColumn(idx_col, _(col))
                idx_col += 1
        else:
            # the hard way: we want images on the column header
            info = wx.ListItem()
            info.SetMask(wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT)
            info.SetImage(-1)
            info.m_format = wx.LIST_FORMAT_LEFT

            idx_col = 0
            for lbl in self.cols_data["colsNames"]:
                info.SetText(_(lbl)) 
                self.InsertColumnInfo(idx_col, info)
                idx_col += 1


    def AddItem(self, event):
        """! Appends an item to list whith default values"""

        itemData = copy(self.cols_data["itemDefaultVals"])

        self.selectedkey = self.GetItemCount()

        itemData[0] = self.selectedkey + 1
        self.itemDataMap.append(copy(itemData))

        self.Append(map(str, itemData))             

        self.selected = self.GetItemCount() - 1
        self.SetItemData(self.selected, self.selectedkey)

        self.SetItemState(self.selected,
                          wx.LIST_STATE_SELECTED,
                          wx.LIST_STATE_SELECTED)

        self.ResizeColumns()

        return self.selected

    def EditCell(self, item, col, cellData):
        """! Changes value in list"""
        
        self.itemDataMap[self.GetItemData(item)][col] = cellData
        self.SetStringItem(item, col, str(cellData))


    def DeleteItem(self, event = None):
        """! Deletes selected item in list"""
        if self.selected == wx.NOT_FOUND:
            return

        key = self.GetItemData(self.selected)
        wx.ListCtrl.DeleteItem(self, self.selected)

        del self.itemDataMap[key]

        # update key and point number
        for newkey in range(key, len(self.itemDataMap)):
            index = self.FindItemData(-1, newkey + 1)
            self.itemDataMap[newkey][0] = newkey
            self.SetStringItem(index, 0, str(newkey + 1))
            self.SetItemData(index, newkey)

        # update selected
        if self.GetItemCount() > 0:
            if self.selected < self.GetItemCount():
                self.selectedkey = self.GetItemData(self.selected)
            else:
                self.selected = self.GetItemCount() - 1
                self.selectedkey = self.GetItemData(self.selected)
                
            self.SetItemState(self.selected,
                              wx.LIST_STATE_SELECTED,
                              wx.LIST_STATE_SELECTED)
        else:
            self.selected = wx.NOT_FOUND
            self.selectedkey = -1


    def ClearItem(self, event):
        """"! Clears all values in selected item of points list and unchecks it."""
        if self.selected == wx.NOT_FOUN:
            return
        index = self.selected
        i = 0
        for value in self.self.cols_data["itemDefaultVals"]:
            if i == 0:
                i  += 1
                continue
            self.EditCell(index, i, value)
            i  += 1
        self.CheckItem(index, False)

    def ResizeColumns(self, minWidth = [90, 120]):
        """! Resize columns"""
        for i in range(self.GetColumnCount()):
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
            # first column is checkbox, don't set to minWidth
            if i > 0 and self.GetColumnWidth(i) < minWidth[i > 4]:
                self.SetColumnWidth(i, minWidth[i > 4])

        self.SendSizeEvent()

    def GetSelected(self):
        """!Get index of selected item."""
        return self.selected

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self


    def OnItemActivated(self, event):
        """! When item is double clicked, open editor to update coordinate values. """
        data = []

        index = event.GetIndex()
        key = self.GetItemData(index)       
        changed = False

        for i in range(self.GetColumnCount()):
            if  self.cols_data["colsEditable"][i]:
                data.append([i, #culumn number
                             self.GetItem(index, i).GetText(), #cell value 
                             self.cols_data["colsEditable"][i]]) #convert function for type check

        dlg = self.CreateEditDialog(data = data, pointNo = key)

        if dlg.ShowModal() == wx.ID_OK:
            editedData = dlg.GetValues() # string
            
            if len(editedData) == 0:
                GError(parent = self,
                       message=_("Invalid value inserted. Operation canceled."))
            else:
                i = 0
                for editedCell in editedData:
                    if editedCell[1] != data[i][1]:
                        self.SetStringItem(index, editedCell[0], str(editedCell[1]))
                        self.itemDataMap[key][editedCell[0]] = editedCell[1]
                        changed = True
                    i += 1 

        return changed
        
    def CreateEditDialog(self, data, pointNo):
        """!
        It is possible to define in child derived class
        and adapt created dialog (e. g. it's title...) 
        """

        return  EditItem(parent=self, id=wx.ID_ANY, data = data, pointNo=pointNo)

    def OnColClick(self, event):
        """!ListCtrl forgets selected item..."""
        self.selected = self.FindItemData(-1, self.selectedkey)
        self.SetItemState(self.selected,
                          wx.LIST_STATE_SELECTED,
                          wx.LIST_STATE_SELECTED)
        event.Skip()

    def OnItemSelected(self, event):

        if self.selected != event.GetIndex():
            self.selected = event.GetIndex()
            self.selectedkey = self.GetItemData(self.selected)

        event.Skip()

    def getSmallUpArrowImage(self):

        stream = open(os.path.join(globalvar.ETCIMGDIR, 'small_up_arrow.png'), 'rb')
        try:
            img = wx.ImageFromStream(stream)
        finally:
            stream.close()
        return img

    def getSmallDnArrowImage(self):

        stream = open(os.path.join(globalvar.ETCIMGDIR, 'small_down_arrow.png'), 'rb')
        try:
            img = wx.ImageFromStream(stream)
        finally:
            stream.close()
        return img

class EditItem(wx.Dialog):
    
    def __init__(self, parent, data, pointNo, itemCap = "Point No." ,id=wx.ID_ANY,
                 title =_("Edit point"), style=wx.DEFAULT_DIALOG_STYLE):
        """!Dialog for editing item cells in list"""

        wx.Dialog.__init__(self, parent, id, title=_(title), style=style)

        panel = wx.Panel(parent=self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox (parent=panel, id=wx.ID_ANY,
                            label=" %s %s " % (_(itemCap), str(pointNo + 1)))
        boxSizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        # source coordinates
        gridSizer = wx.GridBagSizer(vgap=5, hgap=5)
       
        self.fields = [] 
        self.data = deepcopy(data)


        col = 0
        row = 0
        iField = 0
        for cell in self.data:

            # Select
            if type(cell[2]).__name__ == "list":
                self.fields.append(wx.ComboBox(parent = panel, id = wx.ID_ANY,
                                               choices = cell[2],
                                               style = wx.CB_READONLY, 
                                               size = (110, -1)))
            # Text field
            else:
                if cell[2] == float:
                    validator = FloatValidator()
                elif cell[2] == int:
                    validator = IntegerValidator()
                else:
                    validator = None

                if validator:
                    self.fields.append(wx.TextCtrl(parent=panel, id=wx.ID_ANY, 
                                                   validator = validator, size=(150, -1)))
                else:
                    self.fields.append(wx.TextCtrl(parent=panel, id=wx.ID_ANY, 
                                                   size=(150, -1)))
                    self.fields[iField].SetValue(str(cell[1]))

            label = wx.StaticText(parent = panel, id=wx.ID_ANY,
                                  label = _(parent.GetColumn(cell[0]).GetText()) + ":") # name of column)

            gridSizer.Add(item=label,
                          flag=wx.ALIGN_CENTER_VERTICAL,
                          pos=(row, col))

            col += 1

            gridSizer.Add(item=self.fields[iField],
                          pos=(row, col))


            if col%3 == 0:
                col = 0
                row += 1
            else:
                col += 1

            iField += 1

        boxSizer.Add(item=gridSizer, proportion=1,
                  flag=wx.EXPAND | wx.ALL, border=5)

        sizer.Add(item=boxSizer, proportion=1,
                  flag=wx.EXPAND | wx.ALL, border=5)

        #
        # buttons
        #
        self.btnCancel = wx.Button(panel, wx.ID_CANCEL)
        self.btnOk = wx.Button(panel, wx.ID_OK)
        self.btnOk.SetDefault()

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.btnCancel)
        btnSizer.AddButton(self.btnOk)
        btnSizer.Realize()

        sizer.Add(item=btnSizer, proportion=0,
                  flag=wx.ALIGN_RIGHT | wx.ALL, border=5)

        panel.SetSizer(sizer)
        sizer.Fit(self)

    def GetValues(self):
        """!Return list of values (as strings).
        """

        iField = 0
        self.data
        for cell in self.data:
            value = self.fields[iField].GetValue()
            
            if type(cell[2]).__name__ == "list":
                    cell[1] = value
            else:
                try:
                    cell[1] = cell[2](value)
                except ValueError:
                    return []
            iField += 1

        return self.data
