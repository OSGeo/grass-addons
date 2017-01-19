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
#% description: Reclassifies Landsat8 QA band according to acceptable pixel quality as defined by the user.
#% keyword: imagery
#% keyword: qc
#% keyword: bitpattern
#% keyword: mask
#% keyword: landsat8
#%End

#%option G_OPT_F_OUTPUT
#% description: Output file with reclass rules
#% required: no
#%end

#%option
#% key: designated_fill
#% multiple: No
#% description: Unacceptable conditions for Designated Fill (bit 0)
#% options: No, Yes
#% required : no
#%end

#%option
#% key: dropped_frame
#% multiple: No
#% description: Unacceptable conditions for Dropped Frame (bit 1)
#% options: No, Yes
#% required : no
#%end

#%option
#% key: terrain_occlusion
#% multiple: No
#% description: Unacceptable conditions for Terrain Occlusion (bit 2)
#% options: No, Yes
#% required : no
#%end

##%option
##% key: reserved
##% multiple: No
##% description: Unacceptable conditions for Reserved (not currently used) (bit 3)
##% options: No, Yes
##% required : no
##%end

#%option
#% key: water
#% multiple: yes
#% description: Unacceptable conditions for Water Confidence (bit 4-5)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cloud_shadow
#% multiple: yes
#% description: Unacceptable conditions for Cloud Shaddow Confidence (bit 6-7)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: vegetation
#% multiple: yes
#% description: Unacceptable conditions for Vegetation Confidence (bit 8-9)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: snow_ice
#% multiple: yes
#% description: Unacceptable conditions for Snow/Ice Confidence (bit 10-11)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cirrus
#% multiple: yes
#% description: Unacceptable conditions for Cirrus Confidence (bit 12-13)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%option
#% key: cloud
#% multiple: yes
#% description: Unacceptable conditions for Cloud Confidence (bit 14-15)
#% options: Not Determined, No, Maybe, Yes
#% required : no
#%end

#%rules
#% required: designated_fill,dropped_frame,terrain_occlusion,water,cloud_shadow,vegetation,snow_ice,cirrus,cloud
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

    # Parse options
    output = options['output']

    # Extract bitpattern filter from user input
    bit_filter = []
    for f in options.keys():
        if options[f] and f != 'output':
            bit_filter.append(f)

    # Check if propper input is provided:
    for o in bit_filter:
        if len(options[o].split(',')) >= 4:
            grass.fatal("""All conditions for {} specified as
            unacceptable, this will result in an empty map.""".format(o))

    # Define length of Landsat8 QA bitpattern
    number_of_bits = 16

    # Get maximum integer representation
    max_int = int(''.join([str(1)] * number_of_bits), 2)

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
          'cloud_shadow': 2,
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
        'cloud_shadow': 6,
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

    # List for categories representing pixels of unacceptable quality
    rc = []

    # Loop over all possible integer representations of a 16-bit bitpattern
    # given as category values in the QA band
    for cat in range(max_int + 1):
        # Get the binary equivalent of the integer value
        bin_cat = '{0:016b}'.format(cat)

        # Loop over user-defined the bitpattern filter (bit_filter) elements
        for k in bit_filter:
            # Calculate bit positions end (bpe)
            bpe = bps[k] + bl[k]

            # Extract unnacceptable bitpatterns (bp) form bitpattern filter
            for bp in options[k].split(','):

                if bl[k] == 1:
                    bits = single_bits[bp]
                else:
                    bits = double_bits[bp]

                # Check if bitpattern of the category should be filtered
                if bits == bin_cat[len(bin_cat) - bpe:len(bin_cat) - bps[k]]:
                    # Add category to recassification rule
                    rc.append(str(cat) + ' = NULL')
                    break
            # Avoid duplicates in reclass rules when several filter are applied
            if bits == bin_cat[len(bin_cat) - bpe:len(bin_cat) - bps[k]]:
                break

    # Construct rules for reclassification
    rules = '\n'.join(rc) + '\n* = 1\n'

    # Print to stdout if no output file is specified
    if not options['output']:
            sys.stdout.write(rules)
    else:
        with open(output, 'w') as o:
            o.write(rules)

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
