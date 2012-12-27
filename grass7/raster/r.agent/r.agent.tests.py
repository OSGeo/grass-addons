#!/usr/bin/env python

def dotest(function, argv):
    """Global wrapper for the individual test suits."""
    while True:
        n = function.func_doc
        o = str(argv)
        if not n:
            n = str(function)
        t = str(raw_input("execute this now: '"+n+" - "+o+"'? [y/n/abort] "))
        if t == "y":
            if argv != None:
                function(*argv)
            else:
                function()
            break
        elif t == "n":
            break
        elif t == "abort":
            exit()

def testPlayground():
    """Test suite for Class: Playground"""
    pg = playground.Playground()
    
    print(pg.region)

def testWorld():
    """Test suite for Class: World"""
    w = world.World()

def testACO():
    """Test suite for World-Class: ACO"""
    w = aco.ACO()

def testAgent(ttl):
    """Test suite for Class: Agent"""
    w = world.World()
    w = agent.Agent(ttl, w)

def testAnt(ttl, position):
    """Test suite for Agent-Class: Ant"""
    w = world.World()
    w = ant.Ant(ttl, w, position)

if __name__ == "__main__":
    """Main method for testing when run as a script."""
    import sys
    import os

    from libagent import error

    if os.environ.get("GISBASE") == None:
        raise error.EnvError("r.agent::TestSuite", "Please run inside GRASS.")

    from libagent import playground
    from libagent import world
    from libagent import aco
    from libagent import agent
    from libagent import ant

    alltests = {"playground":[testPlayground, []],
                "world":[testWorld, []],
                "aco":[testACO, []],
                "Agent":[testAgent, [1]],
                "Ant":[testAnt, [1, []]]}

    if len(sys.argv) == 1:
        for test,details in alltests.iteritems():
            dotest(details[0], details[1])
    else:
        sys.argv.pop(0)
        for t in sys.argv:
            if t in alltests:
                dotest(*alltests[t])
            else:
                print("Test does not exist: ", t)


