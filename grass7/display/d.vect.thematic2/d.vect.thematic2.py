#!/usr/bin/env python

############################################################################
#
# MODULE:       d.vect.thematic2
# AUTHOR(S):	Michael Barton, Arizona State University with contributions
#               by Martin Landa, Jachym Cepicky, Daniel Calvelo Aros and Moritz Lennert
# PURPOSE:	    Displays thematic vector map with graduated colors
#               or graduated points and line thickneses
# COPYRIGHT:	(C) 2006-2014 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################


#%module
#% description: Displays thematic map created from vector features and numeric attributes.
#% keyword: display
#% keyword: cartography
#% keyword: vector
#% keyword: thematic
#% keyword: legend
#%end
#%option G_OPT_V_MAP
#%end
#%option G_OPT_V_FIELD
#%end
#%option G_OPT_DB_COLUMN
#% description: Name of attribute column to use for thematic display (must be numeric)
#% required: yes
#%end
#%option G_OPT_V_TYPE
#%answer: point,line,area
#%end
#%option G_OPT_DB_WHERE
#% guisection: Theme
#%end
#%option
#% key: themetype
#% type: string
#% options: graduated_colors,graduated_points,graduated_lines
#% answer: graduated_colors
#% description: Type of thematic display
#% required: yes
#% guisection: Theme
#%end
#%option
#% key: themecalc
#% type: string
#% options: interval,std_deviation,quartiles,custom_breaks
#% answer: interval
#% description: Thematic divisions of data for display
#% required: yes
#% guisection: Theme
#%end
#%option
#% key: breakpoints
#% type: string
#% label: Break points for custom breaks option
#% description: Separate values by spaces (0 10 20 30 ...)
#% required: no
#% guisection: Theme
#%end
#%option
#% key: icon
#% type: string
#% description: Vector point icon for point data
#% options: basic/box,basic/circle,basic/cross2,basic/diamond,basic/star,basic/cross1,basic/x
#% answer: basic/circle
#% required: no
#% guisection: Points
#%end
#%option
#% key: size
#% type: double
#% label: Icon size for point data
#% description: Minimum icon size/line width for graduated points/lines)
#% answer: 5
#% required: no
#% guisection: Points
#%end
#%option
#% key: maxsize
#% type: double
#% description: Maximum icon size/line width for graduated points and lines
#% answer: 20
#% required: no
#% guisection: Points
#%end
#%option
#% key: nint
#% type: integer
#% description: Number of classes for interval theme (integer)
#% answer: 4
#% required: no
#% guisection: Theme
#%end
#%option
#% key: colorscheme
#% type: string
#% label: Color scheme for graduated color mapping
#% description: Select 'single_color' for graduated point/line display
#% options: blue-red,red-blue,green-red,red-green,blue-green,green-blue,cyan-yellow,yellow-cyan,custom_gradient,single_color
#% answer: blue-red
#% required: yes
#% guisection: Color
#%end
#% option
#% key: point_color
#% type: string
#% label: Color for graduated points map
#% description: GRASS named color or R:G:B triplet. Set color scheme to single color
#% answer: 255:0:0
#% required: no
#% guisection: Color
#%end
#% option
#% key: line_color
#% type: string
#% label: Color for graduated lines or point/area outlines
#% description: GRASS named color or R:G:B triplet. Set color scheme to single color.
#% answer: 0:0:0
#% required: no
#% guisection: Color
#%end
#% option
#% key: start_color
#% type: string
#% label: Beginning color for custom color gradient
#% description: Must be expressed as R:G:B triplet
#% answer: 255:0:0
#% required: no
#% guisection: Color
#%end
#% option
#% key: end_color
#% type: string
#% label: Ending color for custom color gradient
#% description: Must be expressed as R:G:B triplet
#% answer: 0:0:255
#% required: no
#% guisection: Color
#%end
#% option
#% key: monitor
#% type: string
#% description: Select WXGUI display monitor for legend
#% options: wx0,wx1,wx2,wx3,wx4,wx5,wx6,none
#% answer: wx1
#% required: no
#% guisection: Misc
#%end
#%flag 
#% guisection: Files
#% key: g
#%description: Save thematic map commands to group file for GIS Manager
#%end
#%option
#% key: psmap
#% type: string
#% label: Root for the name of psmap instruction files to be in current directory
#% description: If not set, no psmap instruction files will be created)
#% required: no
#% guisection: Files
#%end
#%option G_OPT_I_GROUP
#% description: Name of group file where thematic map commands will be saved
#% required: no
#% guisection: Files
#%end
#%option G_OPT_DB_COLUMN
#% key: rgb_column
#% description: Name of color column to populate RGB values
#%end
#%flag 
#% guisection: Theme
#%key: l
#%description: Create graphic legend in x11 display monitor
#%end
#%flag
#% guisection: Color
#% key: f
#% description: Only draw fills (no outlines) for areas and points
#%end
#%flag 
#% guisection: Misc
#%key: s
#%description: Output legend for GIS Manager (for scripting use only)
#%end
#%flag 
#% guisection: Misc
#%key: m
#%description: Use math notation brackets in legend
#%end

