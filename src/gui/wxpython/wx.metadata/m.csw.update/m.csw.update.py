#!/usr/bin/env python

############################################################################
#
# MODULE:       m.csw.update
#
# AUTHOR(S):    Tomas Zigo <tomas.zigo slovanet.sk>
#
# PURPOSE:      Update csw connections resources candidates
#
# COPYRIGHT:    (C) 2020 by Tomas Zigo, and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Update catalogue service for the web connections resources candidates.
# % keyword: connections resources
# % keyword: csw
# % keyword: metadata
# %end

# %option G_OPT_F_INPUT
# % key: spreadsheet
# % description: Path to spreadsheet file (ODS format)
# % gisprompt: old,bin,file
# % answer: API-cases.ods
# % required: no
# %end

# %option
# % key: url
# % key_desc: string
# % type: string
# % description: Spreadsheet file URL
# % multiple: no
# % required: no
# %end

# %option G_OPT_F_INPUT
# % key: xml
# % description: Path to CSW connections resources XML file
# % gisprompt: old,bin,file
# % answer: connections_resources.xml
# % required: yes
# %end

# %option G_OPT_F_INPUT
# % key: xsd
# % description: Path to CSW connections resources validation schema XSD file
# % gisprompt: old,bin,file
# % answer: connections_resources.xsd
# % required: yes
# %end

# %option
# % key: timeout
# % type: integer
# % key_desc: timeout
# % description: Timeout for checking if CSW connections resources URL is active
# % answer: 10
# % required: yes
# %end

# %option
# % key: separator
# % type: string
# % key_desc: separator
# % description: Separator inside connections resources item string '{Name}{Separator}{URL}' (print only), use "separator"
# % answer: ': '
# % required: no
# %end

# %option
# % key: proxy
# % type: string
# % key_desc: proxy
# % description: Set the proxy with: "http=<value>,ftp=<value>"
# % required: no
# % multiple: yes
# %end

# %option
# % key: header
# % type: string
# % key_desc: header
# % description: Set the header with: "User-Agent=<value>,Accept=<value>"
# % answer: User-Agent=Mozilla/5.0
# % required: no
# % multiple: yes
# %end

# %flag
# % key: a
# % description: Print all active (valid and active) CSW connections resources only
# %end

# %flag
# % key: i
# % description: Print not active CSW connections resources only
# %end

# %flag
# % key: v
# % description: Print valid CSW connections resources URLs
# %end

# %flag
# % key: n
# % description: Print not valid CSW connections resources URLs
# %end

# %flag
# % key: p
# % description: Print all new CSW connections (valid/not valid, active/not active) resources with following format '{Country}, {Governmental level}, {API provider}: {URL}'
# %end

# %flag
# % key: s
# % description: Print new CSW connections resources summary info
# %end

# %flag
# % key: w
# % description: Print default spreadsheet file URL
# %end

# %flag
# % key: l
# % description: Print default local spreadsheet file URL
# %end

# %flag
# % key: x
# % description: Validate CSW connections resources XML file against XSD schema
# %end

# %flag
# % key: c
# % description: Remove and print not active CSW connection resources from XML file
# %end

# %flag
# % key: k
# % description: Remove and print not valid CSW connections resources from XML file
# %end

# %rules
# % exclusive: -a, -i
# % exclusive: -v, -n
# % exclusive: -a, -n
# % exclusive: -i, -n
# %end


import http
import io
import os
import sys
import urllib
import urllib.request as urlrequest
from enum import Enum

import grass.script as gscript
from grass.script.core import percent
from grass.script.utils import set_path

set_path(modulename="wx.metadata", dirname="mdlib", path="..")

from mdlib import globalvar

HEADERS = {}

HTTP_STATUS_CODES = list(http.HTTPStatus)

MODULES = {
    "lxml": {
        "check_version": False,
    },
    "owslib": {
        "check_version": True,
        "package": ["owslib.csw", "owslib.ows"],
        "method": [["CatalogueServiceWeb"], ["ExceptionReport"]],
        "version": ">=0.9",
    },
    "pyexcel_ods3": {
        "check_version": False,
    },
    "validators": {
        "check_version": False,
    },
}


class UrlValidationFailure(Exception):
    pass


class FilePathDoesNotExists(Exception):
    pass


class UrlType(Enum):
    WEB = "web"
    FILE = "file"


