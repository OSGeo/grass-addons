#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat8.qc

 AUTHOR(S):    Stefan Blumentrath <stefan.blumentrath@nina.no>

 PURPOSE:      Reclass Landsat8 QA band according to acceptable pixel quality
               as defined by the user

 COPYRIGHT:    (C) 2016 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

#%Module
#% description: Reclass Landsat8 QA band according to acceptable pixel quality as defined by the user
#% keywords: imagery
#% keywords: qc
#% keywords: bitpattern
#% keywords: mask
#% keywords: landsat8
#%End

#%flag
#% key: i
#% description: Invert filter (default is set unacceptable pixels to NULL)
#%end

#%flag
#% key: p
#% guisection: Main
#% description: Print effect of bitpattern filter in number of pixels filtered and exit
#%end

#%option G_OPT_R_INPUT
#% guisection: Main
#% description: Landsat8 QA band
#% required : yes
#%end

#%option
#% key: designated_fill
#% multiple: No
#% description: Unacceptable conditions for Designated Fill (bit 0)
#% guisection: QA bit filter
#% options: No, Yes
#% required : no
#%end

#%option
#% key: dropped_frame
#% multiple: No
#% description: Unacceptable conditions for Dropped Frame (bit 1)
#% guisection: QA bit filter
#% options: No, Yes
#% required : no
#%end

#%option
#% key: terrain_occlusion
#% multiple: No
#% description: Unacceptable conditions for Terrain Occlusion (bit 2)
#% guisection: QA bit filter
#% options: No, Yes
#% required : no
#%end

##%option
##% key: reserved
##% multiple: No
##% description: Unacceptable conditions for Reserved (not currently used) (bit 3)
##% guisection: QA bit filter
##% options: No, Yes
##% required : no
##%end

#%option
#% key: water
#% multiple: yes
#% description: Unacceptable conditions for Water Confidence (bit 4-5)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cloud_shaddow
#% multiple: yes
#% description: Unacceptable conditions for Cloud Shaddow Confidence (bit 6-7)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: vegetation
#% multiple: yes
#% description: Unacceptable conditions for Vegetation Confidence (bit 8-9)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: snow_ice
#% multiple: yes
#% description: Unacceptable conditions for Snow/Ice Confidence (bit 10-11)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cirrus
#% multiple: yes
#% description: Unacceptable conditions for Cirrus Confidence (bit 12-13)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cloud
#% multiple: yes
#% description: Unacceptable conditions for Cloud Confidence (bit 14-15)
#% guisection: QA bit filter
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option G_OPT_R_OUTPUT
#% description: Name for output QA band filter
#% guisection: Main
#% required: no
#%end

#%rules
#% required: designated_fill,dropped_frame,terrain_occlusion,water,cloud_shaddow,vegetation,snow_ice,cirrus,cloud
#%end

import os
import sys
import grass.script as grass

if "GISBASE" not in os.environ:
    print "You must be in GRASS GIS to run this program."
    sys.exit(1)


