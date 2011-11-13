#!/usr/bin/env python
############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      very basic test collection for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

class Playground(object):
    """A Playground is a major component of a World,
       defining and organizing space."""
    def __init__(self):
        self.layers = dict()
        self.offset = [None,None]
        self.limit = [None,None]
        self.steps = []
    def setbounds(self, north=None, south=None, east=None, west=None,
                     rows=None, cols=None):
        pass
    def getbounds(self):
        return []
    def setlayer(self, layername, layer, force=False):
        pass
    def createlayer(self, layername, grassmap=False):
        pass
    def getlayer(self, layername):
        return []
    def removelayer(self, layername):
        pass
    def writelayer(self, layername):
        pass

