"""!
@package ServerInfoAPIs.py

@brief Python code providing API's for managing the xml
based file storing of the server information.

Classes:
 - ServerData
Functions:
 - initServerInfoBase
 - ifServerNameExists
 - addServerInfo
 - removeServerInfo
 - updateServerInfo
 - getAllRows

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup
import os.path

# PY2/PY3 compat
if sys.version_info.major >= 3:
    unicode = str


class ServerData:
    pass


def initServerInfoBase(fileName):
    """
    @description: Intializes soup for the Beautiful soup parser. Reads the exisitng Data from the fileName paramter.
    @todo:None
    @param xml: String, Name of file to be loaded in soup.
    @return: Boolean, True if a successful, else False
    """
    if os.path.exists(fileName):
        try:
            f = open(fileName, "r")
        except:
            return None, False
        xml = f.read()
        f.close()
        soup = BeautifulStoneSoup(xml)
        serverinfolist = soup.findAll("serverinfo")
    else:
        serverinfolist = []
        soup = BeautifulSoup()
        xml = "null"

    if len(serverinfolist) == 0:
        serverinfo = Tag(soup, "serverinfo")
        soup.insert(0, serverinfo)

    return soup, True


def ifServerNameExists(soup, servername):
    """
    @description: Checks for the membership of servername in the soup
    @todo:None
    @param soup: soup
    @param servername: String, name of the server to be checked for
    @return: Boolean, True if found, else False
    """
    servers = soup.findAll("servername")
    for server in servers:
        name = server.string.strip()
        if name == servername:
            return True
        else:
            return False
    return False


def addServerInfo(
    soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue
):
    """
    @description: Adds server info to the soup
    @todo:None
    @param soup: soup
    @param serverinfo:
    @param uid: Unique Id of the server
    @param snamevalue: String, server name
    @param urlvalue: String, url of the server
    @param unamevalue: String, UserName for the server
    @param passwordvalue: String, password for the server
    @return: Boolean, True if added successfuly, else False
    """
    snamevalue = unicode(snamevalue)
    if ifServerNameExists(soup, snamevalue):
        return False
    else:
        server = Tag(soup, "server")
        serverinfo.insert(0, server)
        # Creating server info tags
        servername = Tag(soup, "servername")
        serverurl = Tag(soup, "serverurl")
        username = Tag(soup, "username")
        password = Tag(soup, "password")
        # Inserting server info fields
        server.insert(0, servername)
        server.insert(1, serverurl)
        server.insert(2, username)
        server.insert(3, password)
        # Adding attribute to server tag
        server["id"] = uid
        # Adding text values to the server info fields
        servername.insert(0, snamevalue)
        serverurl.insert(0, urlvalue)
        username.insert(0, unamevalue)
        password.insert(0, passwordvalue)
        return True


def removeServerInfo(soup, serverID):
    """
    @description: removes server with uid = serverID
    @todo:None
    @param soup: soup
    @param serverID: String, UID of the server to be removed.
    @return: Boolean, True if successfuly removed, else False
    """
    serverID = unicode(serverID)
    elements = soup.findAll(id=serverID)
    if len(elements) == 0:
        return False
    else:
        for element in elements:
            element.extract()
        return True


def updateServerInfo(
    soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue
):
    """
    @description: updates server with uid = uid
    @todo:None
    @param soup: soup
    @param serverinfo:
    @param uid: Unique Id of the server
    @param snamevalue: String, server name
    @param urlvalue: String, url of the server
    @param unamevalue: String, UserName for the server
    @param passwordvalue: String, password for the server
    @return: Boolean, True if updated successfuly, else False
    """
    snamevalue = unicode(snamevalue)
    if removeServerInfo(soup, uid):
        if addServerInfo(
            soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue
        ):
            return True
        else:
            return False
    else:
        return False


def getAllRows(soup):
    """
    @description: returns all the rows in the xml file table.
    @todo:None
    @param soup: soup
    @return: servers(dictionary), map_servernameTouid(dictionary)
    """
    elements = soup.findAll("server")
    servers = {}
    map_servernameTouid = {}
    for element in elements:
        uid = element["id"]
        servername = element.findAll("servername")[0]
        serverurl = element.findAll("serverurl")[0]
        username = element.findAll("username")[0]
        password = element.findAll("password")[0]
        serverdata = ServerData()
        serverdata.servername = unicode(servername.contents[0].strip())
        serverdata.url = serverurl.contents[0].strip()
        serverdata.username = username.contents[0].strip()
        serverdata.password = password.contents[0].strip()
        servers[uid] = serverdata
        map_servernameTouid[serverdata.servername] = uid
    return servers, map_servernameTouid
