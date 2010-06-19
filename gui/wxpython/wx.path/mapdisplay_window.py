"""!
@package mapdisp_window.py

@brief GIS map display canvas, buffered window.

Classes:
 - MapWindow
 - BufferedWindow

(C) 2006-2009 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Michael Barton
@author Jachym Cepicky
@author Martin Landa <landa.martin gmail.com>
"""

import os
import time
import math
import sys
import tempfile
import traceback

import wx

import grass.script as grass

import dbm
import dbm_dialogs
import gdialogs
import gcmd
import utils
import globalvar
import gselect
from debug import Debug
from preferences import globalSettings as UserSettings
from units import ConvertValue as UnitsConvertValue
from mapdisp_window import MapWindow
    
class BufferedWindow(MapWindow, wx.Window):
    """!
    A Buffered window class.

    When the drawing needs to change, you app needs to call the
    UpdateMap() method. Since the drawing is stored in a bitmap, you
    can also save the drawing to file by calling the
    SaveToFile(self,file_name,file_type) method.
    """

    def __init__(self, parent, id,
                 pos = wx.DefaultPosition,
                 size = wx.DefaultSize,
                 style=wx.NO_FULL_REPAINT_ON_RESIZE,
                 Map=None, tree=None, lmgr=None):

        MapWindow.__init__(self, parent, id, pos, size, style,
                           Map, tree, lmgr)
        wx.Window.__init__(self, parent, id, pos, size, style)

        self.Map = Map
        self.tree = tree
        self.lmgr = lmgr    # Layer Manager
        self.counter =0
        self.points = []
        
        #
        # Flags
        #
        self.resize = False # indicates whether or not a resize event has taken place
        self.dragimg = None # initialize variable for map panning

        #
        # Variable for drawing on DC
        #
        self.pen = None      # pen for drawing zoom boxes, etc.
        self.polypen = None  # pen for drawing polylines (measurements, profiles, etc)
        # List of wx.Point tuples defining a polyline (geographical coordinates)
        self.polycoords = []
        # ID of rubber band line
        self.lineid = None
        # ID of poly line resulting from cumulative rubber band lines (e.g. measurement)
        self.plineid = None
        
        #
        # Event bindings
        #
        self.Bind(wx.EVT_PAINT,        self.OnPaint)
        self.Bind(wx.EVT_SIZE,         self.OnSize)
        self.Bind(wx.EVT_IDLE,         self.OnIdle)
        self.Bind(wx.EVT_MOTION,       self.MouseActions)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.MouseActions)
        self.processMouse = True
        
        #
        # Render output objects
        #
        self.mapfile = None   # image file to be rendered
        self.img = ""         # wx.Image object (self.mapfile)
        # used in digitization tool (do not redraw vector map)
        self.imgVectorMap = None
        # decoration overlays
        self.overlays = {}
        # images and their PseudoDC ID's for painting and dragging
        self.imagedict = {}   
        self.select = {}      # selecting/unselecting decorations for dragging
        self.textdict = {}    # text, font, and color indexed by id
        self.currtxtid = None # PseudoDC id for currently selected text

        #
        # Zoom objects
        #
        self.zoomhistory = [] # list of past zoom extents
        self.currzoom = 0 # current set of extents in zoom history being used

        self.zoomtype = 1   # 1 zoom in, 0 no zoom, -1 zoom out
        self.hitradius = 10 # distance for selecting map decorations
        self.dialogOffset = 5 # offset for dialog (e.g. DisplayAttributesDialog)

        # OnSize called to make sure the buffer is initialized.
        # This might result in OnSize getting called twice on some
        # platforms at initialization, but little harm done.
        ### self.OnSize(None)

        self.DefinePseudoDC()
        # redraw all pdc's, pdcTmp layer is redrawn always (speed issue)
        self.redrawAll = True

        # will store an off screen empty bitmap for saving to file
        self._buffer = ''

        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
        self.Bind(wx.EVT_KEY_DOWN , self.OnKeyDown)
        
        # vars for handling mouse clicks
        self.dragid   = -1
        self.lastpos  = (0, 0)

    def OnButtonDClick(self,event):
        precision = int(UserSettings.Get(group = 'projection', key = 'format',
                                             subkey = 'precision'))
        try:
            e, n = self.Pixel2Cell(event.GetPositionTuple())
        except AttributeError:
            return

        self.counter = self.counter + 1
        point =("%.*f|%.*f" %  (precision, e, precision, n))
        self.points.append(point + '|point')
        if self.counter == 2:
            f =open("tmp1",'w')
            for p in self.points:
                f.write("%s\n" % p)
            f.close()

            f =open("tmp2",'w')
            f.write("%d %d %d\n" %(1,1,2) )
            f.close()
 
            command =["g.remove",'vect=vnet_out,startend,tmp_vnet_path']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command =["v.in.ascii",'input=tmp1','output=startend']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command=["v.net", "input=myroads",'points=startend', 'out=vnet_out', 'op=connect', 'thresh=200']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            command=["v.net.path", 'vnet_out','afcol=forward', 'abcol=backward', 'out=tmp_vnet_path','file=tmp2']
            gcmd.CommandThread(command,stdout=None,stderr=None).run()

            self.mapname = 'tmp_vnet_path@' + grass.gisenv()['MAPSET']
            self.cmd= ['d.vect', str("map=" + self.mapname),'col=red','width=2']
            self.Map.AddLayer(type='vector', name=self.mapname, command=self.cmd)
            self.UpdateMap(render=True)
            self.counter =0

    def DefinePseudoDC(self, vdigit = False):
        """!Define PseudoDC class to use

        @vdigit True to use PseudoDC from vdigit
        """
        # create PseudoDC used for background map, map decorations like scales and legends
        self.pdc = self.PseudoDC(vdigit)
        # used for digitization tool
        self.pdcVector = None
        # decorations (region box, etc.)
        self.pdcDec = self.PseudoDC(vdigit)
        # pseudoDC for temporal objects (select box, measurement tool, etc.)
        self.pdcTmp = self.PseudoDC(vdigit)
        
    def PseudoDC(self, vdigit = False):
        """!Create PseudoDC instance"""
        if vdigit:
            PseudoDC = VDigitPseudoDC
        else:
            PseudoDC = wx.PseudoDC
        
        return PseudoDC()
    
    def CheckPseudoDC(self):
        """!Try to draw background
        
        @return True on success
        @return False on failure
        """
        try:
            self.pdc.BeginDrawing()
            self.pdc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            self.pdc.BeginDrawing()
        except StandardError, e:
            traceback.print_exc(file = sys.stderr)
            return False
        
        return True
    
    def Draw(self, pdc, img=None, drawid=None, pdctype='image', coords=[0, 0, 0, 0]):
        """!
        Draws map and overlay decorations
        """
        if drawid == None:
            if pdctype == 'image' and img:
                drawid = self.imagedict[img]
            elif pdctype == 'clear':
                drawid == None
            else:
                drawid = wx.NewId()
        
        if img and pdctype == 'image':
            # self.imagedict[img]['coords'] = coords
            self.select[self.imagedict[img]['id']] = False # ?

        pdc.BeginDrawing()

        if drawid != 99:
            bg = wx.TRANSPARENT_BRUSH
        else:
            bg = wx.Brush(self.GetBackgroundColour())

        pdc.SetBackground(bg)
        
        ### pdc.Clear()

        Debug.msg (5, "BufferedWindow.Draw(): id=%s, pdctype=%s, coord=%s" % \
                       (drawid, pdctype, coords))

        # set PseudoDC id
        if drawid is not None:
            pdc.SetId(drawid)
        
        if pdctype == 'clear': # erase the display
            bg = wx.WHITE_BRUSH
            # bg = wx.Brush(self.GetBackgroundColour())
            pdc.SetBackground(bg)
            pdc.RemoveAll()
            pdc.Clear()
            pdc.EndDrawing()
            
            self.Refresh()
            return

        if pdctype == 'image': # draw selected image
            bitmap = wx.BitmapFromImage(img)
            w,h = bitmap.GetSize()
            pdc.DrawBitmap(bitmap, coords[0], coords[1], True) # draw the composite map
            pdc.SetIdBounds(drawid, wx.Rect(coords[0],coords[1], w, h))

        elif pdctype == 'box': # draw a box on top of the map
            if self.pen:
                pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
                pdc.SetPen(self.pen)
                x2 = max(coords[0],coords[2])
                x1 = min(coords[0],coords[2])
                y2 = max(coords[1],coords[3])
                y1 = min(coords[1],coords[3])
                rwidth = x2-x1
                rheight = y2-y1
                rect = wx.Rect(x1, y1, rwidth, rheight)
                pdc.DrawRectangleRect(rect)
                pdc.SetIdBounds(drawid, rect)
                
        elif pdctype == 'line': # draw a line on top of the map
            if self.pen:
                pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
                pdc.SetPen(self.pen)
                pdc.DrawLinePoint(wx.Point(coords[0], coords[1]),wx.Point(coords[2], coords[3]))
                pdc.SetIdBounds(drawid, wx.Rect(coords[0], coords[1], coords[2], coords[3]))
                # self.ovlcoords[drawid] = coords

        elif pdctype == 'polyline': # draw a polyline on top of the map
            if self.polypen:
                pdc.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
                pdc.SetPen(self.polypen)
                ### pdc.DrawLines(coords)
                if (len(coords) < 2):
                    return
                i = 1
                while i < len(coords):
                    pdc.DrawLinePoint(wx.Point(coords[i-1][0], coords[i-1][1]),
                                      wx.Point(coords[i][0], coords[i][1]))
                    i += 1

                # get bounding rectangle for polyline
                xlist = []
                ylist = []
                if len(coords) > 0:
                    for point in coords:
                        x,y = point
                        xlist.append(x)
                        ylist.append(y)
                    x1=min(xlist)
                    x2=max(xlist)
                    y1=min(ylist)
                    y2=max(ylist)
                    pdc.SetIdBounds(drawid, wx.Rect(x1,y1,x2,y2))
                    # self.ovlcoords[drawid] = [x1,y1,x2,y2]
                    
        elif pdctype == 'point': # draw point
            if self.pen:
                pdc.SetPen(self.pen)
                pdc.DrawPoint(coords[0], coords[1])
                coordsBound = (coords[0] - 5,
                               coords[1] - 5,
                               coords[0] + 5,
                               coords[1] + 5)
                pdc.SetIdBounds(drawid, wx.Rect(coordsBound))
                # self.ovlcoords[drawid] = coords

        elif pdctype == 'text': # draw text on top of map
            if not img['active']:
                return #only draw active text
            if img.has_key('rotation'):
                rotation = float(img['rotation'])
            else:
                rotation = 0.0
            w, h = self.GetFullTextExtent(img['text'])[0:2]
            pdc.SetFont(img['font'])
            pdc.SetTextForeground(img['color'])
            coords, w, h = self.TextBounds(img)
            if rotation == 0:
                pdc.DrawText(img['text'], coords[0], coords[1])
            else:
                pdc.DrawRotatedText(img['text'], coords[0], coords[1], rotation)
            pdc.SetIdBounds(drawid, wx.Rect(coords[0], coords[1], w, h))
            
        pdc.EndDrawing()
        
        self.Refresh()
        
        return drawid

    def TextBounds(self, textinfo):
        """!
        Return text boundary data

        @param textinfo text metadata (text, font, color, rotation)
        @param coords reference point
        """
        if textinfo.has_key('rotation'):
            rotation = float(textinfo['rotation'])
        else:
            rotation = 0.0
        
        coords = textinfo['coords']
        
        Debug.msg (4, "BufferedWindow.TextBounds(): text=%s, rotation=%f" % \
                   (textinfo['text'], rotation))

        self.Update()
        ### self.Refresh()

        self.SetFont(textinfo['font'])

        w, h = self.GetTextExtent(textinfo['text'])

        if rotation == 0:
            coords[2], coords[3] = coords[0] + w, coords[1] + h
            return coords, w, h

        boxh = math.fabs(math.sin(math.radians(rotation)) * w) + h
        boxw = math.fabs(math.cos(math.radians(rotation)) * w) + h
        coords[2] = coords[0] + boxw
        coords[3] = coords[1] + boxh
        
        return coords, boxw, boxh


        
    def OnPaint(self, event):
        """!
        Draw PseudoDC's to buffered paint DC

        self.pdc for background and decorations
        self.pdcVector for vector map which is edited
        self.pdcTmp for temporaly drawn objects (self.polycoords)

        If self.redrawAll is False on self.pdcTmp content is re-drawn
        """
        Debug.msg(4, "BufferedWindow.OnPaint(): redrawAll=%s" % self.redrawAll)
        
        dc = wx.BufferedPaintDC(self, self.buffer)
        
        ### dc.SetBackground(wx.Brush("White"))
        dc.Clear()
        
        # use PrepareDC to set position correctly
        self.PrepareDC(dc)
        
        # create a clipping rect from our position and size
        # and update region
        rgn = self.GetUpdateRegion().GetBox()
        dc.SetClippingRect(rgn)
        
        switchDraw = False
        if self.redrawAll is None:
            self.redrawAll = True
            switchDraw = True
        
        if self.redrawAll: # redraw pdc and pdcVector
            # draw to the dc using the calculated clipping rect
            self.pdc.DrawToDCClipped(dc, rgn)
            
            # draw vector map layer
            if self.pdcVector:
                # decorate with GDDC (transparency)
                try:
                    gcdc = wx.GCDC(dc)
                    self.pdcVector.DrawToDCClipped(gcdc, rgn)
                except NotImplementedError, e:
                    print >> sys.stderr, e
                    self.pdcVector.DrawToDCClipped(dc, rgn)
            
            self.bufferLast = None
        else: # do not redraw pdc and pdcVector
            if self.bufferLast is None:
                # draw to the dc
                self.pdc.DrawToDC(dc)
                
                if self.pdcVector:
                    # decorate with GDDC (transparency)
                    try:
                        gcdc = wx.GCDC(dc)
                        self.pdcVector.DrawToDC(gcdc)
                    except NotImplementedError, e:
                        print >> sys.stderr, e
                        self.pdcVector.DrawToDC(dc)
                        
                # store buffered image
                # self.bufferLast = wx.BitmapFromImage(self.buffer.ConvertToImage())
                self.bufferLast = dc.GetAsBitmap(wx.Rect(0, 0, self.Map.width, self.Map.height))
            
            pdcLast = self.PseudoDC(vdigit = False)
            pdcLast.DrawBitmap(self.bufferLast, 0, 0, False)
            pdcLast.DrawToDC(dc)
        
        # draw decorations (e.g. region box)
        try:
            gcdc = wx.GCDC(dc)
            self.pdcDec.DrawToDC(gcdc)
        except NotImplementedError, e:
            print >> sys.stderr, e
            self.pdcDec.DrawToDC(dc)
        
        # draw temporary object on the foreground
        ### self.pdcTmp.DrawToDCClipped(dc, rgn)
        self.pdcTmp.DrawToDC(dc)
        
        if switchDraw:
            self.redrawAll = False
        
    def OnSize(self, event):
        """!Scale map image so that it is the same size as the Window
        """
        Debug.msg(3, "BufferedWindow.OnSize():")
        
        # set size of the input image
        self.Map.ChangeMapSize(self.GetClientSize())
        # align extent based on center point and display resolution
        # this causes that image is not resized when display windows is resized
        ### self.Map.AlignExtentFromDisplay()
        
        # Make new off screen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        self.buffer = wx.EmptyBitmap(max(1, self.Map.width), max(1, self.Map.height))
        
        # get the image to be rendered
        self.img = self.GetImage()
        
        # update map display
        if self.img and self.Map.width + self.Map.height > 0: # scale image during resize
            self.img = self.img.Scale(self.Map.width, self.Map.height)
            if len(self.Map.GetListOfLayers()) > 0:
                self.UpdateMap()

        # re-render image on idle
        self.resize = True



    def OnIdle(self, event):
        """!Only re-render a composite map image from GRASS during
        idle time instead of multiple times during resizing.
        """
        if self.resize:
            self.UpdateMap(render=True)

        event.Skip()

        
    def GetOverlay(self):
        """!
        Converts rendered overlay files to wx.Image

        Updates self.imagedict

        @return list of images
        """
        imgs = []
        for overlay in self.Map.GetListOfLayers(l_type="overlay", l_active=True):
            if os.path.isfile(overlay.mapfile) and os.path.getsize(overlay.mapfile):
                img = wx.Image(overlay.mapfile, wx.BITMAP_TYPE_ANY)
                self.imagedict[img] = { 'id' : overlay.id,
                                        'layer' : overlay }
                imgs.append(img)

        return imgs

    def GetImage(self):
        """!Converts redered map files to wx.Image

        Updates self.imagedict (id=99)

        @return wx.Image instance (map composition)
        """
        imgId = 99
        if self.Map.mapfile and os.path.isfile(self.Map.mapfile) and \
                os.path.getsize(self.Map.mapfile):
            img = wx.Image(self.Map.mapfile, wx.BITMAP_TYPE_ANY)
        else:
            img = None
        
        self.imagedict[img] = { 'id': imgId }
        
        return img

    def UpdateMap(self, render=True, renderVector=True):
        """!
        Updates the canvas anytime there is a change to the
        underlaying images or to the geometry of the canvas.
        
        @param render re-render map composition
        @param renderVector re-render vector map layer enabled for editing (used for digitizer)
        """
        start = time.clock()
        
        self.resize = False
        
        # if len(self.Map.GetListOfLayers()) == 0:
        #    return False
        
        if self.img is None:
            render = True
        
        #
        # initialize process bar (only on 'render')
        #

        
        #
        # render background image if needed
        #
        
        # update layer dictionary if there has been a change in layers
        if self.tree and self.tree.reorder == True:
            self.tree.ReorderLayers()
        
        # reset flag for auto-rendering
        if self.tree:
            self.tree.rerender = False
        
        if render:
            # update display size
            self.Map.ChangeMapSize(self.GetClientSize())
            windres = True
            self.mapfile = self.Map.Render(force=True, mapWindow=self.parent,
                                           windres=windres)
        else:
            self.mapfile = self.Map.Render(force=False, mapWindow=self.parent)
        
        self.img = self.GetImage() # id=99
            
        #
        # clear pseudoDcs
        #
        for pdc in (self.pdc,
                    self.pdcDec,
                    self.pdcTmp):
            pdc.Clear()
            pdc.RemoveAll()
        
        #
        # draw background map image to PseudoDC
        #
        if not self.img:
            self.Draw(self.pdc, pdctype='clear')
        else:
            try:
                id = self.imagedict[self.img]['id']
            except:
                return False

            self.Draw(self.pdc, self.img, drawid=id)
        
        #
        # render vector map layer
        #
     
        
        #
        # render overlays
        #
        for img in self.GetOverlay():
            # draw any active and defined overlays
            if self.imagedict[img]['layer'].IsActive():
                id = self.imagedict[img]['id']
                self.Draw(self.pdc, img=img, drawid=id,
                          pdctype=self.overlays[id]['pdcType'], coords=self.overlays[id]['coords'])

        for id in self.textdict.keys():
            self.Draw(self.pdc, img=self.textdict[id], drawid=id,
                      pdctype='text', coords=[10, 10, 10, 10])
        
        # optionally draw computational extent box
        #self.DrawCompRegionExtent()
        
        #
        # redraw pdcTmp if needed
        #
        if len(self.polycoords) > 0:
            self.DrawLines(self.pdcTmp)
        


        stop = time.clock()

        
        return True


    def IsInRegion(self, region, refRegion):
        """!
        Test if 'region' is inside of 'refRegion'

        @param region input region
        @param refRegion reference region (e.g. computational region)

        @return True if region is inside of refRegion
        @return False 
        """
        if region['s'] >= refRegion['s'] and \
                region['n'] <= refRegion['n'] and \
                region['w'] >= refRegion['w'] and \
                region['e'] <= refRegion['e']:
            return True

        return False

    def EraseMap(self):
        """!
        Erase the canvas
        """
        self.Draw(self.pdc, pdctype='clear')
                  
        if self.pdcVector:
            self.Draw(self.pdcVector, pdctype='clear')
        
        self.Draw(self.pdcDec, pdctype='clear')
        self.Draw(self.pdcTmp, pdctype='clear')
        
    def DragMap(self, moveto):
        """!
        Drag the entire map image for panning.

        @param moveto dx,dy
        """
        dc = wx.BufferedDC(wx.ClientDC(self))
        dc.SetBackground(wx.Brush("White"))
        dc.Clear()
        
        self.dragimg = wx.DragImage(self.buffer)
        self.dragimg.BeginDrag((0, 0), self)
        self.dragimg.GetImageRect(moveto)
        self.dragimg.Move(moveto)
        
        self.dragimg.DoDrawImage(dc, moveto)
        self.dragimg.EndDrag()
        
    def DragItem(self, id, event):
        """!
        Drag an overlay decoration item
        """
        if id == 99 or id == '' or id == None: return
        Debug.msg (5, "BufferedWindow.DragItem(): id=%d" % id)
        x, y = self.lastpos
        dx = event.GetX() - x
        dy = event.GetY() - y
        self.pdc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        r = self.pdc.GetIdBounds(id)
        ### FIXME in vdigit/pseudodc.i
        if type(r) is list:
            r = wx.Rect(r[0], r[1], r[2], r[3])
        if id > 100: # text dragging
            rtop = (r[0],r[1]-r[3],r[2],r[3])
            r = r.Union(rtop)
            rleft = (r[0]-r[2],r[1],r[2],r[3])
            r = r.Union(rleft)
        self.pdc.TranslateId(id, dx, dy)

        r2 = self.pdc.GetIdBounds(id)
        if type(r2) is list:
            r2 = wx.Rect(r[0], r[1], r[2], r[3])
        if id > 100: # text
            self.textdict[id]['coords'] = r2
        r = r.Union(r2)
        r.Inflate(4,4)
        self.RefreshRect(r, False)
        self.lastpos = (event.GetX(), event.GetY())
                
    def MouseDraw(self, pdc=None, begin=None, end=None):
        """!
        Mouse box or line from 'begin' to 'end'

        If not given from self.mouse['begin'] to self.mouse['end'].

        """
