"""!
@package mapwindow.py

@brief buffered window, map display for DataCatalog.
orginal code from wxGUI module mapdisp_window.py.
Modified for map display in DataCatalog.

Classes:
 - BufferedWindow

(C) 2006-2009 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton (original author)
@author Jachym Cepicky (original author)
@author Martin Landa <landa.martin gmail.com> (original author)
@author Mohammed Rashad K.M (modified for DataCatalog)
"""

import os
import time
import math
import sys
import tempfile
import wx
import globalvar
import gselect
from debug import Debug



    
class BufferedWindow(wx.Window):

    def __init__(self, parent, id,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE,Map=None):

		wx.Window.__init__(self, parent, id, pos, size, style)
		Debug.msg(4, "BufferedWindow.__init(): Map=%s" % Map)
		self.Map = Map
	    
		self.Bind(wx.EVT_PAINT,        self.OnPaint)
		self.buffer = wx.EmptyBitmap(max(1, self.Map.width), max(1, self.Map.height))
		self.mapfile = None
		self.img = ""

		self.imagedict = {}   
		self.select = {}
		self.pdc = wx.PseudoDC()




    def Draw(self, pdc, img=None, drawid=None, pdctype='image', coords=[0, 0, 0, 0]):

        if drawid == None:
            if pdctype == 'image' and img:
                drawid = self.imagedict[img]
            else:
                drawid = wx.NewId()
        
        if img and pdctype == 'image':
            self.select[self.imagedict[img]['id']] = False # ?

        pdc.BeginDrawing()
        Debug.msg (5, "BufferedWindow.Draw(): id=%s, pdctype=%s, coord=%s" % \
                       (drawid, pdctype, coords))

        # set PseudoDC id
        if drawid is not None:
            pdc.SetId(drawid)

        if pdctype == 'image': # draw selected image
            bitmap = wx.BitmapFromImage(img)
            w,h = bitmap.GetSize()
            pdc.DrawBitmap(bitmap, coords[0], coords[1], True) # draw the composite map
            pdc.SetIdBounds(drawid, wx.Rect(coords[0],coords[1], w, h))


        pdc.EndDrawing()
        self.Refresh()
        
        return drawid


    def OnPaint(self,event):
        #Debug.msg(4, "BufferedWindow.OnPaint(): redrawAll=%s" % self.redrawAll)
        dc = wx.BufferedPaintDC(self, self.buffer)
        dc.Clear()
        self.PrepareDC(dc)
        self.bufferLast = None
        self.pdc.DrawToDC(dc)
        self.bufferLast = dc.GetAsBitmap(wx.Rect(0, 0, self.Map.width, self.Map.height))
        pdcLast =  wx.PseudoDC()
        pdcLast.DrawBitmap(self.bufferLast, 0, 0, False)
        pdcLast.DrawToDC(dc)



    def GetImage(self):
        imgId = 99
        if self.Map.mapfile and os.path.isfile(self.Map.mapfile) and \
                os.path.getsize(self.Map.mapfile):
            img = wx.Image(self.Map.mapfile, wx.BITMAP_TYPE_ANY)
	    #print self.Map.mapfile
        else:
            img = None

        self.imagedict[img] = { 'id': imgId }

        return img

    def UpdateMap(self, render=True, renderVector=True):

		if self.img is None:
			render = True

		if render:
			# update display size
			self.Map.ChangeMapSize(self.GetClientSize())
			self.mapfile = self.Map.Render(force=True,  windres=False)
		else:
			self.mapfile = self.Map.Render(force=False)

		self.img = self.GetImage() # id=99
		self.pdc.Clear()
		self.pdc.RemoveAll()
        
		if not self.img:
			self.Draw(self.pdc, pdctype='clear')
		else:
			try:
				id = self.imagedict[self.img]['id']
			except:
				return False

			self.Draw(self.pdc, self.img, drawid=id)      
     
		return True


