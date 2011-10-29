############################################################################
#
# MODULE:       r.agent.*
# AUTHOR(S):    michael lustenberger inofix.ch
# PURPOSE:      library file for the r.agent.* suite
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

from random import choice, randint
import agent
import error

class Ant(agent.Agent):
    """custom"""
    def __init__(self, timetolive, world, position):
        agent.Agent.__init__(self, timetolive, world, position)
        self.position.extend([None,None,0,0])
        self.home = self.position[:]
        self.laststeps = [self.position[:]]
        self.visitedsteps = []
        self.done = False
        self.nextstep = [None,None,0,0,0,0]
        self.goal = []
        self.penalty = 0.0
        self.steppaint = world.stepintensity
        self.pathpaint = world.pathintensity
        if world.decisionbase == "standard":
            self.pickaposition = self.smellposition
            self.pheroweight = self.world.pheroweight * 2
            self.randomweight = self.world.randomweight * 2
        elif world.decisionbase == "random":
            self.pickaposition = self.randomposition
        elif world.decisionbase == "test":
            self.pickaposition = self.testposition
            self.pheroweight = self.world.pheroweight * 2
            self.randomweight = self.world.randomweight * 2
        if world.validposition == "avoidloop":
            self.haspositions = self.avoidloop
        elif world.validposition == "forgetloop":
            self.haspositions = self.forgetloop
        elif world.validposition == "avoidorforgetloop":
            self.haspositions = self.avoidorforgetloop
        elif world.validposition == "specials":
            self.haspositions = self.searchspecials
    def paint(self, position, value):
#TODO mv to tests:
        if self.world.pherovapour[position[0]][position[1]] < 0:
            print "home:", self.home, "paint:", position, ":", value
            raise error.Error("Ant.paint()", "Not painting over specials.")
        if self.world.maxpheromone-value > \
         self.world.pherovapour[position[0]][position[1]]:
            self.world.pherovapour[position[0]][position[1]] += value
    def randomposition(self, positions):
        self.nextstep = positions[randint(0, len(positions)-1)]
    def testposition(self, positions):
        i = 0
        l = []
        for pos in positions:
            l.append([pos[3]/self.randomweight+randint(0,\
                self.world.maxpheromone)/self.pheroweight, i])
            i += 1
        l.sort()
        self.nextstep = positions[l[0][1]]
#TODO add some position search alg that avoids high penalties..
    def smellposition(self, positions):
        self.nextstep = positions[0]
        self.nextstep[3] = self.nextstep[3]/self.randomweight+ \
                    randint(0,self.world.maxpheromone)/self.pheroweight
        for pos in positions[1:]:
            pos[3] = pos[3]/self.randomweight+ \
                    randint(0,self.world.maxpheromone)/self.pheroweight
            if self.nextstep[3] < pos[3]:
                self.nextstep = pos
    def avoidloop(self, positions):
        ''' This method tries to avoid stepping on already passed
            nodes. That it is basically. '''
        # remember all positions for worst case..
        temppositions = positions[:]
        for last in self.laststeps[:]:
            for pos in positions[:]:
                if last[0] == pos[0] and last[1] == pos[1]:
                    # position already visited once..
                    try:
                        positions.remove(pos)
                    except ValueError:
                        pass
        if len(positions) == 0:
            # can not be special value, because it would already be visited
            # make sure it is not home
            pos = choice(temppositions)
            if pos[0] == self.home[0] and pos[1] == self.home[1]:
                temppositions.remove(pos)
                pos = choice(temppositions)
            # if none was left: choose another one by chance
            # no need to proceed with choosing from only one position
            self.nextstep = pos
            return True
        else:
            for pos in positions[:]:
                if pos[3] < 0:
                    # home is already handled because visited
                    # goal node found. add one to the counter
                    self.world.nrop += 1
                    self.done = True
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False       
    def avoidorforgetloop(self, positions):
        ''' This method tries to avoid stepping on already passed
            nodes. If this is not possible or if a path is coming
            close to such nodes in the grid, it will grant not to
            produce loops by deleting all intermediate steps.'''
        # remember all positions for worst case..
        temppositions = positions[:]
        # initially start with no loop found
        hasposition = False
        # search for loops, but exclude last step from process (keep it)
        for last in self.laststeps[:]:
            if hasposition == True:
                # remove loop, but remember visited steps
                self.visitedsteps.append(last)
                self.laststeps.remove(last)
            else:
                # search for loop in positions
                for pos in positions[:]:
                    if last[0] == pos[0] and last[1] == pos[1]:
                        # shortcut found, so remove loop
                        hasposition = True
                        # remove that position from possible next ones
                        positions.remove(pos)
                        # change direction penalty to new shortcut
                        self.laststeps[-1][4] = pos[4]
        # remove all yet visited nodes from possible next positions
        for visited in self.visitedsteps:
            for pos in positions[:]:
                if visited[0] == pos[0] and visited[1] == pos[1]:
                    # do not step on visited nodes again
                    positions.remove(pos)
        if len(positions) == 0:
            # can not be special value, because it would already be visited
            # make sure it is not home
            pos = choice(temppositions)
            if pos[0] == self.home[0] and pos[1] == self.home[1]:
                temppositions.remove(pos)
                pos = choice(temppositions)
            # if none was left: choose another one by chance
            # no need to proceed with choosing from only one position
            self.nextstep = pos
            return True
        else:
            for pos in positions[:]:
                if pos[3] < 0:
                    # home is already handled because visited
                    # goal node found. add one to the counter
                    self.world.nrop += 1
                    self.done = True
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False
    def forgetloop(self, positions):
        ''' This method deletes all positions that form a loop in the
            path. It also prohibits to walk back one step both to the
            true former position, and to the assumed last step on the
            newly created shortcut.'''
        # initially start with no loop found
        hasposition = False
        # search for loops, but exclude last step from process (keep it)
        for last in self.laststeps[:-1]:
            if hasposition == True:
                # remove loop
                self.laststeps.remove(last)
            else:
                # search for loop in positions
                for pos in positions[:]:
                    if last[0] == pos[0] and last[1] == pos[1]:
                        # shortcut found, so remove loop
                        hasposition = True
                        # remove that position from possible next ones
                        positions.remove(pos)
                        # change direction penalty for laststep to new shortcut
                        self.laststeps[-1][4] = pos[4]
        for pos in positions[:]:
            if pos[3] < 0:
                # promissing, but home is not excluded (only loops are..)
                if pos[0] == self.home[0] and pos[1] == self.home[1]:
                    # so, make sure it is not home..
                    positions.remove(pos)
                else:
                    # goal node found. add one to the counter
                    self.world.nrop += 1
                    self.done = True
                    # now, head back home..
                    self.nextstep = self.laststeps.pop()
                    return True
        return False
    def searchspecials(self, positions):
        for pos in positions[:]:
            if pos[3] < 0:
                # nice value found, goal might be reached
                if pos[0] == self.home[0] and pos[1] == self.home[1]:
                    # make sure it is not home..
                    positions.remove(pos)
                else:
                    # this is it! add one to the counter
                    self.world.nrop += 1
                    self.done = True
                    self.nextstep = self.laststeps.pop()
                    return True
        return False
    def choose(self):
        positions = self.world.getneighbourpositions(self.position)
        # remove last step from possible neighbourpositions
        try:
            positions.remove(self.laststeps[len(self.laststeps)-1])
        except ValueError:
            pass
        if not self.haspositions(positions):
            self.pickaposition(positions)
    def walk(self):
        # we are all only getting older..
        if self.age() == False:
            return False
        # if we do not have decided yet where to go to..
        if self.nextstep[0] == None:
            self.choose()
        # if penalty is positive, wait one round
        if self.penalty > 0:
            self.penalty -= 1
        else:
            # add penalty from direction or underground
