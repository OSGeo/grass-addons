#!/usr/bin/env python
# -*- coding: utf-8
"""
@package mdgrass
@module  v.info.iso, r.info.iso, g.gui.metadata
@brief   Base class for import(r.info,v.info) and export(r/v.support)
         metadata with using OWSLib and jinja template.

Classes:
 - mdgrass::GrassMD

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.

@author Matej Krejci <matejkrejci gmail.com> (GSoC 2014)
"""
from owslib.iso import *
from jinja2 import Environment, FileSystemLoader

from lxml import etree
import os
import sys
import re
import StringIO
import subprocess as sub
import uuid
import mdutil  # metadata lib
import getpass  # whoami for linux and  ms-win

from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.gis import Mapset
from grass.pygrass import raster
from grass.pygrass.modules import Module
from grass.script import parse_key_val
from subprocess import PIPE
from datetime import date, datetime
from grass.script import parser
from grass.script import core as grass


class GrassMD():

    '''
    @var self.map:  name of choosen map by user
    @var self.type: typ of map representation(cell, vector, r3)
    @var md_grass:  dict with metadata from r.info v.info except for "r.info flag=h"

    '''

    def __init__(self, map, type):
        self.map = map
        self.type = type
        self.isMapExist()  # function to check if map exist
        self.md_grass = {}
        self.md_abstract = ''
        self.md_vinfo_h = ''  # v.info flag=h" - parse
        self.gisenv_grass = grass.gisenv()  # dict with gisenv information
        # suffix of output xml file (variables)
        self.schema_type = '_basic.xml'
        self.dirpath = os.path.join(os.getenv('GRASS_ADDON_BASE'), 'etc', 'wx.metadata')
        # metadata object from OWSLIB ( for define md values)
        self.md = MD_Metadata(md=None)
        self.template = None  # path to file with xml templates

        if self.type == "cell":
            self.parseRast()
        elif self.type == "vector":
            self.parseVect()
        elif self.type == "r3??":
            # TODO
            self.parseRast3D()

    def isMapExist(self):
        '''Check if the map is in current mapset'''
        self.mapset = grass.find_file(self.map, self.type)['mapset']
        if not self.mapset:
            grass.fatal(_("Map <%s> does not exist in current mapset") % self.map)

    def parseRast3D(self):
        pass

    def parseVect(self):
        '''Read metadata from v.info
        @var self.md_grass dictionary of metadata from v.info
        '''
        # parse md from v.info flags=-g -e -t
        vinfo = Module('v.info',
            self.map,
            flags='get',
            quiet=True,
            stdout_=PIPE)

        self.md_grass = parse_key_val(vinfo.outputs.stdout)

        # parse md from v.info flag=h (history of map in grass)
        rinfo_h = Module('v.info',
              self.map,
              flags='h',
              quiet=True,
              stdout_=PIPE)

        md_h_grass = rinfo_h.outputs.stdout
        buf = StringIO.StringIO(md_h_grass)
        line = buf.readline().splitlines()
        while str(line) != '[]':
            if str(line[0]).strip() != "":
                self.md_vinfo_h += line[0] + '\n'
            line = buf.readline().splitlines()
        buf.close()

        # convert GRASS parsed date format to iso format
        # if date format is diverse from standard, use them
        self._createISODate('source_date')

    def _createISODate(self, key):
        '''Function for converting GRASS-generated date to ISO format
           if the format of date is different from GRASS-generated format - use it and print warning
        '''
        try:
            date = datetime.strptime(self.md_grass[key], '%a %b %d %H:%M:%S %Y')
            self.md_grass['dateofcreation'] = date.strftime('%Y-%m-%d')
        except:
            grass.warning('date of creation: unknown date format')
            self.md_grass['dateofcreation'] = self.md_grass[key]

    def parseRast(self):
        '''Read metadata from r.info
        #self.md_grass       dictionary of metadata from v.info
        #self.md_abstract    string created by merge information from 'description' and 'source'
        '''
        rinfo = Module('r.info',
                       self.map,
                       flags='gre',
                       quiet=True,
                       stdout_=PIPE)

        self.md_grass = parse_key_val(rinfo.outputs.stdout)

        # convert date to ISO format
        self._createISODate('date')

        # create abstract
        if self.md_grass['description'] != '""':
            self.md_abstract = self.md_grass['description'] + '; '
        if self.md_grass['source1'] != '""':
            self.md_abstract += self.md_grass['source1'] + '; '
        if self.md_grass['source2'] != '""':
            self.md_abstract += self.md_grass['source2'] + '; '
        self.md_abstract += 'Total cells: ' + self.md_grass['cells'] + '; '
        self.md_abstract += 'A range of values: min: ' + \
            self.md_grass['min'] + '  max: ' + self.md_grass['max']
        self.md_abstract.translate(None, """&<>"'""")

    def createGrassBasicISO(self, template=None):
        '''Create basic/essential profile based on ISO
        - unknown values are filling by n = '$NULL'
        '''
        try:
            self.md_grass['comments'] = self.md_grass['comments'].replace('\n', '; ')
        except:
            pass

        n = '$NULL'
        # jinja templates
        if template is None:
            self.template = os.path.join('templates', 'basicTemplate.xml')
        else:
            self.template = template

        # OWSLib md object
        self.md.identification = MD_DataIdentification()
        self.md.dataquality = DQ_DataQuality()
        self.md.distribution = MD_Distribution()
        self.md.identification.extent = EX_Extent()
        self.md.identification.extent.boundingBox = EX_GeographicBoundingBox()

        # Metadata on metadata
        val = CI_ResponsibleParty()
        val.organization = n
        val.email = n
        val.role = n
        self.md.contact.append(val)

        # Identification/Resource Title
        self.md.identification.title = mdutil.replaceXMLReservedChar(self.md_grass['title'])
        self.md.datestamp = mdutil.replaceXMLReservedChar(date.today().isoformat())

        # Identification/Resource Type
        self.md.identification.identtype = 'dataset'

        # Identification/Unique Resource Identifier
        self.md.identifier = mdutil.replaceXMLReservedChar(str(uuid.uuid4()))
        self.md.identification.uricode.append(n)
        self.md.identification.uricodespace.append(n)

        # Geographic/BB
        self.md.identification.extent.boundingBox.minx = mdutil.replaceXMLReservedChar(self.md_grass['north'])
        self.md.identification.extent.boundingBox.maxx = mdutil.replaceXMLReservedChar(self.md_grass['south'])
        self.md.identification.extent.boundingBox.miny = mdutil.replaceXMLReservedChar(self.md_grass['east'])
        self.md.identification.extent.boundingBox.maxy = mdutil.replaceXMLReservedChar(self.md_grass['west'])

        # Conformity/Title
        self.md.dataquality.conformancetitle.append(
            'GRASS GIS basic metadata profile based on ISO 19115, 19139')

        # Conformity/Date:
        self.md.dataquality.conformancedate.append(mdutil.replaceXMLReservedChar(date.today().isoformat()))
        self.md.dataquality.conformancedatetype.append('publication')

        # Temporal/Date of creation
        val = CI_Date()
        val.date = self.md_grass['dateofcreation']
        val.type = 'creation'
        self.md.identification.date.append(val)

        self.md.identification.uom.append('m')  # TODO

        # different metadata sources for vector and raster
        if self.type == 'cell':
            # Identification/Resource Abstract
            self.md.identification.abstract = mdutil.replaceXMLReservedChar(self.md_abstract)
            # Geographic/resolution
            self.md.identification.distance.append(mdutil.replaceXMLReservedChar(self.md_grass['nsres']))  # TODO for discuss

            # Quality/Lineage
            try:
                self.md.dataquality.lineage = mdutil.replaceXMLReservedChar(self.md_grass['comments']).replace('\n', '\\n')
            except:
                grass.warning('Native metadata *flag=comments* not found, dataquality.lineage filled by $NULL')
                self.md.dataquality.lineage = n

            self.md.identification.denominators.append(n)
            # Organisation/Responsible Party:
            val = CI_ResponsibleParty()
            val.organization = n  # self.md_grass['creator']
            val.role = n
            val.email = n
            self.md.identification.contact.append(val)

        if self.type == 'vector':

            # Identification/Resource Abstract
            # TODO not enough sources for create abstarce
            self.md.identification.abstract = mdutil.replaceXMLReservedChar(self.md_grass['name'])
            self.md.dataquality.lineage = mdutil.replaceXMLReservedChar(self.md_vinfo_h).replace('\n', '\\n')

            self.md.identification.denominators.append(self.md_grass['scale'])
            # Organisation/Responsible Party:
            val = CI_ResponsibleParty()
            val.organization = n  # mdutil.replaceXMLReservedChar(getpass.getuser())
            val.email = n
            val.role = n
            self.md.identification.contact.append(val)

        self.templatePathAbs = os.path.join(self.dirpath, self.template)

    def createGrassInspireISO(self, template=None):
        '''Create valid INSPIRE profile and fill it as much as possible by GRASS metadata. Missing values is $NULL
        -create basic md profile and add INSPIRE mandatory attributes
        '''

        self.schema_type = '_inspire.xml'

        # create basic profile
        self.createGrassBasicISO()

        if template is None:
            self.template = os.path.join('templates',  'inspireTemplate.xml')
        else:
            self.template = template

        n = '$NULL'

        if len(self.md.identification.distance) == 0:
            self.md.identification.distance.append(n)  # TODO
        # Classification/Topic Category
        self.md.identification.topiccategory.append(n)
        self.md.identification.resourcelanguage.append(n)
        self.md.languagecode = n
        # Keyword/Keyword
        kw = {}
        kw['keywords'] = []
        kw['keywords'].append(n)

        kw['type'] = n
        kw['thesaurus'] = {}
        kw['thesaurus']['date'] = n
        kw['thesaurus']['datetype'] = n
        kw['thesaurus']['title'] = n
        self.md.identification.keywords.append(kw)

        # Conformity/Title
        # remove value from basic profile
        self.md.dataquality.conformancetitle.pop()
        self.md.dataquality.conformancetitle.append(
            'Commission Regulation (EU) No 1089/2010 of 23 November 2010 implementing Directive 2007/2/EC of the European Parliament and of the Council as regards interoperability of spatial data sets and services')
        # Identification/Resource Locator
        val = CI_OnlineResource()
        val.url = n
        self.md.distribution.online.append(val)

        # Conformity/Date
        self.md.dataquality.conformancedate.append(n)
        self.md.dataquality.conformancedatetype.append(n)

        # Conformity/Degree
        self.md.dataquality.conformancedegree.append('true')

        # Constraints/Limitations on public access
        self.md.identification.accessconstraints.append(n)
        self.md.identification.otherconstraints.append(n)

        # Constraints/Conditions for access and use-general
        self.md.identification.uselimitation.append(n)

        # Temporal/Temporal Extent
        self.md.identification.temporalextent_start = n
        self.md.identification.temporalextent_end = n

        self.templatePathAbs = os.path.join(self.dirpath, self.template)
        # print self.templatePathAbs

    def readXML(self, xml_file):
        '''create instance of metadata(owslib) from xml file'''
        self.md = MD_Metadata(etree.parse(xml_file))

    def saveXML(self, path=None, xml_out_name=None, wxparent=None, overwrite=False):
        ''' Save init. record  of OWSLib objects to ISO XML file'''

        # if  output file name is None, use map name and add suffix
        if xml_out_name is None:
            xml_out_name = self.type + '_' + str(self.map).partition('@')[0]  # + self.schema_type
        if not xml_out_name.lower().endswith('.xml'):
            xml_out_name += '.xml'

        if not path:
            path = os.path.join(mdutil.pathToMapset(), 'metadata')
            if not os.path.exists(path):
                print os.makedirs(path)
        path = os.path.join(path, xml_out_name)

        # generate xml using jinja templates
        env = Environment(loader=FileSystemLoader(self.dirpath))
        env.globals.update(zip=zip)
        template = env.get_template(self.template)
        iso_xml = template.render(md=self.md)

        # write xml to flat file
        if wxparent != None:
            if os.path.isfile(path):
                if mdutil.yesNo(wxparent, 'Metadata file exists. Do you want to overwrite file: %s?' % path, 'Overwrite dialog'):
                    try:
                        xml_file = open(path, "w")
                        xml_file.write(iso_xml)
                        xml_file.close()
                        Module('g.message', message='metadata exported: \n\
                                                     %s' % (str(path)))
                    except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                        grass.fatal('ERROR: cannot write xml to file')
                return path
            else:
                try:
                    xml_file = open(path, "w")
                    xml_file.write(iso_xml)
                    xml_file.close()
                    Module('g.message', message='metadata exported: \n\
                                                     %s' % (str(path)))
                except IOError as e:
                    print "I/O error({0}): {1}".format(e.errno, e.strerror)
                    grass.fatal('ERROR: cannot write xml to file')
                    # sys.exit()
                return path
        else:
            if os.path.isfile(path):
                Module('g.message', message='Metadata file exists: %s' % path)
                if overwrite:
                    try:
                        xml_file = open(path, "w")
                        xml_file.write(iso_xml)
                        xml_file.close()
                        Module('g.message', message='Metadata file has been overwritten')
                    except IOError as e:
                        print "I/O error({0}): {1}".format(e.errno, e.strerror)
                        grass.fatal('error: cannot write xml to file')
                        # sys.exit()
                    return path
                else:
                    # TODO --o??
                    Module('g.message', message='For overwriting use flag -o')
                    return False

    def validate_inspire(self):
        return mdutil.isnpireValidator(self.md)

    def validate_basic(self):
        return mdutil.grassProfileValidator(self.md)

    def updateGrassMd(self, md):
        '''
        Update some parameters in r/v.support. This part need revision #TODO
        '''
        if self.type == "vector":

            if len(md.contact) > 0:
                _org = ''
                for co in md.contact:
                    if co.organization != '':
                        _org += co.organization + ', '
                    if co.email != '':
                        _org += co.email + ', '
                    if co.role != '':
                        _org += co.role + '; '

                Module('v.support',
                       map=self.map,
                       organization=_org,
                       flags='r')

            if md.identification.date is not None:
                if len(md.identification.date) > 0:
                    for d in md.identification.date:
                        if d.type == 'creation':
                            _date = d.date

                    Module('v.support',
                           map=self.map,
                           date=_date,
                           flags='r')

            if md.identification.contact is not None:
                if len(md.identification.contact) > 0:
                    _person = md.identification.contact.organization.pop()

                    Module('v.support',
                           map=self.map,
                           person=_person,
                           flags='r')

            if md.identification.title is not (None or ''):
                _name = md.identification.title
                Module('v.support',
                       map=self.map,
                       map_name=_name,
                       flags='r')

            if len(md.identification.denominators) > 0:
                _scale = md.identification.denominators.pop()
                try:
                    _scale = int(_scale)
                    Module('v.support',
                           map=self.map,
                           scale=_scale,
                           flags='r')
                except:
                    pass

            if md.identification.keywords is not None or len(md.identification.keywords) > 0:
                _comments = ''
                for k in md.identification.keywords:
                    for kw in k["keywords"]:
                        if kw != '':
                            _comments += kw + ', '
                    if k["thesaurus"]["title"] != '':
                        _comments += k["thesaurus"]["title"] + ', '
                    if k["thesaurus"]["date"] != '':
                        _comments += k["thesaurus"]["date"] + ', '
                    if k['thesaurus']['datetype'] != '':
                        _comments += k['thesaurus']['datetype'] + ';'

                Module('v.support',
                       map=self.map,
                       comment=_comments,
                       flags='r')

