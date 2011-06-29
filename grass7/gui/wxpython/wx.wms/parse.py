from xml.dom.minidom import parse, parseString
from urllib2 import Request, urlopen, URLError, HTTPError
     
def parsexml(xml):
    dom = parseString(xml)
    layerlist = dom.getElementsByTagName('Layer')
    for node in layerlist:
    	#print node.toxml()
    	namelist = node.getElementsByTagName('Name')
    	l = []
    	for name in namelist:
    		l = l + [(name.toxml())]
    	return l

