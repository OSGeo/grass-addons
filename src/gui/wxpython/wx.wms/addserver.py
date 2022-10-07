# -*- coding: utf-8 -*-
"""!
@package addserver.py

@brief Main Python app for managing the server information.
Add a new server, Edit an existing server, Remove an existing
server.

Classes:
 - ServerData
 - ServerAdd

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author: Maris Nartiss (maris.nartiss gmail.com)
@author: Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

import wx
import os
import popen2
import uuid
from urllib2 import Request, urlopen, URLError, HTTPError
import urlparse
import urllib

from grass.script import core as grass
from wx.lib.pubsub import Publisher
from BeautifulSoup import BeautifulSoup, Tag, NavigableString, BeautifulStoneSoup
from ServerInfoAPIs import (
    addServerInfo,
    removeServerInfo,
    updateServerInfo,
    initServerInfoBase,
    getAllRows,
)
from parse import parsexml, isServiceException, populateLayerTree, isValidResponse
from LoadConfig import loadConfigFile

# PY2/PY3 compat
if sys.version_info.major >= 3:
    unicode = str


class ServerData:
    pass


class Message:
    pass


class ServerAdd(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: ServerAdd.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.StatusBar = self.CreateStatusBar(1, 0)
        self.Servers = wx.StaticText(self, -1, "  Servers")
        self.ServerList = wx.ComboBox(self, -1, choices=[], style=wx.CB_DROPDOWN)
        self.static_line_1 = wx.StaticLine(self, -1)
        self.ServerName = wx.StaticText(self, -1, "  ServerName*")
        self.ServerNameText = wx.TextCtrl(self, -1, "")
        self.URL = wx.StaticText(self, -1, "  URL*")
        self.URLText = wx.TextCtrl(self, -1, "")
        self.Username = wx.StaticText(self, -1, "  Username")
        self.UsernameText = wx.TextCtrl(self, -1, "")
        self.Password = wx.StaticText(self, -1, "  Password")
        self.PasswordText = wx.TextCtrl(self, -1, "", style=wx.TE_PASSWORD)
        self.PasswordExplain = wx.StaticText(
            self, -1, "  Note: Password will be stored as a plain text"
        )
        self.static_line_2 = wx.StaticLine(self, -1)
        self.Save = wx.Button(self, -1, "Save")
        self.Remove = wx.Button(self, -1, "Remove")
        self.AddNew = wx.Button(self, -1, "AddNew")
        self.Quit = wx.Button(self, -1, "Quit")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.OnServerList, self.ServerList)
        self.Bind(wx.EVT_TEXT, self.OnText, self.ServerNameText)
        self.Bind(wx.EVT_TEXT, self.OnText, self.URLText)
        self.Bind(wx.EVT_TEXT, self.OnText, self.UsernameText)
        self.Bind(wx.EVT_TEXT, self.OnText, self.PasswordText)
        self.Bind(wx.EVT_BUTTON, self.OnSave, self.Save)
        self.Bind(wx.EVT_BUTTON, self.OnRemove, self.Remove)
        self.Bind(wx.EVT_BUTTON, self.OnAddNew, self.AddNew)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, self.Quit)
        # end wxGlade

        # sudeep code starts
        if not loadConfigFile(self):
            grass.fatal_error(
                _("Configuration file error. Unable to start application.")
            )
            self.Close()

        self.soup, open = initServerInfoBase("ServersList.xml")
        if not open:
            return
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.__populate_URL_List(self.ServerList)
        Publisher().subscribe(self.OnWMSMenuClose, ("WMS_Menu_Close"))
        self.editOn = False
        self.selectedUid = None
        self.selectedServer = None
        # sudeep code ends

    def __set_properties(self):
        # begin wxGlade: ServerAdd.__set_properties
        self.SetTitle("AddServer")
        self.SetSize((422, 250))
        self.StatusBar.SetStatusWidths([-1])
        # statusbar fields
        StatusBar_fields = ["StatusBar"]
        for i in range(len(StatusBar_fields)):
            self.StatusBar.SetStatusText(StatusBar_fields[i], i)
        self.Servers.SetMinSize((90, 17))
        self.ServerList.SetMinSize((189, 29))
        self.ServerName.SetMinSize((96, 20))
        self.ServerNameText.SetMinSize((189, 25))
        self.URL.SetMinSize((90, 20))
        self.URLText.SetMinSize((189, 25))
        self.Username.SetMinSize((90, 20))
        self.UsernameText.SetMinSize((189, 25))
        self.Password.SetMinSize((90, 20))
        self.PasswordText.SetMinSize((189, 25))
        self.PasswordExplain.SetMinSize((303, 20))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: ServerAdd.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_7 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2.Add(self.Servers, 0, 0, 0)
        sizer_2.Add(self.ServerList, 0, 0, 0)
        sizer_1.Add(sizer_2, 0, wx.EXPAND, 0)
        sizer_1.Add(self.static_line_1, 0, wx.EXPAND, 0)
        sizer_3.Add(self.ServerName, 0, 0, 0)
        sizer_3.Add(self.ServerNameText, 0, 0, 0)
        sizer_1.Add(sizer_3, 1, wx.EXPAND, 0)
        sizer_4.Add(self.URL, 0, 0, 0)
        sizer_4.Add(self.URLText, 0, 0, 0)
        sizer_1.Add(sizer_4, 1, wx.EXPAND, 0)
        sizer_5.Add(self.Username, 0, 0, 0)
        sizer_5.Add(self.UsernameText, 0, 0, 0)
        sizer_1.Add(sizer_5, 1, wx.EXPAND, 0)
        sizer_6.Add(self.Password, 0, 0, 0)
        sizer_6.Add(self.PasswordText, 0, 0, 0)
        sizer_1.Add(sizer_6, 1, wx.EXPAND, 0)
        sizer_1.Add(self.PasswordExplain, 0, 0, 0)
        sizer_1.Add(self.static_line_2, 0, wx.EXPAND, 0)
        sizer_7.Add(self.Save, 0, 0, 0)
        sizer_7.Add(self.Remove, 0, 0, 0)
        sizer_7.Add(self.AddNew, 0, 0, 0)
        sizer_7.Add(self.Quit, 0, 0, 6)
        sizer_1.Add(sizer_7, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        self.Layout()
        # end wxGlade

    def valueExists(self, dict, newServerName):
        """
        @description: to check if a value exists in the dictionary or not.
        @todo:None
        @param self: reference variable
        @param dict: dictionary.
        @param newServerName: String, value to be checked for.
        @return: boolean
        """
        try:
            for key, value in dict.items():
                if value.servername == newServerName:
                    return True
            return False
        except:
            return False

    def parse_WMS_URL(self, full_url):
        """
        @description: Strips any WMS parts from url for easy reuse.
           Strips all WMS 1.1.1 and 1.3.0 parts from URL.
           This could be moved to some separate WxS support procedure file.
        @todo:None
        @param self: reference variable
        @param full_url: user provided WMS URL.
        @return: URL as dict suitable for storage or None if provided URL isn't a valid WMS URL.
        """
        WMS_13_parameters = (
            "VERSION",
            "SERVICE",
            "REQUEST",
            "FORMAT",
            "UPDATESEQUENCE",
            "LAYERS",
            "STYLES",
            "CRS",
            "BBOX",
            "WIDTH",
            "HEIGHT",
            "TRANSPARENT",
            "BGCOLOR",
            "EXCEPTIONS",
            "TIME",
            "ELEVATION",
            "QUERY_LAYERS",
            "INFO_FORMAT",
            "FEATURE_COUNT",
            "I",
            "J",
        )
        url = urlparse.urlparse(full_url)
        final_url = {
            "scheme": url.scheme,
            "hostname": url.hostname,
            "port": url.port,
            "path": url.path,
            "params": url.params,
            "username": url.username,
            "password": url.password,
            "netloc": url.netloc,
        }

        # WMS supports only http or https
        if final_url["scheme"] not in ("http", "https"):
            # URL without scheme is not a valid one. http is a good guess.
            if url.scheme == "":
                return self.parse_WMS_URL("http://" + full_url)
            return None

        # If URL lacks host, it's not valid
        if not final_url["hostname"]:
            return None

        # Leave any non-WMS query parts
        query = urlparse.parse_qs(url.query)
        for k in query.keys():
            if k.upper() in WMS_13_parameters:
                del query[k]
        final_url["query"] = urllib.urlencode(query)
        return urlparse.urlunparse(
            (
                final_url["scheme"],
                final_url["netloc"],
                final_url["path"],
                final_url["params"],
                final_url["query"],
                None,
            )
        )

    def OnSave(self, event):  # wxGlade: ServerAdd.<event_handler>
        """
        @description: Called on Save button press. Validates the information provided.
        Saves or updates the provided information.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: None
        """
        newServerName = unicode(self.ServerNameText.GetValue())
        newUrl = self.URLText.GetValue()
        newUserName = self.UsernameText.GetValue()
        newPassword = self.PasswordText.GetValue()

        newUrl = self.parse_WMS_URL(newUrl.strip())
        if not newUrl:
            message = _("Provided WMS URL is not valid.")
            self.ShowMessage(message, _("Error"))
            grass.warning(message)
            return

        if self.selectedUid is None:
            update = False
        else:
            update = True

        serverData = ServerData()

        if len(newServerName) != 0:
            if self.selectedServer is not None:
                if not self.selectedServer.servername == newServerName:
                    if self.valueExists(self.servers, newServerName):
                        message = _(
                            "Server name already exists. Please enter a different server name"
                        )
                        self.ShowMessage(message, _("Warning"))
                        grass.warning(message)
                        StatusBar_fields = [message]
                        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                        return

            validUrl, message = self.validateUrl(newUrl)
            if not validUrl:
                message = _("Unable to validate URL (%s)") % message
                self.ShowMessage(message, _("Warning"))
                grass.warning(message)
            else:
                message = _("Url validated (%s)") % message

            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            serverData.servername = newServerName
            serverData.url = newUrl
            serverData.username = newUserName
            serverData.password = newPassword

            if update:
                if updateServerInfo(
                    self.soup,
                    self.soup.serverinfo,
                    self.selectedUid,
                    newServerName,
                    newUrl,
                    newUserName,
                    newPassword,
                ):
                    if not self.saveXMLData():
                        oldInfo = self.servers[self.selectedUid]
                        if updateServerInfo(
                            self.soup,
                            self.soup.serverinfo,
                            self.selectedUid,
                            oldInfo.servername,
                            oldInfo.url,
                            oldInfo.username,
                            oldInfo.password,
                        ):
                            message = _("Unable to save XML, changes reverted back")
                            grass.warning(message)
                            return
                        else:
                            message = _(
                                "Unable to save XML, changes will be reverted back on restart"
                            )
                            grass.warning(message)
                            return
                    message = "update save successful"
                    grass.message(message)
                    self.servers[self.selectedUid] = serverData
                    del self.map_servernameTouid[self.selectedServer.servername]
                    self.selectedServer = serverData
                    self.map_servernameTouid[newServerName] = self.selectedUid

                    msg = self.servers
                    Publisher().sendMessage(("update.serverList"), msg)

                    msg = self.map_servernameTouid
                    Publisher().sendMessage(("update.map_servernameTouid"), msg)
                    message = _("Server Info Updated")
                    grass.message(message)
                    StatusBar_fields = [message]
                    self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                    self.setModified(False)
                else:
                    message = _("Update not Successful")
                    self.ShowMessage(message, "Warning")
                    grass.warning(message)
                    StatusBar_fields = [message]
                    self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            else:
                uid = str(uuid.uuid4())
                if addServerInfo(
                    self.soup,
                    self.soup.serverinfo,
                    uid,
                    newServerName,
                    newUrl,
                    newUserName,
                    newPassword,
                ):
                    if not self.saveXMLData():
                        if removeServerInfo(self.soup, uid):
                            message = _("Unable to save XML. Info not saved")
                            grass.warning(message)
                            return
                        else:
                            message = _(
                                "Unable to save XML. Changes will be reverted back on restart"
                            )
                            grass.warning(message)
                            return
                    message = "soup save successfully"
                    grass.message(message)
                    self.selectedUid = uid
                    self.servers[self.selectedUid] = serverData
                    self.selectedServer = serverData
                    self.map_servernameTouid[newServerName] = uid
                    msg = self.servers
                    Publisher().sendMessage(("update.serverList"), msg)
                    msg = self.map_servernameTouid
                    Publisher().sendMessage(("update.map_servernameTouid"), msg)
                    message = "Server Info Saved Successfully"
                    grass.message(message)
                    StatusBar_fields = [message]
                    self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                    self.setModified(False)
                else:
                    message = "Save not successful"
                    self.ShowMessage(message, "Warning")
                    "Server Info Saved Successfully"
                    StatusBar_fields = [message]
                    self.StatusBar.SetStatusText(StatusBar_fields[0], 0)

            self.selectedURL = newUrl
            self.__update_URL_List()
        else:
            message = _("Please fill in server name")
            self.ShowMessage(message, _("Warning"))
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)

        self.editOn = False
        if event:
            event.Skip()

    def OnRemove(self, event):  # wxGlade: ServerAdd.<event_handler>
        """
        @description: Called on Remove button press. Deleted the server info selected to be deleted.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: None
        """
        if self.selectedUid is None:
            message = _("No server selected. Remove unsuccessful")
            self.ShowMessage(message, _("Warning"))
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return
        else:
            if removeServerInfo(self.soup, self.selectedUid):
                if not self.saveXMLData():
                    uid = self.selectedUid
                    servername = self.servers[uid].servername
                    url = self.servers[uid].url
                    username = self.servers[uid].username
                    password = self.servers[uid].password
                    if addServerInfo(
                        self.soup,
                        self.soup.serverinfo,
                        uid,
                        servername,
                        url,
                        username,
                        password,
                    ):
                        message = "Unable to write data in file, Changes reverted, Remove unsuccessful"
                        grass.warning(message)
                        StatusBar_fields = [message]
                        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                        return
                    else:
                        message = "Unable to write data in file, Unable to revert changes, Remove unsuccessful"
                        grass.warning(message)
                        StatusBar_fields = [message]
                        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                        return

                message = "Remove Successful"
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                grass.message(message)
                del self.map_servernameTouid[self.selectedServer.servername]
                if len(self.servers) > 0:
                    self.ServerList.SetSelection(0)
                if len(self.servers) == 0:
                    self.ServerList.Clear()

                del self.servers[self.selectedUid]
                self.selectedUid = None
                self.__update_URL_List()
                self.selectedServer = None
                self.ServerNameText.Clear()
                self.PasswordText.Clear()
                self.URLText.Clear()
                self.UsernameText.Clear()
                msg = self.servers
                Publisher().sendMessage(("update.serverList"), msg)
            else:
                message = "Remove Unsuccessful"
                self.ShowMessage(message, "Warning")
                grass.warning(message)
                StatusBar_fields = [message]
                self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
                return

        self.editOn = False
        event.Skip()

    def OnAddNew(self, event):  # wxGlade: ServerAdd.<event_handler>
        """
        @description: Called on AddNew button press. Clears all the fields.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: None
        """
        self.checkIfModified(event)
        self.selectedUid = None
        self.ServerNameText.Clear()
        self.PasswordText.Clear()
        self.URLText.Clear()
        self.UsernameText.Clear()
        self.editOn = False
        self.selectedServer = None
        StatusBar_fields = ["Fill in the Info fields"]
        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
        event.Skip()

    def OnQuit(self, event):  # wxGlade: ServerAdd.<event_handler>
        """
        @description: Called on Quit button press. Closes the AddServerFrame.
        Sends   Add_Server_Frame_Closed message to wmsmenu Frame before closing.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: None
        """
        if self.checkIfModified(event) == wx.ID_CANCEL:
            return
        if not self.saveXMLData():
            message = "Unable to write in file, Exiting Application"
            grass.message(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)

        msg = self.servers
        Publisher().sendMessage(("Add_Server_Frame_Closed"), msg)
        self.Destroy()
        event.Skip()

    def OnServerList(self, event):  # wxGlade: ServerAdd.<event_handler>
        """
        @description: Called on ServerList (ComboBox) select.
        Parses the selected url and fills the corresponding fields with the information present.
        Sends   Add_Server_Frame_Closed message to wmsmenu Frame before closing.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: None
        """
        self.checkIfModified(event)
        info = self.ServerList.GetValue()
        if len(info) == 0:
            return
        urlarr = info.split(self.name_url_delimiter)
        if len(urlarr) == 2:
            uid = self.map_servernameTouid[urlarr[0]]
            self.selectedUid = uid
            self.selectedServer = self.servers[uid]
            self.ServerNameText.SetValue(self.selectedServer.servername)
            self.URLText.SetValue(self.selectedServer.url)
            self.UsernameText.SetValue(self.selectedServer.username)
            self.PasswordText.SetValue(self.selectedServer.password)
        else:
            message = "Wrong format of URL selected"
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            grass.fatal_error(message)

        event.Skip()

    def OnText(self, event):  # wxGlade: ServerAdd.<event_handler>
        self.editOn = True
        event.Skip()

    # wxGlade methods ends

    def setModified(self, booleanValue):
        """
        @description: Sets SetModified function of all fields to booleanValue.
        @todo:None
        @param self: reference variable
        @param booleanValue: Boolean, boolean value to be set
        @return: None
        """
        self.ServerNameText.SetModified(booleanValue)
        self.URLText.SetModified(booleanValue)
        self.UsernameText.SetModified(booleanValue)
        self.PasswordText.SetModified(booleanValue)

    def checkIfModified(self, event):
        """
        @description: To check if any field is modified and unsaved. Displays a pop-up if a field is Unsaved.
        @todo:None
        @param self: reference variable
        @param event: event associated
        @return: wx.ID_CANCEL or wx.ID_YES
        """
        if (
            self.URLText.IsModified()
            or self.ServerNameText.IsModified()
            or self.UsernameText.IsModified()
            or self.PasswordText.IsModified()
        ):
            dial = wx.MessageDialog(
                None,
                "You have unsaved changes.\n Do you want to save them ?",
                "Quit",
                wx.STAY_ON_TOP
                | wx.YES_NO
                | wx.YES_DEFAULT
                | wx.CANCEL
                | wx.ICON_QUESTION,
            )
            val = dial.ShowModal()
            if val == wx.ID_CANCEL:
                return val
            if val == wx.ID_YES:
                self.OnSave(event)
                return val

    def ShowMessage(self, message, type="Warning"):
        """
        @description: Display's the message as a pop-up.
        @todo:None
        @param self: reference variable
        @param message: String, message to be displayed.
        @param type: String, the type of message
        @return: None
        """
        wx.MessageBox(message, type)

    def __populate_URL_List(self, ComboBox):
        """
        @description: Internal function to populate ServerList(ComboBox). Used to populate ServerList for the first time in the init function.
        @todo:None
        @param self: reference variable
        @param ComboBox: ComboBox to be updated.
        @return: None
        """
        self.servers, self.map_servernameTouid = getAllRows(self.soup)
        ComboBox.Append("")
        for key, value in self.servers.items():
            ComboBox.Append(
                value.servername
                + self.name_url_delimiter
                + value.url[0 : self.urlLength]
            )
        return

    def __update_URL_List(self):
        """
        @description: Internal function to update ServerList(ComboBox).
        @todo:None
        @param self: reference variable
        @param ComboBox: ComboBox to be updated.
        @return: None
        """
        self.ServerList.Clear()
        ComboBox = self.ServerList
        ComboBox.Append("")
        for key, value in self.servers.iteritems():
            ComboBox.Append(
                value.servername
                + self.name_url_delimiter
                + value.url[0 : self.urlLength]
            )

    def saveXMLData(self):
        """
        @description: Saves the information (soup) , in the file ServersList.xml.
        @todo:None
        @param self: reference variable
        @return: Boolean, True if save is successful else returns False.
        """
        xml = self.soup.prettify()
        try:
            TMP = grass.tempfile()
            if TMP is None:
                grass.fatal_error(_("Unable to create temporary files"))
            f = open(TMP, "w")
            f.write(xml)
            f.close()
        except:
            message = _("Unable to write in %s file. Save not successful") % TMP
            grass.warning(message)
            return False
        try:
            copyCommand = "cp " + TMP + " ServersList.xml"  # FIXME
            r, w, e = popen2.popen3(copyCommand)
            if len(e.readlines()) != 0:
                message = "Copy failed, raising excpetion in savexml()"
                grass.warning(message)
                r.close()
                w.close()
                e.close()
                raise Exception
            r.close()
            w.close()
            e.close()
        except:
            return False

        return True

    def allFieldsValid(self, newServerName, newUrl, newUserName, newPassword):
        """
        @description: Validates all the field informations.
        @todo:None.
        @param self: reference variable.
        @param newServerName: String, name of the server.
        @param newUrl: String, url of the server.
        @param newUserName: String, UserName for the server.
        @param newPassword: String, Password for the server.
        @return: Boolean, True if all fields are valid, else False.
        """
        # FIXME All texts should be encoded and accept all characters!
        # Šitajam vajadzētu pazust, ja izmanto XML, kas automātiski kodē tekstus.
        if newServerName.count(self.name_url_delimiter) > 0:
            message = "Warning: UserName cannot consist of " + self.name_url_delimiter
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            return False

        if newUrl.count(self.name_url_delimiter) > 0:
            message = "Warning: URL cannot consist of " + self.name_url_delimiter
            StatusBar_fields = ["Warning: URL Delimiter conflict. Edit config file"]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            return False

        character = ">"
        if (
            newServerName.count(character) > 0
            or newUrl.count(character) > 0
            or newUserName.count(character) > 0
            or newPassword.count(character) > 0
        ):
            message = character + " is not allowed in a Field"
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return False

        character = "<"
        if (
            newServerName.count(character) > 0
            or newUrl.count(character) > 0
            or newUserName.count(character) > 0
            or newPassword.count(character) > 0
        ):
            message = character + " is not allowed in a Field"
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return False

        character = "&"
        if (
            newServerName.count(character) > 0
            or newUserName.count(character) > 0
            or newPassword.count(character) > 0
        ):
            message = character + " is not allowed in a Field"
            self.ShowMessage(message, "Warning")
            grass.warning(message)
            StatusBar_fields = [message]
            self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
            return False

        return True

    def validateUrl(self, url):
        """
        @description: Validates the url provided. Sends a getCapabilities request to the url server and checks for the response.
        @todo:None
        @param self: reference variable
        @return: Boolean, True if valid, else returns False.
        """
        message = _("Validating URL...")
        StatusBar_fields = [message]
        self.StatusBar.SetStatusText(StatusBar_fields[0], 0)
        req = Request(url)
        message = "Successful"
        try:
            response = urlopen(req, None, self.timeoutValueSeconds)
            xml = response.read()
            if not isValidResponse(xml):
                message = "Invalid GetCapabilties response"
            if isServiceException(xml):
                message = "Service Exception"
        except HTTPError as e:
            message = "The server couldn't fulfill the request."
        except URLError as e:
            message = "Failed to reach a server."
        except ValueError as e:
            message = "Value error"
        except Exception as e:
            message = "urlopen exception, unable to fetch data for getcapabilities"
            message = str(e)

        if not message == "Successful":
            return False, message
        else:
            return True, message

    def OnWMSMenuClose(self, msg):
        """
        @description: Called on receiving WMS_Menu_Close message from wmsmenu Frame.
        @todo:None
        @param self: reference variable
        @param msg: message received, not used in the function though.
        @return: None
        """
        self.Close()
        self.Destroy()
        return


# end of class ServerAdd


def AddServerFrame(parentWMS):
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_2 = ServerAdd(None, -1, "")
    app.SetTopWindow(frame_2)
    frame_2.Show()
    app.MainLoop()


if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    frame_2 = ServerAdd(None, -1, "")
    app.SetTopWindow(frame_2)
    frame_2.Show()
    app.MainLoop()
