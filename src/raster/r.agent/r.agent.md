## DESCRIPTION

*r.agent* consists of a library *libagent* and some submodules which use
this it. The submodules are described in their resp. directories. The
library provides the basic functionality to introduce agent based
modeling on raster maps and fully integrates with GRASS thanks to the
new python API\!

For a maximum of transparency and the hope that it might serve as a
framework to build more submodules on it, it is written in python and in
an object oriented manner.

Let's think of the maps and layers as playgrounds where little worlds
with agents may evolve.

Please note the *tests* subfolder. It contains unit tests that might be
called after each change on the library to verify that nothing was
broken during the development.

## SEE ALSO

  - [r.agent.aco](r.agent.aco.md): Agents wander around on the terrain,
    marking paths to new locations.
  - [r.agent.rand](r.agent.rand.md): Agents wander around on the
    terrain, marking paths to new locations.

## AUTHOR

Michael Lustenberger inofix.ch
