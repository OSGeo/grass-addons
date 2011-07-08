import wx
import  cStringIO

class ImagePanel(wx.Panel):
  def displayImage():
    try:
        imageFile = 'map.png'
        data = open(imageFile, "rb").read()
        stream = cStringIO.StringIO(data)
        bmp = wx.BitmapFromImage( wx.ImageFromStream( stream ))
        wx.StaticBitmap(self, -1, bmp, (5, 5))
    except IOError:
        print "Image file %s not found" % imageFile
        raise SystemExit
        
def NewImageFrame(): 
    app = wx.PySimpleApp()
    frame = wx.Frame(None, -1, "Map Display", size = (400, 300))
    ImagePanel(frame1,-1)
    frame.Show(1)
    app.MainLoop()
