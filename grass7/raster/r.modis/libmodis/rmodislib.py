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
    def __init__(self,value = None):
        urlbase = 'e4ftl01u.ecs.nasa.gov'
        usrsnow = 'n4ftl01u.ecs.nasa.gov'
	self.prod = value
	self.products = {
          'lst_aqua_daily':{'url':urlbase,'folder':'MOLA/MYD11A1.005','res':1000, 
          'spec':'( 1 0 0 0 1 0 0 0 0 0 0 0 )','spec_qa':'( 0 1 0 0 0 1 0 0 0 0 0 0 )'},
          'lst_terra_daily':{'url':urlbase,'folder':'MOLT/MOD11A1.005','res':1000, 
          'spec':'( 1 0 0 0 1 0 0 0 0 0 0 0 )','spec_qa':'( 0 1 0 0 0 1 0 0 0 0 0 0 )'}, 
          'snow_terra_eight':{'url':usrsnow,'folder':'SAN/MOST/MOD10A2.005','res':500,
          'spec':'( 1 1 0 0 0 0 0 0 0 0 0 )','spec_qa':'( 0 0 0 0 0 0 0 0 0 0 0 )'}, 
          'ndvi_terra_sixte':{'url':urlbase, 'folder':'MOLT/MOD13Q1.005','res':250,
          'spec':'( 1 1 0 0 0 0 0 0 0 0 0 )','spec_qa':'( 0 0 1 1 0 0 0 0 0 0 0 )'}
        }

    def returned(self):
	return self.products[self.prod]

    def fromcode(self,code):
        import string
        for k,v in self.products.iteritems():
          if string.find(v['folder'],code) != -1:
            return self.products[k]
        return "The code insert is not supported yet. Can you ask to the dev "\
               + "mailing list for a support in the future"

    def __str__(self):
	prod = self.returned()
	string = "url: " + prod['url'] + ", folder: " + prod['folder'] + \
                ", spectral subset: " + prod['spec'] + ", spectral subset qa:" + \
                prod['spec_qa']
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
    def __init__(self,value):
        self.proj = value
        self.projections = {'latlong':'GEO', 'lcc':'LAMBERT CONFORMAL CONIC',
             'merc':'MERCARTOR', 'polar':'POLARSTEREOGRAFIC', 'utm':'UTM', 
             'tmerc':'TRANSFERT MERCARTOR'}

    def returned(self):
        return self.projections[self.proj]

class datum:
    """Definition of datum for convert from sinusoidal projection. Not all 
    datumare supported"""
    def __init__(self,value):
        self.datum = value
        self.datumlist = {'AGGIUNGERE':'AGGIUNGERE'}

    def returned(self):
        return self.datumlist[self.datum]
