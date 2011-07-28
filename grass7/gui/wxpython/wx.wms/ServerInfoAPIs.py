from BeautifulSoup import BeautifulSoup, Tag, BeautifulStoneSoup

def addServerInfo(soup, serverinfo, snamevalue, urlvalue, unamevalue, passwordvalue):
    
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

def removerServerInfo(soup, serverID):
    elements = soup.findAll(id = serverID)
    for element in elements:
        element.extract()
        

    