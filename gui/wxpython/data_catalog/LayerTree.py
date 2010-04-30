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
        self.ID_OSSIM2 = wx.NewId()
        self.ID_INFO = wx.NewId()
        self.ID_REPORT = wx.NewId()
        self.ID_AREA = 200
        self.ID_LENGTH = 201
        self.ID_COOR = 202

        acel = wx.AcceleratorTable([ 
		        (wx.ACCEL_CTRL,  ord('R'), self.ID_REN ) ,
		        (wx.ACCEL_CTRL,  ord('C'), self.ID_COPY) ,
		        (wx.ACCEL_NORMAL, wx.WXK_DELETE, self.ID_DEL) ])


        self.SetAcceleratorTable(acel)

        self.dict = {}

        self.colour = '0:0:0'  #default colour for vector lines
        self.colour_selected = False

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
        self.Bind(CT.EVT_TREE_ITEM_ACTIVATED,     self.ChooseColour)

        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK,self.OnTreePopUp)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.OnEndRename)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.OnBeginRename)

	    #Event bindings for tree menu
        self.Bind(wx.EVT_MENU,self.OnCopy,id=self.ID_COPY)
        self.Bind(wx.EVT_MENU,self.OnRename,id=self.ID_REN)
        self.Bind(wx.EVT_MENU,self.OnDelete,id=self.ID_DEL)
        self.Bind(wx.EVT_MENU,self.OnOssim,id=self.ID_OSSIM)
        self.Bind(wx.EVT_MENU,self.OnOssim2,id=self.ID_OSSIM2)
        self.Bind(wx.EVT_MENU,self.OnInfo,id=self.ID_INFO)
        self.Bind(wx.EVT_MENU,self.OnReport,id=self.ID_REPORT)
        self.Bind(wx.EVT_MENU,self.OnvReport,id=self.ID_AREA)
        self.Bind(wx.EVT_MENU,self.OnvReport,id=self.ID_LENGTH)
        self.Bind(wx.EVT_MENU,self.OnvReport,id=self.ID_COOR)


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
        
   



    def OnInfo(self,event):

        item =  self.GetSelection()
        parent = self.GetItemParent(item)
        pText = self.GetItemText(parent)

        leftpanel=self.GetParent()
        notebook = leftpanel.GetParent()
        frame = notebook.GetParent()

        if not self.ItemHasChildren(item):
            self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()

            if pText == "Raster Map" :
                command = ["r.info", 'map=' +  self.mapname]
                frame.goutput.RunCmd(command)
            if pText == "Vector Map" :
                command = ["v.info", 'map=' +  self.mapname]
                frame.goutput.RunCmd(command)

    def OnReport(self,event):

        item =  self.GetSelection()
        parent = self.GetItemParent(item)
        pText = self.GetItemText(parent)

        leftpanel=self.GetParent()
        notebook = leftpanel.GetParent()
        frame = notebook.GetParent()

        
        if not self.ItemHasChildren(item):
            self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()
            
            if pText == "Raster Map" :
                command = ["r.report", 'map=' +  self.mapname]
                frame.goutput.RunCmd(command)
