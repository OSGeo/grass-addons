import wx
import wx_utils as wx_utils

class RightTree(wx.TreeCtrl):

    def __init__(self, parent, id,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style= wx.TR_HIDE_ROOT|wx.TR_HAS_BUTTONS):

        wx.TreeCtrl.__init__(self, parent, id, pos, size, style)
        self.itemFont2 = wx.Font(pointSize=9,weight=0, family=wx.FONTFAMILY_DEFAULT ,style=wx.FONTSTYLE_ITALIC)


    def PopulateDisplay(self):
        root1 = self.AddRoot('root')
        node_raster2 = self.AppendItem(root1, "Display 0")
        node_vector2 = self.AppendItem(root1, "Display 1")
        node_dbf2 = self.AppendItem(root1, "Display 2")
        treeNodes2 = [node_raster2,node_vector2,node_dbf2]
        #Nodes with no children are given an italic type font
        for node in treeNodes2: 
            if not self.ItemHasChildren(node):
	            if self.GetItemText(node) == 'Display 0':
		            tmp_item2 = self.AppendItem(node, "No raster maps found.")
	            elif self.GetItemText(node) == 'Display 1':
		            tmp_item2 = self.AppendItem(node, "No vector maps found.")
	            elif self.GetItemText(node) == 'Display 2':
		            tmp_item2 = self.AppendItem(node, "No DBF files found.")
	            self.SetItemFont(tmp_item2,self.itemFont2)

        #self.pg_panel = wx.Panel(self.gm_cb, id=wx.ID_ANY, style= wx.EXPAND)
        #self.gm_cb.AddPage(self.pg_panel, text="Display "+ str(self.disp_idx + 1), select = True)
        #self.curr_page = self.gm_cb.GetCurrentPage()
        

        # create layer tree (tree control for managing GIS layers)  and put on new notebook page


