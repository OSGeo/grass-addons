"""
MODULE:       r.agent.*
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      library file for the r.agent.* suite
COPYRIGHT:    (C) 2015 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

import random
from math import sqrt

from libagent import error

import numpy


class Playground(object):
    """
    A Playground is a major component of a World, defining and organizing
    space, i.e. it mainly consists of a set of raster layers, makes
    them accessible and puts them in relation to one another.
    """

    STRAIGHT = 0
    DIAGONAL = sqrt(2) - 1

    def __init__(self):
        """Create a Playground"""
        self.layers = dict()
        self.region = dict()
        self.setregion(1, 1)

    def stringcoordinate(self, x, y):
        """
        Convert string coordinates to float coordinates.
        @param x string west-east coordinate
        @param y string south-north coordinate
        @return position as a list of floats: south-north, west-east
        """
        try:
            # try to convert the string value to a float
            x = float(x)
            y = float(y)
            # also catch 'inf' and 'nan' ..
            if (x == x) and (y == y) and (x + y - 1 != x + y):
                return [float(y), float(x)]
            else:
                return []
        except ValueError:
            return []

    def setregion(self, rows, cols):
        """
        Set the geometry of the playground, based only on the number
        of rows and columns
        @param numeric number of rows
        @param numeric number of columns
        """
        self.region["s"] = 0
        self.region["n"] = rows
        self.region["w"] = 0
        self.region["e"] = cols
        self.region["rows"] = rows
        self.region["cols"] = cols

        for layer in self.layers:
            if not (len(layer) is rows and len(layer[0]) is cols):
                raise error.Error(
                    "r.agent::libagent.playground.Playground.setregion()",
                    "new region is incompatible with some layer(s).",
                )

    def getregion(self):
        """
        Return the region information
        @return dict region
        """
        return self.region

    def gettotalcount(self):
        """
        Return the number of cells in the playground
        @return int total cells count
        """
        return self.region["rows"] * self.region["cols"]

    def getdiagonalcount(self):
        """
        Return the number of cells in the diagonal
        @return int diagonal cells count
        """
        return sqrt(pow(self.region["rows"], 2) + pow(self.region["cols"], 2))

    def getbound(self, bound):
        """
        Return the requested bound, takes: 'n', 's', 'w', or 'e'
        @param string bound
        @return float the outermost coordinate
        """
        if bound == "n" or bound == "s" or bound == "w" or bound == "e":
            return self.region[bound]

    def setlayer(self, layername, layer, force=False):
        """
        Put an existing map layer to the layer collection
        @param string name of the layer
        @param list a map layer
        @param boolean optional, whether to overwrite values if key exists
        """
        if not force and layername in self.layers:
            raise error.Error(
                "r.agent::libagent.playground.Playground.setlayer()",
                "May not overwrite existing layer.",
            )
        self.layers[layername] = layer

    def createlayer(self, layername, filename=False, force=False):
        """
        Create a new layer and add it to the layer collection
        @param string name of the layer
        @param string optional name, whether to create it from an existing file
        @param boolean optional, whether to overwrite an existing layer
        """
        r = self.region["rows"]
        c = self.region["cols"]
        layer = numpy.zeros(r * c).reshape((r, c))

        if filename:
            # TODO import from file
            pass

        self.setlayer(layername, layer)

    def getlayer(self, layername):
        """
        Return a layer from the collection by its name
        @param string name of the layer
        @return list the requested map layer
        """
        retval = False
        if layername in self.layers:
            retval = self.layers[layername]
        return retval

    def removelayer(self, layername):
        """
        Remove (forget about) the layer named from the layer collection
        @param string name of the layer
        """
        if layername in self.layers:
            self.layers.pop(layername)

    def writelayer(self, layername, filename, force=False):
        """
        Write out a given layer to a certain file
        @param string name of the layer to be exported
        @param string name of the file to be written to
        @param boolean optional, whether an existing file may be overwritten
        """
        # TODO export to file
        # TODO overwrite policy: to increment or to fail?
        pass

    def getrandomposition(self):
        """
        Return a random position on the playground
        @return list some coordinates
        """
        ns = random.randrange(0, self.region["rows"])
        nw = random.randrange(0, self.region["cols"])
        return [ns, nw]

    def isvalidposition(self, position):
        """
        Test if a position really is on the playground
        @return list position if on, boolean False if off the playground
        """
        if (
            0 <= position[0] < self.region["rows"]
            and 0 <= position[1] < self.region["cols"]
        ):
            return position
        else:
            return False

    def addneighbourposition(self, positions, position):
        """
        Try adding a position to a list of positions.
        @param list to be filled up
        @param position to be verified and added
        @return the new list
        """
        if self.isvalidposition(position):
            positions.append(position)
        return positions

    def getorderedneighbourpositions(self, position, freedom):
        """
        Get all the positions reachable from a certain position and
        ordered by their orientation from the given position
        @param list coordinates of a certain cell
        @param int number of potentially reachable neighbours
        @return list of coordinates, or boolean False
        """
        positions = []
        # test for all valid freedoms
        if not freedom == 4 and not freedom == 8:
            return False
        # collect the coordinates
        if freedom >= 4:
            # walking south (=0)
            self.addneighbourposition(
                positions, [position[0] - 1, position[1], 0, Playground.STRAIGHT]
            )
            # walking north (=1)
            self.addneighbourposition(
                positions, [position[0] + 1, position[1], 1, Playground.STRAIGHT]
            )
            # walking west (=2)
            self.addneighbourposition(
                positions, [position[0], position[1] - 1, 2, Playground.STRAIGHT]
            )
            # walking east (=3)
            self.addneighbourposition(
                positions, [position[0], position[1] + 1, 3, Playground.STRAIGHT]
            )
        if freedom >= 8:
            # walking south-west (=4)
            self.addneighbourposition(
                positions, [position[0] - 1, position[1] - 1, 4, Playground.DIAGONAL]
            )
            # walking north-west (=5)
            self.addneighbourposition(
                positions, [position[0] + 1, position[1] - 1, 5, Playground.DIAGONAL]
            )
            # walking south-east (=6)
            self.addneighbourposition(
                positions, [position[0] - 1, position[1] + 1, 6, Playground.DIAGONAL]
            )
            # walking north-east (=7)
            self.addneighbourposition(
                positions, [position[0] + 1, position[1] + 1, 7, Playground.DIAGONAL]
            )
        return positions

    def getneighbourpositions(self, position, freedom):
        """
        Get all the positions reachable from a certain position and shuffle
        @param list coordinates of a certain cell
        @param int number of potentially reachable neighbours
        @return list of coordinates, or boolean False
        """
        positions = self.getorderedneighbourpositions(position, freedom)
        if positions:
            random.shuffle(positions)
        return positions

    def getcellvalue(self, layername, position):
        """
        Get the content of a certain cell in a layer specified.
        @param layername the name of the layer to query
        @param position the exact position of the cell in question
        @return the value stored in the cell
        """
        return self.layers[layername][position[0]][position[1]]

    def setcellvalue(self, layername, position, value):
        """
        Set the content of a certain cell in a layer specified.
        @param layername the name of the layer to be edited
        @param position the exact position of the cell in question
        """
        self.layers[layername][position[0]][position[1]] = value

    def decaycellvalues(self, layername, halflife, minimum=0):
        """
        Let the values in each cell decay, volatilize or evaporate over time.
        This method is intended for relatively small 2D python arrays, see
        grassland.Grassland.decaycellvalues for numpy arrays.
        @param string layername name of the layer to work on
        @param long halflife or number of years when to reach half of the value
        @param long minimum value to keep on cell
        """
        if halflife > 0:
            for i in range(self.region["rows"]):
                for j in range(self.region["cols"]):
                    if self.layers[layername][i][j] > minimum:
                        v = self.layers[layername][i][j] * 0.5 ** (1.0 / halflife)
                        if v > minimum:
                            self.layers[layername][i][j] = v
                        else:
                            self.layers[layername][i][j] = minimum
