#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 MODULE:       i.landsat8.qa

 AUTHOR(S):    Stefan Blumentrath <stefan.blumentrath@nina.no>

 PURPOSE:      Reclass Landsat QA band according to acceptable pixel quality
               as defined by the user

 COPYRIGHT:    (C) 2016-2021 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

#%Module
#% description: Reclassifies Landsat QA band according to acceptable pixel quality as defined by the user.
#% keyword: imagery
#% keyword: pixel
#% keyword: quality
#% keyword: qa
#% keyword: bitpattern
#% keyword: mask
#% keyword: landsat
#%End

#%option G_OPT_F_OUTPUT
#% description: Output file with reclass rules
#% required: no
#%end


#%option
#% key: collection
#% multiple: No
#% description: Landsat Collection (1 or 2)
#% options: 1, 2
#% answer: 1
#% required : no
#%end

#%option
#% key: sensor
#% multiple: No
#% description: Landsat Collection (1 or 2)
#% options: Landsat 8 OLI, Landsat 8 OLI/TIRS, Landsat 1-5 MSS, Landsat 7 ETM+, Landsat 4-5 TM
#% answer: 1
#% required : no
#%end

#%option
#% key: designated_fill
#% multiple: No
#% description: Unacceptable conditions for Designated Fill
#% options: No, Yes
#% required : no
#%end

#%option
#% key: terrain_occlusion
#% multiple: No
#% description: Unacceptable conditions for Terrain Occlusion / Dropped Pixels
#% options: No, Yes
#% required : no
#%end

#%option
#% key: radiometric_saturation
#% multiple: No
#% description: Unacceptable conditions for Radiometric Saturation
#% options: Not Determined, Low, Medium, High
#% required : no
#%end

#%option
#% key: cloud
#% multiple: No
#% description: Unacceptable conditions for Clouds
#% options: No, Yes
#% required : no
#%end

#%option
#% key: cloud_confidence
#% multiple: yes
#% description: Unacceptable conditions for Cloud confidence
#% options: Not Determined, Low, Medium, High
#% required : no
#%end

#%option
#% key: cloud_shadow_confidence
#% multiple: yes
#% description: Unacceptable conditions for Cloud Shaddow Confidence
#% options: Not Determined, Low, Medium, High
#% required : no
#%end

#%option
#% key: snow_ice_confidence
#% multiple: yes
#% description: Unacceptable conditions for Snow/Ice Confidence
#% options: Not Determined, Low, Medium, High
#% required : no
#%end

#%option
#% key: cirrus_confidence
#% multiple: yes
#% description: Unacceptable conditions for Cirrus Confidence
#% options: Not Determined, Low, Medium, High
#% required : no
#%end

#%rules
#% required: designated_fill,terrain_occlusion,radiometric_saturation,cloud,cloud_confidence,cloud_shadow_confidence,snow_ice_confidence,cirrus_confidence
#%end

import os
import sys
import grass.script as grass

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main():
    """
    Main program
    """

    # Parse options
    output = options['output']
    collection = options['collection']
    sensor = options['sensor']

    # Extract bitpattern filter from user input
    bit_filter = []
    for f in options.keys():
        if options[f] and f not in ['output', 'collection', 'sensor']:
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
    Populated bits:

    0		Designated Fill
    1		Terrain Occlusion
    2-3		Radiometric saturation
    4		Cloud
    5-6		Cloud confidence
    7-8		Cloud shaddow confidence
    9-10	Snow/Ice confidence
    11-12	Cirrus confidence
    """

    # Define bit length (single or double bits)
    bit_length = {'1': {'designated_fill': 1,
          'terrain_occlusion': 1,
          'radiometric_saturation': 2,
          'cloud': 1,
          'cloud_confidence': 2,
          'cloud_shadow_confidence': 2,
          'snow_ice_confidence': 2,
          'cirrus_confidence': 2,
          }}

    # Define bit position start
    bit_position = {'1': {'designated_fill': 0,
          'terrain_occlusion': 1,
          'radiometric_saturation': 2,
          'cloud': 4,
          'cloud_confidence': 5,
          'cloud_shadow_confidence': 7,
          'snow_ice_confidence': 9,
          'cirrus_confidence': 11,
          }}

    """
    For the single bits (0, 1, 2, and 3):
        0 = No, this condition does not exist
        1 = Yes, this condition exists.
    """

    # Define single bits dictionary
    single_bits = {'No': '0',
                   'Yes': '1'}

    """
    The double bits (2-3, 5-6, 7-8, 9-10, and 11-12), read from left to
    right, represent levels of confidence that a condition exists:
    00 = 'Not Determined' = Algorithm did not determine the status
                            of this condition
    01 = 'Low' = Algorithm has low to no confidence that this condition exists
                (0-33 percent confidence)
    10 = 'Medium' = Algorithm has medium confidence that this condition exists
                (34-66 percent confidence)
    11 = 'High' = Algorithm has high confidence that this condition exists
                (67-100 percent confidence).
    """

    # Define double bits dictionary
    double_bits = {'Not Determined': '00',
                   'Low': '01',
                   'Medium': '10',
                   'High': '11'}

    bit_position = bit_position[collection]
    bit_length = bit_length[collection]

    # List for categories representing pixels of unacceptable quality
    rc = []

    # Loop over all possible integer representations of a 16-bit bitpattern
    # given as category values in the QA band
    print(bit_filter)
    for cat in range(max_int + 1):
        # Get the binary equivalent of the integer value
        bin_cat = '{0:016b}'.format(cat)

        # Loop over user-defined the bitpattern filter (bit_filter) elements
        for k in bit_filter:
            # Calculate bit positions end (bpe)
            bpe = bit_position[k] + bit_length[k]

            # Extract unnacceptable bitpatterns (bp) form bitpattern filter
            for bp in options[k].split(','):

                if bit_length[k] == 1:
                    bits = single_bits[bp]
                else:
                    bits = double_bits[bp]

                # Check if bitpattern of the category should be filtered
                if bits == bin_cat[len(bin_cat) - bpe:len(bin_cat) - bit_position[k]]:
                    # Add category to recassification rule
                    rc.append(str(cat) + ' = NULL')
                    break
            # Avoid duplicates in reclass rules when several filter are applied
            if bits == bin_cat[len(bin_cat) - bpe:len(bin_cat) - bit_position[k]]:
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