class UpdateConnectionsResources:
    """Update/print csw connnections resources with active and valid
    csw urls

    :param str conns_resrs_xml: connections resources xml file path
    :param str conns_resrs_xsd: connections resources validation schema
    xsd file path
    :param str spreadsheet_file_url: spreadsheet file web url address
    or file path url
    :param str data_theme: data theme (ogc csw -> 'Geospatial')
    :param int csw_timeout: timeout for checking csw url activity
    :param str separator: separator inside csw connection resource string
    {Name}{Separator}{Url} (print only)
    :param bool print_info: print all (valid, not valid, active, not active)
    csw resources connections urls only
    :param bool print_summary_info: print summary info statistic
    :param bool active_csw_url: print active and valid csw urls only
    :param bool not_active_csw_url: print not active and valid csw urls only
    :param bool valid_csw_url: print valid csw urls only
    :param bool not_valid_csw_url: print not valid csw urls only
    :param bool valid_xml: validate default conections resources xml
    file against xsd schema
    :param bool active_xml_csw_url: remove and print not active csw
    connection resources from xml file
    :param bool not_valid_xml_csw_url: remove and print not valid csw
    connection resources from xml file
    """

    data_theme_opts = [
        "Addresses",
        "Agriculture",
        "Banking",
        "BusinessPolitics",
        "Chemicals",
        "Criminality",
        "Culture",
        "Education",
        "Environment",
        "Food",
        "Geospatial",
        "Government",
        "Grand Total",
        "Health",
        "IoT",
        "Language",
        "Legal",
        "Meteo",
        "NewsCadastre",
        "Research",
        "Social",
        "Statistics",
        "Taxation",
        "Transportation",
        "Utilities",
        "Various",
        "Weather",
    ]

    data_theme_opts += ["All"]

    def __init__(
        self,
        conns_resrs_xml,
        conns_resrs_xsd,
        spreadsheet_file_url,
        data_theme="Geospatial",
        csw_timeout=10,
        separator=": ",
        print_info=False,
        print_summary_info=False,
        active_csw_url=False,
        not_active_csw_url=False,
        valid_csw_url=False,
        not_valid_csw_url=False,
        valid_xml=False,
        active_xml_csw_url=False,
        not_valid_xml_csw_url=False,
    ):

        from mdlib.dependency import check_dependencies

        module_not_found = []
        for module in MODULES:
            if not check_dependencies(module):
                module_not_found.append(True)
        if module_not_found:
            sys.exit(1)

        try:
            global CatalogueServiceWeb, etree, ExceptionReport, get_data, validators

            import lxml.etree as etree

            from owslib.csw import CatalogueServiceWeb
            from owslib.ows import ExceptionReport

            from pyexcel_ods3 import get_data

            import validators
        except ModuleNotFoundError as e:
            msg = e.msg
            gscript.fatal(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self._spreadsheet_file_url_type = None
        self._spreadsheet_file_url = spreadsheet_file_url

        self._conns_resrs_xsd = conns_resrs_xsd
        self._conns_resrs_xml = conns_resrs_xml

        self._data_theme = data_theme
        self._active_csw_url = active_csw_url
        self._not_active_csw_url = not_active_csw_url
        self._valid_csw_url = valid_csw_url
        self._not_valid_csw_url = not_valid_csw_url
        self._csw_timeout = csw_timeout
        self._separator = separator
        self._print_info = print_info
        self._print_summary_info = print_summary_info
        self._valid_xml = valid_xml
        self._active_xml_csw_url = active_xml_csw_url
        self._not_valid_xml_csw_url = not_valid_xml_csw_url

        self._downloaded_file = None
        self._xml_root = None
        self._xml_tree = None
        self._new_connections = 0
        self._print_result = ""
        self._print_summary_result = ""
        self._file_data_key = "API_Cases"
        self._not_valid_csw_urls = []
        self._not_active_csw_urls = []
        self._xml_parser = etree.XMLParser(remove_blank_text=True)
        self._progress_message = "Percent complete..."

        # Process csw connections resources xml file
        if self._valid_xml:
            self._validate_xml(
                xml=self._conns_resrs_xml,
                xsd=self._conns_resrs_xsd,
            )
            return

        if self._active_xml_csw_url:
            self._check_active_xml_csw_url()
            return

        if self._not_valid_xml_csw_url:
            self._check_not_valid_xml_csw_url()
            return

        # Print or write new csw resources connections candidates
        if self._spreadsheet_file_url_type == UrlType.WEB:
            self._download_file()
            self._read_file(file=self._downloaded_file)
        else:
            self._read_file(file=self._spreadsheet_file_url)
        self.get_data()

    @property
    def _spreadsheet_file_url(self):
        return self.__spreadsheet_file_url

    @_spreadsheet_file_url.setter
    def _spreadsheet_file_url(self, path):
        if ("http" or "https") in path:
            self._validate_url(url=path)
            self.__spreadsheet_file_url = path
            self._spreadsheet_file_url_type = UrlType.WEB
        else:
            if not os.path.exists(path):
                gscript.fatal(
                    _(
                        "Spreadsheets file '{}' "
                        "doesn't exists.".format(
                            path,
                        ),
                    ),
                )
            if not path.lower().endswith(".ods"):
                gscript.fatal(
                    _(
                        "File '{}' is not spreadsheets file (.ods)".format(
                            path,
                        ),
                    ),
                )

            self.__spreadsheet_file_url = path
            self._spreadsheet_file_url_type = UrlType.FILE

    @property
    def _conns_resrs_xsd(self):
        return self.__conns_resrs_xsd

    @_conns_resrs_xsd.setter
    def _conns_resrs_xsd(self, path):
        if not os.path.exists(path):
            gscript.fatal(
                _(
                    "Connnections resources xsd schema file '{}' "
                    "doesn't exists.".format(
                        path,
                    ),
                ),
            )
        if not path.lower().endswith(".xsd"):
            gscript.fatal(
                _("File '{}' is not xsd file (.xsd)".format(path)),
            )
        self.__conns_resrs_xsd = path

    @property
    def _conns_resrs_xml(self):
        return self.__conns_resrs_xml

    @_conns_resrs_xml.setter
    def _conns_resrs_xml(self, path):
        if not os.path.exists(path):
            gscript.fatal(
                _(
                    "Connnections resources file '{}' "
                    "doesn't exists.".format(
                        path,
                    ),
                ),
            )
        if not path.lower().endswith(".xml"):
            gscript.fatal(
                _("File '{}' is not xml file (.xml)".format(path)),
            )
        self._validate_xml(xml=path, xsd=self._conns_resrs_xsd)
        self.__conns_resrs_xml = path

    @property
    def _data_theme(self):
        return self.__data_theme

    @_data_theme.setter
    def _data_theme(self, value):
        if value not in self.data_theme_opts:
            gscript.fatal(
                _(
                    "Param 'data_theme' args is not allowed value, "
                    "allowed values are: {}".format(
                        ", ".join(self.data_theme_opts),
                    ),
                ),
            )
        self.__data_theme = value

    @property
    def _active_csw_url(self):
        return self.__active_csw_url

    @_active_csw_url.setter
    def _active_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _("Param 'active_csw_url' arg require boolean value"),
            )
        self.__active_csw_url = value

    @property
    def _not_active_csw_url(self):
        return self.__not_active_csw_url

    @_not_active_csw_url.setter
    def _not_active_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _(
                    "Param 'not_active_csw_url' arg require boolean value",
                ),
            )
        self.__not_active_csw_url = value

    @property
    def _valid_csw_url(self):
        return self.__valid_csw_url

    @_valid_csw_url.setter
    def _valid_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _(
                    "Param 'valid_csw_url' arg require boolean value",
                ),
            )
        self.__valid_csw_url = value

    @property
    def _not_valid_csw_url(self):
        return self.__not_valid_csw_url

    @_not_valid_csw_url.setter
    def _not_valid_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _(
                    "Param 'valid_csw_url' arg require boolean value",
                ),
            )
        self.__not_valid_csw_url = value

    @property
    def _separator(self):
        return self.__separator

    @_separator.setter
    def _separator(self, value):
        if not isinstance(value, str):
            gscript.fatal(
                _(
                    "Param 'valid_csw_url' arg require str value",
                ),
            )
        self.__separator = value

    @property
    def _csw_timeout(self):
        return self.__csw_timeout

    @_csw_timeout.setter
    def _csw_timeout(self, value):
        if not isinstance(value, int):
            gscript.fatal(
                _("Param 'csw_timeout' arg require integer value"),
            )
        self.__csw_timeout = value

    @property
    def _print_info(self):
        return self.__print_info

    @_print_info.setter
    def _print_info(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _("Param 'print_info' arg require boolean value"),
            )
        self.__print_info = value

    @property
    def _print_summary_info(self):
        return self.__print_summary_info

    @_print_summary_info.setter
    def _print_summary_info(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _("Param 'print_summary_info' arg require boolean value"),
            )
        self.__print_summary_info = value

    @property
    def _active_xml_csw_url(self):
        return self.__active_xml_csw_url

    @_active_xml_csw_url.setter
    def _active_xml_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _("Param 'active_xml_csw_url' arg require boolean value"),
            )
        self.__active_xml_csw_url = value

    @property
    def _not_valid_xml_csw_url(self):
        return self.__not_valid_xml_csw_url

    @_not_valid_xml_csw_url.setter
    def _not_valid_xml_csw_url(self, value):
        if not isinstance(value, bool):
            gscript.fatal(
                _("Param 'not_valid_xml_csw_url' arg require " "boolean value"),
            )
        self.__not_valid_xml_csw_url = value

    def _download_file(self):
        """Download file"""
        if not self._downloaded_file:
            try:
                response = urlopen(
                    url=self._spreadsheet_file_url,
                    headers=HEADERS,
                )
                if not response.code == 200:
                    index = HTTP_STATUS_CODES.index(response.code)
                    desc = HTTP_STATUS_CODES[index].description
                    gscript.fatal(
                        _(
                            "Download file from <{url}>, "
                            "return status code {code}, "
                            "{desc}".format(
                                url=self._spreadsheet_file_url,
                                code=response.code,
                                desc=desc,
                            ),
                        ),
                    )
                if (
                    response.getheader("Content-Type")
                    != "application/vnd.oasis.opendocument.spreadsheet"
                ):
                    gscript.fatal(
                        _(
                            "Wrong downloaded file format. "
                            "Check url <{}>. Allowed file format is "
                            "OpenDocument Format (ODF) with .ods extension "
                            "- a spreadsheet file".format(
                                self._spreadsheet_file_url,
                            ),
                        ),
                    )

                self._downloaded_file = io.BytesIO()
                self._downloaded_file.write(response.read())

            except urllib.error.HTTPError as err:
                gscript.fatal(
                    _(
                        "Download file from <{url}>, "
                        "return status code {code}, ".format(
                            url=self._spreadsheet_file_url,
                            code=err,
                        ),
                    ),
                )
            except urllib.error.URLError:
                gscript.fatal(
                    _(
                        "Download file from <{url}>, "
                        "failed. Check internet connection.".format(
                            url=self._spreadsheet_file_url,
                        ),
                    ),
                )

    def _is_multiple_url(self, url):
        """Check if url string contains multiple url

        :param str url: url address(es)

        :return bool: multiple/single
        """
        if url.count("\n") > 1:
            return True
        return False

    def _strip_url(self, url):
        """Strip url

        :param str url: url address

        :return str: stripped url
        """
        return url.strip().split()[0].replace("\n", "")

    def _handle_multiple_url(self, url):
        """Parse multiple url from one string and valide them and check
        if csw url is active

        :param str url: url address(es)
        """
        if self._is_multiple_url(url):
            for u in url.split("\n"):
                if ("https" or "http") in u:
                    u = self._strip_url(url=u)
                    validated_url = self._validate_url(
                        url=u,
                        add_url=True,
                    )
                    if validated_url:
                        self._active_csw_url(
                            url=u,
                            add_url=True,
                        )
        else:
            validated_url = self._validate_url(
                self._strip_url(url=url),
                add_url=True,
            )

            if validated_url:
                self._is_active_csw_url(
                    self._strip_url(url=url),
                    add_url=True,
                )

    def _validate_url(self, url, add_url=False):
        """Valide url

        :param str url: url address
        :param bool add_url: append not valid url into list of not
        valid urls

        :return str/None: url string (url is valid) or None
        """
        if isinstance(
            validators.url(url),
            validators.ValidationFailure,
        ):
            if add_url:
                self._not_valid_csw_urls.append(url)
            else:
                gscript.fatal(
                    _(
                        "Validation url <{}> failure".format(url),
                    ),
                )
        else:
            return url

    def _validate_xml(self, xml, xsd):
        """Validate xml file against xsd schema

        :param str xml: xml file path
        :param str xsd: xsd file path
        """
        _xsd = etree.parse(xsd)
        xsd_schema = etree.XMLSchema(_xsd)
        if not xsd_schema.validate(etree.parse(xml)):
            gscript.fatal(
                _(
                    "Connnections resources xml file '{xml}' "
                    "is not valid.\n\n{xsd_schema}".format(
                        xml=xml,
                        xsd_schema=gscript.decode(
                            etree.tostring(
                                _xsd,
                                pretty_print=True,
                            ),
                        ),
                    ),
                ),
            )

    def _validate_xml_at_parse_time(self, xml_string):
        """Validate xml string against xsd schema at parse time

        :param str xml_string: xml string
        """
        xsd = etree.parse(self._conns_resrs_xsd)
        xml_schema = etree.XMLSchema(xsd)
        parser = etree.XMLParser(schema=xml_schema)
        try:
            etree.fromstring(xml_string, parser)
        except etree.XMLSyntaxError:
            gscript.fatal(
                _(
                    "Can't parse connection xml item string '{}'. "
                    "Xml string is not valid.".format(
                        xml_string,
                    ),
                ),
            )

    def _get_root_tag(self):
        """Get connections resources xml file root tag

        :return str: xml root tag string format
        """
        return '<{tag} version="1.0">{csw_element}</{tag}>'

    def _read_file(self, file):
        """Read spreadsheets file"""
        self._data = get_data(file, start_row=1)

    def _is_active_csw_url(self, url, add_url=False):
        """Check if csw url is active

        :param str url: url address
        :param bool add_url: append not active url into list of not
        active csw urls

        :return bool: active/not active
        """
        try:
            CatalogueServiceWeb(url, timeout=self._csw_timeout)
            return True
        except ExceptionReport as err:
            msg = "Error connecting to csw: {}, {}".format(err, url)
        except ValueError as err:
            msg = "Value Error: {}, {}".format(err, url)
        except Exception as err:
            msg = "Unknown Error: {}, {}".format(err, url)
        if add_url:
            self._not_active_csw_urls.append(url)
        return False

    def _check_active_xml_csw_url(self):
        """Check active xml csw connections resources"""
        self._parse_xml()
        not_active_csw = []

        gscript.warning(
            _(
                "Non active csw items going to be removed from connections "
                "resources xml file {xml}".format(
                    xml=self._conns_resrs_xml,
                ),
            ),
        )
        gscript.message(_(self._progress_message))
        n = len(self._xml_root)
        for i, csw in enumerate(self._xml_root):
            if not self._is_active_csw_url(url=csw.attrib["url"]):
                not_active_csw.append(
                    "{name}{separator}{url}\n".format(
                        name=csw.attrib["name"],
                        separator=self._separator,
                        url=csw.attrib["url"],
                    ),
                )
                self._xml_root.remove(csw)
            percent(i, n, 1)
        percent(1, 1, 1)

        if not_active_csw:
            self._write_xml()

        # Length of printed string 60
        not_active_csw.append(
            "Number of non active csw{count:.>35}\n".format(
                count=len(not_active_csw),
            ),
        )
        sys.stdout.write("".join(not_active_csw))

    def _check_not_valid_xml_csw_url(self):
        """Check not valid xml csw connections resources urls"""
        self._parse_xml()
        not_valid_csw_urls = []

        gscript.warning(
            _(
                "Non valid csw urls going to be removed from connections "
                "resources xml file {xml}".format(
                    xml=self._conns_resrs_xml,
                ),
            ),
        )
        gscript.message(_(self._progress_message))
        n = len(self._xml_root)
        for i, csw in enumerate(self._xml_root):
            if not self._validate_url(url=csw.attrib["url"], add_url=True):
                not_valid_csw_urls.append(
                    "{name}{separator}{url}\n".format(
                        name=csw.attrib["name"],
                        separator=self._separator,
                        url=csw.attrib["url"],
                    ),
                )
                self._xml_root.remove(csw)
            percent(i, n, 1)
        percent(1, 1, 1)

        self._not_valid_csw_urls = []

        if not_valid_csw_urls:
            self._write_xml()

        # Length of printed string 60
        not_valid_csw_urls.append(
            "Number of non valid csw urls{count:.>32}\n".format(
                count=len(not_valid_csw_urls),
            ),
        )
        sys.stdout.write("".join(not_valid_csw_urls))

    def _get_data_row(self, row, print_or_write):
        """Get data row

        param: list row: row with data
        param: method print_or_write: print or write method

        row[0] column -> API Country or type of provider*
        row[1] column -> API Provider*
        row[2] column -> Name Id*
        row[3] column -> Short description*
        row[4] column -> API URL (endpoint or link to documentation)*
        row[5] column -> Type of API*
        row[6] column -> Number of API (approx)*
        row[7] column -> Theme(s)*
        row[8] column -> Governmental Level*
        row[9] column -> Country code*
        row[10] column -> Source*
        """
        n = 1
        if self._is_multiple_url(row[5]):
            # Handle multiple urls (same item name with diff prefix number)
            for u in row[5].split("\n"):
                if "http" in u or "https" in u:
                    data_row = self._get_data_format().format(
                        country=row[1],
                        govermental_level=row[8],
                        api_provider=row[2],
                        separator=self._separator,
                        url=self._strip_url(url=u),
                    )
                    data_row = "{}. ".format(n) + data_row
                    print_or_write(data_row)
                    n += 1
        else:
            data_row = self._get_data_format().format(
                country=row[1],
                govermental_level=row[8],
                api_provider=row[2],
                separator=self._separator,
                url=self._strip_url(url=row[5]),
            )
            print_or_write(data_row)

    def _write_data(self, row):
        """Write csw reasource connection item into xml resources
        connections file

        :param list row: readed row from spreadsheets
        """
        self._get_data_row(
            row=row,
            print_or_write=self._write_csw_conn_element,
        )

    def _make_xpath_query(self, **kwargs):
        """Make xml xpath query, find existed resource connnection item
        from xml file

        :param dict kwargs: 'name: url'

        :return str: xpath '[@name=value][@url=value]'
        """
        result = []
        for n, u in kwargs.items():
            result.append("[@{name}='{url}']".format(name=n, url=u))
        return "".join(result)

    def _csw_conn_exist(self, root, **kwargs):
        """Find existed resource connnection item from xml file

        :param object root: xml root element
        :param dict kwargs: 'name: url'

        :return bool: exist/not exist'
        """
        if root.xpath("//csw{}".format(self._make_xpath_query(**kwargs))):
            return True
        return False

    def _parse_xml(self):
        """Parse connections resources xml file"""
        self._xml_tree = etree.parse(
            source=self._conns_resrs_xml,
            parser=self._xml_parser,
        )
        self._xml_root = self._xml_tree.getroot()

    def _write_xml(self):
        """Write to connnections resources xml file"""
        gscript.warning(
            _(
                "Write active and valid csw connections resources into "
                "the xml file {xml}".format(
                    xml=self._conns_resrs_xml,
                ),
            ),
        )

        self._xml_tree.write(self._conns_resrs_xml, pretty_print=True)
        self._xml_root = None
        self._xml_tree = None

    def _write_csw_conn_element(self, data_row):
        """Write new csw connection resource item into xml file

        :param str data_row: xml csw resource connection xml item string
        """

        def append_csw():
            st = etree.Element("csw", name=name, url=url)
            self._validate_xml_at_parse_time(
                xml_string=self._get_root_tag().format(
                    tag=self._xml_root.tag,
                    csw_element=etree.tostring(st).decode(),
                ),
            )
            self._xml_root.append(st)

        name, url = self._split_data_row(data_row)

        if not self._csw_conn_exist(self._xml_root, name=name, url=url):
            # Check if url is active nd valid
            if (
                url not in self._not_valid_csw_urls
                and url not in self._not_active_csw_urls
            ):
                append_csw()
                self._new_connections += 1

    def _get_data_format(self):
        """Get dat row format"""
        return "{country}, " "{govermental_level}, " "{api_provider}{separator}" "{url}"

    def _split_data_row(self, row):
        """Split data row string

        :param str row: csw resource connection item for printing
        '{Name}{Separator}{Url}'

        :return tuple: name, url
        """
        if "https" in row:
            url_start = row.index("https")
            name = row[: url_start - len(self._separator)]
            url = row[url_start:]
        elif "http" in row:
            url_start = row.index("http")
            name = row[: url_start - len(self._separator)]
            url = row[url_start:]
        return name, url

    def _print_csw_conn_element(self, row):
        """Print service candidates list

        param: list row: csw resource connection item for printing
        '{Name}{Separator}{Url}'
        """
        row_format = "{}\n"
        join_char = ""

        name, url = self._split_data_row(row)

        if self._valid_csw_url:

            # Valid and active
            if self._active_csw_url:
                if (
                    url not in self._not_valid_csw_urls
                    and url not in self._not_active_csw_urls
                ):

                    self._print_result = join_char.join(
                        [
                            self._print_result,
                            row_format.format(row),
                        ]
                    )

            # Valid and not active
            else:
                if url not in self._not_valid_csw_urls:
                    self._print_result = join_char.join(
                        [
                            self._print_result,
                            row_format.format(row),
                        ]
                    )

        elif self._not_valid_csw_url:

            if url in self._not_valid_csw_urls:
                self._print_result = join_char.join(
                    [
                        self._print_result,
                        row_format.format(row),
                    ]
                )

        else:
            if self._active_csw_url:
                # Active always valid
                if (
                    url not in self._not_valid_csw_urls
                    and url not in self._not_active_csw_urls
                ):
                    self._print_result = join_char.join(
                        [
                            self._print_result,
                            row_format.format(row),
                        ]
                    )

            elif self._not_active_csw_url:
                # Not active always valid
                if (
                    url in self._not_active_csw_urls
                    and url not in self._not_valid_csw_urls
                ):

                    self._print_result = join_char.join(
                        [
                            self._print_result,
                            row_format.format(row),
                        ]
                    )
            else:
                # Print all services
                self._print_result = join_char.join(
                    [
                        self._print_result,
                        row_format.format(row),
                    ]
                )

        self._new_connections += 1

    def _print_data(self, row):
        """Print csw reasource connection item into stdout

        :param list row: readed row from spreadsheets
        """
        self._get_data_row(
            row=row,
            print_or_write=self._print_csw_conn_element,
        )

    def _print_or_write_data(self, row):
        """Print or write csw connection reasource item

        :param list row: readed row from spreadsheets
        """
        if self._print_info:
            self._print_data(row)
        else:
            self._write_data(row)

    def _print_summary_stats(self):
        """Print summary info

        if print csw connections resources into stdout:

        - Number of new connections resource
        - Number of not valid new connnections resources urls
        - Number of not active new connnections resources
        - Sum

        if write csw connections resources into xml file:

        - Number of new added connections resource
        - Number of not valid new connnections resources urls
        - Number of not active new connnections resources
        - Sum

        Length of printed string 60
        """
        join_char = ""
        eof = "\n"

        if self._print_info:
            self._print_summary_result = join_char.join(
                [
                    self._print_summary_result,
                    (
                        "Number of new connections resource"
                        "{value:.>25}{eof}".format(
                            value=self._new_connections
                            - len(self._not_valid_csw_urls)
                            - len(self._not_active_csw_urls),
                            eof=eof,
                        )
                    ),
                ],
            )
        else:
            self._print_summary_result = join_char.join(
                [
                    self._print_summary_result,
                    (
                        "Number of new added connections resource"
                        "{value:.>19}{eof}".format(
                            value=self._new_connections
                            - len(self._not_valid_csw_urls)
                            - len(self._not_active_csw_urls),
                            eof=eof,
                        )
                    ),
                ],
            )

        self._print_summary_result = join_char.join(
            [
                self._print_summary_result,
                (
                    "Number of not valid new connnections resources urls"
                    "{value:.>8}{eof}".format(
                        value=len(self._not_valid_csw_urls),
                        eof=eof,
                    )
                ),
            ],
        )
        self._print_summary_result = join_char.join(
            [
                self._print_summary_result,
                (
                    "Number of not active new connnections resources urls"
                    "{value:.>8}{eof}".format(
                        value=len(self._not_active_csw_urls),
                        eof=eof,
                    )
                ),
            ],
        )
        self._print_summary_result = join_char.join(
            [
                self._print_summary_result,
                (
                    "Sum"
                    "{value:.>57}{eof}".format(
                        value=self._new_connections,
                        eof=eof,
                    )
                ),
            ]
        )

        sys.stdout.write(self._print_summary_result)

    def get_data(self):
        """
        Get csw list of candidates
        """
        if not self._print_info:
            self._parse_xml()

        if self._data_theme == "All":
            gscript.message(_(self._progress_message))
            n = len(self._data[self._file_data_key])
            for i, row in enumerate(self._data[self._file_data_key]):
                if row:
                    # Url validation
                    self._handle_multiple_url(url=row[5])
                    self._print_or_write_data(row)
                percent(i, n, 1)
            percent(1, 1, 1)
        else:
            gscript.message(_(self._progress_message))
            n = len(self._data[self._file_data_key])
            for i, row in enumerate(self._data[self._file_data_key]):
                if row:
                    if row[8] == self._data_theme:
                        # Url validation
                        self._handle_multiple_url(url=row[5])
                        self._print_or_write_data(row)
                percent(i, n, 1)
            percent(1, 1, 1)

        if self._print_info:
            sys.stdout.write(self._print_result)
        else:
            self._write_xml()

        if self._print_summary_info:
            self._print_summary_stats()