#        self.redrawAll = False
        
        if not pdc:
            return

        if begin is None:
            begin = self.mouse['begin']
        if end is None:
            end   = self.mouse['end']

        Debug.msg (5, "BufferedWindow.MouseDraw(): use=%s, box=%s, begin=%f,%f, end=%f,%f" % \
                       (self.mouse['use'], self.mouse['box'],
                        begin[0], begin[1], end[0], end[1]))

        if self.mouse['box'] == "box":
            boxid = wx.ID_NEW
            mousecoords = [begin[0], begin[1],
                           end[0], end[1]]
            r = pdc.GetIdBounds(boxid)
            if type(r) is list:
                r = wx.Rect(r[0], r[1], r[2], r[3])
            r.Inflate(4, 4)
            try:
                pdc.ClearId(boxid)
            except:
                pass
            self.RefreshRect(r, False)
            pdc.SetId(boxid)
            self.Draw(pdc, drawid=boxid, pdctype='box', coords=mousecoords)
        elif self.mouse['box'] == "line" or self.mouse['box'] == 'point':
            self.lineid = wx.ID_NEW
            mousecoords = [begin[0], begin[1], \
                           end[0], end[1]]
            x1=min(begin[0],end[0])
            x2=max(begin[0],end[0])
            y1=min(begin[1],end[1])
            y2=max(begin[1],end[1])
            r = wx.Rect(x1,y1,x2-x1,y2-y1)
            r.Inflate(4,4)
            try:
                pdc.ClearId(self.lineid)
            except:
                pass
            self.RefreshRect(r, False)
            pdc.SetId(self.lineid)
            self.Draw(pdc, drawid=self.lineid, pdctype='line', coords=mousecoords)

    def DrawLines(self, pdc=None, polycoords=None):
        """!
        Draw polyline in PseudoDC

        Set self.pline to wx.NEW_ID + 1

        polycoords - list of polyline vertices, geographical coordinates
        (if not given, self.polycoords is used)

        """
        if not pdc:
            pdc = self.pdcTmp

        if not polycoords:
            polycoords = self.polycoords
        
        if len(polycoords) > 0:
            self.plineid = wx.ID_NEW + 1
            # convert from EN to XY
            coords = []
            for p in polycoords:
                coords.append(self.Cell2Pixel(p))

            self.Draw(pdc, drawid=self.plineid, pdctype='polyline', coords=coords)
            
            Debug.msg (4, "BufferedWindow.DrawLines(): coords=%s, id=%s" % \
                           (coords, self.plineid))

            return self.plineid

        return -1

    def DrawCross(self, pdc, coords, size, rotation=0,
                  text=None, textAlign='lr', textOffset=(5, 5)):
        """!Draw cross in PseudoDC

        @todo implement rotation

        @param pdc PseudoDC
        @param coord center coordinates
        @param rotation rotate symbol
        @param text draw also text (text, font, color, rotation)
        @param textAlign alignment (default 'lower-right')
        @textOffset offset for text (from center point)
        """
        Debug.msg(4, "BufferedWindow.DrawCross(): pdc=%s, coords=%s, size=%d" % \
                  (pdc, coords, size))
        coordsCross = ((coords[0] - size, coords[1], coords[0] + size, coords[1]),
                       (coords[0], coords[1] - size, coords[0], coords[1] + size))

        self.lineid = wx.NewId()
        for lineCoords in coordsCross:
            self.Draw(pdc, drawid=self.lineid, pdctype='line', coords=lineCoords)

        if not text:
            return self.lineid

        if textAlign == 'ul':
            coord = [coords[0] - textOffset[0], coords[1] - textOffset[1], 0, 0]
        elif textAlign == 'ur':
            coord = [coords[0] + textOffset[0], coords[1] - textOffset[1], 0, 0]
        elif textAlign == 'lr':
            coord = [coords[0] + textOffset[0], coords[1] + textOffset[1], 0, 0]
        else:
            coord = [coords[0] - textOffset[0], coords[1] + textOffset[1], 0, 0]
        
        self.Draw(pdc, img=text,
                  pdctype='text', coords=coord)

        return self.lineid

    def MouseActions(self, event):
        """!
        Mouse motion and button click notifier
        """
        if not self.processMouse:
            return

        # zoom with mouse wheel
        if event.GetWheelRotation() != 0:
            self.OnMouseWheel(event)
            
        # left mouse button pressed
        elif event.LeftDown():
            self.OnLeftDown(event)

        # left mouse button released
        elif event.LeftUp():
            self.OnLeftUp(event)

        # dragging
        elif event.Dragging():
            self.OnDragging(event)

        # double click
        elif event.ButtonDClick():
            self.OnButtonDClick(event)



                
        
    def OnMouseWheel(self, event):
        """!
        Mouse wheel moved
        """
        self.processMouse = False
        current  = event.GetPositionTuple()[:]
        wheel = event.GetWheelRotation()
        Debug.msg (5, "BufferedWindow.MouseAction(): wheel=%d" % wheel)
        # zoom 1/2 of the screen, centered to current mouse position (TODO: settings)
        begin = (current[0] - self.Map.width / 4,
                 current[1] - self.Map.height / 4)
        end   = (current[0] + self.Map.width / 4,
                 current[1] + self.Map.height / 4)
        
        if wheel > 0:
            zoomtype = 1
        else:
            zoomtype = -1

        # zoom
        self.Zoom(begin, end, zoomtype)

        # redraw map
        self.UpdateMap()

        ### self.OnPaint(None)

        # update statusbar
        self.parent.StatusbarUpdate()

        self.Refresh()
        self.processMouse = True
