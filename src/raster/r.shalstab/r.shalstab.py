#!/usr/bin/env python

##############################################################################
#
# MODULE:      r.shalstab
# VERSION:     1.0
# AUTHOR(S):   Andrea Filipello & Daniele Strigaro
# PURPOSE:     A model based on the algorithm developet by Montgomery and Dietrich (1994)
# COPYRIGHT:   (C) 2013 by Andrea Filipello & Daniele Strigaro
#              andrea.filipello@gmail.com; daniele.strigaro@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
##############################################################################

# %module
# % description: A model for shallow landslide susceptibility.
# % keyword: raster
# % keyword: critical rainfall
# % keyword: landslide
# %end
# %option
# % key: dem
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Name of input elevation raster map
# % required: yes
# %end
# %option
# % key: phy
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Soil friction angle (angle)
# % required: yes
# %end
# %option
# % key: c_soil
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Soil cohesion (N/m^2)
# % required: yes
# %end
# %option
# % key: gamma
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Soil density(Kg/m^3)
# % required: yes
# %end
# %option
# % key: z
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Vertical thickness of soil (m)
# % required: yes
# %end
# %option
# % key: k
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: hydraulic conductivity (m/h)
# % required: yes
# %end
# %option
# % key: root
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: name
# % description: Root cohesion k (N/m^2)
# % required: no
# %end
##############################################################################
# output
##############################################################################
# %option
# % key: susceptibility
# % type: string
# % gisprompt: new,cell,raster
# % key_desc: susceptibility
# % description: Name for output landslide susceptibility map (from 1 to 7)
# % required : yes
# %end
# %option
# % key: critic_rain
# % type: string
# % gisprompt: new,cell,raster
# % key_desc: critical rain
# % description: Name for output critical rainfall map (mm/day)
# % required : yes
# %END

import sys
import os

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass
    except:
        sys.exit("grass.script can't be imported.")


def main():
    r_elevation = options["dem"].split("@")[0]
    mapname = options["dem"].replace("@", " ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".", "_")
    c_soil = options["c_soil"]
    phy = options["phy"]
    gamma = options["gamma"]
    # gamma_wet = options['gamma_wet']
    z = options["z"]
    # b = options['b']
    k = options["k"]
    root = options["root"]
    susceptibility = options["susceptibility"]
    critic_rain = options["critic_rain"]
    if root == "":
        root = 0
    # if gamma_wet == '':
    #    gamma_wet = 2100
    # calculate slope
    grass.run_command(
        "r.slope.aspect",
        elevation=r_elevation,
        slope="slopes",
        min_slope=0.0,
        overwrite="True",
    )
    # zero value = null
    grass.run_command("r.null", map="slopes", setnull=0)
    # calculate soil transmissivity T (m^2/day)
    grass.mapcalc("T=$k*24*$z*cos(slopes)", k=k, z=z)
    # calculate dimensionless
    grass.mapcalc(
        "C=($root+$c_soil)/($z*cos(slopes)*9.81*$gamma)",
        root=root,
        c_soil=c_soil,
        z=z,
        gamma=gamma,
    )
    # calculate contribution area
    grass.run_command("r.watershed", elevation=r_elevation, accumulation="accum")

    grass.mapcalc("A=abs(accum*((ewres()+nsres())/2)*((ewres()+nsres())/2))")
    # stable condition
    grass.mapcalc("assoluta_stab=(1-1000/($gamma))*tan($phy)", gamma=gamma, phy=phy)
    grass.mapcalc("assoluta_cond=if(assoluta_stab>tan(slopes),9999,0)")
    # unstable condition
    grass.mapcalc("assoluta_instab=C/cos(slopes)+(tan($phy))", phy=phy)
    grass.mapcalc("cond_instab=if(assoluta_instab<tan(slopes),-9999,0)")
    # calculate 1(m/day)
    grass.mapcalc(
        "i_crit_m=T*sin(slopes)*(((ewres()+nsres())/2)/A)*($gamma/1000*(1-(1-(C/(sin(slopes))))*(tan(slopes)/tan($phy))))+(assoluta_cond)+(cond_instab)",
        phy=phy,
        gamma=gamma,
    )
    # Calculation of critical rain (mm / hr) and riclassification
    grass.mapcalc("i_cri_mm=i_crit_m*1000")
    # grass.mapcalc("i_cri_mm_reclass=if(i_cri_mm<0, 0, if(i_cri_mm>))")
    grass.run_command("r.colors", map="i_cri_mm", color="precipitation")
    reclass_rules = "0 thru 30 = 2\n31 thru 100 = 3\n101 thru 150 = 4\n151 thru 200 = 5\n201 thru 999 = 6"
    grass.write_command(
        "r.reclass",
        input="i_cri_mm",
        output="i_recl",
        overwrite="True",
        rules="-",
        stdin=reclass_rules,
    )
    grass.mapcalc("copia_reclass=i_recl+0")
    grass.run_command("r.null", map="copia_reclass", null=0)
    grass.mapcalc("Stable=if(i_cri_mm>1000,7,0)")
    grass.mapcalc("Unstable=if(i_cri_mm<0,1,0)")
    grass.mapcalc("Icritica=copia_reclass+Unstable+Stable")
    colors_rules = (
        "1 255:85:255\n2 255:0:0\n3 255:170:0\n4 255:255:0\n"
        "5 85:255:0\n6 170:255:255\n7 255:255:255"
    )
    grass.write_command(
        "r.colors", map="Icritica", rules="-", stdin=colors_rules, quiet=True
    )

    grass.run_command(
        "r.neighbors",
        input="Icritica",
        method="average",
        size=3,
        output="I_cri_average",
    )
    # rename maps
    grass.run_command("g.rename", raster=("I_cri_average", susceptibility))
    grass.run_command("g.rename", raster=("i_cri_mm", critic_rain))
    # remove temporary map
    grass.run_command(
        "g.remove",
        flags="f",
        type="raster",
        name=(
            "A",
            "copia_reclass",
            "i_crit_m",
            "i_recl",
            # "i_cri_mm",
            "accum",
            "slopes",
            "Stable",
            "T",
            "Unstable",
            "C",
            "Icritica",
            "assoluta_stab",
            "assoluta_cond",
            "assoluta_instab",
            "cond_instab",
        ),
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