def file_path(path):
    """File path validation

    :param str path: file path
    """
    if os.path.isfile(path):
        return path
    else:
        raise FilePathDoesNotExists(
            "File path '{}' doesn't exist".format(
                path,
            ),
        )


def url_path(url):
    """Url path validation

    :param str url: url path
    """
    if isinstance(
        validators.url(url),
        validators.ValidationFailure,
    ):
        raise UrlValidationFailure(
            "Validation url <{}> failure".format(url),
        )
    return url


def urlopen(url, headers, *args, **kwargs):
    """Wrapper around urlopen. Same function as 'urlopen', but with the
    ability to define headers.

    :param str url: url address
    :param dict headers: https(s) headers
    """
    request = urlrequest.Request(url, headers=headers)
    return urlrequest.urlopen(request, *args, **kwargs)


def manage_proxies(proxies):
    """Manage proxies

    param: str proxies: proxies definition "http=<value>,ftp=<value>"
    """
    _proxies = {}
    for ptype, purl in (p.split("=") for p in proxies.split(",")):
        _proxies[ptype] = purl
        proxy = urlrequest.ProxyHandler(_proxies)
        opener = urlrequest.build_opener(proxy)
        urlrequest.install_opener(opener)


def manage_headers(headers):
    """Manage headers

    param: str headers: htttp(s) headers definition
    "User-Agent=<value>,Accept=<value>"
    """
    global HEADERS
    for ptype, purl in (p.split("=") for p in headers.split(",")):
        HEADERS[ptype] = purl


