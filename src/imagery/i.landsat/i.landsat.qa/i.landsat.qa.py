#!/usr/bin/env python

"""
 MODULE:       i.landsat.qa

 AUTHOR(S):    Stefan Blumentrath <stefan.blumentrath@nina.no>

 PURPOSE:      Reclass Landsat QA band according to acceptable pixel quality
               as defined by the user

 COPYRIGHT:    (C) 2016-2021 by the GRASS Development Team

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.
"""

# %Module
# % description: Reclassifies Landsat QA band according to acceptable pixel quality as defined by the user.
# % keyword: imagery
# % keyword: pixel
# % keyword: quality
# % keyword: qa
# % keyword: bitpattern
# % keyword: mask
# % keyword: landsat
# %End

# %option G_OPT_F_OUTPUT
# % description: Output file with reclass rules
# % required: no
# %end

# %option
# % key: dataset
# % type: string
# % description: Landsat dataset to search for
# % required: no
# % options: landsat_tm_c1, landsat_etm_c1, landsat_8_c1, landsat_tm_c2_l1, landsat_tm_c2_l2, landsat_etm_c2_l1, landsat_etm_c2_l2, landsat_ot_c2_l1, landsat_ot_c2_l2
# % answer: landsat_8_c1
# % guisection: Filter
# %end

# %option
# % key: designated_fill
# % multiple: No
# % description: Unacceptable conditions for Designated Fill
# % options: No, Yes
# % required : no
# %end

# %option
# % key: cloud
# % multiple: No
# % description: Unacceptable conditions for Clouds
# % options: No, Yes
# % required : no
# %end

# %option
# % key: cloud_confidence
# % multiple: yes
# % description: Unacceptable conditions for Cloud confidence
# % options: Not Determined, Low, Medium, High
# % required : no
# %end

# %option
# % key: cloud_shadow_confidence
# % multiple: yes
# % description: Unacceptable conditions for Cloud Shaddow Confidence
# % options: Not Determined, Low, Medium, High
# % required : no
# %end

# %option
# % key: snow_ice_confidence
# % multiple: yes
# % description: Unacceptable conditions for Snow/Ice Confidence
# % options: Not Determined, Low, Medium, High
# % required : no
# %end

# %option
# % key: cirrus_confidence
# % multiple: yes
# % description: Unacceptable conditions for Cirrus Confidence
# % options: Not Determined, Low, Medium, High
# % required : no
# %end

# %option
# % key: dilated_cloud
# % multiple: No
# % description: Unacceptable conditions for Pixels with Dilated Clouds (only collection 2)
# % options: No, Yes
# % required : no
# %end

# %option
# % key: snow
# % multiple: No
# % description: Unacceptable conditions for Snow Pixels (only collection 2)
# % options: No, Yes
# % required : no
# %end

# %option
# % key: clear
# % multiple: No
# % description: Unacceptable conditions for Clear Pixels (only collection 2)
# % options: No, Yes
# % required : no
# %end

# %option
# % key: water
# % description: Unacceptable conditions for Water Pixels (only collection 2)
# % options: No, Yes
# % required : no
# %end

# %option
# % key: terrain_occlusion
# % multiple: No
# % description: Unacceptable conditions for Terrain Occlusion / Dropped Pixels (only collection 1)
# % options: No, Yes
# % required : no
# %end

# %option
# % key: radiometric_saturation
# % multiple: yes
# % description: Unacceptable conditions for Radiometric Saturation (only collection 1)
# % options: Not Determined, Low, Medium, High
# % required : no
# %end

# %rules
# % required: designated_fill,terrain_occlusion,radiometric_saturation,cloud,cloud_confidence,cloud_shadow_confidence,snow_ice_confidence,cirrus_confidence,dilated_cloud,snow,clear,water,terrain_occlusion,radiometric_saturation
# %end

# To do:
# - implement other quality bands of esp. collection 2
#   - QA_RADSAT
#   - SR_QA_AEORSOL
#   - SR_Cloud_QA
# - remove unsupported conditions from bitpattern check
# - Add tests

import os
import sys
import grass.script as grass

if "GISBASE" not in os.environ:
    print(_("You must be in GRASS GIS to run this program."))
    sys.exit(1)


def check_user_input(user_input):
    """Checks user input for consistency"""
    collection_unsupported = {
        "c1": ["dilated_cloud", "snow", "clear", "water"],
        "c2": ["terrain_occlusion", "radiometric_saturation"],
    }

    sensor, collection = user_input["dataset"].split("_")[1:3]

    # Extract bitpattern filter from user input
    bit_filter = []
    for f in user_input:
        if user_input[f] and f not in ["output", "dataset"]:
            bit_filter.append(f)

    # Check if propper input is provided:
    for o in bit_filter:
        if len(user_input[o].split(",")) >= 4:
            grass.fatal(
                _(
                    """All conditions for {} specified as
            unacceptable, this will result in an empty map.""".format(
                        o
                    )
                )
            )
        # Check if valid combination of options if provided
        if o in collection_unsupported[collection]:
            grass.warning(
                _(
                    "Condition {condition} is unsupported in Collection {collection}".format(
                        condition=o, collection=user_input["collection"]
                    )
                )
            )
    return sensor, collection, bit_filter


