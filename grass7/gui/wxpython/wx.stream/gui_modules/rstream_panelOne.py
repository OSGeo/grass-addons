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

from rstream_panelOne import *


# First panel # Network extraction

class TabPanelOne(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id = wx.ID_ANY)
       
        self.parent = parent
        self.thre = 0
        self.r_elev = 'r_elev'
        self.r_acc = 'r_acc'
        self.r_stre = 'r_stre'
        self.v_net = 'v_net'
        self.r_drain = 'r_drain'
        
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

        cb1 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Custom (select existing map)", style = wx.RB_GROUP)
        hbox1.Add(item = cb1, flag = wx.LEFT)
        cb2 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by MFD algorithm")
        hbox1.Add(item = cb2, flag = wx.LEFT)
        cb3 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by SFD algorithm")
        hbox1.Add(item = cb3, flag = wx.LEFT)

        select.Add(item = hbox1, pos = (4,0))

        # Box to insert name of acc map 

        global select2, textOne

        select2 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False) # select existing map
        select.Add(item = select2, pos = (5,0), span = wx.DefaultSpan)
        textOne = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT) 
        select.Add(item = textOne, flag = wx.LEFT | wx.EXPAND , pos = (6,0), span = wx.DefaultSpan)


        # linking buttons and text
        self.texts = {"Custom (select existing map)" : select2,
                      "Create by MFD algorithm" : textOne,
                      "Create by SFD algorithm" : textOne}


        self.selectedText = select2 # default is select existing map

        # Disable 
        textOne.Enable(False)

        # RadioButton binders
        cb1.Bind(wx.EVT_RADIOBUTTON, self.OnSelectExistAcc)
        cb2.Bind(wx.EVT_RADIOBUTTON, self.OnSelectMFDAcc)
        cb3.Bind(wx.EVT_RADIOBUTTON, self.OnSelectSFDAcc)

        #----------------------------

        # Ask user for Mask
        text3 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Mask (optional)") 
        select.Add(item = text3, flag = wx.LEFT, pos = (7,0), span = wx.DefaultSpan)

        # Add the box for choosing the map
        select3 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        select.Add(item = select3, pos = (8,0), span = wx.DefaultSpan)

        # binder
        select3.Bind(wx.EVT_TEXT, self.OnSelectMask)

        #----------------------------

        # Ask user for threshold
        text4 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Threshold (required)") 
        select.Add(item = text4, flag = wx.LEFT, pos = (9,0), span = wx.DefaultSpan)

        # Box to insert threshold
        txtTwo = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtTwo, flag = wx.LEFT, pos = (10,0), span = wx.DefaultSpan)

        # binder
        txtTwo.Bind(wx.EVT_TEXT, self.OnSelecTh)


        #----------------------------
        #---------Output maps---------


        # Flow direction map
        text5 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Flow direction map (required)") 
        select.Add(item = text5, flag = wx.LEFT | wx.EXPAND, pos = (11,0), span = wx.DefaultSpan)

        # Box to insert name of new flow dir map (to be created)
        txtThr = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtThr, flag = wx.LEFT | wx.EXPAND , pos = (12,0), span = wx.DefaultSpan)

        # binder
        txtThr.Bind(wx.EVT_TEXT, self.OnSelecFd)


        #----------------------------

        # Streams map
        text6 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Streams (required)") 
        select.Add(item = text6, flag = wx.LEFT | wx.EXPAND, pos = (13,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        txtFou = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFou, flag = wx.LEFT | wx.EXPAND , pos = (14,0), span = wx.DefaultSpan)

        # binder
        txtFou.Bind(wx.EVT_TEXT, self.OnSelecStr)

        #----------------------------

        # Network map
        text7 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Network (required)") 
        select.Add(item = text7, flag = wx.LEFT | wx.EXPAND, pos = (15,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        txtFiv = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        select.Add(item = txtFiv, flag = wx.LEFT | wx.EXPAND , pos = (16,0), span = wx.DefaultSpan)

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
        self.r_elev = event.GetString()

    def OnSelectMFDAcc(self, event):
        """!Gets new flow accum map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.r_acc = self.texts[radioSelected.GetLabel()]
        self.r_acc.Enable(True)
        self.SelectedText = self.r_acc

        #select2.Bind(wx.EVT_TEXT, self.OnSelectExistAcc
        #r_acc = event.GetString()
        # r.watershed elevation = r_elev accumulation = r_acc -a (MFD)

        gcmd.RunCommand('r.watershed', elevation = 'r_elev' , accumulation = 'r_acc' , drainage = 'r_new_dir' , convergence = 5 , flags = 'a')

    def OnSelectSFDAcc(self, event):
        """!Gets new flow accum map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.r_acc = self.texts[radioSelected.GetLabel()]
        self.r_acc.Enable(True)
        self.SelectedText = self.r_acc

        #r_acc = event.GetString()
        # r.watershed elevation = r_elev accumulation = r_acc -a (SFD, flag = -s)

        gcmd.RunCommand('r.watershed', elevation = 'r_elev' , accumulation = 'r_acc' , drainage = 'r_new_dir' , convergence = 5 , flags = 'sa')

    def OnSelectExistAcc(self, event):
        """!Gets existing flow acc map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.r_acc = self.texts[radioSelected.GetLabel()]
        self.r_acc.Enable(True)
        self.SelectedText = self.r_acc

    def OnSelectMask(self, event):
        """!Gets mask map and assign it to var
        """
        self.r_mask = event.GetString()

    def OnSelecTh(self, event):
        """!Gets threshold and assign it to var
        """
        self.thre = event.GetString()


    #-------------output maps-------------

    def OnSelecFd(self, event):
        """!Gets flow direction map and assign it to var
        """
        self.r_drain = event.GetString()

    def OnSelecStr(self, event):
        """!Gets stream map and assign it to var
        """
        self.r_stre = event.GetString()

    def OnSelecNet(self, event):
        """!Gets network map and assign it to var
        """
        self.v_net = event.GetString()
    

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
    

    #-------------Network extraction-------------
    
    def OnRun(self, event):
        
        print self.r_elev
        print self.r_acc
        print self.thre
        print self.r_stre
        print self.v_net
        print self.r_drain

        gcmd.RunCommand('r.stream.extract', elevation = self.r_elev , accumulation = self.r_acc , threshold = self.thre, 
                        stream_rast = self.r_stre, stream_vect = self.v_net, direction = self.r_drain)




