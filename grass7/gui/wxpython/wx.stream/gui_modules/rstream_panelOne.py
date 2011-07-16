#!/usr/bin/python
# -*- coding: utf-8 -*-

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

import wx
import gselect



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
        select.Add(item = text1, flag = wx.LEFT, pos = (1,0), span = wx.DefaultSpan, border = 0)

        # Add the box for choosing the map 
        select1 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select1, pos = (2,0), span = wx.DefaultSpan)

        # binder
        select1.Bind(wx.EVT_TEXT, self.OnSelectElev)

        #----------------------------

        # Ask user for Flow accumulation
        text2 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT/OUTPUT : Flow accumulation (required)") 
        select.Add(item = text2, flag = wx.LEFT, pos = (3,0), span = wx.DefaultSpan)
        

        # Flow accum can be either existent or to be calculated
        # RadioButton
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        cb1 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Custom (select existing map)")
        hbox1.Add(item = cb1, flag = wx.LEFT)
        cb2 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by MFD algorithm")
        hbox1.Add(item = cb2, flag = wx.LEFT)
        cb3 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by SFD algorithm")
        hbox1.Add(item = cb3, flag = wx.LEFT)

        select.Add(item = hbox1, pos = (4,0))

        # Box to insert name of acc map 

        global select2, textOne, textTwo

        select2 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False) # select existing map
        select.Add(item = select2, pos = (5,0), span = wx.DefaultSpan)
        textOne = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT) # MFD
        select.Add(item = textOne, flag = wx.LEFT | wx.EXPAND , pos = (6,0), span = wx.DefaultSpan)
        textTwo = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT) # SFD
        select.Add(item = textTwo, flag = wx.LEFT | wx.EXPAND , pos = (7,0), span = wx.DefaultSpan)


        # linking buttons and text
        self.texts = {"Custom (select existing map)" : select2,
                      "Create by MFD algorithm" : textOne,
                      "Create by SFD algorithm" : textTwo}

        self.selectedText = select2 # default is select existing map

        # Disable 
        textOne.Enable(False)
        textTwo.Enable(False)


        # RadioButton binders
        cb1.Bind(wx.EVT_RADIOBUTTON, self.OnSelectExistAcc)
        cb2.Bind(wx.EVT_RADIOBUTTON, self.OnSelectMFDAcc)
        cb3.Bind(wx.EVT_RADIOBUTTON, self.OnSelectSFDAcc)

        #textOne.Bind(wx.EVT_TEXT, self.OnSelectMFDAcc)
        #textTwo.Bind(wx.EVT_TEXT, self.OnSelectSFDAcc)
        #select2.Bind(wx.EVT_TEXT, self.OnSelectExistAcc)

        #----------------------------

        # Ask user for Mask
        text3 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Mask (optional)") 
        select.Add(item = text3, flag = wx.LEFT, pos = (8,0), span = wx.DefaultSpan)

        # Add the box for choosing the map
        select3 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select3, pos = (9,0), span = wx.DefaultSpan)

        # binder
        select3.Bind(wx.EVT_TEXT, self.OnSelectMask)

        #----------------------------

        # Ask user for threshold
        text4 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Threshold (required)") 
        select.Add(item = text4, flag = wx.LEFT, pos = (10,0), span = wx.DefaultSpan)

        # Box to insert threshold
        txtTwo = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtTwo, flag = wx.LEFT, pos = (11,0), span = wx.DefaultSpan)

        # binder
        txtTwo.Bind(wx.EVT_TEXT, self.OnSelecTh)


        #----------------------------
        #---------Output maps---------


        # Flow direction map
        text5 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Flow direction map (required)") 
        select.Add(item = text5, flag = wx.LEFT | wx.EXPAND, pos = (12,0), span = wx.DefaultSpan)

        # Box to insert name of new flow dir map (to be created)
        txtThr = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtThr, flag = wx.LEFT | wx.EXPAND , pos = (13,0), span = wx.DefaultSpan)

        # binder
        txtThr.Bind(wx.EVT_TEXT, self.OnSelecFd)


        #----------------------------

        # Streams map
        text6 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Streams (required)") 
        select.Add(item = text6, flag = wx.LEFT | wx.EXPAND, pos = (14,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        txtFou = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFou, flag = wx.LEFT | wx.EXPAND , pos = (15,0), span = wx.DefaultSpan)

        # binder
        txtFou.Bind(wx.EVT_TEXT, self.OnSelecStr)

        #----------------------------

        # Network map
        text7 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Network (required)") 
        select.Add(item = text7, flag = wx.LEFT | wx.EXPAND, pos = (16,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        txtFiv = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFiv, flag = wx.LEFT | wx.EXPAND , pos = (17,0), span = wx.DefaultSpan)

        # binder
        txtFiv.Bind(wx.EVT_TEXT, self.OnSelecNet)


        #----------------------------
 
        self.panel.SetSizer(select)

        btnPanel = wx.Panel(self)

        #-------------Buttons-------------

        self.createButtonBar(btnPanel)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.panel, 1, wx.EXPAND)
        sizer.Add(btnPanel, 0, wx.EXPAND)
        self.SetSizer(sizer)
    
        
    #-------------input maps-------------

    def OnSelectElev(self, event):
        """!Gets elevation map and assign it to var
        """
        r_elev = event.GetString()
        
        #import pdb; pdb.set_trace()

    def OnSelectMFDAcc(self, event):
        """!Gets new flow accum map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        r_new_acc = textOne.GetString[radioSelected.GetLabel()] #FIXME event 
        r_new_acc.Enable(True)
        self.SelectedText = r_new_acc

        #select2.Bind(wx.EVT_TEXT, self.OnSelectExistAcc
        #r_new_acc = event.GetString()
        # r.watershed elevation = r_elev accumulation = r_new_acc -a (MFD)

    def OnSelectSFDAcc(self, event):
        """!Gets new flow accum map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        r_new_acc = textTwo.GetString[radioSelected.GetLabel()] #FIXME
        r_new_acc.Enable(True)
        self.SelectedText = r_new_acc

        #r_new_acc = event.GetString()
        # r.watershed elevation = r_elev accumulation = r_new_acc -a (SFD, flag = -s)

    def OnSelectExistAcc(self, event):
        """!Gets existing flow acc map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        r_ex_acc = select2.GetString[radioSelected.GetLabel()] #FIXME
        r_ex_acc.Enable(True)
        self.SelectedText = r_ex_acc

        #r_ex_acc = event.GetString()

    def OnSelectMask(self, event):
        """!Gets mask map and assign it to var
        """
        r_mask = event.GetString()

    def OnSelecTh(self, event):
        """!Gets threshold and assign it to var
        """
        thre = event.GetString()


    #-------------output maps-------------

    def OnSelecFd(self, event):
        """!Gets flow direction map and assign it to var
        """
        r_drain = event.GetString()

    def OnSelecStr(self, event):
        """!Gets stream map and assign it to var
        """
        r_stre = event.GetString()

    def OnSelecNet(self, event):
        """!Gets network map and assign it to var
        """
        v_net = event.GetString()


      

    #-------------Buttons-------------

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
    

    #-------------Preview funct-------------

    def OnPreview(self, event):
        pass
    

    #-------------Get the network extraction-------------
    
    def OnRun(self, event):
        pass