def main():
    """
    Main program
    """

    # Parse options
    output = options["output"]
    dataset = options["dataset"]

    sensor, collection, bit_filter = check_user_input(options)

    # Define bitpattern characteristics according to
    # https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-1-level-1-quality-assessment-band
    # https://www.usgs.gov/core-science-systems/nli/landsat/landsat-collection-2-quality-assessment-bands

    # Define length of Landsat QA bitpattern
    max_bits_used = {
        "c1": {
            "ot": 13,
            "8": 13,
            "etm": 13,
            "tm": 11,
            "Landsat_1-5_MSS": 7,
        },
        "c2": {
            "ot": 16,
            "8": 16,
            "etm": 14,
            "tm": 14,
            "Landsat_1-5_MSS": 10,
        },
    }

    # Populated bits
    # Collection 1:

    # 0		Designated Fill
    # 1		Terrain Occlusion
    # 2-3	Radiometric saturation
    # 4		Cloud
    # 5-6	Cloud confidence
    # 7-8	Cloud shaddow confidence
    # 9-10	Snow/Ice confidence
    # 11-12	Cirrus confidence

    # Define bit length (single or double bits)
    bit_length = {
        "c1": {
            "designated_fill": 1,
            "terrain_occlusion": 1,
            "radiometric_saturation": 2,
            "cloud": 1,
            "cloud_confidence": 2,
            "cloud_shadow_confidence": 2,
            "snow_ice_confidence": 2,
            "cirrus_confidence": 2,
        },
        "c2": {
            "designated_fill": 1,
            "dilated_cloud": 1,
            "cirrus": 1,
            "cloud": 1,
            "cloud_shadow": 1,
            "snow": 1,
            "clear": 1,
            "water": 1,
            "cloud_confidence": 2,
            "cloud_shadow_confidence": 2,
            "snow_ice_confidence": 2,
            "cirrus_confidence": 2,
        },
    }

    # Define bit position start
    bit_position = {
        "c1": {
            "designated_fill": 0,
            "terrain_occlusion": 1,
            "radiometric_saturation": 2,
            "cloud": 4,
            "cloud_confidence": 5,
            "cloud_shadow_confidence": 7,
            "snow_ice_confidence": 9,
            "cirrus_confidence": 11,
        },
        "c2": {
            "designated_fill": 0,
            "dilated_cloud": 1,
            "cirrus": 2,
            "cloud": 3,
            "cloud_shadow": 4,
            "snow": 5,
            "clear": 6,
            "water": 7,
            "cloud_confidence": 8,
            "cloud_shadow_confidence": 10,
            "snow_ice_confidence": 12,
            "cirrus_confidence": 14,
        },
    }

    # Define single bits dictionary

    # For the single bits (0, 1, 2, and 3):
    #     0 = No, this condition does not exist
    #     1 = Yes, this condition exists.

    single_bits = {"No": "0", "Yes": "1"}

    # Define double bits dictionary

    # The double bits (2-3, 5-6, 7-8, 9-10, and 11-12), read from left to
    # right, represent levels of confidence that a condition exists:
    # 00 = 'Not Determined' = Algorithm did not determine the status
    #                         of this condition
    # 01 = 'Low' = Algorithm has low to no confidence that this condition exists
    #             (0-33 percent confidence)
    # 10 = 'Medium' = Algorithm has medium confidence that this condition exists
    #             (34-66 percent confidence)
    # 11 = 'High' = Algorithm has high confidence that this condition exists
    #             (67-100 percent confidence).

    double_bits = {"Not Determined": "00", "Low": "01", "Medium": "10", "High": "11"}

    bit_position = bit_position[collection]
    bit_length = bit_length[collection]

    # Check if valid bitpattern input is given
    for pattern in options:
        if pattern in bit_length.keys() and options[pattern]:
            bit_keys = (
                single_bits.keys() if bit_length[pattern] == 1 else double_bits.keys()
            )
            if not set(options[pattern].split(",")).issubset(set(bit_keys)):
                grass.fatal(
                    _(
                        "Invalid input for option <{opt}>.\
                only the following are allowed: {valid}".format(
                            opt=pattern, valid=",".join(bit_keys)
                        )
                    )
                )

    # List for categories representing pixels of unacceptable quality
    rc = []

    # Loop over all possible integer representations of a 16-bit bitpattern
    # given as category values in the QA band

    # Get maximum integer representation
    for cat in range(int("".join([str(1)] * max_bits_used[collection][sensor]), 2) + 1):
        # Get the binary equivalent of the integer value
        bin_cat = "{0:016b}".format(cat)

        # Loop over user-defined the bitpattern filter (bit_filter) elements
        for k in bit_filter:
            # Calculate bit positions end (bpe)
            bpe = bit_position[k] + bit_length[k]

            # Extract unnacceptable bitpatterns (bp) form bitpattern filter
            for bp in options[k].split(","):

                if bit_length[k] == 1:
                    bits = single_bits[bp]
                else:
                    bits = double_bits[bp]

                # Check if bitpattern of the category should be filtered
                if bits == bin_cat[len(bin_cat) - bpe : len(bin_cat) - bit_position[k]]:
                    # Add category to recassification rule
                    rc.append(str(cat) + " = NULL")
                    break
            # Avoid duplicates in reclass rules when several filter are applied
            if bits == bin_cat[len(bin_cat) - bpe : len(bin_cat) - bit_position[k]]:
                break

    # Construct rules for reclassification
    rules = "\n".join(rc) + "\n* = 1\n"

    # Print to stdout if no output file is specified
    if not options["output"]:
        sys.stdout.write(rules)
    else:
        with open(output, "w") as o:
            o.write(rules)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
