"""!
@package iclass.toolbars

@brief wxIClass toolbars and icons.

Classes:
 - toolbars::IClassMapToolbar
 - toolbars::IClassToolbar
 - toolbars::IClassMapManagerToolbar

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Vaclav Petras <wenzeslaus gmail.com>
@author Anna Kratochvilova <kratochanna gmail.com>
"""

import wx

from gui_core.toolbars import BaseToolbar, BaseIcons
from icons.icon import MetaIcon
from iclass.dialogs     import IClassMapDialog as MDialog

import grass.script as grass

rdigitIcons = {
    'delCmd' : MetaIcon(img = 'layer-remove',
                            label = _('Delete selected map layer')),

    }
        
class RDigitMapToolbar(BaseToolbar):
    """!RDigit Map toolbar """
    def __init__(self, parent):
        """!RDigit Map toolbar constructor"""
        BaseToolbar.__init__(self, parent)
        
        self.InitToolbar(self._toolbarData())

        # realize the toolbar
        self.Realize()
        
        self.action = { 'id' : self.pan }
        self.defaultAction = { 'id' : self.pan,
                               'bind' : self.parent.OnPan }
        self.OnTool(None)
        self.EnableTool(self.zoomBack, False)
 
    def _toolbarData(self):
        """!Toolbar data"""
        icons = BaseIcons
        return self._getToolbarData((("displaymap", icons["display"],
                                      self.parent.OnDraw),
                                     ("rendermap", icons["render"],
                                      self.parent.OnRender),
                                     ("erase", icons["erase"],
                                      self.parent.OnErase),
                                     (None, ),
                                     ("pan", icons["pan"],
                                      self.parent.OnPan,
                                      wx.ITEM_CHECK),
                                     ("zoomIn", icons["zoomIn"],
                                      self.parent.OnZoomIn,
                                      wx.ITEM_CHECK),
                                     ("zoomOut", icons["zoomOut"],
                                      self.parent.OnZoomOut,
                                      wx.ITEM_CHECK),
                                     ("zoomMenu", icons["zoomMenu"],
                                      self.parent.OnZoomMenu),
                                     (None, ),
                                     ("zoomBack", icons["zoomBack"],
                                      self.parent.OnZoomBack),
                                     ("zoomToMap", icons["zoomExtent"],
                                      self.parent.OnZoomToMap) ))

class RDigitMapManagerToolbar(BaseToolbar):
    """!IClass toolbar
    """
    def __init__(self, parent, mapManager):
        """!IClass toolbar constructor
        """
        BaseToolbar.__init__(self, parent)
        
        self.InitToolbar(self._toolbarData())
        self.choice = wx.Choice(parent = self, id = wx.ID_ANY, size = (300, -1))
        self.choiceid = self.AddControl(self.choice)
        self.choice.Bind(wx.EVT_CHOICE, self.OnSelectLayer)
        
        self.mapManager = mapManager
        # realize the toolbar
        self.Realize()
        
    def _toolbarData(self):
        """!Toolbar data"""
        return self._getToolbarData((("addRast", BaseIcons['addRast'],
                                      self.OnAddRast),
                                      ("delRast", rdigitIcons['delCmd'],
                                      self.OnDelRast)))
                                    
    def OnSelectLayer(self, event):
        layer = self.choice.GetStringSelection()
        self.mapManager.SelectLayer(name = layer)
        
    def OnAddRast(self, event):
        dlg = MDialog(self, title = _("Add raster map"), element = 'raster')
        if dlg.ShowModal() == wx.ID_OK:
            raster = grass.find_file(name = dlg.GetMap(), element = 'cell')
            if raster['fullname']:
                self.mapManager.AddLayer(name = raster['fullname'])
                
        dlg.Destroy()
        
    def OnDelRast(self, event):
        layer = self.choice.GetStringSelection()
        idx = self.choice.GetSelection()
        if layer:
            self.mapManager.RemoveLayer(name = layer, idx = idx)
            
