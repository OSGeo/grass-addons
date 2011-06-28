#!/usr/bin/python

# toolbar.py

import wx
from urllib2 import Request, urlopen, URLError, HTTPError

class MyToolBar(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(350, 250))

        vbox = wx.BoxSizer(wx.VERTICAL)
        toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        toolbar.AddSimpleTool(1, wx.Image('/home/sudeep/Icons/default.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Server Managment', '')
        toolbar.AddSimpleTool(2, wx.Image('/home/sudeep/Icons/default.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Get Capabilities', '')
        toolbar.AddSimpleTool(3, wx.Image('/home/sudeep/Icons/default.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'None', '')
        toolbar.AddSeparator()
        toolbar.AddSimpleTool(4, wx.Image('/home/sudeep/Icons/default.png', wx.BITMAP_TYPE_PNG).ConvertToBitmap(), 'Exit', '')
        toolbar.Realize()
        vbox.Add(toolbar, 0, border=5)
        self.SetSizer(vbox)
        self.statusbar = self.CreateStatusBar()
        self.Centre()

        self.Bind(wx.EVT_TOOL, self.OnServerManagment, id=1)
        self.Bind(wx.EVT_TOOL, self.OnGetCapabilities, id=2)
        self.Bind(wx.EVT_TOOL, self.OnNone, id=3)
        self.Bind(wx.EVT_TOOL, self.OnExit, id=4)

    def OnServerManagment(self, event):
        self.statusbar.SetStatusText('New Command')

    def OnGetCapabilities(self, event):
    	url = 'http://www.gisnet.lv/cgi-bin/topo?request=GetCapabilities&service=wms'
	req = Request(url)
	try:
	    response = urlopen(req)
	    xml = response.read()
	    self.statusbar.SetStatusText(xml) 
	    
	except HTTPError, e:
	    print 'The server couldn\'t fulfill the request.'
	    print 'Error code: ', e.code
	except URLError, e:
	    print 'We failed to reach a server.'
	    print 'Reason: ', e.reason
	else:
	    print 'Successful'



    def OnNone(self, event):
        self.statusbar.SetStatusText('Save Command')

    def OnExit(self, event):
        self.Close()

class MyAppsudeep(wx.App):
    def OnInit(self):
        frame = MyToolBar(None, -1, 'toolbar.py')
        frame.Show(True)
        return True

def func():
	app = MyAppsudeep(0)
	app.MainLoop()


