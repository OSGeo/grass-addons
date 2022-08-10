#!/usr/bin/env python3
# 
############################################################################
#
# MODULE:       i.burn
# AUTHOR(S):    Carlos H. Grohmann, Gustavo Baptista, Gustavo Ferreira
# PURPOSE:      Calculates burn area indices from Landsat/Sentinel images
# COPYRIGHT:    (C) 2021 GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#############################################################################

#%Module
#%  description: i.burn - burn area indices (NBR, dNBR, RdNBR)
#%End
#%option G_OPT_R_INPUT
#% key: nir_post
#% label: Raster input map - Postfire NIR band
#% description: Landsat 5/7: band 4; Landsat 8/9: band 5; Sentinel 2: band 8A
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_INPUT
#% key: swir_post
#% label: Raster input map - Postfire SWIR band
#% description: Landsat 5-9: band 7; Sentinel 2: band 12
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_OUTPUT
#% key: nbr_post
#% description: Postfire NBR output raster map
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_INPUT
#% key: nir_pre
#% label: Raster input map - Prefire NIR band
#% description: Landsat 5/7: band 4; Landsat 8/9: band 5; Sentinel 2: band 8A
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_INPUT
#% key: swir_pre
#% label: Raster input map - Prefire SWIR band
#% description: Landsat 5-9: band 7; Sentinel 2: band 12
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_OUTPUT
#% key: nbr_pre
#% description: Prefire NBR output raster map
#% required : no
#% guisection: NBR
#%end
#%option G_OPT_R_INPUT
#% key: nbr_pre_in
#% description: Prefire NBR raster map
#% required : no
#% guisection: dNBR/RdNBR
#%end
#%option G_OPT_R_INPUT
#% key: nbr_post_in
#% description: Postfire NBR raster map
#% required : no
#% guisection: dNBR/RdNBR
#%end
#%option G_OPT_R_OUTPUT
#% key: dnbr
#% description: dNBR output raster map
#% required : no
#% guisection: dNBR/RdNBR
#%end
#%option G_OPT_R_OUTPUT
#% key: rdnbr
#% description: RdNBR output raster map
#% required : no
#% guisection: dNBR/RdNBR
#%end
# %flag
# % key: n
# % description: Calculate post-fire NBR
#% guisection: NBR
# %end
# %flag
# % key: b
# % description: Calculate pre-fire NBR
#% guisection: NBR
# %end
# %flag
# % key: d
# % description: Calculate dNBR (requires pre- and postfire NBR)
#% guisection: dNBR/RdNBR
# %end
# %flag
# % key: r
# % description: Calculate RdNBR (requires pre- and postfire NBR)
#% guisection: dNBR/RdNBR
# %end

import sys
import grass.script as gs
from grass.exceptions import CalledModuleError

# 'darkgreen'
# 'green'
# 'lightgreen'
# 'yellow'
# 'darkred'
# 'brown'
# 'red'

# -500
# -250
# -100
# 100
# 270
# 440
# 660
# 1300


COLORS = '''
0% 0:61:0
-375 0:61:0
-175 0:128:0
0 143:237:143
185 255:255:0
355 137:0:0
550 99:41:41
980 255:0:0
100% 255:0:0.0
'''

CATS = '''
-500:-250:High Regrowth
-250:-100:Low Regrowth
-100:100:Not Burned
100:270:Low Severity
270:440:Moderate Low Severity
440:660:Moderate High Severity
660:1300:High Severity
'''

RECLASS = '''
-5000 thru -250 = 1 High Regrowth
-250 thru -100 = 2 Low Regrowth
-100 thru 100 = 3 Not Burned
100 thru 270 = 4 Low Severity
270 thru 440 = 5 Moderate Low Severity
440 thru 660 = 6 Moderate High Severity
660 thru 13000 =  7 High Severity
'''

COLORS_CLASS = '''
0% 0:61:0
1 0:61:0
2 0:128:0
3 143:237:143
4 255:255:0
5 137:0:0
6 99:41:41
7 255:0:0
100% 255:0:0.0
'''


