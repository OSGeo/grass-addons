#!/usr/bin/env python

"""
@package editor
@module g.gui.metadata
@brief base editor, read/write ISO metadata, generator of widgets in editor

Classes:
 - editor::MdFileWork
 - editor::MdBox
 - editor::MdWxDuplicator
 - editor::MdItem
 - editor::MdNotebookPage
 - editor::MdMainEditor

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""

import contextlib
import os
import re
import sys
import tempfile
from subprocess import PIPE

from grass.pygrass.modules import Module

from gui_core.widgets import (
    EmailValidator,
    IntegerValidator,
    NTCValidator,
    SimpleValidator,
    TimeISOValidator,
)

import wx
import wx.lib.scrolledpanel as scrolled

from . import globalvar
from .mdjinjaparser import JinjaTemplateParser

# =========================================================================
# MD filework
# =========================================================================
ADD_RM_BUTTON_SIZE = (35, 35)


class MdFileWork:

    """initializer of metadata in OWSLib and export OWSLib object to xml by jinja template system"""

    def __init__(self, pathToXml=None):

        try:
            global Environment, FileSystemLoader, etree, GError, GMessage, mdutil

            from jinja2 import Environment, FileSystemLoader
            from lxml import etree

            from core.gcmd import GError, GMessage

            from . import mdutil
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.path = pathToXml
        self.owslibInfo = None

    def initMD(self, path=None):
        """
        @brief initialize metadata
        @param path: path to xml
        @return: initialized md object by input xml
        """
        if path is None:
            self.md = mdutil.get_md_metadatamod_inst(md=None)
            return self.md
        else:
            io = open(path, "r")
            str1 = ""
            for line in io.readlines():
                str1 += mdutil.removeNonAscii(line)
            io.close()
            io1 = open(path, "w")
            io1.write(str1)
            io1.close()

            try:
                tree = etree.parse(path)
                root = tree.getroot()
                self.md = mdutil.get_md_metadatamod_inst(root)

                return self.md

            except Exception as e:
                GError("Error loading xml:\n" + str(e))

    def saveToXML(
        self,
        md,
        owsTagList,
        jinjaPath,
        outPath=None,
        xmlOutName=None,
        msg=True,
        rmTeplate=False,
    ):
        """
        @note creator of xml with using OWSLib md object and jinja template
        @param md: owslib.iso.MD_Metadata
        @param owsTagList: in case if user is defining template
        @param jinjaPath: path to jinja template
        @param outPath: path of exported xml
        @param xmlOutName: name of exported xml
        @param msg: gmesage info after export
        @param rmTeplate: remove template after use
        @return: initialized md object by input xml
        """
        # if  output file name is None, use map name and add postfix
        self.dirpath = os.path.dirname(os.path.realpath(__file__))
        self.md = md
        self.owsTagList = owsTagList

        if xmlOutName is None:
            xmlOutName = "RANDExportMD"  # TODO change to name of map
        if not xmlOutName.lower().endswith(".xml"):
            xmlOutName += ".xml"
        # if path is None, use lunch. dir
        if not outPath:
            outPath = os.path.join(self.dirpath, xmlOutName)
        else:
            outPath = os.path.join(outPath, xmlOutName)
        xml = open(jinjaPath, "r")

        str1 = ""
        for line in xml.readlines():
            line = mdutil.removeNonAscii(line)
            str1 += line
        xml.close
        try:
            io = open(jinjaPath, "w")
            io.write(str1)
            io.close()
        except Exception as err:
            print(
                "WARNING: Cannot check and remove non ascii characters from template err:< %s >"
                % err
            )

        # generating xml using jinja templates
        head, tail = os.path.split(jinjaPath)
        env = Environment(loader=FileSystemLoader(head))
        env.globals.update(zip=zip)
        template = env.get_template(tail)
        if self.owsTagList is None:
            iso_xml = template.render(md=self.md)
        else:
            iso_xml = template.render(md=self.md, owsTagList=self.owsTagList)
        xml_file = xmlOutName

        try:
            xml_file = open(outPath, "w")
            xml_file.write(iso_xml)
            xml_file.close()

            if msg:
                GMessage("File is exported to: %s" % outPath)

            if rmTeplate:
                os.remove(jinjaPath)

            return outPath

        except Exception as e:
            GError("Error writing xml:\n" + str(e))


# =========================================================================
# CREATE BOX (staticbox+button(optional)
# =========================================================================


class MdBox(wx.Panel):

    """widget(static box) which include metadata items (MdItem)"""

    def __init__(self, parent, label="label"):
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.label = label
        self.mdItems = list()
        self.stbox = wx.StaticBox(
            self, label=label, id=wx.ID_ANY, style=wx.RAISED_BORDER
        )
        self.stbox.SetForegroundColour((0, 0, 0))
        self.stbox.SetBackgroundColour((200, 200, 200))
        self.stbox.SetFont(wx.Font(12, wx.NORMAL, wx.NORMAL, wx.NORMAL))

    def addItems(self, items, multi=True, rmMulti=False, isFirstNum=-1):
        """
        @param items: editor::MdItems
        @param multi: true in case when box has button for duplicating box and included items
        @param rmMulti: true in case when box has button for removing box and included items
        @param isFirstNum: handling with 'add' and 'remove' button of box.
                            this param is necessary for generating editor in editor::MdEditor.generateGUI.inBlock()
                            note: just first generated box has 'add' button (because being mandatory) and next others has
                            'remove' button
        """
        if isFirstNum != 1:
            multi = False
            rmMulti = True

        # if not initialize in jinja template (default is true)
        if multi is None:
            multi = True

        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.panelSizer)

        self.boxButtonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.panelSizer.AddSpacer(5)
        self.panelSizer.Add(self.boxButtonSizer, flag=wx.EXPAND, proportion=1)

        self.stBoxSizer = wx.StaticBoxSizer(self.stbox, orient=wx.VERTICAL)
        self.boxButtonSizer.Add(self.stBoxSizer, flag=wx.EXPAND, proportion=1)

        for item in items:
            self.mdItems.append(item)
            self.stBoxSizer.Add(item, flag=wx.EXPAND, proportion=1)
            self.stBoxSizer.AddSpacer(5)

        if multi:
            self.addBoxButt = wx.Button(
                self, id=wx.ID_ANY, size=ADD_RM_BUTTON_SIZE, label="+"
            )
            self.boxButtonSizer.Add(self.addBoxButt, 0)
            self.addBoxButt.Bind(wx.EVT_BUTTON, self.duplicateBox)

        if rmMulti:
            self.rmBoxButt = wx.Button(
                self, id=wx.ID_ANY, size=ADD_RM_BUTTON_SIZE, label="-"
            )
            self.boxButtonSizer.Add(self.rmBoxButt, 0)
            self.rmBoxButt.Bind(wx.EVT_BUTTON, self.removeBox)

    def addDuplicatedItem(self, item):
        self.stBoxSizer.Add(
            item,
            proportion=1,
            flag=wx.EXPAND | wx.BOTTOM,
            border=5,
        )
        self.GetParent().Layout()

    def getCtrlID(self):
        return self.GetId()

    def removeBox(self, evt):
        for item in self.mdItems:
            item.mdDescription.removeMdItem(item)
        self.GetParent().removeBox(self)

    def removeMdItem(self, mdItem, items):
        """
        @param mdItem: object editor::MdItem
        @param items: widgets to destroy
        """
        mdItem.mdDescription.removeMdItem(mdItem)
        for item in items:
            try:
                item.Destroy()
            except:
                pass
        self.stBoxSizer.Remove(mdItem)
        self.GetParent().Layout()

    def duplicateBox(self, evt):
        duplicator = MdWxDuplicator(self.mdItems, self.GetParent(), self.label)
        clonedBox = duplicator.mdBox
        self.GetParent().addDuplicatedItem(clonedBox, self.GetId())


# ===============================================================================
# Handling keywords from database
# ===============================================================================
class MdBoxKeywords(MdBox):
    def __init__(self, parent, parent2, label):
        super(MdBoxKeywords, self).__init__(parent, label)
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.panelSizer)
        self.boxButtonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.parent2 = parent2

        self.panelSizer.Add(self.boxButtonSizer, flag=wx.EXPAND, proportion=1)
        self.parent = parent
        self.stBoxSizer = wx.StaticBoxSizer(self.stbox, orient=wx.VERTICAL)
        self.boxButtonSizer.Add(self.stBoxSizer, flag=wx.EXPAND, proportion=1)
        self.itemHolder = []
        self.textTMP = None

    def addKeywordItem(self, item):
        self.stBoxSizer.Add(
            item,
            proportion=1,
            border=5,
            flag=wx.EXPAND | wx.BOTTOM,
        )

    def removeKeywordItem(self, item):
        self.parent2.removeKeyfromBox(item, self.textTMP)
        self.stBoxSizer.Remove(item)
        self.parent.Fit()


# ===============================================================================
# DUPLICATOR OF WIDGETS-mditem
# ===============================================================================


class MdWxDuplicator:

    """duplicator of MdBox and MdItem object"""

    def __init__(self, mdItems, parent, boxlabel=None, mdItemOld=None, template=None):
        """
        @param mdItems:  list of editor::MdItem
        @param parent: parent of new duplicated box
        @param boxlabel: label of static box
        @param mdItemOld: object which will be duplicated
        @param template: in case if 'template mode' is on in editor
        """
        # duplicate box of items
        if boxlabel:
            itemList = list()
            self.mdBox = MdBox(parent, boxlabel)
            for i in mdItems:
                try:  # check if item has multiple button
                    i.addItemButt.GetLabel()
                    multi = True
                except:
                    multi = False
                try:  # check if chckBoxEdit exists
                    i.chckBoxEdit.GetValue()
                    template = True
                except:
                    template = False

                i = i.mdDescription  # var mdDescription is  jinjainfo::MdDescription
                mdItem1 = MdItem(
                    parent=self.mdBox,
                    item=i,
                    multiplicity=multi,
                    isFirstNum=1,
                    chckBox=template,
                )

                itemList.append(mdItem1)

                i.addMdItem(mdItem1)  # add item with using jinjainfo::MDescription
            self.mdBox.addItems(itemList, False, True)  # fill box

        else:  # duplicate only MdItem
            self.mdItem = MdItem(
                parent=parent,
                item=mdItems,
                multiplicity=False,
                rmMulti=True,
                isFirstNum=-1,
                chckBox=template,
            )

            try:
                if mdItems.inbox is not None:
                    mdItems.addMdItem(self.mdItem, mdItemOld)
                else:
                    mdItems.addMdItem(self.mdItem)
            except:
                mdItems.addMdItem(self.mdItem)


# =========================================================================
# METADATA ITEM (label+ctrlText+button(optional)+chckbox(template)
# =========================================================================
class MdItem(wx.BoxSizer):

    """main building blocks of generated GUI of editor"""

    def __init__(
        self,
        parent,
        item,
        multiplicity=None,
        rmMulti=False,
        isFirstNum=-1,
        chckBox=False,
    ):
        """
        @param item: jinjainfo::MdDescription(initialized by parsing information from jinja template)
        @param multiplicity: if true- widget has button for duplicate self
        @param rmMulti: if true- widget has button for remove self
        @param isFirstNum: handling with 'add' and 'remove' button of box.
                            this param is necessary for generating editor in editor::MdEditor.generateGUI.inBlock()
                            note: just first generated box has 'add' button (because being mandatory) and next others has
                            'remove' button
        @param chckBox: in case-True  'template editor' is on and widget has checkbox
        """
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.isValid = False
        self.isChecked = False
        self.mdDescription = item
        self.chckBox = chckBox
        self.multiple = multiplicity
        self.parent = parent
        added = False
        if multiplicity is None:
            self.multiple = item.multiplicity

        if isFirstNum != 1:
            self.multiple = False

        if isFirstNum != 1 and item.multiplicity:
            rmMulti = True
        self.tagText = wx.StaticText(parent=parent, id=wx.ID_ANY, label=item.name)
        if self.mdDescription.databaseAttr == "language":
            self.fillComboDB("language")
            added = True
        elif self.mdDescription.databaseAttr == "topicCategory":
            self.fillComboDB("topicCategory")
            added = True
        elif self.mdDescription.databaseAttr == "degree":
            self.fillComboDB("degree")
            added = True
        elif self.mdDescription.databaseAttr == "dateType":
            self.fillComboDB("dateType")
            added = True
        elif self.mdDescription.databaseAttr == "role":
            self.fillComboDB("role")
            added = True

        if self.chckBox is False and not added:
            if item.multiline is True:
                self.valueCtrl = wx.TextCtrl(
                    parent,
                    id=wx.ID_ANY,
                    size=(0, 70),
                    validator=self.validators(item.type),
                    style=wx.VSCROLL
                    | wx.TE_MULTILINE
                    | wx.TE_WORDWRAP
                    | wx.TAB_TRAVERSAL
                    | wx.RAISED_BORDER,
                )
            else:
                self.valueCtrl = wx.TextCtrl(
                    parent,
                    id=wx.ID_ANY,
                    validator=self.validators(item.type),
                    style=wx.VSCROLL
                    | wx.TE_DONTWRAP
                    | wx.TAB_TRAVERSAL
                    | wx.RAISED_BORDER
                    | wx.HSCROLL,
                )
        elif self.chckBox is True and not added:
            if item.multiline is True:
                self.valueCtrl = wx.TextCtrl(
                    parent,
                    id=wx.ID_ANY,
                    size=(0, 70),
                    style=wx.VSCROLL
                    | wx.TE_MULTILINE
                    | wx.TE_WORDWRAP
                    | wx.TAB_TRAVERSAL
                    | wx.RAISED_BORDER,
                )
            else:
                self.valueCtrl = wx.TextCtrl(
                    parent,
                    id=wx.ID_ANY,
                    style=wx.VSCROLL
                    | wx.TE_DONTWRAP
                    | wx.TAB_TRAVERSAL
                    | wx.RAISED_BORDER
                    | wx.HSCROLL,
                )

        self.valueCtrl.Bind(wx.EVT_MOTION, self.onMove)
        self.valueCtrl.SetExtraStyle(wx.WS_EX_VALIDATE_RECURSIVELY)

        if self.multiple:
            self.addItemButt = wx.Button(parent, -1, size=ADD_RM_BUTTON_SIZE, label="+")
            self.addItemButt.Bind(wx.EVT_BUTTON, self.duplicateItem)

        if rmMulti:
            self.rmItemButt = wx.Button(parent, -1, size=ADD_RM_BUTTON_SIZE, label="-")
            self.rmItemButt.Bind(wx.EVT_BUTTON, self.removeItem)

        if self.chckBox:
            self.chckBoxEdit = wx.CheckBox(parent, -1, size=(30, 30))
            self.chckBoxEdit.Bind(wx.EVT_CHECKBOX, self.onChangeChckBox)
            self.chckBoxEdit.SetValue(False)
            self.isChecked = False
            self.valueCtrl.Disable()

        self.createInfo()
        self.tip = wx.ToolTip(self.infoTip)

        self._addItemLay(item.multiline, rmMulti)

    def fillComboDB(self, label):
        if label == "language":
            lang = [
                "Afrikaans",
                "Albanian",
                "Arabic",
                "Armenian",
                "Basque",
                "Bengali",
                "Bulgarian",
                "Catalan",
                "Cambodian",
                "Chinese",
                "Croatian",
                "Czech",
                "Danish",
                "Dutch",
                "English",
                "Estonian",
                "Fiji",
                "Finnish",
                "French",
                "Georgian",
                "German",
                "Greek",
                "Gujarati",
                "Hebrew",
                "Hindi",
                "Hungarian",
                "Icelandic",
                "Indonesian",
                "Irish",
                "Italian",
                "Japanese",
                "Javanese",
                "Korean",
                "Latin",
                "Latvian",
                "Lithuanian",
                "Macedonian",
                "Malay",
                "Malayalam",
                "Maltese",
                "Maori",
                "Marathi",
                "Mongolian",
                "Nepali",
                "Norwegian",
                "Persian",
                "Polish",
                "Portuguese",
                "Punjabi",
                "Quechua",
                "Romanian",
                "Russian",
                "Samoan",
                "Serbian",
                "Slovak",
                "Slovenian",
                "Spanish",
                "Swahili",
                "Swedish",
                "Tamil",
                "Tatar",
                "Telugu",
                "Thai",
                "Tibetan",
                "Tonga",
                "Turkish",
                "Ukrainian",
                "Urdu",
                "Uzbek",
                "Vietnamese",
                "Welsh",
                "Xhosa",
            ]
            self.valueCtrl = wx.ComboBox(
                self.parent,
                id=wx.ID_ANY,
            )
            for lng in lang:
                self.valueCtrl.Append(lng)
        if label == "topicCategory":
            lang = [
                "farming",
                "biota",
                "boundaries",
                "climatologyMeteorologyAtmosphere",
                "economy",
                "elevation",
                "enviroment",
                "geoscientificInformation",
                "health",
                "imageryBaseMapsEarthCover",
                "intelligenceMilitary",
                "inlandWaters",
                "location",
                "planningCadastre",
                "society",
                "structure",
                "transportation",
                "utilitiesCommunication",
            ]
            self.valueCtrl = wx.ComboBox(
                self.parent,
                id=wx.ID_ANY,
            )
            for lng in lang:
                self.valueCtrl.Append(lng)
        if label == "degree":
            lang = ["Not evaluated", "Not conformant", "Conformant"]
            self.valueCtrl = wx.ComboBox(
                self.parent,
                id=wx.ID_ANY,
            )
            for lng in lang:
                self.valueCtrl.Append(lng)
        if label == "dateType":
            lang = ["Date of creation", "Date of last revision", "Date of publication"]
            self.valueCtrl = wx.ComboBox(
                self.parent,
                id=wx.ID_ANY,
            )
            for lng in lang:
                self.valueCtrl.Append(lng)
        if label == "role":
            lang = [
                "Author",
                "Custodian",
                "Distributor",
                "Originator",
                "Owner",
                "Point of contact",
                "Principal Investigation",
                "Processor",
                "Publisher",
                "Resource provider",
                "User",
            ]
            self.valueCtrl = wx.ComboBox(
                self.parent,
                id=wx.ID_ANY,
            )
            for lng in lang:
                self.valueCtrl.Append(lng)

    def validators(self, validationStyle):

        if validationStyle == "email":
            return EmailValidator()

        if validationStyle == "integer":
            return NTCValidator("DIGIT_ONLY")

        if validationStyle == "decimal":
            return NTCValidator("DIGIT_ONLY")

        if validationStyle == "date":
            return TimeISOValidator()

        # return EmptyValidator()
        return SimpleValidator("")

    def onChangeChckBox(self, evt):
        """current implementation of editor mode for defining templates not allowed to check
        only single items in static box. There are two cases:  all items in box are checked or not.
        """
        if self.mdDescription.inbox:  # MdItems are in box
            try:
                items = self.valueCtrl.GetParent().mdItems
                if self.isChecked:
                    self.valueCtrl.Disable()
                    self.isChecked = False
                else:
                    self.valueCtrl.Enable()
                    self.isChecked = True

                for item in items:
                    if self.isChecked:
                        item.valueCtrl.Enable()
                        item.chckBoxEdit.SetValue(True)
                        item.isChecked = True
                    else:
                        item.valueCtrl.Disable()
                        item.chckBoxEdit.SetValue(False)
                        item.isChecked = False
            except:
                pass
        else:
            if self.isChecked:
                self.valueCtrl.Disable()
                self.isChecked = False
            else:
                self.valueCtrl.Enable()
                self.isChecked = True

    def onMove(self, evt=None):
        self.valueCtrl.SetToolTip(self.tip)

    def createInfo(self):
        """Feed for tooltip"""
        string = ""
        if self.mdDescription.ref is not None:
            string += self.mdDescription.ref + "\n\n"
        if self.mdDescription.name is not None:
            string += "NAME: \n" + self.mdDescription.name + "\n\n"
        if self.mdDescription.desc is not None:
            string += "DESCRIPTION: \n" + self.mdDescription.desc + "\n\n"
        if self.mdDescription.example is not None:
            string += "EXAMPLE: \n" + self.mdDescription.example + "\n\n"
        if self.mdDescription.type is not None:
            string += "DATA TYPE: \n" + self.mdDescription.type + "\n\n"
        string += "*" + "\n"
        if self.mdDescription.statements is not None:
            string += "Jinja template info: \n" + self.mdDescription.statements + "\n"

        if self.mdDescription.statements1 is not None:
            string += self.mdDescription.statements1 + "\n"
        string += "OWSLib info:\n" + self.mdDescription.tag
        self.infoTip = string

    def removeItem(self, evt):
        """adding all items in self(mdItem) to list and call parent remover"""
        ilist = [self.valueCtrl, self.tagText]
        try:
            ilist.append(self.rmItemButt)
        except:
            pass
        try:
            ilist.append(self.chckBoxEdit)
        except:
            pass
        self.valueCtrl.GetParent().removeMdItem(self, ilist)

    def duplicateItem(self, evt):
        """add Md item to parent(box or notebook page)"""
        parent = self.valueCtrl.GetParent()
        # if parent is box
        if self.mdDescription.inbox:
            duplicator = MdWxDuplicator(
                mdItems=self.mdDescription,
                parent=parent,
                mdItemOld=self,
                template=self.chckBox,
            )
        else:
            duplicator = MdWxDuplicator(
                mdItems=self.mdDescription, parent=parent, template=self.chckBox
            )

        clonedMdItem = duplicator.mdItem
        # call parent "add" function
        self.valueCtrl.GetParent().addDuplicatedItem(clonedMdItem)

    def setValue(self, value):
        """Set value & color of widgets
        in case if is template creator 'on':
            yellow: in case if value is marked by $NULL(by mdgrass::GrassMD)
            red:    if value is '' or object is not initialized. e.g. if user
                    read non fully valid INSPIRE xml with INSPIRE jinja template,
                    the GUI generating mechanism will create GUI according to template
                    and all missing tags(xml)-gui(TextCtrls) will be marked by red
        """
        if value is None or value == "":
            if self.chckBox:
                self.chckBoxEdit.SetValue(True)
                self.isChecked = True
                try:
                    self.onChangeChckBox(None)
                    self.onChangeChckBox(None)
                except:
                    pass
                self.valueCtrl.SetBackgroundColour((245, 204, 230))  # red

            self.valueCtrl.SetValue("")
            self.valueCtrl.Enable()

        elif self.chckBox and value == "$NULL":
            self.valueCtrl.SetBackgroundColour((255, 255, 82))  # yellow
            self.valueCtrl.SetValue("")

            if self.chckBox:
                self.chckBoxEdit.SetValue(True)
                self.isChecked = True
                self.valueCtrl.Enable()
                try:
                    self.onChangeChckBox(None)
                    self.onChangeChckBox(None)
                except:
                    pass

        elif value == "$NULL":
            self.valueCtrl.SetValue("")

        else:
            self.isValid = True
            self.valueCtrl.SetValue(value)

    def getValue(self):

        value = mdutil.replaceXMLReservedChar(self.valueCtrl.GetValue())
        value = value.replace("\n", "")
        value = value.replace('"', "")
        value = value.replace("'", "")
        return value

    def getCtrlID(self):
        return self.valueCtrl.GetId()

    def _addItemLay(self, multiline, rmMulti):
        self.textFieldSizer = wx.BoxSizer(wx.HORIZONTAL)
        if multiline is True:
            self.textFieldSizer.Add(self.valueCtrl, proportion=1, flag=wx.EXPAND)
        else:
            self.textFieldSizer.Add(self.valueCtrl, proportion=1)

        if self.multiple:
            self.textFieldSizer.Add(self.addItemButt, 0)

        if rmMulti:
            self.textFieldSizer.Add(self.rmItemButt, 0)

        if self.chckBox:
            self.textFieldSizer.Add(self.chckBoxEdit, 0)

        self.Add(self.tagText, proportion=0)
        self.Add(self.textFieldSizer, proportion=0, flag=wx.EXPAND)


class MdItemKeyword(wx.BoxSizer):
    def __init__(self, parent, text, keyword, title, keywordObj):
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.isValid = False
        self.isChecked = False
        self.keywordObj = keywordObj
        self.text = wx.StaticText(parent=parent, id=wx.ID_ANY, label=text)
        self.parent = parent
        self.rmItemButt = wx.Button(parent, -1, size=ADD_RM_BUTTON_SIZE, label="-")
        self.rmItemButt.Bind(wx.EVT_BUTTON, self.removeItem)
        self.keyword = keyword
        self.title = title
        # self.createInfo()
        # self.tip = wx.ToolTip(self.infoTip)
        self.layout()

    def getVal(self):
        return self.text.GetLabel()

    def getKyewordObj(self):
        self.keywordObj["keywords"] = self.keyword
        self.keywordObj["title"] = self.title
        return self.keywordObj

    def removeItem(self, evt):
        self.parent.textTMP = self.text.GetLabel()
        self.textFieldSizer.Clear()
        # self.textFieldSizer.Destroy()

        self.rmItemButt.Destroy()
        self.text.Destroy()
        self.parent.removeKeywordItem(self)

    def layout(self):
        self.textFieldSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.textFieldSizer.Add(
            self.rmItemButt,
            0,
            flag=wx.RIGHT,
            border=5,
        )
        self.textFieldSizer.Add(
            self.text,
            0,
            flag=wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
        )
        self.Add(self.textFieldSizer, proportion=0, flag=wx.EXPAND)


# =========================================================================
# =========================================================================
# ADD NOTEBOOK PAGE
# =========================================================================


class MdNotebookPage(scrolled.ScrolledPanel):

    """
    every notebook page is initialized by jinjainfo::MdDescription.group (label)
    """

    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent=parent, id=wx.ID_ANY)
        self.items = []
        self._addNotebookPageLay()
        self.sizerIndexDict = {}
        self.sizerIndex = 0

    def _addNotebookPageLay(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)

    def _getIndex(self):
        """
        index for handling position of editor::MdBox,MdItem in editor::MdNotebookPage(self).
        Primary for correct duplicating Boxes or items on notebook page
        """
        self.sizerIndex += 1
        return self.sizerIndex

    def addKeywordObj(self, item):
        self.mainSizer.Add(item, proportion=0, flag=wx.EXPAND)

    def addItem(self, item):
        """
        @param item: can be editor::MdBox or editor::MDItem
        """
        if isinstance(item, list):
            for i in item:
                if isinstance(i, list):
                    for ii in i:
                        self.sizerIndexDict[ii.getCtrlID()] = self._getIndex()
                        self.mainSizer.Add(ii, proportion=0, flag=wx.EXPAND)
                else:
                    self.sizerIndexDict[i.getCtrlID()] = self._getIndex()
                    self.mainSizer.Add(i, proportion=0, flag=wx.EXPAND)
        else:
            self.sizerIndexDict[item.getCtrlID()] = self._getIndex()
            self.mainSizer.Add(item, proportion=0, flag=wx.EXPAND)

    def addDuplicatedItem(self, item, mId):
        """adding duplicated object to sizer to position after parent"""
        self.items.append(item)
        posIndex = self.sizerIndexDict[mId]
        self.mainSizer.Insert(posIndex, item, proportion=0, flag=wx.EXPAND)
        self.GetParent().Refresh()
        self.Layout()
        self.SetupScrolling()

    def removeBox(self, box):
        box.Destroy()
        self.SetSizerAndFit(self.mainSizer)

    def removeMdItem(self, mdDes, items):
        """Remove children
        @param mdDes: editor::MdItem.mdDescription
        @param items: all widgets to remove of MdItem
        """
        mdDes.mdDescription.removeMdItem(
            mdDes
        )  # remove from jinjainfi:MdDEscription object
        for item in items:
            item.Destroy()
        self.SetSizerAndFit(self.mainSizer)


# class MdItemKyewords
class MdKeywords(wx.BoxSizer):
    def __init__(self, parent, mdObject, mdOWS):
        wx.BoxSizer.__init__(self, wx.VERTICAL)

        try:
            global GMessage

            from core.gcmd import GMessage
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.itemHolder = set()
        self.parent = parent
        self.keywordsOWSObject = mdOWS

        self.comboKeysLabel = wx.StaticText(
            parent=self.parent, id=wx.ID_ANY, label="Keywords from repositories"
        )
        self.comboKeys = wx.ComboBox(parent=self.parent, id=wx.ID_ANY)

        self.keysList = wx.TreeCtrl(
            parent=self.parent,
            id=wx.ID_ANY,
            size=(0, 120),
            style=wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_DEFAULT_STYLE,
        )
        self.box = MdBoxKeywords(parent=parent, parent2=self, label="Keywords")
        self.memKeys = set()
        self.comboKeys.Bind(wx.EVT_COMBOBOX, self.onSetVocabulary)
        self.keysList.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.addItemsToBox)
        self.layout()
        Module("db.connect", flags="d")
        self._table_name = "metadata_themes"
        self.fillDb()
        self.fillKeywordsList()

    def removeKeyfromBox(self, item, text):
        self.memKeys.remove(text)
        self.itemHolder.remove(item)

    def addItemsToBox(self, evt):
        item = evt.GetItem()
        if item == self.keysList.GetRootItem():
            return

        keyword = self.keysList.GetItemText(item)
        currKeyword = self.titles[self.comboKeys.GetValue()]
        out = (
            self.comboKeys.GetValue()
            + ", "
            + keyword
            + ", "
            + currKeyword["type"]
            + ", "
            + currKeyword["date"]
        )
        if keyword in self.memKeys:
            return
        self.memKeys.add(out)

        kItem = MdItemKeyword(
            self.box, out, keyword, self.comboKeys.GetValue(), currKeyword
        )
        self.itemHolder.add(kItem)
        self.box.addKeywordItem(kItem)
        self.box.Fit()
        self.parent.Fit()

    def dbSelect(self, sql):
        res = Module("db.select", sql=sql, flags="c", stdout_=PIPE)
        return res.outputs.stdout

    def dbExecute(self, sql):
        Module("db.execute", sql=sql)

    def GetKws(self):
        return self.itemHolder  # dict is in var keywordObj

    def fillDb(self):
        if not mdutil.isTableExists(self._table_name):
            sql = (
                "create table if not exists {table} "
                "(title TEXT, keyword TEXT, date_iso TEXT, "
                "date_type TEXT)".format(
                    table=self._table_name,
                )
            )
            self.dbExecute(sql)

            titles = [
                ["keywordConcepts.xml", "GEMET - Concepts, version 2.4"],
                ["keywordThemes.xml", "GEMET - Themes, version 2.4"],
                ["keywordGroups.xml", "GEMET - Groups, version 2.4"],
            ]

            context = mdutil.StaticContext()
            libPath = os.path.join(context.lib_path, "config")

            for title in titles:
                path = os.path.join(libPath, title[0])
                root = etree.parse(path).getroot()

                values = ""
                for item in root:
                    values += (
                        "('{title}', '{keyword}', '{date_iso}', "
                        "'{date_type}'), ".format(
                            title=title[1],
                            keyword=item[0][0].text,
                            date_iso="2010-01-13",
                            date_type="publication",
                        )
                    )

                sql = (
                    "INSERT INTO '{table}' "
                    "('title', 'keyword', 'date_iso', "
                    "'date_type') VALUES {values};".format(
                        table=self._table_name,
                        values=values[:-2],
                    )
                )
                self.dbExecute(sql)

    def fillKeywordsList(self):
        sql = "SELECT title ,keyword, date_iso, date_type FROM {}".format(
            self._table_name,
        )

        # TODO check if database exist
        self.keysDict = None
        metaRepository = self.dbSelect(sql)
        self.titles = {}
        theme = ""
        titleTmp = None
        lines = metaRepository.splitlines()
        # lines.pop()
        for line in lines:
            line = line.split("|")
            if theme != line[0]:  # if new theme found
                if titleTmp is not None:  # first loop
                    self.titles[titleTmp] = self.keysDict
                theme = line[0]
                self.keysDict = {}
                self.keysDict["date"] = line[2]
                self.keysDict["type"] = line[3]
                self.keysDict["keywords"] = [1]
            self.keysDict["keywords"].append(str(line[1]))
            titleTmp = line[0]

        if self.keysDict is None:
            GMessage("Predefined values of metadata are missing in database")
            return
        self.titles[titleTmp] = self.keysDict

        for key in list(self.titles.keys()):
            self.comboKeys.Append(key)

    def onSetVocabulary(self, evt):
        self.keysList.DeleteAllItems()
        self.root = self.keysList.AddRoot("Keywords")
        title = self.comboKeys.GetValue()

        keywords = self.titles[title]["keywords"]
        keywords.pop(0)
        for keyword in keywords:
            self.keysList.AppendItem(parent=self.root, text=str(keyword))
        self.keysList.ExpandAll()

    def layout(self):
        self.Add(self.box, flag=wx.EXPAND)
        self.Add(self.comboKeysLabel, flag=wx.EXPAND)
        self.Add(self.comboKeys, flag=wx.EXPAND)
        self.Add(
            self.keysList,
            proportion=1,
            border=10,
            flag=wx.EXPAND | wx.TOP | wx.BOTTOM,
        )


# =========================================================================
# MAIN FRAME
# =========================================================================
class MdMainEditor(wx.Panel):

    """
    main functions : self.generateGUI(): generating GUI from: editor:MdItem,MdBox,MdNotebookPage
                     self.createNewMD(): filling OWSLib.iso.MD_Metadata by values from generated GUI
                     self.defineTemplate(): creator of predefined templates in template editor mode
    """

    def __init__(self, parent, profilePath, xmlMdPath, templateEditor=False):
        """
        @param profilePath: path to jinja template for generating GUI of editor
        @param xmlMdPath: path of xml for init Editor
        @param templateEditor: mode-creator of template
        """
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        try:
            global CI_Date, CI_OnlineResource, CI_ResponsibleParty, DQ_DataQuality, EX_Extent, EX_GeographicBoundingBox, GError, MD_Distribution, MD_ReferenceSystem

            from owslib.iso import (
                CI_Date,
                CI_OnlineResource,
                CI_ResponsibleParty,
                DQ_DataQuality,
                EX_Extent,
                EX_GeographicBoundingBox,
                MD_Distribution,
                MD_ReferenceSystem,
            )

            from core.gcmd import GError
        except ModuleNotFoundError as e:
            msg = e.msg
            sys.exit(
                globalvar.MODULE_NOT_FOUND.format(
                    lib=msg.split("'")[-2], url=globalvar.MODULE_URL
                )
            )

        self.mdo = MdFileWork()
        self.md = self.mdo.initMD(xmlMdPath)
        self.templateEditor = templateEditor
        self.profilePath = profilePath

        self.jinj = JinjaTemplateParser(self.profilePath)
        # list of object MdDescription
        self.mdDescription = self.jinj.mdDescription
        # string of tags from jinja template (loops and OWSLib objects)
        self.mdOWSTagStr = self.jinj.mdOWSTagStr
        self.mdOWSTagStrList = self.jinj.mdOWSTagStrList  #
        self.keywords = None
        self.nbPage = None
        self.generateGUI()
        self._layout()

    # ----------------------------------------------------------- GUI GENERATOR START
    def executeStr(self, stri, mdDescrObj):
        """note- exec cannot be in sub function
        for easy understanding to product of self.generateGUI()- print stri
        """
        # print stri
        exec(stri)

    def plusC(self, num=None):
        """iterator for handling jinja teplate items in self.generateGUI and self.createNewMD"""
        if num is None:
            num = 1
        self.c += num
        if self.c >= self.max:
            self.c -= 1  # ensure to 'list out of bounds'
            self.stop = True

    def minusC(self, num=None):
        """iterator for handling jinja template items in self.generateGUI and self.createNewMD"""
        if num is None:
            num = 1
        self.c -= num
        if self.c <= self.max:
            self.stop = False

    def generateGUI(self):
        """
        @var tagStringLst:  tagStringLst is self.mdOWSTagStr in list.
                            Item=line from jinja template(only lines with owslib objects and loops)
        @var mdDescrObj:    list of MdDescription() objects initialized\
                            by information from jinja t.
        @var self.c:        index of var: tagStringLst and var: self.mdDescription
        @var markgroup:     markers of created list in GUI notebook
        @var self.max:      length of tagStringLst and mdDescrObj
        @var self.stop:     index self.c is increasing  by function plusC(),\
                            that care about not exceeding the index
        HINT: print param stri in self.executeStr()
        """

        def prepareStatements():
            """in jinja template are defining some py-function specifically:
            e.g. |length=len
            also statements with pythonic 'zip' must be prepare specifically for generator of GUI
            """
            for c in range(self.max):
                if "|length" in str(tagStringLst[c]):
                    a = tagStringLst[c]
                    a = a.replace("|length", ")").replace("if ", "if len(self.")
                    tagStringLst[c] = a
                if "zip(" in tagStringLst[c]:
                    sta = tagStringLst[c]
                    tagStringLst[c] = sta.replace("md.", "self.md.")

        def chckIfJumpToLoop(sta):
            """if loaded xml not include tags(OWSLib object) from jinja template, this function will
                    generate sample of item(marked by red in GUI-template mode).
            @note: in case of sub statements e.g. metadata-keywords is need to check booth statements
            @param sta: statements of the loop
            for understanding print param for self.executeStr()
            """
            self.isValidS = False
            staTMP = sta
            if "\t" not in staTMP:
                tab = "\t"
                tab1 = ""
                staTMP = staTMP + ":\n" + tab + "self.isValidS=True"
            else:
                tab = "\t"
                tab1 = "\t"
                staTMP = staTMP.replace("\t", "") + ":\n" + tab + "self.isValidS=True"

            try:  # if loop for in for
                self.executeStr(staTMP, False)
            except:
                staTMP = (
                    self.staTMP.replace("self.isValidS=True", "")
                    + "\n\t"
                    + staTMP.replace("\t", "\t\t")
                )
                self.executeStr(staTMP, False)

            self.staTMP = staTMP
            if self.isValidS:
                return sta
            else:
                return tab1 + "for n in range(1)"

        def inBlock():
            """This part of code build string-code for executing. This can happend if is necassary to use statements
                to generate gui(OWSLib objects in list). The block of code is building from "statement" which is represended by OWSLib object.
                In case if OWSLib object is non initialized(metadata missing), function chckIfJumpToLoop() replace statements by "for n in range(1)".
            @var IFStatements: True= string is IF statements
            @var loop: current statements, mostly loop FOR
            @var str1: final string for execute
            @var box:  True if editor::MdItems is in editor::MdBox
            @var isValid: True in case if OWSLib object in statement is initialized. False= statements is 'for n in range(1)'
            """
            IFStatements = False
            statements = tagStringLst[self.c - 1]
            if "if" in statements.split():
                IFStatements = True
            loop = statements.replace(" md.", " self.md.")
            looptmp = chckIfJumpToLoop(loop)
            str2 = "numOfSameBox=0\n"
            str2 += looptmp

            str2 += ":\n"
            str2 += "\t" + "self.ItemList=list()\n"  # initialize list
            str2 += "\t" + "numOfSameBox+=1\n"

            box = False
            if self.mdDescription[self.c].inbox:
                box = True
                str2 += (
                    "\t"
                    + "box=MdBox(self.nbPage,mdDescrObj["
                    + str(self.c)
                    + "].inbox)\n"
                )  # add box

            str1 = str2
            while "\t" in tagStringLst[self.c] and self.stop is False:
                if (
                    "for" not in str(tagStringLst[self.c]).split()
                    and "if" not in str(tagStringLst[self.c]).split()
                ):

                    value = str(self.mdOWSTagStrList[self.c])
                    str1 += (
                        "\t"
                        + "self.mdDescription["
                        + str(self.c)
                        + "].addStatements('"
                        + loop
                        + "')\n"
                    )

                    if box:
                        str1 += (
                            "\t"
                            + "it=MdItem(parent=box,item=mdDescrObj["
                            + str(self.c)
                            + "],isFirstNum=numOfSameBox,chckBox=self.templateEditor)\n"
                        )
                    else:
                        str1 += (
                            "\t"
                            + "it=MdItem(parent=self.nbPage,item=mdDescrObj["
                            + str(self.c)
                            + "],isFirstNum=numOfSameBox,chckBox=self.templateEditor)\n"
                        )

                    if self.isValidS:  # if metadata are loaded to owslib
                        if IFStatements:
                            str1 += "\t" + "it.setValue(self." + str(value) + ")\n"
                        else:
                            str1 += "\t" + "it.setValue(" + str(value) + ")\n"
                    else:
                        if IFStatements:
                            str1 += "\t" + 'it.setValue("")\n'
                        else:
                            str1 += "\t" + 'it.setValue("")\n'

                    str1 += (
                        "\t" + "self.mdDescription[" + str(self.c) + "].addMdItem(it)\n"
                    )
                    str1 += "\t" + "self.ItemList.append(it)\n"
                    tab = "\t"
                    self.plusC()

                else:  # if statements in statements
                    statements = tagStringLst[self.c]
                    str2 = ""
                    keyword = False

                    if '["keywords"]' in statements:
                        keyword = True
                        str2 += "\t" + "self.keywordsList=[]\n"

                    str2 += "\t" + "numOfSameItem=0\n"
                    loop2 = statements.replace(" md.", " self.md.")
                    looptmp1 = chckIfJumpToLoop(loop2)
                    str2 += looptmp1 + ":\n"
                    self.plusC()
                    str1 += str2
                    while "\t\t" in tagStringLst[self.c] and self.stop is False:
                        value = str(self.mdOWSTagStrList[self.c])
                        # save information about loops
                        str1 += "\t\t" + "numOfSameItem+=1\n"
                        str1 += (
                            "\t\t"
                            + "self.mdDescription["
                            + str(self.c)
                            + "].addStatements('"
                            + loop
                            + "')\n"
                        )
                        str1 += (
                            "\t\t"
                            + "self.mdDescription["
                            + str(self.c)
                            + "].addStatements1('"
                            + loop2
                            + "')\n"
                        )

                        if box:
                            str1 += (
                                "\t\t"
                                + "it=MdItem(parent=box,item=mdDescrObj["
                                + str(self.c)
                                + "],isFirstNum=numOfSameItem,chckBox=self.templateEditor)\n"
                            )
                        else:
                            str1 += (
                                "\t\t"
                                + "it=MdItem(self.nbPage,mdDescrObj["
                                + str(self.c)
                                + "],isFirstNum=numOfSameItem,chckBox=self.templateEditor)\n"
                            )

                        if self.isValidS:
                            str1 += "\t\t" + "it.setValue(" + str(value) + ")\n"
                        else:
                            str1 += "\t\t" + 'it.setValue("")\n'

                        str1 += "\t\t" + "self.ItemList.append(it)\n"
                        if keyword:
                            str1 += "\t\t" + "self.keywordsList.append(it)\n"
                            str1 += (
                                "\t"
                                + "self.mdDescription["
                                + str(self.c)
                                + "].addMdItem(self.keywordsList)\n"
                            )
                        else:
                            str1 += (
                                "\t\t"
                                + "self.mdDescription["
                                + str(self.c)
                                + "].addMdItem(it)\n"
                            )

                        tab = "\t\t"
                        self.plusC()
            if box:
                str1 += (
                    tab
                    + "box.addItems(items=self.ItemList,multi=mdDescrObj[self.c].inboxmulti,isFirstNum=numOfSameBox)\n"
                )
                str1 += tab + "self.nbPage.addItem(box)\n"
            else:
                str1 += tab + "self.nbPage.addItem(self.ItemList)\n"

            self.executeStr(str1, mdDescrObj)

        # --------------------------------------------------------------------- INIT VARS
        self.notebook = wx.Notebook(self)
        markedgroup = []  # notebook panel marker
        tagStringLst = self.mdOWSTagStrList
        mdDescrObj = self.mdDescription  # from jinja
        self.c = 0
        self.stop = False
        self.max = len(mdDescrObj)
        prepareStatements()
        self.notebokDict = {}
        # --------------------------------------------- #START of the loop of generator
        while self.stop is False:  # self.stop is managed by def plusC(self):
            group = mdDescrObj[self.c].group

            if group not in markedgroup:  # if group is not created
                markedgroup.append(group)  # mark group
                self.nbPage = MdNotebookPage(self.notebook)
                self.notebook.AddPage(self.nbPage, mdDescrObj[self.c].group)
                if mdDescrObj[self.c].group == "Keywords":
                    self.keywords = MdKeywords(
                        parent=self.nbPage,
                        mdObject=mdDescrObj[self.c],
                        mdOWS=self.md.identification.keywords,
                    )
                    self.nbPage.addKeywordObj(self.keywords)
                self.notebokDict[mdDescrObj[self.c].group] = self.nbPage
            else:
                self.nbPage = self.notebokDict[mdDescrObj[self.c].group]

            # if  statements started
            if "\t" in tagStringLst[self.c] and self.stop is False:
                inBlock()
            # if is just single item without statements
            elif (
                "for" not in str(tagStringLst[self.c]).split()
                and "if" not in str(tagStringLst[self.c]).split()
            ):
                it = MdItem(
                    parent=self.nbPage,
                    item=mdDescrObj[self.c],
                    chckBox=self.templateEditor,
                )
                value = "self." + str(self.mdOWSTagStrList[self.c]).replace("\n", "")
                value = eval(value)
                if value is None:
                    value = ""

                it.setValue(value)
                self.mdDescription[self.c].addMdItem(it)
                self.nbPage.addItem(it)
                self.plusC()
            else:
                self.plusC()
        if self.templateEditor:
            self.refreshChkboxes()

    def refreshChkboxes(self):
        """In case if template editor is on, after generating GUI it is
        obligatory to refresh checkboxes
        """
        for item in self.mdDescription:
            for i in item.mdItem:
                try:
                    i.onChangeChckBox(None)
                    i.onChangeChckBox(None)
                except:
                    pass

    # ----------------------------------------------------------- GUI GENERATOR END

    def defineTemplate(self):
        """Main function for generating jinja template in mode "template editor"
        Every widget MdItem is represented by 'jinja tag'. Not checked widget= tag in jinja template will be replaced by
        list of string with string of replaced tag. In rendering template this produces holding(non removing) jinja-tag from template.
        In case if widget is checked= rendering will replace OWSLib object by filled values( like in normal editing mode)
        @var finalTemplate:    string included final jinja template
        """
        try:
            template = open(self.profilePath, "r")
        except Exception as e:
            GError("Error loading template:\n" + str(e))

        owsTagList = list()
        indexowsTagList = 0
        finalTemplate = ""
        chcked = False
        forSTS = False
        ifSTS = False

        for line in template.readlines():
            if "{% for" in line:
                forSTS = True

            if "{% if" in line:
                ifSTS = True

            for r, item in enumerate(self.mdDescription):
                str1 = item.selfInfoString
                if str1 in line:  # owslib definition in line
                    try:
                        if not item.mdItem[0].isChecked:
                            chcked = False
                    except:
                        try:
                            if self.mdDescription[r + 1].mdItem[0].isChecked is False:
                                chcked = False
                        except:
                            try:
                                if (
                                    self.mdDescription[r + 2].mdItem[0].isChecked
                                    is False
                                ):
                                    chcked = False
                            except:
                                try:
                                    if (
                                        self.mdDescription[r + 3].mdItem[0].isChecked
                                        is False
                                    ):
                                        chcked = False
                                except:
                                    pass
                    if not chcked:  # chckbox in gui

                        if forSTS:
                            forSTS = False

                        if ifSTS:
                            ifSTS = False

                        owsTagList.append(str1)
                        templateStr = "{{ owsTagList[" + str(indexowsTagList) + "] }}"
                        indexowsTagList += 1

                        line = line.replace(str1, templateStr)
                        tag = "{{ " + item.tag + " }}"
                        line = line.replace(tag, templateStr)

                        finalTemplate += line
                        continue

            if chcked:
                if "{% endfor -%}" in line and forSTS == 0:
                    str1 = "{% endfor -%}"
                    owsTagList.append(str1)
                    templateStr = "{{ owsTagList[" + str(indexowsTagList) + "] }}"
                    indexowsTagList += 1

                    line = line.replace(str1, templateStr)
                    tag = "{{" + item.tag + "}}"
                    line = line.replace(tag, templateStr)
                    finalTemplate += line

                elif "{% endif -%}" in line and ifSTS == 0:
                    str1 = "{% endif -%}"
                    owsTagList.append(str1)
                    templateStr = "{{ owsTagList[" + str(indexowsTagList) + "] }}"
                    indexowsTagList += 1

                    line = line.replace(str1, templateStr)
                    tag = "{{" + item.tag + "}}"
                    line = line.replace(tag, templateStr)
                    finalTemplate += line

                else:
                    finalTemplate += line
            chcked = True

        head, tail = os.path.split(self.profilePath)
        tail = "EXPT" + tail
        self.profilePath = os.path.join(head, tail)
        templateOut = open(self.profilePath, "w")
        templateOut.write(finalTemplate)
        templateOut.close()

        return owsTagList

    # ----------------------------------------- FILL OWSLib BY EDITED METADATA IN GUI

    def executeStr1(self, stri, item):
        """note- exec cannot be in sub function
        for easier understanding to product of self.createNewMD()- print stri
        """
        # print stri
        exec(stri)

    def getKeywordsFromRepositoryWidget(self, md):
        if self.keywords is not None:
            for item in self.keywords.GetKws():
                titles = item.getKyewordObj()

                kw = {}
                kw["keywords"] = []
                kw["keywords"].append(titles["keywords"])
                kw["type"] = None
                kw["thesaurus"] = {}
                kw["thesaurus"]["title"] = titles["title"]
                kw["thesaurus"]["date"] = titles["date"]
                kw["thesaurus"]["datetype"] = titles["type"]
                md.identification.keywords.append(kw)
        return md

    def saveMDfromGUI(self, evt=None):
        """Main function for exporting metadata from filled widgets.
        Initializing owslib object by metadata from gui(export of metadata)
        """

        def prepareStatements():
            """replacing some specific declaration of python function in jinja template"""
            for c in range(self.max):
                if "|length" in str(mdDes[c].tag):
                    a = mdDes[c].tag
                    a = a.replace("|length", ")").replace("if ", "if len(self.")
                    mdDes[c].tag = a
                if "|length" in str(mdDes[c].statements):
                    a = mdDes[c].statements
                    a = a.replace("|length", ")").replace("if ", "if len(self.")
                    mdDes[c].statements = a
                if "|length" in str(mdDes[c].statements1):
                    a = mdDes[c].statements1
                    a = a.replace("|length", ")").replace("if ", "if len(self.")
                    mdDes[c].statements1 = a

        def chckIf1Statements():
            """Return true if next item in jinjainfo::MdDescription is statement"""
            try:
                if mdDes[self.c + 1].statement:
                    return True
                else:
                    return False
            except:
                return False

        def chckIf2xStatements():
            """Return true if next two items in jinjainfo::MdDescription are representing statements"""
            if "if" in mdDes[self.c].tag.split() or "for" in mdDes[self.c].tag.split():
                try:
                    if (
                        "if" in mdDes[self.c + 1].tag.split()
                        or "for" in mdDes[self.c + 1].tag.split()
                    ):
                        return True
                    else:
                        return False
                except:
                    return False

        def noneStatements():
            """Without condition or loop"""
            str1 = ""
            for wxCtrl in mdDes[self.c].mdItem:
                if wxCtrl.getValue() is not None:
                    str1 += (
                        "self."
                        + mdDes[self.c].tag
                        + '="'
                        + str(wxCtrl.getValue())
                        + '"\n'
                    )
                    self.executeStr1(str1, mdDes[self.c])
                    str1 = ""
            self.plusC()

        def inStatements():
            """possible combinations of statements
            (1)    IF
                        item
                ----------------------------------------------------
            (2)    for
            (2.1)          item (with init OWSLib object)
                       "or"
            (2.2)          item (without init)
                           item with ZIP
            """
            cTmp = self.c
            tag = str(mdDes[cTmp].tag).split()

            tag1 = "self." + str(tag[-1])
            tag = "self." + str(tag[-1]) + ".append(self.val)\n"

            self.plusC()
            # statements of current item
            stat = mdDes[self.c].statements
            str1 = ""
            leng = len(mdDes[self.c].mdItem)

            # (2.1) IF NECESSARY TO INITIALIZE OWSLIB OBJECT
            if mdDes[cTmp].object and "if" not in mdDes[cTmp].tag.split():
                objStr = "self.val=" + mdDes[cTmp].object + "\n"

                for n in range(leng):
                    numOfItems = 0
                    str1 += objStr
                    while mdDes[self.c].statements == stat and self.stop is False:
                        metadata = re.split(r"[.]", mdDes[self.c].tag)
                        metadata[0] = "self.val."
                        str1 += (
                            "".join(metadata)
                            + "='"
                            + str(mdDes[self.c].mdItem[n].getValue())
                            + "'\n"
                        )
                        self.plusC()
                        numOfItems += 1

                    str1 += tag
                    self.executeStr1(str1, False)
                    str1 = ""
                    self.minusC(numOfItems)

                self.plusC(numOfItems)
            # (2.2) no init and py ZIP'
            elif (
                "for" in mdDes[cTmp].tag.split()
                and mdDes[cTmp].object is None
                and " zip(" in mdDes[cTmp].tag
            ):
                leng = len(mdDes[self.c].mdItem)
                tag1 = mdutil.findBetween(mdDes[cTmp].tag, "zip(", ")").split(",")

                for n in range(leng):
                    numOfItems = 0
                    while mdDes[self.c].statements == stat and self.stop is False:
                        str1 += (
                            "self."
                            + tag1[numOfItems]
                            + ".append('"
                            + mdDes[self.c].mdItem[n].getValue()
                            + "')\n"
                        )
                        self.plusC()
                        numOfItems += 1

                    self.executeStr1(str1, False)
                    str1 = ""
                    self.minusC(numOfItems)

                self.plusC(numOfItems)
            # 'no init FOR'
            elif "for" in mdDes[cTmp].tag.split() and mdDes[cTmp].object is None:
                leng = len(mdDes[self.c].mdItem)
                numOfItems = 0
                for n in range(leng):
                    numOfItems = 0
                    while mdDes[self.c].statements == stat and self.stop is False:
                        str1 += (
                            tag1
                            + ".append('"
                            + mdDes[self.c].mdItem[n].getValue()
                            + "')\n"
                        )
                        self.plusC()
                        numOfItems += 1

                    self.executeStr1(str1, False)
                    str1 = ""
                    self.minusC(numOfItems)

                self.plusC(numOfItems)
            # (1) 'no init IF'
            elif "if" in mdDes[cTmp].tag.split():

                objStr = mdDes[cTmp].tag.replace(" md.", " self.md.") + ":\n"

                for n in range(leng):
                    numOfItems = 0
                    while mdDes[self.c].statements == stat and self.stop is False:
                        metadata = "self." + mdDes[self.c].tag
                        str1 += (
                            "".join(metadata)
                            + "='"
                            + str(mdDes[self.c].mdItem[n].getValue())
                            + "'\n"
                        )
                        self.plusC()
                        numOfItems += 1

                    self.minusC(numOfItems)
                    self.executeStr1(str1, False)
                    str1 = ""
                self.plusC(numOfItems)

        def in2Statements():
            """possible combinations of statements
            (1)    IF:
                       FOR:
            (1.1)           item (with init OWSLib object)
                            "or"
            (1.2)           item (without init)
                ----------------------------------------------------
            (2)     FOR:
                        FOR:(implemented fixedly just for MD-keywords)
            (2.1)            item (with init OWSLib object)
                             "or"
            (2.2)            item (without init)
            """
            prepareStatements()
            cTmp = self.c
            cTmp1 = self.c + 1
            tag = str(mdDes[cTmp].tag).split()
            tag1 = str(mdDes[cTmp1].tag).split()
            stat = mdDes[self.c + 2].statements

            append = "self." + str(tag1[-1]) + ".append(self.val)\n"
            appendNoInit = "self." + str(tag1[-1])
            # (1)
            # if statements-if in jinja template=skip and do single loop
            if "if" in tag and "for" in tag1:
                leng = len(mdDes[self.c + 2].mdItem)
                # (1.1)
                if mdDes[cTmp1].object:
                    condition = mdDes[cTmp].tag.replace(" md.", " self.md.") + ":\n"
                    objectOWSLib = "\t" + "self.val=" + mdDes[cTmp1].object + "\n"
                    condition2 = (
                        "\t" + mdDes[cTmp1].tag.replace(" md.", " self.md.") + ":\n"
                    )
                    self.plusC()
                    self.plusC()

                    for n in range(leng):
                        numOfItems = 0
                        str1 = condition + "\n"
                        str1 += condition2 + "\n"
                        str1 += "\t" + objectOWSLib + "\n"

                        while mdDes[self.c].statements == stat and self.stop is False:
                            metadata = re.split(r"[.]", mdDes[self.c].tag)
                            metadata[0] = "\t\tself.val"
                            str1 += (
                                "".join(metadata)
                                + "='"
                                + str(mdDes[self.c].mdItem[n].getValue())
                                + "'\n"
                            )
                            self.plusC()
                            numOfItems += 1

                        str1 += "\t\t" + append
                        self.executeStr1(str1, False)
                        str1 = ""
                        self.minusC(numOfItems)
                    self.plusC(numOfItems)
                # (1.2)"if and for "
                else:
                    self.plusC()
                    self.plusC()
                    numOfItems = 0
                    size = len(mdDes[self.c].mdItem)
                    for n in range(size):
                        numOfItems = 0
                        str1 = ""

                        while mdDes[self.c].statements == stat and self.stop is False:
                            str1 += (
                                appendNoInit
                                + '.append("'
                                + mdDes[self.c].mdItem[n].getValue()
                                + '")\n'
                            )
                            self.plusC()
                            numOfItems += 1

                        self.executeStr1(str1, False)
                        self.minusC(numOfItems)
                    self.plusC(numOfItems)
            # (2) only keywords  (dict)
            elif "for" in tag and "for" in tag1:  #
                self.plusC()  # skip statementes 2x
                self.plusC()
                numOfkwGroup = len(mdDes[self.c + 1].mdItem)
                for n in range(numOfkwGroup):
                    kw = {}
                    kw["keywords"] = []
                    try:
                        keyWordLen = len(mdDes[self.c].mdItem[n])
                        for k in range(keyWordLen):
                            kw["keywords"].append(mdDes[self.c].mdItem[n][k].getValue())
                    except:
                        kw["keywords"].append(mdDes[self.c].mdItem[n].getValue())

                    kw["type"] = None
                    kw["thesaurus"] = {}
                    kw["thesaurus"]["title"] = mdDes[self.c + 1].mdItem[n].getValue()
                    kw["thesaurus"]["date"] = mdDes[self.c + 2].mdItem[n].getValue()
                    kw["thesaurus"]["datetype"] = mdDes[self.c + 3].mdItem[n].getValue()
                    self.md.identification.keywords.append(kw)

                self.plusC()
                self.plusC()
                self.plusC()
                self.plusC()

        # ------------------------------------------------------------------------------ next function
        self.mdo = MdFileWork()
        self.md = self.mdo.initMD()
        # most of objects from OWSLib is initialized in configure file
        # dirpath = os.path.dirname(os.path.realpath(__file__))
        context = mdutil.StaticContext()
        path = os.path.join(context.lib_path, "config", "init_md.txt")

        mdInitData = open(path, "r")
        mdExec = mdInitData.read()
        self.executeStr1(mdExec, None)

        self.c = 0
        self.stop = False
        self.max = len(self.mdDescription)
        mdDes = self.mdDescription

        while self.stop is False:
            # if no statements
            if (
                mdDes[self.c].statements is None
                and "if" not in mdDes[self.c].tag.split()
                and "for" not in mdDes[self.c].tag.split()
            ):
                noneStatements()

            # if 2x statements
            elif chckIf2xStatements():
                in2Statements()

            # if 1x statements
            elif chckIf1Statements:
                inStatements()

        self.md = self.getKeywordsFromRepositoryWidget(self.md)
        return self.md

    # ------------------------------------ END- FILL OWSLib BY EDITED METADATA IN GUI

    def exportToXml(self, jinjaPath, outPath, xmlOutName, msg):
        self.saveMDfromGUI()
        self.mdo.saveToXML(self.md, None, jinjaPath, outPath, xmlOutName, msg)

    def exportTemplate(self, jinjaPath, outPath, xmlOutName):
        self.profilePath = jinjaPath
        owsTagList = self.defineTemplate()
        self.saveMDfromGUI()
        self.mdo.saveToXML(
            self.md,
            owsTagList,
            self.profilePath,
            outPath,
            xmlOutName,
            msg=True,
            rmTeplate=True,
        )

    # ------------------------------------------------------------------------ LAYOUT

    def _layout(self):
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.mainSizer)
        noteSizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook.SetSizer(noteSizer)
        self.mainSizer.Add(self.notebook, proportion=1, flag=wx.EXPAND)
        self.Show()
