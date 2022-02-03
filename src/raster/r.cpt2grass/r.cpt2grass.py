#!/usr/bin/env python

#
############################################################################
#
# MODULE:       r.cpt2grass
# AUTHOR(S):    M. Hamish Bowman, Otago University, New Zealand
#               (original GRASS 6 implementation)
#               Anna Petrasova (rewritten to GRASS 7 in Python)
# PURPOSE:      Convert a GMT color table into a GRASS color rules file
# COPYRIGHT:    (c) 2007 by Hamish Bowman, Anna Petrasova
#               and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# SEE ALSO:     GMT: The Generic Mapping Tools
#                 http://gmt.soest.hawaii.edu
#
#############################################################################

# %module
# % description: Convert or apply a GMT color table to a GRASS raster map
# %end
# %option G_OPT_F_INPUT
# % description: Name of input GMT color table (.cpt file)
# % required: no
# % guisection: Input
# %end
# %option
# % key: url
# % type: string
# % description: URL of the color table
# % required: no
# % guisection: Input
# %end
# %option G_OPT_R_INPUT
# % key: map
# % description: Raster map to apply it to
# % required: no
# % guisection: Input
# %end
# %option G_OPT_F_OUTPUT
# % description: Name for new rules file
# % required: no
# %end
# %flag
# % key: s
# % description: Stretch color scale to match map data extent
# %end
# %rules
# % required: input,url
# % exclusive: input,url
# %end

import sys
import grass.script as gscript


def HSVtoRGB(h, s, v):
    """Converts HSV to RGB.
    Based on the Foley and Van Dam HSV algorithm used
    by James Westervelt's (CERL) hsv.rgb.sh script from GRASS 4/5."""
    # Hue: 0-360 degrees
    # Saturation: 0.0-1.0
    # Value: 0.0-1.0
    if v == 0.0:
        return (0, 0, 0)
    if v == 1.0:
        return (255, 255, 255)

    if h >= 360:
        h -= 360
    h = h / 60.0
    i = int(h)
    f = h - i
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))

    # init/fallback
    R = G = B = 0
    # red
    if i == 0:
        R = v
    if i == 1:
        R = q
    if i == 2:
        R = p
    if i == 3:
        R = p
    if i == 4:
        R = t
    if i == 5:
        R = v

    # green
    if i == 0:
        G = t
    if i == 1:
        G = v
    if i == 2:
        G = v
    if i == 3:
        G = q
    if i == 4:
        G = p
    if i == 5:
        G = p

    # blue
    if i == 0:
        B = p
    if i == 1:
        B = p
    if i == 2:
        B = t
    if i == 3:
        B = v
    if i == 4:
        B = v
    if i == 5:
        B = q

    return (R * 255, G * 255, B * 255)


def main(options, flags):
    input_file = options["input"]
    input_url = options["url"]
    if input_url:
        try:
            from six.moves.urllib.request import urlopen
        except ImportError:
            from urllib2 import urlopen

        txt = urlopen(input_url).readlines()
    else:
        with open(input_file, "r") as f:
            txt = f.readlines()

    model = "RGB"  # assuming RGB
    cpt_rules = []
    for line in txt:
        if not line.strip():
            continue
        if "COLOR_MODEL" in line:
            model = line.split("=")[-1].strip()
        elif line[0] in ("B", "F", "N", "#"):
            continue
        else:
            cpt_rules.append(line.strip())

    if model not in ("RGB", "HSV"):
        gscript.fatal(_("Only the RGB and HSV color models are supported"))

    rules = []
    if flags["s"]:
        # sort?
        cpt_min = float(cpt_rules[0].split()[0])
        cpt_max = float(cpt_rules[-1].split()[4])
        cpt_range = cpt_max - cpt_min
    for line in cpt_rules:
        try:
            v1, r1, g1, b1, v2, r2, g2, b2 = line.split()
        except ValueError:
            gscript.fatal(
                _(
                    "Parsing input failed. The expected format is 'value1 R G B value2 R G B'"
                )
            )
        v1 = float(v1)
        v2 = float(v2)
        if model == "HSV":
            r1, b1, g1 = HSVtoRGB(int(r1), int(g1), int(b1))
            r2, b2, g2 = HSVtoRGB(int(r2), int(g2), int(b2))
        if flags["s"]:
            v1 = 100 * (cpt_range - (cpt_max - v1)) / cpt_range
            v2 = 100 * (cpt_range - (cpt_max - v2)) / cpt_range
        rules.append(
            "{v:.3f}{perc} {r}:{g}:{b}".format(
                v=v1, perc="%" if flags["s"] else "", r=r1, g=g1, b=b1
            )
        )
        rules.append(
            "{v:.3f}{perc} {r}:{g}:{b}".format(
                v=v2, perc="%" if flags["s"] else "", r=r2, g=g2, b=b2
            )
        )
    if options["map"]:
        gscript.write_command(
            "r.colors", map=options["map"], rules="-", stdin="\n".join(rules)
        )
    if options["output"]:
        with open(options["output"], "w") as f:
            f.write("\n".join(rules))
            f.write("\n")
    elif not options["map"]:
        print("\n".join(rules) + "\n")


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main(options, flags))
