#!/usr/bin/env python
"""
MODULE:       r.agent.aco
AUTHOR(S):    michael lustenberger inofix.ch
PURPOSE:      r.agent.aco is used to organize ant-like agents in a raster
              based playground. As described by the Ant Colony Optimization
              algorithm, the ants wander around looking for attractors,
              marking their paths if they find any.
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
# % description: Name of pheromone output map
# % required : yes
# %end
# %option
# % key: inputmap
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of input pheromone raster map (e.g. from prior run)
# % required : no
# %end
# %flag
# % key: p
# % description: Allow overwriting existing pheromone maps
# %end
# %flag
# % key: s
# % description: Produce a sequence of pheromone maps (by appending a number)
# %end
# %flag
# % key: c
# % description: Overwrite existing cost map (only used with penalty conversion)
# %end
# %option
# % key: costmap
# % type: string
# % gisprompt: old,cell,raster
# % description: Name of penalty resp. cost raster map (note conversion checkbox)
# % required : yes
# %end
# %flag
# % key: a
# % description: Auto-convert cost (slope..) to penalty map (using "tobler", see docu)
# %end
# %flag
# % key: l
# % description: Avoid loops on the way back
# %end
# %option
# % key: sitesmap
# % type: string
# % gisprompt: old,vect,vector
# % description: Name of sites map, vector data with possible points of origin
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
# % key: outrounds
# % type: integer
# % gisprompt: number
# % description: Produce output after running this number of iterations/rounds
# % options: 0-999999
# % required : no
# %end
# %option
# TODO evaluate..
# % key: targetvisibility
# % type: integer
# % gisprompt: number
# % description: Distance to target from where it might be 'sensed'
# % options: 0-999999
# % required : no
# %end
# %option
# % key: highcostlimit
# % type: integer
# % gisprompt: number
# % description: Penalty values above this point an ant considers as illegal/bogus when in 'costlymarked' modus
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: lowcostlimit
# % type: integer
# % gisprompt: number
# % description: Penalty values below this point an ant considers as illegal/bogus when in 'costlymarked' modus
# % options: -99999-99999
# % required : no
# %end
# %option
# % key: maxpheromone
# % type: integer
# % gisprompt: number
# % description: Absolute maximum of pheromone intensity a position may have
# % options: <minpheromone>-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: minpheromone
# % type: integer
# % gisprompt: number
# % description: Absolute minimum of pheromone intensity to leave on playground
# % options: 0-<maxpheromone>
# % required : no
# %end
# %option
# % key: volatilizationtime
# % type: integer
# % gisprompt: number
# % description: Half-life for pheromone to volatize (e.g. =rounds)
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: stepintensity
# % type: integer
# % gisprompt: number
# % description: Pheromone intensity to leave on each step
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: pathintensity
# % type: integer
# % gisprompt: number
# % description: Pheromone intensity to leave on found paths
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: maxants
# % type: integer
# % gisprompt: number
# % description: Maximum amount of ants that may live concurrently (x*y)
# % options: 0-<the bigger the playground, the more space they have>
# % required : no
# %end
# %option
# % key: antslife
# % type: integer
# % gisprompt: number
# % description: Time to live for an ant (e.g. four times points distance)
# % options: 0-<max integer on system would make sense>
# % required : no
# %end
# %option
# % key: decisionalgorithm
# % type: string
# % gisprompt: algorithm
# % description: Algorithm used for walking step
# % answer: standard
# % options: standard,marked,costlymarked,random,test
# % required : yes
# %end
# %option
# % key: evaluateposition
# % type: string
# % gisprompt: algorithm
# % description: Algorithm used for finding and remembering paths
# % answer: avoidorforgetloop
# % options: standard,avoidloop,forgetloop,avoidorforgetloop
# % required : yes
# %end
# %option
# % key: agentfreedom
# % type: integer
# % gisprompt: number
# % description: Number of possible directions the ant can take (4 or 8)
# % options: 4,8
# % required : no
# %end
# %option
# % key: pheromoneweight
# % type: integer
# % gisprompt: number
# % description: How is the pheromone value (P) weighted when walking (p*P:r*R:c*C)
# % answer: 1
# % options: 0-99999
# % required : yes
# %end
# %option
# % key: randomnessweight
# % type: integer
# % gisprompt: number
# % description: How is the random value (R) weighted when walking (p*P:r*R:c*C)
# % answer: 1
# % options: 0-99999
# % required : yes
# %end
# %option
# % key: costweight
# % type: integer
# % gisprompt: number
# % description: How is the penalty value (C) weighted when walking (p*P:r*R:c*C)
# % answer: 0
# % options: 0-99999
# % required : yes
# %end

import sys
from sys import exit, maxsize
from math import sqrt
from math import exp
from random import randint

try:
    from grass.script import core as grass
except ImportError:
    raise error.EnvError("r.agent.aco:", "Please run inside GRASS.")

from grass.pygrass.utils import set_path

set_path("r.agent", "libagent", "..")
from libagent import error, grassland, anthill


def setmaps(site, cost, wastecosts, inphero, outphero, wastephero):
    """
    Set the user maps in place
    """
    if site:
        if -1 == site.find("@"):
            site = site + "@" + grass.gisenv()["MAPSET"]
        # set sitemap and site list
        world.sites = world.playground.parsevectorlayer(
            anthill.Anthill.SITE, site, -1, True
        )
        if not world.sites:
            raise error.DataError("r.agent.aco:", "There were no sites in" + site)
    else:
        raise error.DataError("r.agent.aco:", "The site map is mandatory.")
    if cost:
        if -1 == cost.find("@"):
            cost = cost + "@" + grass.gisenv()["MAPSET"]
        # set cost/penalty layer
        world.playground.setgrasslayer(anthill.Anthill.COST, cost, True)
        world.overwritepenalty = wastecosts
    else:
        raise error.DataError("r.agent.aco:", "The cost map is mandatory.")
    if outphero:
        if -1 == outphero.find("@"):
            outphero = outphero + "@" + grass.gisenv()["MAPSET"]
    else:
        raise error.DataError("r.agent.aco:", "The output map is mandatory.")
    if inphero == outphero:
        if not wastephero:
            raise error.DataError("aco:", "May not overwrite the output map.")
    if inphero:
        if -1 == inphero.find("@"):
            inphero = inphero + "@" + grass.gisenv()["MAPSET"]
        world.playground.setgrasslayer(anthill.Anthill.RESULT, inphero, True)
    world.playground.grassmapnames[anthill.Anthill.RESULT] = outphero
    # TODO hopefully not really needed - workaround for broken(?) garray
    world.playground.createlayer("copy", outphero, True)
    world.playground.grassmapnames["copy"] = outphero
    world.overwritepheormone = wastephero


def letantsdance(rounds, outrounds):
    """
    Organize the agents and the pheromone on the playground.
    """
    if world.addsequencenumber:
        outputmapbasename = world.playground.grassmapnames[
            anthill.Anthill.RESULT
        ].split("@")
    else:
        outputmapbasename = False
        outputmapname = False
    if 0 < outrounds < rounds:
        # calculate when to write output
        mainloops = rounds / outrounds
        nextwrite = outrounds
    else:
        # produce output only at the end
        mainloops = 1
        nextwrite = rounds
    run = 0
    while run < mainloops:
        if outputmapbasename:
            outputmapname = outputmapbasename[0] + str(run) + "@" + outputmapbasename[1]
        # loop and write out the contents at the end
        world.letantsdance(nextwrite)
        # Print the number of found paths
        grass.info("Number of found paths: " + str(world.numberofpaths))
        # export the value maps
        # TODO hopefully not really needed - workaround for broken(?) garray
        for i in range(len(world.playground.layers[anthill.Anthill.RESULT])):
            for j in range(len(world.playground.layers[anthill.Anthill.RESULT][0])):
                world.playground.layers["copy"][i][j] = world.playground.layers[
                    anthill.Anthill.RESULT
                ][i][j]
        world.playground.writelayer("copy", outputmapname, world.overwritepheormone)
        # TODO world.playground.writelayer(anthill.Anthill.RESULT, False,
        # TODO                                    world.overwritepheormone)
        #        print "nrofpaths:", world.nrop
        # count down outer
        run += 1


#    print "nrofrounds", nrofrounds


def main():

    try:
        setmaps(
            options["sitesmap"],
            options["costmap"],
            flags["c"],
            options["inputmap"],
            options["outputmap"],
            flags["p"],
        )

        #        world.playground.setboundsfromlayer("costs")
        if not options["outrounds"]:
            options["outrounds"] = 0
        elif flags["s"] and options["outrounds"] > 0:
            world.addsequencenumber = True

        if flags["s"]:
            world.antavoidsloops = True
        if options["lowcostlimit"]:
            world.minpenalty = int(options["lowcostlimit"])
        if options["highcostlimit"]:
            world.maxpenalty = int(options["highcostlimit"])
        if options["maxpheromone"]:
            world.maxpheromone = int(options["maxpheromone"])
            world.maxrandom = world.maxpheromone
        if options["minpheromone"]:
            world.minpheromone = int(options["minpheromone"])
            world.minrandom = world.minpheromone
        if options["volatilizationtime"]:
            world.volatilizationtime = int(options["volatilizationtime"])
        if options["stepintensity"]:
            world.stepintensity = int(options["stepintensity"])
        if options["pathintensity"]:
            world.pathintensity = int(options["pathintensity"])
        if options["maxants"]:
            world.maxants = int(options["maxants"])
        if options["antslife"]:
            world.antslife = int(options["antslife"])
        if options["decisionalgorithm"]:
            world.decisionbase = str(options["decisionalgorithm"])
        if options["evaluateposition"]:
            world.evaluationbase = str(options["evaluateposition"])
        #        if options['agentfreedom']:
        #            world.globalfreedom = int(options['agentfreedom'])
        if options["pheromoneweight"]:
            world.pheroweight = int(options["pheromoneweight"])
        if options["randomnessweight"]:
            world.randomweight = int(options["randomnessweight"])
        if options["costweight"]:
            world.costweight = int(options["costweight"])
        # if arglist[0] == "stability":
        # TODO ask silvia..

    #        world.checkvalues()
    except error.DataError:
        grass.fatal("Failed to parse args..")
        sys.exit(1)
    letantsdance(int(options["rounds"]), int(options["outrounds"]))
    grass.message("FINISH")


if __name__ == "__main__":
    options, flags = grass.parser()
    world = anthill.Anthill(grassland.Grassland())
    main()
