#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.rast.move
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
# %option
# % key: nulls
# % type: string
# % options: zeros,warning,error
# % label: Handling of null values
# % description: Null (no-data) values in rasters will be considered zeros, cause a warning or an error
# % description: zeros;Null value will be converted to zeros;warning;A null value will cause a warning (one for each raster) and will be converted to zero;error;A null value will cause an error
# %end
# %option G_OPT_V_OUTPUT
# %end

import math

import grass.script as gs


class NullValue(RuntimeError):
    """Raised when null value is not allowed and encountered"""


class OutOfBounds(RuntimeError):
    """Raised when vector extent is large than region (raster) extent"""


def move_vector(
    input_vector_name, output_vector_name, x_raster_name, y_raster_name, handle_nulls
):
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

    x_null = y_null = 0

    with VectorTopo(input_vector_name, mode="r") as input_vector, VectorTopo(
        output_vector_name, mode="w"
    ) as output_vector:
        for feature in input_vector:
            first_cat = ctypes.c_int()
            Vect_cat_get(feature.c_cats, 1, ctypes.byref(first_cat))
            new_point_list = []
            for point in feature:
                pixel = coor2pixel((point.x, point.y), region)
                if (
                    pixel[0] < 0
                    or pixel[0] >= region.rows
                    or pixel[1] < 0
                    or pixel[1] >= region.cols
                ):
                    raise OutOfBounds(
                        _(
                            "Part of the vector ({x}, {y}) is outside of extent "
                            "defined by the computational region"
                        ).format(x=point.x, y=point.y)
                    )
                x_value = x_raster[int(pixel[0]), int(pixel[1])]
                y_value = y_raster[int(pixel[0]), int(pixel[1])]
                if math.isnan(x_value):
                    if handle_nulls == "zeros":
                        x_value = 0
                    elif handle_nulls == "warning":
                        x_null += 1
                        x_value = 0
                    else:
                        raise NullValue(
                            _(
                                "Null value encountered in {raster} (X) at {x},{y}"
                            ).format(raster=x_raster_name, x=point.x, y=point.y)
                        )
                if math.isnan(y_value):
                    if handle_nulls == "zeros":
                        y_value = 0
                    elif handle_nulls == "warning":
                        y_null += 1
                        y_value = 0
                    else:
                        raise NullValue(
                            _(
                                "Null value encountered in {raster} (Y) at {x},{y}"
                            ).format(raster=y_raster_name, x=point.x, y=point.y)
                        )
                point = Point(point.x + x_value, point.y + y_value)
                new_point_list.append(point)
            new_line = Line(new_point_list)
            Vect_cat_set(new_line.c_cats, 1, first_cat.value)
            output_vector.write(new_line)

    if x_null:
        gs.warning(
            _("Null value encountered in {raster} (X): {n}x").format(
                raster=x_raster_name, n=x_null
            )
        )
    if y_null:
        gs.warning(
            _("Null value encountered in {raster} (Y): {n}x").format(
                raster=y_raster_name, n=y_null
            )
        )

    x_raster.close()
    y_raster.close()


def main():
    options, unused_flags = gs.parser()

    input_vector_name = options["input"]
    x_raster_name = options["x_raster"]
    y_raster_name = options["y_raster"]
    output_vector_name = options["output"]

    try:
        move_vector(
            input_vector_name=input_vector_name,
            x_raster_name=x_raster_name,
            y_raster_name=y_raster_name,
            output_vector_name=output_vector_name,
            handle_nulls=options["nulls"],
        )
    except (NullValue, OutOfBounds) as error:
        gs.fatal(error)


if __name__ == "__main__":
    main()
