## DESCRIPTION

*v.net.salesman.opt* estimates the optimal route to visit nodes on a
vector network and optionally tries to improve the result.

Costs may be either line lengths, or attributes saved in a database
table. These attribute values are taken as costs of whole segments, not
as costs to traverse a length unit (e.g. meter) of the segment. For
example, if the speed limit is 100 km / h, the cost to traverse a 10 km
long road segment must be calculated as length / speed = 10 km / (100
km/h) = 0.1 h. Supported are cost assignments for arcs, and also
different costs for both directions of a vector line. For areas, costs
will be calculated along boundary lines.

The input vector needs to be prepared with *v.net operation=connect* in
order to connect points representing center nodes to the network.

Points specified by category must be exactly on network nodes, and the
input vector map needs to be prepared with *v.net operation=connect*.

### Optimization

For less than 10 nodes, the initial result is usually very close to the
shortest possible tour and further optimization will have no effect.

*v.net.salesman.opt* uses the same heuristics like *v.net.salesman.opt*
to find a good tour which is not necessarily the optimal tour. The tour
can be optimized with two methods: bootstrapping and genetic algorithm
(GA). The bootstrapping method removes a subtour from the tour and
reinserts the nodes resulting in a shorter tour. This is applied on
intermediate tours and the final tour.

The genetic algorithm first creates several initial tours. From these
tours nearly identical toursare eliminated. The remaining tours are
recombined to create new, better tours. All tours are now mutated. The
sequence of Selection, Recombination, Mutation is repeated until there
is no better solution. Finally, the best tour is optimized with
bootstrapping.

## NOTES

Arcs can be closed using cost = -1.

## EXAMPLE

Visiting all 167 schools (North Carolina):

```sh
# North Carolina

# prepare network by connecting schools to streets
v.net -c input=streets_wake points=schools_wake output=streets_schools \
  operation=connect alayer=1 nlayer=2 thresh=1000

# verify data preparation
v.category in=streets_schools op=report
# type       count        min        max
# point          6          1          6

# find the shortest path
v.net.salesman.opt in=streets_schools ccats=1-167 out=schools_tour

# Resulting tour length: 551551.662

# find the shortest path, optimize with genetic algorithm
v.net.salesman.opt in=streets_schools ccats=1-167 out=schools_tour_ga method=ga

# Resulting tour length: 521191.083
# The original tour was 5.8% longer

# find the shortest path, optimize with bootstrapping
v.net.salesman.opt in=streets_schools ccats=1-167 out=schools_tour_bs method=bs

# Resulting tour length: 510693.965
# The original tour was 8.0% longer

```

## SEE ALSO

*[d.path](https://grass.osgeo.org/grass-stable/manuals/d.path.html)*,
*[v.net](https://grass.osgeo.org/grass-stable/manuals/v.net.html)*,
*[v.net.alloc](https://grass.osgeo.org/grass-stable/manuals/v.net.alloc.html)*,
*[v.net.iso](https://grass.osgeo.org/grass-stable/manuals/v.net.iso.html)*,
*[v.net.path](https://grass.osgeo.org/grass-stable/manuals/v.net.path.html)*,
*[v.net.steiner](https://grass.osgeo.org/grass-stable/manuals/v.net.steiner.html)*

## AUTHORS

Radim Blazek, ITC-Irst, Trento, Italy  
Markus Metz  
Documentation: Markus Neteler, Markus Metz
