import os
import sys
import wx
import glob
import render
from threading import Thread
from debug import Debug as Debug
from icon import Icons as Icons
import gui_modules.menuform as menuform
import gdialogs
from preferences import globalSettings as UserSettings
from vdigit import haveVDigit
grassversion = os.getenv("GRASS_VERSION")
if grassversion.rfind("6.4") != 0:
    from gcmd import GMessage
import histogram
import gui_modules.profile as profile


import wx.lib.customtreectrl as CT
try:
    import treemixin 
except ImportError:
    from wx.lib.mixins import treemixin

import wx.combo
import wx.lib.newevent
import wx.lib.buttons  as  buttons

#To run DataCatalog from any directory set this pathname for access to gui_modules 
gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','wxpython','gui_modules')
sys.path.append(pypath)


import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import gcmd

import utils
from grass.script import core as grass
if grassversion.rfind("6.4") != 0:
    from gui_modules.layertree import LayerTree as layertree
else:
    from gui_modules.wxgui_utils import LayerTree as layertree

class LayerTree(layertree):



    def __init__(self, parent,
                 id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=(300,300), style=wx.SUNKEN_BORDER,
                 ctstyle=CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                 CT.TR_HIDE_ROOT | CT.TR_FULL_ROW_HIGHLIGHT |
                 CT.TR_MULTIPLE,**kwargs):

        if 'style' in kwargs:
            ctstyle |= kwargs['style']
            del kwargs['style']

        self.frame = kwargs['frame']
        del kwargs['frame']

        self.Map = kwargs['Map']
        del kwargs['Map']

        self.lmgr = kwargs['lmgr']

        self.gisdbase = kwargs['gisdbase']
        del kwargs['gisdbase']

        if globalvar.hasAgw:
            CT.CustomTreeCtrl.__init__(self,parent, id, agwStyle = ctstyle)
        else:
            CT.CustomTreeCtrl.__init__(self,parent,id,style=ctstyle)
        self.SetName("LayerTree")



        self.layer_selected = None 

        self.rerender = False                # layer change requires a rerendering if auto render
        self.reorder = False 

        il = wx.ImageList(16, 16, mask=False)

        trart = wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, (16, 16))
        self.folder_open = il.Add(trart)
        trart = wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16, 16))
        self.folder = il.Add(trart)

        bmpsize = (16, 16)
        trgif = Icons["addrast"].GetBitmap(bmpsize)
        self.rast_icon = il.Add(trgif)

        trgif = Icons["addrast3d"].GetBitmap(bmpsize)
        self.rast3d_icon = il.Add(trgif)

        trgif = Icons["addrgb"].GetBitmap(bmpsize)
        self.rgb_icon = il.Add(trgif)

        trgif = Icons["addhis"].GetBitmap(bmpsize)
        self.his_icon = il.Add(trgif)

        trgif = Icons["addshaded"].GetBitmap(bmpsize)
        self.shaded_icon = il.Add(trgif)

        trgif = Icons["addrarrow"].GetBitmap(bmpsize)
        self.rarrow_icon = il.Add(trgif)

        trgif = Icons["addrnum"].GetBitmap(bmpsize)
        self.rnum_icon = il.Add(trgif)

        trgif = Icons["addvect"].GetBitmap(bmpsize)
        self.vect_icon = il.Add(trgif)

        trgif = Icons["addthematic"].GetBitmap(bmpsize)
        self.theme_icon = il.Add(trgif)

        trgif = Icons["addchart"].GetBitmap(bmpsize)
        self.chart_icon = il.Add(trgif)

        trgif = Icons["addgrid"].GetBitmap(bmpsize)
        self.grid_icon = il.Add(trgif)

        trgif = Icons["addgeodesic"].GetBitmap(bmpsize)
        self.geodesic_icon = il.Add(trgif)

        trgif = Icons["addrhumb"].GetBitmap(bmpsize)
        self.rhumb_icon = il.Add(trgif)

        trgif = Icons["addlabels"].GetBitmap(bmpsize)
        self.labels_icon = il.Add(trgif)

        trgif = Icons["addcmd"].GetBitmap(bmpsize)
        self.cmd_icon = il.Add(trgif)

        self.AssignImageList(il) 





        self.ID_COPY = wx.NewId()
        self.ID_OSSIM = wx.NewId()
        self.ID_OSSIM2 = wx.NewId()
        self.ID_INFO = wx.NewId()
        self.ID_REPORT = wx.NewId()
        self.ID_AREA = 200
        self.ID_LENGTH = 201
        self.ID_COOR = 202
        self.ID_REN = wx.NewId()
        self.ID_DEL = wx.NewId()

        self.root = self.AddRoot("Map Layers")
        self.SetPyData(self.root, (None,None))




        d = self.GetParent()
        notebook = d.GetParent()


        child=notebook.GetChildren()
        for panel in child:
	          if panel.GetName() == "MapWindow":
		        self.mapdisplay = panel


        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnLayerChecked)
        # self.Bind(CT.EVT_TREE_ITEM_ACTIVATED,     self.ChooseColour)

        #self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,self.OnTreePopUp)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndRename)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginRename)

        #Event bindings for tree menu
        self.Bind(wx.EVT_MENU,self.OnCopy,id=self.ID_COPY)
        self.Bind(wx.EVT_MENU,self.OnRenameMap,id=self.ID_REN)
        self.Bind(wx.EVT_MENU,self.OnDeleteMap,id=self.ID_DEL)
        self.Bind(wx.EVT_MENU,self.OnOssim,id=self.ID_OSSIM)
        self.Bind(wx.EVT_MENU,self.OnOssim2,id=self.ID_OSSIM2)



        self.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.OnExpandNode)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnCollapseNode)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivateLayer)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnChangeSel)
        self.Bind(wx.EVT_TREE_DELETE_ITEM, self.OnDeleteMap)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnLayerContextMenu)
        self.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.addon = os.getenv("integrated-gui")

  
   


    def Minimal(self,item):
        print "here"
        mnuCopy = self.popupMenu.Append(self.ID_COPY,'&Copy Map\tCtrl+C')
        mnuRename = self.popupMenu.Append(self.ID_REN,'&Rename Map\tCtrl-R')
        mnuDel = self.popupMenu.Append(self.ID_DEL,'&Delete Map\tDEL')
        self.popupMenu.AppendSeparator()
        mnuOssim = self.popupMenu.Append(self.ID_OSSIM,'&Send to OssimPlanet')
        mnuOssim = self.popupMenu.Append(self.ID_OSSIM2,'&Remove from OssimPlanet')



    def OnLayerContextMenu (self, event):
        """!Contextual menu for item/layer"""
        if not self.layer_selected:
            event.Skip()
            return

        self.popupMenu = wx.Menu()
        item =  event.GetItem()
        if self.IsItemChecked(item) == False:

            if self.addon == "True":
                self.Minimal(item)
        else:

            if self.addon == "True":
                self.Minimal(item)
            ltype =  self.GetPyData(self.layer_selected)[0]['type']

            Debug.msg (4, "LayerTree.OnContextMenu: layertype=%s" % \
						   ltype)

            if not hasattr (self, "popupID1"):
                self.popupID1 = wx.NewId()
                self.popupID2 = wx.NewId()
                self.popupID3 = wx.NewId()
                self.popupID4 = wx.NewId()
                self.popupID5 = wx.NewId()
                self.popupID6 = wx.NewId()
                self.popupID7 = wx.NewId()
                self.popupID8 = wx.NewId()
                self.popupID9 = wx.NewId()
                self.popupID10 = wx.NewId()
                self.popupID11 = wx.NewId() # nviz
                self.popupID12 = wx.NewId()
                self.popupID13 = wx.NewId()
                self.popupID14 = wx.NewId()
                self.popupID15 = wx.NewId()

            numSelected = len(self.GetSelections()) 

			# general item
            self.popupMenu.Append(self.popupID1, text=_("Remove from MapTree"))
            self.Bind(wx.EVT_MENU, self.lmgr.OnDeleteLayer, id=self.popupID1)

            if ltype != "command": # rename
                self.popupMenu.Append(self.popupID2, text=_("Rename"))
                self.Bind(wx.EVT_MENU, self.RenameLayer, id=self.popupID2)
                if numSelected > 1:
                    self.popupMenu.Enable(self.popupID2, False)

			# map layer items
            if ltype != "group" and \
					ltype != "command":
                self.popupMenu.AppendSeparator()
                self.popupMenu.Append(self.popupID8, text=_("Change opacity level"))
                self.Bind(wx.EVT_MENU, self.OnPopupOpacityLevel, id=self.popupID8)
                self.popupMenu.Append(self.popupID3, text=_("Properties"))
                self.Bind(wx.EVT_MENU, self.OnPopupProperties, id=self.popupID3)

                if ltype in ('raster', 'vector', 'raster3d') and self.mapdisplay.toolbars['nviz']:
                    self.popupMenu.Append(self.popupID11, _("3D view properties"))
                    self.Bind (wx.EVT_MENU, self.OnNvizProperties, id=self.popupID11)

                if ltype in ('raster', 'vector', 'rgb'):
                    self.popupMenu.Append(self.popupID9, text=_("Zoom to selected map(s)"))
                    self.Bind(wx.EVT_MENU, self.mapdisplay.OnZoomToMap, id=self.popupID9)
                    self.popupMenu.Append(self.popupID10, text=_("Set computational region from selected map(s)"))
                    self.Bind(wx.EVT_MENU, self.OnSetCompRegFromMap, id=self.popupID10)
                if numSelected > 1:
                    self.popupMenu.Enable(self.popupID8, False)
                    self.popupMenu.Enable(self.popupID3, False)
	
			# specific items
            try:
				mltype =  self.GetPyData(self.layer_selected)[0]['type']
            except:
                mltype = None
			#
			# vector layers (specific items)
			#
            if mltype and mltype == "vector":
                self.popupMenu.AppendSeparator()
                self.popupMenu.Append(self.popupID4, text=_("Show attribute data"))
                self.Bind (wx.EVT_MENU, self.lmgr.OnShowAttributeTable, id=self.popupID4)
                self.popupMenu.Append(self.popupID5, text=_("Start editing"))
                self.popupMenu.Append(self.popupID6, text=_("Stop editing"))
                self.popupMenu.Enable(self.popupID6, False)
                self.Bind (wx.EVT_MENU, self.OnStartEditing, id=self.popupID5)
                self.Bind (wx.EVT_MENU, self.OnStopEditing, id=self.popupID6)

                layer = self.GetPyData(self.layer_selected)[0]['maplayer']
                # enable editing only for vector map layers available in the current mapset
                digitToolbar = self.mapdisplay.toolbars['vdigit']
                if digitToolbar:
					# background vector map
                    self.popupMenu.Append(self.popupID14,
							              text=_("Use as background vector map"),
							              kind=wx.ITEM_CHECK)
                    self.Bind(wx.EVT_MENU, self.OnSetBgMap, id=self.popupID14)
                    if UserSettings.Get(group='vdigit', key='bgmap', subkey='value',
							            internal=True) == layer.GetName():
                        self.popupMenu.Check(self.popupID14, True)
                if layer.GetMapset() != grass.gisenv()['MAPSET']:
					# only vector map in current mapset can be edited
					self.popupMenu.Enable (self.popupID5, False)
					self.popupMenu.Enable (self.popupID6, False)
                elif digitToolbar and digitToolbar.GetLayer():
					# vector map already edited
					vdigitLayer = digitToolbar.GetLayer()
					if vdigitLayer is layer:
						# disable 'start editing'
						self.popupMenu.Enable (self.popupID5, False)
						# enable 'stop editing'
						self.popupMenu.Enable(self.popupID6, True)
						# disable 'remove'
						self.popupMenu.Enable(self.popupID1, False)
						# disable 'bgmap'
						self.popupMenu.Enable(self.popupID14, False)
					else:
						# disable 'start editing'
						self.popupMenu.Enable(self.popupID5, False)
						# disable 'stop editing'
						self.popupMenu.Enable(self.popupID6, False)
						# enable 'bgmap'
						self.popupMenu.Enable(self.popupID14, True)
	
                self.popupMenu.Append(self.popupID7, _("Metadata"))
                self.Bind (wx.EVT_MENU, self.OnMetadata, id=self.popupID7)
                if numSelected > 1:
                    self.popupMenu.Enable(self.popupID4, False)
                    self.popupMenu.Enable(self.popupID5, False)
                    self.popupMenu.Enable(self.popupID6, False)
                    self.popupMenu.Enable(self.popupID7, False)
                    self.popupMenu.Enable(self.popupID14, False)

			#
			# raster layers (specific items)
			#
            elif mltype and mltype == "raster":
                self.popupMenu.Append(self.popupID12, text=_("Zoom to selected map(s) (ignore NULLs)"))
                self.Bind(wx.EVT_MENU, self.mapdisplay.OnZoomToRaster, id=self.popupID12)
                self.popupMenu.Append(self.popupID13, text=_("Set computational region from selected map(s) (ignore NULLs)"))
                self.Bind(wx.EVT_MENU, self.OnSetCompRegFromRaster, id=self.popupID13)
                self.popupMenu.AppendSeparator()
                self.popupMenu.Append(self.popupID15, _("Set color table"))
                self.Bind (wx.EVT_MENU, self.OnColorTable, id=self.popupID15)
                self.popupMenu.Append(self.popupID4, _("Histogram"))
                self.Bind (wx.EVT_MENU, self.OnHistogram, id=self.popupID4)
                self.popupMenu.Append(self.popupID5, _("Profile"))
                self.Bind (wx.EVT_MENU, self.OnProfile, id=self.popupID5)
                self.popupMenu.Append(self.popupID6, _("Metadata"))
                self.Bind (wx.EVT_MENU, self.OnMetadata, id=self.popupID6)
	
                if numSelected > 1:
                    self.popupMenu.Enable(self.popupID12, False)
                    self.popupMenu.Enable(self.popupID13, False)
                    self.popupMenu.Enable(self.popupID15, False)
                    self.popupMenu.Enable(self.popupID4, False)
                    self.popupMenu.Enable(self.popupID5, False)
                    self.popupMenu.Enable(self.popupID6, False)
                    self.popupMenu.Enable(self.popupID11, False)

			## self.PopupMenu(self.popupMenu, pos)
        self.PopupMenu(self.popupMenu)
        self.popupMenu.Destroy()



	def ChooseColour(self,event):

		colourdialog = wx.ColourDialog(self)
		colourdialog.ShowModal()
		rgb = colourdialog.GetColourData().GetColour()
		rgb = str(rgb)
		self.colour = rgb.replace(',',':')
		self.colour = self.colour.strip('(')
		self.colour = self.colour.strip(')')

		item = event.GetItem()
		col = colourdialog.GetColourData().GetColour()

		self.SetHilightFocusColour(col)
		self.SetItemTextColour(item,col)
		item =  event.GetItem()
		parent = self.GetItemParent(item)
		if self.IsItemChecked(parent):
			self.colour_selected = True
			self.CheckItem(parent)
		else:
			self.CheckItem(parent)


    def OnEndRename(self,event):
		"""
		Rename mapset using grass commands
		"""
		item = event.GetItem()
		oldName = self.GetItemText(item) 
		try:
			newName =  self.GetEditControl().GetValue()
		except:
			return
	
    def OnBeginRename(self,event):

		item = self.GetItemText(event.GetItem())

    def OnReport(self,event):

        item =  self.GetSelection()
        mapLayer = self.GetPyData(self.layer_selected)[0]['maplayer']
        mltype = self.GetPyData(self.layer_selected)[0]['type']

        if mltype == 'raster':
            cmd = ['r.info']
        elif mltype == 'vector':
            cmd = ['v.info']
        cmd.append('map=%s' % mapLayer.name)

        # print output to command log area
        self.lmgr.goutput.RunCmd(cmd, switchPage=True)

	
        

    def OnCopy( self,event ):
		#print "copy"
		item =  self.GetSelection()
		parent = self.GetItemParent(item)
		pText = self.GetItemText(parent)
		name = self.GetCopyName(item)
		if pText == "Raster Map" :
			cmdflag = 'rast=' + self.GetItemText(item) + ',' + name
			self.PrependItem(parent=parent,text=name,ct_type=1)
		elif pText  == "Vector Map" :
			cmdflag = 'vect=' + self.GetItemText(item) + ',' + name
			self.PrependItem(parent=parent,text=name,ct_type=1)

		if cmdflag:
			command = ["g.copy", cmdflag]
			gcmd.CommandThread(command,stdout=None,stderr=None).run()


    def GetCopyName(self, item):
        """
        Returns unique name depending on the mapname to be copied.
        """

        def GetPrefix(prefix):
			"""
			This returns a prefix to the given map name 
			prefix applied here is _copy_x.
			"""

			prefix = "_copy_" + str(self.count)
			self.count = self.count + 1
			return prefix

			#end of GetPrefix

        def CheckName(parent,prefix,name):
			"""
			Checks all silbings of the parent wheather the name 
			already exists.
			"""
			ncount = self.GetChildrenCount(parent, False)
			ck = 1
			current , ck = self.GetFirstChild(parent)
			for i in range(ncount):
				if str(self.GetItemText(current)) == str(name + prefix):
					return False
				else:
					current,ck = self.GetNextChild(parent,ck)
			return True
		
			#End of CheckName

		#GetCopyName function starts here
        ext = None	
        self.count  = 1
        ext = GetPrefix(ext)
        name = str(self.GetItemText(item))
        parent = self.GetItemParent(item)
        while  CheckName(parent,ext,name) == False:
	        ext = GetPrefix(ext)
	        CheckName(parent,ext,name)

        name = str(name + ext)
        return name


    def OnRenameMap( self,event ):
        item = self.GetSelection()
        self.EditLabel( self.GetSelection())
        mapLayer = self.GetPyData(self.layer_selected)[0]['maplayer']
        mltype = self.GetPyData(self.layer_selected)[0]['type']
        try:
            newName =  self.GetEditControl().GetValue()
        except:
            newName = mapLayer.name



        if mltype == 'raster':
            cmd = ['g.rename rast=']
        elif mltype == 'vector':
            cmd = ['g.rename vect=']
        cmd.append('%s,%s' % mapLayer.name,newName)

        # print output to command log area
        self.lmgr.goutput.RunCmd(cmd, switchPage=True)


    def OnDeleteMap( self,event ):
		"""
		Performs grass command for deleting a map
		"""
		item =  self.GetSelection()
		if item is not None:
			dlg = wx.MessageDialog(self, message=_(    "Do you want to delete selected map ?"),
						        caption=_("Delete Map"),
						        style=wx.YES_NO | wx.YES_DEFAULT | \
						            wx.CANCEL | wx.ICON_QUESTION)
			ret = dlg.ShowModal()
			if ret == wx.ID_YES:
				dlg.Destroy()
                mapLayer = self.GetPyData(self.layer_selected)[0]['maplayer']
                mltype = self.GetPyData(self.layer_selected)[0]['type']

        if mltype == 'raster':
            cmd = ['g.remove rast=']
        elif mltype == 'vector':
            cmd = ['g.remove vect=']
        cmd.append('%s' % mapLayer.name)

        # print output to command log area
        self.lmgr.goutput.RunCmd(cmd, switchPage=True)


				parent  =self.GetItemParent(item) 
				if self.GetItemText(parent) == "Raster Map" :
					cmdflag = 'rast=' + str(self.GetItemText(item))
				elif self.GetItemText(parent) == "Vector Map" :
					cmdflag = 'vect=' + str(self.GetItemText(item))

				if cmdflag:
					command = ["g.remove", cmdflag]
					gcmd.CommandThread(command,stdout=None,stderr=None).run()
					select = self.GetPrevSibling(item)
					self.Delete(item)
					#self.SelectItem(select)

			elif ret == wx.ID_CANCEL:
			 dlg.Destroy()
			 return


    def OnOssim( self,event ):

		"""
		Performs grass command for adding a map
		"""
		item =  self.GetSelection()
		cmdflag = None
		parent  =self.GetItemParent(item) 
		if self.GetItemText(parent) == "Raster Map" :
			cmdflag = 'r.planet.py -a map=' + str(self.GetItemText(item))
		else:
			if self.GetItemText(item) == 'colour':
				col=self.GetItemTextColour(item)
				mapname = self.GetItemParent(item)
			else:
				child,cookie = self.GetFirstChild(item)
				mapname = item
				col = self.GetItemTextColour(child)
			if col.IsOk() is True:
				col=str(col)
				col = col.replace('(','')
				col = col.replace(')','')
				col = col.split(',')

				cmdflag = 'v.planet.py -a map=' + str(self.GetItemText(mapname)) + \
				            ' brush=' + str(col[0].strip()+','+col[1].strip()+','+col[2].strip()) + \
				            ' pen=' + str(col[0].strip()+','+col[1].strip()+','+col[2].strip()) + \
				            ' size=' +str('1,1')
				#print cmdflag

		if cmdflag is not None:        
			current = OssimPlanet(cmdflag)
			current.start()



    def OnOssim2( self,event ):
		"""
		Performs grass command for deleting a map
		"""
		item =  self.GetSelection()
		cmdflag = None
		parent  =self.GetItemParent(item) 
		if self.GetItemText(parent) == "Raster Map" :
			cmdflag = 'r.planet.py -r map=' + str(self.GetItemText(item))
		else:
			if self.GetItemText(item) == 'colour':
				previtem = self.GetItemParent(item)
				cmdflag = 'v.planet.py -r map=' + str(self.GetItemText(previtem))
			else:
				cmdflag = 'v.planet.py -r map=' + str(self.GetItemText(item))

		if cmdflag is not None:
			current = OssimPlanet(cmdflag)
			current.start()
        



class OssimPlanet(Thread):
   def __init__ (self,cmd):
      Thread.__init__(self)
      self.cmd =  cmd
   def run(self):
      os.system(self.cmd)	



