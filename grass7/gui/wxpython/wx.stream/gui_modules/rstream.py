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

	# create the layout
        self._layout()

    def _layout(self): 

	# create the grid for gselect
        select = wx.GridBagSizer(20, 5)

        #----------------------------
        #---------Input maps---------

        # Ask user for digital elevation model
        text1 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Elevation map (required)") 
        select.Add(item = text1, flag = wx.LEFT, pos = (1,0), span = (1,2))

        # Add the box for choosing the map
        select1 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select1, pos = (2,0), span = (1,2))

        # binder
        select1.Bind(wx.EVT_TEXT, self.OnSelect)

        #----------------------------

        # Ask user for Flow accumulation
        text2 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT/OUTPUT : Flow accumulation (required)") 
        select.Add(item = text2, flag = wx.LEFT, pos = (3,0), span = (1,2))

        # Flow accum can be either existent or to be calculated
        # Check box
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        cb1 = wx.CheckBox(parent = self.panel, label='Create by MFD algorithm')
        hbox1.Add(item = cb1, flag = wx.LEFT, border=10)
        cb2 = wx.CheckBox(parent = self.panel, label='Create by SFD algorithm')
        hbox1.Add(item = cb2, flag = wx.LEFT, border=10)
        cb3 = wx.CheckBox(parent = self.panel, label='Custom (select existing map)')
        hbox1.Add(item = cb3, flag = wx.LEFT, border=10)

        select.Add(item = hbox1, pos = (4,0))
        
        # Check box binder

        # Box to insert name of new acc map (to be created)
        txtOne = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtOne, flag = wx.LEFT | wx.EXPAND , pos = (5,0), span = (1,2))

        # Add the box for choosing the map
        select2 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select2, pos = (6,0), span = (1,2))

        # binder
        select2.Bind(wx.EVT_TEXT, self.OnSelect)

        #----------------------------

        # Ask user for Mask
        text3 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Mask (optional)") 
        select.Add(item = text3, flag = wx.LEFT, pos = (7,0), span = (1,2))

        # Add the box for choosing the map
        select3 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select3, pos = (8,0), span = (1,2))

        # binder
        select3.Bind(wx.EVT_TEXT, self.OnSelect)

        #----------------------------

        # Ask user for threshold
        text4 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Threshold (required)") 
        select.Add(item = text4, flag = wx.LEFT, pos = (9,0), span = (1,2))

        # Box to insert threshold
        txtTwo = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtTwo, flag = wx.LEFT, pos = (10,0), span = (1,2))


        #----------------------------
        #---------Output maps---------


        # Flow direction map
        text5 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Flow direction map (required)") 
        select.Add(item = text5, flag = wx.LEFT | wx.EXPAND, pos = (11,0), span = (1,2))

        # Box to insert name of new flow dir map (to be created)
        txtThr = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtThr, flag = wx.LEFT | wx.EXPAND , pos = (12,0), span = (1,2))

        #----------------------------

        # Streams map
        text6 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Streams (required)") 
        select.Add(item = text6, flag = wx.LEFT | wx.EXPAND, pos = (13,0), span = (1,2))

        # Box to insert name of new streams map (to be created)
        txtFou = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFou, flag = wx.LEFT | wx.EXPAND , pos = (14,0), span = (1,2))

        #----------------------------

        # Network map
        text7 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Network (required)") 
        select.Add(item = text7, flag = wx.LEFT | wx.EXPAND, pos = (15,0), span = (1,2))

        # Box to insert name of new streams map (to be created)
        txtFiv = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFiv, flag = wx.LEFT | wx.EXPAND , pos = (16,0), span = (1,2))



        #----------------------------
 
        self.panel.SetSizer(select)

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


