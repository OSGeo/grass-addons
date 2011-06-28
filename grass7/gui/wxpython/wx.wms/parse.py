from xml.dom.minidom import parse, parseString
from urllib2 import Request, urlopen, URLError, HTTPError
    
def parsexml():
    url = 'http://www.gisnet.lv/cgi-bin/topo?request=GetCapabilities&service=wms'
    req = Request(url)
    response = urlopen(req)
    xml = response.read()
    dom = parseString(xml)
    layerlist = dom.getElementsByTagName('Layer')
    for node in layerlist:
    	#print node.toxml()
    	namelist = node.getElementsByTagName('Name')
    	for name in namelist:
    		print name.toxml()
       

parsexml()

