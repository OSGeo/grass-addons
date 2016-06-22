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
#% keyword: forest
#% keyword: fragmentation index
#% keyword: landscape structure analysis
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
import numpy as np
import uuid
import atexit
import tempfile
import string
import grass.script as grass

if not os.environ.has_key("GISBASE"):
    grass.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)

# create set to store names of temporary maps to be deleted upon exit
clean_rast = []


def cleanup():
    cleanrast = list(reversed(clean_rast))
    for rast in cleanrast:
        grass.run_command("g.remove", flags="f", type="rast", name=rast, quiet=True)

# Functions

def CheckLayer(envlay):
    ffile = grass.find_file(envlay, element = 'cell')
    if ffile['fullname'] == '':
        grass.fatal("The layer " + envlay + " does not exist.")

def tmpname(prefix):
    tmpf = prefix + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.append(tmpf)
    return tmpf

# Main

def main():
    # Variables
    ipl = options['input']
    CheckLayer(ipl)
    opl = options['output']
    wz  = int(options['window'])
    if wz % 2 == 0:
        grass.fatal("Please provide an odd number for the moving window")
    flag_r = flags['r']
    flag_t = flags['t']
    flag_s = flags['s']
    flag_a = flags['a']


    # set to current input map region (user option, default=current region)
    if flag_r:
        grass.message("Setting region to input map...")
        grass.run_command('g.region', quiet=True, raster=ipl)

    # Check if map values are limited to 1 and 0
    tmpdir = tempfile.mkdtemp()
    tmpfile = tmpdir + 'forestfrag1'
    grass.run_command("r.stats", flags="cn", overwrite=True,
                      quiet=True, input=ipl, output=tmpfile, separator="|")
    tstf = np.loadtxt(tmpfile, delimiter="|", dtype="int")
    os.remove(tmpfile)
    if min(tstf[:,0]) != 0 or max(tstf[:,0]) != 1:
        grass.fatal("Your input map must be binary, with values 0 and 1")

    # computing pf values
    grass.info("Step 1: Computing Pf values...")

    # let forested pixels be x and number of all pixels in moving window
    # be y, then pf=x/y"

    # generate grid with pixel-value=number of forest-pixels in window
    # generate grid with pixel-value=number of pixels in moving window:
    tmpA2 = tmpname('tmpA01_')
    tmpC3 = tmpname('tmpA02_')
    grass.run_command("r.neighbors", quiet=True, input=ipl,
                      output=[tmpA2, tmpC3], method=["sum", "count"], size=wz)

    # create pf map
    pf = tmpname('tmpA03_')
    grass.mapcalc("$pf = if(" + ipl + ">=0, float($tmpA2) / float($tmpC3))", pf=pf,
                  tmpA2=tmpA2, tmpC3=tmpC3, quiet=True)

    # computing pff values

    ## Considering pairs of pixels in cardinal directions in a 3x3 window, the total
    ## number of adjacent pixel pairs is 12. Assuming that x pairs include at least
    ## one forested pixel, and y of those pairs are forest-forest pairs, so pff equals
    ## y/x"

    grass.info("Step 2: Computing Pff values...")

    # Create copy of forest map and convert NULL to 0 (if any)
    tmpC4 = tmpname('tmpA04_')
    grass.run_command("g.copy", raster=[ipl, tmpC4], quiet=True)
    grass.run_command("r.null", map=tmpC4, null=0, quiet=True)

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

    grass.run_command("r.mapcalc", file=tmpfile2, quiet=True)
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

    grass.run_command("r.mapcalc", file=tmpfile3, quiet=True)
    os.close(fd3)
    os.remove(tmpfile3)

    # create pff map

    pff = tmpname('tmpA07_')
    grass.mapcalc("$pff = if(" + ipl + " >= 0, float($tmpl4) / float($tmpl5))", tmpl4=tmpl4,
                  tmpl5=tmpl5, pff=pff,quiet=True)

    # computing fragmentation index

    grass.info("Step 3: Computing fragmentation index...")
    pf2 = tmpname('tmpA08_')
    grass.mapcalc("$pf2 = $pf - $pff", pf2=pf2, pf=pf, pff=pff, quiet=True)
    f1 = tmpname('tmpA09_') # patch
    grass.mapcalc("$f1 = if($pf<0.4,1,0)", f1=f1, pf=pf, quiet=True)
    f2 = tmpname('tmpA10_') # transitional
    grass.mapcalc("$f2 = if($pf>=0.4 && $pf<0.6,2,0)", pf=pf, f2=f2, quiet=True)
    f3 = tmpname('tmpA11_') # edge
    grass.mapcalc("$f3 = if($pf>=0.6 && $pf2<0,3,0)", pf=pf, pf2=pf2, f3=f3, quiet=True)
    f4 = tmpname('tmpA12_') # perforate
    grass.mapcalc("$f4 = if($pf>0.6 && $pf<1 && $pf2>0,4,0)", pf=pf, pf2=pf2, f4=f4, quiet=True)
    f5 = tmpname('tmpA13_') # interior
    grass.mapcalc("$f5 = if($pf==1,5,0)", pf=pf, pff=pff, f5=f5, quiet=True)
    f6 = tmpname('tmpA14_') # undetermined
    grass.mapcalc("$f6 = if($pf>0.6 && $pf<1 && $pf2==0,6,0)", pf=pf, pf2=pf2, pff=pff, f6=f6, quiet=True) # undetermined
    Index = tmpname('tmpA15_')
    grass.run_command("r.series", input=[f1,f2,f3,f4,f5,f6], output=Index,
                      method="sum", quiet=True)
    indexfin2 = tmpname('tmpA16_')
    grass.mapcalc("$if2 = $ipl * $Index", if2=indexfin2, ipl=ipl,
                           Index=Index, quiet=True)

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
    grass.run_command("r.reclass", quiet=True, input=indexfin2, output=indexfin3,
                      title="fragmentation index", rules=tmprul)
    os.close(fd4)
    os.remove(tmprul)

    # Shrink the region
    if flag_a:
        regionoriginal = tmpname('tmpA18_')
        grass.run_command("g.region", save=regionoriginal, quiet=True, overwrite=True)
        reginfo = grass.parse_command("g.region", flags="gp")
        NSCOR = SWn * float(reginfo['nsres'])
        EWCOR = SWn * float(reginfo['ewres'])
        grass.run_command("g.region",
                          n=float(reginfo['n'])-NSCOR,
                          s=float(reginfo['s'])+NSCOR,
                          e=float(reginfo['e'])-EWCOR,
                          w=float(reginfo['w'])+EWCOR,
                          quiet=True)
    grass.mapcalc("$opl = $if3", opl=opl, if3=indexfin3, quiet=True)

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
    grass.run_command("r.colors", quiet=True, map=opl, rules=tmpcol)
    os.close(fd5)
    os.remove(tmpcol)

    # Function call
    if flag_r:rflag="\n\t-r"
    else: rflag=""
    if flag_t: tflag="\n\t-t"
    else: tflag=""
    if flag_s: sflag="\n\t-s"
    else: sflag=""
    if flag_a: aflag="\n\t-a"
    else: aflag=""
    desctxt = "r.forestfrag \n\tinput=" + ipl + "\n\toutput=" + opl + \
            "\n\twindow=" + str(wz) + rflag + tflag + sflag + aflag

    # Write metadata for main layer
    fd6, tmphist = tempfile.mkstemp()
    text_file = open(tmphist, "w")
    text_file.write("Forest fragmentation index (6 classes) following Riiters et al. (2000)\n\
\t(1) patch\n\t(2) transitional\n\t(3) edge\n\t(4) perforated\n\t(5) interior\n\t(6) undetermined\n")
    text_file.write("\ncreated using:\n")
    text_file.write(desctxt)
    text_file.close()
    grass.run_command("r.support", map=opl, title="Forest fragmentation",
                      units="Fragmentation classes (6)",
                      source1="based on " + ipl,
                      source2="",
                      description="Forst fragmentation index (6 classes)",
                      loadhistory=tmphist)
    os.close(fd6)
    os.remove(tmphist)

    # Write metadata for intermediate layers
    if flag_t:
        # pf layer
        fd7, tmphist = tempfile.mkstemp()
        text_file = open(tmphist, "w")
        text_file.write("created using:\n")
        text_file.write(desctxt + "\n")
        text_file.close()
        grass.run_command("r.support", map=pf,
                          title="Proportion forested",
                          units="Proportion",
                          source1="based on " + ipl,
                          source2="",
                          description="Proportion of pixels in the moving window that is forested",
                          loadhistory=tmphist)
        os.close(fd7)
        os.remove(tmphist)

        # pff layer
        fd8, tmphist = tempfile.mkstemp()
        text_file = open(tmphist, "w")
        text_file.write("created using:\n")
        text_file.write(desctxt + "\n\n")
        text_file.write("Proportion of all adjacent (cardinal directions only) pixel pairs that\n")
        text_file.write("include at least one forest pixel for which both pixels are forested.\n")
        text_file.write("It thus (roughly) estimates the conditional probability that, given a\n")
        text_file.write("pixel of forest, its neighbor is also forest")
        text_file.close()
        grass.run_command("r.support", map=pff,
                          title="Conditional probability neighboring cell is forest",
                          units="Proportion",
                          source1="based on " + ipl,
                          source2="",
                          description="Probability neighbor of forest cell is forest",
                          loadhistory=tmphist)
        os.close(fd8)
        os.remove(tmphist)

    # Report fragmentation index and names of layers created

    if flag_s:
        grass.run_command("r.report", map=opl, units=["h","p"],
                          flags="n", page_width=50, quiet=True)
    grass.info("\n")
    grass.info("The following layers were created\n")
    grass.info("The fragmentation index: " + opl +"\n")
    if flag_t:
        grass.run_command("g.rename", quiet=True, raster=[pf,opl + "_pf"])
        grass.run_command("g.rename", quiet=True, raster=[pff,opl + "_pff"])
        grass.info("The proportion forested (pf): " + opl + "_pf\n")
        grass.info("The proportion forested pixel pairs: " + opl + "_pff\n")
        clean_rast.remove(pf)
        clean_rast.remove(pff)

    # Clean up
    if flag_a:
        grass.run_command("g.region", region=regionoriginal, quiet=True, overwrite=True)
    os.removedirs(tmpdir)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