def main():
    """
    Main program
    """

    # flags
    invert = flags['i']
    print_effect = flags['p']

    # Parse options
    input = options['input']
    output = options['output']

    # Define bitpattern filter (bf)
    bf = {'designated_fill': options['designated_fill'],
          'dropped_frame': options['dropped_frame'],
          'terrain_occlusion': options['terrain_occlusion'],
          # 'reserved': options[''],
          'water': options['water'],
          'cloud_shaddow': options['cloud_shaddow'],
          'vegetation': options['vegetation'],
          'snow_ice': options['snow_ice'],
          'cirrus': options['cirrus'],
          'cloud': options['cloud']}

    # Check if propper input is provided:
    if print_effect and output:
        grass.fatal("output option and p-flag are mutually exclusive")

    if print_effect and invert:
        grass.fatal("i-flag and p-flag are mutually exclusive")

    for o in ['water', 'cloud_shaddow', 'vegetation',
              'snow_ice', 'cirrus', 'cloud']:
        if len(bf[o].split(',')) >= 4 and not invert:
            grass.fatal("""All conditions for {} specified as 
            unacceptable, this will result in an empty map.""".format(o))
        if not bf[o] and invert:
            grass.fatal("""No conditions for {} selected for an
            invers filter, this will result in an empty map.""".format(o))

    # Define bitpattern characteristics according to
    # http://landsat.usgs.gov/qualityband.php
    """
    Currently populated bits:

    0     Designated Fill
    1     Dropped Frame
    2     Terrain Occlusion
    3     Reserved (not currently used)
    4-5     Water Confidence
    6-7     Reserved for cloud shaddow
    8-9     Vegetation confidence
    10-11     Snow/Ice confidence
    12-13     Cirrus confidence
    14-15     Cloud confidence
    """

    # Define bit length (single or double bits)
    bl = {'designated_fill': 1,
          'dropped_frame': 1,
          'terrain_occlusion': 1,
          # 'reserved': 1,
          'water': 2,
          'cloud_shaddow': 2,
          'vegetation': 2,
          'snow_ice': 2,
          'cirrus': 2,
          'cloud': 2}

    # Define bit position start
    bps = {
        'designated_fill': 0,
        'dropped_frame': 1,
        'terrain_occlusion': 2,
        # 'reserved': 3,
        'water': 4,
        'cloud_shaddow': 6,
        'vegetation': 8,
        'snow_ice': 10,
        'cirrus': 12,
        'cloud': 14}

    """
    For the single bits (0, 1, 2, and 3):
        0 = No, this condition does not exist
        1 = Yes, this condition exists.
    """

    # Define single bits dictionary
    single_bits = {'No': '0',
                   'Yes': '1'}

    """
The double bits (4-5, 6-7, 8-9, 10-11, 12-13, and 14-15), read from left to
right, represent levels of confidence that a condition exists:
00 = 'Not Determined' = Algorithm did not determine the status
                        of this condition
01 = 'No' = Algorithm has low to no confidence that this condition exists
            (0-33 percent confidence)
10 = 'Maybe' = Algorithm has medium confidence that this condition exists
               (34-66 percent confidence)
11 = 'Yes' = Algorithm has high confidence that this condition exists
             (67-100 percent confidence).
    """

    # Define double bits dictionary
    double_bits = {'Not Determined': '00',
                   'No': '01',
                   'Maybe': '10',
                   'Yes': '11'}

    # Get categories and number of pixels from QA band raster
    qa_cats = grass.parse_command('r.stats', flags='cn', input=input).keys()

    # Initialise string for reclass rules
    rc = ''

    # Initialise dictionary for printing the effect of the different bitpattern
    if print_effect:
        pe = {}

    # Loop over category values present in the QA band (qa_cats)
    for line in qa_cats:
        cat, pixels = line.split(' ')
        # Convert integer categories into bitpattern
        bin_cat = '{0:016b}'.format(int(cat))

        # Loop over the bitpattern filter (bf) elements defined by the user
        for k in bf.keys():
            # Only work on bits included in the user`s bitpattern filter (bf)
            if bf[k]:
                # Calculate bit positions end (bpe)
                bpe = bps[k] + bl[k]
                # Extract unnacceptable bitpatterns (bp) form bitpattern filter
                for bp in bf[k].split(','):
                    if bl[k] == 1:
                        bits = single_bits[bp]
                    else:
                        bits = double_bits[bp]
                    # Check if bitpattern of the category should be filtered
                    if bits == bin_cat[len(bin_cat) -
                                       bpe:len(bin_cat) - bps[k]]:
                        # Add category to recassification rule
                        rc = rc + ' {}'.format(cat)
                        # Calculate nuber of pixels which are filtered using
                        # the current bitpattern
                        if print_effect:
                            pe_key = '{} = {}'.format(k, bp)
                            if pe_key not in pe.keys():
                                pe[pe_key] = int(pixels)
                            else:
                                pe[pe_key] = pe[pe_key] + int(pixels)

    # Construct rules for reclassification
    if invert:
        rc = rc + ' = 1\n * = NULL'
    else:
        rc = rc + ' = NULL\n * = 1'

    # Print filterstistics if requested, else reclassify
    if print_effect:
        for k in pe.keys():
            sys.stdout.write('{} {}\n'.format(k, pe[k]))
    else:
        grass.write_command('r.reclass', flags='', input=input, output=output,
                            rules='-', stdin=rc)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())

