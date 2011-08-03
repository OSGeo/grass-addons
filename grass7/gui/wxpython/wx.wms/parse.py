from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import re
from urllib2 import Request, urlopen, URLError, HTTPError


def parsexml(xml):

 xmltext = xml
 soup = BeautifulSoup(xmltext)
 #layers = soup.findAll('layer', queryable="1")
 layers = soup.findAll('layer')
 '''
 for attr, value in soup.find('layer').attrs:
 	print attr, "       =          ", value '''
 namelist = []
 for layer in layers:
	soupname = BeautifulSoup(str(layer))
	names =  soupname.findAll('name')
	if len(names) > 0:
		namelist += names[0]
 return namelist
'''
f = open('wmsmaris.xml','r')
a=f.read()
print a
#parsexml(a) '''

def isServiceException(xml):
	print 'here'
	#print xml
	soup = BeautifulSoup(xml)
	#print soup
	exceptions = soup.findAll('ServiceException')
	#print exceptions
	exceptionList = []
	xmltext = str(xml)
	if(xmltext.count('ServiceException') > 0):
		return True
	else:
		return False
	print 'done'


   
def populateLayerTree(xml,LayerTree, layerTreeRoot):
	f = open('cacheGetCapabilities.xml','w')
	f.write(xml)
	f.close()
	
	f = open('cacheGetCapabilities.xml','r')
	xml = f.read()
	#print xml
	soup = BeautifulSoup(xml)
	dfs(soup,LayerTree, layerTreeRoot)
	
def dfs(root,LayerTree, ltr):
	if not hasattr(root, 'contents'):
		print root.string
		return
	else:
		id = ltr
		print root.name
		if(root.name == 'layer'):
			names = root.findAll('name')
			if(len(names)>0):
				id = LayerTree.AppendItem(ltr,names[0].string)
				print  names[0].string
		children = root.contents
		for child in children:
			dfs(child, LayerTree, id)
    		return

