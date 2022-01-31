#!/usr/bin/env python


############################################################################
#
# MODULE:     i.ortho.corr
# AUTHOR(S):  Luca Delucchi
# PURPOSE:    Useful to correct orthophoto using the camera angle map
#             create by i.ortho.photo
#
# COPYRIGHT:    (C) 2011 by Luca Delucchi
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
#
#############################################################################
# %module
# % description: Corrects orthophoto taking part of the adjacent orthophotos using a camera angle map.
# % keyword: imagery
# % keyword: orthorectification
# %end
# %option
# % key: input
# % type: string
# % gisprompt: input raster
# % key_desc: name
# % description: Name of input raster map
# % required: yes
# %end
# %option
# % key: osuffix
# % type: string
# % gisprompt: suffix of ortophoto
# % key_desc: ortho
# % description: Suffix of ortophoto map, default is .ortho, use None for no suffix
# % required: no
# %end
# %option
# % key: csuffix
# % type: string
# % gisprompt: suffix of camera
# % key_desc: ortho
# % description: Suffix of camera angle map, default is .camera_angle, use None for no suffix
# % required: no
# %end
# %option
# % key: tiles
# % type: string
# % gisprompt: input vector tiles
# % key_desc: name
# % description: Name of input vector tiles map create by a list of orthophoto
# % required: yes
# %end
# %option
# % key: field
# % type: string
# % gisprompt: name of location's field
# % key_desc: name
# % description: Name of location's field in the input vector tiles map
# % required: no
# %end
# %option
# % key: exclude
# % type: string
# % gisprompt: pattern to exclude some tiles
# % key_desc: name
# % description: Pattern to use if you want exclude some tiles
# % required: no
# %end
# %option
# % key: output
# % type: string
# % gisprompt: output raster
# % key_desc: name
# % description: Name of output raster map
# % required: no
# %end

# import library
import os
import sys
import re
import grass.script as grass


def main():
    # check if GISBASE is set
    if "GISBASE" not in os.environ:
        # return an error advice
        print("You must be in GRASS GIS to run this program.")
        sys.exit(1)

    # input raster map
    map_in = options["input"]
    # output raster map
    map_out = options["output"]
    # vector tiles map
    map_tiles = options["tiles"]
    # location's field
    field = options["field"]
    if field == "":
        field = "location"
    # orthophoto suffix
    ortho = options["osuffix"]
    if ortho == "":
        ortho = ".ortho"
    # camera angle suffix
    camera = options["csuffix"]
    if camera == "":
        camera = ".camera_angle"
    # check if the ortho and camera angle suffix
    if ortho == camera:
        print("Ortho and camera suffix can't be the same.")
    sys.exit(1)

    ex_pattern = options["exclude"]
    # return the points
    points = controlPoints(map_in)
    # the tiles near input map
    nearMaps = mapTile(points, map_in, map_tiles, field)
    print(nearMaps)
    # calculate output map
    calcMap(map_in, map_out, nearMaps, ortho, camera, ex_pattern)


def controlPoints(inputmap):
    """This function serve to return the coordinates of the photo's four
    vertex

    :param str inpumap: the input raster map's name
    """

    # return r.info about input file
    rinfo = grass.raster_info(inputmap)
    nsres = rinfo["nsres"]
    ewres = rinfo["ewres"]
    # create a dictionary for Nord East
    NE = [rinfo["east"] - 2 * ewres, rinfo["north"] - 2 * nsres]
    # create a dictionary for Nord West
    NW = [rinfo["west"] + 2 * ewres, rinfo["north"] - 2 * nsres]
    # create a dictionary for Sud East
    SE = [rinfo["east"] - 2 * ewres, rinfo["south"] + 2 * nsres]
    # create a dictionary for Sud West
    SW = [rinfo["west"] + 2 * ewres, rinfo["south"] + 2 * nsres]
    ## create a dictionary for Nord Center
    # NC = {'x':rinfo['east']-(rinfo['east']-rinfo['west'])/2, 'y':rinfo["north"]-2*nsres}
    ## create a dictionary for Sud Center
    # SC = {'x':rinfo['east']-(rinfo['east']-rinfo['west'])/2,'y':rinfo["south"]+2*nsres}
    ## create a dictionary for West Center
    # WC = {'x':rinfo['west']+2*ewres, 'y':rinfo["north"] - (rinfo["north"] - rinfo["south"]) / 2 }
    ## create a dictionary for East Center
    # EC = {'x':rinfo['east']-2*ewres, 'y':rinfo["north"]- (rinfo["north"] - rinfo["south"]) / 2}
    # create a dictionary to return the four point
    retDict = {"NE": NE, "NW": NW, "SE": SE, "SW": SW}  # 'NC' : NC,'SC' : SC,
    # 'WC' : WC, 'EC' : EC}
    # return the dictionary
    return retDict


