#!/usr/bin/env python

"""

MODULE:       r.colors.out_sld
AUTHOR(S):    Hamish Bowman
              Stefan Blumentrath, NINA: Port to GRASS GIS 7 / Python,
              label and opacity support
PURPOSE:      Export GRASS raster color table to OGC SLD template v1.0.0
COPYRIGHT:    (C) 2011 by Hamish Bowman, and the GRASS Development Team

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

Based on hints from
http://docs.geoserver.org/stable/en/user/styling/sld/reference/rastersymbolizer.html

"""

"""
TODO:
- Add transparency support
- Support for interval ColorMap?
"""

# %Module
# % description: Exports the color table associated with a raster map layer in SLD format.
# % keyword: raster
# % keyword: export
# % keyword: color table
# %End

# %Option G_OPT_R_MAP
# % required: yes
# %End

# %Option
# % key: style_name
# % required: no
# % label: Name for style
# % description: A name for the style which might be displayed on the server
# % answer: GRASS color table
# %End

# %Option G_OPT_F_OUTPUT
# % required: no
# % label: Name for output SLD rules file
# % description: "-" to write to stdout
# % answer: -
# %End

# %flag
# % key: n
# % description: Propagate NULLs
# %end

import os
import sys
import grass.script as grass


def set_output_encoding(encoding="utf-8"):
    import codecs

    current = sys.stdout.encoding
    if current is None:
        sys.stdout = codecs.getwriter(encoding)(sys.stdout)
    current = sys.stderr.encoding
    if current is None:
        sys.stderr = codecs.getwriter(encoding)(sys.stderr)


def main():

    # Set output encoding to UTF-8
    set_output_encoding()
    # Parse input
    output = options["output"]  # done
    style_name = options["style_name"]  # done
    map = options["map"]  # done

    # check if input file exists
    if not grass.find_file(map)["file"]:
        grass.fatal(_("Raster map <%s> not found") % map)

    # Get map metadata
    mapinfo = grass.parse_command("r.info", flags="e", map=map)

    if mapinfo["title"]:
        name = "{} : {}".format(mapinfo["map"], mapinfo["title"])
    else:
        name = mapinfo["map"]

    # Get color rules
    color_rules = grass.read_command("r.colors.out", map=map).split("\n")

    # Get maptype (CELL, FCELL, DCELL)
    maptype = grass.parse_command("r.info", flags="g", map=map)["datatype"]

    # Check if map has categories if type is CELL
    if maptype == "CELL":
        grass.verbose("Reading category lables, may take a while...")
        categories = grass.parse_command("r.category", map=map, separator="=")
        if list(set(categories.values()))[0] or len(list(set(categories.values()))) > 1:
            use_categories = True
        else:
            use_categories = False
    else:
        use_categories = False

    # Initialize SLD with header
    sld = """<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor version="1.0.0"
    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
    xmlns="http://www.opengis.net/sld"
    xmlns:ogc="http://www.opengis.net/ogc"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <Name>{}</Name>""".format(
        style_name
    )
    sld += """    <UserStyle>
      <Title>{}</Title>\n
      <FeatureTypeStyle>
        <Rule>
          <RasterSymbolizer>\n""".format(
        name
    )

    # Define type of ColorMap depending on data type of input map
    if use_categories:
        sld += "            <ColorMap type={}>\n".format('"values"')
        ColorMapEntry = '              <ColorMapEntry color="#{0:02x}{1:02x}{2:02x}" quantity="{3}" label="{4}" opacity="{5}" />\n'
    else:
        sld += "            <ColorMap>\n"
        # sld+='            <ColorMap type={}>\n'.format('"ramp"')
        ColorMapEntry = '              <ColorMapEntry color="#{0:02x}{1:02x}{2:02x}" quantity="{3}" opacity="{4}" />\n'

    # loop over colors
    for num, c in enumerate(color_rules):
        grass.percent(num + 1, len(color_rules), 1)
        if len(c.split(" ")) == 2 and not c.split(" ")[0] == "default":
            q = c.split(" ")[0]
            if q == "nv":
                q = "NaN"
                r = 255
                g = 255
                b = 255
                o = 0
            else:
                r = int(c.split(" ")[1].split(":")[0])
                g = int(c.split(" ")[1].split(":")[1])
                b = int(c.split(" ")[1].split(":")[2])
                o = 1
            if use_categories:
                if str(q) in list(categories.keys()):
                    l = categories[str(q)]
                elif q == "NaN":
                    l = "NoData"
                else:
                    continue
                if not q == "NaN" or flags["n"]:
                    sld += ColorMapEntry.format(r, g, b, q, l, o)
            else:
                if not q == "NaN" or flags["n"]:
                    sld += ColorMapEntry.format(r, g, b, q, o)

    # write file footer
    sld += """            </ColorMap>
          </RasterSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>\n"""

    if output == "-":
        # Write SLD to stdout if no output is requested
        print(sld)
    else:
        # Write SLD to file if requested
        with open(output, "wb+") as o:
            o.write(sld.encode("utf8"))


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
