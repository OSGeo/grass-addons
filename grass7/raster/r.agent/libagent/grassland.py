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

class GrassLand(playground.Playground):
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
        self.setlayer(layername, layer)

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
        #TODO implement
        if self.layers.has_key(layername) and \
          self.grassmapnames.has_key(layername):
            grassmapname = self.grassmapnames[layername]
            layer = self.layers[layername]
            layer.write(grassmapname, overwrite=force)

