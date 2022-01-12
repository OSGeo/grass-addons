#!/usr/bin/env python


############################################################################
#
# MODULE:    r.forestfrag
#
# AUTHOR(S): Emmanuel Sambale (original shell version)
#            Stefan Sylla (original shell version)
#            Paulo van Breugel (Python version, paulo at ecodiv dot earth)
#            Vaclav Petras (major code clean up, wenzeslaus gmail com)
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
#% key: size
#% type: integer
#% description: Moving window size (odd number)
#% key_desc: number
#% options: 3-
#% answer : 3
#% required: no
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

#%option
#% key: window
#% type: integer
#% label: This option is deprecated, use the option size instead
#% options: 3-
#% required: no
#%end

import os
import sys
import uuid
import atexit
import tempfile
import grass.script as gs

# Neutral naming for better compatibility between 2D and 3D version
from grass.script.raster import mapcalc


LABELS = """\
0 exterior
1 patch
2 transitional
3 edge
4 perforated
5 interior
6 undetermined
"""

COLORS_SAMBALE = """\
0 255:255:0
1 215:48:39
2 252:141:89
3 254:224:139
4 217:239:139
5 26:152:80
6 145:207:96
"""

# Create set to store names of temporary maps to be deleted upon exit
CLEAN_RAST = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="raster", name=rast, quiet=True)


def raster_exists(name):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    ffile = gs.find_file(name, element="cell")
    if not ffile["fullname"]:
        gs.fatal(_("Raster map <%s> not found") % name)


