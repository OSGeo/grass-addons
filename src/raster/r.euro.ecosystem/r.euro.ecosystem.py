#!/usr/bin/env python

"""
MODULE:    r.euro.ecosystem

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Sets colors and category labels of European ecosystem raster data sets.
           Rules can be defined for level 1 and level 2 data.
           Color and category label rules donated by European Environment Agency (EEA).
           

COPYRIGHT: (C) 2015, 2019 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: Sets colors and categories of European ecosystem raster data set
# % keyword: raster
# % keyword: color
# % keyword: category
# % keyword: ecosystem
# %end

# %option G_OPT_R_INPUT
# % key: input
# %end

# %flag
# % key: 1
# % description: level 1 data
# %end

# %flag
# % key: 2
# % description: level 2 data
# %end


import sys
import os
import csv
import math
import shutil
import tempfile
import grass.script as grass


def main():

    iraster = options["input"]
    eraster = options["input"].split("@")[0]
    level1 = flags["1"]
    level2 = flags["2"]
    if level1:
        color_rules_level1 = eraster + "_color_level1.txt"
        cat_rules_level1 = eraster + "_cat_level1.txt"
    if level2:
        color_rules_level2 = eraster + "_color_level2.txt"
        cat_rules_level2 = eraster + "_cat_level2.txt"
    global tmp

    # start settings
    grass.message("Setting colors and categories ...")

    # define intermediate folder files
    datatempdir = tempfile.gettempdir()
    if level1:
        tmp_col_l1 = os.path.join(datatempdir, color_rules_level1)
        tmp_cat_l1 = os.path.join(datatempdir, cat_rules_level1)
    if level2:
        tmp_col_l2 = os.path.join(datatempdir, color_rules_level2)
        tmp_cat_l2 = os.path.join(datatempdir, cat_rules_level2)

    # write intermediate color and cat rule file data level 1
    if level1:
        # write intermediate color rule file level 1
        fcl1 = open("%s" % (tmp_col_l1), "wt")
        fcl1.write(
            """1 115:178:255
        2 255:211:127
        3 0:112:255
        4 223:115:255
        5 85:255:0
        6 255:170:0
        7 38:115:0
        8 178:178:178
        9 255:255:0
        10 255:0:0"""
        )
        # close intermediate color level 1 rules
        fcl1.close()
        # write intermediate category rule file level 1
        fcal1 = open("%s" % (tmp_cat_l1), "wt")
        fcal1.write(
            """1|A Marine habitats
        2|B Coastal habitats
        3|C Inland surface waters
        4|D Mires, bogs and fens
        5|E Grasslands and land dominated by forbs, mosses or lichens
        6|F Heathland, scrub and tundra
        7|G Woodland, forest and other wooded land
        8|H Inland unvegetated or sparsely vegetated habitats
        9|I Regularly or recently cultivated, hortocultural and domestic habitats
        10|J Constructed, industrial and other artificial habitats"""
        )
        # close intermediate category level 1 rules
        fcal1.close()

        # apply color rules level 1
        grass.message("applying color rules for data level 1...")
        grass.run_command("r.colors", map=iraster, rules=tmp_col_l1, quiet=True)

        # apply category rules level 1
        grass.message("applying category rules for data level 1...")
        grass.run_command(
            "r.category", map=iraster, rules=tmp_cat_l1, separator="pipe", quiet=True
        )

    # write intermediate color and cat rule file data level 2
    if level2:
        # write intermediate color rule file level 2
        fcl2 = open("%s" % (tmp_col_l2), "wt")
        fcl2.write(
            """9 166:255:230
        10 0:255:166
        11 230:230:230
        12 200:200:200
        13 170:170:170
        14 128:242:230
        15 0:204:242
        16 0:204:153
        17 64:49:81
        18 96:73:122
        19 177:160:199
        20 204:192:218
        21 218:238:243
        22 183:222:232
        23 240:240:150
        24 230:230:77
        25 204:242:77
        26 153:255:153
        28 204:255:255
        29 242:204:166
        30 151:71:6
        31 226:107:10
        32 250:191:143
        33 252:213:180
        34 253:253:217
        35 218:238:243
        36 183:222:232
        37 146:205:220
        38 49:200:155
        40 230:128:0
        41 128:255:0
        42 230:166:0
        43 0:166:0
        44 77:255:0
        45 79:98:40
        47 242:242:242
        48 204:204:204
        49 255:255:255
        50 204:255:204
        52 255:255:168
        53 255:255:0
        54 255:0:0
        55 255:125:125
        56 166:0:204
        57 255:85:0
        58 230:230:255
        59 166:77:0
        100 182:237:240
        101 180:236:240
        103 177:232:240
        104 175:231:240
        105 175:230:240
        106 173:229:240
        110 170:227:240
        111 170:226:240
        113 164:220:237
        114 164:220:237
        115 161:218:237
        116 159:216:237
        120 157:214:237
        200 145:205:237
        201 145:205:237
        203 138:199:235
        204 136:197:235
        205 134:196:235
        206 134:194:235
        210 131:193:235
        211 129:192:235
        213 127:190:235
        214 124:189:235
        215 124:187:235
        216 120:185:235
        220 120:185:235
        300 104:172:232
        301 104:172:232
        303 100:170:232
        304 97:167:232
        305 94:164:230
        306 92:163:230
        310 92:163:230
        311 87:161:230
        313 85:160:230
        314 83:159:230
        315 80:157:230
        316 80:155:230
        320 76:153:230
        326 64:145:227
        400 61:144:227
        401 57:142:227
        403 54:141:227
        404 50:138:227
        405 48:137:227
        406 43:134:224
        410 40:135:224
        411 38:134:224
        413 31:131:224
        414 31:131:224
        415 31:126:222
        416 31:126:222
        420 33:128:222
        426 32:114:214
        500 34:111:212
        501 34:111:212
        503 33:107:209
        504 33:107:209
        505 33:102:207
        506 33:102:207
        510 33:98:204
        511 33:98:204
        513 32:94:201
        514 32:91:201
        515 32:90:199
        516 34:89:199
        520 33:88:196
        526 33:77:191
        600 32:76:189
        601 32:76:189
        603 32:73:186
        604 32:70:186
        605 29:68:184
        606 29:65:184
        610 29:64:181
        614 28:58:176
        616 28:55:176
        620 28:54:173
        700 25:44:166
        701 23:40:166
        704 23:37:163
        705 21:35:161
        706 21:35:161
        710 21:32:158
        720 15:22:153"""
        )
        # close intermediate color level 2 rules
        fcl2.close()

        # write intermediate category rule file level 2
        fcal2 = open("%s" % (tmp_cat_l2), "wt")
        fcal2.write(
            """100|A100 - Littoral undetermined substrate with no sea ice presence
        101|A101 - Littoral rock and biogenic with no sea ice presence
        103|A103 - Littoral coarse sediment with no sea ice presence
        104|A104 - Littoral mixed sediment with no sea ice presence
        105|A105 - Littoral sand with no sea ice presence
        106|A106 - Littoral mud with no sea ice presence
        110|A110 - Littoral undetermined substrate with seasonal sea ice presence
        111|A111 - Littoral rock and biogenic with seasonal sea ice presence
        113|A113 - Littoral coarse sediment with seasonal sea ice presence
        114|A114 - Littoral mixed sediment with seasonal sea ice presence
        115|A115 - Littoral sand with seasonal sea ice presence
        116|A116 - Littoral mud with seasonal sea ice presence
        120|A120 - Littoral undetermined substrate with perrennial sea ice
        200|A200 - Infralittoral undetermined substrate with no sea ice presence
        201|A201 - Infralittoral rock and biogenic with no sea ice presence
        203|A203 - Infralittoral coarse sediment with no sea ice presence
        204|A204 - Infralittoral mixed sediment with no sea ice presence
        205|A205 - Infralittoral sand with no sea ice presence
        206|A206 - Infralittoral mud with no sea ice presence
        210|A210 - Infralittoral undetermined substrate with seasonal sea ice presence
        211|A211 - Infralittoral rock and biogenic with seasonal sea ice presence
        213|A213 - Infralittoral coarse sediment with seasonal sea ice presence
        214|A214 - Infralittoral mixed sediment with seasonal sea ice presence
        215|A215 - Infralittoral sand with seasonal sea ice presence
        216|A216 - Infralittoral mud with seasonal sea ice presence
        220|A220 - Infralittoral undetermined substrate with perrennial sea ice
        300|A300 - Circalittoral undetermined substrate with no sea ice presence
        301|A301 - Circalittoral rock and biogenic with no sea ice presence
        303|A303 - Circalittoral coarse sediment with no sea ice presence
        304|A304 - Circalittoral mixed sediment with no sea ice presence
        305|A305 - Circalittoral sand with no sea ice presence
        306|A306 - Circalittoral mud with no sea ice presence
        310|A310 - Circalittoral undetermined substrate with seasonal sea ice presence
        311|A311 - Circalittoral rock and biogenic with seasonal sea ice presence
        313|A313 - Circalittoral coarse sediment with seasonal sea ice presence
        314|A314 - Circalittoral mixed sediment with seasonal sea ice presence
        315|A315 - Circalittoral sand with seasonal sea ice presence
        316|A316 - Circalittoral mud with seasonal sea ice presence
        320|A320 - Circalittoral undetermined substrate with perrennial sea ice
        326|A326 - Circalittoral mud with perrennial sea ice
        400|A400 - Offshore circalittoral undetermined substrate with no sea ice presence
        401|A401 - Offshore circalittoral rock and biogenic with no sea ice presence
        403|A403 - Offshore circalittoral coarse sediment with no sea ice presence
        404|A404 - Offshore circalittoral mixed sediment with no sea ice presence
        405|A405 - Offshore circalittoral sand with no sea ice presence
        406|A406 - Offshore circalittoral mud with no sea ice presence
        410|A410 - Offshore circalittoral undetermined substrate with seasonal sea ice presence
        411|A411 - Offshore circalittoral rock and biogenic with seasonal sea ice presence
        413|A413 - Offshore circalittoral coarse sediment with seasonal sea ice presence
        414|A414 - Offshore circalittoral mixed sediment with seasonal sea ice presence
        415|A415 - Offshore circalittoral sand with seasonal sea ice presence
        416|A416 - Offshore circalittoral mud with seasonal sea ice presence
        420|A420 - Offshore circalittoral undetermined substrate with perrennial sea ice
        426|A426 - Offshore circalittoral mud with perrennial sea ice
        500|A500 - Upper bathyal undetermined substrate with no sea ice presence
        501|A501 - Upper bathyal rock and biogenic with no sea ice presence
        503|A503 - Upper bathyal coarse sediment with no sea ice presence
        504|A504 - Upper bathyal mixed sediment with no sea ice presence
        505|A505 - Upper bathyal sand with no sea ice presence
        506|A506 - Upper bathyal mud with no sea ice presence
        510|A510 - Upper bathyal undetermined substrate with seasonal sea ice presence
        511|A511 - Upper bathyal rock and biogenic with seasonal sea ice presence
        513|A513 - Upper bathyal coarse sediment with seasonal sea ice presence
        514|A514 - Upper bathyal mixed sediment with seasonal sea ice presence
        515|A515 - Upper bathyal sand with seasonal sea ice presence
        516|A516 - Upper bathyal mud with seasonal sea ice presence
        520|A520 - Upper bathyal undetermined substrate with perrennial sea ice
        526|A526 - Upper bathyal mud with perrennial sea ice
        600|A600 - Lower bathyal undetermined substrate with no sea ice presence
        601|A601 - Lower bathyal rock and biogenic with no sea ice presence
        603|A603 - Lower bathyal coarse sediment with no sea ice presence
        604|A604 - Lower bathyal mixed sediment with no sea ice presence
        605|A605 - Lower bathyal sand with no sea ice presence
        606|A606 - Lower bathyal mud with no sea ice presence
        610|A610 - Lower bathyal undetermined substrate with seasonal sea ice presence
        614|A614 - Lower bathyal mixed sediment with seasonal sea ice presence
        616|A616 - Lower bathyal mud with seasonal sea ice presence
        620|A620 - Lower bathyal undetermined substrate with perrennial sea ice
        700|A700 - Abyssal undetermined substrate with no sea ice presence
        701|A701 - Abyssal rock and biogenic with no sea ice presence
        704|A704 - Abyssal mixed sediment with no sea ice presence
        705|A705 - Abyssal sand with no sea ice presence
        706|A706 - Abyssal mud with no sea ice presence
        710|A710 - Abyssal undetermined substrate with seasonal sea ice presence
        720|A720 - Abyssal undetermined substrate with perrennial sea ice
        9|X1 - Estuaries
        10|X2_3 - Coastal lagoons
        11|B1 - Coastal dunes and sandy shores
        12|B2 - Coastal shingle
        13|B3 - Rock cliffs, ledges and shores, including the supralittoral
        14|C1 - Surface standing waters
        15|C2 - Surface running waters
        16|C3 - Littoral zone of inland surface waterbodies
        17|D1 - Raised and blanket bogs
        18|D2 - Valley mires, poor fens and transition mires
        19|D3 - Aapa, palsa and polygon mires
        20|D4 - Base-rich fens and calcareous spring mires
        21|D5 - Sedge and reedbeds, normally without free-standing water
        22|D6 - Inland saline and brackish marshes and reedbeds
        23|E1 - Dry grasslands
        24|E2 - Mesic grasslands
        25|E3 - Seasonally wet and wet grasslands
        26|E4 - Alpine and subalpine grasslands
        28|E6 - Inland salt steppes
        29|E7 - Sparsely wooded grasslands
        30|F1 - Tundra
        31|F2 - Arctic, alpine and subalpine scrub
        32|F3 - Temperate and mediterranean-montane scrub
        33|F4 - Temperate shrub heathland
        34|F5 - Maquis, arborescent matorral and thermo-Mediterranean brushes
        35|F6 - Garrigue
        36|F7 - Spiny Mediterranean heaths (phrygana, hedgehog-heaths and related coastal cliff vegetation)
        37|F8 - Thermo-Atlantic xerophytic scrub
        38|F9 - Riverine and fen scrubs
        40|FB - Shrub plantations
        41|G1 - Broadleaved deciduous woodland
        42|G2 - Broadleaved evergreen woodland
        43|G3 - Coniferous woodland
        44|G4 - Mixed deciduous and coniferous woodland
        45|G5 - Lines of trees, small anthropogenic woodlands, recently felled woodland, early-stage woodland and coppice
        47|H2 - Screes
        48|H3 - Inland cliffs, rock pavements and outcrops
        49|H4 - Snow or ice-dominated habitats
        50|H5 - Miscellaneous inland habitats with very sparse or no vegetation
        52|I1 - Arable land and market gardens
        53|I2 - Cultivated areas of gardens and parks
        54|J1 - Buildings of cities, towns and villages
        55|J2 - Low density buildings
        56|J3 - Extractive industrial sites
        57|J4 - Transport networks and other constructed hard-surfaced areas
        58|J5 - Highly artificial man-made waters and associated structures
        59|J6 - Waste deposits"""
        )
        # close intermediate category level 1 rules
        fcal2.close()

        # apply color rules level 2
        grass.message("applying color rules for data level 2...")
        grass.run_command("r.colors", map=iraster, rules=tmp_col_l2, quiet=True)

        # apply category rules level 2
        grass.message("applying category rules for data level 2...")
        grass.run_command(
            "r.category", map=iraster, rules=tmp_cat_l2, separator="pipe", quiet=True
        )

    # do some clean up
    grass.message("----")
    grass.message("cleaning intermediate files ....")
    if level1:
        os.remove("%s" % tmp_col_l1)
        os.remove("%s" % tmp_cat_l1)

    if level2:
        os.remove("%s" % tmp_col_l2)
        os.remove("%s" % tmp_cat_l2)

    grass.message("Cleaning done.")
    grass.message("----")


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
