"""!
@package vdigit.mapwindow

@brief Map display canvas for wxGUI raster digitizer

Classes:
 - mapwindow::RDigitWindow

(C) 2011 by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Mohammed Rashad <rashadkm gmail.com>
"""

import wx

from core.gcmd import RunCommand, GMessage, GError
from core.debug import Debug
from mapdisp.mapwindow import BufferedWindow
from core.settings import UserSettings
from core.utils import ListOfCatsToRange
from core.globalvar import QUERYLAYER


class Circle:
    def __init__(self, pt, r):
        self.point = pt
        self.radius = r


class RDigitWindow(BufferedWindow):
    """!A Buffered window extended for raster digitizer."""

    def __init__(
        self,
        parent,
        giface,
        Map,
        frame,
        id=wx.ID_ANY,
        tree=None,
        lmgr=None,
        style=wx.NO_FULL_REPAINT_ON_RESIZE,
        **kwargs,
    ):
        BufferedWindow.__init__(
            self,
            parent=parent,
            giface=giface,
            id=id,
            Map=Map,
            frame=frame,
            tree=tree,
            style=style,
            **kwargs,
        )
        self.lmgr = lmgr
        self.pdcVector = wx.PseudoDC()
        self.toolbar = self.parent.GetToolbar("rdigit")
        self.digit = None  # wxvdigit.IVDigit
        self.existingCoords = list()
        self.polygons = list()
        self.circles = list()
        self.idx = wx.ID_NEW + 1
        self.selectid = None
        self.selectid_circle = None
        self.idxCats = dict()
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def SetToolbar(self, toolbar):
        """!Set up related toolbar"""
        self.toolbar = toolbar

    def _onMotion(self, coord, precision):
        """!Track mouse motion and update statusbar (see self.Motion)

        @parem coord easting, northing
        @param precision formatting precision
        """
        e, n = coord

        if (
            self.toolbar.GetAction() != "addLine"
            or self.toolbar.GetAction("type") not in ("line", "boundary")
            or len(self.polycoords) == 0
        ):
            return False

        # for linear feature show segment and total length
        distance_seg = self.Distance(self.polycoords[-1], (e, n), screen=False)[0]
        distance_tot = distance_seg
        for idx in range(1, len(self.polycoords)):
            distance_tot += self.Distance(
                self.polycoords[idx - 1], self.polycoords[idx], screen=False
            )[0]
        self.parent.SetStatusText(
            "%.*f, %.*f (seg: %.*f; tot: %.*f)"
            % (
                precision,
                e,
                precision,
                n,
                precision,
                distance_seg,
                precision,
                distance_tot,
            ),
            0,
        )

        return True

    def OnKeyDown(self, event):
        """!Key pressed"""
        shift = event.ShiftDown()
        kc = event.GetKeyCode()

        event = None
        if not shift:
            if kc == ord("P"):
                event = wx.CommandEvent(winid=self.toolbar.addPoint)
                tool = self.toolbar.OnAddPoint
            elif kc == ord("L"):
                event = wx.CommandEvent(winid=self.toolbar.addLine)
                tool = self.toolbar.OnAddLine
        if event:
            self.toolbar.OnTool(event)
            self.selectid = None
            tool(event)

    def DrawLines2(self, plineid, pdc=None, polycoords=None):
        """!Draw polyline in PseudoDC

        Set self.pline to wx.NEW_ID + 1

        polycoords - list of polyline vertices, geographical coordinates
        (if not given, self.polycoords is used)
        """
        if not pdc:
            pdc = self.pdcTmp

        if not polycoords:
            polycoords = self.polycoords

        if len(polycoords) > 0:
            coords = []
            for p in polycoords:
                coords.append(self.Cell2Pixel(p))

            self.Draw(pdc, drawid=plineid, pdctype="polyline", coords=coords)

            Debug.msg(
                2, "BufferedWindow.DrawLines2(): coords=%s, id=%s" % (coords, plineid)
            )

            return plineid

        return -1

    def _updateMap(self):
        if not self.toolbar or not self.toolbar.GetMapName():
            return

        self.pdcVector.RemoveAll()

        for poly in self.polygons:
            idx = poly.keys()[0]
            # print idx
            self.pdcVector.SetId(idx)
            # if self.selectid:
            # if poly.has_key(self.selectid):
            # print poly[self.selectid]
            if idx != self.selectid:
                self.pen = self.polypen = wx.Pen(colour=wx.GREEN, width=2)
            else:
                self.pen = self.polypen = wx.Pen(colour=wx.RED, width=2)

            self.DrawLines2(idx, pdc=self.pdcVector, polycoords=poly[idx])

        # print self.circles
        for circle in self.circles:
            idx = circle.keys()[0]
            C = circle[idx]

            if idx != self.selectid_circle:
                self.pen = self.polypen = wx.Pen(colour=wx.GREEN, width=2)
            else:
                self.pen = self.polypen = wx.Pen(colour=wx.RED, width=2)

            self.pdcVector.BeginDrawing()
            self.pdcVector.SetBrush(wx.Brush(wx.CYAN, wx.TRANSPARENT))
            self.pdcVector.SetPen(self.pen)
            self.pdcVector.SetId(idx)
            self.pdcVector.DrawCircle(C.point[0], C.point[1], C.radius)
            self.pdcVector.EndDrawing()
            self.Refresh()

        item = None
        if self.tree:
            try:
                item = self.tree.FindItemByData("maplayer", self.toolbar.GetMapName())
            except TypeError:
                pass

        # translate tmp objects (pointer position)
        if self.toolbar.GetAction() == "moveLine" and hasattr(self, "moveInfo"):
            if "beginDiff" in self.moveInfo:
                # move line
                for id in self.moveInfo["id"]:
                    self.pdcTmp.TranslateId(
                        id, self.moveInfo["beginDiff"][0], self.moveInfo["beginDiff"][1]
                    )
                del self.moveInfo["beginDiff"]

    def OnLeftDownAddLine(self, event):
        """!Left mouse button pressed - add new feature"""
        try:
            mapLayer = self.toolbar.GetMapName()
        except:
            return

        if self.toolbar.GetAction("type") in ["point", "centroid"]:
            # add new point / centroiud
            east, north = self.Pixel2Cell(self.mouse["begin"])
            nfeat, fids = self.digit.AddFeature(
                self.toolbar.GetAction("type"), [(east, north)]
            )
            # if nfeat < 1:
            # return

            self.UpdateMap(render=False)  # redraw map

        elif self.toolbar.GetAction("type") in ["line", "boundary", "area"]:
            # add new point to the line
            self.polycoords.append(self.Pixel2Cell(event.GetPositionTuple()[:]))
            self.DrawLines(pdc=self.pdcTmp)

    def _onLeftDown(self, event):
        """!Left mouse button donw - raster digitizer various actions"""
        mapLayer = self.toolbar.GetMapName()
        if not mapLayer:
            GError(parent=self, message=_("No raster map selected for editing."))
            event.Skip()
            return

        action = self.toolbar.GetAction()
        # print action
        if not action:
            GMessage(
                parent=self,
                message=_(
                    "Nothing to do. " "Choose appropriate tool from digitizer toolbar."
                ),
            )
            event.Skip()
            return

        # set pen
        self.pen = wx.Pen(
            colour=UserSettings.Get(
                group="vdigit", key="symbol", subkey=["newSegment", "color"]
            ),
            width=2,
            style=wx.SHORT_DASH,
        )
        self.polypen = wx.Pen(
            colour=UserSettings.Get(
                group="vdigit", key="symbol", subkey=["newLine", "color"]
            ),
            width=2,
            style=wx.SOLID,
        )

        if action == "addLine":
            self.OnLeftDownAddLine(event)

        elif action == "deleteCircle":
            # print "delete:Circle"
            x, y = event.GetPositionTuple()
            ids = self.pdcVector.FindObjects(x, y)
            # print ids
            if len(ids) > 0:
                self.selectid_circle = ids[0]
            else:
                self.selectid_circle = None

            ids = []
            self.polycoords = []

        elif action == "addCircle":
            if len(self.polycoords) < 1:  # ignore 'one-point' lines
                self.polycoords.append(event.GetPositionTuple()[:])

    def OnLeftUpVarious(self, event):
        """!Left mouse button released - raster digitizer various
        actions
        """
        pos1 = self.Pixel2Cell(self.mouse["begin"])
        pos2 = self.Pixel2Cell(self.mouse["end"])

        nselected = 0
        action = self.toolbar.GetAction()

        if action in ("deleteLine", "deleteCircle", "deleteArea"):

            if action in ["deleteArea", "deleteLine"]:

                x, y = event.GetPositionTuple()
                ids = self.pdcVector.FindObjectsByBBox(x, y)
                if len(ids) > 0:
                    self.selectid = ids[0]
                else:
                    self.selectid = None

                ids = []
                self.polycoords = []
                self.UpdateMap(render=False)

    def _onLeftUp(self, event):
        """!Left mouse button released"""

        # eliminate initial mouse moving efect
        self.mouse["begin"] = self.mouse["end"]

        action = self.toolbar.GetAction()

        if action in ("deleteLine", "deleteArea", "deleteCircle"):
            self.OnLeftUpVarious(event)

        elif action == "addCircle":
            if len(self.polycoords) > 0:  # ignore 'one-point' lines

                beginpt = self.polycoords[0]
                endpt = event.GetPositionTuple()[:]
                dist, (north, east) = self.Distance(beginpt, endpt, False)
                # print dist
                circle = dict()
                c = Circle(beginpt, dist)
                circle[self.idx] = c
                self.idx = self.idx + 1
                self.circles.append(circle)

                self._updateMap()
                self.polycoords = []

    def _onRightDown(self, event):
        # digitization tool (confirm action)
        action = self.toolbar.GetAction()

    def _onRightUp(self, event):
        """!Right mouse button released (confirm action)"""
        action = self.toolbar.GetAction()

        if action == "addLine" and self.toolbar.GetAction("type") in [
            "line",
            "boundary",
            "area",
        ]:
            # -> add new line / boundary
            mapName = self.toolbar.GetMapName()
            if not mapName:
                GError(parent=self, message=_("No raster map selected for editing."))
                return

            if mapName:
                if len(self.polycoords) < 2:  # ignore 'one-point' lines
                    return

                self.idxCats[self.idx] = self.digit.AddFeature(
                    self.toolbar.GetAction("type"), self.polycoords
                )
                if self.toolbar.GetAction("type") == "boundary":
                    x0, y0 = self.polycoords[0]
                    for coord in self.polycoords:
                        x, y = coord  # self.Cell2Pixel(coord)
                        c = wx.Point(x, y)
                        self.existingCoords.append(c)

                    self.existingCoords.append(wx.Point(x0, y0))
                    coordIdx = dict()
                    coordIdx[self.idx] = self.existingCoords
                    self.polygons.append(coordIdx)
                    self.idx = self.idx + 1
                    self.existingCoords = []

                if self.toolbar.GetAction("type") == "line":
                    for coord in self.polycoords:
                        x, y = coord  # self.Cell2Pixel(coord)
                        c = wx.Point(x, y)
                        self.existingCoords.append(c)

                    coordIdx = dict()
                    coordIdx[self.idx] = self.existingCoords
                    self.polygons.append(coordIdx)
                    self.idx = self.idx + 1
                    self.existingCoords = []

                # Update Map
                self.polycoords = []
                self.UpdateMap(render=False)
                self.redrawAll = True
                self.Refresh()

        elif action in ["deleteArea", "deleteLine"]:
            # -> delete selected raster features
            x, y = event.GetPositionTuple()
            ids = self.pdcVector.FindObjectsByBBox(x, y)
            idx = ids[0]
            cat = None
            if idx in self.idxCats:
                cat = self.idxCats[idx]
                self.digit.DeleteArea(cat)

            polygonsCopy = self.polygons
            self.polygons = []
            for poly in polygonsCopy:
                id = poly.keys()[0]
                if idx != id:
                    self.polygons.append(poly)

        elif action == "deleteCircle":
            x, y = event.GetPositionTuple()
            ids = self.pdcVector.FindObjectsByBBox(x, y)
            idx = ids[0]
            cat = None
            # print self.idxCats
            # print self.idxCats.has_key(idx) , idx
            if idx in self.idxCats:
                cat = self.idxCats[idx]
                # print cat
                # self.digit.DeleteCircle(cat)

            circlesCopy = self.circles
            self.circles = []
            for circle in circlesCopy:
                id = circle.keys()[0]
                if idx != id:
                    self.circles.append(circle)

    def _onMouseMoving(self, event):
        self.mouse["end"] = event.GetPositionTuple()[:]

        Debug.msg(
            5,
            "BufferedWindow.OnMouseMoving(): coords=%f,%f"
            % (self.mouse["end"][0], self.mouse["end"][1]),
        )

        action = self.toolbar.GetAction()
        if action == "addLine" and self.toolbar.GetAction("type") in [
            "line",
            "boundary",
            "area",
        ]:
            if len(self.polycoords) > 0:
                self.MouseDraw(
                    pdc=self.pdcTmp, begin=self.Cell2Pixel(self.polycoords[-1])
                )

            self.Refresh()  # TODO: use RefreshRect()
            self.mouse["begin"] = self.mouse["end"]

    def _zoom(self, event):
        tmp1 = self.mouse["end"]
        tmp2 = self.Cell2Pixel(self.moveInfo["begin"])
        dx = tmp1[0] - tmp2[0]
        dy = tmp1[1] - tmp2[1]
