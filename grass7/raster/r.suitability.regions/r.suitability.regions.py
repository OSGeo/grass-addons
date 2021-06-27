#!/usr/bin/env python

############################################################################
# MODULE:         Locate suitable regions
# AUTHOR(S):      Paulo van Breugel
# PURPOSE:        From suitability map to suitable regions
# COPYRIGHT: (C) 2021 by Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
##############################################################################

#%module
#% description: From suitability map to suitable regions
#%end
#%option G_OPT_R_INPUT
#% key: suitrast
#% label: Suitability raster
#% description: Raster layer represting suitability (0-1)
#% required: yes
#% multiple: no
#% guisection: Input
#%end
#%option G_OPT_R_OUTPUT
#% key: suitreg
#% label: Output raster
#% description: Raster with candidate regions for conservation
#% required: yes
#% multiple: no
#% guisection: Input
#%end
#%option
#% key: minsuit
#% description: Threshold value above which areas are considered suitable
#% required: yes
#% type: string
#% answer: 0.7
#% key_desc: float
#% guisection: Input
#%end
#%option
#% key: minfrag
#% description: Minimum area (in hectares) limit for fragments
#% required: yes
#% type: string
#% answer: 1000
#% key_desc: float
#% guisection: Input
#%end
#%option
#% key: absminsuit
#% description: Threshold below which cells are marked as fully unsuitable
#% required: no
#% type: string
#% key_desc: float
#% guisection: Input
#%end

#%flag
#% key: d
#% label: Clumps including diagonal neighbors
#% description: Clumps including diagonal neighbors
#% guisection: Optional
#%end

#%option
#% key: radius
#% description: Radius for focal stat
#% required: no
#% type: integer
#% answer: 1
#% guisection: Focal stats
#%end
#%flag
#% key: c
#% label: Circular neighborhood
#% description: Use circular neighborhood for focal statistic
#% guisection: Focal stats
#%end
#%option
#% key: focalstat
#% description: Neighborhood operation (focal statistic)
#% required: no
#% type: string
#% answer: median
#% options:maximum,median,quart1,quart3
#% guisection: Focal stats
#%end

#%option
#% key: maxgap
#% description: Maximum gap size (in hectares) to remove
#% required: no
#% type: string
#% answer: 0
#% key_desc: float
#% guisection: Remove gaps
#%end

#%flag
#% key: z
#% label: Suitability per region
#% description: Compute map with average suitability per region
#% guisection: Reporting stats
#%end
#%flag
#% key: a
#% label: Calculates area of clumped areas (hectares)
#% description: Calculates area of clumped areas 
#% guisection: Reporting stats
#%end

#%flag
#% key: k
#% label: Keep map with all suitable cells
#% description: Keep map that show suitable areas (irrespective of clump size)
#% guisection: Optional
#%end

#%flag
#% key: f
#% label: Keep suitability based on focal statistics
#% description: Keep suitabiliyt based on focal statistics
#% guisection: Optional
#%end

import sys
import os
import atexit
import uuid
import grass.script as gs

RECLASSRULES1 = """\
1:filled gaps
2:suitable areas
"""
COLORRULES1 = """
1 230:230:230
""".strip()

COLORRULES2 = """
1 241:241:114
2 139:205:85
""".strip()


CLEAN_LAY = []
def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_LAY))
    for rast in cleanrast:
        ffile = gs.find_file(name=rast, element="cell", 
                              mapset=gs.gisenv()['MAPSET']) 
        if ffile['file']:
            gs.run_command("g.remove", flags="f", type="raster",
                            name=rast, quiet=True)

def tmpname(prefix):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = prefix + str(uuid.uuid4())
    tmpf = tmpf.replace('-', '_')
    CLEAN_LAY.append(tmpf)
    return tmpf

