from BeautifulSoup import BeautifulSoup, Tag, NavigableString, BeautifulStoneSoup
from ServerInfoAPIs import addServerInfo, removeServerInfo, updateServerInfo, initServerInfoBase, getAllRows


soup, f = initServerInfoBase('out.xml')
print addServerInfo(soup, soup.serverinfo, 'a1', 'b1', 'c1', 'd1')
print addServerInfo(soup, soup.serverinfo, 'a2', 'b2', 'c2', 'd2')
print addServerInfo(soup, soup.serverinfo, 'a1', 'b1', 'c1', 'd1')              
print updateServerInfo(soup, soup.serverinfo, 'a1', 'b112', 'c112', 'd112')
print removeServerInfo(soup, "a2")

print getAllRows(soup)
xml = soup.prettify()
f.write(xml)
f.close()
