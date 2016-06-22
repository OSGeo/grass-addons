#!/usr/bin/env python
# -*- coding: utf-8 -*-

############################################################################
#
# MODULE:    r.forestfrag
#
# AUTHOR(S): Emmanuel Sambale, Stefan Sylla,
#            Paulo van Breugel (Python version, paulo@ecodiv.org)
#
# PURPOSE:   Creates forest fragmentation index map from a
#            forest-non-forest raster; The index map is based on
#            Riitters, K., J. Wickham, R. O'Neill, B. Jones, and
#            E. Smith. 2000. in: Global-scalepatterns of forest
#            fragmentation. Conservation Ecology 4(2): 3. [online]
#            URL: http://www.consecol.org/vol4/iss2/art3/
#
# COPYRIGHT: (C) 1997-2016 by the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

#%module
#% description: Computes the forest fragmentation index (Riitters et al. 2000)
#% keyword: raster
#% keyword: landscape structure analysis
#% keyword: forest
#% keyword: fragmentation index
#% keyword: Riitters
#%end

#%option G_OPT_R_INPUT
#% description: Name of forest raster map (where forest=1, non-forest=0)
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% required: yes
#%end

#%option
#% key: window
#% type: integer
#% description: Moving window size (odd number)
#% key_desc: number
#% answer: 3
#% required: yes
#%end

#%option G_OPT_R_OUTPUT
#% key: pf
#% label: Name for output Pf (forest area density) raster map
#% description: Proportion of area which is forested (amount of forest)
#% required: no
#%end

#%option G_OPT_R_OUTPUT
#% key: pff
#% label: Name for output Pff (forest connectivity) raster map
#% description: Conditional probability that neighboring cell is forest
#% required: no
#%end

#%flag
#% key: r
#% description: Set computational region to input raster map
#%end

#%flag
#% key: t
#% description: Keep Pf and Pff maps
#%end

#%flag
#% key: s
#% description: Run r.report on output map
#%end

#%flag
#% key: a
#% description: Trim the output map to avoid border effects
#%end


# import libraries
import os
import sys
import uuid
import atexit
import tempfile
import string
import grass.script as gs

# create set to store names of temporary maps to be deleted upon exit
clean_rast = []


def cleanup():
    cleanrast = list(reversed(clean_rast))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="rast", name=rast, quiet=True)

# Functions

def raster_exists(envlay):
    ffile = gs.find_file(envlay, element = 'cell')
    if not ffile['fullname']:
        gs.fatal(_("Raster map <%s> not found") % envlay)

def tmpname(prefix):
    tmpf = prefix + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.append(tmpf)
    return tmpf

# Main