#        event.Skip()

    def OnDragging(self, event):
        """!
        Mouse dragging with left button down
        """
        Debug.msg (5, "BufferedWindow.MouseAction(): Dragging")
        current  = event.GetPositionTuple()[:]
        previous = self.mouse['begin']
        move = (current[0] - previous[0],
                current[1] - previous[1])
        
        digitToolbar = self.parent.toolbars['vdigit']
        
        # dragging or drawing box with left button
        if self.mouse['use'] == 'pan' or \
                event.MiddleIsDown():
            self.DragMap(move)
        
        # dragging decoration overlay item
        elif (self.mouse['use'] == 'pointer' and 
                not digitToolbar and 
                self.dragid != None):
            self.DragItem(self.dragid, event)
        
        # dragging anything else - rubber band box or line
        else:
            if (self.mouse['use'] == 'pointer' and 
                not digitToolbar): return
            self.mouse['end'] = event.GetPositionTuple()[:]
#            digitClass = self.parent.digit
            if (event.LeftIsDown()):
                # draw box only when left mouse button is pressed
                self.MouseDraw(pdc=self.pdcTmp)
        
        # event.Skip()

        
    def OnLeftDown(self, event):
        """!
        Left mouse button pressed
        """
        Debug.msg (5, "BufferedWindow.OnLeftDown(): use=%s" % \
                   self.mouse["use"])

        self.mouse['begin'] = event.GetPositionTuple()[:]
        
        if self.mouse["use"] in ["measure", "profile"]:
            # measure or profile
            if len(self.polycoords) == 0:
                self.mouse['end'] = self.mouse['begin']
                self.polycoords.append(self.Pixel2Cell(self.mouse['begin']))
                self.ClearLines(pdc=self.pdcTmp)
            else:
                self.mouse['begin'] = self.mouse['end']
        elif self.mouse['use'] == 'zoom':
            pass

        #
        # vector digizer
        #
        elif self.mouse["use"] == "pointer" and \
                self.parent.toolbars['vdigit']:
            digitToolbar = self.parent.toolbars['vdigit']
            digitClass   = self.parent.digit
            
            try:
                mapLayer = digitToolbar.GetLayer().GetName()
            except:
                wx.MessageBox(parent=self,
                              message=_("No vector map selected for editing."),
                              caption=_("Vector digitizer"),
                              style=wx.OK | wx.ICON_INFORMATION | wx.CENTRE)
                event.Skip()
                return
            
            if digitToolbar.GetAction() not in ("moveVertex",
                                                "addVertex",
                                                "removeVertex",
                                                "editLine"):
                # set pen
                self.pen = wx.Pen(colour='Red', width=2, style=wx.SHORT_DASH)
                self.polypen = wx.Pen(colour='dark green', width=2, style=wx.SOLID)

            if digitToolbar.GetAction() in ("addVertex",
                                            "removeVertex",
                                            "splitLines"):
                # unselect
                digitClass.driver.SetSelected([])

            if digitToolbar.GetAction() == "addLine":
                self.OnLeftDownVDigitAddLine(event)
            
            elif digitToolbar.GetAction() == "editLine" and \
                    hasattr(self, "vdigitMove"):
                self.OnLeftDownVDigitEditLine(event)

            elif digitToolbar.GetAction() in ("moveLine", 
                                              "moveVertex",
                                              "editLine") and \
                    not hasattr(self, "vdigitMove"):
                self.OnLeftDownVDigitMoveLine(event)

            elif digitToolbar.GetAction() in ("displayAttrs"
                                              "displayCats"):
                self.OnLeftDownVDigitDisplayCA(event)
            
            elif digitToolbar.GetAction() in ("copyCats",
                                              "copyAttrs"):
                self.OnLeftDownVDigitCopyCA(event)
            
            elif digitToolbar.GetAction() == "copyLine":
                self.OnLeftDownVDigitCopyLine(event)
            
            elif digitToolbar.GetAction() == "zbulkLine":
                self.OnLeftDownVDigitBulkLine(event)
            
        elif self.mouse['use'] == 'pointer':
            # get decoration or text id
            self.idlist = []
            self.dragid = ''
            self.lastpos = self.mouse['begin']
            idlist = self.pdc.FindObjects(self.lastpos[0], self.lastpos[1],
                                          self.hitradius)
            if 99 in idlist:
                idlist.remove(99)                             
            if idlist != []:
                self.dragid = idlist[0] #drag whatever is on top
        else:
            pass

        event.Skip()

    def OnLeftUp(self, event):
        """!
        Left mouse button released
        """
        Debug.msg (5, "BufferedWindow.OnLeftUp(): use=%s" % \
                       self.mouse["use"])
        
        self.mouse['end'] = event.GetPositionTuple()[:]
        
        if self.mouse['use'] in ["zoom", "pan"]:
            # set region in zoom or pan
            begin = self.mouse['begin']
            end = self.mouse['end']
            
            if self.mouse['use'] == 'zoom':
                # set region for click (zero-width box)
                if begin[0] - end[0] == 0 or \
                        begin[1] - end[1] == 0:
                    # zoom 1/2 of the screen (TODO: settings)
                    begin = (end[0] - self.Map.width / 4,
                             end[1] - self.Map.height / 4)
                    end   = (end[0] + self.Map.width / 4,
                             end[1] + self.Map.height / 4)
            
            self.Zoom(begin, end, self.zoomtype)

            # redraw map
            self.UpdateMap(render=True)

            # update statusbar