def strip_string(value):
    """Strip string

    :param str value: string

    :return str: stripped string
    """
    return value.strip().replace('"', "").replace("'", "")


def main():
    options, flags = gscript.parser()

    default_xml = "connections_resources.xml"
    default_xsd = "connections_resources.xsd"
    default_ods = "API-cases.ods"
    url = (
        "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/APIS4DGOV/"
        "cases/LATEST/API-cases.ods"
    )

    addon_dir = os.path.realpath(
        os.path.join(os.path.dirname(__file__), ".."),
    )
    config_dir = [addon_dir, "etc", "wx.metadata", "config"]
    if options["xml"] != default_xml:
        xml = options["xml"]
    else:
        xml = os.path.join(*config_dir + [options["xml"]])
    if options["xsd"] != default_xsd:
        xsd = options["xsd"]
    else:
        xsd = os.path.join(*config_dir + [options["xsd"]])
    if options["spreadsheet"] != default_ods:
        spreadsheet = options["spreadsheet"]
    else:
        spreadsheet = os.path.join(
            *config_dir + [options["spreadsheet"]],
        )

    options["separator"] = strip_string(options["separator"])

    if options["proxy"]:
        options["proxy"] = strip_string(options["proxy"])
        manage_proxies(proxies=options["proxy"])
    if options["header"]:
        options["header"] = strip_string(options["header"])
        manage_headers(headers=options["header"])

    if not options["url"] and not options["spreadsheet"]:
        gscript.fatal(
            _("Set 'url=' or 'spreadsheet=' parameter argument"),
        )
    if options["url"] and options["spreadsheet"]:
        spreadsheet = options["url"]
        gscript.warning(
            _(
                "Use spreadsheet file url '{}' for getting new csw "
                "resources connections candidates".format(
                    url,
                ),
            ),
        )

    if (flags["a"] or flags["i"] or flags["v"] or flags["n"]) and not flags["p"]:
        flags["p"] = True

    if flags["w"]:
        sys.stdout.write("{}\n".format(url))
        return

    if flags["l"]:
        sys.stdout.write(
            "{}\n".format(
                os.path.join(*config_dir + [options["spreadsheet"]]),
            ),
        )
        return

    UpdateConnectionsResources(
        spreadsheet_file_url=spreadsheet,
        conns_resrs_xml=xml,
        conns_resrs_xsd=xsd,
        separator=options["separator"],
        csw_timeout=int(options["timeout"]),
        active_csw_url=flags["a"],
        not_active_csw_url=flags["i"],
        valid_csw_url=flags["v"],
        not_valid_csw_url=flags["n"],
        print_info=flags["p"],
        print_summary_info=flags["s"],
        valid_xml=flags["x"],
        active_xml_csw_url=flags["c"],
        not_valid_xml_csw_url=flags["k"],
    )


if __name__ == "__main__":
    sys.exit(main())
