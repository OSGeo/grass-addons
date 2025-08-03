#!/usr/bin/env python


############################################################################
#
# MODULE:    r3.forestfrag
#
# AUTHOR(S): Vaclav Petras (3D, based on r.forestfrag, wenzeslaus gmail com)
#            Emmanuel Sambale (original shell version of r.forestfrag)
#            Stefan Sylla (original shell version of r.forestfrag)
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

# %module
# % description: Computes the forest fragmentation index (Riitters et al. 2000)
# % keyword: raster3d
# % keyword: landscape structure analysis
# % keyword: vegetation structure analysis
# % keyword: forest
# % keyword: fragmentation index
# % keyword: Riitters
# %end

# %option G_OPT_R3_INPUT
# % description: Name of forest raster map (where forest=1, non-forest=0)
# % required: yes
# %end

# %option G_OPT_R3_OUTPUT
# % required: yes
# %end

# %option
# % key: size
# % type: integer
# % description: Moving window size (odd number)
# % key_desc: number
# % options: 3-
# % answer : 3
# % required: yes
# %end

# %option G_OPT_R3_OUTPUT
# % key: pf
# % label: Name for output Pf (forest area density) raster map
# % description: Proportion of area which is forested (amount of forest)
# % required: no
# %end

# %option G_OPT_R3_OUTPUT
# % key: pff
# % label: Name for output Pff (forest connectivity) raster map
# % description: Conditional probability that neighboring cell is forest
# % required: no
# %end

# %option
# % key: transitional_limit
# % type: double
# % description: transitional_limit
# % answer: 0.6
# % required: yes
# %end

# %option
# % key: patch_limit
# % type: double
# % description: patch_limit
# % answer: 0.4
# % required: yes
# %end

# %option
# % key: interior_limit
# % type: double
# % description: interior_limit
# %end

# %option
# % key: color
# % type: string
# % label: Source raster for colorization
# % description: Input and color_input are taken from input and color_input options respectively. The rest is computed using r.slope.aspect
# % required: no
# % options: sambale,riitters,perceptual
# % descriptions: sambale;Sambale, Stefan Sylla;riitters; Riitters et. al 2000;perceptual;Perceptually uniform
# % answer: sambale
# %end

# %flag
# % key: r
# % description: Set computational region to input raster map
# %end

# %flag
# % key: t
# % description: Keep Pf and Pff maps
# %end

# %flag
# % key: a
# % description: Trim the output map to avoid border effects
# %end


import sys
import uuid
import atexit
import grass.script as gs

# neutral naming for better compatibility with 2D version
from grass.script.raster3d import mapcalc3d as mapcalc


COLORS_SAMBALE = """\
0 255:255:0
1 215:48:39
2 252:141:89
3 254:224:139
4 217:239:139
5 26:152:80
6 145:207:96
"""

COLORS_RIITTERS = """\
0 255:255:255
1 34:34:220
2 153:204:255
3 255:153:102
4 255:255:102
5 34:255:34
6 230:255:0
"""

COLORS_PERCEPTUAL = """\
0 245:244:68
1 35:60:37
2 172:92:80
3 192:126:73
4 157:182:90
5 107:214:72
6 195:233:82
"""

COLORS_PERCEPTUAL_WHITE = """\
0 255:255:255
1 172:92:80
2 192:126:73
3 157:182:90
4 245:244:68
5 107:214:72
6 195:233:82
"""


# create set to store names of temporary maps to be deleted upon exit
CLEAN_RAST = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="raster3d", name=rast, quiet=True)


def raster_exists(name):
    """Check if the raster map exists, call GRASS fatal otherwise"""
    ffile = gs.find_file(name, element="grid3")
    if not ffile["fullname"]:
        gs.fatal(_("Raster map <%s> not found") % name)


