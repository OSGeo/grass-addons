#!/usr/bin/env python

"""
@module  mdpdffactory
@brief   Pdf creator

Classes:
 - mdpdffactory::MapBBFactory
 - mdpdffactory::MyTheme
 - mdpdffactory::MD_ITEM
 - mdpdffactory::PdfCreator
 - mdpdffactory::Point
"""

import io
import math
import os
import subprocess
import sys
import tempfile

from core.gcmd import GError, GWarning

from grass.pygrass.modules.interface.env import G_debug
from grass.script import core as grass
from grass.script.utils import get_lib_path

from . import globalvar
from .mdpdftheme import (
    CENTER,
    DefaultTheme,
    H1,
    H4,
    LEFT,
    Pdf,
    T1,
    T2,
    T3,
)


class MyTheme(DefaultTheme):
    def __init__(self):
        super().__init__()
        self.doc = {
            "leftMargin": 25,
            "rightMargin": 25,
            "bottomMargin": 25,
            "allowSplitting": False,
        }


class PdfCreator(object):
    def __init__(self, MD_metadata, pdf_file, map, type, filename, profile):
        """@:param MD_metadata- instance of metadata(owslib)
        @:param pdf_file- path and name of generated report
        """
        try:
            global Image, PageBreak, Paragraph, Table, PilImage

            from PIL import Image as PilImage
            from reportlab.platypus import (
                Image,
                PageBreak,
                Paragraph,
                Table,
            )
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.md = MD_metadata
        self.pdf_file = pdf_file
        self.TABLE_WIDTH = 540
        self.map = map
        self.type = type
        self.profile = profile
        if self.profile is None:
            self.profile = "custom iso profile"
        self.filename = filename
        self.my_theme = MyTheme()

    def getMapPic(self):
        f = os.path.join(tempfile.gettempdir(), "tmpPic.png")

        grass.run_command("g.region", save="tmpPdf", overwrite=True)
        grass.run_command("g.region", flags="d")

        grass.run_command(
            "d.mon", start="cairo", output=f, width=200, height=200, overwrite=True
        )
        grass.run_command("d.erase")
        if self.type == "raster":
            grass.run_command("g.region", raster=self.map)
            grass.run_command("d.rast", map=self.map)
        if self.type == "vector":
            grass.run_command("g.region", vector=self.map)
            grass.run_command("d.vect", map=self.map)
        grass.run_command("d.mon", stop="cairo")
        grass.run_command("g.region", region="tmpPdf")
        return f

    def findItem(self, items, name2, idx=-1):
        values = []
        for i in items:
            if i.name2 == name2:
                values.append(i.value[0])

        if idx == -1:
            if len(values) == 0:
                values.append("unknown")
            return values

        if len(values) <= idx:
            return "unknown"

        if values[idx] is not None:
            return values[idx]

        return "unknown"

    # def chckTextValidity(self):
    def tableFactory(self, title, headers, key):
        """
        @:param headers - list of header
        """
        self.doc.add_header(title, H4)
        head = []
        head.append(headers)
        tmp = []
        for i in range(len(self.findItem(self.story[key], headers[0]))):
            for header in headers:
                value = self.findItem(self.story[key], header, i)
                # value=self.chckTextValidity(value)
                text = Paragraph(
                    """
                %s<br/>
                """
                    % value,
                    self.my_theme.paragraph,
                )
                tmp.append(text)
            head.append(tmp)
            tmp = []

        self.doc.add_table(head, self.TABLE_WIDTH)

    def textFactory(self, title, tag, name, multiple=0):
        self.doc.add_header(title, H4)
        val = self.findItem(self.story[tag], name, multiple)
        lines = ""
        if len(val) > 1 and multiple == -1:
            tmp = []
            for v in val:
                tmp.append(v)
            lines = ", ".join(tmp)
            text = Paragraph(
                """
            %s<br/>
            """
                % lines,
                self.my_theme.paragraph,
            )
            self.doc.add_fparagraph(text)
            return

        if len(val) > 400:
            for line in val.splitlines():
                lines += line + "\n"
                if len(lines) > 400:
                    text = Paragraph(
                        """
                                    %s<br/>
                                    """
                        % lines,
                        self.my_theme.paragraph,
                    )
                    self.doc.add_fparagraph(text)
                    lines = ""
        else:
            text = Paragraph(
                """
                            %s<br/>
                            """
                % val,
                self.my_theme.paragraph,
            )
            self.doc.add_fparagraph(text)

    def createPDF(self, save=True):
        self.story = self._parseMDOWS()
        self.doc = Pdf("Metadata file", "GRASS GIS")

        self.doc.set_theme(self.my_theme)

        lib_name = "config"
        logo_path = get_lib_path("wx.metadata", lib_name)

        logo_path = os.path.join(logo_path, lib_name, "logo_variant_bg.png")
        self.doc.add_image(logo_path, 57, 73, LEFT)

        if self.map is None:
            self.doc.add_header(self.filename, T1)
        else:
            self.doc.add_header(self.map, T1)
            self.doc.add_header(self.filename, T2)

        if self.type == "vector":
            name = "vector map"
            self.doc.add_header(name, T2)
        else:
            name = "raster map"
            self.doc.add_header(name, T2)

        self.doc.add_header("%s metadata profile" % self.profile, T3)

        self.doc.add_spacer(2)

        if map is not None:
            mapPic = self.getMapPic()
            self.doc.add_image(mapPic, 200, 200, CENTER)

        self.textFactory(
            title="Keywords", name="Keywords", tag="identification", multiple=-1
        )
        self.textFactory(title="Abstract", name="Abstract", tag="identification")
        # #################### metadata #################################
        self.doc.add_spacer(25)
        self.doc.add_header("Metadata on metadata", H1)
        head = ["Organization name", "E-mail", "Role"]  # this is the header row
        self.tableFactory("Metadata point of contact", head, "contact")
        self.textFactory(title="Metadata date", name="Datestamp", tag="datestamp")
        self.textFactory(title="Metadata language", name="Language", tag="languagecode")
        # #################### identification #################################
        self.doc.add(PageBreak())
        self.doc.add_header("Identification", H1)
        self.textFactory(title="Restource title", name="Title", tag="identification")
        self.textFactory(title="Identifier", name="Identifier", tag="identifier")
        # self.textFactory(title="Resource locator", name='Identifier',tag='identifier')#TODO linkage is missing

        self.tableFactory("Resource language", ["Language"], "identification")
        # head = ['Organization name', 'E-mail','Role']
        # .tableFactory("identifier",head,'contact')

        ##################### Keywords ################################## TODO

        ##################### Geographic ##################################
        self.doc.add_spacer(25)
        self.doc.add_header("Geographic Location", H1)

        maxy = float(self.findItem(self.story["identification"], "maxy", 0))
        maxx = float(self.findItem(self.story["identification"], "maxx", 0))
        miny = float(self.findItem(self.story["identification"], "miny", 0))
        minx = float(self.findItem(self.story["identification"], "minx", 0))

        head = [
            [
                "North Bound Latitude",
                "East Bound Longitude",
                "South Bound Latitude",
                "West Bound Longitude",
            ]
        ]
        head.append([maxx, maxy, minx, miny])
        self.doc.add_table(head, self.TABLE_WIDTH)
        self.doc.add_spacer(25)
        mapPath = MapBBFactory(
            [[maxx, minx], [maxy, miny]],
        )

        ##################### Add OpenStreetMap picture(extend) ##################################
        try:
            gmap = Image(mapPath.link1, 200, 200)
            gmap1 = Image(mapPath.link2, 200, 200)
            self.doc.add(Table([[gmap1, gmap]]))
            self.doc.add(PageBreak())
        except:
            GWarning(
                _(
                    "Cannot download metadata picture of extend provided"
                    " by OpenStreetMap. Please check internet connection."
                )
            )

        ##################### Temporal ##################################
        self.doc.add_spacer(25)
        self.doc.add_header("Temporal reference", H1)
        self.textFactory(
            title="Temporal extend start",
            name="Temporal extend start",
            tag="identification",
        )
        self.textFactory(
            title="Temporal extend end",
            name="Temporal extend end",
            tag="identification",
        )

        ##################### Quality ##################################
        self.doc.add_spacer(25)
        self.doc.add_header("Quality a validity", H1)
        self.textFactory(title="Lineage", name="Lineage", tag="dataquality")

        # self.textFactory(title="Temporal extend start", name='Temporal extend start',tag='identification')
        # TODO md.identification.denominators

        ######################Conformity ########################
        self.doc.add_spacer(25)
        self.doc.add_header("Conformity", H1)
        head = ["Conformance date", "Conformance date type", "Specification"]
        self.tableFactory("Conformity", head, "dataquality")
        ###################### Constraints ########################
        self.doc.add_spacer(25)
        self.doc.add_header("Constraints", H1)
        self.tableFactory(
            "Condition applying to use", ["Use limitation"], "identification"
        )
        self.tableFactory(
            "Condition applying to access", ["Access constraints"], "identification"
        )
        self.tableFactory(
            "Limitation on public access", ["Other constraintrs"], "identification"
        )
        ###################### Responsible party ########################
        self.doc.add_spacer(25)
        self.doc.add_header("Responsible party", H1)
        header = ["Organization name", "E-mail", "Role"]
        self.tableFactory(
            "Organisations responsible for the establishment, management, maintenance and distribution of spatial data sets and services",
            header,
            "identification",
        )

        text = self.doc.render()
        # http://www.reportlab.com/docs/reportlab-userguide.pdf
        if save and self.pdf_file is not None:
            path = self.savePDF(text)
            return path

        return text

    def _parseMDOWS(self, md=None):
        if md is None:
            md = self.md
        metadata = {}
        metadata["identification"] = []
        metadata["languagecode"] = []
        metadata["datestamp"] = []
        metadata["identifier"] = []
        metadata["dataquality"] = []
        metadata["contact"] = []
        metadata["distance"] = []
        # #########################################################
        # ##############  identification  #########################
        if md.identification is not None:
            if md.identification.contact is not None:
                for contact in md.identification.contact:
                    if contact.organization is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                contact.organization,
                                "gmd:CI_ResponsibleParty",
                                "Organization name",
                            )
                        )
                    if contact.email is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(contact.email, "gmd:CI_ResponsibleParty", "E-mail")
                        )
                    if contact.role is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(contact.role, "gmd:CI_ResponsibleParty", "Role")
                        )

            if md.identification.title is not (None or ""):
                metadata["identification"].append(
                    MD_ITEM(
                        md.identification.title, "gmd:md_DataIdentification", "Title"
                    )
                )

            if md.identification.abstract is not (None or ""):
                metadata["identification"].append(
                    MD_ITEM(
                        md.identification.abstract,
                        "gmd:md_DataIdentification",
                        "Abstract",
                    )
                )

            if md.identification.identtype is not (None or ""):
                metadata["identification"].append(
                    MD_ITEM(
                        md.identification.identtype, "gmd:md_ScopeCode", "Resource type"
                    )
                )

            if md.identification.resourcelanguage is not None:
                for language in md.identification.resourcelanguage:
                    if language != "":
                        metadata["identification"].append(
                            MD_ITEM(language, "gmd:language", "Language")
                        )

            if md.identification.uricode is not None:
                for uri in md.identification.uricode:
                    if uri != "":
                        metadata["identification"].append(
                            MD_ITEM(
                                uri, "gmd:RS_Identifier", "Unique Resource Identifier"
                            )
                        )

            if md.identification.topiccategory is not None:
                for topic in md.identification.topiccategory:
                    if topic != "":
                        metadata["identification"].append(
                            MD_ITEM(topic, "gmd:topicCategory", "Topic Category")
                        )

            # #########################################################
            # ########################  keywords  #########################
            if md.identification.keywords is not None:
                for key in md.identification.keywords:
                    for k in key["keywords"]:
                        if k is not (None or ""):
                            metadata["identification"].append(
                                MD_ITEM(k, "gmd:MD_Keywords", "Keywords")
                            )

                    if key["thesaurus"] is not (None or ""):
                        if key["thesaurus"]["title"] is not (None or ""):
                            metadata["identification"].append(
                                MD_ITEM(
                                    key["thesaurus"]["title"],
                                    "gmd:thesaurusName",
                                    "Thesaurus title",
                                )
                            )
                        if key["thesaurus"]["date"] is not (None or ""):
                            metadata["identification"].append(
                                MD_ITEM(
                                    key["thesaurus"]["date"],
                                    "gmd:thesaurusName",
                                    "Thesaurus date",
                                )
                            )
                        if key["thesaurus"]["datetype"] is not (None or ""):
                            metadata["identification"].append(
                                MD_ITEM(
                                    key["thesaurus"]["datetype"],
                                    "gmd:thesaurusName",
                                    "Thesaurus date type ",
                                )
                            )

            if md.identification.extent is not None:
                if md.identification.extent.boundingBox is not None:
                    if md.identification.extent.boundingBox.minx is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                md.identification.extent.boundingBox.minx,
                                "gmd:westBoundLongitude",
                                "minx",
                            )
                        )
                    if md.identification.extent.boundingBox.maxx is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                md.identification.extent.boundingBox.maxx,
                                "gmd:eastBoundLongitude",
                                "maxx",
                            )
                        )
                    if md.identification.extent.boundingBox.miny is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                md.identification.extent.boundingBox.miny,
                                "gmd:southBoundLatitude",
                                "miny",
                            )
                        )
                    if md.identification.extent.boundingBox.maxy is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                md.identification.extent.boundingBox.maxy,
                                "gmd:northBoundLatitude",
                                "maxy",
                            )
                        )

            if md.identification.date is not None:
                for date in md.identification.date:
                    if date is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(date, "gmd:CI_Date", "Date")
                        )

            if md.identification.temporalextent_start is not (None or ""):
                metadata["identification"].append(
                    MD_ITEM(
                        md.identification.temporalextent_start,
                        "gmd:EX_TemporalExtent",
                        "Temporal extend start",
                    )
                )
            if md.identification.temporalextent_end is not (None or ""):
                metadata["identification"].append(
                    MD_ITEM(
                        md.identification.temporalextent_end,
                        "gmd:EX_TemporalExtent",
                        "Temporal extend end",
                    )
                )

            if md.identification.uselimitation is not None:
                for limitation in md.identification.uselimitation:
                    if limitation is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(limitation, "gmd:useLimitation", "Use limitation")
                        )

            if md.identification.accessconstraints is not None:
                for accessconstraints in md.identification.accessconstraints:
                    if accessconstraints is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                accessconstraints,
                                "gmd:accessConstraints",
                                "Access constraints",
                            )
                        )

            if md.identification.otherconstraints is not None:
                for otherconstraints in md.identification.otherconstraints:
                    if otherconstraints is not (None or ""):
                        metadata["identification"].append(
                            MD_ITEM(
                                otherconstraints,
                                "gmd:otherConstraints",
                                "Other constraintrs",
                            )
                        )

        # #########################################################
        # ########################  date  #########################
        if md.languagecode is not (None or ""):
            metadata["languagecode"].append(
                MD_ITEM(md.languagecode, "gmd:LanguageCode", "Language")
            )

        if md.datestamp is not (None or ""):
            metadata["datestamp"].append(
                MD_ITEM(md.datestamp, "gmd:dateStamp", "Datestamp")
            )

        if md.identifier is not (None or ""):
            metadata["identifier"].append(
                MD_ITEM(md.identifier, "gmd:identifier", "Identifier")
            )

        if md.dataquality is not (None or ""):
            if md.dataquality.lineage is not (None or ""):
                metadata["dataquality"].append(
                    MD_ITEM(md.dataquality.lineage, "gmd:LI_Lineage", "Lineage")
                )

            if md.dataquality.conformancedate is not None:
                for conformancedate in md.dataquality.conformancedate:
                    if conformancedate is not (None or ""):
                        metadata["dataquality"].append(
                            MD_ITEM(
                                conformancedate,
                                "gmd:DQ_ConformanceResult",
                                "Conformance date",
                            )
                        )

            if md.dataquality.conformancedatetype is not None:
                for conformancedatetype in md.dataquality.conformancedatetype:
                    if conformancedate is not (None or ""):
                        metadata["dataquality"].append(
                            MD_ITEM(
                                conformancedatetype,
                                "gmd:DQ_ConformanceResult",
                                "Conformance date type",
                            )
                        )

            if md.dataquality.conformancetitle is not None:
                for conformancetitle in md.dataquality.conformancetitle:
                    if conformancedate is not (None or ""):
                        metadata["dataquality"].append(
                            MD_ITEM(
                                conformancetitle,
                                "gmd:DQ_ConformanceResult",
                                "Specification",
                            )
                        )

        if md.contact is not None:
            for contact in md.contact:
                if contact.organization is not (None or ""):
                    metadata["contact"].append(
                        MD_ITEM(
                            contact.organization, "gmd:contact", "Organization name"
                        )
                    )

                if contact.email is not (None or ""):
                    metadata["contact"].append(
                        MD_ITEM(contact.email, "gmd:contact", "E-mail")
                    )  # TODO more email can be

                if contact.role is not (None or ""):
                    metadata["contact"].append(
                        MD_ITEM(contact.role, "gmd:role", "Role")
                    )

        # #### quality validity
        if self.md.identification.distance is not (None or ""):
            metadata["distance"].append(
                MD_ITEM(self.md.identification.distance, "gmd:distance", "Distance")
            )
        return metadata

    def savePDF(self, doc, pathToPdf=None):
        if pathToPdf is None:
            pathToPdf = self.pdf_file
        out = open(pathToPdf, "wb+")
        out.write(doc)
        out.close()
        return pathToPdf