# TODO: think about adding 1 to each and then multiplicate them ;)
            self.penalty += self.nextstep[4] + self.nextstep[2]
            # are we luckily walking home?
            if self.done == True:
                # walk back home one step
                self.position = [self.nextstep[0],self.nextstep[1]]
                # mark current position as a good choice
                self.paint(self.position, self.pathpaint)
                if len(self.laststeps) > 1:
                    # next step towards back home
                    self.nextstep = self.laststeps.pop()
                else:
                    # retire after work
                    self.snuffit()
            else:
                # make a step
                self.position = self.nextstep
                # remember it
                self.laststeps.append(self.position)
                # clear nextstep for next round
                self.nextstep = [None,None,0,0,0,0]
                # mark current position
                self.paint(self.position, self.steppaint)

def test():
    """Test suite for Ant Class"""
    import aco
    print "creating a new world"
    w = aco.ACO()
    w.bounds = [5,0,5,0,6,6]
    w.playground.setbounds(5,0,5,0,6,6)
    print " limits set:",w.playground.getbounds()
    w.playground.setnewlayer("cost", "raster", True)
    w.costsurface = w.playground.getlayer("cost").raster
    w.playground.setnewlayer("phero", "raster", True)
    w.pherovapour = w.playground.getlayer("phero").raster
    print " playground looks like (cost+phero)"
    print " #c#",w.costsurface
    print " #p#",w.pherovapour
    w.holes = [[0,0,1]]
    print ""
    print "let's put some life in it.."
    w.bear(Ant,5,[0,0])
    a = w.agents[0]
    print " agent seems fine (for now). time to live:",str(a.ttl),\
        ". location:",a.position
    a.paint([0,0],500)
    a.paint([1,1],800)
    a.paint([1,2],900)
    print " playground(phero) after some painting:"
    print " ", w.pherovapour
    print "look around on positions.."
    positions = w.getneighbourpositions(a.position)
    print " tmp positions: ", positions
    print "- any special cells in raster? ",\
        a.searchspecials(positions)
    positions[1][3] = -1
    print "- any special cells in raster (marking one)? ",\
        a.searchspecials(positions)
    print "now die."
    a.snuffit()
    print ""
    print "new ant.."
    w.bear(Ant,5,[0,0])
    a = w.agents[0]
    print " agent seems fine (for now). time to live:",str(a.ttl),\
        ". location:",a.position
    print "let's do some positioning..."
    positions = w.getneighbourpositions(a.position)
    print "- now pickaposition:"
    a.randomposition(positions)
    print " a random choice: ", a.nextstep
    a.smellposition(positions)
    print " in smell-mode we would choose: ", a.nextstep
    a.testposition(positions)
    print " alternative test:", a.nextstep
    print "- hasposition alternatives"
    print " avoid walking in loops:"
    ps = positions[:]
    a.avoidloop(ps)
    print " ",ps
    ps = positions[:]
    print " forget loops:"
    a.forgetloop(ps)
    print " ",ps
    ps = positions[:]
    print " avoid or forget loops:"
    a.avoidorforgetloop(ps)
    print " ",ps
    print "- regularly choose a position now.. based on .. why not: smell."
    print positions
    a.choose()
    print " ant: I'd go there,", a.position
    print "- make a step forward then.."
    a.walk()
    print " ant: I am here now,", a.position
    print "all done."

