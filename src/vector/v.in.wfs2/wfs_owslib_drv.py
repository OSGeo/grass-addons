import grass.script as grass

try:
    from owslib.wfs import WebFeatureService
    from owslib.util import ServiceException
except:
    grass.fatal(
        _(
            "OSWLib can not be found. Install OSWLib (https://github.com/geopython/OWSLib) or use GRASS driver."
        )
    )

from wfs_base import WFSBase


class WFSOwsLibDrv(WFSBase):
    def _download(self):
        """!Downloads data from WFS server using OSWlLib driver

        @return temp_map with downloaded data
        """
        grass.message(_("Downloading data from WFS server..."))

        if self.bbox:
            query_bbox = (
                self.bbox["minx"],
                self.bbox["miny"],
                self.bbox["maxx"],
                self.bbox["maxy"],
            )
        else:
            query_bbox = self.bbox

        wfs = WebFeatureService(url=self.o_url, version=self.o_wfs_version)

        try:
            wfs_data = wfs.getfeature(
                typename=[self.o_layers],
                srsname="EPSG:" + str(self.o_srs),
                maxfeatures=self.o_maximum_features,
                bbox=query_bbox,
            )
        # TODO do it better
        except ServiceException as e:
            grass.fatal(_("Server returned exception"))

        grass.debug(url)

        temp_map = self._temp()

        # download data into temporary file
        try:
            temp_map_opened = open(temp_map, "w")
            temp_map_opened.write(wfs_data.read())
            temp_map_opened
        except IOError:
            grass.fatal(_("Unable to write data into tempfile"))
        finally:
            temp_map_opened.close()

        return temp_map
