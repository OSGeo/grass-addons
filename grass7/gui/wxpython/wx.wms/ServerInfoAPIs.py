from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup

class ServerData():
    pass

def initServerInfoBase(fileName):
    try:
        f = open(fileName,'r')
        xml = f.read()   
        f.close()
        soup = BeautifulStoneSoup(xml)
        serverinfolist = soup.findAll('serverinfo')
        print 'serverinfolisthere'
        print serverinfolist
        print len(serverinfolist)    
    except:
        serverinfolist = []
        soup = BeautifulSoup()
        xml = "null"
    
    if(len(serverinfolist) == 0):

            serverinfo = Tag(soup, "serverinfo")
            soup.insert(0, serverinfo)
            
    return soup


def addServerInfo(soup, serverinfo, snamevalue, urlvalue, unamevalue, passwordvalue):
    elements = soup.findAll(id = snamevalue)
    if(len(elements)!=0):
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
        server['id'] = snamevalue
    
        #Adding text values to the server info fields
        servername.insert(0,snamevalue)
        serverurl.insert(0, urlvalue)
        username.insert(0, unamevalue)
        password.insert(0, passwordvalue)
        return True

def removeServerInfo(soup, serverID):
    elements = soup.findAll(id = serverID)
    if(len(elements)==0):
        return False
    else:
        for element in elements:
            element.extract()
        return True

def updateServerInfo(soup, serverinfo, snamevalue, urlvalue, unamevalue, passwordvalue):
    if(removeServerInfo(soup, snamevalue)):
        print "1"
        if(addServerInfo(soup, serverinfo, snamevalue, urlvalue, unamevalue, passwordvalue)):
            return True
        else:
            return False
    else:
        return False

def getAllRows(soup):
    elements = soup.findAll('server')
    servers = {}
    for element in elements:
        servername = element.findAll('servername')[0]
        serverurl = element.findAll('serverurl')[0]
        username = element.findAll('username')[0]
        password = element.findAll('password')[0]
        serverdata = ServerData()
        serverdata.servername = servername.contents[0].strip()
        serverdata.url = serverurl.contents[0].strip()
        serverdata.username = username.contents[0].strip()
        serverdata.password = password.contents[0].strip()
        servers[serverdata.servername] = serverdata
        
    return servers