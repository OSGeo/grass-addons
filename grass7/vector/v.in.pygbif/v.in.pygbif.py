#!/usr/bin/env python

"""
MODULE:    v.in.pygbif

AUTHOR(S): Stefan Blumentrath < stefan.blumentrath AT nina.no>
           Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Search and import GBIF species distribution data directly from
           GBIF API using pygbif

COPYRIGHT: (C) 2016 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

"""
To Dos:
- use proper cleanup routine, esp if using csv + vrt (copy from other modules)
- handle layers in mask input
- add progress bar

"""

#%module
#% description: Search and import GBIF species distribution data
#% keyword: vector
#% keyword: geometry
#%end

#%option G_OPT_V_OUTPUT
#% key: output
#% description: Name of resulting vector map with occurrences
#% required : yes
#%end

#%option
#% key: taxa
#% description: Comma separated list of taxon names or keys to fetch data for
#% required : yes
#%end

#%option G_OPT_V_INPUT
#% key: mask
#% description: Vector map that delimits region of interest
#% guisection: Spatial filter
#% required: no
#%end

#%option
#% key: date_from
#% type: string
#% description: Lower bound of acceptable dates (format: yyyy, yyyy-MM, yyyy-MM-dd, or MM-dd)
#% guisection: Temporal filter
#% required: no
#%end

#%option
#% key: date_to
#% type: string
#% description:  Upper bound of acceptable dates (format: yyyy, yyyy-MM, yyyy-MM-dd, or MM-dd)
#% guisection: Temporal filter
#% required: no
#%end

# Import will allways be limited to current region except for latlon locations
#%flag
#% key: b
#% description: Do not build topology
#%end

#%flag
#% key: r
#% description: Do not limit import to current region (works only in lat/lon)
#% guisection: Spatial filter
#%end

#%flag
#% key: p
#% description: Print result from matching taxa names and exit
#% guisection: Print
#% suppress_required: yes
#%end

#%flag
#% key: i
#% description: Produce individual map for each taxon
#%end

#%flag
#% key: g
#% description: Print result from matching taxon names in shell script style and exit
#% guisection: Print
#% suppress_required: yes
#%end

#%flag
#% key: o
#% description: Print number of matching occurrences per taxon and exit
#% guisection: Print
#% suppress_required: yes
#%end

#%flag
#% key: t
#% description: Print result of taxon matching in table format and exit
#% guisection: Print
#% suppress_required: yes
#%end

#%option
#% key: basisofrecord
#% type: string
#% description: Accepted basis of records
#% guisection: Context filter
#% required: no
#% multiple: no
#% options: ALL,FOSSIL_SPECIMEN,HUMAN_OBSERVATION,LITERATURE,LIVING_SPECIMEN,MACHINE_OBSERVATION,OBSERVATION,PRESERVED_SPECIMEN,UNKNOWN
#% answer: ALL
#%end

#%option
#% key: rank
#% type: string
#% description: Rank of the taxon to search for
#% guisection: Context filter
#% required: yes
#% multiple: no
#% options: class,cultivar,cultivar_group,domain,family,form,genus,informal,infrageneric_name,infraorder,infraspecific_name,infrasubspecific_name,kingdom,order,phylum,section,series,species,strain,subclass,subfamily,subform,subgenus,subkingdom,suborder,subphylum,subsection,subseries,subspecies,subtribe,subvariety,superclass,superfamily,superorder,superphylum,suprageneric_name,tribe,unranked,variety
#% answer: species
#%end

#%option
#% key: recordedby
#% type: string
#% description: The person who recorded the occurrence.
#% guisection: Context filter
#%end

#%option
#% key: institutioncode
#% type: string
#% description: An identifier of any form assigned by the source to identify the institution the record belongs to.
#% guisection: Context filter
#%end

#%option
#% key: country
#% type: string
#% description: The 2-letter country code (as per ISO-3166-1) of the country in which the occurrence was recorded
#% guisection: Spatial filter
#%end

#%option
#% key: continent
#% type: string
#% description: The continent in which the occurrence was recorded
#% guisection: Spatial filter
#% options: africa, antarctica, asia, europe, north_america, oceania, south_america
#%end

#%flag
#% key: n
#% description: Do not limit search to records with coordinates
#% guisection: Spatial filter
#%end

#%flag
#% key: s
#% description: Do also import occurrences with spatial issues
#% guisection: Spatial filter
#%end

import sys
import os
import math
from osgeo import ogr
from osgeo import osr
import grass.script as grass
from grass.pygrass.vector import Vector
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point
from dateutil.parser import parse

if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

try:
    from pygbif import occurrences
    from pygbif import species
except ImportError:
    grass.fatal(_("Cannot import pygbif (https://github.com/sckott/pygbif)"
                  " library."
                  " Please install it (pip install pygbif)"
                  " or ensure that it is on path"
                  " (use PYTHONPATH variable)."))

def set_output_encoding(encoding='utf-8'):
    import sys
    import codecs
    '''When piping to the terminal, python knows the encoding needed, and
       sets it automatically. But when piping to another program (for example,
       | less), python can not check the output encoding. In that case, it 
       is None. What I am doing here is to catch this situation for both 
       stdout and stderr and force the encoding'''
    current = sys.stdout.encoding
    if current is None :
        sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    current = sys.stderr.encoding
    if current is None :
        sys.stderr = codecs.getwriter(encoding)(sys.stderr)

def main():

    # Parse input options
    output = options['output']
    mask = options['mask']
    species_maps = flags['i']
    no_region_limit = flags['r']
    no_topo = flags['b']
    print_species = flags['p']
    print_species_table = flags['t']
    print_species_shell = flags['g']
    print_occ_number = flags['o']
    allow_no_geom = flags['n']
    hasGeoIssue = flags['s']
    taxa_list = options['taxa'].split(',')
    institutionCode = options['institutioncode']
    basisofrecord = options['basisofrecord']
    recordedby = options['recordedby'].split(',')
    date_from = options['date_from']
    date_to = options['date_to']
    country = options['country']
    continent = options['continent']
    rank = options['rank']

    # Define static variable
    # Number of occurrences to fetch in one request
    chunk_size = 300
    # lat/lon proj string
    latlon_crs = ['+proj=longlat +no_defs +a=6378137 +rf=298.257223563 +towgs84=0.000,0.000,0.000',
              '+proj=longlat +no_defs +a=6378137 +rf=298.257223563 +towgs84=0,0,0,0,0,0,0']
    # List attributes available in Darwin Core
    # not all attributes are returned in each request
    # to avoid key errors when accessing the dictionary returned by pygbif
    # presence of DWC keys in the returned dictionary is checked using this list
    # The number of keys in this list has to be equal to the number of columns
    # in the attribute table and the attributes written for each occurrence
    dwc_keys = ['key', 'taxonRank', 'taxonKey', 'taxonID', 'scientificName',
                'species', 'speciesKey', 'genericName', 'genus', 'genusKey',
                'family', 'familyKey', 'order', 'orderKey', 'class',
                'classKey', 'phylum', 'phylumKey', 'kingdom', 'kingdomKey',
                'eventDate', 'verbatimEventDate', 'startDayOfYear',
                'endDayOfYear', 'year', 'month', 'day', 'occurrenceID',
                'occurrenceStatus', 'occurrenceRemarks', 'Habitat',
                'basisOfRecord', 'preparations', 'sex', 'type', 'locality',
                'verbatimLocality', 'decimalLongitude', 'decimalLatitude',
                'geodeticDatum', 'higerGeography', 'continent', 'country',
                'countryCode', 'stateProvince', 'gbifID', 'protocol',
                'identifier', 'recordedBy', 'identificationID', 'identifiers',
                'dateIdentified', 'modified', 'institutionCode',
                'lastInterpreted', 'lastParsed', 'references', 'relations',
                'catalogNumber', 'occurrenceDetails', 'datasetKey',
                'datasetName', 'collectionCode', 'rights', 'rightsHolder',
                'license', 'publishingOrgKey', 'publishingCountry',
                'lastCrawled', 'specificEpithet', 'facts', 'issues',
                'extensions', 'language']
    # Deinfe columns for attribute table
    cols = [(u'cat',       'INTEGER PRIMARY KEY'),
            (u'g_search',       'varchar(100)'),
            (u'g_key',       'integer'),
            (u'g_taxonrank',       'varchar(50)'),
            (u'g_taxonkey',       'integer'),
            (u'g_taxonid',       'varchar(50)'),
            (u'g_scientificname',       'varchar(255)'),
            (u'g_species',       'varchar(255)'),
            (u'g_specieskey',       'integer'),
            (u'g_genericname',       'varchar(255)'),
            (u'g_genus',       'varchar(50)'),
            (u'g_genuskey',       'integer'),
            (u'g_family',       'varchar(50)'),
            (u'g_familykey',       'integer'),
            (u'g_order',       'varchar(50)'),
            (u'g_orderkey',       'integer'),
            (u'g_class',       'varchar(50)'),
            (u'g_classkey',       'integer'),
            (u'g_phylum',       'varchar(50)'),
            (u'g_phylumkey',       'integer'),
            (u'g_kingdom',       'varchar(50)'),
            (u'g_kingdomkey',       'integer'),
            (u'g_eventdate',       'text'),
            (u'g_verbatimeventdate',       'varchar(50)'),
            (u'g_startDayOfYear',       'integer'),
            (u'g_endDayOfYear',       'integer'),
            (u'g_year',       'integer'),
            (u'g_month',       'integer'),
            (u'g_day',       'integer'),
            (u'g_occurrenceid',       'varchar(255)'),
            (u'g_occurrenceStatus',       'varchar(50)'),
            (u'g_occurrenceRemarks',       'varchar(50)'),
            (u'g_Habitat',       'varchar(50)'),
            (u'g_basisofrecord',       'varchar(50)'),
            (u'g_preparations',       'varchar(50)'),
            (u'g_sex',       'varchar(50)'),
            (u'g_type',       'varchar(50)'),
            (u'g_locality',       'varchar(255)'),
            (u'g_verbatimlocality',       'varchar(255)'),
            (u'g_decimallongitude',       'double precision'),
            (u'g_decimallatitude',       'double precision'),
            (u'g_geodeticdatum',       'varchar(50)'),
            (u'g_higerGeography',       'varchar(255)'),
            (u'g_continent',       'varchar(50)'),
            (u'g_country',       'varchar(50)'),
            (u'g_countryCode',       'varchar(50)'),
            (u'g_stateProvince',       'varchar(50)'),
            (u'g_gbifid',       'varchar(255)'),
            (u'g_protocol',       'varchar(255)'),
            (u'g_identifier',       'varchar(50)'),
            (u'g_recordedby',       'varchar(255)'),
            (u'g_identificationid',       'varchar(255)'),
            (u'g_identifiers',       'text'),
            (u'g_dateidentified',       'text'),
            (u'g_modified',       'text'),
            (u'g_institutioncode',       'varchar(50)'),
            (u'g_lastinterpreted',       'text'),
            (u'g_lastparsed',       'text'),
            (u'g_references',       'varchar(255)'),
            (u'g_relations',       'text'),
            (u'g_catalognumber',       'varchar(50)'),
            (u'g_occurrencedetails',       'text'),
            (u'g_datasetkey',       'varchar(50)'),
            (u'g_datasetname',       'varchar(255)'),
            (u'g_collectioncode',       'varchar(50)'),
            (u'g_rights',       'varchar(255)'),
            (u'g_rightsholder',       'varchar(255)'),
            (u'g_license',       'varchar(50)'),
            (u'g_publishingorgkey',       'varchar(50)'),
            (u'g_publishingcountry',       'varchar(50)'),
            (u'g_lastcrawled',       'text'),
            (u'g_specificepithet',       'varchar(50)'),
            (u'g_facts',       'text'),
            (u'g_issues',       'text'),
            (u'g_extensions',       'text'),
            (u'g_language',       'varchar(50)')]

    set_output_encoding()
    # Set temporal filter if requested by user
    # Initialize eventDate filter
    eventDate = None
    # Check if date from is compatible (ISO compliant)
    if date_from:
        try:
            parse(date_from)
        except:
            grass.fatal("Invalid invalid start date provided")

        if date_from and not date_to:
            eventDate = '{}'.format(date_from)
    # Check if date to is compatible (ISO compliant)
    if date_to:
        try:
            parse(date_to)
        except:
            grass.fatal("Invalid invalid end date provided")
        # Check if date to is after date_from
        if parse(date_from) < parse(date_to):
            eventDate = '{},{}'.format(date_from, date_to)
        else:
            grass.fatal("Invalid date range: End date has to be after start date!")
    # Set filter on basisOfRecord if requested by user
    if basisofrecord == 'ALL':
        basisOfRecord = None
    else:
        basisOfRecord = basisofrecord
    # Allow also occurrences with spatial issues if requested by user
    hasGeospatialIssue = False
    if hasGeoIssue:
        hasGeospatialIssue = True
    # Allow also occurrences without coordinates if requested by user
    hasCoordinate = True
    if allow_no_geom:
        hasCoordinate = False

    # Set reprojection parameters
    # Set target projection of current LOCATION
    target_crs = grass.read_command('g.proj', flags='fj').rstrip(os.linesep)
    target = osr.SpatialReference(target_crs)
    target.ImportFromProj4(target_crs)
    if target == 'XY location (unprojected)':
        grass.fatal("Sorry, XY locations are not supported!")

    # Set source projection from GBIF
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    if target_crs not in latlon_crs:
        transform = osr.CoordinateTransformation(source, target)
        reverse_transform = osr.CoordinateTransformation(target, source)

    # Generate WKT polygon to use for spatial filtering if requested
    if mask:
        if len(mask.split('@')) == 2:
            m = VectorTopo(mask.split('@')[0], mapset=mask.split('@')[1])
        else:
            m = VectorTopo(mask)
        if not m.exist():
            grass.fatal('Could not find vector map <{}>'.format(mask))
        m.open('r')
        if not m.is_open():
            grass.fatal('Could not open vector map <{}>'.format(mask))

        # Use map Bbox as spatial filter if map contains <> 1 area
        if m.number_of('areas') == 1:
            region_pol = str(m.read(1)).replace('LINESTRING', 'POLYGON(') + ')'
        else:
            bbox = str(m.bbox()).replace('Bbox(', '').replace(' ', '').rstrip(')').split(',')
            region_pol = 'POLYGON(({0} {1}, {0} {3}, {2} {3}, {2} {1}, {0} {1}))'.format(bbox[2],
                         bbox[0], bbox[3], bbox[1])
        m.close()
    else:
        # Do not limit import spatially if LOCATION is able to take global data
        if no_region_limit:
            if target_crs not in latlon_crs:
                grass.fatal('Import of data from outside the current region is'
                            'only supported in a WGS84 location!')
            region_pol = None
        else:
            # Limit import spatially to current region
            # if LOCATION is !NOT! able to take global data
            # to avoid pprojection ERRORS
            region = grass.parse_command('g.region', flags='g')
            region_pol = 'POLYGON(({0} {1}, {0} {3}, {2} {3}, {2} {1}, {0} {1}))'.format(region['e'],
                         region['n'], region['w'], region['s'])

    # Do not reproject in latlon LOCATIONS
    if target_crs not in latlon_crs:
        pol = ogr.CreateGeometryFromWkt(region_pol)
        pol.Transform(reverse_transform)
        pol = pol.ExportToWkt()
    else:
        pol = region_pol

    # Create output map if not output maps for each species are requested
    if not species_maps and not print_species and not print_species_shell and not print_occ_number and not print_species_table:
        mapname = output
        new = Vector(mapname)
        new.open('w', tab_name=mapname, tab_cols=cols)
        cat = 1

    # Import data for each species
    for s in taxa_list:
        # Get the taxon key if not the taxon key is provided as input
        try:
            key = int(s)
        except:
            try:
                species_match = species.name_backbone(s, rank=rank,
                                                      strict=False,
                                                      verbose=True)
                key = species_match['usageKey']
            except:
                grass.error('Data request for taxon {} failed. Are you online?'.format(s))
                continue

        # Return matching taxon and alternatives and exit
        if print_species:
            print u'Matching taxon for {} is:'.format(s)
            print u'{} {}'.format(species_match['scientificName'], species_match['status'])
            if 'alternatives' in species_match.keys():
                print 'Alternative matches might be:'.format(s)
                for m in species_match['alternatives']:
                    print u'{} {}'.format(m['scientificName'], m['status'])
            else:
                print 'No alternatives found for the given taxon'
            continue
        if print_species_shell:
            print u'match={}'.format(species_match['scientificName'])
            if 'alternatives' in species_match.keys():
                alternatives = []
                for m in species_match['alternatives']:
                    alternatives.append(m['scientificName'])
                print u'alternatives={}'.format(u','.join(alternatives))
            continue
        if print_species_table:
            if 'alternatives' in species_match.keys():
                if len(species_match['alternatives']) == 0:
                    print u'{0}|{1}|{2}|'.format(s, key, species_match['scientificName'])
                else:
                    alternatives = []
                    for m in species_match['alternatives']:
                        alternatives.append(m['scientificName'])
                    print u'{0}|{1}|{2}|{3}'.format(s, key, species_match['scientificName'],
                                                    u','.join(alternatives))
            continue
        try:
            returns_n = occurrences.search(taxonKey=key,
                                           hasGeospatialIssue=hasGeospatialIssue,
                                           hasCoordinate=hasCoordinate,
                                           institutionCode=institutionCode,
                                           basisOfRecord=basisOfRecord,
                                           recordedBy=recordedby,
                                           eventDate=eventDate,
                                           continent=continent,
                                           country=country,
                                           geometry=pol,
                                           limit=1)['count']
        except:
            grass.error('Data request for taxon {} faild. Are you online?'.format(s))
            returns_n = 0

        # Exit if search does not give a return
        # Print only number of returns for the given search and exit
        if print_occ_number:
            grass.message('Found {0} occurrences for taxon {1}...'.format(returns_n, s))
            continue
        elif returns_n <= 0:
            grass.warning('No occurrences for current search for taxon {0}...'.format(s))
            continue
        elif returns_n >= 200000:
            grass.warning('Your search for {1} returns {0} records.\n'
                          'Unfortunately, the GBIF search API is limited to 200,000 records per request.\n'
                           'The download will be incomplete. Please consider to split up your search.'.format(returns_n, s))

        # Get the number of chunks to download
        chunks = int(math.ceil(returns_n / float(chunk_size)))
        grass.verbose('Downloading {0} occurrences for taxon {1}...'.format(returns_n, s))

        # Create a map for each species if requested using map name as suffix
        if species_maps:
            mapname = '{}_{}'.format(s.replace(' ', '_'), output)

            new = Vector(mapname)
            new.open('w', tab_name=mapname, tab_cols=cols)
            cat = 1

        # Download the data from GBIF
        for c in range(chunks):
            # Define offset
            offset = c * chunk_size 
            # Adjust chunk_size to the hard limit of 200,000 records in GBIF API
            # if necessary
            if offset + chunk_size >= 200000:
                chunk_size = 200000 - offset
            # Get the returns for the next chunk
            returns = occurrences.search(taxonKey=key,
                                         hasGeospatialIssue=hasGeospatialIssue,
                                         hasCoordinate=hasCoordinate,
                                         institutionCode=institutionCode,
                                         basisOfRecord=basisOfRecord,
                                         recordedBy=recordedby,
                                         eventDate=eventDate,
                                         continent=continent,
                                         country=country,
                                         geometry=pol,
                                         limit=chunk_size,
                                         offset=offset)

            # Write the returned data to map and attribute table
            for res in returns['results']:
                if target_crs not in latlon_crs:
                    point = ogr.CreateGeometryFromWkt('POINT ({} {})'.format(res['decimalLongitude'], res['decimalLatitude']))
                    point.Transform(transform)
                    x = point.GetX()
                    y = point.GetY()
                else:
                    x = res['decimalLatitude']
                    y = res['decimalLongitude']

                point = Point(x, y)

                for k in dwc_keys:
                    if k not in res.keys():
                        res.update({k: None})

                new.write(point, attrs=(
                          res['key'],
                          u'{}'.format(s),
                          res['taxonRank'],
                          res['taxonKey'],
                          res['taxonID'],
                          res['scientificName'],
                          res['species'],
                          res['speciesKey'],
                          res['genericName'],
                          res['genus'],
                          res['genusKey'],
                          res['family'],
                          res['familyKey'],
                          res['order'],
                          res['orderKey'],
                          res['class'],
                          res['classKey'],
                          res['phylum'],
                          res['phylumKey'],
                          res['kingdom'],
                          res['kingdomKey'],
                          str(res['eventDate']),
                          str(res['verbatimEventDate']),
                          res['startDayOfYear'],
                          res['endDayOfYear'],
                          res['year'],
                          res['month'],
                          res['day'],
                          res['occurrenceID'],
                          res['occurrenceStatus'],
                          res['occurrenceRemarks'],
                          res['Habitat'],
                          res['basisOfRecord'],
                          res['preparations'],
                          res['sex'],
                          res['type'],
                          res['locality'],
                          res['verbatimLocality'],
                          res['decimalLongitude'],
                          res['decimalLatitude'],
                          res['geodeticDatum'],
                          res['higerGeography'],
                          res['continent'],
                          res['country'],
                          res['countryCode'],
                          res['stateProvince'],
                          res['gbifID'],
                          res['protocol'],
                          res['identifier'],
                          res['recordedBy'],
                          res['identificationID'],
                          u','.join(res['identifiers']),
                          str(res['dateIdentified']),
                          str(res['modified']),
                          res['institutionCode'],
                          str(res['lastInterpreted']),
                          str(res['lastParsed']),
                          res['references'],
                          u','.join(res['relations']),
                          res['catalogNumber'],
                          str(res['occurrenceDetails']),
                          res['datasetKey'],
                          res['datasetName'],
                          res['collectionCode'],
                          res['rights'],
                          res['rightsHolder'],
                          res['license'],
                          res['publishingOrgKey'],
                          res['publishingCountry'],
                          str(res['lastCrawled']),
                          res['specificEpithet'],
                          u','.join(res['facts']),
                          u','.join(res['issues']),
                          u','.join(res['extensions']),
                          res['language'],))

                cat = cat + 1

        # Close the current map if a map for each species is requested
        if species_maps:
            new.table.conn.commit()
            new.close()
            if not no_topo:
                grass.run_command('v.build', map=mapname, option='build')

    # Close the output map if not a map for each species is requested
    if not species_maps and not print_species and not print_species_shell and not print_occ_number and not print_species_table:
        new.table.conn.commit()
        new.close()
        if not no_topo:
            grass.run_command('v.build', map=mapname, option='build')

# Run the module
# ToDo: Add an atexit procedure which closes and removes the current map
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
