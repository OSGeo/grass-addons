#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
#
# MODULE:       r.biodiversity
# AUTHOR(S):    Paulo van Breugel <p.vanbreugel AT gmail.com>
# PURPOSE:      Compute biodiversity indici over input layers
#
# COPYRIGHT: (C) 2014 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
#%Module
#% description: Compute biodiversity indici over input layers
#% keyword: raster
#% keyword: diversity index
#% keyword: renyi entrophy
#% keyword: shannon
#% keyword: simpson
#% keyword: richness
#% keyword: biodiversity
#% keyword: eveness
#%End

#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% description: input layers
#% label: input layers
#% key_desc: name
#% required: yes
#% multiple: yes
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: prefix name output layer
#% key_desc: name
#% required: yes
#% multiple: no
#%end

#%flag
#% key: r
#% description: Renyi enthropy index
#% guisection: Indices
#%end

#%option
#% key: alpha
#% type: double
#% description: Order of generalized entropy
#% key_desc: number(s)
#% multiple: yes
#% options: 0.0-*
#% guisection: Indices
#%end

#%rules
#% collective: -r,alpha
#%end

#%flag
#% key: s
#% description: Richness index
#% guisection: Indices
#%end

#%flag
#% key: h
#% description: Shannon index
#% guisection: Indices
#%end

#%flag
#% key: p
#% description: Reversed Simpson index
#% guisection: Indices
#%end

#%flag
#% key: g
#% description: Gini-Simpson index
#% guisection: Indices
#%end

#%flag
#% key: e
#% description: Pielou's evenness index
#% guisection: Indices
#%end

#%flag
#% key: n
#% description: Shannon effective number of species
#% guisection: Indices
#%end

#%rules
#% required: -r,-s,-h,-e,-p,-g,-n
#%end

#----------------------------------------------------------------------------
# Standard
#----------------------------------------------------------------------------

# import libraries
import os
import sys
import uuid
import atexit
import string
import grass.script as grass
if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

#----------------------------------------------------------------------------
# Functions
#----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()
def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove",
        type="rast", name = rast, quiet = True)

def CheckLayer(envlay):
    for chl in xrange(len(envlay)):
        ffile = grass.find_file(envlay[chl], element = 'cell')
        if ffile['fullname'] == '':
            grass.fatal("The layer " + envlay[chl] + " does not exist.")

# Create temporary name
def tmpname(name):
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.add(tmpf)
    return tmpf

#----------------------------------------------------------------------------
# main function
#----------------------------------------------------------------------------

