#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.move.points
#
# AUTHOR(S):    Vaclav Petras
#
# PURPOSE:      Update a column values using Python expressions
#
# COPYRIGHT:    (C) 2023 by Vaclav Petras and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Move points by distance specified in a raster
# % keyword: vector
# % keyword:
# % keyword:
# % keyword:
# %end
# %option G_OPT_V_INPUT
# %end
# %option G_OPT_R_INPUT
# %key: x_raster
# %end
# %option G_OPT_R_INPUT
# %key: y_raster
# %end
# %option G_OPT_V_OUTPUT
# %end

import math

import grass.script as gs


def move_vector(input_vector_name, output_vector_name, x_raster_name, y_raster_name):
    # Lazy import ctypes
    # pylint: disable=import-outside-toplevel
    import ctypes

    from grass.pygrass.gis.region import Region
    from grass.pygrass.raster import RasterSegment
    from grass.pygrass.utils import coor2pixel
    from grass.pygrass.vector import VectorTopo
    from grass.pygrass.vector.geometry import Line, Point
    from grass.lib.vector import Vect_cat_set, Vect_cat_get

    x_raster = RasterSegment(x_raster_name)
    x_raster.open("r")
    y_raster = RasterSegment(y_raster_name)
    y_raster.open("r")

    region = Region()

    with VectorTopo(input_vector_name, mode="r") as input_vector, VectorTopo(
        output_vector_name, mode="w"
    ) as output_vector:
        for feature in input_vector:
            first_cat = ctypes.c_int()
            Vect_cat_get(feature.c_cats, 1, ctypes.byref(first_cat))
            new_point_list = []
            for point in feature:
                pixel = coor2pixel((point.x, point.y), region)
                x_value = x_raster[int(pixel[0]), int(pixel[1])]
                y_value = y_raster[int(pixel[0]), int(pixel[1])]
                if math.isnan(x_value):
                    # NULL is zero.
                    # Implement also null is warning (boolean) and null is error (raise here).
                    x_value = 0
                if math.isnan(y_value):
                    y_value = 0
                point = Point(point.x + x_value, point.y + y_value)
                new_point_list.append(point)
            new_line = Line(new_point_list)
            Vect_cat_set(new_line.c_cats, 1, first_cat.value)
            output_vector.write(new_line)

    x_raster.close()
    y_raster.close()


def main():
    options, unused_flags = gs.parser()

    input_vector_name = options["input"]
    x_raster_name = options["x_raster"]
    y_raster_name = options["y_raster"]
    output_vector_name = options["output"]

    move_vector(
        input_vector_name=input_vector_name,
        x_raster_name=x_raster_name,
        y_raster_name=y_raster_name,
        output_vector_name=output_vector_name,
    )


if __name__ == "__main__":
    main()
