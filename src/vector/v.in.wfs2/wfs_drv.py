import grass.script as gs

from urllib2 import urlopen
import xml.etree.ElementTree as ET

from wfs_base import WFSBase


class WFSDrv(WFSBase):
    def _download(self):
        """!Downloads data from WFS server

        @return temp_map with downloaded data
        """
        gs.message(_("Downloading data from WFS server..."))

        proj = self.projection_name + "=EPSG:" + str(self.o_srs)

        url = self.o_url + (
            "SERVICE=WFS&REQUEST=GetFeature&VERSION=%s&TYPENAME=%s"
            % (self.o_wfs_version, self.o_layers)
        )

        if self.bbox:
            if self.flip_coords:
                # flip coordinates if projection is geographic (see:wfs_base.py _computeBbox)
                query_bbox = dict(self._flipBbox(self.bbox))
            else:
                query_bbox = self.bbox

            url += "&BBOX=%s,%s,%s,%s" % (
                query_bbox["minx"],
                query_bbox["miny"],
                query_bbox["maxx"],
                query_bbox["maxy"],
            )

        if self.o_maximum_features:
            url += "&MAXFEATURES=" + str(self.o_maximum_features)

        if self.o_urlparams != "":
            url += "&" + self.o_urlparams

        gs.debug(url)
        try:
            wfs_data = urlopen(url)
        except OSError:
            gs.fatal(_("Unable to fetch data from server"))

        temp_map = self._temp()

        # download data into temporary file
        try:
            temp_map_opened = open(temp_map, "w")
            temp_map_opened.write(wfs_data.read())
            temp_map_opened
        except OSError:
            gs.fatal(_("Unable to write data into tempfile"))
        finally:
            temp_map_opened.close()

        namespaces = ["http://www.opengis.net/ows", "http://www.opengis.net/ogc"]

        context = ET.iterparse(temp_map, events=["start"])
        event, root = context.next()

        for namesp in namespaces:
            if (
                root.tag == "{%s}ExceptionReport" % namesp
                or root.tag == "{%s}ServiceExceptionReport" % namesp
            ):
                try:
                    error_xml_opened = open(temp_map, "r")
                    err_str = error_xml_opened.read()
                except OSError:
                    gs.fatal(_("Unable to read data from tempfile"))
                finally:
                    error_xml_opened.close()

                if err_str is not None:
                    gs.fatal(_("WFS server error: %s") % err_str)
                else:
                    gs.fatal(_("WFS server unknown error"))

        return temp_map