#------------------------------------------------------------------------ RASTER
        if self.type == "cell":

            if md.identification.title is not (None or ''):
                _title = md.identification.title
                Module('r.support',
                       map=self.map,
                       title=_title,
                       overwrite=True)

            if md.dataquality.lineage is not (None or ''):
                _history = md.dataquality.lineage
                Module('r.support',
                       map=self.map,  # append
                       history=_history)

            _units = ''
            if len(md.identification.distance) > 0:
                _units += md.identification.distance.pop()
            if len(md.identification.uom) > 0:
                _units += md.identification.uom.pop()
            if _units != '':
                Module('r.support',
                       map=self.map,
                       units=_units,
                       overwrite=True)

            if md.identification.keywords is not None or len(md.identification.keywords) > 0:
                _comments = self.md_grass['description']
                for k in md.identification.keywords:
                    for kw in k["keywords"]:
                        if kw != '':
                            _comments += kw + ', '
                    if k["thesaurus"]["title"] != '':
                        _comments += k["thesaurus"]["title"] + ', '
                    if k["thesaurus"]["date"] != '':
                        _comments += k["thesaurus"]["date"] + ', '
                    if k['thesaurus']['datetype'] != '':
                        _comments += k['thesaurus']['datetype'] + ';'

                Module('r.support',
                       map=self.map,
                       description=_comments,
                       overwrite=True)
