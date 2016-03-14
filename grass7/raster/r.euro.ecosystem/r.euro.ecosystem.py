#!/usr/bin/env python

"""
MODULE:    r.euro.ecosystem

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Sets colors and category labels of European ecosystem raster data sets.
           Rules can be defined for level 1 and level 2 data.
           Color and category label rules donated by European Environment Agency (EEA).
           

COPYRIGHT: (C) 2015 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%module
#% description: Sets colors and categories of European ecosystem raster data set
#% keyword: raster
#% keyword: color
#% keyword: category
#% keyword: ecosystem
#%end

#%option G_OPT_R_INPUT 
#% key: input
#%end

#%flag
#% key: 1
#% description: level 1 data
#%end

#%flag
#% key: 2
#% description: level 2 data
#%end


import sys
import os
import csv
import math
import shutil
import tempfile
import grass.script as grass

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():

    iraster = options['input']		
    eraster = options['input'].split('@')[0]
    level1 = flags['1']
    level2 = flags['2']
    if level1 :
        color_rules_level1 = eraster+'_color_level1.txt'
        cat_rules_level1 = eraster+'_cat_level1.txt'		
    if level2 :
        color_rules_level2 = eraster+'_color_level2.txt'
        cat_rules_level2 = eraster+'_cat_level2.txt'
    global tmp	 
		
    # start settings
    grass.message( "Setting colors and categories ..." )

    # define intermediate folder files
    datatempdir = tempfile.gettempdir()
    if level1 :
        tmp_col_l1 = os.path.join( datatempdir, color_rules_level1 )
        tmp_cat_l1 = os.path.join( datatempdir, cat_rules_level1 )
    if level2 :    
        tmp_col_l2 = os.path.join( datatempdir, color_rules_level2 )
        tmp_cat_l2 = os.path.join( datatempdir, cat_rules_level2 )	

		
    # write intermediate color and cat rule file data level 1
    if level1 :
		# write intermediate color rule file level 1
        fcl1 = open('%s' % (tmp_col_l1), 'wt')
        fcl1.write("""1 115:178:255
        2 255:211:127
        3 0:112:255
        4 223:115:255
        5 85:255:0
        6 255:170:0
        7 38:115:0
        8 178:178:178
        9 255:255:0
        10 255:0:0""")
		# close intermediate color level 1 rules      
        fcl1.close()
		# write intermediate category rule file level 1
        fcal1 = open('%s' % (tmp_cat_l1), 'wt')
        fcal1.write("""1|A Marine habitats
        2|B Coastal habitats
        3|C Inland surface waters
        4|D Mires, bogs and fens
        5|E Grasslands and land dominated by forbs, mosses or lichens
        6|F Heathland, scrub and tundra
        7|G Woodland, forest and other wooded land
        8|H Inland unvegetated or sparsely vegetated habitats
        9|I Regularly or recently cultivated, hortocultural and domestic habitats
        10|J Constructed, industrial and other artificial habitats""")
		# close intermediate category level 1 rules      
        fcal1.close()

        # apply color rules level 1
        grass.message ( "applying color rules for data level 1..." )		
        grass.run_command("r.colors", map = iraster,
                                        rules = tmp_col_l1,
                                        quiet = True)

		
		# apply category rules level 1
        grass.message ( "applying category rules for data level 1..." )			
        grass.run_command("r.category", map = iraster,
                                        rules = tmp_cat_l1,
                                        separator = 'pipe',
                                        quiet = True)		
		
    # write intermediate color and cat rule file data level 2		
    if level2 :
		# write intermediate color rule file level 2
        fcl2 = open('%s' % (tmp_col_l2), 'wt')
        fcl2.write("""11 230:230:230
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
        101 148:138:84
        102 166:157:112
        103 202:197:168
        104 221:217:196
        105 41:199:242
        106 47:111:242
        109 166:255:230
        110 0:255:166
        112 184:177:140
        128 120:149:184
        134 40:235:196
        138 153:176:203
        181 45:96:146
        182 120:149:184
        185 186:203:222
        186 220:230:241
        250 0:0:0""")	
        # close intermediate color level 2 rules 
        fcl2.close()
		
		# write intermediate category rule file level 2
        fcal2 = open('%s' % (tmp_cat_l2), 'wt')
        fcal2.write("""101|A1 Littoral rock and other hard substrata
        102|A2 Littoral sediment
        112|A1_2 Littoral rock or sediment
        103|A3 Infralittoral rock and other hard substrata
        104|A4 Circalittoral rock and other hard substrata
        134|A3_4 Infralittoral and circalittoral rock and other hard substrata
        105|A5 Sublittoral sediment
        106|A6 Deep-sea bed
        109|X1 Estuaries
        110|X2_3 Coastal lagoons
        181|A1_8 Littoral rock and other hard substrata and sea ice
        182|A2_8 Littoral sediment and sea ice
        128|A1_2_8 Littoral rock or sediment and sea ice
        138|A3_4_8 Infralittoral and circalittoral rock and other hard substrata and sea ice
        185|A5_8 Sublittoral sediment and sea ice
        186|A6_8 Deep-sea bed and sea ice
        250|Unclassified
        9|X1 Estuaries
        10|X2_3 Coastal lagoons
        11|B1 Coastal dunes and sandy shores
        12|B2 Coastal shingle
        13|B3 Rock cliffs, ledges and shores, including the supralittoral
        14|C1 Surface standing waters
        15|C2 Surface running waters
        16|C3 Littoral zone of inland surface waterbodies
        17|D1 Raised and blanket bogs
        18|D2 Valley mires, poor fens and transition mires
        19|D3 Aapa, palsa and polygon mires
        20|D4 Base-rich fens and calcareous spring mires
        21|D5 Sedge and reedbeds, normally without free-standing water
        22|D6 Inland saline and brackish marshes and reedbeds
        23|E1 Dry grasslands
        24|E2 Mesic grasslands
        25|E3 Seasonally wet and wet grasslands
        26|E4 Alpine and subalpine grasslands
        27|E5 Woodland fringes and clearings and tall forb stands
        28|E6 Inland salt steppes
        29|E7 Sparsely wooded grasslands
        30|F1 Tundra
        31|F2 Arctic, alpine and subalpine scrub
        32|F3 Temperate and mediterranean-montane scrub
        33|F4 Temperate shrub heathland
        34|F5 Maquis, arborescent matorral and thermo-Mediterranean brushes
        35|F6 Garrigue
        36|F7 Spiny Mediterranean heaths (phrygana, hedgehog-heaths and related coastal cliff vegetation)
        37|F8 Thermo-Atlantic xerophytic scrub
        38|F9 Riverine and fen scrubs
        39|FA Hedgerows
        40|FB Shrub plantations
        41|G1 Broadleaved deciduous woodland
        42|G2 Broadleaved evergreen woodland
        43|G3 Coniferous woodland
        44|G4 Mixed deciduous and coniferous woodland
        45|G5 Lines of trees, small anthropogenic woodlands, recently felled woodland, early-stage woodland and coppice
        46|H1 Terrestrial underground caves, cave systems, passages and waterbodies
        47|H2 Screes
        48|H3 Inland cliffs, rock pavements and outcrops
        49|H4 Snow or ice-dominated habitats
        50|H5 Miscellaneous inland habitats with very sparse or no vegetation
        51|H6 Recent volcanic features
        52|I1 Arable land and market gardens
        53|I2 Cultivated areas of gardens and parks
        54|J1 Buildings of cities, towns and villages
        55|J2 Low density buildings
        56|J3 Extractive industrial sites
        57|J4 Transport networks and other constructed hard-surfaced areas
        58|J5 Highly artificial man-made waters and associated structures
        59|J6 Waste deposits""")
		# close intermediate category level 1 rules      
        fcal2.close()


		# apply color rules level 2
        grass.message ( "applying color rules for data level 2..." )
        grass.run_command("r.colors", map = iraster,
                                        rules = tmp_col_l2,
                                        quiet = True)

		
		# apply category rules level 2
        grass.message ( "applying category rules for data level 2..." )	
        grass.run_command("r.category", map = iraster,
                                        rules = tmp_cat_l2,
                                        separator = 'pipe',
                                        quiet = True)

    # do some clean up
    grass.message( "----" )
    grass.message( "cleaning intermediate files ...." )	
    if level1 :
        os.remove("%s" % tmp_col_l1)
        os.remove("%s" % tmp_cat_l1)

    if level2 :
        os.remove("%s" % tmp_col_l2)
        os.remove("%s" % tmp_cat_l2)

    grass.message( "Cleaning done." )
    grass.message( "----" )
										
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