def tmpname(prefix):
    """Generate a tmp name which contains prefix

    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = prefix + str(uuid.uuid4())
    tmpf = tmpf.replace("-", "_")
    CLEAN_RAST.append(tmpf)
    return tmpf


def pairs_expression(map_name, max_index, combine_op, aggregate_op="+"):
    """Generate window (matrix) expression

    :param map_name: name of the map to index
    :param max_index: the maximum positive index to use;
                      usually (window_size - 1) / 2
    :param combine_op: operator used to combine values in the pair
    :param aggregate_op: operator used to combine all pairs together
    """
    s = max_index  # just to be brief
    base_expr = "({m}[{a},{b}] {o} {m}[{c},{d}])"
    expr = []
    for j in range(-s, s + 1):
        for i in range(-s, s):
            expr.append(
                base_expr.format(m=map_name, o=combine_op, a=i, b=j, c=i + 1, d=j)
            )
    for i in range(-s, s + 1):
        for j in range(-s, s):
            expr.append(
                base_expr.format(m=map_name, o=combine_op, a=i, b=j, c=i, d=j + 1)
            )
    return aggregate_op.join(expr)


def main(options, flags):
    # Options and flags into variables
    ipl = options["input"]
    raster_exists(ipl)
    opl = options["output"]
    # Size option backwards compatibility with window
    if not options["size"] and not options["window"]:
        gs.fatal(_("Required parameter <%s> not set") % "size")
    if options["size"]:
        wz = int(options["size"])
    if options["window"]:
        gs.warning(_("The window option is deprecated, use the option" " size instead"))
        wz = int(options["window"])
    if options["size"] and options["size"] != "3" and options["window"]:
        gs.warning(
            _(
                "When the obsolete window option is used, the"
                " new size option is ignored"
            )
        )
    if wz % 2 == 0:
        gs.fatal(
            _("Please provide an odd number for the moving" " window size, not %d") % wz
        )
    # User wants pf or pff
    user_pf = options["pf"]
    user_pff = options["pff"]
    # Backwards compatibility
    if flags["t"]:
        gs.warning(_("The -t flag is deprecated, use pf and pff options" " instead"))
    if not user_pf and not user_pff and flags["t"]:
        user_pf = opl + "_pf"
        user_pff = opl + "_pff"
    elif flags["t"]:
        gs.warning(_("When pf or pff option is used, the -t flag" " is ignored"))
    flag_r = flags["r"]
    flag_s = flags["s"]
    clip_output = flags["a"]

    # Set to current input map region if requested by the user
    # Default is (and should be) the current region
    # We could use tmp region for this but if the flag is there
    # it makes sense to use it from now on (but we should reconsider)
    if flag_r:
        gs.message(_("Setting region to input map..."))
        gs.run_command("g.region", raster=ipl, quiet=True)

    # Check if map values are limited to 1 and 0
    input_info = gs.raster_info(ipl)
    # We know what we are doing only when input is integer
    if input_info["datatype"] != "CELL":
        gs.fatal(_("The input raster map must have type CELL" " (integer)"))
    # For integer, we just need to text min and max
    if input_info["min"] != 0 or input_info["max"] != 1:
        gs.fatal(
            _(
                "The input raster map must be a binary raster,"
                " i.e. it should contain only values 0 and 1"
                " (now the minimum is %d and maximum is %d)"
            )
            % (input_info["min"], input_info["max"])
        )

    # Computing pf values
    # Let forested pixels be x and number of all pixels in moving window
    # be y, then pf=x/y"

    gs.info(_("Step 1: Computing Pf values..."))

    # Generate grid with pixel-value=number of forest-pixels in window
    # Generate grid with pixel-value=number of pixels in moving window:
    tmpA2 = tmpname("tmpA01_")
    tmpC3 = tmpname("tmpA02_")
    gs.run_command(
        "r.neighbors",
        quiet=True,
        input=ipl,
        output=[tmpA2, tmpC3],
        method=["sum", "count"],
        size=wz,
    )

    # Create pf map
    if user_pf:
        pf = user_pf
    else:
        pf = tmpname("tmpA03_")
    mapcalc(
        "$pf = if( $ipl >=0, float($tmpA2) / float($tmpC3))",
        ipl=ipl,
        pf=pf,
        tmpA2=tmpA2,
        tmpC3=tmpC3,
    )

    # Computing pff values
    # Considering pairs of pixels in cardinal directions in
    # a 3x3 window, the total number of adjacent pixel pairs is 12.
    # Assuming that x pairs include at least one forested pixel, and
    # y of those pairs are forest-forest pairs, so pff equals y/x.

    gs.info(_("Step 2: Computing Pff values..."))

    # Create copy of forest map and convert NULL to 0 (if any)
    tmpC4 = tmpname("tmpA04_")
    gs.run_command("g.copy", raster=[ipl, tmpC4], quiet=True)
    gs.run_command("r.null", map=tmpC4, null=0, quiet=True)

    # Window dimensions
    max_index = int((wz - 1) / 2)
    # Number of 'forest-forest' pairs
    expr1 = pairs_expression(map_name=tmpC4, max_index=max_index, combine_op="&")
    # Number of 'nonforest-forest' pairs
    expr2 = pairs_expression(map_name=tmpC4, max_index=max_index, combine_op="|")
    # Create pff map
    if user_pff:
        pff = user_pff
    else:
        pff = tmpname("tmpA07_")
    # Potentially this can be split and parallelized
    mapcalc(
        "$pff = if($ipl >= 0, float($tmpl4) / float($tmpl5))",
        ipl=ipl,
        tmpl4=expr1,
        tmpl5=expr2,
        pff=pff,
    )

    # Computing fragmentation index
    # (a b) name, condition
    # where a is a number used by Riitters et al. in ERRATUM (2)
    # and b is a number used in the sh script by Sambale and Sylla
    # b also defines 0 for non-forested which is consistent with input
    # (1 3) edge, if Pf > 0.6 and Pf - Pff < 0
    # (2 6) undetermined, if Pf > 0.6 and Pf = Pff
    # (3 4) perforated, if Pf > 0.6 and Pf - Pff > 0
    # (4 5) interior, if Pf = 1.0
    # (5 1) patch, if Pf < 0.4
    # (6 2) transitional, if 0.4 < Pf < 0.6

    gs.info(_("Step 3: Computing fragmentation index..."))

    if clip_output:
        indexfin2 = tmpname("tmpA16_")
    else:
        indexfin2 = opl
    mapcalc(
        "eval(" "dpf = $pf - $pff,"
        # Individual classes
        "patch = if($pf < 0.4, 1, 0),"
        "transitional = if($pf >= 0.4 && $pf < 0.6, 2, 0),"
        "edge = if($pf >= 0.6 && dpf<0,3,0),"
        "perforated = if($pf > 0.6 && $pf < 1 && dpf > 0, 4, 0),"
        "interior = if($pf == 1, 5, 0),"
        "undetermined = if($pf > 0.6 && $pf < 1 && dpf == 0, 6, 0),"
        # null is considered as non-forest and we need to do it before +
        "patch = if(isnull(patch), 0, patch),"
        "transitional = if(isnull(transitional), 0, transitional),"
        "edge = if(isnull(edge), 0, edge),"
        "perforated = if(isnull(perforated), 0, perforated),"
        "interior = if(isnull(interior), 0, interior),"
        "undetermined = if(isnull(undetermined), 0, undetermined),"
        # Combine classes (they don't overlap)
        # more readable than nested ifs from the ifs above
        "all = patch + transitional + edge + perforated + interior"
        " + undetermined"
        ")\n"
        # Mask result by non-forest (according to the input)
        # Removes the nonsense data created in the non-forested areas
        "$out = all * $binary_forest",
        out=indexfin2,
        binary_forest=ipl,
        pf=pf,
        pff=pff,
    )

    # Shrink the region
    if clip_output:
        gs.use_temp_region()
        reginfo = gs.parse_command("g.region", flags="gp")
        nscor = max_index * float(reginfo["nsres"])
        ewcor = max_index * float(reginfo["ewres"])
        gs.run_command(
            "g.region",
            n=float(reginfo["n"]) - nscor,
            s=float(reginfo["s"]) + nscor,
            e=float(reginfo["e"]) - ewcor,
            w=float(reginfo["w"]) + ewcor,
            quiet=True,
        )
        mapcalc("$opl = $if3", opl=opl, if3=indexfin2, quiet=True)

    # Create categories
    # TODO: parametrize classes (also in r.mapcalc, r.colors and desc)?
    # TODO: translatable labels?
    labels = LABELS
    gs.write_command(
        "r.category", quiet=True, map=opl, rules="-", stdin=labels, separator="space"
    )

    # create color table
    colors = COLORS_SAMBALE
    gs.write_command("r.colors", map=opl, rules="-", stdin=colors, quiet=True)

    # write metadata for main layer
    gs.run_command(
        "r.support",
        map=opl,
        title="Forest fragmentation",
        source1="Based on %s" % ipl,
        description="Forest fragmentation index (6 classes)",
    )
    gs.raster_history(opl)

    # write metadata for intermediate layers
    if user_pf:
        # pf layer
        gs.run_command(
            "r.support",
            map=pf,
            title="Proportion forested",
            units="Proportion",
            source1="Based on %s" % ipl,
            description="Proportion of pixels in the moving" " window that is forested",
        )
        gs.raster_history(pf)

    if user_pff:
        # pff layer
        unused, tmphist = tempfile.mkstemp()
        text_file = open(tmphist, "w")
        long_description = """\
Proportion of all adjacent (cardinal directions only) pixel pairs that
include at least one forest pixel for which both pixels are forested.
It thus (roughly) estimates the conditional probability that, given a
pixel of forest, its neighbor is also forest.
"""
        text_file.write(long_description)
        text_file.close()
        gs.run_command(
            "r.support",
            map=pff,
            title="Conditional probability neighboring cell" " is forest",
            units="Proportion",
            source1="Based on %s" % ipl,
            description="Probability neighbor of forest cell" " is forest",
            loadhistory=tmphist,
        )
        gs.raster_history(pff)
        os.remove(tmphist)

    # report fragmentation index and names of layers created

    if flag_s:
        gs.run_command(
            "r.report", map=opl, units=["h", "p"], flags="n", page_width=50, quiet=True
        )

    gs.info(_("The following layers were created"))
    gs.info(_("The fragmentation index: %s") % opl)
    if user_pf:
        gs.info(_("The proportion forested (Pf): %s") % pf)
    if user_pff:
        gs.info(_("The proportion forested pixel pairs (Pff): %s") % pff)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