def main():

    options, flags = gs.parser()

    # options and flags
    nir_post = options["nir_post"]
    swir_post = options["swir_post"]
    nbr_post = options["nbr_post"]
    nir_pre = options["nir_pre"]
    swir_pre = options["swir_pre"]
    nbr_pre = options["nbr_pre"]
    nbr_pre_in = options["nbr_pre_in"]
    nbr_post_in = options["nbr_post_in"]
    dnbr = options["dnbr"]
    rdnbr = options["rdnbr"]
    nbr_post_ok = flags["n"]
    nbr_pre_ok = flags["b"]
    dnbr_ok = flags["d"]
    rdnbr_ok = flags["r"]

    def set_colors_classes(raster):
        rclass = f'{raster}_class'
        gs.write_command('r.colors', map=raster, rules='-', stdin=COLORS, quiet=True)
        # gs.write_command('r.category', map=raster, rules='-', stdin=CATS, separator=':', quiet=True)
        gs.write_command('r.reclass', input=raster, output=rclass, rules='-', stdin=RECLASS)
        gs.write_command('r.colors', map=rclass, rules='-', stdin=COLORS_CLASS, quiet=True)


    # NBR: ((band_4 - band_7) / (band_4 + band_7)) * 1000 (Key & Benson, 2006)
    if nbr_post_ok:
        # check if nir and swir exist. If not, return error
        if not gs.find_file(name=nir_post, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nir_post)
        if not gs.find_file(name=swir_post, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % swir_post)
        # calculate
        gs.message("Calculating postfire NBR...")
        gs.mapcalc(f'{nbr_post} = (({nir_post} - {swir_post}) / ({nir_post} + {swir_post})) * 1000.')
        # set_colors_classes(nbr_post)
        gs.run_command('r.colors', map=nbr_post, color='grey')
        gs.message("done.")
        gs.message(" ")

    if nbr_pre_ok:
        # check if nir and swir exist. If not, return error
        if not gs.find_file(name=nir_pre, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nir_pre)
        if not gs.find_file(name=swir_pre, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % swir_pre)
        # calculate
        gs.message("Calculating prefire NBR...")
        gs.mapcalc(f'{nbr_pre} = (({nir_pre} - {swir_pre}) / ({nir_pre} + {swir_pre})) * 1000.')
        # set_colors_classes(nbr_pre)
        gs.run_command('r.colors', map=nbr_pre, color='grey')
        gs.message("done.")
        gs.message(" ")

    # dNBR: (NBR_prefire - NBR_postfire) #dNBR (Roy et al., 2006)
    if dnbr_ok:
        # check if NBR prefire and postfire exist. If not, return error
        if not gs.find_file(name=nbr_post_in, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nbr_post_in)
        if not gs.find_file(name=nbr_pre_in, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nbr_pre_in)
        # then dNBR
        gs.message("Calculating dNBR...")
        gs.mapcalc(f'{dnbr} = {nbr_pre_in} - {nbr_post_in}')
        set_colors_classes(dnbr)
        gs.message("done.")
        gs.message(" ")


    # RdNBR: (NBR_prefire - NBR_postfire) / sqrt(abs(NBR_prefire / 1000)) (Miller & Thode, 2007)
    if rdnbr_ok:
        # check if NBR prefire and postfire exist. If not, return error
        if not gs.find_file(name=nbr_post_in, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nbr_post_in)
        if not gs.find_file(name=nbr_pre_in, element='cell')['file']:
            gs.fatal("Raster map <%s> not found" % nbr_pre_in)
        # then calculate RdNBR
        gs.message("Calculating RdNBR...")
        gs.mapcalc(f'{rdnbr} = ({nbr_pre_in} - {nbr_post_in}) / sqrt(abs({nbr_pre_in} / 1000.))')
        set_colors_classes(rdnbr)
        gs.message("done.")
        gs.message(" ")


if __name__ == "__main__":
    argv = sys.argv[:]
    if len(argv)<2:
        sys.argv.append('--ui')
    main()







