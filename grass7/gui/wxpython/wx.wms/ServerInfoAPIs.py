from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup
import os.path

class ServerData():
    pass

def initServerInfoBase(fileName):
    if(os.path.exists(fileName)):
        try:
            f = open(fileName,'r')
        except:
            print 'Unable to open File '+fileName
            print 'exiting application...'
            return None, False
        xml = f.read()   
        f.close()
        soup = BeautifulStoneSoup(xml)
        serverinfolist = soup.findAll('serverinfo')
        #print 'serverinfolisthere'
        #print serverinfolist
        #print len(serverinfolist)    
    else:
        serverinfolist = []
        soup = BeautifulSoup()
        xml = "null"
    
    if(len(serverinfolist) == 0):
            serverinfo = Tag(soup, "serverinfo")
            soup.insert(0, serverinfo)
            
    return soup, True

def ifServerNameExists(soup,servername):
    servers = soup.findAll('servername')
    for server in servers:
        name = server.string.strip()
        if(name == servername):
            return True
        else:
            return False
    return False
    

def addServerInfo(soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue):
    snamevalue = unicode(snamevalue)
    if(ifServerNameExists(soup, snamevalue)):
        return False
    else:
        server = Tag(soup, "server")
        serverinfo.insert(0,server)
        
        #Creating server info tags
        servername = Tag(soup, "servername")
        serverurl = Tag(soup, "serverurl")
        username = Tag(soup, "username")
        password = Tag(soup, "password")
        
        #Inserting server info fields
        server.insert(0, servername)
        server.insert(1, serverurl)
        server.insert(2, username)
        server.insert(3, password)
    
        #Adding attribute to server tag
        
        server['id'] = uid
    
        #Adding text values to the server info fields
        servername.insert(0,snamevalue)
        serverurl.insert(0, urlvalue)
        username.insert(0, unamevalue)
        password.insert(0, passwordvalue)
        return True

def removeServerInfo(soup, serverID):
    serverID = unicode(serverID)
    elements = soup.findAll(id = serverID)
    if(len(elements)==0):
        return False
    else:
        for element in elements:
            element.extract()
        return True

def updateServerInfo(soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue):
    snamevalue = unicode(snamevalue)
    if(removeServerInfo(soup, uid)):
        if(addServerInfo(soup, serverinfo, uid, snamevalue, urlvalue, unamevalue, passwordvalue)):
            return True
        else:
            return False
    else:
        return False

def getAllRows(soup):
    elements = soup.findAll('server')
    servers = {}
    map_servernameTouid = {}
    for element in elements:
        uid = element['id']
        servername = element.findAll('servername')[0]
        serverurl = element.findAll('serverurl')[0]
        username = element.findAll('username')[0]
        password = element.findAll('password')[0]
        serverdata = ServerData()
        serverdata.servername = unicode(servername.contents[0].strip())
        serverdata.url = serverurl.contents[0].strip()
        serverdata.username = username.contents[0].strip()
        serverdata.password = password.contents[0].strip()
        servers[uid] = serverdata
        map_servernameTouid[serverdata.servername] = uid
    return servers, map_servernameTouid