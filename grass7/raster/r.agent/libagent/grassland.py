"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2015 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import grass.script as grass
from grass.script import array as garray

from libagent import error, playground


class Grassland(playground.Playground):
    """
    A GrassLand is a Playground and the interface to GRASS.

    Besides the plain raster layers it also connects them to the
    layer names used in GRASS and it can parse vector layers (for
    now only point vectors though) from GRASS too.
    """

    # internal logging class name
    ME = "r.agent::libagent.grassland.Grassland()"

    def __init__(self):
        """Create a Playground with all the relevant info by GRASS"""
        self.layers = dict()
        self.grassmapnames = dict()
        self.region = grass.region()
        if self.region['ewres'] != self.region['nsres']:
            raise error.DataError(Grassland.ME,
                                    "Only square raster cells make sense.")

#    def grassinfo(self, msg):
#        grass.info(msg)

    def setgrasslayer(self, layername, grassmapname, force=False):
        """
        Put an existing map from GRASS to the layer collection
        @param string name of the layer
        @param string name of an existing GRASS map layer
        @param boolean optional, whether to overwrite values if key exists
        """
        layer = garray.array()
        # fill the new grass array with the contents from the map (must exist)
        if grassmapname in grass.list_strings('rast'):
            layer.read(grassmapname)
            self.grassmapnames[layername] = grassmapname
            self.setlayer(layername, layer, force)
        else:
            raise error.DataError(Grassland.ME,
                                    "Grass Map was missing: " + grassmapname)

    def createlayer(self, layername, grassmapname=False, force=False):
        """
        Create a new layer and add it to the layer collection
        @param string name of the layer
        @param string optional name of a GRASS map layer (False if only local)
        @param boolean optional, whether to overwrite an existing layer
        """
        layer = garray.array()
        if grassmapname:
            self.grassmapnames[layername] = grassmapname
        self.setlayer(layername, layer, force)

    def removelayer(self, layername):
        """
        Remove (forget about) the layer named from the layer collection
        @param string name of the layer
        """
        if self.layers.has_key(layername):
            self.layers.pop(layername)
        if self.grassmapnames.has_key(layername):
            self.grassmapnames.pop(layername)

    def writelayer(self, layername, grassmapname=False, force=False):
        """
        Write out a given layer to a GRASS map file
        @param string name of the layer to be exported
        @param string optional name of the GRASS map file to be written
        @param boolean optional, whether an existing file may be overwritten
        """
        if not grassmapname:
            if self.grassmapnames.has_key(layername):
                grassmapname=self.grassmapnames[layername]
            else:
                raise error.DataError(Grassland.ME,
                                        "Grass Map name is empty.")
        if self.layers.has_key(layername):
            if grassmapname in \
                    grass.list_strings('rast'):
                if force:
                    force="force"
                else:
                    raise error.DataError(Grassland.ME,
                                        "Grass map already exists.")
            self.layers[layername].write(grassmapname, overwrite=force)
        else:
            raise error.DataError(Grassland.ME, "Layer is not in list.")

    def parsevectorlayer(self, layername, grassmapname, value=1, force=False):
        """
        Take point information from a vector layer, mark the points on the
        layer specified and return them as a list
        @param string name of the layer to be exported
        @param string name of the GRASS map file to be created
        @param int value to be set
        @param boolean optional, whether an existing file may be overwritten
        """
        vectors = []
        if grassmapname in grass.list_strings('vect'):
            layer = grass.vector_db_select(grassmapname)['values']
            # TODO only points are supported, ask some expert how to test this
            # TODO indexing seems to start at "1".. verify!
            for v in layer.values():
                # TODO do they all look like this??
                if len(v) == 4 and v[0] == v[3]:
                    p = self.stringcoordinate(v[1],v[2])
                    # TODO - as with grass numpy array it seems that
                    # [0,0] is north-most west-most..
                    p[0] = int(round(
                        ( self.region["n"] - p[0] ) / self.region["nsres"] ))
                    p[1] = int(round(
                        ( p[1] - self.region["w"] ) / self.region["ewres"] ))
                    vectors.append(p)
                    self.layers[layername][p[0]][p[1]] = value
        return vectors

    def decaycellvalues(self, layername, halflife, minimum=0):
        """
        Let the values in each cell decay, volatilize or evaporate over time.
        This method is optimized for numpy arrays, see playground for plain
        arrays.
        @param string layername name of the layer to work on
        @param long halflife or number of years when to reach half of the value
        @param long minimum value to keep on cell
        """
        if halflife > 0:
            self.layers[layername] = self.layers[layername]*0.5**(1.0/halflife)
            #TODO find out why 'filename' is lost - numpy vs. garray..
        #TODO think about moving 'minimum' to a predifined matrix in anthill
        if minimum > 0:
            mask = garray.numpy.ones_like(self.layers[layername]) - 1 + minimum
            self.layers[layername] = \
                    garray.numpy.maximum(self.layers[layername], mask)
