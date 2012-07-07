"""!
@package vnet.toolbars

@brief Vector network analysis dialog - toolbars

Classes:
 - toolbars::PointListToolbar
 - toolbars::MainToolbar

(C) 2012 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Stepan Turek <stepan.turek seznam.cz> (GSoC 2012, mentor: Martin Landa)
"""

import wx

from icon              import MetaIcon
from gui_core.toolbars import BaseToolbar, BaseIcons

class PointListToolbar(BaseToolbar):
    """!Toolbar for managing list of points

    @param parent reference to VNETDialog
    """
    def __init__(self, parent, list):
        BaseToolbar.__init__(self, parent)
        self.list = list
        self.InitToolbar(self._toolbarData())
        
        # realize the toolbar
        self.Realize()


    def _toolbarData(self):

        icons = {
            'insertPoint'  : MetaIcon(img = 'pointer',
                                    label = _('Insert point with mouse')),
            'pointAdd'     : MetaIcon(img = 'point-create',
                                    label = _('Add new point')),
            'pointDelete'  : MetaIcon(img = 'gcp-delete',
                                    label = _('Delete selected point'))
            }

        return  self._getToolbarData((('insertPoint', icons['insertPoint'],
                                      self.list.dialog.OnInsertPoint,
                                      wx.ITEM_CHECK),
                                     ('pointAdd', icons["pointAdd"],
                                        self.list.AddItem),
                                     ('pointDelete', icons["pointDelete"],
                                        self.list.DeleteItem)))
                                    

class MainToolbar(BaseToolbar):
    """!Main toolbar
    """
    def __init__(self, parent):
        BaseToolbar.__init__(self, parent)
        
        self.InitToolbar(self._toolbarData())

        choices = [ _('Shortest path'), ]
        self.combo = wx.ComboBox(parent = self, id = wx.ID_ANY,
                                 choices = choices,
                                 style = wx.CB_READONLY, size = (110, -1))
        self.combo.SetSelection(0)
        
        self.comboid = self.AddControl(self.combo)
        #self.parent.Bind(wx.EVT_COMBOBOX, self.OnSelectTool, self.comboid)
                
        # workaround for Mac bug. May be fixed by 2.8.8, but not before then.
        self.combo.Hide()
        self.combo.Show()

        # realize the toolbar
        self.Realize()


    def _toolbarData(self):

        icons = {
                 'run' : MetaIcon(img = 'execute',
                                  label = _('Execute analysis')),
                 'saveTempLayer'   : MetaIcon(img = 'map-export',
                                             label = _('Add temporary result of analasis into layer tree')),
                  'settings'  : BaseIcons['settings'].SetLabel( _('Vector network analasis settings'))
                }

        return self._getToolbarData((
                                     ("run", icons['run'],
                                      self.parent.OnAnalyze),
                                     ("saveTempLayer", icons['saveTempLayer'],
                                      self.parent.OnSaveTmpLayer),
                                     ('settings', icons["settings"],
                                      self.parent.OnSettings),                                    
                                     ("quit", BaseIcons['quit'],
                                      self.parent.OnCloseDialog)
                                    ))
