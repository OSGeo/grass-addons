#!/usr/bin/python
 

from urllib2 import Request, urlopen, URLError, HTTPError
import wx
from parse import parsexml
import cStringIO
from image import NewImageFrame

class WMSGUI(wx.Frame):
  
    def __init__(self, parent, title):
        super(WMSGUI, self).__init__(parent, title=title, 
            size=(390, 350))
            
        self.InitUI()
        self.Centre()
        self.Show()     
        
    def InitUI(self):
    	
    
        self.panel = wx.Panel(self)

        self.font = wx.SystemSettings_GetFont(wx.SYS_SYSTEM_FONT)
        self.font.SetPointSize(9)

        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.st1 = wx.StaticText(self.panel, label='URL')
        self.st1.SetFont(self.font)
        self.hbox1.Add(self.st1, flag=wx.RIGHT, border=8)
        self.tc = wx.TextCtrl(self.panel)
        self.hbox1.Add(self.tc, proportion=1)
        self.vbox.Add(self.hbox1, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=10)

        self.vbox.Add((-1, 10))

        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.st2 = wx.StaticText(self.panel, label=':::')
        self.st2.SetFont(self.font)
        self.hbox2.Add(self.st2)
        self.vbox.Add(self.hbox2, flag=wx.LEFT | wx.TOP, border=10)

        self.vbox.Add((-1, 10))

        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.tc2 = wx.TextCtrl(self.panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.hbox3.Add(self.tc2, proportion=1, flag=wx.EXPAND)
        self.vbox.Add(self.hbox3, proportion=1, flag=wx.LEFT|wx.RIGHT|wx.EXPAND, 
            border=10)

        self.vbox.Add((-1, 25))

        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.cb1 = wx.CheckBox(self.panel, label='A')
        self.cb1.SetFont(self.font)
        self.hbox4.Add(self.cb1)
        self.cb2 = wx.CheckBox(self.panel, label='B')
        self.cb2.SetFont(self.font)
        self.hbox4.Add(self.cb2, flag=wx.LEFT, border=10)
        self.cb3 = wx.CheckBox(self.panel, label='C')
        self.cb3.SetFont(self.font)
        self.hbox4.Add(self.cb3, flag=wx.LEFT, border=10)
        self.vbox.Add(self.hbox4, flag=wx.LEFT, border=10)

        self.vbox.Add((-1, 25))

        self.hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn1 = wx.Button(self.panel, label='GetMaps', size=(150, 30))
        self.hbox5.Add(self.btn1)
        self.btn2 = wx.Button(self.panel, label='GetCapabilities', size=(150, 30))
        self.hbox5.Add(self.btn2, flag=wx.LEFT|wx.BOTTOM, border=5)
        self.vbox.Add(self.hbox5, flag=wx.ALIGN_CENTER|wx.CENTER, border=10)
        
        self.btn1.Bind(wx.EVT_BUTTON, self.OnServerManagment)
	self.btn2.Bind(wx.EVT_BUTTON, self.OnGetCapabilities)
	
        self.panel.SetSizer(self.vbox)
        
        self.tc.SetValue('http://www.gisnet.lv/cgi-bin/topo?request=GetCapabilities&service=wms')

    def OnServerManagment(self, event):
        url = self.tc.GetValue()
        url = 'http://www.gisnet.lv/cgi-bin/topo?service=WMS&request=GetMap&version=1.1.1&format=image/png&width=800&height=600&srs=EPSG:4326&layers=Atlants&bbox=-180,0,0,90'
	req = Request(url)
	try:
	    response = urlopen(req)
	    image = response.read()
	    outfile = open('map.png','wb')
	    outfile.write(image)
	    outfile.close()
	    
	    NewImageFrame()
        
	    
	except HTTPError, e:
	    print 'The server couldn\'t fulfill the request.'
	    print 'Error code: ', e.code
	except URLError, e:
	    print 'We failed to reach a server.'
	    print 'Reason: ', e.reason
	except IOError:
       	    print "Image file %s not found" % imageFile
            raise SystemExit
	else:
	    print 'Successful'

    def OnGetCapabilities(self, event):
    	#url = 'http://www.gisnet.lv/cgi-bin/topo?request=GetCapabilities&service=wms'
    	url = self.tc.GetValue()
	req = Request(url)
	try:
	    response = urlopen(req)
	    xml = response.read()
	    #self.statusbar.SetStatusText(xml) 
	    reslist = parsexml(xml)
	    st = ''
	    for res in reslist:
	    	   st = st + res + '\n'
	    self.tc2.SetValue(st) 
	    print xml
	except HTTPError, e:
	    print 'The server couldn\'t fulfill the request.'
	    print 'Error code: ', e.code
	except URLError, e:
	    print 'We failed to reach a server.'
	    print 'Reason: ', e.reason
	else:
	    print 'Successful'
'''
class MyAppsudeep(wx.App):
    def OnInit(self):
        frame = MyToolBar(None, -1, 'toolbar.py')
        frame.Show(True)
        return True
'''
def func():
	app = wx.App()
   	WMSGUI(None, title='WMS')
     	app.MainLoop()
	
	'''

if __name__ == '__main__':
  
    app = wx.App()
    WMSGUI(None, title='WMS')
    app.MainLoop() '''
