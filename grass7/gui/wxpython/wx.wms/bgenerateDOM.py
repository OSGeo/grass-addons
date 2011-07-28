from BeautifulSoup import BeautifulSoup, Tag, NavigableString, BeautifulStoneSoup
from ServerInfoAPIs import addServerInfo, removeServerInfo, updateServerInfo

try:
    f = open('out.xml','r+')
    xml = f.read()   
    soup = BeautifulStoneSoup(xml)
    serverinfolist = soup.findAll('serverinfo')
    print len(serverinfolist)    
except:
    f = open('out.xml','w')
    serverinfolist = []
    soup = BeautifulSoup()

if(len(serverinfolist) == 0):
        serverinfo = Tag(soup, "serverinfo")
        soup.insert(0, serverinfo)
        
        
print addServerInfo(soup, soup.serverinfo, 'a1', 'b1', 'c1', 'd1')
print addServerInfo(soup, soup.serverinfo, 'a2', 'b2', 'c2', 'd2')
print addServerInfo(soup, soup.serverinfo, 'a1', 'b1', 'c1', 'd1')              
print updateServerInfo(soup, soup.serverinfo, 'a1', 'b112', 'c112', 'd112')
print removeServerInfo(soup, "a2")


xml = soup.prettify()
f.write(xml)
f.close()
