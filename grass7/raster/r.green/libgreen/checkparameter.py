# -*- coding: utf-8 -*-
from grass.exceptions import ParameterError
from grass.pygrass.messages import get_msgr
from grass.pygrass.raster import RasterRow
from grass.pygrass.vector import VectorTopo


def check_required_columns(vname, layer, reqcols, pname):
    """Check if the vector input maps has the right columns
    in the attribute table."""
    vname, mset = vname.split('@') if '@' in vname else (vname, '')
    with VectorTopo(vname, mset, mode='r', layer=layer) as vect:
        columns = vect.table.columns
    for col in reqcols:
        if col not in columns:
            msg = ("Parameter: %s require the following columns: %r,"
                   " %s is missing")
            raise ParameterError(msg % (pname, reqcols, col))
    return vect


def check_range(value, min=0., max=1.):
    """Check if a value is between a range"""
    if value < min or value > max:
        raise ParameterError("Value not between: %f, %f" % (min, max))
    return value


def check_float_or_raster(parameter, min=None, max=None):
    """Check if the parameter is a float or a raster map in a certain range."""
    try:
        par = float(parameter)
        if min is not None and max is not None:
            par = check_range(par, min, max)
    except:
        try:
            rname, mset = (parameter.split('@') if '@' in parameter
                           else (parameter, ''))
            if min is not None and max is not None:
                with RasterRow(rname, mset) as rst:
                    mn, mx = rst.info.range
                    check_range(mn, min, max)
                    check_range(mx, min, max)
            par = parameter
        except:
            raise ParameterError("Raster is not readable or not in a range")
    return par


def exception2error(exc):
    get_msgr().error(str(exc.args[0] if len(exc.args) == 1 else str(exc.args)))
