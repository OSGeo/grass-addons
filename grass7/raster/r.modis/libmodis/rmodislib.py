#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:	r.modis
# AUTHOR(S):	Luca Delucchi
# PURPOSE:	Here there are some important class to run r.modis modules
#
#
# COPYRIGHT:	(C) 2011 by Luca Delucchi
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

class product:
    """Definition of modis product with url and path in the ftp server
    """
    def __init__(self,value):
        urlbase = 'e4ftl01u.ecs.nasa.gov'
        usrsnow = 'n4ftl01u.ecs.nasa.gov'
	self.prod = value
	self.products = {'lst_aqua_daily':{'url':urlbase,
	  'folder':'MOLA/MYD11A1.005'},'lst_terra_daily':{'url':urlbase,
	  'folder':'MOLT/MOD11A1.005'},'snow_terra_eight':{'url':usrsnow,
	  'folder':'SAN/MOST/MOD10A2.005'}, 'ndvi_terra_sixte':{'url':urlbase,
          'folder':'MOLT/MOD13Q1.005'} }

    def returned(self):
	return self.products[self.prod]

    def __str__(self):
	prod = self.returned()
	string = "url: " + prod['url'] + ", folder: " + prod['folder']
	return string

class resampling:
    """Return the resampling value from the code used in the modules
    """
    def __init__(self,value):
        self.code = value
        self.resampling = {'NN': 'NEAREST_NEIGHBOR','BI' : 'BICUBIC',
        'CC' : '','NONE' : 'NONE'}

    def returned(self):
        return self.resampling[self.code]

class projection:
    """Definition of projection for convert from sinusoidal projection to
    another one. Not all projection systems are supported"""
