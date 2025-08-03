#!/usr/bin/env python
"""
MODULE:       r.agent.rand
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      r.agent.rand is used to get simple agents wander around
              in a raster based playground just by chance. This is the
              most basic application for the libant library (i.e. a test).
COPYRIGHT:    (C) 2011 by Michael Lustenberger and the GRASS Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.
"""

##TODO it is time to make this all multithreaded..

# %Module
# % description: Agents wander around on the terrain, marking paths to new locations.
# %End
# %option
# % key: outputmap
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of step output map
# % required : yes
# %end
# %flag
# % key: p
# % description: Allow overwriting existing output maps
# %end
# %option
# % key: costmap
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of penalty resp. cost raster map (note conversion checkbox)
# % required : yes
# %end
# %option
# % key: rounds
# % type: integer
# % gisprompt: number
# % description: Number of iterations/rounds to run
# % answer: 999
# % options: 0-999999
# % required : yes
# %end
# %option
# % key: mark
# % type: integer
# % gisprompt: number
# % description: Mark each step an agent takes
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: maxagents
# % type: integer
# % gisprompt: number
# % description: Maximum amount of agents that may live concurrently (x*y)
# % options: 0-<the bigger the playground, the more space they have>
# % required : no
# %end
# %option
# % key: agentslife
# % type: integer
# % gisprompt: number
# % description: Time to live for an agent
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: agentfreedom
# % type: integer
# % gisprompt: number
# % description: Number of possible directions the ant can take (4 or 8)
# % options: 4,8
# % required : no
# %end

import sys
from sys import exit, maxsize
from math import sqrt
from math import exp
from random import randint

try:
    from grass.script import core as grass
except ImportError:
    raise error.EnvError("r.agent.rand:", "Please run inside GRASS.")

from grass.pygrass.utils import set_path

set_path("r.agent", "libagent", "..")
from libagent import error, grassland, world


def setmaps(cost, output):
    """
    Set the user maps in place
    """
    if cost:
        if -1 == cost.find("@"):
            cost = cost + "@" + grass.gisenv()["MAPSET"]
        # set cost/penalty layer
        world.playground.setgrasslayer("COST", cost, True)
    else:
        raise error.DataError("r.agent.rand:", "The cost map is mandatory.")
    if output:
        if -1 == output.find("@"):
            output = output + "@" + grass.gisenv()["MAPSET"]
        world.playground.setgrasslayer("RESULT", output, True)
    else:
        raise error.DataError("r.agent.rand:", "The output map is mandatory.")


#    world.playground.grassmapnames['RESULT'] = output
# TODO hopefully not really needed - workaround for broken(?) garray
#    world.playground.createlayer("copy", output, True)
#    world.playground.grassmapnames["copy"] = output


def run(rounds, maxagents, agentlife, mark, overwrite):
    """
    Organize the agents on the playground.
    """
    for i in range(rounds):
        for i in range(int(maxagents) - len(world.agents)):
            world.bear(agentlife)
        for i in range(len(world.agents)):
            agent = world.agents[i]
            agent.step()
            position = agent.getposition()
            newvalue = world.playground.getcellvalue("RESULT", position) + mark
            world.playground.setcellvalue("RESULT", position, newvalue)
    world.playground.writelayer("RESULT", False, overwrite)


def main():
    try:
        setmaps(options["costmap"], options["outputmap"])
    except error.DataError:
        grass.fatal("Failed to parse args..")
        sys.exit(1)
    if options["maxagents"]:
        maxagents = int(options["maxagents"])
    else:
        maxagents = 99
    if options["agentslife"]:
        agentslife = int(options["agentslife"])
    else:
        agentslife = 99
    if options["mark"]:
        mark = int(options["mark"])
    else:
        mark = 99

    run(int(options["rounds"]), maxagents, agentslife, mark, flags["p"])
    grass.message("FINISH")


if __name__ == "__main__":
    options, flags = grass.parser()
    world = world.World(grassland.Grassland())
    main()
