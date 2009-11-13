"""
@package catalog.py

GRASS DataCatalog.

@breif A GRASS GIS data manager used to copy,rename,delete,
display maps in different mapsets and locations.

Classes:
 - DataCatalog
 - CatalogApp

(C) 2007 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad K.M <rashadkm at gmail dot com>

"""

import os
import sys
#To run DataCatalog from any directory set this pathname for access to gui_modules 
gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','wxpython','gui_modules')
sys.path.append(pypath)


import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import wx
import gcmd
import glob
import render
from mapwindow import BufferedWindow


class DataCatalog(wx.Frame):

	def __init__(self,size=wx.DefaultSize):
		wx.Frame.__init__(self, None, wx.ID_ANY, "Data Catalog", wx.DefaultPosition, wx.DefaultSize)
		self.Maximize()

		self.gisbase  = os.getenv("GISBASE")
		self.gisrc  = self.read_gisrc()
		self.viewInfo = True        #to display v/r.info on mapdisplay
		self.gisdbase = self.gisrc['GISDBASE']

        #backup location and mapset from gisrc which may be modified  by datacatalog
		self.iLocation = self.gisrc['LOCATION_NAME']
		self.iMapset = self.gisrc['MAPSET']

		self.ID_REN= wx.NewId()
		self.ID_COPY = wx.NewId()
		self.ID_DEL = wx.NewId()
		self.ID_EXPAND = wx.NewId()
		self.ID_COLLAPSE = wx.NewId()

		acel = wx.AcceleratorTable([ 
				(wx.ACCEL_CTRL,  ord('R'), self.ID_REN ) ,
				(wx.ACCEL_CTRL,  ord('C'), self.ID_COPY) ,
				(wx.ACCEL_NORMAL, wx.WXK_DELETE, self.ID_DEL) ])


		self.SetAcceleratorTable(acel)


		#creating sizers    
		self.cmbSizer = wx.GridBagSizer(hgap=5, vgap=0) 
		self.mSizer = wx.BoxSizer(wx.VERTICAL)

		#these two sizers are applied to splitter window
		self.leftSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.rightSizer = wx.BoxSizer(wx.VERTICAL)

		#populate location combobox
		self.loclist = self.GetLocations()

		#creating controls
		self.mInfo = wx.TextCtrl(self.pRight, wx.ID_ANY, style = wx.TE_MULTILINE|wx.HSCROLL|wx.TE_READONLY)
		self.chkInfo = wx.CheckBox(self.cmbPanel, wx.ID_ANY,"Display Info", wx.DefaultPosition, wx.DefaultSize)
		self.treeExpand = wx.CheckBox(self.cmbPanel, wx.ID_ANY,"Expand All", wx.DefaultPosition, wx.DefaultSize)
		self.lbLocation = wx.StaticText(self.cmbPanel, wx.ID_ANY, "Location")
		self.lbMapset = wx.StaticText(self.cmbPanel, wx.ID_ANY, "Mapset")
		self.cmbLocation = wx.ComboBox(self.cmbPanel, value = "Select Location",size=wx.DefaultSize, choices=self.loclist)
		self.cmbMapset = wx.ComboBox(self.cmbPanel, value = "Select Mapset", size=wx.DefaultSize)	
		self.tree = wx.TreeCtrl(self.pLeft, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS|wx.TR_EDIT_LABELS)
		self.itemFont = wx.Font(pointSize=9,weight=0, family=wx.FONTFAMILY_DEFAULT ,style=wx.FONTSTYLE_ITALIC)
		#self.redir = wx.TextCtrl(self, wx.ID_ANY)

		self.Map = render.Map()
		self.MapWindow = BufferedWindow(self.pRight, wx.ID_ANY,wx.DefaultPosition, size=(640,480), Map=self.Map)
		self.Map.Clean()


		#By default v/r.info will be displayed
		self.chkInfo.SetValue(True) 
		self.treeExpand.SetValue(False)

		#apply bindings and setting layouts
		self.doBindings()
		self.doLayout()
		self.Centre()
        
    
	def OnToggleInfo(self,event):  
		if self.chkInfo.GetValue() == True:
			self.viewInfo = True
			self.mInfo.Show()
		else: 
			self.viewInfo = False
			self.mInfo.Hide()

	def OnToggleExpand(self,event):  
		if self.tree and self.treeExpand.GetValue() == True:
		  self.tree.ExpandAll()
		else: 
		  self.tree.CollapseAll()

	def OnBeginRename(self,event):

	    item = self.tree.GetItemText(event.GetItem())
	    if type(item) == str and item in ("Raster Map", "Vector Map" , "DBF"):
	        event.Veto()             #disable editing of parent items
	
	def OnEndRename(self,event):
		"""
		Rename mapset using grass commands
		"""
		item = event.GetItem()
		oldName = self.tree.GetItemText(item) 
		try:
			newName =  self.tree.GetEditControl().GetValue()
		except:
			return
		parent =self.tree.GetItemParent(item)
		if self.tree.GetItemText(parent) == "Raster Map" :
			cmdflag = 'rast=' +  oldName + ',' + newName
		elif self.tree.GetItemText(parent) == "Vector Map" :
			cmdflag = 'vect=' +  oldName + ',' + newName

		if cmdflag:
			command = ["g.rename", cmdflag]
			gcmd.CommandThread(command,stdout=None,stderr=None).run()



	def OnTreePopUp(self,event):
		"""
		Display a popupMenu for copy,rename & delete operations
		"""
		item =  event.GetItem()
		if not self.tree.ItemHasChildren(item) and \
			   self.tree.GetItemFont(item) != self.itemFont:

			self.popupmenu = wx.Menu()
			mnuCopy = self.popupmenu.Append(self.ID_COPY,'&Copy\tCtrl+C')
			mnuRename = self.popupmenu.Append(self.ID_REN,'&Rename\tCtrl-R')
			mnuDel = self.popupmenu.Append(self.ID_DEL,'&Delete\tDEL')
			self.tree.PopupMenu(self.popupmenu)





	def OnCopy( self,event ):
        #print "copy"
		item =  self.tree.GetSelection()
		parent = self.tree.GetItemParent(item)
		pText = self.tree.GetItemText(parent)
		name = self.GetCopyName(item)
		if pText == "Raster Map" :
			cmdflag = 'rast=' + self.tree.GetItemText(item) + ',' + name
			self.tree.InsertItem(parent,item, name)
		elif pText  == "Vector Map" :
			cmdflag = 'vect=' + self.tree.GetItemText(item) + ',' + name
			self.tree.InsertItem(parent,item, name)

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
			ncount = self.tree.GetChildrenCount(parent, False)
			ck = 1
			current , ck = self.tree.GetFirstChild(parent)
			for i in range(ncount):
				if str(self.tree.GetItemText(current)) == str(name + prefix):
					return False
				else:
					current,ck = self.tree.GetNextChild(parent,ck)
			return True
            
            #End of CheckName

        #GetCopyName function starts here
		ext = None	
		self.count  = 1
		ext = GetPrefix(ext)
		name = str(self.tree.GetItemText(item))
		parent = self.tree.GetItemParent(item)
		while  CheckName(parent,ext,name) == False:
			ext = GetPrefix(ext)
			CheckName(parent,ext,name)

		name = str(name + ext)
		return name


	def OnRename( self,event ):

	    item = self.tree.GetSelection()
	    self.tree.EditLabel( self.tree.GetSelection())


	def OnDelete( self,event ):
		"""
		Performs grass command for deleting a map
		"""
		item =  self.tree.GetSelection()
		parent  =self.tree.GetItemParent(item) 
		if self.tree.GetItemText(parent) == "Raster Map" :
			cmdflag = 'rast=' + str(self.tree.GetItemText(item))
		elif self.tree.GetItemText(parent) == "Vector Map" :
			cmdflag = 'vect=' + str(self.tree.GetItemText(item))

		if cmdflag:
			command = ["g.remove", cmdflag]
			gcmd.CommandThread(command,stdout=None,stderr=None).run()
			select = self.tree.GetPrevSibling(item)
			self.tree.Delete(item)
			self.tree.SelectItem(select)


	def OnCloseWindow(self,event):

		if self.gisrc['LOCATION_NAME'] != self.iLocation or \
			self.gisrc['MAPSET'] != self.iMapset:
			self.gisrc['LOCATION_NAME'] = self.iLocation
			self.gisrc['MAPSET'] = self.iMapset
			self.update_grassrc(self.gisrc)	
 
		self.Map.Clean()
		event.Skip()
        #self.Destroy()
	

	def OnDisplay(self, event):
		item =  event.GetItem()
		pText = self.tree.GetItemText(self.tree.GetItemParent(item)) 

		if not self.tree.ItemHasChildren(item):
			self.mapname = "map=" + self.tree.GetItemText(item) + "@" +self.cmbMapset.GetValue()
	        if pText == "Raster Map" :
				self.cmd= ['d.rast', str(self.mapname)]
				self.infocmd = ["r.info", str(self.mapname)]
	        elif pText == "Vector Map" :
				self.cmd= ['d.vect', str(self.mapname)]
				self.infocmd = ["v.info", str(self.mapname)]

		if self.cmd:		
			self.Map.Clean()
			self.Map.__init__()			#to update projection and region
			self.Map.AddLayer(type='raster', name='layer1', command=self.cmd)	
			self.Map.region = self.Map.GetRegion()
			self.MapWindow.flag = True
			self.MapWindow.Map = self.Map
			self.MapWindow.UpdateMap(render=True)

		if self.viewInfo is True:
	   		gcmd.CommandThread(self.infocmd, stdout=self.mInfo).run()
	   		lines = self.mInfo.GetValue()
	   		lines = lines.replace('|','')
	   		lines =lines.replace('+','')
	   		lines =lines.replace('-','')
	   		#lines =lines.replace('-+','-------------------------------+')
	   		#lines =lines.replace('-\n','---------------------------------')
	   		#lines = lines.replace('+','----+')
			self.mInfo.SetValue(lines)

	def OnMapsetChange(self,event):
		"""
		Create the tree nodes based on selected location and mapset.
		Also update gisrc and grassrc files.
		"""
		self.tree.DeleteAllItems()
		self.AddTreeNodes(self.cmbLocation.GetValue(),self.cmbMapset.GetValue())	
		self.gisrc['LOCATION_NAME'] = str(self.cmbLocation.GetValue())
		self.gisrc['MAPSET'] = str(self.cmbMapset.GetValue())
		self.update_grassrc(self.gisrc)



	def OnLocationChange(self,event):
		"""
		Populate mapset combobox with selected location.
		"""

		self.cmbMapset.Clear()
		self.cmbMapset.SetValue("Select Mapset")
		self.tree.DeleteAllItems()

		maplists = self.GetMapsets(self.cmbLocation.GetValue())
		for mapsets in maplists:
			self.cmbMapset.Append(str(mapsets))

	def AddTreeNodes(self,location,mapset):
		"""
		Adds tree nodes. raster,vector and dbf files are identified using 
		their directory structure.
		"""

		root = self.tree.AddRoot('root')
		node_raster = self.tree.AppendItem(root, "Raster Map")
		node_vector = self.tree.AppendItem(root, "Vector Map")
		node_dbf = self.tree.AppendItem(root, "DBF")
		treeNodes = [node_raster,node_vector,node_dbf]

		glocs = glob.glob(os.path.join(self.gisdbase,location, mapset,"*"))
		for gloc in glocs:
			if not os.path.isfile(gloc) and os.path.isdir(gloc):
				if(os.path.basename(gloc)=='cats'):
					for rast in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
						self.tree.AppendItem(node_raster, os.path.basename(rast))
				elif(os.path.basename(gloc)=='vector'):
					for vect in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
						self.tree.AppendItem(node_vector, os.path.basename(vect))
				elif(os.path.basename(gloc)=='dbf'):
					for dfile in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
						self.tree.AppendItem(node_dbf, os.path.basename(dfile))

        #Nodes with no children are given an italic type font
		for node in treeNodes: 
			if not self.tree.ItemHasChildren(node):
				if self.tree.GetItemText(node) == 'Raster Map':
					tmp_item = self.tree.AppendItem(node, "No raster maps found.")
				elif self.tree.GetItemText(node) == 'Vector Map':
					tmp_item = self.tree.AppendItem(node, "No vector maps found.")
				elif self.tree.GetItemText(node) == 'DBF':
					tmp_item = self.tree.AppendItem(node, "No DBF files found.")
				self.tree.SetItemFont(tmp_item,self.itemFont)

	def GetMapsets(self,location):
		"""
		Read and returns all mapset int GRASS data directory.
		"""
		
		maplist = []
		for mapset in glob.glob(os.path.join(self.gisdbase, location, "*")):
			if os.path.isdir(mapset) and os.path.isfile(os.path.join(self.gisdbase, location, mapset, "WIND")):
				maplist.append(os.path.basename(mapset))
				#print mapset
		return maplist

	def GetLocations(self):
		"""
		Read and returns all locations int GRASS data directory.
		"""
		loclist = []
		for location in glob.glob(os.path.join(self.gisdbase, "*")):
			if os.path.join(location, "PERMANENT") in glob.glob(os.path.join(location, "*")):
				loclist.append(os.path.basename(location))
		return loclist


	def doBindings(self):
        
		#Event bindings for combo boxes
		self.Bind(wx.EVT_COMBOBOX,self.OnMapsetChange,self.cmbMapset)
		self.Bind(wx.EVT_COMBOBOX,self.OnLocationChange,self.cmbLocation)

		#Event bindings for tree -(display,popup,label edit.)
		self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnDisplay,self.tree)
		self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,self.OnTreePopUp,self.tree)
		self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndRename,self.tree)
		self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginRename,self.tree)

		#Event bindings for tree menu
		self.Bind(wx.EVT_MENU,self.OnCopy,id=self.ID_COPY)
		self.Bind(wx.EVT_MENU,self.OnRename,id=self.ID_REN)
		self.Bind(wx.EVT_MENU,self.OnDelete,id=self.ID_DEL)

		self.Bind(wx.EVT_CLOSE,    self.OnCloseWindow)

		#Event bindings for v/r.info checkbox
		self.Bind(wx.EVT_CHECKBOX, self.OnToggleInfo,self.chkInfo)
		self.Bind(wx.EVT_CHECKBOX, self.OnToggleExpand,self.treeExpand)
	def doLayout(self):

		#combo panel sizers
		self.cmbSizer.Add(self.lbLocation,pos=(1,0),flag=wx.ALL,border=2)
		self.cmbSizer.Add(self.lbMapset,pos=(1,1),flag=wx.ALL,border=2)
		self.cmbSizer.Add(self.cmbLocation,pos=(2,0),flag=wx.ALL)
		self.cmbSizer.Add(self.cmbMapset,pos=(2,1),flag=wx.ALL)
		self.cmbSizer.Add(self.chkInfo,pos=(2,2),flag=wx.ALL)
		self.cmbSizer.Add(self.treeExpand,pos=(2,3),flag=wx.ALL)
		self.cmbPanel.SetSizer(self.cmbSizer)

		#splitter window sizers
		self.mSizer.Add(self.cmbPanel,flag=wx.EXPAND)
		self.mSizer.Add(self.win, 1, wx.EXPAND)
		self.SetSizer(self.mSizer)

		#sizers for splitter window panels
		self.leftSizer.Add(self.tree,1,wx.EXPAND)
		self.rightSizer.Add(self.MapWindow)
		self.rightSizer.Add(self.mInfo,1,wx.EXPAND)
		self.pLeft.SetSizer(self.leftSizer)
		self.pRight.SetSizer(self.rightSizer)



	def read_gisrc(self):
		"""
		Read variables from $HOME/.grassrc7 file
		"""

		rc = {}

		gisrc = os.getenv("GISRC")

		if gisrc and os.path.isfile(gisrc):
			try:
				f = open(gisrc, "r")
				for line in f.readlines():
					key, val = line.split(":", 1)
					rc[key.strip()] = val.strip()
			finally:
				f.close()

		return rc

	def update_grassrc(self,gisrc):
		"""
		Update $HOME/.grassrc7 and gisrc files
		"""

		rc = os.getenv("GISRC")
		grassrc = os.path.join(os.getenv('HOME'), ".grassrc7.%s" % os.uname()[1])
		if not os.access(grassrc, os.R_OK):
			grassrc = os.path.join(os.getenv('HOME'), ".grassrc7")
		if rc and os.path.isfile(rc):
			try:
				f = open(rc, 'w')
				for key, val in gisrc.iteritems():
				    f.write("%s: %s\n" % (key, val))
			finally:
				f.close()

		if grassrc and os.path.isfile(grassrc):
			try:
				g = open(grassrc, 'w')
				for key, val in gisrc.iteritems():
				    g.write("%s: %s\n" % (key, val))
			finally:
				    g.close()

#End of DataCatalog class

class CatalogApp(wx.App):

    def OnInit(self):
        wx.InitAllImageHandlers()
        self.catalog = DataCatalog()
        self.catalog.Show()
	    #self.catalog.Maximize()
	return 1


# end of class MapApp

# Run the program
if __name__ == "__main__":
    g_catalog = CatalogApp(0)
    g_catalog.MainLoop()
    #sys.exit(0)	
    