#            if pText == "Vector Map" :
#                command = ["v.report", 'map=' +  self.mapname]
#                frame.goutput.RunCmd(command)

        
    def OnvReport(self,event):

        item =  self.GetSelection()
        Id = event.GetId()
        if Id == 200:
            option = 'area'
        elif Id == 201:
            option = 'length'
        elif Id == 202:
            option = 'coor'
        parent = self.GetItemParent(item)
        pText = self.GetItemText(parent)

        leftpanel=self.GetParent()
        notebook = leftpanel.GetParent()
        frame = notebook.GetParent()

        
        #if not self.ItemHasChildren(item):
        self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()
        command = ["v.report", 'map=' +  self.mapname,'option=' + str(option)]
        frame.goutput.RunCmd(command)





    def OnLayerChecked(self, event):
        """!Enable/disable data layer"""

        item    = event.GetItem()
        checked = item.IsChecked()


        pText = self.GetItemText(self.GetItemParent(item)) 


        leftpanel=self.GetParent()
        notebook = leftpanel.GetParent()
        frame = notebook.GetParent()





        self.mapname =  self.GetItemText(item) + "@" + frame.cmbMapset.GetValue()
        #for f in frames:
        #    print f.GetName()     
        #maptree = mapframe.maptree

        if pText == "Raster Map" :
            if checked == True:
                self.cmd= ['d.rast', str("map=" + self.mapname)]
                maplayer = self.MapWindow.Map.AddLayer(type='raster', name=self.mapname, command=self.cmd)
                self.layer_selected = maplayer
                self.type = 'raster'
            else:
                layers =  self.MapWindow.Map.GetListOfLayers( l_type='raster', l_name=self.mapname)
                for layer in layers:
                    self.MapWindow.Map.DeleteLayer(layer)
                    self.MapWindow.EraseMap()
        
        


        if pText == "Vector Map" :
            if checked == True:
                self.cmd= ['d.vect', str("map=" + self.mapname),str('color=' +  self.colour)]
                if self.colour_selected == False:
                    maplayer = self.MapWindow.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
                else:
                    self.colour_selected = False
                    layers =  self.MapWindow.Map.GetListOfLayers( l_type='vector', l_name=self.mapname)
                    for layer in layers:
                        maplayer=layer.__init__(type='vector', name=self.mapname, cmd=self.cmd)
                self.layer_selected = maplayer
                self.type = 'vector'
            else:
                layers =  self.MapWindow.Map.GetListOfLayers( l_type='vector', l_name=self.mapname)
                for layer in layers:
                    self.MapWindow.Map.DeleteLayer(layer)
                    self.MapWindow.EraseMap()
        
        self.MapWindow.Map.region = self.MapWindow.Map.GetRegion()
        self.MapWindow.flag = True
        self.MapWindow.UpdateMap(render=True)
        self.MapWindow.flag = False







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
                        vectormap = self.PrependItem(node_vector, os.path.basename(vect),ct_type=1)
                        self.PrependItem(vectormap, "colour")
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
        parent = self.GetItemParent(item)
        pText = self.GetItemText(parent)
      #  if not self.ItemHasChildren(item) and \
      #         self.GetItemFont(item) != self.itemFont:
        if self.GetItemText(item)!='Raster Map' and \
                self.GetItemText(item)!='Vector Map' and \
                self.GetItemText(item)!='DBF' and \
                self.GetItemFont(item) != self.itemFont:
            self.popupmenu = wx.Menu()
            mnuCopy = self.popupmenu.Append(self.ID_COPY,'&Copy\tCtrl+C')
            mnuRename = self.popupmenu.Append(self.ID_REN,'&Rename\tCtrl-R')
            mnuDel = self.popupmenu.Append(self.ID_DEL,'&Delete\tDEL')
            #self.popupmenu.AppendSeperator()
            mnuOssim = self.popupmenu.Append(self.ID_OSSIM,'&Send to OssimPlanet')
            mnuOssim = self.popupmenu.Append(self.ID_OSSIM2,'&Remove from OssimPlanet')
            #self.popupmenu.AppendSeperator()
            mnuInfo = self.popupmenu.Append(self.ID_INFO,'&Info')

            if pText == 'Vector Map':
                mnuReport = wx.Menu()
                mnuReport.Append(self.ID_AREA, 'Area')
                mnuReport.Append(self.ID_LENGTH, 'Length')
                mnuReport.Append(self.ID_COOR, 'Coordinate')
                self.popupmenu.AppendMenu(wx.ID_ANY, 'Report', mnuReport)
            else:
                mnuReport =self.popupmenu.Append(self.ID_REPORT,'&Report')

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
        cmdflag = None
        parent  =self.GetItemParent(item) 
        if self.GetItemText(parent) == "Raster Map" :
            #print str(self.GetItemText(item))
            cmdflag = 'r.planet.py -a map=' + str(self.GetItemText(item))
        else:
           # child,cookie = self.GetNextChild(item,cookie=1)
            if self.GetItemText(item) == 'colour':
                col=self.GetItemTextColour(item)
            else:
                child,cookie = self.GetFirstChild(item)
                col = self.GetItemTextColour(child)
            if col.IsOk() is True:
                col=str(col)
                col = col.replace('(','')
                col = col.replace(')','')
                col = col.split(',')

                cmdflag = 'v.planet.py -a map=' + str(self.GetItemText(item)) + \
                            ' brush=' + str(col[0].strip()+','+col[1].strip()+','+col[2].strip()) + \
                            ' pen=' + str(col[0].strip()+','+col[1].strip()+','+col[2].strip()) + ' size=' +str('1,1')
                print cmdflag

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
        

    def OnDisplay(self, event):

        item =  event.GetItem()
        pText = self.GetItemText(self.GetItemParent(item)) 
        


class OssimPlanet(Thread):
   def __init__ (self,cmd):
      Thread.__init__(self)
      self.cmd =  cmd
   def run(self):
      os.system(self.cmd)	



