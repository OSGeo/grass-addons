from BeautifulSoup import BeautifulSoup, Tag, NavigableString, BeautifulStoneSoup


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

try:
    f = open('out.xml','r+')
    xml = f.read()   
    soup = BeautifulStoneSoup(xml)
    serverinfolist = soup.findAll('serverinfo')
    print len(serverinfolist)    
except:
    f = open('out.xml','w')
    serverinfolist = []
    
if(len(serverinfolist) == 0):
        serverinfo = Tag(soup, "serverinfo")
        soup.insert(0, serverinfo)
        
        
addServerInfo(soup, soup.serverinfo, 'a2', 'b2', 'c2', 'd2')

xml = soup.prettify()

#f = open('out.xml','w')
f.write(xml)
f.close()



#xml = "<doc><tag1>Contents 1<tag2>Contents 2<tag1>Contents 3"
soup1 = BeautifulStoneSoup(xml)
print soup1.prettify()