#            self.parent.StatusbarUpdate()

            
        elif (self.mouse['use'] == 'pointer' and 
                self.dragid >= 0):
            # end drag of overlay decoration
            
            if self.dragid < 99 and self.overlays.has_key(self.dragid):
                self.overlays[self.dragid]['coords'] = self.pdc.GetIdBounds(self.dragid)
            elif self.dragid > 100 and self.textdict.has_key(self.dragid):
                self.textdict[self.dragid]['coords'] = self.pdc.GetIdBounds(self.dragid)
            else:
                pass
            self.dragid = None
            self.currtxtid = None
        
    def OnRightDown(self, event):
        """!
        Right mouse button pressed
        """
        Debug.msg (5, "BufferedWindow.OnRightDown(): use=%s" % \
                   self.mouse["use"])
                   
        digitToolbar = self.parent.toolbars['vdigit']
        if digitToolbar:
            digitClass = self.parent.digit
            # digitization tool (confirm action)
            if digitToolbar.GetAction() in ("moveLine",
                                            "moveVertex") and \
                    hasattr(self, "vdigitMove"):

                pFrom = self.vdigitMove['begin']
                pTo = self.Pixel2Cell(event.GetPositionTuple())
                
                move = (pTo[0] - pFrom[0],
                        pTo[1] - pFrom[1])
                
                if digitToolbar.GetAction() == "moveLine":
                    # move line
                    if digitClass.MoveSelectedLines(move) < 0:
                        return
                elif digitToolbar.GetAction() == "moveVertex":
                    # move vertex
                    fid = digitClass.MoveSelectedVertex(pFrom, move)
                    if fid < 0:
                        return

                    self.__geomAttrbUpdate([fid,])
                
                del self.vdigitMove
                
        event.Skip()

    def OnRightUp(self, event):
        """!
        Right mouse button released
        """
        Debug.msg (5, "BufferedWindow.OnRightUp(): use=%s" % \
                   self.mouse["use"])

        digitToolbar = self.parent.toolbars['vdigit']
        if digitToolbar:
            digitClass = self.parent.digit
            # digitization tool (confirm action)
            if digitToolbar.GetAction() == "addLine" and \
                    digitToolbar.GetAction('type') in ["line", "boundary"]:
                # -> add new line / boundary
                try:
                    map = digitToolbar.GetLayer().GetName()
                except:
                    map = None
                    wx.MessageBox(parent=self,
                                  message=_("No vector map selected for editing."),
                                  caption=_("Error"), style=wx.OK | wx.ICON_ERROR | wx.CENTRE)
                    
                if map:
                    # mapcoords = []
                    # xy -> EN
                    # for coord in self.polycoords:
                    #    mapcoords.append(self.Pixel2Cell(coord))
                    if digitToolbar.GetAction('type') == 'line':
                        line = True
                    else:
                        line = False

                    if len(self.polycoords) < 2: # ignore 'one-point' lines
                        return
                    
                    fid = digitClass.AddLine(map, line, self.polycoords)
                    if fid < 0:
                        return
                    
                    position = self.Cell2Pixel(self.polycoords[-1])
                    self.polycoords = []
                    self.UpdateMap(render=False)
                    self.redrawAll = True
                    self.Refresh()
                    
                    # add new record into atribute table
                    if UserSettings.Get(group='vdigit', key="addRecord", subkey='enabled') and \
                            (line is True or \
                                 (not line and fid > 0)):
                        posWindow = self.ClientToScreen((position[0] + self.dialogOffset,
                                                         position[1] + self.dialogOffset))

                        # select attributes based on layer and category
                        cats = { fid : {
                                UserSettings.Get(group='vdigit', key="layer", subkey='value') :
                                    (UserSettings.Get(group='vdigit', key="category", subkey='value'), )
                                }}
                        
                        addRecordDlg = dbm_dialogs.DisplayAttributesDialog(parent=self, map=map,
                                                                           cats=cats,
                                                                           pos=posWindow,
                                                                           action="add")

                        self.__geomAttrb(fid, addRecordDlg, 'length', digitClass,
                                         digitToolbar.GetLayer())
                        # auto-placing centroid
                        self.__geomAttrb(fid, addRecordDlg, 'area', digitClass,
                                         digitToolbar.GetLayer())
                        self.__geomAttrb(fid, addRecordDlg, 'perimeter', digitClass,
                                         digitToolbar.GetLayer())

                        if addRecordDlg.mapDBInfo and \
                               addRecordDlg.ShowModal() == wx.ID_OK:
                            sqlfile = tempfile.NamedTemporaryFile(mode="w")
                            for sql in addRecordDlg.GetSQLString():
                                sqlfile.file.write(sql + ";\n")
                            sqlfile.file.flush()
                            gcmd.RunCommand('db.execute',
                                            parent = True,
                                            quiet = True,
                                            input = sqlfile.name)
                        
                        if addRecordDlg.mapDBInfo:
                            self.__updateATM()
            
            elif digitToolbar.GetAction() == "deleteLine":
                # -> delete selected vector features
                if digitClass.DeleteSelectedLines() < 0:
                    return
                self.__updateATM()
            elif digitToolbar.GetAction() == "splitLine":
                # split line
                if digitClass.SplitLine(self.Pixel2Cell(self.mouse['begin'])) < 0:
                    return
            elif digitToolbar.GetAction() == "addVertex":
                # add vertex
                fid = digitClass.AddVertex(self.Pixel2Cell(self.mouse['begin']))
                if fid < 0:
                    return
            elif digitToolbar.GetAction() == "removeVertex":
                # remove vertex
                fid = digitClass.RemoveVertex(self.Pixel2Cell(self.mouse['begin']))
                if fid < 0:
                    return
                self.__geomAttrbUpdate([fid,])
            elif digitToolbar.GetAction() in ("copyCats", "copyAttrs"):
                try:
                    if digitToolbar.GetAction() == 'copyCats':
                        if digitClass.CopyCats(self.copyCatsList,
                                               self.copyCatsIds, copyAttrb=False) < 0:
                            return
                    else:
                        if digitClass.CopyCats(self.copyCatsList,
                                               self.copyCatsIds, copyAttrb=True) < 0:
                            return
                    
                    del self.copyCatsList
                    del self.copyCatsIds
                except AttributeError:
                    pass
                
                self.__updateATM()
                
            elif digitToolbar.GetAction() == "editLine" and \
                    hasattr(self, "vdigitMove"):
                line = digitClass.driver.GetSelected()
                if digitClass.EditLine(line, self.polycoords) < 0:
                    return
                
                del self.vdigitMove
                
            elif digitToolbar.GetAction() == "flipLine":
                if digitClass.FlipLine() < 0:
                    return
            elif digitToolbar.GetAction() == "mergeLine":
                if digitClass.MergeLine() < 0:
                    return
            elif digitToolbar.GetAction() == "breakLine":
                if digitClass.BreakLine() < 0:
                    return
            elif digitToolbar.GetAction() == "snapLine":
                if digitClass.SnapLine() < 0:
                    return
            elif digitToolbar.GetAction() == "connectLine":
                if len(digitClass.driver.GetSelected()) > 1:
                    if digitClass.ConnectLine() < 0:
                        return
            elif digitToolbar.GetAction() == "copyLine":
                if digitClass.CopyLine(self.copyIds) < 0:
                    return
                del self.copyIds
                if self.layerTmp:
                    self.Map.DeleteLayer(self.layerTmp)
                    self.UpdateMap(render=True, renderVector=False)
                del self.layerTmp

            elif digitToolbar.GetAction() == "zbulkLine" and len(self.polycoords) == 2:
                pos1 = self.polycoords[0]
                pos2 = self.polycoords[1]

                selected = digitClass.driver.GetSelected()
                dlg = VDigitZBulkDialog(parent=self, title=_("Z bulk-labeling dialog"),
                                        nselected=len(selected))
                if dlg.ShowModal() == wx.ID_OK:
                    if digitClass.ZBulkLines(pos1, pos2, dlg.value.GetValue(),
                                             dlg.step.GetValue()) < 0:
                        return
                self.UpdateMap(render=False, renderVector=True)
            elif digitToolbar.GetAction() == "typeConv":
                # -> feature type conversion
                # - point <-> centroid
                # - line <-> boundary
                if digitClass.TypeConvForSelectedLines() < 0:
                    return

            if digitToolbar.GetAction() != "addLine":
                # unselect and re-render
                digitClass.driver.SetSelected([])
                self.polycoords = []
                self.UpdateMap(render=False)

            self.redrawAll = True
            self.Refresh()
            
        event.Skip()

    def OnMiddleDown(self, event):
        """!
        Middle mouse button pressed
        """
        self.mouse['begin'] = event.GetPositionTuple()[:]
        
        digitToolbar = self.parent.toolbars['vdigit']
        # digitization tool
        if self.mouse["use"] == "pointer" and digitToolbar:
            digitClass = self.parent.digit
            if (digitToolbar.GetAction() == "addLine" and \
                    digitToolbar.GetAction('type') in ["line", "boundary"]) or \
                    digitToolbar.GetAction() == "editLine":
                # add line or boundary -> remove last point from the line
                try:
                    removed = self.polycoords.pop()
                    Debug.msg(4, "BufferedWindow.OnMiddleDown(): polycoords_poped=%s" % \
                                  [removed,])

                    self.mouse['begin'] = self.Cell2Pixel(self.polycoords[-1])
                except:
                    pass

                if digitToolbar.GetAction() == "editLine":
                    # remove last vertex & line
                    if len(self.vdigitMove['id']) > 1:
                        self.vdigitMove['id'].pop()

                self.UpdateMap(render=False, renderVector=False)

            elif digitToolbar.GetAction() in ["deleteLine", "moveLine", "splitLine",
                                              "addVertex", "removeVertex", "moveVertex",
                                              "copyCats", "flipLine", "mergeLine",
                                              "snapLine", "connectLine", "copyLine",
                                              "queryLine", "breakLine", "typeConv"]:
                # varios tools -> unselected selected features
                digitClass.driver.SetSelected([])
                if digitToolbar.GetAction() in ["moveLine", "moveVertex", "editLine"] and \
                        hasattr(self, "vdigitMove"):

                    del self.vdigitMove
                    
                elif digitToolbar.GetAction() == "copyCats":
                    try:
                        del self.copyCatsList
                        del self.copyCatsIds
                    except AttributeError:
                        pass
                
                elif digitToolbar.GetAction() == "copyLine":
                    del self.copyIds
                    if self.layerTmp:
                        self.Map.DeleteLayer(self.layerTmp)
                        self.UpdateMap(render=True, renderVector=False)
                    del self.layerTmp

                self.polycoords = []
                self.UpdateMap(render=False) # render vector

            elif digitToolbar.GetAction() == "zbulkLine":
                # reset polyline
                self.polycoords = []
                digitClass.driver.SetSelected([])
                self.UpdateMap(render=False)
            
            self.redrawAll = True

    def OnMiddleUp(self, event):
        """!
        Middle mouse button released
        """
        self.mouse['end'] = event.GetPositionTuple()[:]
        
        # set region in zoom or pan
        begin = self.mouse['begin']
        end = self.mouse['end']
        
        self.Zoom(begin, end, 0) # no zoom
        
        # redraw map
        self.UpdateMap(render=True)
        
        # update statusbar
        self.parent.StatusbarUpdate()
        
    def ClearLines(self, pdc=None):
        """!
        Clears temporary drawn lines from PseudoDC
        """
        if not pdc:
            pdc=self.pdcTmp
        try:
            pdc.ClearId(self.lineid)
            pdc.RemoveId(self.lineid)
        except:
            pass

        try:
            pdc.ClearId(self.plineid)
            pdc.RemoveId(self.plineid)
        except:
            pass

        Debug.msg(4, "BufferedWindow.ClearLines(): lineid=%s, plineid=%s" %
                  (self.lineid, self.plineid))

        ### self.Refresh()

        return True

    def Pixel2Cell(self, (x, y)):
        """!
        Convert image coordinates to real word coordinates

        Input : int x, int y
        Output: float x, float y
        """

        try:
            x = int(x)
            y = int(y)
        except:
            return None

        if self.Map.region["ewres"] > self.Map.region["nsres"]:
            res = self.Map.region["ewres"]
        else:
            res = self.Map.region["nsres"]

        w = self.Map.region["center_easting"] - (self.Map.width / 2) * res
        n = self.Map.region["center_northing"] + (self.Map.height / 2) * res

        east  = w + x * res
        north = n - y * res

        # extent does not correspond with whole map canvas area...
        # east  = self.Map.region['w'] + x * self.Map.region["ewres"]
        # north = self.Map.region['n'] - y * self.Map.region["nsres"]

        return (east, north)

    def Cell2Pixel(self, (east, north)):
        """!
        Convert real word coordinates to image coordinates
        """

        try:
            east  = float(east)
            north = float(north)
        except:
            return None

        if self.Map.region["ewres"] > self.Map.region["nsres"]:
            res = self.Map.region["ewres"]
        else:
            res = self.Map.region["nsres"]

        w = self.Map.region["center_easting"] - (self.Map.width / 2) * res
        n = self.Map.region["center_northing"] + (self.Map.height / 2) * res

        # x = int((east  - w) / res)
        # y = int((n - north) / res)

        x = (east  - w) / res
        y = (n - north) / res

        return (x, y)

    def Zoom(self, begin, end, zoomtype):
        """!
        Calculates new region while (un)zoom/pan-ing
        """
        x1, y1 = begin
        x2, y2 = end
        newreg = {}

        # threshold - too small squares do not make sense
        # can only zoom to windows of > 5x5 screen pixels
        if abs(x2-x1) > 5 and abs(y2-y1) > 5 and zoomtype != 0:

            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            # zoom in
            if zoomtype > 0:
                newreg['w'], newreg['n'] = self.Pixel2Cell((x1, y1))
                newreg['e'], newreg['s'] = self.Pixel2Cell((x2, y2))

            # zoom out
            elif zoomtype < 0:
                newreg['w'], newreg['n'] = self.Pixel2Cell((-x1 * 2, -y1 * 2))
                newreg['e'], newreg['s'] = self.Pixel2Cell((self.Map.width  + 2 * \
                                                                (self.Map.width  - x2),
                                                            self.Map.height + 2 * \
                                                                (self.Map.height - y2)))
        # pan
        elif zoomtype == 0:
            dx = x1 - x2
            dy = y1 - y2
            newreg['w'], newreg['n'] = self.Pixel2Cell((dx, dy))
            newreg['e'], newreg['s'] = self.Pixel2Cell((self.Map.width  + dx,
                                                        self.Map.height + dy))

        # if new region has been calculated, set the values
        if newreg != {}:
            # LL locations
            if self.parent.Map.projinfo['proj'] == 'll':
                if newreg['n'] > 90.0:
                    newreg['n'] = 90.0
                if newreg['s'] < -90.0:
                    newreg['s'] = -90.0
            
            ce = newreg['w'] + (newreg['e'] - newreg['w']) / 2
            cn = newreg['s'] + (newreg['n'] - newreg['s']) / 2
            
            if hasattr(self, "vdigitMove"):
                # xo = self.Cell2Pixel((self.Map.region['center_easting'], self.Map.region['center_northing']))
                # xn = self.Cell2Pixel(ce, cn))
                tmp = self.Pixel2Cell(self.mouse['end'])
            
            # calculate new center point and display resolution
            self.Map.region['center_easting'] = ce
            self.Map.region['center_northing'] = cn
            self.Map.region["ewres"] = (newreg['e'] - newreg['w']) / self.Map.width
            self.Map.region["nsres"] = (newreg['n'] - newreg['s']) / self.Map.height
            self.Map.AlignExtentFromDisplay()

            if hasattr(self, "vdigitMove"):
                tmp1 = self.mouse['end']
                tmp2 = self.Cell2Pixel(self.vdigitMove['begin'])
                dx = tmp1[0] - tmp2[0]
                dy = tmp1[1] - tmp2[1]
                self.vdigitMove['beginDiff'] = (dx, dy)
                for id in self.vdigitMove['id']:
                    self.pdcTmp.RemoveId(id)
            
            self.ZoomHistory(self.Map.region['n'], self.Map.region['s'],
                             self.Map.region['e'], self.Map.region['w'])

        if self.redrawAll is False:
            self.redrawAll = True

    def ZoomBack(self):
        """!Zoom to previous extents in zoomhistory list
        """
        zoom = list()
        
        if len(self.zoomhistory) > 1:
            self.zoomhistory.pop()
            zoom = self.zoomhistory[-1]
        
        # disable tool if stack is empty
        if len(self.zoomhistory) < 2: # disable tool
            if self.parent.GetName() == 'MapWindow':
                toolbar = self.parent.toolbars['map']
            elif self.parent.GetName() == 'GRMapWindow':
                toolbar = self.parent.toolbars['georect']
            
            toolbar.Enable('zoomback', enable = False)
        
        # zoom to selected region
        self.Map.GetRegion(n = zoom[0], s = zoom[1],
                           e = zoom[2], w = zoom[3],
                           update = True)
        # update map
        self.UpdateMap()
        

    def ZoomHistory(self, n, s, e, w):
        """!
        Manages a list of last 10 zoom extents

        @param n,s,e,w north, south, east, west

        @return removed history item if exists (or None)
        """
        removed = None
        self.zoomhistory.append((n,s,e,w))
        
        if len(self.zoomhistory) > 10:
            removed = self.zoomhistory.pop(0)
        
        if removed:
            Debug.msg(4, "BufferedWindow.ZoomHistory(): hist=%s, removed=%s" %
                      (self.zoomhistory, removed))
        else:
            Debug.msg(4, "BufferedWindow.ZoomHistory(): hist=%s" %
                      (self.zoomhistory))
        
        # update toolbar
        if len(self.zoomhistory) > 1:
            enable = True
        else:
            enable = False
        
        if self.parent.GetName() == 'MapWindow':
            toolbar = self.parent.toolbars['map']
        elif self.parent.GetName() == 'GRMapWindow':
            toolbar = self.parent.toolbars['georect']
        
        toolbar.Enable('zoomback', enable)
        
        return removed

    def ResetZoomHistory(self):
        """!Reset zoom history"""
        self.zoomhistory = list()
        
        
    def ZoomToMap(self, layers = None, ignoreNulls = False, render = True):
        """!
        Set display extents to match selected raster
        or vector map(s).

        @param layer list of layers to be zoom to
        @param ignoreNulls True to ignore null-values
        @param render True to re-render display
        """
        zoomreg = {}

        if not layers:
            layers = self.GetSelectedLayer(multi = True)
        
        if not layers:
            return
        
        rast = []
        vect = []
        updated = False
        for l in layers:
            # only raster/vector layers are currently supported
            if l.type == 'raster':
                rast.append(l.name)
            elif l.type == 'vector':
                digitToolbar = self.parent.toolbars['vdigit']
                if digitToolbar and digitToolbar.GetLayer() == l:
                    w, s, b, e, n, t = self.parent.digit.driver.GetMapBoundingBox()
                    self.Map.GetRegion(n=n, s=s, w=w, e=e,
                                       update=True)
                    updated = True
                else:
                    vect.append(l.name)
        
        if not updated:
            self.Map.GetRegion(rast = rast,
                               vect = vect,
                               update = True)
        
        self.ZoomHistory(self.Map.region['n'], self.Map.region['s'],
                         self.Map.region['e'], self.Map.region['w'])
        
        if render:
            self.UpdateMap()


        
