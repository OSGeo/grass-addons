import wx
import  cStringIO

class ImagePanel(wx.Panel):
   def __init__(self, parent, id):
    wx.Panel.__init__(self, parent, id)
    try:
        imageFile = 'map.png'
        data = open(imageFile, "rb").read()
        stream = cStringIO.StringIO(data) 
        bmp = wx.BitmapFromImage( wx.ImageFromStream( stream )) 
        wx.StaticBitmap(self, -1, bmp, (5, 5))          
        png = wx.Image(imageFile, wx.BITMAP_TYPE_ANY).ConvertToBitmap() 
        wx.StaticBitmap(self, -1, png, (10 + png.GetWidth(), 5), (png.GetWidth(), png.GetHeight()))
    except IOError:
        print "Image file %s not found" % imageFile
        raise SystemExit

def NewImageFrame(): 
    NewWindowapp = wx.PySimpleApp()
    NewWindowframe = wx.Frame(None, -1, "Map Display", size = (400, 300))
    ImagePanel(NewWindowframe,-1)
    NewWindowframe.Show(1)
    NewWindowapp.MainLoop()