def tmpmask(input, absmin):
    """Create tmp mask"""
    rules="*:{}:1".format(absmin)
    tmprecode = tmpname("tmprecode")
    gs.write_command("r.recode", input=input, output=tmprecode, rule='-',
                   stdin=rules, quiet=True)
    return tmprecode

def main(options, flags):
    
    #Variables
    #options = {"suitrast":"habitat_suitability2", "absminsuit":'0',
    #           "radius":'3', "focalstat":"median", "minsuit":'0.7',
    #           "minfrag":'1000', "maxgap":'500',
    #           "suitreg":"tmp001"}
    #flags = {"c":True, "d":True, "r":False, "z":False, "k":True, "f":True}
    
    suitrast = options['suitrast']
    absminsuit = options['absminsuit']
    radius = int(options['radius'])
    if (radius % 2) == 0:
        gs.error("Radius should be an odd positive number")
    focalstat = options['focalstat']
    minsuit = float(options['minsuit'])
    minfrag = float(options['minfrag'])
    maxgap = float(options['maxgap'])
    suitreg = options['suitreg']
    
    # Flags
    flag_c = flags['c']
    if flag_c:
        c = "c"
    else:
        c = ""
    flag_d = flags['d']
    if flag_d:
        d = "d"
    else:
        d = ""
    flag_z = flags['z']
    flag_k = flags['k']
    flag_f = flags['f']
    flag_a = flags['a']
    
    # Temporary layer names
    tmp01 = tmpname("tmp01")
    tmp02 = tmpname("tmp02")
    tmp02a = tmpname("tmp02a")
    tmp03 = tmpname("tmp03")
    tmp04 = tmpname("tmp04")
    tmp05 = tmpname("tmp05")
    tmp06 = tmpname("tmp06")
    tmp07a = tmpname("tmp07a")
    tmp07 = tmpname("tmp07")
    tmp08 = tmpname("tmp08")
    xtralayer = "{}_filledgaps".format(suitreg)
   
    # Compute neighborhood statistic
    if (radius > 1) & (len(absminsuit) == 0):
        gs.message("Computing neighborhood statistic")
        gs.run_command("r.neighbors", flags=c, input=suitrast, quiet=True,
                       output=tmp02a, method=focalstat, size=radius)
        gs.run_command("r.series", input=[suitrast,tmp02a], 
                       method="maximum", output=tmp02)
    elif radius > 1:
        gs.message("Computing neighborhood statistic")
        try:
            float(absminsuit)
        except:
            gs.error("absminsuit must by numeric or left empty")
        gs.run_command("r.neighbors", flags=c, input=suitrast, quiet=True,
                       output=tmp01, method=focalstat, size=radius)
        gs.run_command("r.series", input=[suitrast,tmp01],
                       method="maximum", output=tmp02a)
        gs.run_command("r.mapcalc", quiet=True,
                        expression = ("{0} = if({1} > {2},{3},null())"
                                     .format(tmp02, suitrast, absminsuit,
                                             tmp02a)))       
    else:
        gs.run_command("g.copy", raster=[suitrast,tmp02], quiet=True)
            
    # Convert suitability to boolean: suitable (1) or not (nodata)   
    gs.message("Creating boolean map suitable/none-suitable")
    gs.run_command("r.mapcalc", quiet=True,
                    expression=("{} = if({} >= {},1,null())"
                                .format(tmp03, tmp02, minsuit)))
        
    # Clump contiguous cells (adjacent celss with same value) and 
    # remove clumps that are below user provided size
    gs.message("Clumping continuous cells and removing small fragments")
    gs.run_command("r.reclass.area", flags=d, input=tmp03, output=tmp04,
                   value=minfrag, mode="greater", method="reclass", 
                   quiet=True)
    
    # Remove gaps within suitable regions with size smaller than maxgap
    # Note, in the reclass.area module below mode 'greater' is used because
    # 1/nodata is reversed. The last step (clump) is to assign unique values
    # to the clumps, which makes it easier to filter and analyse results
    if maxgap > 0:
        gs.message("Removing small gaps of non-suitable areas - step 1")
        expr = ("{} = if(isnull({}),1,null())"
                .format(tmp05, tmp04))               
        gs.run_command("r.mapcalc", expression=expr, quiet=True)
        gs.message("Removing small gaps of non-suitable areas - step 2")
        gs.run_command("r.reclass.area", input=tmp05, output=tmp06,
                       value=maxgap, mode="greater", method="reclass",
                       quiet=True)  
        gs.message("Removing small gaps of non-suitable areas - step 3")
        expr3 = ("{} = int(if(isnull({}),1,null()))"
                           .format(tmp07a, tmp06))
        gs.run_command("r.mapcalc", expression=expr3, quiet=True)
        if len(absminsuit) > 0:
            bumask = tmpmask(input=suitrast, absmin=absminsuit)
            gs.run_command("r.mapcalc", 
                           expression=("{} = if(isnull({}), {},null())"
                           .format(tmp07, bumask, tmp07a)))
        else:
            gs.run_command("g.rename", raster=[tmp07a,tmp07])

        # Create map with category clump-suitable, clump-unsuitable
        gs.message("Create map with category clump-suitable, clump-unsuitable")
        gs.run_command("r.series", quiet=True, output=xtralayer,
                           input=[tmp04,tmp07], method="sum")
        gs.write_command("r.category", map=xtralayer, rules="-",
                         separator=":", stdin=RECLASSRULES1, quiet=True)
        
        # Assign unique ids to clumps
        gs.message("Assigning unique id's to clumps")
        gs.run_command("r.clump", flags=d, input=tmp07, output=suitreg,
                       quiet=True)
        gs.run_command("r.support", map=xtralayer, 
                       title="Regions + filled gaps", 
                       units="2 = suitable, 1 = filled gaps",
		               description=("Map indicating which cells of the",
			                "\nidentified regions are suitable, and",
			                "\nwhich are gaps included\n"))
        gs.write_command("r.colors", rules='-', map=xtralayer,
                       stdin=COLORRULES2, quiet=True)
        
    else:
        # Assign unique ids to clumps
        gs.message("Assigning unique id's to clumps")
        gs.run_command("r.clump", flags=d, input=tmp04, output=suitreg,
                       quiet=True)
    gs.run_command("r.support", map=suitreg,
			   title="Suitable regions",
               units="IDs of suitable regions",
               description=("Map with potential areas for conservation"
               "\n, Based on the suitability layer {}\n"
               .format(suitrast)))
    
    if flag_a:
        gs.message("Compute area per clump")
        areastat = "{}_clumpsize".format(suitreg)
        gs.run_command("r.area", input=suitreg, output=tmp08, quiet=True)
        gs.run_command("r.mapcalc", quiet=True,
                       expression=("{} = {} * area()/10000"
                                   .format(areastat, tmp08)))
        
    # Zonal statistics
    if flag_z:
        gs.message("Compute average suitability per clump")
        zonstat = "{}_averagesuitability".format(suitreg)
        gs.run_command("r.stats.zonal", base=suitreg, cover=suitrast, 
                       method="average", output=zonstat, quiet=True)
        gs.run_command("r.colors", map=zonstat, color="bgyr", quiet=True)
    gs.message("Done")
    
    # Keep map with all suitable areas
    if flag_k:
        rname = "{}_allsuitableareas".format(suitreg)
        gs.run_command("g.rename", raster=[tmp03,rname], quiet=True)
        gs.write_command("r.colors", rules='-', map=rname, stdin=COLORRULES1,
                       quiet=True)
    # Keep suitability map based on focal statistic
    if flag_f:
        rname2 = "{}_focalsuitability".format(suitreg)
        gs.run_command("g.rename", raster=[tmp02, rname2], quiet=True)
        gs.run_command("r.colors", map=rname2, raster=suitrast, quiet=True)
  
    
if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