class MD_ITEM:
    def __init__(self, value, name1, name2=None):
        self.value = []
        self.name1 = name1
        self.name2 = name2
        self.addValue(value)

    def addValue(self, value):
        self.value.append(value)


class Point:
    """Stores a simple (x,y) point.  It is used for storing x/y pixels.

    Attributes:
      x: An int for a x value.
      y: An int for a y value.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def ToString(self):
        return "(%s, %s)" % (self.x, self.y)

    def Equals(self, other):
        if other is None:
            return False
        else:
            return other.x == self.x and other.y == self.y


class MapBBFactory:
    """Class for compute bounding box for static map with using osm API"""

    def __init__(self, coords, size=[200, 200]):
        self._map_img_polygon_style = {
            "pathOptions": {
                "color": "#3388ff",
                "weight": 3,
                "fillOpacity": 0,
            },
        }
        self.pixels_per_lon_degree = []
        self.pixels_per_lon_radian = []
        self.pixel_origo = []
        self.pixel_range = []
        self.pixels = 256
        self.size = size
        self.zoom_max = 17
        zoom_levels = list(range(0, self.zoom_max))
        for z in zoom_levels:
            origin = self.pixels / 2
            self.pixels_per_lon_degree.append(self.pixels / 360)
            self.pixels_per_lon_radian.append(self.pixels / (2 * math.pi))
            self.pixel_origo.append(Point(origin, origin))
            self.pixel_range.append(self.pixels)
            self.pixels = self.pixels * 2

        bounds = self.CalcBoundsFromPoints(coords[0], coords[1])
        corners = self.calcCornersFromBounds(bounds)
        self._update_polygon_geometry_style(map_extent=corners)
        center = self.CalcCenterFromBounds(bounds)
        zoom = self.CalculateBoundsZoomLevel(bounds, size)
        self._is_osmsm_installed()
        self.link1, self.link2 = self.buildLink(center, zoom, corners)

    def _is_osmsm_installed(self):
        """Check if osmsm static map image OpenStreetMap generator is
        installed

        https://github.com/jperelli/osm-static-maps
        """
        try:
            grass.call(["osmsm"], stdout=subprocess.PIPE)
        except OSError:
            GError(
                _(
                    "Could not found osmsm static map image OpenStreetMap"
                    " generator. Please install it."
                )
            )

    def _update_polygon_geometry_style(self, map_extent):
        """Update polygon geometry style

        :param map_extent list: list of Polygon feature dict without
                                style pathOptions dict key

        updated list with pathOptions dict key:

        [{'geometry': {'coordinates': [[[-78.77462049,
                                         35.80918894],
                                        [-78.77462049,
                                         35.68792712],
                                        [-78.60830318,
                                         35.68792712],
                                        [-78.60830318,
                                         35.80918894],
                                        [-78.77462049,
                                         35.80918894]]],
                       'pathOptions': {'color': '#3388ff',
                                       'fillOpacity': 0,
                                       'weight': 3},
                       'type': 'Polygon'},

        """
        map_extent[0]["geometry"].update(self._map_img_polygon_style)

    def calcCornersFromBounds(self, bounds):
        """
        :param bounds: An int that is either the value passed in or
        the min or the max.

        :return geojson: polygon representation, defined by 5 points
        """
        corners = []
        # [lat, lng]
        XminYmax = [bounds[0][0], bounds[1][1]]
        XminYmin = [bounds[0][0], bounds[0][1]]
        XmaxYmin = [bounds[1][0], bounds[0][1]]
        XmaxYmax = [bounds[1][0], bounds[1][1]]
        corners.append(XminYmax)
        corners.append(XminYmin)
        corners.append(XmaxYmin)
        corners.append(XmaxYmax)
        corners.append(XminYmax)

        return [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [corners],
                },
            }
        ]

    def buildLink(self, center, zoom, corners):
        """Generate map static images with osmsm OpenStreetMap geodata

        https://github.com/jperelli/osm-static-maps

        :param zoom int: map zoom
        :param corners list: list of Polygon feature with style pathOptions
                             dict key
                            [{'geometry': {'coordinates': [[[-78.77462049,
                                                             35.80918894],
                                                            [-78.77462049,
                                                             35.68792712],
                                                            [-78.60830318,
                                                             35.68792712],
                                                            [-78.60830318,
                                                             35.80918894],
                                                            [-78.77462049,
                                                             35.80918894]]],
                                           'pathOptions': {'color': '#3388ff',
                                                           'fillOpacity': 0,
                                                           'weight': 3},
                                           'type': 'Polygon'},
                              'type': 'Feature'}]

        :return list: list of map images paths
        """
        pics = []
        temp = tempfile.gettempdir()
        pic_cmd = [
            "osmsm",
            f"-W {self.size[0]}",
            f"-H {self.size[1]}",
            f"-c {center['lat']},{center['lng']}",
            f"-g {corners[0]['geometry']}",
        ]
        # reduced zoom
        pic_with_reduced_zoom_cmd = [
            *pic_cmd,
            f"-z {zoom - 4}",
        ]
        for index, pic_cmd in enumerate([pic_cmd, pic_with_reduced_zoom_cmd]):
            pic = grass.Popen(
                pic_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            pic, error = pic.communicate(0)
            if error:
                GError(
                    _("Failed get static map image with osmsm. {}").format(
                        grass.decode(error),
                    )
                )
            else:
                G_debug(
                    3,
                    f"Generate static map{index}.png img with param arg: {pic_cmd}",
                )
                pic_file = os.path.join(temp, f"map{index}.png")
                pic = io.BytesIO(pic)
                pic = PilImage.open(pic)
                pic.save(pic_file)
                pics.append(pic_file)
        return pics

    def CalcCenterFromBounds(self, bounds):
        """Calculates the center point given southwest/northeast lat/lng
         pairs.

         Given southwest and northeast bounds, this method will return
         the center point.  We use this method when we have done a search
         for points on the map, and we get multiple results.  In the
         results we don't get anything to calculate the center point of
         the map so this method calculates it for us.

         :param list bounds: A list of length 2, each holding a list of
         length 2. It holds the southwest and northeast lat/lng bounds
         of a map.  It should look like this: [[southwestLat, southwestLng],
         [northeastLat, northeastLng]]

        :return dict: An dict containing keys lat and lng for the center
         point.
        """
        north = bounds[1][1]
        south = bounds[0][1]
        east = bounds[1][0]
        west = bounds[0][0]
        center = {}
        center["lng"] = north - float((north - south) / 2)
        center["lat"] = east - float((east - west) / 2)

        return center

    def Bound(self, value, opt_min, opt_max):
        """Returns value if in min/max, otherwise returns the min/max.

        Args:
          value: The value in question.
          opt_min: The minimum the value can be.
          opt_max: The maximum the value can be.

        Returns:
          An int that is either the value passed in or the min or the max.
        """
        if opt_min is not None:
            value = max(value, opt_min)
        if opt_max is not None:
            value = min(value, opt_max)
        return value

    def DegreesToRadians(self, deg):
        return deg * (math.pi / 180)

    def FromLatLngToPixel(self, lat_lng, zoom):
        """Given lat/lng and a zoom level, returns a Point instance.

        This method takes in a lat/lng and a _test_ zoom level and based on that it
        calculates at what pixel this lat/lng would be on the map given the zoom
        level.  This method is used by CalculateBoundsZoomLevel to see if this
        _test_ zoom level will allow us to fit these bounds in our given map size.

        Args:
          lat_lng: A list of a lat/lng point [lat, lng]
          zoom: A list containing the width/height in pixels of the map.

        Returns:
          A Point instance in pixels.
        """
        o = self.pixel_origo[zoom]
        x = round(o.x + lat_lng[1] * self.pixels_per_lon_degree[zoom])
        siny = self.Bound(math.sin(self.DegreesToRadians(lat_lng[0])), -0.9999, 0.9999)
        y = round(
            o.y
            + 0.5
            * math.log((1 + siny) / (1 - siny))
            * -self.pixels_per_lon_radian[zoom]
        )
        return Point(x, y)

    def CalculateBoundsZoomLevel(self, bounds, view_size):
        """Given lat/lng bounds, returns map zoom level.

        This method is used to take in a bounding box (southwest and northeast
        bounds of the map view we want) and a map size and it will return us a zoom
        level for our map.  We use this because if we take the bottom left and
        upper right on the map we want to show, and calculate what pixels they
        would be on the map for a given zoom level, then we can see how many pixels
        it will take to display the map at this zoom level.  If our map size is
        within this many pixels, then we have the right zoom level.

        Args:
          bounds: A list of length 2, each holding a list of length 2. It holds
            the southwest and northeast lat/lng bounds of a map.  It should look
            like this: [[southwestLat, southwestLat], [northeastLat, northeastLng]]
          view_size: A list containing the width/height in pixels of the map.

        Returns:
          An int zoom level.
        """
        zmax = self.zoom_max
        zmin = 0
        bottom_left = bounds[0]
        top_right = bounds[1]
        backwards_range = list(range(zmin, zmax))
        backwards_range.reverse()
        for z in backwards_range:
            bottom_left_pixel = self.FromLatLngToPixel(bottom_left, z)
            top_right_pixel = self.FromLatLngToPixel(top_right, z)
            if bottom_left_pixel.x > top_right_pixel.x:
                bottom_left_pixel.x -= self.CalcWrapWidth(z)
            if (
                abs(top_right_pixel.x - bottom_left_pixel.x) <= view_size[0]
                and abs(top_right_pixel.y - bottom_left_pixel.y) <= view_size[1]
            ):
                return z
        return 0

    def CalcBoundsFromPoints(self, lats, lngs):
        """Calculates the max/min lat/lng in the lists.

        This method takes in a list of lats and a list of lngs, and
        outputs the southwest and northeast bounds for these points.
        We use this method when we have done a search for points on the
        map, and we get multiple results. In the results we don't get a
        bounding box so this method calculates it for us.

        param: list lats: list of latitudes
        param: lsit lngs: list of longitudes

        returns list: a list of length 2, each holding a list of
        length 2. It holds the southwest and northeast lat/lng
        bounds of a map.  It should look like this:
        [[southwestLat, southwestLng], [northeastLat, northeastLng]]
        """
        lats = [float(x) for x in lats]
        lngs = [float(x) for x in lngs]
        flats = list(map(float, lats))
        flngs = list(map(float, lngs))
        west = min(flngs)
        east = max(flngs)
        north = max(flats)
        south = min(flats)

        coords = "{bottom_left}\n{top_right}".format(
            bottom_left="{} {}".format(west, south),
            top_right="{} {}".format(east, north),
        )

        proc = grass.start_command(
            "m.proj",
            flags="do",
            input="-",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        result, error = proc.communicate(input=grass.encode(coords))

        bounds = []
        for row in grass.decode(result).split("\n"):
            if row:
                x, y, z = row.split("|")
                bounds.append([float(x), float(y)])

        return bounds
