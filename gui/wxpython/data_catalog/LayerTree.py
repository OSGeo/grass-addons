import os
import sys
import wx
import glob
import render
from threading import Thread


#To run DataCatalog from any directory set this pathname for access to gui_modules 
gbase = os.getenv("GISBASE") 
pypath = os.path.join(gbase,'etc','wxpython','gui_modules')
sys.path.append(pypath)


import globalvar
if not os.getenv("GRASS_WXBUNDLED"):
    globalvar.CheckForWx()
import gcmd




class LayerTree(wx.TreeCtrl):

    def __init__(self, parent, id,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style= wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS,gisdbase=None):

        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
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



    def AddTreeNodes(self,location,mapset):
	    """
	    Adds tree nodes. raster,vector and dbf files are identified using 
	    their directory structure.
	    """

	    root = self.AddRoot('root')
	    node_raster = self.AppendItem(root, "Raster Map")
	    node_vector = self.AppendItem(root, "Vector Map")
	    node_dbf = self.AppendItem(root, "DBF")
	    treeNodes = [node_raster,node_vector,node_dbf]

	    glocs = glob.glob(os.path.join(self.gisdbase,location, mapset,"*"))
	    for gloc in glocs:
		    if not os.path.isfile(gloc) and os.path.isdir(gloc):
			    if(os.path.basename(gloc)=='cellhd'):
				    for rast in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
					    self.AppendItem(node_raster, os.path.basename(rast))
			    elif(os.path.basename(gloc)=='vector'):
				    for vect in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
					    self.AppendItem(node_vector, os.path.basename(vect))
			    elif(os.path.basename(gloc)=='dbf'):
				    for dfile in glob.glob(os.path.join(self.gisdbase,location, mapset,gloc, "*")):
					    self.AppendItem(node_dbf, os.path.basename(dfile))

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
		    self.InsertItem(parent,item, name)
	    elif pText  == "Vector Map" :
		    cmdflag = 'vect=' + self.GetItemText(item) + ',' + name
		    self.InsertItem(parent,item, name)

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
                self.SelectItem(select)

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
        

        leftpanel=self.GetParent()
        splitter = leftpanel.GetParent()
        frame = splitter.GetParent()
        window2 = splitter.GetWindow2()

        winlist = window2.GetChildren()
        for win in winlist:
            if type(win) == wx.lib.flatnotebook.FlatNotebook:
                #win.SetSelection(0)
                child=win.GetChildren()
                for panel in child:
                    #print panel.GetName()
                    if panel.GetName() == "pg_panel":
                        mapframe = panel

                        

       # mtree = mapframe.maptree
        #print mtree.GetName()


        

        if not self.ItemHasChildren(item):
            self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()
            #for f in frames:
            #    print f.GetName()     
            maptree = mapframe.maptree

            if pText == "Raster Map" :
                self.cmd= ['d.rast', str("map=" + self.mapname)]
                l_type="raster"
                
                self.maplayer = mapframe.Map.AddLayer(type=l_type, name=self.mapname, command=self.cmd)	

                #mapframe.maptree.AddLayer(ltype="raster", lname=self.mapname, lchecked=True,lcmd=self.cmd)
                maptree.ltype = 'raster'
                
                mapframe.Map.region = mapframe.Map.GetRegion()
                mapframe.MapWindow2D.flag = True
                mapframe.MapWindow2D.UpdateMap(render=True)
                mapframe.MapWindow2D.flag = False

                layer = maptree.PrependItem(parent=maptree.root, text=self.mapname, ct_type=1)
                maptree.first = True
                maptree.layer_selected = layer
                maptree.CheckItem(layer)
                #self.layer.append(self.maplayer)
                maptree.PlusLayer(self.maplayer)

              

        #update new layer 
#        mapframe.maptree.SetPyData(newItem, mapframe.maptree.GetPyData(dragItem))

            
#                mapframe.maptree.CheckItem(newItem, checked=True) # causes a new render
#                mapframe.maptree.SelectItem(newItem, select=True)







	            #self.infocmd = ["r.info", str(self.mapname)]
            elif pText == "Vector Map" :
                self.cmd= ['d.vect', str("map=" + self.mapname)]
                mapframe.maptree.AddLayer(ltype="vector", lname=self.mapname, lchecked=True,lcmd=self.cmd)
                l_type="vector"
	            #self.infocmd = ["r.info", str(self.mapname)]

                self.maplayer = mapframe.Map.AddLayer(type=l_type, name=self.mapname, command=self.cmd)	

                #mapframe.maptree.AddLayer(ltype="raster", lname=self.mapname, lchecked=True,lcmd=self.cmd)
                maptree.ltype = 'vector'
                
                mapframe.Map.region = mapframe.Map.GetRegion()
                mapframe.MapWindow2D.flag = True
                mapframe.MapWindow2D.UpdateMap(render=True)
                mapframe.MapWindow2D.flag = False

                layer = maptree.PrependItem(parent=maptree.root, text=self.mapname, ct_type=1)
                maptree.first = True
                maptree.layer_selected = layer
                maptree.CheckItem(layer)
                #self.layer.append(self.maplayer)
                maptree.PlusLayer(self.maplayer)
                


       # if self.cmd:
         #  mapframe.Map.Clean()
         #  mapframe.Map.__init__()			#to update projection and region
         #  mapframe.Map.AddLayer(type=l_type, name='layer1', command=self.cmd)	
         #  mapframe.Map.region = panel.Map.GetRegion()
         #  mapframe.MapWindow2D.flag = True
         #  mapframe.MapWindow2D.UpdateMap(render=True)

class OssimPlanet(Thread):
   def __init__ (self,cmd):
      Thread.__init__(self)
      self.cmd =  cmd
   def run(self):
      os.system(self.cmd)	



