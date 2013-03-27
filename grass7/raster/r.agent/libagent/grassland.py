"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import playground
import grass.script as grass
from grass.script import array as garray

class Grassland(playground.Playground):
    """A GrassLand is a Playground and the interface to GRASS."""

    def __init__(self):
        """Create a Playground with all the relevant info by GRASS"""
        self.layers = dict()
        self.grassmapnames = dict()
        self.region = grass.region()
        if self.region['ewres'] != self.region['nsres']:
            raise error.DataError("r.agent::libagent.playground.Playground()",
                                    "Only square raster cells make sense.")

    def setgrasslayer(self, layername, grassmapname, force=False):
        """
        Put an existing map from GRASS to the layer collection
        @param string name of the layer
        @param string name of an existing GRASS map layer
        @param boolean optional, whether to overwrite values if key exists
        """
        layer = garray.array()
        # fill the new grass array with the contents from the file
        if grassmapname in grass.list_grouped('rast')[grass.gisenv()['MAPSET']]:
            layer.read(grassmapname)
            self.grassmapnames[layername] = grassmapname
            self.setlayer(layername, layer, force)

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
        @param string optional name of the GRASS map file to be created
        @param boolean optional, whether an existing file may be overwritten
        """
        if self.layers.has_key(layername) and \
                                    self.grassmapnames.has_key(layername):
            if force:
                force="force"
            self.layers[layername].write(self.grassmapnames[layername],
                                                        overwrite=force)

    def parsevectorlayer(self, layername, grassmapname, value=1, force=False):
        """
        Take point information from a vector layer, mark them on the
        layer specified and return them as a list
        @param string name of the layer to be exported
        @param string name of the GRASS map file to be created
        @param int value to be set
        @param boolean optional, whether an existing file may be overwritten
        """
        vectors = []
        if grassmapname in grass.list_grouped('rast')[grass.gisenv()['MAPSET']]:
            layer = grass.vector_db_select(grassmapname)['values']
            # TODO only points are supported, ask some expert how to test this
            # TODO indexing seems to start at "1".. verify!
            for v in layer.values():
                if len(v) == 4 and v[0] == v[3]:
                    x = ( v[1] - self.region["s"] ) / self.region["ewres"]
                    y = ( v[1] - self.region["s"] ) / self.region["nsres"]
                    vectors.append([x, y])
                    self.layers[layername][y][x] = value
        return vectors

