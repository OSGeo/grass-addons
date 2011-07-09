from BeautifulSoup import BeautifulSoup
import re
from urllib2 import Request, urlopen, URLError, HTTPError

def parsexml(xml):

 xmltext = xml
 soup = BeautifulSoup(xmltext)
 #layers = soup.findAll('layer', queryable="1")
 layers = soup.findAll('layer')
 namelist = []
 for layer in layers:
	soupname = BeautifulSoup(str(layer))
	names =  soupname.findAll('name')
	if len(names) > 0:
		namelist += names[0]
 return namelist
	

