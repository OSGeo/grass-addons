from BeautifulSoup import BeautifulSoup, Tag, NavigableString, BeautifulStoneSoup
from ServerInfoAPIs import addServerInfo, removerServerInfo

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
                
addServerInfo(soup, soup.serverinfo, 'a1', 'b1', 'c1', 'd1')
addServerInfo(soup, soup.serverinfo, 'a2', 'b2', 'c2', 'd2')
removerServerInfo(soup, "a2")
xml = soup.prettify()
f.write(xml)
f.close()
