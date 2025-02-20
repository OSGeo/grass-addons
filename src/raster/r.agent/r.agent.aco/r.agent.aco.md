## DESCRIPTION

As a first real example of a world there is an ACO-based environment
(see [Ant Colony
Optimization](https://en.wikipedia.org/wiki/Ant_colony_optimization_algorithms))
available.

The basic concept of such an ACO world, is to take some cost surface and
transform it to a penalty layer. Even if the algorithm comes from the
realm of insects, it might be adapted to different animal kingdoms.
Depending on the type of agent this penalty layer must be reinterpreted:
if for example, we want to talk about human agents the penalty layer may
be expressed by the walking velocity, e.g. calculated with the algorithm
proposed by
[Tobler1993](https://web.archive.org/web/20220523095740/http://www.geodyssey.com/papers/tobler93.html).
The actors on the playground will wander around on the playground using
the time for their paths that correspond with the values in the penalty
grid. If they find some attractor, they walk home to the position they
originated, marking their way with pheromones. While this pheromone
vanishes over time, the following agents are more likely to choose their
next steps to a position that smells most.

This first toolset was mainly developed for [Topoi Project
A-III-4](https://www.topoi.org/group/a-iii-4-topoi-1/), with some
inspirations from previous work conducted at the [Uni
Bern](https://www.unibe.ch/) in 2008.

## NOTES

The state of this software is: "first do it".

ACO works best on dynamic maps -- it constantly tries to improve
paths...

## EXAMPLE

A fictive use case could look something like this (note: at the moment
the in- and output variables with *libold*, are still ascii-files):

```sh
r.agent.aco outputmap=out.map penaltymap=testpenalty.grid \
  sitesmap=sites.vect rounds=100 outrounds=100 volatilizationtime=5000 \
  antslife=2000 maxants=400 pathintensity=1000000
```

For running the total test suite on the libraries, i.e. to run all the
tests that are at the end of each python file, use this test collection
(for certain tests, the following files must exist though: "elev.grid",
and "arch.vect"):

```sh
user@host:~$ cd /<pathtoaddons>/r.agent/libagent

user@host:libold$ ./alltests.py
```

## TODO

Integrate it directly within grass.

Improve encapsulation of classes.

Find good parameters, or parameter finding strategies for the ACO part.
Try to avoid high penalty fields. Think about heuristics too.

Implement other ABM scenarios.

## SEE ALSO

## AUTHOR

Michael Lustenberger inofix.ch
