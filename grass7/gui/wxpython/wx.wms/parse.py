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
       	'''temp = node.getElementsByTagName('Name')
    	if hasattr(temp,'toxml'):
    		temp.toxml()
    		print 'yoyo'
    	else:
    		print 'dkndskjfnskdjnksdjfn'
 '''


    #print layerlist
    '''forecasts = []
    for node in dom.getElementsByTagNameNS(WEATHER_NS, 'forecast'):
        forecasts.append({
            'date': node.getAttribute('date'),
            'low': node.getAttribute('low'),
            'high': node.getAttribute('high'),
            'condition': node.getAttribute('text')
        })
    ycondition = dom.getElementsByTagNameNS(WEATHER_NS, 'condition')[0]
    return {
        'current_condition': ycondition.getAttribute('text'),
        'current_temp': ycondition.getAttribute('temp'),
        'forecasts': forecasts,
        'title': dom.getElementsByTagName('title')[0].firstChild.data
    }'''
    


parsexml()

