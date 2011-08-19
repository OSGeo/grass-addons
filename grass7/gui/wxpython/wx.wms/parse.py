"""!
@package parse.py

@brief Python app for parsing the getCapabilties reponse, checking
service exception in the wms server reply and hierarchical display
of layers.

Functions:
 - parsexml
 - isValidResponse
 - isServiceException
 - populateLayerTree
 - dfs

(C) 2006-2011 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author: Maris Nartiss (maris.nartiss gmail.com)
@author Sudeep Singh Walia (Indian Institute of Technology, Kharagpur , sudeep495@gmail.com)
"""

from grass.script import core as grass
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
def isValidResponse(xml):
	soup = BeautifulSoup(xml)
	getCapabilities = soup.findAll('wmt_ms_capabilities')
	print 'heeeeeeeeereeeeee'
	print len(getCapabilities)
	if(len(getCapabilities)==0):
		print 'False'
		return False
	else:
		print 'True'
		return True
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
	TMP = grass.tempfile()
	if TMP is None:
		grass.fatal("Unable to create temporary files")
	print '########################'
	print TMP
	print '########################'
	f = open(TMP,'w')
	f.write(xml)
	f.close()
	
	f = open(TMP,'r')
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

