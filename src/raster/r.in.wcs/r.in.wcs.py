#!/usr/bin/env python

"""
MODULE:     r.in.wcs.py

AUTHOR(S):  Martin Zbinden <martin.zbinden@immerda.ch>, inspired by
            module r.in.wms (GRASS7) by Stepan Turek <stepan.turek AT seznam.cz>
            Luca Delucchi <lucadeluge gmail com>

PURPOSE:    Downloads and imports data from WCS server (only version 1.0.0).
            According to http://grasswiki.osgeo.org/wiki/WCS

VERSION:        0.1

DATE:           Mon Jun 16 21:00:00 CET 2014

COPYRIGHT:  (C) 2014 Martin Zbinden and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %module
# % description: Downloads and imports coverage from WCS server.
# % keyword: raster
# % keyword: import
# % keyword: OGC web services
# %end

# %option
# % key: url
# % type: string
# % description: Service URL (typically http://.../mapserv? )
# % required: yes
# % answer: http://...?
# %end

# %flag
# % key: c
# % description: Get the server capabilities then exit
# % guisection: Request
# %end

# %flag
# % key: r
# % description: Reproject raster data using r.import if needed
# %end

# %option
# % key: coverage
# % type: string
# % description: Coverage name to request
# % multiple: no
# % required: no
# % guisection: Request
# %end

# %option
# % key: urlparams
# % type: string
# % description: Additional query parameters to pass to the server
# % guisection: Request
# %end

# %option
# % key: username
# % type:string
# % description: Username for server connection
# % guisection: Request
# %end

# %option
# % key: password
# % type:string
# % description: Password for server connection
# % guisection: Request
# %end

# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: Name for output raster map (default: coveragename)
# % required: no
# %end

# %option
# % key: location
# % type: string
# % description: Name for new location to create
# % required: no
# %end

# %option
# % key: region
# % type: string
# % description: Name for region instead of current region
# % required: no
# %end

# %option
# % key: crs
# % type: string
# % description: A valid CRS string to pass at WCS request
# % required: no
# %end

import os
import sys
import base64
import subprocess
import grass.script as grass

try:
    from urllib2 import urlopen, HTTPError, Request
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
try:
    from httplib import HTTPException
except ImportError:
    # python3
    from http.client import HTTPException


class WCSBase:
    """Base class tp get WCS layer"""

    def __init__(self):
        try:
            import lxml.etree as etree
        except ImportError:
            grass.fatal("lxml Python library was not found. Please install it.")
        # these variables are information for destructor
        self.temp_files_to_cleanup = []
        self.params = {}
        self.temp_map = None
        self.etree = etree

    def __del__(self):

        # tries to remove temporary files, all files should be
        # removed before, implemented just in case of unexpected
        # stop of module
        for temp_file in self.temp_files_to_cleanup:
            grass.try_remove(temp_file)

    def _debug(self, fun, msg):
        """Print debug messages"""
        grass.debug("%s.%s: %s" % (self.__class__.__name__, fun, msg))

    def _initializeParameters(self, options, flags):
        """
        Initialize all given and needed parameters. Get region information and
        calculate boundingbox according to it

        """
        self._debug("_initializeParameters", "started")

        for key in ["url", "coverage", "output", "location", "crs"]:
            self.params[key] = options[key].strip()

        if not self.params["output"]:
            self.params["output"] = self.params["coverage"]
            if not grass.overwrite():
                result = grass.find_file(name=self.params["output"], element="cell")
                if result["file"]:
                    grass.fatal(
                        "Raster map <%s> does already exist. Choose other "
                        "output name or toggle flag --o." % self.params["output"]
                    )

        for key in ["password", "username", "version", "region"]:
            self.params[key] = options[key]

        # check if authentication information is complete
        if (self.params["password"] and self.params["username"] == "") or (
            self.params["password"] == "" and self.params["username"]
        ):
            grass.fatal(
                _(
                    "Please insert both %s and %s parameters or none of them."
                    % ("password", "username")
                )
            )

        # configure region extent (specified name or current region)
        self.params["region"] = self._getRegionParams(options["region"])
        self.params["boundingbox"] = self._computeBbox()
        self.params["rimport"] = flags["r"]
        self._debug("_initializeParameters", "finished")

    def _getRegionParams(self, opt_region):
        """!Get region parameters from region specified or active default region

        @return region_params as a dictionary
        """
        self._debug("_getRegionParameters", "started")

        if opt_region:
            reg_spl = opt_region.strip().split("@", 1)
            reg_mapset = "."
            if len(reg_spl) > 1:
                reg_mapset = reg_spl[1]

            if not grass.find_file(
                name=reg_spl[0], element="windows", mapset=reg_mapset
            )["name"]:
                grass.fatal(_("Region <%s> not found") % opt_region)

        if opt_region:
            s = grass.read_command(
                "g.region", quiet=True, flags="ug", region=opt_region
            )
            region_params = grass.parse_key_val(s, val_type=float)
            grass.verbose("Using region parameters for region %s" % opt_region)
        else:
            region_params = grass.region()
            grass.verbose("Using current grass region")

        self._debug("_getRegionParameters", "finished")
        return region_params

    def _computeBbox(self):
        """!Get extent for WCS query (bbox) from region parameters

        @return bounding box defined by list [minx,miny,maxx,maxy]
        """
        self._debug("_computeBbox", "started")
        boundingboxvars = ("w", "s", "e", "n")
        boundingbox = list()
        for f in boundingboxvars:
            boundingbox.append(self.params["region"][f])
        grass.verbose(
            "Boundingbox coordinates:\n %s  \n [West, South, Eest, North]" % boundingbox
        )
        self._debug("_computeBbox", "finished")
        return boundingbox

    def getMap(self, options, flags):
        """!Download data from WCS server.

        @return mapname with downloaded data
        """
        self._debug("GetMap", "started")

        self._initializeParameters(options, flags)
        p = self._download()

        if p != 0:
            grass.fatal("Download or import of WCS data failed.")

        return self.params["output"]

    def _fetchCapabilities(self, options):
        """!Download capabilities from WCS server

        @return cap (instance of method _fetchDataFromServer)
        """
        self._debug("_fetchCapabilities", "started")
        cap_url = options["url"].strip()

        if "?" in cap_url:
            cap_url += "&"
        else:
            cap_url += "?"

        cap_url += "SERVICE=WCS&REQUEST=GetCapabilities&VERSION=" + options["version"]

        if options["urlparams"]:
            cap_url += "&" + options["urlparams"]

        grass.message("Fetching capabilities file\n%s" % cap_url)

        try:
            cap = self._fetchDataFromServer(
                cap_url, options["username"], options["password"]
            )
        except (IOError, HTTPException) as e:
            if isinstance(e, HTTPError) and e.code == 401:
                grass.fatal(
                    _("Authorization failed to <%s> when fetching capabilities")
                    % options["url"]
                )
            else:
                msg = _("Unable to fetch capabilities from <%s>: %s") % (
                    options["url"],
                    e,
                )

                if hasattr(e, "reason"):
                    msg += _("\nReason: ") + str(e.reason)

                grass.fatal(msg)
        self._debug("_fetchCapabilities", "finished")
        return cap

    def _fetchDataFromServer(self, url, username=None, password=None):
        """!Fetch data from server"""
        self._debug("_fetchDataFromServer", "started")
        request = Request(url=url)
        if username and password:
            base64string = base64.encodestring("%s:%s" % (username, password)).replace(
                "\n", ""
            )
            request.add_header("Authorization", "Basic %s" % base64string)

        try:
            return urlopen(request)
        except ValueError as error:
            grass.fatal("%s" % error)

        self._debug("_fetchDataFromServer", "finished")

    def getCapabilities(self, options, flags):
        """!Get capabilities from WCS server and print to stdout"""
        self._debug("GetCapabilities", "started")

        cap = self._fetchCapabilities(options)
        root = self.etree.fromstringlist(cap.readlines())

        cov_offering = []
        for label in root.iter("{*}CoverageOfferingBrief"):
            text = label.find("{*}name").text + " : "
            # label could be missing for a working WCS service
            try:
                text += label.find("{*}label").text
            except AttributeError:
                pass
            cov_offering.append(text)
        if cov_offering:
            grass.message("Available layers:")
            grass.message("\n".join(cov_offering))
        else:
            grass.message("No layers available")
        self._debug("GetCapabilities", "finished")

    def _tempfile(self):
        """!Create temp_file and append list self.temp_files_to_cleanup
            with path of file

        @return string path to temp_file
        """
        self._debug("_tempfile", "started")
        temp_file = grass.tempfile()
        if temp_file is None:
            grass.fatal(_("Unable to create temporary files"))

        # list of created tempfiles for destructor
        self.temp_files_to_cleanup.append(temp_file)
        self._debug("_tempfile", "finished")

        return temp_file


class WCSGdalDrv(WCSBase):
    """Class for WCS GDAL using VirtulRaster"""

    def __init__(self):
        super(WCSGdalDrv, self).__init__()
        self.out = ""
        self.err = ""
        self.xml_file = ""
        self.vrt_file = ""

    def _createXML(self):
        """!Create XML for GDAL WCS driver

        @return path to XML file
        """
        self._debug("_createXML", "started")

        gdal_wcs = self.etree.Element("WCS_GDAL")
        server_url = self.etree.SubElement(gdal_wcs, "ServiceUrl")
        server_url.text = self.params["url"]

        version = self.etree.SubElement(gdal_wcs, "Version")
        version.text = self.params["version"]

        coverage = self.etree.SubElement(gdal_wcs, "CoverageName")
        coverage.text = self.params["coverage"]

        if self.params["username"]:
            userpwd = self.etree.SubElement(gdal_wcs, "UserPwd")
            userpwd.text = self.params["username"] + ":" + self.params["password"]

        if self.params["crs"]:
            crs = self.etree.SubElement(gdal_wcs, "supportedCRSs")
            crs.text = self.params["crs"]

        xml_file = self._tempfile()

        etree_gdal_wcs = self.etree.ElementTree(gdal_wcs)
        grass.debug(etree_gdal_wcs)
        self.etree.ElementTree(gdal_wcs).write(xml_file)

        self._debug("_createXML", "finished -> %s" % xml_file)

        return xml_file

    def _createVRT(self):
        """! create VRT with help of gdalbuildvrt program
        VRT is a virtual GDAL dataset format

        @return path to VRT file
        """
        self._debug("_createVRT", "started")
        vrt_file = self._tempfile()
        command = ["gdalbuildvrt", "-te"]
        command += self.params["boundingbox"]
        command += ["-resolution", "user", "-tr"]
        command += [self.params["region"]["ewres"], self.params["region"]["nsres"]]
        command += [vrt_file, self.xml_file]
        command = [str(i) for i in command]

        grass.verbose(" ".join(command))
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        self.out, self.err = process.communicate()
        self.out, self.err = grass.decode(self.out), grass.decode(self.err)
        grass.verbose(self.out)

        if self.err:
            grass.verbose(self.err + "\n")
            if "does not exist" in self.err:
                grass.warning(
                    'Coverage "%s" cannot be opened / does not exist.'
                    % self.params["coverage"]
                )
            grass.fatal(
                "Generation of VRT-File failed (gdalbuildvrt ERROR). Set verbose-flag for details."
            )

        self._debug("_createVRT", "finished")
        return vrt_file

    def _download(self):
        """!Downloads data from WCS server using GDAL WCS driver

        @return ret (exit code of r.in.gdal module)
        """
        self._debug("_download", "started")

        self.xml_file = self._createXML()
        self.vrt_file = self._createVRT()

        grass.message("Starting module r.in.gdal ...")

        env = os.environ.copy()
        env["GRASS_MESSAGE_FORMAT"] = "gui"

        if self.params["rimport"]:
            p = grass.start_command(
                "r.import",
                input=self.vrt_file,
                output=self.params["output"],
                stdout=grass.PIPE,
                stderr=grass.PIPE,
                env=env,
            )
        elif self.params["location"] == "":
            p = grass.start_command(
                "r.in.gdal",
                input=self.vrt_file,
                output=self.params["output"],
                stdout=grass.PIPE,
                stderr=grass.PIPE,
                env=env,
            )
        else:
            p = grass.start_command(
                "r.in.gdal",
                input=self.vrt_file,
                output=self.params["output"],
                location=self.params["location"],
                stdout=grass.PIPE,
                stderr=grass.PIPE,
                env=env,
            )

        while p.poll() is None:
            line = p.stderr.readline()
            linepercent = line.replace(b"GRASS_INFO_PERCENT:", b"").strip()
            if linepercent.isdigit():
                # print linepercent
                grass.percent(int(linepercent), 100, 1)

        grass.percent(100, 100, 5)

        ret = p.wait()
        if ret != 0:
            grass.fatal("r.in.gdal for %s failed." % self.vrt_file)
        else:
            grass.message(
                "r.in.gdal was successful for new raster map %s "
                % self.params["output"]
            )

        grass.try_remove(self.vrt_file)
        grass.try_remove(self.xml_file)
        self._debug("_download", "finished")

        return ret


def main():
    """Main function"""
    flag_c = flags["c"]

    options["version"] = (
        "1.0.0"  # right now only supported version, therefore not in GUI
    )

    grass.debug("Using GDAL WCS driver")
    wcs = WCSGdalDrv()  # only supported driver

    if flag_c:
        wcs.getCapabilities(options, flags)

    else:
        grass.message("Importing raster map into GRASS...")
        fetched_map = wcs.getMap(options, flags)
        if not fetched_map:
            grass.warning(
                _("Nothing imported.\n Data not has been downloaded from wcs server.")
            )
            return 1

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
