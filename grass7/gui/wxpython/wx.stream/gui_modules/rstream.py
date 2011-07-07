"""!
@package rstream.py

@brief GUI for r.stream.* modules

See http://grass.osgeo.org/wiki/Wx.stream_GSoC_2011

Classes:
 - RStreamFrame

(C) 2011 by Margherita Di Leo, and the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Margherita Di Leo (GSoC student 2011)
"""

import os
import sys

sys.path.append(os.path.join(os.getenv('GISBASE'), 'etc', 'gui', 'wxpython', 'gui_modules'))

import wx
import wx.aui

from debug import Debug as Debug
from preferences import globalSettings as UserSettings

import grass.script as grass
import gselect
import gcmd
import dbm
import globalvar
import utils
import menuform


## #-------------Panels-------------

# First panel # Network extraction

class TabPanelOne(wx.Panel):
    def __init__(self, parent):

        wx.Panel.__init__(self, parent, id = wx.ID_ANY)
       
        self.parent = parent
        
        # define the panel for select maps
	self.panel = wx.Panel(self)

        # define gselect
        self.mapselect = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                                    type = 'rast', multiple = False)
        # binder of gselect
        self.mapselect.Bind(wx.EVT_TEXT, self.OnSelect)                                    

	# create the layout
        self._layout()

    def _layout(self): 

	# create the grid for gselect
        select = wx.GridBagSizer(8, 5)

        # Ask user for digital elevation model

        text1 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "Elevation") #FIXME text does not appear
        select.Add(item = text1, flag = wx.LEFT, pos = (1,0),span = (1,2))

        select.Add(item = self.mapselect, pos = (2,0),
                     span = (1,2))
                     
        self.SetSizer(select)

        btnPanel = wx.Panel(self)

        #-------------Buttons-------------

        self.createButtonBar(btnPanel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.panel, 1, wx.EXPAND)
        sizer.Add(btnPanel, 0, wx.EXPAND)
        self.SetSizer(sizer)

        
    def OnSelect(self, event):
            """!Gets raster map or function selection and send it to
            insertion method
            """
            item = event.GetString()
            self._addSomething(item)        

    def buttonData(self):
        return (("Update Preview", self.OnPreview),        
                ("Run Analysis", self.OnRun))

    def createButtonBar(self, panel, yPos = 0):
        xPos = 0
        for eachLabel, eachHandler in self.buttonData():
            pos = (xPos, yPos)
            button = self.buildOneButton(panel, eachLabel, eachHandler, pos)
            xPos += button.GetSize().width
    
    def buildOneButton(self, parent, label, handler, pos = (0,0)):
        button = wx.Button(parent, wx.ID_ANY, label, pos)
        self.Bind(wx.EVT_BUTTON, handler, button)
        return button
    
    def OnPreview(self, event):
        pass
    
    def OnRun(self, event):
        pass




# Child panel class before customization 

class TabPanel(wx.Panel):

    def __init__(self, parent):

        wx.Panel.__init__(self, parent = parent, id = wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)
        txtOne = wx.TextCtrl(self, wx.ID_ANY, "")
        txtTwo = wx.TextCtrl(self, wx.ID_ANY, "")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(txtOne, 0, wx.ALL, 5)
        sizer.Add(txtTwo, 0, wx.ALL, 5)

        self.SetSizer(sizer)


## #-------------Main Frame-------------
class RStreamFrame(wx.Frame):
    def __init__(self, parent = None, id = wx.ID_ANY,
                 title = _("GRASS GIS Hydrological Modelling Utility"), **kwargs):
        """!Main window of r.stream's GUI
        
        @param parent parent window
        @param id window id
        @param title window title
        
        @param kwargs wx.Frames' arguments
        """
        self.parent = parent
        
        wx.Frame.__init__(self, parent = parent, id = id, title = title, name = "RStream", **kwargs)
        self.SetIcon(wx.Icon(os.path.join(globalvar.ETCICONDIR, 'grass.ico'), wx.BITMAP_TYPE_ICO))
        
        #panel = ParentPanel(self)
        # create the AuiNotebook instance
        nb = wx.aui.AuiNotebook(self)

        # add some pages to the notebook
        pages = [(TabPanelOne(nb), "Network extraction"),
                 (TabPanel(nb), "Tab 2"),
                 (TabPanel(nb), "Tab 3")]

        for page, label in pages:
            nb.AddPage(page, label)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(nb, 1, wx.EXPAND)

        # button for close and other
        button = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_close = wx.Button(parent = self, id = wx.ID_CLOSE)
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
        button.Add(item=self.btn_close,flag = wx.ALL, border = 5)        
        sizer.Add(button)
        
        self.SetSizer(sizer)

    def OnClose(self, event): 
        self.Destroy()        
        self.Show()





def main():
    app = wx.PySimpleApp()
    wx.InitAllImageHandlers()
    frame = RStreamFrame()
    frame.Show()
    
    app.MainLoop()

if __name__ == "__main__":
    main()