def mapTile(points, inputmap, tilemap, field):
    """This function serve to return the name of the near maps of the
    input map

    :param points: the points returned by controlPoints function
    :param tilemap: the tiles vector map's name
    :param field: the field's name where it is set the name of other maps

    """

    # list of the map's names
    nameFiles = []
    # for each point
    for k, v in points.items():
        # query the tiles vector map
        what = vector_what(tilemap, v)
        for l, m in what.items():
            if l != "general":
                # create the name for path
                nameFile = os.path.basename(m[field])
                if nameFiles.count(nameFile) == 0:
                    # add the file name to list
                    nameFiles.append(nameFile)
    # return list
    nameFiles.remove(inputmap)
    return nameFiles


def vector_what(map, coor):
    """!Return the result of v.what using the map and coordinates passed

    @param map vector map name
    @param coor a list of x,y coordinates

    @return parsed output in dictionary

    """

    result = {}
    # create string for east_north param
    fields = grass.read_command("v.what", flags="ag", map=map, east_north=coor)
    # split lines
    fields = fields.splitlines()
    # value for number of features
    value = 0
    # create a temporary dictionary
    temp_dic = {}
    # for each line
    for field in fields:
        # split key and value
        kv = field.split("=", 1)
        if len(kv) > 1:
            # Start the new feature
            if kv[0].strip() == "Driver":
                # if value is 0 dictionary contain general information about map
                if value == 0:
                    result["general"] = temp_dic
                # else features
                else:
                    result["feature" + str(value)] = temp_dic
                # value for the new feature
                value = value + 1
                # create a new temporary dictionary
                temp_dic = {}
                # add driver to the new dictionary
                temp_dic[kv[0].strip()] = str(kv[1])
            else:
                # add value to the dictionary
                temp_dic[kv[0].strip()] = str(kv[1])
    # add the last feature
    result["feature" + str(value)] = temp_dic
    return result


def calcMap(inmap, outmap, tiles, osuffix, csuffix, exclude):
    """Calculate the map of minimum of the other camera maps"""
    maxValue = 30
    # input map
    prefix_input = inmap.strip(osuffix)
    camera_input = prefix_input + csuffix
    # set the re
    if exclude != "":
        r = re.compile(exclude)
    # set the outmap if it isn't passed by user
    if outmap == "":
        outmap = prefix_input + ".ortho_corr"
    # check for each map the best cameta angle
    for i in range(0, len(tiles)):
        if exclude != "":
            exclude_tile = r.search(tiles[i])
            if exclude_tile:
                continue
        prefix_tile = tiles[i].strip(osuffix)
        camera_tile = prefix_tile + csuffix
        # first tile start the new map
        if i == 0:
            grass.mapcalc(
                "${out} = if(isnull(${c_tile}), ${in_map}, "
                "if(${c_input} >= ${maxV}, ${in_map}, "
                "if(${c_tile} >= ${maxV}, ${tile}, ${in_map})))",
                out=outmap,
                c_input=camera_input,
                c_tile=camera_tile,
                in_map=inmap,
                tile=tiles[i],
                maxV=maxValue,
            )

            grass.mapcalc(
                "temp_camera = if(isnull(${c_tile}), ${c_input}, "
                "if(${c_input} >= ${maxV}, ${c_input}, "
                "if(${c_tile} >= ${maxV}, ${c_tile}, ${c_input})))",
                c_input=camera_input,
                c_tile=camera_tile,
                maxV=maxValue,
            )
        # for the other tile check the outmap
        else:
            grass.mapcalc(
                "${out} = if(isnull(${c_tile}), ${out}, "
                "if(temp_camera >= ${maxV},${out}, "
                "if(${c_tile} >= ${maxV}, ${tile}, ${out})))",
                out=outmap,
                c_tile=camera_tile,
                tile=tiles[i],
                maxV=maxValue,
            )

            grass.mapcalc(
                "temp_camera = if(isnull(${c_tile}), temp_camera, "
                "if(temp_camera >= ${maxV}, ${c_input}, "
                "if(${c_tile} >= ${maxV}, ${c_tile},${c_input})))",
                c_input=camera_input,
                c_tile=camera_tile,
                maxV=maxValue,
            )
    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
