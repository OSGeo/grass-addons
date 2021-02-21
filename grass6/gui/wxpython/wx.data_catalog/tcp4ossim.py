#!/usr/bin/env python
import socket
from xml.dom import minidom
import os
import sys

apppath = os.path.abspath(os.path.dirname(sys.argv[0]))
configfile = '%s/conf.xml' % (apppath)

def parseTCPconf():
    xmldoc = minidom.parse(configfile)
    tcpconf = {}
    planetsashaconf = xmldoc.firstChild
    if planetsashaconf.childNodes[1].childNodes[1].firstChild is not None:
        tcpconf['tcpHost'] = planetsashaconf.childNodes[1].childNodes[1].firstChild.data
    else :
        print 'tcpHost not found'
        tcpconf['tcpHost'] = 'None'

    if planetsashaconf.childNodes[1].childNodes[3].firstChild is not None:
        tcpconf['tcpDport'] = planetsashaconf.childNodes[1].childNodes[3].firstChild.data
    else :
        print 'tcpDport not found'
        tcpconf['tcpDport'] = 'None'

    if planetsashaconf.childNodes[1].childNodes[5].firstChild is not None:
        tcpconf['tcpPport'] = planetsashaconf.childNodes[1].childNodes[5].firstChild.data
    else :
        print 'tcpPport not found'
        tcpconf['tcpPport'] = 'None'

    return tcpconf	


def setparamconnection():
    try :
        conf = parseTCPconf()
        host = conf['tcpHost']
        nav = conf['tcpPport']
        data = conf['tcpDport']
        return host, nav, data
    except :
        print 'Use preference Panel to set preference'


def addfile(output):
    host = setparamconnection()[0]
    dport = setparamconnection()[2]
    ossim_data_xml = "<Add target=':idolbridge'><Image groupType='groundTexture'><filename>%s</filename> <id>%s</id><name>%s</name></Image></Add>" % (output,output,output)
    ossimdata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ossimdata.connect((host, int(dport)))
    try :
        ossimdata.send(ossim_data_xml)
        ossimdata.close()
    except :
        print "Connection error"


def zoomto(lon,lat,distance):
    host = setparamconnection()[0]
    pport = setparamconnection()[1]
    ossim_zoom_xml = '<Set target=":navigator" vref="wgs84"><Camera><longitude>%s</longitude><latitude>%s</latitude><altitude>%s</altitude><heading>0</heading><pitch>0</pitch><roll>0</roll><altitudeMode>absolute</altitudeMode><range>%s</range></Camera></Set>' % (lon, lat, distance, distance)
    ossimposition = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try :
        ossimposition.connect((host, int(pport)))  
        ossimposition.send(ossim_zoom_xml)
        ossimposition.close()
    except :
        print "Connection error"


def removefile(output):
    host = setparamconnection()[0]
    dport = setparamconnection()[2]
    ossimdata = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ossimdata.connect((host, int(dport)))
    ossim_data_xml = "<Remove target=':idolbridge' id='%s' />" % (output)
    try :
        ossimdata.send(ossim_data_xml)
        ossimdata.close()
    except :
        print 'Connection error'


def addzoom(output,lon,lat,distance):
    addfile(output)
    zoomto(lon,lat,distance)


#addzoom('/Users/sasha/Desktop/rgb.tif',-81.0009,29.0009,15000)
#removefile('/data/florida/Brevard.tif','localhost',8000)
