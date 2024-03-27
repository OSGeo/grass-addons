#!/usr/bin/env python

"""
@package jinjainfo
@module g.gui.metadata
@brief  Library for parsing information from jinja template

Classes:
 - jinjainfo::MdDescription
 - jinjainfo::JinjaTemplateParser

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

import sys

from . import globalvar


class MdDescription:
    """Object which is initialzed by jinja template in '{# #}'"""

    def __init__(
        self,
        tag=None,
        object=None,
        name="",
        desc=None,
        example=None,
        type=None,
        multi=0,
        inboxmulti=None,
        group=None,
        inbox=None,
        multiline=None,
        validator=None,
        num=None,
        ref=None,
        selfInfoString=None,
        database=None,
    ):
        """
        @param tag: OWSLib object which will be replaced by value of object after jinja template system renders new file
        @param object: some objects in OWSLib need to be initialized temporally in gui generator. Others are initialized by configure file
        @param name:  label and tooltip name
        @param desc: description/definition of metadata item
        @param example: example of md item (tooltip)
        @param type: data type, necessary to validate widgets
        @param multi: 0=only one instance of editor::MdItem widget can be, 1= multiple instances of widgets can be
        @param inboxmulti: 0=static box of items has not button for duplicating self 1=has button
        @param group: this param initializes page in notebook in mani editor
        @param inbox: Every item in block of code in jinja template must have same value of inbox.
               The value of inbox representing label of static box in gui.
        @param multiline: If true- textCtrl widget will be initalized with multiline control
        @param validator: Currently not used
        @param ref: additional information about reference of metadata item (ISO reference)
        @param selfInfoString: string value representing all these information (parsed from jinja template)
        @var mdItem: very important parameter which holds instances of widgets(editor::MdItem)
             on every index of list is one instance of widget. In case, if is in static box MdItem with duplicating button:
            index of list is represented by list of these items
        @var statements: hold information about first statement in block
        @var statements1: hold info about second statement in block of var: statement
        """
        self.tag = tag
        self.object = object
        self.name = name
        self.desc = desc
        self.example = example
        self.type = type
        self.multiplicity = multi  # multiplicity of MD item
        self.group = group
        self.inbox = inbox
        self.ref = ref
        self.databaseAttr = database
        self.selfInfoString = selfInfoString

        self.inboxmulti = inboxmulti
        self.multiline = multiline  # type of ctrl text
        self.validator = validator
        # --info from jinja -end

        self.statements = None
        self.statements1 = None
        self.mdItem = list()

    def addMdItem(self, newMdItem, oldMdItem=None):
        """care about integrity of var: self.mdItem"""
        # if new mditem is from box- need to hold information
        # about it (list on the same index in self.mdItem)
        if oldMdItem is not None:
            for n, item in enumerate(self.mdItem):
                for i in item:
                    if i == oldMdItem:
                        self.mdItem[n].append(newMdItem)
        else:
            self.mdItem.append(newMdItem)

    def removeMdItem(self, item):
        """care about integrity of var: self.mdItem"""
        try:
            for k, oldListItem in enumerate(self.mdItem):
                for i in oldListItem:
                    if oldListItem == item:
                        self.mdItem[k].remove(item)
        except:
            self.mdItem.remove(item)

    def addStatements(self, stat):
        if self.statements is None:
            self.statements = stat

    def addStatements1(self, stat):
        if self.statements1 is None:
            self.statements1 = stat


class JinjaTemplateParser:
    """Parser of OWSLib tag and init. values of jinjainfo::MdDescription from jinja template."""

    def __init__(self, template):
        """
        @var mdDescription: list of jinjainfo::mdDescription
        @var mdOWSTag: list of tags in jinja templates
        @var mdOWSTagStr: string representing OWSLib tags from template (per line)
        @var mdOWSTagStrList: on each index of list is one line with parsed OWSLib tag
        """

        try:
            global GError, mdutil

            from core.gcmd import GError

            from . import mdutil
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.mdDescription = []
        self.mdOWSTag = []
        self.template = template

        self.mdOWSTagStr = ""
        self.mdOWSTagStrList = []

        self._readJinjaInfo()
        self._readJinjaTags()
        self._formatMdOWSTagStrToPythonBlocks()

    def _readJinjaTags(self):
        """Parser of OWSLib tag from jinja template to list"""
        try:
            with open(self.template, "r") as f:
                for line in f:

                    # if found start of comments
                    if str(line).find("{{") != -1:
                        obj = mdutil.findBetween(line, "{{", "}}")
                        self.mdOWSTag.append(obj)

                    if str(line).find("{%") != -1:
                        obj = mdutil.findBetween(line, "{%", "-%}")
                        self.mdOWSTag.append(obj)

        except:
            GError("Cannot open jinja template")
            # print "I/O error({0}): {1}".format(e.errno, e.strerror)

    def _readJinjaInfo(self):
        """Parser  of 'comments'({# #}) in jinja template which are represented by jinjainfo::MdDescription
        parsed values initializing list of jinjainfo::MdDesctiption obect
        """
        try:
            with open(self.template, "r") as f:
                for line in f:
                    # if found start of comments
                    if str(line).find("{#") != -1:
                        values = mdutil.findBetween(line, "{#", "#}")
                        values1 = mdutil.findBetween(line, "{%", "#}")
                        values2 = mdutil.findBetween(line, "{{", "#}")
                        if values1 != "":
                            values += ",selfInfoString='''{%" + values1 + "#}'''"
                        else:
                            values += ",selfInfoString='''{{" + values2 + "#}'''"

                        exe_str = (
                            "self.mdDescription.append(MdDescription(%s))" % values
                        )
                        exe_str = exe_str.encode("utf-8", "ignore")
                        eval(exe_str)
        except:
            GError("Cannot open jinja template")
            # print "I/O error({0}): {1}".format(e.errno, e.strerror)

    def _formatMdOWSTagStrToPythonBlocks(self):
        """Formatting of parsed tags to pythonic blocks"""
        self.mdOWSTagStr = ""
        tab = 0
        for item in self.mdOWSTag:
            if str(item).find(" endfor ") != -1 or str(item).find(" endif ") != -1:
                tab -= 1
                continue

            tabstr = "\t" * tab
            str1 = tabstr + item[1:] + "\n"
            self.mdOWSTagStr += str1
            self.mdOWSTagStrList.append(tabstr + item[1:])

            if str(item).find(" for ") != -1 or str(item).find(" if ") != -1:
                tab += 1
