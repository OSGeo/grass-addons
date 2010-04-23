"""
@package LayerTree.py



@breif A LayerTree for managing maps
based on selected location and mapset

Classes:
 - LayerTree

(C) 2007 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Mohammed Rashad K.M <rashadkm at gmail dot com>

"""
import os
import sys
import wx
import glob
import render
from threading import Thread

import wx.lib.customtreectrl as CT
try:
    import treemixin 
except ImportError:
    from wx.lib.mixins import treemixin

#To run DataCatalog from any directory set this pathname for access to gui_modules 
gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','wxpython','gui_modules')
sys.path.append(pypath)


import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import gcmd




class LayerTree(treemixin.DragAndDrop, CT.CustomTreeCtrl):



    def __init__(self, parent,
                 id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=(300,300), style=wx.SUNKEN_BORDER,
                 ctstyle=CT.TR_HAS_BUTTONS | CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                 CT.TR_HIDE_ROOT | CT.TR_FULL_ROW_HIGHLIGHT |
                 CT.TR_MULTIPLE,mapdisplay=None,frame=None,panel=None,Map=None,lmgr=None,gisdbase=None):
        self.items = []
        self.itemCounter = 0
        
        super(LayerTree, self).__init__(parent, id, pos, size, style=style, ctstyle=ctstyle)
        self.SetName("LayerTree")


        self.itemFont = wx.Font(pointSize=9,weight=0, family=wx.FONTFAMILY_DEFAULT ,style=wx.FONTSTYLE_ITALIC)

        self.gisdbase = gisdbase


        self.Map = None
        #if self.Map is not None:
        #    print self.Map.width

        self.ID_REN= wx.NewId()
        self.ID_COPY = wx.NewId()
        self.ID_DEL = wx.NewId()
        self.ID_OSSIM = wx.NewId()

        acel = wx.AcceleratorTable([ 
		        (wx.ACCEL_CTRL,  ord('R'), self.ID_REN ) ,
		        (wx.ACCEL_CTRL,  ord('C'), self.ID_COPY) ,
		        (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.ID_DEL) ])


        self.SetAcceleratorTable(acel)

        self.dict = {}

        self.layer = []
        self.maplayer = None

        d = self.GetParent()
        notebook = d.GetParent()


        child=notebook.GetChildren()
        for panel in child:
              if panel.GetName() == "pg_panel":
                self.mapdisplay = panel

        self.MapWindow = self.mapdisplay.MapWindow2D
        self.Bind(CT.EVT_TREE_ITEM_CHECKED,     self.OnLayerChecked)


        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,self.OnTreePopUp)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndRename)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginRename)

	    #Event bindings for tree menu
        self.Bind(wx.EVT_MENU,self.OnCopy,id=self.ID_COPY)
        self.Bind(wx.EVT_MENU,self.OnRename,id=self.ID_REN)
        self.Bind(wx.EVT_MENU,self.OnDelete,id=self.ID_DEL)
        self.Bind(wx.EVT_MENU,self.OnOssim,id=self.ID_OSSIM)




    def OnLayerChecked(self, event):
        """!Enable/disable data layer"""

        item    = event.GetItem()
        checked = item.IsChecked()


        pText = self.GetItemText(self.GetItemParent(item)) 


        leftpanel=self.GetParent()
        notebook = leftpanel.GetParent()
        frame = notebook.GetParent()


        if not self.ItemHasChildren(item):
            self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()
            #for f in frames:
            #    print f.GetName()     
            #maptree = mapframe.maptree

            if pText == "Raster Map" :
                self.cmd= ['d.rast', str("map=" + self.mapname)]
                l_type='raster'
                
                self.maplayer = self.MapWindow.Map.AddLayer(type='raster', name=self.mapname, command=self.cmd)
               

                #layer = maptree.PrependItem(parent=maptree.root, text=self.mapname, ct_type=1)
                #maptree.first = True
                #maptree.layer_selected = layer
                #maptree.CheckItem(layer)
                #self.layer.append(self.maplayer)
                #maptree.PlusLayer(self.maplayer)


            if pText == "Vector Map" :
                self.cmd= ['d.vect', str("map=" + self.mapname)]
                l_type='vector'
                
                self.maplayer = self.MapWindow.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)


            self.MapWindow.Map.region = self.MapWindow.Map.GetRegion()
            self.MapWindow.flag = True
            self.MapWindow.UpdateMap(render=True)
            self.MapWindow.flag = False
                #layer = maptree.PrependItem(parent=maptree.root, text=self.mapname, ct_type=1)
                #maptree.first = True
                #maptree.layer_selected = layer
                #maptree.CheckItem(layer)
                #self.layer.append(self.maplayer)
                #maptree.PlusLayer(self.maplayer)




    def AddTreeNodes(self,location,mapset):
        """
        Adds tree nodes. raster,vector and dbf files are identified using 
        their directory structure.
        """
        self.DeleteAllItems()
        root = self.AddRoot("Map Layers")
        self.SetPyData(root, (None,None))
        node_raster = self.AppendItem(root, "Raster Map")
        node_vector = self.AppendItem(root, "Vector Map")
        node_dbf = self.AppendItem(root, "DBF")
        treeNodes = [node_raster,node_vector,node_dbf]

        glocs = glob.glob(os.path.join(self.gisdbase,location, mapset,"*"))
        for gloc in glocs:
            if not os.path.isfile(gloc) and os.path.isdir(gloc):
	            if(os.path.basename(gloc)=='cellhd'):
		            for rast in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
			            self.PrependItem(node_raster, os.path.basename(rast),ct_type=1)
	            elif(os.path.basename(gloc)=='vector'):
		            for vect in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
			            self.PrependItem(node_vector, os.path.basename(vect),ct_type=1)
	            elif(os.path.basename(gloc)=='dbf'):
		            for dfile in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
			            self.PrependItem(node_dbf, os.path.basename(dfile),ct_type=1)

        #Nodes with no children are given an italic type font
        for node in treeNodes: 
            if not self.ItemHasChildren(node):
	            if self.GetItemText(node) == 'Raster Map':
		            tmp_item = self.AppendItem(node, "No raster maps found.")
	            elif self.GetItemText(node) == 'Vector Map':
		            tmp_item = self.AppendItem(node, "No vector maps found.")
	            elif self.GetItemText(node) == 'DBF':
		            tmp_item = self.AppendItem(node, "No DBF files found.")
	            self.SetItemFont(tmp_item,self.itemFont)


        self.SortChildren(node_raster)
        self.SortChildren(node_vector)
        self.SortChildren(node_dbf)

    def OnToggleExpand(self,event):  
	    if self.treeExpand.GetValue() == True:
		    self.ExpandAll()
	    else: 
		    self.CollapseAll()


    def OnBeginRename(self,event):

        item = self.GetItemText(event.GetItem())
        if type(item) == str and item in ("Raster Map", "Vector Map" , "DBF"):
            event.Veto()             #disable editing of parent items

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
	    parent =self.GetItemParent(item)
	    if self.GetItemText(parent) == "Raster Map" :
		    cmdflag = 'rast=' +  oldName + ',' + newName
	    elif self.GetItemText(parent) == "Vector Map" :
		    cmdflag = 'vect=' +  oldName + ',' + newName

	    if cmdflag:
		    command = ["g.rename", cmdflag]
		    gcmd.CommandThread(command,stdout=None,stderr=None).run()



    def OnTreePopUp(self,event):
        """
        Display a popupMenu for copy,rename & delete operations
        """
        item =  event.GetItem()
        if not self.ItemHasChildren(item) and \
               self.GetItemFont(item) != self.itemFont:

            self.popupmenu = wx.Menu()
            mnuCopy = self.popupmenu.Append(self.ID_COPY,'&Copy\tCtrl+C')
            mnuRename = self.popupmenu.Append(self.ID_REN,'&Rename\tCtrl-R')
            mnuDel = self.popupmenu.Append(self.ID_DEL,'&Delete\tDEL')
            mnuOssim = self.popupmenu.Append(self.ID_OSSIM,'&send to OssimPlanet')
            self.PopupMenu(self.popupmenu)


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


    def OnRename( self,event ):

        item = self.GetSelection()
        self.EditLabel( self.GetSelection())


    def OnDelete( self,event ):
        """
        Performs grass command for deleting a map
        """
        item =  self.GetSelection()
        dlg = wx.MessageDialog(self, message=_(    "Do you want to delete selected map ?"),
                            caption=_("Delete Map"),
                            style=wx.YES_NO | wx.YES_DEFAULT | \
                                wx.CANCEL | wx.ICON_QUESTION)
        ret = dlg.ShowModal()
        if ret == wx.ID_YES:
            dlg.Destroy()
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
        Performs grass command for deleting a map
        """
        item =  self.GetSelection()
        
        parent  =self.GetItemParent(item) 
        if self.GetItemText(parent) == "Raster Map" :
            cmdflag = 'r.planet.py -a map=' + str(self.GetItemText(item))
        elif self.GetItemText(parent) == "Vector Map" :
            cmdflag = 'v.planet.py -a map=' + str(self.GetItemText(item))

        if cmdflag:
            
            #command = ["r.planet.py", cmdflag]
            #gcmd.CommandThread(command,stdout=None,stderr=None).run()
            current = OssimPlanet(cmdflag)
            current.start()

        

    def OnDisplay(self, event):

        item =  event.GetItem()
        pText = self.GetItemText(self.GetItemParent(item)) 
        


class OssimPlanet(Thread):
   def __init__ (self,cmd):
      Thread.__init__(self)
      self.cmd =  cmd
   def run(self):
      os.system(self.cmd)	



