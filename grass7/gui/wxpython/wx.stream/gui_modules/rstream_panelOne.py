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
import wx.lib.flatnotebook as FN

from debug import Debug as Debug
from preferences import globalSettings as UserSettings

import grass.script as grass
import gselect
import gcmd
import dbm
import globalvar
import utils
import menuform




# First panel # Network extraction

class TabPanelOne(wx.Panel):

    def __init__(self, parent, layerManager, MapFrame):
        wx.Panel.__init__(self, parent, id = wx.ID_ANY)
        
        self.layerManager = layerManager
        self.mapdisp = MapFrame
        self.parent = parent
        self.thre = 0
        self.r_elev = 'r_elev'
        self.r_acc = 'r_acc'
        self.r_stre = 'r_stre'
        self.v_net = 'v_net'
        self.r_drain = 'r_drain'
        
        self.panel = wx.Panel(self)                        
        self._layout()
       
        

    def _layout(self): 

        self.select = wx.GridBagSizer(20, 5)

        #----------------------------
        #---------Input maps---------

        # Ask user for digital elevation model
        self.text1 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Elevation map (required)") 
        self.select.Add(item = self.text1, flag = wx.LEFT, pos = (1,0), span = wx.DefaultSpan, border = 0)

        # Add the box for choosing the map 
        self.select1 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        self.select.Add(item = self.select1, pos = (2,0), span = wx.DefaultSpan)

        # binder
        self.select1.Bind(wx.EVT_TEXT, self.OnSelectElev)

        #----------------------------

        # Ask user for Flow accumulation
        self.text2 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT/OUTPUT : Flow accumulation (required)") 
        self.select.Add(item = self.text2, flag = wx.LEFT, pos = (3,0), span = wx.DefaultSpan)
        

        # Flow accum can be either existent or to be calculated
        # RadioButton
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)

        self.cb1 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Custom (select existing map)", style = wx.RB_GROUP)
        self.hbox1.Add(item = self.cb1, flag = wx.LEFT)
        self.cb2 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by MFD algorithm")
        self.hbox1.Add(item = self.cb2, flag = wx.LEFT)
        self.cb3 = wx.RadioButton(parent = self.panel, id = wx.ID_ANY, label = "Create by SFD algorithm")
        self.hbox1.Add(item = self.cb3, flag = wx.LEFT)

        self.select.Add(item = self.hbox1, pos = (4,0))

        # Box to insert name of acc map 
        self.select2 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False) # select existing map
        self.select.Add(item = self.select2, pos = (5,0), span = wx.DefaultSpan)
        self.textOne = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT) 
        self.select.Add(item = self.textOne, flag = wx.LEFT | wx.EXPAND , pos = (6,0), span = wx.DefaultSpan)


        # linking buttons and text
        self.texts = {"Custom (select existing map)" : self.select2,
                      "Create by MFD algorithm" : self.textOne,
                      "Create by SFD algorithm" : self.textOne}


        self.selectedText = self.select2 # default is select existing map

        # Disable 
        self.textOne.Enable(False)

        # RadioButton binders
        self.cb1.Bind(wx.EVT_RADIOBUTTON, self.OnSelectExistAcc)
        self.cb2.Bind(wx.EVT_RADIOBUTTON, self.OnSelectMFDAcc)
        self.cb3.Bind(wx.EVT_RADIOBUTTON, self.OnSelectSFDAcc)

        #----------------------------

        # Ask user for Mask
        self.text3 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Mask (optional)") 
        self.select.Add(item = self.text3, flag = wx.LEFT, pos = (7,0), span = wx.DefaultSpan)

        # Add the box for choosing the map
        self.select3 = gselect.Select(parent = self.panel, id = wx.ID_ANY, size = (250, -1),
                               type = 'rast', multiple = False)
        self.select.Add(item = self.select3, pos = (8,0), span = wx.DefaultSpan)

        # binder
        self.select3.Bind(wx.EVT_TEXT, self.OnSelectMask)

        #----------------------------

        # Ask user for threshold
        self.text4 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "INPUT : Threshold (required)") 
        self.select.Add(item = self.text4, flag = wx.LEFT, pos = (9,0), span = wx.DefaultSpan)

        # Box to insert threshold
        self.txtTwo = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        self.select.Add(item = self.txtTwo, flag = wx.LEFT, pos = (10,0), span = wx.DefaultSpan)

        # binder
        self.txtTwo.Bind(wx.EVT_TEXT, self.OnSelecTh)


        #----------------------------
        #---------Output maps---------


        # Flow direction map
        self.text5 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Flow direction map (required)") 
        self.select.Add(item = self.text5, flag = wx.LEFT | wx.EXPAND, pos = (11,0), span = wx.DefaultSpan)

        # Box to insert name of new flow dir map (to be created)
        self.txtThr = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        self.select.Add(item = self.txtThr, flag = wx.LEFT | wx.EXPAND , pos = (12,0), span = wx.DefaultSpan)

        # binder
        self.txtThr.Bind(wx.EVT_TEXT, self.OnSelecFd)


        #----------------------------

        # Streams map
        self.text6 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Streams (required)") 
        self.select.Add(item = self.text6, flag = wx.LEFT | wx.EXPAND, pos = (13,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        self.txtFou = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        self.select.Add(item = self.txtFou, flag = wx.LEFT | wx.EXPAND , pos = (14,0), span = wx.DefaultSpan)

        # binder
        self.txtFou.Bind(wx.EVT_TEXT, self.OnSelecStr)

        #----------------------------

        # Network map
        self.text7 = wx.StaticText(parent = self.panel, id = wx.ID_ANY, label = "OUTPUT : Network (required)") 
        self.select.Add(item = self.text7, flag = wx.LEFT | wx.EXPAND, pos = (15,0), span = wx.DefaultSpan)

        # Box to insert name of new streams map (to be created)
        self.txtFiv = wx.TextCtrl(parent = self.panel, id = wx.ID_ANY, style = wx.TE_LEFT)
        self.select.Add(item = self.txtFiv, flag = wx.LEFT | wx.EXPAND , pos = (16,0), span = wx.DefaultSpan)

        # binder
        self.txtFiv.Bind(wx.EVT_TEXT, self.OnSelecNet)


        #----------------------------
 
        self.panel.SetSizer(self.select)
        self.btnPanel = wx.Panel(self)

        #-------------Buttons-------------

        self.createButtonBar(self.btnPanel)       
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.Add(self.panel, 1, wx.EXPAND)
        self.sizer.Add(self.btnPanel, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
    
        
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
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

        print self.r_acc

    def OnSelectSFDAcc(self, event):
        """!Gets new flow accum map and assign it to var
        """
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

    def OnSelectExistAcc(self, event):
        """!Gets existing flow acc map and assign it to var
        """
        self.textOne.Enable(False)
        if self.selectedText:
            self.selectedText.Enable(False)
        radioSelected = event.GetEventObject()
        self.acc = self.texts[radioSelected.GetLabel()]
        self.acc.Enable(True)
        self.SelectedText = self.acc
        self.r_acc = self.acc.GetValue()

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
        """!Allows to watch a preview of the analysis on a small region
        """
        info_region = grass.read_command('g.region', flags = 'p')

        # message box 
        self.msg = wx.MessageDialog(parent = self.panel, 
                                    message = "Please select the center of preview window on the map",
                                    caption = "Preview utility", 
                                    style = wx.OK | wx.CANCEL, 
                                    pos = wx.DefaultPosition)
        self.retCode = self.msg.ShowModal()
        if self.retCode == wx.ID_OK:
            print "OK"

            # get current Map Display
            self.mapdisp = self.layerManager.GetLayerTree().GetMapDisplay()
            self.mapdisp.Raise()
            self.mapdisp.Map.AddLayer(type = 'raster', 
                                 command = ['d.rast', 'map=%s' % self.r_elev])
            self.mapdisp.OnRender(None)
            
            

            # Get position by panel on mouse click
            


        else:
            print "Cancel"
        
        
        
    

    #-------------Network extraction-------------
    
    def OnRun(self, event):

        # radioval1 = self.cb1.GetValue()
        radioval2 = self.cb2.GetValue()
        radioval3 = self.cb3.GetValue()
        
        # MFD
        if radioval2 == 'True':
            grass.message('Creating flow accumulation map with MFD algorithm..')
            grass.run_command('r.watershed', elevation = self.r_elev , 
                              accumulation = self.r_acc , 
                              convergence = 5 , 
                              flags = 'a', overwrite = True )

        # SFD
        if radioval3 == 'True':
            grass.message('Creating flow accumulation map with SFD algorithm..')
            grass.run_command('r.watershed', elevation = self.r_elev , 
                              accumulation = self.r_acc , 
                              drainage = self.r_drain , 
                              convergence = 5 , 
                              flags = 'sa', overwrite = True)

        grass.message('Network extraction..')
        grass.run_command('r.stream.extract', elevation = self.r_elev , 
                          accumulation = self.r_acc , 
                          threshold = self.thre, 
                          stream_rast = self.r_stre, 
                          stream_vect = self.v_net, 
                          direction = self.r_drain, overwrite = True)

        
        # Debug
        print self.r_elev
        print self.r_acc
        print self.thre
        print self.r_stre
        print self.v_net
        print self.r_drain

