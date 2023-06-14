#!/usr/bin/env python

"""
@package mdgrass
@module  v.info.iso, r.info.iso, g.gui.metadata
@brief   Global methods for metadata management

Methods:
-mdutil::removeNonAscii
-mdutil::yesNo
-mdutil::findBetween
-mdutil::replaceXMLReservedChar
-mdutil::pathToMapset
-mdutil::grassProfileValidator
-mdutil::isnpireValidator

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

import importlib
import os
import string
import sys
from subprocess import PIPE

from grass.pygrass.modules import Module
from grass.pygrass.utils import get_lib_path
from grass.script import core as grass

import wx


class Owslib:
    """Lazy import of 'owslib.iso' module"""

    iso = importlib.import_module("owslib.iso", "owslib")
    util = importlib.import_module("owslib.util", "owslib")


class StaticContext(object):
    def __init__(self):
        self.ppath = os.path.dirname(os.path.abspath(__file__))

        self.confDirPath = os.path.join(
            os.getenv("GRASS_ADDON_BASE"),
            "etc",
            "wx.metadata",
            "config",
        )
        path = os.path.join("wx.metadata", "config")
        self.connResources = get_lib_path(
            modname=path,
            libname="connections_resources.xml",
        )
        if self.connResources is None:
            grass.fatal(
                "Fatal error: library < {} > not found".format(path),
            )
        else:
            self.connResources = os.path.join(
                self.connResources,
                "connections_resources.xml",
            )

        self.configureLibPath = get_lib_path(
            modname=path,
            libname="init_md.txt",
        )
        if self.configureLibPath is None:
            grass.fatal(
                "Fatal error: library < {} > not found".format(path),
            )

        path = os.path.join("wx.metadata", "profiles")
        self.profilesLibPath = get_lib_path(
            modname=path,
            libname="basicProfile.xml",
        )
        if self.profilesLibPath is None:
            grass.fatal("Fatal error: library < %s > not found" % path)

        self.lib_path = os.path.normpath(
            os.path.join(self.configureLibPath, os.pardir),
        )


def isTableExists(name):
    res = Module("db.tables", flags="p", stdout_=PIPE)
    for line in res.outputs.stdout.splitlines():
        if name == line:
            return True
    return False


def removeNonAscii(s):
    """Removed non ASCII chars"""
    s = [x for x in s if x in string.printable]
    return "".join(s)


def yesNo(parent, question, caption="Yes or no?"):
    dlg = wx.MessageDialog(
        parent,
        question,
        caption,
        wx.YES_NO | wx.ICON_QUESTION,
    )
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result


def findBetween(s, first, last):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)
        return s[start:end]
    except ValueError:
        return ""


def replaceXMLReservedChar(inp):
    if inp:
        import re

        inp = re.sub("<", "&lt;", inp)
        inp = re.sub(">", "&gt;", inp)
        inp = re.sub("&", "&amp;", inp)
        inp = re.sub("%", "&#37;", inp)
    return inp


def pathToMapset():
    gisenvDict = grass.gisenv()
    return os.path.join(
        gisenvDict["GISDBASE"],
        gisenvDict["LOCATION_NAME"],
        gisenvDict["MAPSET"],
    )


def grassProfileValidator(md):
    """Validation of GRASS BASIC XML-OWSLib  file-object"""

    result = {}
    result["status"] = "succeded"
    result["errors"] = []
    result["num_of_errors"] = "0"
    errors = 0

    if md.identification is None:
        result["errors"].append("gmd:CI_ResponsibleParty: Organization name is missing")
        result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
        result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
        result["errors"].append("gmd:md_DataIdentification: Title is missing")
        result["errors"].append("gmd:md_DataIdentification: Abstract is missing")
        result["errors"].append("gmd:md_ScopeCode: Resource type is missing")
        result["errors"].append(
            "gmd:RS_Identifier: Unique Resource Identifier is missing"
        )
        result["errors"].append("gmd:EX_Extent: Extent element is missing")
        result["errors"].append("gmd:EX_GeographicBoundingBox: Bounding box is missing")
        result["errors"].append(
            "Both gmd:EX_TemporalExtent and gmd:CI_Date are missing"
        )
        result["errors"].append("gmd:useLimitation is missing")
        errors += 20
    else:
        if len(md.identification.contact) < 1 or md.identification.contact is None:
            result["errors"].append(
                "gmd:CI_ResponsibleParty: Organization name is missing"
            )
            result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
            result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
            errors += 3
        else:
            if md.identification.contact[0].organization is (None or ""):
                result["errors"].append(
                    "gmd:CI_ResponsibleParty: Organization name is missing"
                )
                errors += 1

            if md.identification.contact[0].email is (None or ""):
                result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
                errors += 1

            if md.identification.contact[0].role is (None or ""):
                result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
                errors += 1

        if md.identification.title is (None or ""):
            result["errors"].append("gmd:md_DataIdentification: Title is missing")
            errors += 1
        if md.identification.abstract is (None or ""):
            result["errors"].append("gmd:md_DataIdentification: Abstract is missing")
            errors += 1
        if md.identification.identtype == "":
            result["errors"].append("gmd:md_ScopeCode: Resource type is missing")
            errors += 1

        if md.identification.extent is None:
            result["errors"].append("gmd:EX_Extent: Extent element is missing")
            errors += 4
        else:
            if md.identification.extent.boundingBox is None:
                result["errors"].append(
                    "gmd:EX_GeographicBoundingBox: Bounding box is missing"
                )
                errors += 4
            else:
                if md.identification.extent.boundingBox.minx is (None or ""):
                    result["errors"].append("gmd:westBoundLongitude: minx is missing")
                    errors += 1
                if md.identification.extent.boundingBox.maxx is (None or ""):
                    result["errors"].append("gmd:eastBoundLongitude: maxx is missing")
                    errors += 1
                if md.identification.extent.boundingBox.miny is (None or ""):
                    result["errors"].append("gmd:southBoundLatitude: miny is missing")
                    errors += 1
                if md.identification.extent.boundingBox.maxy is (None or ""):
                    result["errors"].append("gmd:northBoundLatitude: maxy is missing")
                    errors += 1

        if len(md.identification.date) < 1 or (
            md.identification.temporalextent_start is (None or "")
            or md.identification.temporalextent_end is (None or "")
        ):
            result["errors"].append(
                "Both gmd:EX_TemporalExtent and gmd:CI_Date are missing"
            )
            errors += 1

    if md.datestamp is (None or ""):
        result["errors"].append("gmd:dateStamp: Date is missing")
        errors += 1

    if md.identifier is (None or ""):
        result["errors"].append("gmd:identifier: Identifier is missing")
        errors += 1

    if md.contact is None:
        result["errors"].append("gmd:contact: Organization name is missing")
        result["errors"].append("gmd:contact: E-mail is missing")
        result["errors"].append("gmd:role: Role is missing")
        errors += 3
    else:
        if md.contact[0].organization is (None or ""):
            result["errors"].append("gmd:contact: Organization name is missing")
            errors += 1

        if md.contact[0].email is (None or ""):
            result["errors"].append("gmd:contact: E-mail is missing")
            errors += 1

        if md.contact[0].role is (None or ""):
            result["errors"].append("gmd:role: Role is missing")
            errors += 1

    if errors > 0:
        result["status"] = "failed"
        result["num_of_errors"] = str(errors)
    return result


def isnpireValidator(md):
    """Validation INSPIRE  XML-OWSLib file-object"""

    result = {}
    result["status"] = "succeded"
    result["errors"] = []
    result["num_of_errors"] = "0"
    errors = 0

    if md.identification is None:
        result["errors"].append("gmd:CI_ResponsibleParty: Organization name is missing")
        result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
        result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
        result["errors"].append("gmd:md_DataIdentification: Title is missing")
        result["errors"].append("gmd:md_DataIdentification: Abstract is missing")
        result["errors"].append("gmd:md_ScopeCode: Resource type is missing")
        result["errors"].append("gmd:language: Resource language is missing")
        result["errors"].append(
            "gmd:RS_Identifier: Unique Resource Identifier is missing"
        )
        result["errors"].append("gmd:topicCategory: TopicCategory is missing")
        result["errors"].append("gmd:md_Keywords: Keywords are missing")
        result["errors"].append("gmd:thesaurusName: Thesaurus title is missing")
        result["errors"].append("gmd:thesaurusName: Thesaurus date is missing")
        result["errors"].append("gmd:thesaurusName: Thesaurus date type is missing")
        result["errors"].append("gmd:EX_Extent: Extent element is missing")
        result["errors"].append("gmd:EX_GeographicBoundingBox: Bounding box is missing")
        result["errors"].append(
            "Both gmd:EX_TemporalExtent and gmd:CI_Date are missing"
        )
        result["errors"].append("gmd:useLimitation is missing")
        result["errors"].append("gmd:accessConstraints is missing")
        result["errors"].append("gmd:otherConstraints is missing")
        errors += 20
    else:
        if md.identification.contact is None or len(md.identification.contact) < 1:
            result["errors"].append(
                "gmd:CI_ResponsibleParty: Organization name is missing"
            )
            result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
            result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
            errors += 3

        else:
            if md.identification.contact[0].organization is (None or ""):
                result["errors"].append(
                    "gmd:CI_ResponsibleParty: Organization name is missing"
                )
                errors += 1

            if md.identification.contact[0].email is (None or ""):
                result["errors"].append("gmd:CI_ResponsibleParty: E-mail is missing")
                errors += 1

            if md.identification.contact[0].role is (None or ""):
                result["errors"].append("gmd:CI_ResponsibleParty: Role is missing")
                errors += 1

        if md.identification.title is (None or ""):
            result["errors"].append("gmd:md_DataIdentification: Title is missing")
            errors += 1
        if md.identification.abstract is (None or ""):
            result["errors"].append("gmd:md_DataIdentification: Abstract is missing")
            errors += 1
        if md.identification.identtype is (None or ""):
            result["errors"].append("gmd:md_ScopeCode: Resource type is missing")
            errors += 1

        if md.identification.resourcelanguage is None:
            errors += 1
            result["errors"].append("gmd:language: Resource language is missing")
        else:
            if (
                len(md.identification.resourcelanguage) < 1
                or md.identification.resourcelanguage[0] == ""
            ):
                result["errors"].append("gmd:language: Resource language is missing")
                errors += 1

        if md.identification.uricode is None:
            result["errors"].append(
                "gmd:RS_Identifier: Unique Resource Identifier is missing"
            )
            errors += 1
        else:
            if len(md.identification.uricode) < 1 or md.identification.uricode[0] == "":
                result["errors"].append(
                    "gmd:RS_Identifier: Unique Resource Identifier is missing"
                )
                errors += 1

        if md.identification.topiccategory is None:
            result["errors"].append("gmd:topicCategory: TopicCategory is missing")
            errors += 1
        else:
            if (
                len(md.identification.topiccategory) < 1
                or md.identification.topiccategory[0] == ""
            ):
                result["errors"].append("gmd:topicCategory: TopicCategory is missing")
                errors += 1

        if md.identification.keywords is None or len(md.identification.keywords) < 1:
            result["errors"].append("gmd:MD_Keywords: Keywords are missing")
            result["errors"].append("gmd:thesaurusName: Thesaurus title is missing")
            result["errors"].append("gmd:thesaurusName: Thesaurus date is missing")
            result["errors"].append("gmd:thesaurusName: Thesaurus date type is missing")
            errors += 4

        else:
            if (
                md.identification.keywords[0]["keywords"] is None
                or len(md.identification.keywords[0]["keywords"]) < 1
                or str(md.identification.keywords[0]["keywords"]) == "[u'']"
            ):
                result["errors"].append("gmd:MD_Keywords: Keywords are missing")
                errors += 1
            if md.identification.keywords[0]["thesaurus"] is None:
                result["errors"].append("gmd:thesaurusName: Thesaurus title is missing")
                result["errors"].append("gmd:thesaurusName: Thesaurus date is missing")
                result["errors"].append(
                    "gmd:thesaurusName: Thesaurus date type is missing"
                )
                errors += 3
            else:
                title = md.identification.keywords[0]["thesaurus"]["title"]
                if title is None or len(title) < 1:
                    result["errors"].append(
                        "gmd:thesaurusName: Thesaurus title is missing"
                    )
                    errors += 1
                date = md.identification.keywords[0]["thesaurus"]["date"]
                if date is None or len(date) < 1:
                    result["errors"].append(
                        "gmd:thesaurusName: Thesaurus date is missing"
                    )
                    errors += 1
                datetype = md.identification.keywords[0]["thesaurus"]["datetype"]
                if datetype is None or len(datetype) < 1:
                    result["errors"].append(
                        "gmd:thesaurusName: Thesaurus date type is missing"
                    )
                    errors += 1

        if md.identification.extent is None:
            result["errors"].append("gmd:EX_Extent: Extent element is missing")
            errors += 1
        else:
            if md.identification.extent.boundingBox is None:
                result["errors"].append(
                    "gmd:EX_GeographicBoundingBox: Bounding box is missing"
                )
                errors += 1
            else:
                if md.identification.extent.boundingBox.minx is (None or ""):
                    result["errors"].append("gmd:westBoundLongitude: minx is missing")
                    errors += 1
                if md.identification.extent.boundingBox.maxx is (None or ""):
                    result["errors"].append("gmd:eastBoundLongitude: maxx is missing")
                    errors += 1
                if md.identification.extent.boundingBox.miny is (None or ""):
                    result["errors"].append("gmd:southBoundLatitude: miny is missing")
                    errors += 1
                if md.identification.extent.boundingBox.maxy is (None or ""):
                    result["errors"].append("gmd:northBoundLatitude: maxy is missing")
                    errors += 1

        if len(md.identification.date) < 1 or (
            md.identification.temporalextent_start is (None or "")
            or md.identification.temporalextent_end is (None or "")
        ):
            result["errors"].append(
                "Both gmd:EX_TemporalExtent and gmd:CI_Date are missing"
            )
            errors += 1

        if (
            len(md.identification.uselimitation) < 1
            or md.identification.uselimitation[0] == ""
        ):
            result["errors"].append("gmd:useLimitation is missing")
            errors += 1
        if (
            len(md.identification.accessconstraints) < 1
            or md.identification.accessconstraints[0] == ""
        ):
            result["errors"].append("gmd:accessConstraints is missing")
            errors += 1
        if (
            len(md.identification.otherconstraints) < 1
            or md.identification.otherconstraints[0] == ""
        ):
            result["errors"].append("gmd:otherConstraints is missing")
            errors += 1

    if md.languagecode is (None or ""):
        result["errors"].append("gmd:LanguageCode: Language code is missing")
        errors += 1
    if md.datestamp is (None or ""):
        result["errors"].append("gmd:dateStamp: Date is missing")
        errors += 1
    if md.identifier is (None or ""):
        result["errors"].append("gmd:identifier: Identifier is missing")
        errors += 1
    if md.dataquality is (None or ""):
        result["errors"].append("gmd:LI_Lineage is missing")
        result["errors"].append("gmd:DQ_ConformanceResult: Date is missing")
        result["errors"].append("gmd:DQ_ConformanceResult: Date type is missing")
        # result["errors"].append(
        #     "gmd:DQ_ConformanceResult: Degree is missing")
        result["errors"].append("gmd:DQ_ConformanceResult: Title is missing")
        errors += 4
    else:
        if md.dataquality.lineage is (None or ""):
            result["errors"].append("gmd:LI_Lineage is missing")
            errors += 1
        if (
            len(md.dataquality.conformancedate) < 1
            or md.dataquality.conformancedate[0] == ""
        ):
            result["errors"].append("gmd:DQ_ConformanceResult: Date is missing")
            errors += 1
        if (
            len(md.dataquality.conformancedatetype) < 1
            or md.dataquality.conformancedatetype[0] == ""
        ):
            result["errors"].append("gmd:DQ_ConformanceResult: Date type is missing")
            errors += 1
        # if len(md.dataquality.conformancedegree) < 1:
        #     result["errors"].append(
        #         "gmd:DQ_ConformanceResult: Degree is missing")
        #     errors += 1
        if (
            len(md.dataquality.conformancetitle) < 1
            or md.dataquality.conformancetitle[0] == ""
        ):
            result["errors"].append("gmd:DQ_ConformanceResult: Title is missing")
            errors += 1

    if md.contact is None or len(md.contact) < 1:
        result["errors"].append("gmd:contact: Organization name is missing")
        result["errors"].append("gmd:contact: E-mail is missing")
        result["errors"].append("gmd:role: Role is missing")
        errors += 3
    else:
        if md.contact[0].organization is (None or ""):
            result["errors"].append("gmd:contact: Organization name is missing")
            errors += 1

        if md.contact[0].email is (None or ""):
            result["errors"].append("gmd:contact: E-mail is missing")
            errors += 1

        if md.contact[0].role is (None or ""):
            result["errors"].append("gmd:role: Role is missing")
            errors += 1

    if errors > 0:
        result["status"] = "failed"
        result["num_of_errors"] = str(errors)

    return result


class MD_DataIdentification_MOD(Owslib.iso.MD_DataIdentification):
    def __init__(self, md=None, identtype=None):
        Owslib.iso.MD_DataIdentification.__init__(
            self,
            md,
            identtype,
        )
        if md is None:
            self.timeUnit = None
            self.temporalType = None
            self.timeUnit = None
            self.factor = None
            self.radixT = None
        else:
            val2 = None
            val1 = None
            val3 = None
            val4 = None
            extents = md.findall(
                Owslib.util.nspath_eval("gmd:extent", Owslib.iso.namespaces),
            )
            extents.extend(
                md.findall(
                    Owslib.util.nspath_eval("srv:extent", Owslib.iso.namespaces),
                ),
            )
            for extent in extents:
                if val2 is None:
                    duration = (
                        "gmd:EX_Extent/gmd:temporalElement/"
                        "gmd:EX_TemporalExtent/gmd:extent/"
                        "gml:TM_PeriodDuration/gml:duration"
                    )
                    val2 = extent.find(
                        Owslib.util.nspath_eval(
                            duration,
                            Owslib.iso.namespaces,
                        ),
                    )  # TODO
                self.temporalType = Owslib.util.testXMLValue(val2)

                if val1 is None:
                    time_unit_type = (
                        "gmd:EX_Extent/gmd:temporalElement/"
                        "gmd:EX_TemporalExtent/gmd:extent/"
                        "gml:timeLength/gml:timeInterval/"
                        "gml:unit/gml:TimeUnitType"
                    )
                    val1 = extent.find(
                        Owslib.util.nspath_eval(
                            time_unit_type,
                            Owslib.iso.namespaces,
                        ),
                    )
                self.timeUnit = Owslib.util.testXMLValue(val1)
                if val3 is None:
                    positive_int = (
                        "gmd:EX_Extent/gmd:temporalElement/"
                        "gmd:EX_TemporalExtent/gmd:extent/"
                        "gml:timeLength/gml:timeInterval/"
                        "gml:radix/gco:positiveInteger"
                    )
                    val3 = extent.find(
                        Owslib.util.nspath_eval(
                            positive_int,
                            Owslib.iso.namespaces,
                        ),
                    )
                self.radixT = Owslib.util.testXMLValue(val3)

                if val4 is None:
                    integer = (
                        "gmd:EX_Extent/gmd:temporalElement/"
                        "gmd:EX_TemporalExtent/gmd:extent/"
                        "gml:timeLength/gml:timeInterval/"
                        "gml:factor/gco:Integer"
                    )
                    val4 = extent.find(
                        Owslib.util.nspath_eval(
                            integer,
                            Owslib.iso.namespaces,
                        ),
                    )
                self.factor = Owslib.util.testXMLValue(val4)


class MD_MetadataMOD(Owslib.iso.MD_Metadata):
    """Process gmd:MD_Metadata"""

    def __init__(self, md=None):
        Owslib.iso.MD_Metadata.__init__(self, md)
        if md is not None:
            val = md.find(
                Owslib.util.nspath_eval(
                    "gmd:identificationInfo/gmd:MD_DataIdentification",
                    Owslib.iso.namespaces,
                ),
            )
            val2 = md.find(
                Owslib.util.nspath_eval(
                    "gmd:identificationInfo/srv:SV_ServiceIdentification",
                    Owslib.iso.namespaces,
                ),
            )

            if val is not None:
                self.identification = MD_DataIdentification_MOD(val, "dataset")
                self.serviceidentification = None
            elif val2 is not None:
                self.identification = MD_DataIdentification_MOD(
                    val2,
                    "service",
                )
                self.serviceidentification = Owslib.iso.SV_ServiceIdentification(val2)
            else:
                self.identification = None
                self.serviceidentification = None

            self.identificationinfo = []
            for idinfo in md.findall(
                Owslib.util.nspath_eval(
                    "gmd:identificationInfo",
                    Owslib.iso.namespaces,
                ),
            ):
                val = list(idinfo)[0]
                tagval = Owslib.util.xmltag_split(val.tag)
                if tagval == "MD_DataIdentification":
                    self.identificationinfo.append(
                        MD_DataIdentification_MOD(val, "dataset"),
                    )
                elif tagval == "MD_ServiceIdentification":
                    self.identificationinfo.append(
                        MD_DataIdentification_MOD(val, "service"),
                    )
                elif tagval == "SV_ServiceIdentification":
                    self.identificationinfo.append(
                        Owslib.iso.SV_ServiceIdentification(val),
                    )

            val = md.find(
                Owslib.util.nspath_eval(
                    "gmd:distributionInfo/gmd:MD_Distribution",
                    Owslib.iso.namespaces,
                ),
            )