def main():
    #options = {"input":"spec1,spec2,spec3,spec4,spec5", "output":"AAA9", "alpha":"4"}
    #flags = {"r":"False", "s":True, "h":True, "e":True, "p":True, "n":True, "g":True}

    #--------------------------------------------------------------------------
    # Variables
    #--------------------------------------------------------------------------

    # Layers
    OUT = options['output']
    IN = options['input']
    IN = IN.split(',')
    CheckLayer(IN)

    # Diversity indici
    flag_r = flags['r']
    flag_s = flags['s']
    flag_h = flags['h']
    flag_e = flags['e']
    flag_p = flags['p']
    flag_g = flags['g']
    flag_n = flags['n']
    if options['alpha']:
        Q = map(float, options['alpha'].split(','))
    else:
        Q = map(float, [])
    Qoriginal = list(Q)

    #--------------------------------------------------------------------------
    # Create list of what need to be computed
    #--------------------------------------------------------------------------
    if not flag_r:
        flag_r = []
    if flag_s and not 0.0 in Q:
        Q.append(0.0)
    if flag_h and not 1.0 in Q:
        Q.append(1.0)
    if flag_e and not 0.0 in Q:
        Q.append(0.0)
    if flag_e and not 1.0 in Q:
        Q.append(1.0)
    if flag_p and not 2.0 in Q:
        Q.append(2.0)
    if flag_g and not 2.0 in Q:
        Q.append(2.0)
    if flag_n and not 1.0 in Q:
        Q.append(1.0)

    #--------------------------------------------------------------------------
    # Renyi entropy
    #--------------------------------------------------------------------------
    tmpt = tmpname("sht")
    clean_rast.add(tmpt)
    grass.run_command("r.series", quiet=True, output=tmpt,
                      input=IN, method="sum")

    for n in xrange(len(Q)):

        Qn = str(Q[n])
        Qn = Qn.replace('.', '_')
        out_renyi = OUT + "_Renyi_" + Qn
        tmpl = []

        if Q[n] == 1:
            # If alpha = 1
            for i in xrange(len(IN)):
                tmpi = tmpname('shi' + str(i) + "_")
                tmpl.append(tmpi)
                clean_rast.add(tmpi)
                grass.mapcalc("$tmpi = ($inl/$tmpt) * log(($inl/$tmpt))",
                              tmpi=tmpi,
                              inl=IN[i],
                              tmpt=tmpt,
                              quiet=True)
            tmpta = tmpname("sht")
            clean_rast.add(tmpta)
            grass.run_command("r.series", output=tmpta, input=tmpl,
                                  method="sum", quiet=True)
            grass.mapcalc("$outl = -1 * $tmpta",
                              outl=out_renyi,
                              tmpta=tmpta,
                              overwrite=True,
                              quiet=True)
            grass.run_command("g.remove", type="raster",
                              name=tmpta, flags="f")
        else:
            # If alpha != 1
            for i in xrange(len(IN)):
                tmpi = tmpname('reni')
                tmpl.append(tmpi)
                grass.mapcalc("$tmpi = if($inl==0,0,pow($inl/$tmpt,$alpha))",
                              tmpi=tmpi,
                              tmpt=tmpt,
                              inl=IN[i],
                              alpha=Q[n],
                              quiet=True)
            tmpta = tmpname("sht")
            clean_rast.add(tmpta)
            grass.run_command("r.series", output=tmpta, input=tmpl,
                              method="sum", quiet=True)
            grass.mapcalc("$outl = (1/(1-$alpha)) * log($tmpta)",
                              outl=out_renyi,
                              tmpta=tmpta,
                              alpha=Q[n],
                              quiet=True)
            grass.run_command("g.remove", type="raster",
                              name=tmpta, flags="f", quiet=True)
        grass.run_command("g.remove", type="raster",
                          name=tmpl, flags="f", quiet=True)

    #--------------------------------------------------------------------------
    # Species richness
    #--------------------------------------------------------------------------
    if flag_s:
        out_div = OUT + "_richness"
        in_div = OUT + "_Renyi_0_0"
        grass.mapcalc("$out_div = exp($in_div)",
                      out_div=out_div,
                      in_div=in_div,
                      quiet=True)
        if 0.0 not in Qoriginal and not flag_e:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div, quiet=True)

    #--------------------------------------------------------------------------
    # Shannon index
    #--------------------------------------------------------------------------
    if flag_h:
        out_div = OUT + "_shannon"
        in_div = OUT + "_Renyi_1_0"
        if 1.0 in Qoriginal or flag_e or flag_n:
            grass.run_command("g.copy", raster=(in_div,out_div), quiet=True)
        else:
            grass.run_command("g.rename", raster=(in_div,out_div), quiet=True)

    #--------------------------------------------------------------------------
    # Shannon Effective Number of Species (ENS)
    #--------------------------------------------------------------------------
    if flag_n:
        out_div = OUT + "_ens"
        in_div = OUT + "_Renyi_1_0"
        grass.mapcalc("$out_div = exp($in_div)",
                      out_div=out_div,
                      in_div=in_div,
                      quiet=True)
        if 1.0 not in Qoriginal and not flag_e:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div, quiet=True)

    #--------------------------------------------------------------------------
    # Eveness
    #--------------------------------------------------------------------------
    if flag_e:
        out_div = OUT + "_eveness"
        in_div1 = OUT + "_Renyi_0_0"
        in_div2 = OUT + "_Renyi_1_0"
        grass.mapcalc("$out_div = $in_div2 / $in_div1",
                      out_div=out_div,
                      in_div1=in_div1,
                      in_div2=in_div2,
                      quiet=True)
        if 0.0 not in Qoriginal:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div1, quiet=True)
        if 1.0 not in Qoriginal:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div2, quiet=True)
    #--------------------------------------------------------------------------
    # Inversed Simpson index
    #--------------------------------------------------------------------------
    if flag_p:
        out_div = OUT + "_invsimpson"
        in_div = OUT + "_Renyi_2_0"
        grass.mapcalc("$out_div = exp($in_div)",
                      out_div=out_div,
                      in_div=in_div,
                      quiet=True)
        if 2.0 not in Qoriginal and not flag_g:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div, quiet=True)

    #--------------------------------------------------------------------------
    # Gini Simpson index
    #--------------------------------------------------------------------------
    if flag_g:
        out_div = OUT + "_ginisimpson"
        in_div = OUT + "_Renyi_2_0"
        grass.mapcalc("$out_div = 1.0 - (1.0 / exp($in_div))",
                      out_div=out_div,
                      in_div=in_div,
                      quiet=True)
        if 2.0 not in Qoriginal:
            grass.run_command("g.remove", flags="f", type="raster",
                              name=in_div, quiet=True)

    # Clean up temporary files
    grass.run_command("g.remove", type="raster", name=tmpt,
                      flags="f", quiet=True)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
