Script to generate GRASS location from outside GRASS
from GIS file (e.g. geoTIFF or SHAPE), wktfile or EPSG code.

TODO: rewrite as Python script. A partial solution is
implementedin GRASS 7:

* grass.create_location() [1] for unprojected locations, 
  for the rest is needed running GRASS session (`g.proj`).

[1] http://grass.osgeo.org/programming7/namespacepython_1_1core.html#a0e55b38e9bb8c7b104e8884f26dc618a