def main():
    # Variables
    ipl = options['input']
    raster_exists(ipl)
    opl = options['output']
    wz  = int(options['window'])
    if wz % 2 == 0:
        gs.fatal(_("Please provide an odd number for the moving window"))
    # user wants pf or pff
    user_pf = options['pf']
    user_pff = options['pff']
    # backwards compatibility
    if flags['t']:
        gs.warning(_("The -t flag is deprecated, use pf and pff options"
                     " instead"))
    if not user_pf and not user_pff and flags['t']:
        user_pf = opl + '_pf'
        user_pff = opl + '_pff'
    elif flags['t']:
        gs.warning(_("When pf or pff option is used, the -t flag"
                     " is ignored"))
    flag_r = flags['r']
    flag_s = flags['s']
    flag_a = flags['a']


    # set to current input map region (user option, default=current region)
    if flag_r:
        gs.message(_("Setting region to input map..."))
        gs.run_command('g.region', quiet=True, raster=ipl)

    # check if map values are limited to 1 and 0
    input_info = gs.raster_info(ipl)
    # we know what we are doing only when input is integer
    if input_info['datatype'] != 'CELL':
        gs.fatal(_("The input raster map must have type CELL"
                   " (integer)"))
    # for integer, we just need to text min and max
    if input_info['min'] != 0 or input_info['max'] != 1:
        gs.fatal(_("The input raster map must be a binary raster,"
                   " i.e. it should contain only values 0 and 1"
                   " (now the minimum is %d and maximum is %d)")
                 % (input_info['min'], input_info['max']))

    # computing pf values
    gs.info(_("Step 1: Computing Pf values..."))

    # let forested pixels be x and number of all pixels in moving window
    # be y, then pf=x/y"

    # generate grid with pixel-value=number of forest-pixels in window
    # generate grid with pixel-value=number of pixels in moving window:
    tmpA2 = tmpname('tmpA01_')
    tmpC3 = tmpname('tmpA02_')
    gs.run_command("r.neighbors", quiet=True, input=ipl,
                   output=[tmpA2, tmpC3], method=["sum", "count"], size=wz)

    # create pf map
    if user_pf:
        pf = user_pf
    else:
        pf = tmpname('tmpA03_')
    gs.mapcalc("$pf = if(" + ipl + ">=0, float($tmpA2) / float($tmpC3))", pf=pf,
               tmpA2=tmpA2, tmpC3=tmpC3)

    # computing pff values

    ## Considering pairs of pixels in cardinal directions in a 3x3 window, the total
    ## number of adjacent pixel pairs is 12. Assuming that x pairs include at least
    ## one forested pixel, and y of those pairs are forest-forest pairs, so pff equals
    ## y/x"

    gs.info(_("Step 2: Computing Pff values..."))

    # Create copy of forest map and convert NULL to 0 (if any)
    tmpC4 = tmpname('tmpA04_')
    gs.run_command("g.copy", raster=[ipl, tmpC4], quiet=True)
    gs.run_command("r.null", map=tmpC4, null=0, quiet=True)

    # calculate number of 'forest-forest' pairs

    # Compute matrix dimensions
    SWn= int((wz - 1) / 2)

    # Write mapcalc expression to tmpf - rows
    fd2, tmpfile2 = tempfile.mkstemp()
    tmpl4 = tmpname('tmpA05_')
    text_file = open(tmpfile2, "w")
    text_file.write(tmpl4 + " = ")

    # Write mapcalc expression to tmpf (rows and columns)
    rsub=range(SWn, -SWn-1, -1)
    csub=range(-SWn, SWn, 1)
    for k in rsub:
      for l in csub:
        text_file.write(tmpC4 + "[" + str(k) + "," + str(l) + "]*"
        + tmpC4 + "[" + str(k) + "," + str(l+1) + "] + ")
    rsub=range(-SWn, SWn+1, 1)
    csub=range(SWn, -SWn, -1)
    for k in rsub:
      for l in csub:
          text_file.write(tmpC4 + "[" + str(l) + "," + str(k) + "]*" + tmpC4
          + "[" + str(l-1) + "," + str(k) + "] + ")
    text_file.write("0")
    text_file.close()

    gs.run_command("r.mapcalc", file=tmpfile2)
    os.close(fd2)
    os.remove(tmpfile2)

    # number of 'forest patches

    fd3, tmpfile3 = tempfile.mkstemp()
    tmpl5 = tmpname('tmpA06_')
    text_file = open(tmpfile3, "w")
    text_file.write(tmpl5 + " = ")


    # Write mapcalc expression to tmpf - rows and columns
    rsub=range(SWn, -SWn-1, -1)
    csub=range(-SWn, SWn, 1)
    for k in rsub:
      for l in csub:
        text_file.write("if((" + tmpC4 + "[" + str(k) + "," + str(l) + "]+"
        + tmpC4 + "[" + str(k) + "," + str(l+1) + "])>0,1) + ")
    rsub=range(-SWn, SWn+1, 1)
    csub=range(SWn, -SWn, -1)
    for k in rsub:
      for l in csub:
          text_file.write("if((" + tmpC4 + "[" + str(l) + "," + str(k) + "]+"
        + tmpC4 + "[" + str(l-1) + "," + str(k) + "])>0,1) + ")
    text_file.write("0")
    text_file.close()

    gs.run_command("r.mapcalc", file=tmpfile3)
    os.close(fd3)
    os.remove(tmpfile3)

    # create pff map
    if user_pff:
        pff = user_pff
    else:
        pff = tmpname('tmpA07_')
    gs.mapcalc("$pff = if(" + ipl + " >= 0, float($tmpl4) / float($tmpl5))",
               tmpl4=tmpl4, tmpl5=tmpl5, pff=pff, quiet=True)

    # computing fragmentation index

    gs.info(_("Step 3: Computing fragmentation index..."))
    pf2 = tmpname('tmpA08_')
    gs.mapcalc("$pf2 = $pf - $pff", pf2=pf2, pf=pf, pff=pff, quiet=True)
    f1 = tmpname('tmpA09_') # patch
    gs.mapcalc("$f1 = if($pf<0.4,1,0)", f1=f1, pf=pf, quiet=True)
    f2 = tmpname('tmpA10_') # transitional
    gs.mapcalc("$f2 = if($pf>=0.4 && $pf<0.6,2,0)", pf=pf, f2=f2, quiet=True)
    f3 = tmpname('tmpA11_') # edge
    gs.mapcalc("$f3 = if($pf>=0.6 && $pf2<0,3,0)", pf=pf, pf2=pf2, f3=f3, quiet=True)
    f4 = tmpname('tmpA12_') # perforate
    gs.mapcalc("$f4 = if($pf>0.6 && $pf<1 && $pf2>0,4,0)", pf=pf, pf2=pf2, f4=f4, quiet=True)
    f5 = tmpname('tmpA13_') # interior
    gs.mapcalc("$f5 = if($pf==1,5,0)", pf=pf, pff=pff, f5=f5, quiet=True)
    f6 = tmpname('tmpA14_') # undetermined
    gs.mapcalc("$f6 = if($pf>0.6 && $pf<1 && $pf2==0,6,0)", pf=pf, pf2=pf2, pff=pff, f6=f6, quiet=True) # undetermined
    Index = tmpname('tmpA15_')
    gs.run_command("r.series", input=[f1,f2,f3,f4,f5,f6], output=Index,
                      method="sum", quiet=True)
    indexfin2 = tmpname('tmpA16_')
    gs.mapcalc("$if2 = $ipl * $Index",
               if2=indexfin2, ipl=ipl, Index=Index)

    #create categories
    indexfin3 =  tmpname('tmpA17_')
    fd4, tmprul = tempfile.mkstemp()
    text_file = open(tmprul, "w")
    text_file.write("0 = 0 nonforest\n")
    text_file.write("1 = 1 patch\n")
    text_file.write("2 = 2 transitional\n")
    text_file.write("3 = 3 edge\n")
    text_file.write("4 = 4 perforated\n")
    text_file.write("5 = 5 interior\n")
    text_file.write("6 = 6 undetermined\n")
    text_file.write("* = NULL\n")
    text_file.close()
    gs.run_command("r.reclass", quiet=True, input=indexfin2, output=indexfin3,
                   title="fragmentation index", rules=tmprul)
    os.close(fd4)
    os.remove(tmprul)

    # Shrink the region
    if flag_a:
        regionoriginal = tmpname('tmpA18_')
        gs.run_command("g.region", save=regionoriginal, quiet=True, overwrite=True)
        reginfo = gs.parse_command("g.region", flags="gp")
        NSCOR = SWn * float(reginfo['nsres'])
        EWCOR = SWn * float(reginfo['ewres'])
        gs.run_command("g.region",
                       n=float(reginfo['n'])-NSCOR,
                       s=float(reginfo['s'])+NSCOR,
                       e=float(reginfo['e'])-EWCOR,
                       w=float(reginfo['w'])+EWCOR,
                       quiet=True)
    gs.mapcalc("$opl = $if3", opl=opl, if3=indexfin3, quiet=True)

    #create color codes
    fd5, tmpcol = tempfile.mkstemp()
    text_file = open(tmpcol, "w")
    text_file.write("0 255:255:0\n")
    text_file.write("1 215:48:39\n")
    text_file.write("2 252:141:89\n")
    text_file.write("3 254:224:139\n")
    text_file.write("4 217:239:139\n")
    text_file.write("5 26:152:80\n")
    text_file.write("6 145:207:96\n")
    text_file.close()
    gs.run_command("r.colors", quiet=True, map=opl, rules=tmpcol)
    os.close(fd5)
    os.remove(tmpcol)

    # Write metadata for main layer
    gs.run_command("r.support", map=opl,
                   title="Forest fragmentation",
                   source1="Based on %s" % ipl,
                   source2="",  # to remove what r.recode creates
                   description="Forest fragmentation index (6 classes)")
    gs.raster_history(opl)

    # Write metadata for intermediate layers
    if user_pf:
        # pf layer
        gs.run_command("r.support", map=pf,
                       title="Proportion forested",
                       units="Proportion",
                       source1="Based on %s" % ipl,
                       description="Proportion of pixels in the moving window that is forested")
        gs.raster_history(pf)

    if user_pff:
        # pff layer
        fd8, tmphist = tempfile.mkstemp()
        text_file = open(tmphist, "w")
        text_file.write("Proportion of all adjacent (cardinal directions only) pixel pairs that\n")
        text_file.write("include at least one forest pixel for which both pixels are forested.\n")
        text_file.write("It thus (roughly) estimates the conditional probability that, given a\n")
        text_file.write("pixel of forest, its neighbor is also forest.")
        text_file.close()
        gs.run_command("r.support", map=pff,
                       title="Conditional probability neighboring cell is forest",
                       units="Proportion",
                       source1="Based on %s" % ipl,
                       description="Probability neighbor of forest cell is forest",
                       loadhistory=tmphist)
        gs.raster_history(pff)

    # Report fragmentation index and names of layers created

    if flag_s:
        gs.run_command("r.report", map=opl, units=["h", "p"],
                       flags="n", page_width=50, quiet=True)
    gs.info(_("The following layers were created"))
    gs.info(_("The fragmentation index: %s") % opl)
    if user_pf:
        gs.info(_("The proportion forested (pf): %s") % pf)
    if user_pff:
        gs.info(_("The proportion forested pixel pairs (pff): %s") % pff)

    # Clean up
    if flag_a:
        gs.run_command("g.region", region=regionoriginal, quiet=True, overwrite=True)


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