def tmpname(prefix):
    """Generate a tmp name which conatins prefix

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
    base_expr = "(int({m}[{a},{b},{c}]) {o} int({m}[{d},{e},{f}]))"
    expr = []
    for j in range(-s, s + 1):
        for k in range(-s, s + 1):
            for i in range(-s, s):
                expr.append(
                    base_expr.format(
                        m=map_name, o=combine_op, a=i, b=j, c=k, d=i + 1, e=j, f=k
                    )
                )
    for k in range(-s, s + 1):
        for i in range(-s, s + 1):
            for j in range(-s, s):
                expr.append(
                    base_expr.format(
                        m=map_name, o=combine_op, a=i, b=j, c=k, d=i, e=j + 1, f=k
                    )
                )
    for i in range(-s, s + 1):
        for j in range(-s, s + 1):
            for k in range(-s, s):
                expr.append(
                    base_expr.format(
                        m=map_name, o=combine_op, a=i, b=j, c=k, d=i, e=j, f=k + 1
                    )
                )
    return aggregate_op.join(expr)


def main(options, flags):
    # options and flags into variables
    ipl = options["input"]
    raster_exists(ipl)
    opl = options["output"]
    size = int(options["size"])
    if size % 2 == 0:
        gs.fatal("Please provide an odd number for the moving window")

    transitional_limit = float(options["transitional_limit"])
    patch_limit = float(options["patch_limit"])
    if patch_limit >= transitional_limit:
        gs.fatal("Patch limit must be lower than transitional limit")
    if options["interior_limit"]:
        interior_limit = float(options["interior_limit"])
    else:
        # we choose high value just to be sure
        float_epsilon = 2.0e-06
        interior_limit = float_epsilon
    if 1 - transitional_limit <= interior_limit:
        gs.fatal("Interior tolerance is too high or transitional limit is too high")
    # TODO: set those using flags
    interior_upper_test = False
    interior_circle_test = True
    interior_limit = "{:.7f}".format(interior_limit)
    # user wants pf or pff
    user_pf = options["pf"]
    user_pff = options["pff"]
    flag_r = flags["r"]
    clip_output = flags["a"]

    # set to current input map region if requested by the user
    # default is (and should be) the current region
    # we could use tmp region for this but if the flag is there
    # it makes sense to use it from now on (but we should reconsider)
    if flag_r:
        gs.message(_("Setting region to input map..."))
        gs.run_command("g.region", raster3d=ipl, quiet=True)

    # TODO: check if map values are limited to 1 and 0

    # computing pf values
    # let forested pixels be x and number of all pixels in moving window
    # be y, then pf=x/y"

    gs.info(_("Step 1: Computing Pf values..."))

    # create pf map
    if user_pf:
        pf = user_pf
    else:
        pf = tmpname("tmpA03_")
    gs.run_command(
        "r3.neighbors",
        input=ipl,
        output=pf,
        method="average",
        window=(size, size, size),
    )

    # computing pff values
    # Considering pairs of pixels in cardinal directions in
    # a 3x3 window, the total number of adjacent pixel pairs is 12.
    # Assuming that x pairs include at least one forested pixel, and
    # y of those pairs are forest-forest pairs, so pff equals y/x.

    gs.info(_("Step 2: Computing Pff values..."))

    # create copy of forest map and convert NULL to 0 (if any)
    tmpC4 = tmpname("tmpA04_")
    gs.run_command("g.copy", raster3d=[ipl, tmpC4], quiet=True)
    gs.run_command("r3.null", map=tmpC4, null=0, quiet=True)

    # window dimensions
    max_index = int((size - 1) / 2)
    # number of 'forest-forest' pairs
    expr1 = pairs_expression(map_name=tmpC4, max_index=max_index, combine_op="&")
    # number of 'nonforest-forest' pairs
    expr2 = pairs_expression(map_name=tmpC4, max_index=max_index, combine_op="|")
    # create pff map
    if user_pff:
        pff = user_pff
    else:
        pff = tmpname("tmpA07_")
    mapcalc("$pff = float($e1) / float($e2)", pff=pff, e1=expr1, e2=expr2)

    # computing fragmentation index
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

    # equation for the interior
    if interior_upper_test:
        # using abs just be be sure in case floating pf goes little bit over 1
        interior_eq = "abs($pf - 1) < $in_limit"
    elif interior_circle_test:
        interior_eq = "($pff - 1)^2 + ($pf - 1)^2 < $in_limit^2"
    else:
        interior_eq = "$pf == 1"

    if clip_output:
        indexfin2 = tmpname("tmpA16_")
    else:
        indexfin2 = opl
    expression = (
        "eval("
        "dpf = $pf - $pff,"
        "inter = " + interior_eq + ","  # using plus to avoid formating twice
        # individual classes
        "patch = if($pf < $pa_limit, 1, 0),"
        "transitional = if($pf >= $pa_limit && $pf < $tr_limit, 2, 0),"
        "edge = if($pf >= $tr_limit && not(inter) && dpf < 0, 3, 0),"
        "perforated = if($pf > $tr_limit && not(inter) && dpf > 0, 4, 0),"
        "interior = if(inter, 5, 0),"  # TODO: we could skip this
        "undetermined = if($pf > $tr_limit && not(inter) && dpf == 0, 6, 0),"
        # null is considered as non-forest and we need to do it before +
        "patch = if(isnull(patch), 0, patch),"
        "transitional = if(isnull(transitional), 0, transitional),"
        "edge = if(isnull(edge), 0, edge),"
        "perforated = if(isnull(perforated), 0, perforated),"
        "interior = if(isnull(interior), 0, interior),"
        "undetermined = if(isnull(undetermined), 0, undetermined),"
        # combine classes (they don't overlap)
        # more readable than nested ifs from the ifs above
        "all = patch + transitional + edge + perforated + interior"
        " + undetermined"
        ")\n"
        # mask result by non-forest (according to the input)
        # removes the nonsense data created in the non-forested areas
        "$out = all * $binary_forest"
    )
    gs.debug(expression)
    mapcalc(
        expression,
        out=indexfin2,
        binary_forest=ipl,
        pf=pf,
        pff=pff,
        tr_limit=transitional_limit,
        pa_limit=patch_limit,
        in_limit=interior_limit,
    )

    # TODO: create categories

    # create color table
    if options["color"] == "riitters":
        colors = COLORS_RIITTERS
    if options["color"] == "perceptual":
        colors = COLORS_PERCEPTUAL
    else:
        colors = COLORS_SAMBALE
    gs.write_command("r3.colors", map=opl, rules="-", stdin=colors, quiet=True)

    gs.info(_("The following layers were created"))
    gs.info(_("The fragmentation index: %s") % opl)
    if user_pf:
        gs.info(_("The proportion forested (Pf): %s") % pf)
    if user_pff:
        gs.info(_("The proportion forested pixel pairs (Pff): %s") % pff)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