import sys
import os
import string
import shutil
import atexit
import grass.script as grass

# for Python 3 compatibility
try:
    xrange
except NameError:
    xrange = range

tmp_graph = None
tmp_group = None
tmp_psmap = None
tmp_psleg = None
tmp_gisleg = None

def cleanup():
    for file in [tmp_graph, tmp_group, tmp_psmap, tmp_psleg, tmp_gisleg]:
	if file:
	    grass.try_remove(file)

# hard-coded parameter: the maximum number of legend items before
# we strip them using a middle ellipsis
max_leg_items = 18

def subs(vars, tmpl):
    return string.Template(tmpl).substitute(vars)

def msg(vars, tmpl, verbose=False):
    if not verbose:
        grass.message(subs(vars, tmpl))
    else:
        grass.verbose(subs(vars, tmpl))
        
def out(fh, vars, tmpl):
    fh.write(subs(vars, tmpl))

def main():
    global tmp_graph, tmp_group, tmp_psmap, tmp_psleg, tmp_gisleg

    breakpoints = options['breakpoints']
    colorscheme = options['colorscheme']
    column = options['column']
    endcolor = options['end_color']
    group = options['group']
    layer = options['layer']
    linecolor = options['line_color']
    map = options['map']
    maxsize = options['maxsize']
    monitor = options['monitor']
    nint = options['nint']
    pointcolor = options['point_color']
    psmap = options['psmap']
    size = options['size']
    startcolor = options['start_color']
    themecalc = options['themecalc']
    themetype = options['themetype']
    type = options['type']
    where = options['where']
    icon = options['icon']
    rgb_column = options['rgb_column']
    
    flag_f = flags['f']
    flag_g = flags['g']
    flag_l = flags['l']
    flag_m = flags['m']
    flag_s = flags['s']

    layer = int(layer)
    nint = int(nint)
    size = float(size)
    maxsize = float(maxsize)

    if 'MONITOR' not in grass.gisenv().keys() and \
       'GRASS_RENDER_IMMEDIATE' not in os.environ:
       grass.fatal(_("Neither MONITOR (managed by d.mon command) nor GRASS_RENDER_IMMEDIATE "
                     "(used for direct rendering) defined)"))
            
    mapset = grass.find_file(map, element='vector')['mapset']
    if not mapset:
        grass.fatal(_("Vector map <%s> not found") % map)
    if rgb_column and mapset != grass.gisenv()['MAPSET']:
        grass.warning(_("Vector map <%s> not found in the current mapset. "
                        "Updating RGB values <%s> skipped.") % (map, "rgb_column"))
        rgb_column = None

    # check column type
    inf = grass.vector_columns(map, layer)
    if column not in inf:
	grass.fatal(_("No such column <%s>") % column)
    coltype = inf[column]['type'].lower()

    if coltype not in ["integer", "double precision"]:
	grass.fatal(_("Column <%s> is of type <%s> which is not numeric.") % (column, coltype))

    # create temporary file to hold d.graph commands for legend
    tmp_graph = grass.tempfile()
    # Create temporary file to commands for GIS Manager group
    tmp_group = grass.tempfile()
    # Create temporary file for commands for ps.map map file
    tmp_psmap = grass.tempfile()
    # Create temporary file for commands for ps.map legend file
    tmp_psleg = grass.tempfile()
    # create file to hold elements for GIS Manager legend
    tmp_gisleg = grass.tempfile()

    # Set display variables for group
    atype = int(type == "area")
    ptype = int(type == "point")
    ctype = int(type == "centroid")
    ltype = int(type == "line")
    btype = int(type == "boundary")

    # if running in the GUI, do not create a graphic legend in an xmon
    if flag_s:
        flag_l = False
        # if running in GUI, turn off immediate mode rendering so that the
        # iterated d.vect commands will composite using the display driver
        os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
        os.environ['GRASS_PNG_AUTO_WRITE'] = 'FALSE'

    db = grass.vector_db(map)[1]
    if not db or not db['table']:
        grass.fatal(_("No table connected or layer <%s> does not exist.") % layer)
    table = db['table']
    database = db['database']
    driver = db['driver']

    # update color values to the table?
    if rgb_column:
        # test, if the rgb column is in the table
        s = grass.read_command('db.columns', table = table, database = database, driver = driver)
        if rgb_column not in s.splitlines():
            msg(locals(), _("Creating column <$rgb_column> in table <$table>"))
            sql = "ALTER TABLE %s ADD COLUMN %s varchar(11)" % (table, rgb_column)
            grass.write_command('db.execute', database = database, driver = driver, input = '-', stdin = sql)

    # Group name
    if not group:
        group = "themes"

    f_group = file(tmp_group, 'w')
    f_group.write("Group %s\n" % group)

    # Calculate statistics for thematic intervals
    if type == "line":
        stype = "line"
    else:
        stype = ["point", "centroid"]

    grass.message(_("Calculating statistics..."))
    stats = grass.read_command('v.univar', flags = 'eg', map = map, type = stype, column = column, where = where, layer = layer)
    if not stats:
        grass.fatal(_("Unable to calculate statistics for vector map <%s>" % map))
    stats = grass.parse_key_val(stats)
    if 'min' not in stats:
        grass.fatal(_("Unable to calculate statistics for vector map <%s> "
                      "(missing minimum/maximum value)" % map))
        
    min  = float(stats['min'])
    max  = float(stats['max'])
    mean = float(stats['mean'])
    sd   = float(stats['population_stddev'])
    q1   = float(stats['first_quartile'])
    q2   = float(stats['median'])
    q3   = float(stats['third_quartile'])
    q4   = max

    ptsize = size

    if breakpoints and themecalc != "custom_breaks":
        grass.warning(_("Custom breakpoints ignored due to themecalc setting."))

    # set interval for each thematic map calculation type
    if themecalc == "interval":
        numint = nint
        step = float(max - min) / numint
        breakpoints = [min + i * step for i in xrange(numint + 1)]
        annotations = ""
    elif themecalc == "std_deviation":
        # 2 standard deviation units on either side of mean,
        # plus min to -2 sd units and +2 sd units to max, if applicable
        breakpoints = [min] + [i for i in [(mean + i * sd) for i in [-2,-1,0,1,2]] if min < i < max] + [max]
        annotations = [""] + [("%dsd" % i) for (i, j) in [(i, mean + i * sd) for i in [-2,-1,0,1,2]] if (min < j < max)] + [""]
        annotations = ";".join(annotations)
        numint = len(breakpoints) - 1
    elif themecalc == "quartiles":
        numint=4
        # one for each quartile
        breakpoints = [min, q1, q2, q3, max]
        annotations = " %f; %f; %f; %f" % (q1, q2, q3, q4)
    elif themecalc == "custom_breaks":
        if not breakpoints:
            grass.fatal(_("Required parameter <%s> not set") % "breakpoints") 
        breakpoints = [int(x) for x in breakpoints.split()]
        numint = len(breakpoints) - 1
        annotations = ""
    else:
        grass.fatal(_("Unknown themecalc type <%s>") % themecalc)

    pointstep = (maxsize - ptsize) / (numint - 1)

    # Prepare legend cuts for too large numint
    if numint > max_leg_items:
        xupper = int(numint - max_leg_items / 2) + 1
        xlower = int(max_leg_items / 2) + 1
    else:
        xupper = 0
        xlower = 0

    # legend title
    f_graph = file(tmp_graph, 'w')
    out(f_graph, locals(), """\
color 0:0:0
size 2 2
move 1 95
text Thematic map legend for column $column of map $map
size 1.5 1.8
move 4 90
text Value range: $min - $max
""")

    f_gisleg = file(tmp_gisleg, 'w')
    out(f_gisleg, locals(), """\
title - - - {Thematic map legend for column $column of map $map}
""")

    f_psleg = file(tmp_psleg, 'w')
    out(f_psleg, locals(), """\
text 1% 95% Thematic map legend for column $column of map $map
  ref bottom left
end
text 4% 90% Value range: $min - $max
  ref bottom left
end
""")

    msg(locals(), _("Thematic map legend for column <$column> of map <$map>"), verbose=True)
    msg(locals(), _("Value range: $min - $max"))

    colorschemes = {
        "blue-red":		("0:0:255",	"255:0:0"),
        "red-blue":		("255:0:0",	"0:0:255"),
        "green-red":	("0:255:0",	"255:0:0"),
        "red-green":	("255:0:0",	"0:255:0"),
        "blue-green":	("0:0:255",	"0:255:0"),
        "green-blue":	("0:255:0",	"0:0:255"),
        "cyan-yellow":	("0:255:255",	"255:255:0"),
        "yellow-cyan":	("255:255:0",	"0:255:255"),
        "custom_gradient":	(startcolor,	endcolor)
        }

    # open file for psmap instructions
    f_psmap = file(tmp_psmap, 'w')
    
    # graduated color thematic mapping
    if themetype == "graduated_colors":
        if colorscheme in colorschemes:
            startc, endc = colorschemes[colorscheme]
        # set color schemes for graduated color maps
        elif colorscheme == "single_color":
            if themetype == "graduated_points":
                startc = endc = linecolor
            else:
                startc = endc = pointcolor
        else:
            grass.fatal(_("This should not happen: parser error. Unknown color scheme %s") % colorscheme)

        color = __builtins__.map(int, startc.split(":"))
        endcolor = __builtins__.map(int, endc.split(":"))

        #The number of color steps is one less then the number of classes
        nclrstep = numint - 1
        clrstep = [(a - b) / nclrstep for a, b in zip(color, endcolor)]

        themecolor = startc

        # display graduated color themes
        if themecalc == "interval":
            out(f_graph, locals(), """\
move 4 87
text Mapped by $numint intervals of $step
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by $numint intervals of $step}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by $numint intervals of $step
  ref bottom left
end
""")

            msg(locals(), _("Mapped by $numint intervals of $step"))

        # display graduated color themes for standard deviation units
        if themecalc == "std_deviation":
            out(f_graph, locals(), """\
move 4 87
text Mapped by standard deviation units of $sd (mean = $mean)
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by standard deviation units of $sd (mean = $mean)}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by standard deviation units of $sd (mean = $mean)
  ref bottom left
end
""")

            msg(locals(), _("Mapped by standard deviation units of $sd (mean = $mean)"))

        # display graduated color themes for quartiles
        if themecalc == "quartiles":
            out(f_graph, locals(), """\
move 4 87
text Mapped by quartiles (median = $q2)
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by quartiles (median = $q2)}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by quartiles (median = $q2)
  ref bottom left
end
""")

            msg(locals(), _("Mapped by quartiles (median = $q2)"))

        f_graph.write("""\
move 4 83
text Color
move 14 83
text Value
move 4 80
text =====
move 14 80
text ============
""")

        f_psleg.write("""\
text 4% 83% Color
  ref bottom left
end
text 14% 83% Value
  ref bottom left
end
text 4% 80% =====
  ref bottom left
end
text 14% 80% ============
  ref bottom left
end
""")
        
        grass.message("")
        grass.message(_("Color(R:G:B)\tValue"))
        grass.message("============\t==========")

        line1 = 78
        line2 = 76
        line3 = 75

        i = 0
        first = True
        while i < numint:
            if flag_m:
                # math notation
                if first:
                    closebracket = "]"
                    openbracket = "["
                    mincomparison = ">="
                    first = False
                else:
                    closebracket = "]"
                    openbracket = "["
                    mincomparison = ">"
            else:
                closebracket = "" 
                openbracket = ""
                if first:
                    mincomparison = ">="
                    first = False
                else:
                    mincomparison = ">"
            
            themecolor = ":".join(__builtins__.map(str,color))
            if flag_f:
                linecolor = "none"
            else:
                if type in ["line", "boundary"]:
                    linecolor = themecolor
                else:
                    linecolor = linecolor

            ### ???
            ### rangemin = __builtins__.min(breakpoints)
            ### rangemax = __builtins__.max(breakpoints)
            rangemin = breakpoints[i]
            rangemax = breakpoints[i+1]
            
            if not annotations:
                extranote = ""
            else:
                extranote = annotations[i]

            if i < xlower or i >= xupper:
                xline1 = line2 + 2
                xline3 = line2 - 1
                out(f_graph, locals(), """\
color $themecolor
polygon
5 $xline1
8 $xline1
8 $xline3
5 $xline3
color $linecolor
move 5 $xline1
draw 8 $xline1
draw 8 $xline3
draw 5 $xline3
draw 5 $xline1
move 14 $line2
color 0:0:0
text $openbracket$rangemin - $rangemax$closebracket $extranote
""")
            else:
                if i == xlower:
                    out(f_graph, locals(), """\
color 0:0:0
move 10 $line2
text ...
""")
                else:
                    #undo next increment
                    line2 += 4

            if i < xlower or i >= xupper:
                out(f_gisleg, locals(), """\
area $themecolor $linecolor - {$openbracket$rangemin - $rangemax$closebracket $extranote}
""")

                if type in ["line", "boundary"]:
                    out(f_psleg, locals(), """\
line 5% $xline1% 8% $xline1%
  color $linecolor
end
text 14% $xline1% $openbracket$rangemin - $rangemax$closebracket $extranote
  ref center left
end
""")
                elif type in ["point", "centroid"]:
                    out(f_psleg, locals(), """\
point 8% $xline1%
  color $linecolor
  fcolor $themecolor
  size $size
  symbol $icon
end
text 14% $xline1% $openbracket$rangemin - $rangemax$closebracket $extranote
  ref center left
end
""")
                else:
                    out(f_psleg, locals(), """\
rectangle 5% $xline1% 8% $xline3%
  color 0:0:0
  fcolor $themecolor
end
text 14% $xline3% $openbracket$rangemin - $rangemax$closebracket DCADCA $extranote
  ref bottom left
end
""")
            else:
                if i == xlower:
                    out(f_psleg, locals(), """\
color 0:0:0
text 14% $xline3% ...
  ref bottom left
end
""")

                f_gisleg.write("text - - - {...}\n")

            grass.message("%-15s %s%.3f - %.3f%s %s" % (themecolor, openbracket, rangemin, rangemax, closebracket, extranote))
            if not where:
                sqlwhere = subs(locals(), "$column $mincomparison $rangemin AND $column <= $rangemax")
            else:
                sqlwhere = subs(locals(), "$column $mincomparison $rangemin AND $column <= $rangemax AND $where")

            # update color to database?
            if rgb_column:
                sql = subs(locals(), "UPDATE $table SET $rgb_column = '$themecolor' WHERE $sqlwhere")
                grass.write_command('db.execute', database = database, driver = driver, input = '-', stdin = sql)

            # Create group for GIS Manager
            if flag_g:
                # change rgb colors to hex
                xthemecolor = "#%02X%02X%02X" % tuple(__builtins__.map(int, themecolor.split(":")))
                #xlinecolor=`echo $linecolor | awk -F: '{printf("#%02X%02X%02X\n",$1,$2,$3)}'`

                if "$linecolor" == "black":
                    xlinecolor = "#000000"
                else:
                    xlinecolor = xthemecolor


                # create group entry
                out(f_group, locals(), """\
  _check 1
  Vector $column = $rangemin - $rangemax
    _check 1
    map $map
    display_shape 1
    display_cat 0
    display_topo 0
    display_dir 0
    display_attr 0
    type_point $ptype
    type_line $ltype
    type_boundary $btype
    type_centroid $ctype
    type_area $atype
    type_face 0
    color $xlinecolor
    fcolor $xthemecolor
    width $ptsize
    _use_fcolor 1
    lcolor #000000
    sqlcolor 0
    icon $icon
    size $ptsize
    field $layer
    lfield $layer
    attribute
    xref left
    yref center
    lsize 8
    cat
    where $sqlwhere
    _query_text 0
    _query_edit 1
    _use_where 1
    minreg
    maxreg
    _width 0.1
  End
""")

            # display theme vector map

            grass.run_command('d.vect', map = map, type = type, layer = layer,
                              where = sqlwhere,
                              color = linecolor, fcolor = themecolor, icon = icon, size = ptsize,
                              quiet = True)

            if type in ["line", "boundary"]:
                out(f_psmap, locals(), """\
vlines $map
  type $type
  layer $layer
  where $sqlwhere
  color $linecolor
  label $rangemin - $rangemax
end
""")
            elif type in ["point", "centroid"]:
                out(f_psmap, locals(), """\
vpoints $map
  type $type
  layer $layer
  where $sqlwhere
  color $linecolor
  fcolor $themecolor
  symbol $icon
  label $rangemin - $rangemax
end
""")
            else:
                out(f_psmap, locals(), """\
vareas $map
  layer $layer
  where $sqlwhere
  color $linecolor
  fcolor $themecolor
  label $rangemin - $rangemax
end
""")

            # increment for next theme
            i += 1
            if i == numint:
                color = endcolor
            else:
                color = [__builtins__.min(a - b, 255) for a, b in zip(color, clrstep)]
            line1 -= 4
            line2 -= 4
            line3 -= 4

    #graduated points and line widths thematic mapping

    if themetype in ["graduated_points", "graduated_lines"]:

        #display graduated points/lines by intervals
        if themecalc == "interval":
            out(f_graph, locals(), """\
move 4 87
text Mapped by $numint intervals of $step
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by $numint intervals of $step}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by $numint intervals of $step
  ref bottom left
end
""")

            msg(locals(), _("Mapped by $numint intervals of $step"))

        # display graduated points/lines for standard deviation units
        if themecalc == "std_deviation":

            out(f_graph, locals(), """\
move 4 87
text Mapped by standard deviation units of $sd (mean = $mean)
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by standard deviation units of $sd (mean = $mean)}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by standard deviation units of $sd (mean = $mean)
  ref bottom left
end
""")

            msg(locals(), _("Mapped by standard deviation units of $sd (mean = $mean)"))

        # display graduated points/lines for quartiles
        if themecalc == "quartiles":

            out(f_graph, locals(), """\
move 4 87
text Mapped by quartiles (median = $q2)
""")

            out(f_gisleg, locals(), """\
subtitle - - - {Mapped by quartiles (median = $q2)}
""")

            out(f_psleg, locals(), """\
text 4% 87% Mapped by quartiles (median = $q2)
  ref bottom left
end
""")

            msg(locals(), _("Mapped by quartiles (median = $q2)"))

        line1 = 76
        line2 = 75

        out(f_graph, locals(), """\
move 4 83
text Size/width
move 25 83
text Value
move 4 80
text ==============
move 25 80
text ==============
""")

        out(f_psleg, locals(), """\
text 4% 83% Icon size
  ref bottom left
end
text 25% 83% Value
  ref bottom left
end
text 4% 80% ============
  ref bottom left
end
text 25% 80% ============
  ref bottom left
end
""")


        grass.message("")
        grass.message(_("Size/width\tValue"))
        grass.message("==========\t=====")

        themecolor = pointcolor

        if flag_f:
            linecolor = "none"

        i = numint
        ptsize = maxsize

        while i >= 1:
            if flag_m:
                # math notation
                if i == 1:
                    closebracket = "]"
                    openbracket = "["
                    mincomparison = ">="
                else:
                    closebracket = "]"
                    openbracket = "]"
                    mincomparison = ">"
            else:
                closebracket = "" 
                openbracket = ""
                if i == 1:
                    mincomparison = ">="
                else:
                    mincomparison = ">"

            themecolor = pointcolor

            if flag_f:
                linecolor = "none"

            ### ???
            ### rangemin = __builtins__.min(breakpoints)
            ### rangemax = __builtins__.max(breakpoints)
            rangemin = breakpoints[i-1]
            rangemax = breakpoints[i]

            if not annotations:
                extranote = ""
            else:
                extranote = annotations[i]

            iconsize = int(ptsize / 2)
            lineht = int(ptsize / 4)
            if lineht < 4:
                lineht = 4

            if i < xlower or i >= xupper:
                if themetype == "graduated_lines":
                    out(f_graph, locals(), """\
color $linecolor
""")

                    out(f_gisleg, locals(), """\
line $themecolor $linecolor $ptsize {$openbracket$rangemin - $rangemax$closebracket $extranote}
""")
                else:
                    out(f_graph, locals(), """\
color $themecolor
""")
                    out(f_gisleg, locals(), """\
point $themecolor $linecolor $ptsize {$openbracket$rangemin - $rangemax$closebracket $extranote}
""")

                out(f_graph, locals(), """\
icon + $iconsize 5 $line1
color 0:0:0
move 10 $line2
text $ptsize pts
move 25 $line2
text $openbracket$rangemin - $rangemax$closebracket $extranote
""")
            else:
                if i == xlower:
                    out(f_graph, locals(), """\
color 0:0:0
move 10 $line2
text ...
""")

                    out(f_gisleg, locals(), """\
text - - - ...
""")
                else:
                    # undo future line increment
                    line2 += lineht

            if i < xlower or i >= xupper:
                out(f_psleg, locals(), """\
point 8% $line1%
  color $linecolor
  fcolor $themecolor
  size $iconsize
  symbol $icon
end
text 25% $line1% $openbracket$rangemin - $rangemax$closebracket $extranote
  ref center left
end
""")
            else:
                if i == xlower:
                    out(f_psleg, locals(), """\
text 25% $xline1% ...
   ref center left
end
""")

            grass.message("%-15d %s%.3f - %.3f%s %s" % \
                          (ptsize, openbracket, rangemin, rangemax, closebracket, extranote))

            if not where:
                sqlwhere = subs(locals(), "$column $mincomparison $rangemin AND $column <= $rangemax")
            else:
                sqlwhere = subs(locals(), "$column $mincomparison $rangemin AND $column <= $rangemax AND $where")

            # update color to database?
            if rgb_column:
                sql = subs(locals(), "UPDATE $table SET $rgb_column = '$themecolor' WHERE $sqlwhere")
                grass.write_command('db.execute', database = database, driver = driver, input = '-', stdin = sql)

            # Create group for GIS Manager
            if flag_g:
                # change rgb colors to hex
                xthemecolor = "#%02X%02X%02X" % tuple(__builtins__.map(int,themecolor.split(":")))
                xlinecolor = "#000000"

                # create group entry
                out(f_group, locals(), """\
  _check 1
  Vector $column = $rangemin - $rangemax
    _check 1
    map $map
    display_shape 1
    display_cat 0
    display_topo 0
    display_dir 0
    display_attr 0
    type_point $ptype
    type_line $ltype
    type_boundary $btype
    type_centroid $ctype
    type_area $atype
    type_face 0
    color $xlinecolor
    width $ptsize
    fcolor $xthemecolor
    _use_fcolor 1
    lcolor #000000
    sqlcolor 0
    icon $icon
    size $ptsize
    field $layer
    lfield $layer
    attribute
    xref left
    yref center
    lsize 8
    cat
    where $sqlwhere
    _query_text 0
    _query_edit 1
    _use_where 1
    minreg
    maxreg
    _width 0.1
  End
""")

            #graduates line widths or point sizes

            kwargs = {}
            if themetype == "graduated_lines":
                kwargs['width'] = ptsize
                
            grass.run_command('d.vect', map = map, type = type, layer = layer,
                              where = sqlwhere,
                              color = linecolor, fcolor = themecolor, icon = icon,
                              size = ptsize, quiet = True, **kwargs)
            
            if themetype != "graduated_lines":
                out(f_psmap, locals(), """\
vpoints $map
  type $type
  layer $layer
  where $sqlwhere
  color $linecolor
  fcolor $themecolor
  symbol $icon
  size $ptsize
  label $rangemin - $rangemax
end
""")

            ptsize -= pointstep

            line1 -= lineht
            line2 -= lineht
            i -= 1

    # Create graphic legend
    f_graph.close()
    if flag_l:
        grass.run_command('d.erase')
        grass.run_command('d.graph', input = tmp_graph)

    # Create group file for GIS Manager
    f_group.write("End\n")
    f_group.close()
    if flag_g:
        shutil.copyfile(tmp_group, "%s.dm" % group)

    # Create ps.map map file
    f_psmap.write("end\n")
    f_psmap.close()
    if psmap:
        shutil.copyfile(tmp_psmap, "%s.psmap" % psmap)

    # Create ps.map legend file
    f_psleg.write("end\n")
    f_psleg.close()
    if psmap:
        shutil.copyfile(tmp_psleg, "%s_legend.psmap" % psmap)

    # Create text file to use with d.graph in GIS Manager
    f_gisleg.close()
    if flag_s:
        tmpdir = os.path.dirname(tmp_gisleg)
        tlegfile = os.path.join(tmpdir, "gismlegend.txt")
        shutil.copyfile(tmp_gisleg, tlegfile)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
