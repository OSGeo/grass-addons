#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.economic
# AUTHOR(S):   Sandro Sacchelli (BASH-concept), Pietro Zambelli (Python)
# PURPOSE:     Assess the hydro plant costs
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
#%Module
#% description: Compute the economic costs and values
#% overwrite: yes
#%End
#%option G_OPT_V_MAP
#%  key: plant
#%  description: Name of the input vector map with the plants
#%  required: yes
#%end
#%option G_OPT_V_INPUT
#%  key: plant_layer
#%  description: Name of the vector map layer of other plants, with the following attributes: kind (water intake/turbine), discharge [m3/year], id point, id plant
#%  required: no
#%  answer: 1
#%end
#############################################################################
# DEFINE COLUMNS OF V INPUT
#%option
#%  key: plant_id_column
#%  type: string
#%  description: Column name with the plant id.
#%  required: no
#%  answer: plant_id
#%  guisection: Input columns
#%end
#%option
#%  key: plant_power_column
#%  type: string
#%  description: Column name with power value.
#%  required: no
#%  answer: power
#%  guisection: Input columns
#%end
#%option
#%  key: plant_head_column
#%  type: string
#%  description: Column name with head value.
#%  required: no
#%  answer: head
#%  guisection: Input columns
#%end
#%option
#%  key: plant_side_column
#%  type: string
#%  description: Column name with a string that define the side of the plant
#%  required: no
#%  answer: side
#%  guisection: Input columns
#%end
#%option
#%  key: plant_kind_column
#%  type: string
#%  description: Column name with the strings that define if it is conduct or penstock.
#%  required: no
#%  answer: kind
#%  guisection: Input columns
#%end
#%option
#%  key: plant_kind_intake
#%  type: string
#%  description: Value contained in the column 'kind' which corresponds to the derivation (conduct).
#%  required: no
#%  answer: conduct
#%  guisection: Input columns
#%end
#%option
#%  key: plant_kind_turbine
#%  type: string
#%  description: Value contained in the column 'kind' which corresponds to the penstock.
#%  required: no
#%  answer: penstock
#%  guisection: Input columns
#%end


#############################################################################
# DEFINE COMPENSATION COSTS
# provide raster

#%option
#%  key: interest_rate
#%  type: double
#%  description: Interest rate value
#%  required: no
#%  answer: 0.03
#%  guisection: Compensation
#%end
#%option
#%  key: gamma_comp
#%  type: double
#%  description: Coefficient
#%  required: no
#%  answer: 1.25
#%  guisection: Compensation
#%end
#%option
#%  key: life
#%  type: double
#%  description: Life of the hydropower plant [year]
#%  required: no
#%  answer: 30
#%  guisection: Compensation
#%end


#%option G_OPT_R_INPUT
#%  key: landvalue
#%  description: Name of the raster map with the land value [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option G_OPT_R_INPUT
#%  key: tributes
#%  description: Name of the raster map with the tributes [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option G_OPT_R_INPUT
#%  key: stumpage
#%  description: Name of the raster map with the stumpage value [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option G_OPT_R_INPUT
#%  key: rotation
#%  description: Name of the raster map with the rotation period per landuse type [year].
#%  required: no
#%  guisection: Compensation
#%end
#%option G_OPT_R_INPUT
#%  key: age
#%  description: Name of the raster map with the average age [year].
#%  required: no
#%  guisection: Compensation
#%end

# or rule to transform landuse categories in raster maps
#%option G_OPT_R_INPUT
#%  key: landuse
#%  description: Name of the raster map with the landuse categories.
#%  required: no
#%  guisection: Compensation
#%end

# RULES
#%option
#%  key: rules_landvalue
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a value [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option
#%  key: rules_tributes
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a tribute rate [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option
#%  key: rules_stumpage
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a stumpage value [currency/ha].
#%  required: no
#%  guisection: Compensation
#%end
#%option
#%  key: rules_rotation
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a rotation value [year].
#%  required: no
#%  guisection: Compensation
#%end
#%option
#%  key: rules_age
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse an age [year].
#%  required: no
#%  guisection: Compensation
#%end

#############################################################################
# DEFINE EXCAVATION COSTS

#%option
#%  key: width
#%  type: double
#%  description: With of the excavation works [m]
#%  required: no
#%  answer: 2.
#%  guisection: Excavation
#%end
#%option
#%  key: depth
#%  type: double
#%  description:Depth of the excavation works [m]
#%  required: no
#%  answer: 2.
#%  guisection: Excavation
#%end
#%option
#%  key: slope_limit
#%  type: double
#%  description: Slope limit, above this limit the cost will equal to the maximum [degree]
#%  required: no
#%  answer: 50.
#%  guisection: Excavation
#%end

# provide raster maps

#%option G_OPT_R_INPUT
#%  key: min_exc
#%  description: Minimum excavation costs [currency/mc]
#%  required: no
#%  guisection: Excavation
#%end
#%option G_OPT_R_INPUT
#%  key: max_exc
#%  description: Maximum excavation costs [currency/mc]
#%  required: no
#%  guisection: Excavation
#%end
#%option G_OPT_R_INPUT
#%  key: slope
#%  description: Slope raster map
#%  required: yes
#%  guisection: Excavation
#%end



# RULES
#%option
#%  key: rules_min_exc
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a minimum excavation cost [currency/mc].
#%  required: no
#%  guisection: Excavation
#%end
#%option
#%  key: rules_max_exc
#%  type: string
#%  description: Rule file for the reclassification of the landuse to associate for each landuse a maximum excavation cost [currency/mc].
#%  required: no
#%  guisection: Excavation
#%end

#############################################################################
# DEFINE ELECTROMECHANICAL COSTS
#%option
#%  key: alpha_em
#%  type: double
#%  description: Electro-mechanical parameter costs, default values taken from Aggidis et al. 2010
#%  required: no
#%  answer: 0.56
#%  guisection: Electro-mechanical
#%end
#%option
#%  key: beta_em
#%  type: double
#%  description: Electro-mechanical parameter costs, default values taken from Aggidis et al. 2010
#%  required: no
#%  answer: -0.112
#%  guisection: Electro-mechanical
#%end
#%option
#%  key: gamma_em
#%  type: double
#%  description: Electro-mechanical parameter costs, default values taken from Aggidis et al. 2010
#%  required: no
#%  answer: 15600.0
#%  guisection: Electro-mechanical
#%end
#%option
#%  key: const_em
#%  type: double
#%  description: Electro-mechanical parameter costs constant value, default values taken from Aggidis et al. 2010
#%  required: no
#%  answer: 0.
#%  guisection: Electro-mechanical
#%end

#############################################################################
# DEFINE SUPPLY AND INSTALLATION COSTS
#%option
#%  key: lc_pipe
#%  type: double
#%  description: Supply and installation linear cost for the pipeline [currency/m]
#%  answer: 310.
#%  guisection: Supply & Installation
#%end
#%option
#%  key: lc_electro
#%  type: double
#%  description: Supply and installation linear cost for the electroline [currency/m]
#%  answer: 250.
#%  guisection: Supply & Installation
#%end
#%option G_OPT_V_MAP
#%  key: electro
#%  description: Name of the vector map with the electric grid
#%  required: yes
#%end
#%option G_OPT_V_INPUT
#%  key: electro_layer
#%  description: Name of the vector map layer of other plants, with the following attributes: kind (water intake/turbine), discharge [m3/year], id point, id plant
#%  required: no
#%  answer: 1
#%end

#############################################################################
# DEFINE POWER STATION COSTS
#%option
#%  key: alpha_station
#%  type: double
#%  description: Power station costs are assessd as a fraction of the Electro-mechanical costs
#%  answer: 0.52
#%  guisection: Power station
#%end

#############################################################################
# DEFINE INLET COSTS
#%option
#%  key: alpha_inlet
#%  type: double
#%  description: Inlet costs are assessd as a fraction of the Electro-mechanical costs
#%  answer: 0.38
#%  guisection: Inlet
#%end

#############################################################################
# DEFINE OTHER COSTS
#%option
#%  key: grid
#%  type: double
#%  description:  Cost for grid connection
#%  answer: 50000
#%  guisection: Other
#%end
#%option
#%  key: general
#%  type: double
#%  description:  Factor for general expenses
#%  answer: 0.15
#%  guisection: Other
#%end
#%option
#%  key: hindrances
#%  type: double
#%  description:  Factor for hindrances expenses
#%  answer: 0.1
#%  guisection: Other
#%end
# DEFINE MAINTENANCE COSTS
#%option
#%  key: cost_maintenance_per_kw
#%  type: double
#%  description: Maintenace costs per kW
#%  answer: 7000.
#%  guisection: Maintenance
#%end
#%option
#%  key: alpha_maintenance
#%  type: double
#%  description: alpha coefficient to assess the maintenance costs
#%  answer: 0.05
#%  guisection: Maintenance
#%end
#%option
#%  key: beta_maintenance
#%  type: double
#%  description: beta coefficient to assess the maintenance costs
#%  answer: 0.45
#%  guisection: Maintenance
#%end
#%option
#%  key: const_maintenance
#%  type: double
#%  description: constant to assess the maintenance costs
#%  answer: 0.
#%  guisection: Maintenance
#%end

# DEFINE REVENUES PARAMETERS
#%option
#%  key: energy_price
#%  type: double
#%  description: Energy price per kW [currency/kW]
#%  answer: 0.09
#%  guisection: Revenues
#%end
#%option
#%  key: eta
#%  type: double
#%  description: Energy price per kW [currency/kW]
#%  answer: 0.81
#%  guisection: Revenues
#%end
#%option
#%  key: operative_hours
#%  type: double
#%  description: The number of operative hours per year [hours/year]
#%  answer: 6500.
#%  guisection: Revenues
#%end
#%option
#%  key: alpha_revenue
#%  type: double
#%  description: coefficient to transform installed power to mean
#%  answer: 0.5
#%  guisection: Revenues
#%end
#%option
#%  key: const_revenue
#%  type: double
#%  description: constant to assess the revenues
#%  answer: 0.
#%  guisection: Revenues
#%end

#############################################################################
# DEFINE OUTPUTS
#%option G_OPT_V_OUTPUT
#%  key: output
#%  description: Name of the output vector map
#%  required: yes
#%end

## COSTS
#%option G_OPT_R_OUTPUT
#%  key: compensation
#%  description: Raster map with the compensation values
#%  required: no
#%end
#%option G_OPT_R_OUTPUT
#%  key: excavation
#%  description: Raster map with the excavation costs
#%  required: no
#%end

## VALUES
#%option G_OPT_R_OUTPUT
#%  key: upper
#%  description: Raster map with the compensation values
#%  required: no
#%end

#############################################################################
#%rules
#% required: landvalue, rules_landvalue
#% requires: rules_landvalue, landuse
#% required: tributes, rules_tributes
#% requires: rules_tributes, landuse
#% required: stumpage, rules_stumpage
#% requires: rules_stumpage, landuse
#% required: tributes, rules_rotation
#% requires: rules_rotation, landuse
#% required: tributes, rules_age
#% requires: rules_age, landuse
#% required: min_exc, rules_min_exc
#% requires: rules_min_exc, landuse
#% required: max_exc, rules_max_exc
#% requires: rules_max_exc, landuse
#%end
#exclusive: at most one of the options may be given
#required: at least one of the options must be given
#requires: if the first option is given, at least one of the subsequent options must also be given
#requires_all: if the first option is given, all of the subsequent options must also be given
#excludes: if the first option is given, none of the subsequent options may be given
#collective: all or nothing; if any option is given, all must be given
from __future__ import print_function

import os
import atexit
import random

import numpy as np
import numexpr as ne

from grass.exceptions import ParameterError
from grass.script.core import parser, run_command, overwrite
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v

from grass.pygrass.utils import set_path
from grass.pygrass.raster import RasterRow
from grass.pygrass.vector import VectorTopo, sql
from grass.pygrass.vector.basic import Cats

from grass.pygrass.messages import get_msgr

# set python path to the shared r.green libraries
set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))

from libgreen.utils import cleanup
from libgreen.checkparameter import check_required_columns, exception2error
from libhydro.plant import read_plants, write_structures


def rname(base):
    return '%s_%03d' % (base, random.randint(0, 1000))


def check_raster_or_landuse(opts, params):
    """Return a list of raster name, i f necessary the rasters are generated
    using the file with the rules to convert a landuse map to the raster
    that it is needed.
    """
    msgr = get_msgr()
    rasters = []
    for par in params:
        if opts[par]:
            rasters.append(opts[par])
        elif opts['rules_%s' % par] and opts['landuse']:
            output = rname(par)
            msg = 'Creating: {out} using the rules: {rul}'
            msgr.verbose(msg.format(out=output, rul='rules_%s' % par))
            r.reclass(input=opts['landuse'], output=output,
                      rules=opts['rules_%s' % par])
            rasters.append(output)
        else:
            msg = '{par} or rule_{par} are required'
            raise ParameterError(msg.format(par=par))
    return rasters


def upper_value(upper, stu, lan, rot, age, irate, overwrite=False):
    """Compute the upper value of a land.
    """
    expr = ("{upper} = ({stu} + {lan}) / ((1 + {irate})^({rot} - {age}) )"
            " - {lan}")
    r.mapcalc(expr.format(upper=upper, stu=stu, lan=lan, irate=irate,
                          rot=rot, age=age), overwrite=overwrite)


def compensation_cost(comp, lan, tri, upper,
                      irate, gamma, life, width, overwrite=False):
    """Compute the compensation raster map costs"""
    expr = ("{comp} = (({lan} + {tri} * "
            "(1 + {irate})^{life}/({irate} * (1 + {irate}))) "
            "* {gamma} + {upper}) * {width} * nsres() / 10000")
    r.mapcalc(expr.format(comp=comp, lan=lan, tri=tri, upper=upper,
                          irate=irate, gamma=gamma, life=life, width=width),
              overwrite=overwrite)


def excavation_cost(exc, excmin, excmax, slope,
                    slim, width, depth, overwrite=False):
    """Compute the excavation cost"""
    expr = ("{exc} = if({slope} < {slim}, "
            "({excmin} + ({excmax} - {excmin}) / {slim} * {slope})"
            "* {width} * {depth} * nsres(),"
            "{excmax} * {width} * {depth} * nsres())")
    r.mapcalc(expr.format(exc=exc, slope=slope, excmin=excmin, excmax=excmax,
                          slim=slim, width=width, depth=depth),
              overwrite=overwrite)

def vmapcalc2(vmap, vlayer, cname, ctype, expr, overwrite=False):
    v.db_addcolumn(map=vmap, layer=vlayer, columns=[(cname, ctype)],
                   overwrite=overwrite)
    v.db_update(map=vmap, layer=vlayer, column=cname, query_column=expr,
                overwrite=overwrite)


def get_cnames(expr,
               _names_cache=ne.utils.CacheDict(256),
               _numexpr_cache=ne.utils.CacheDict(256), **kwargs):
    if not isinstance(expr, (str, unicode)):
        raise ValueError("must specify expression as a string")
    # Get the names for this expression
    context = ne.necompiler.getContext(kwargs, frame_depth=1)
    expr_key = (expr, tuple(sorted(context.items())))
    if expr_key not in _names_cache:
        _names_cache[expr_key] = ne.necompiler.getExprNames(expr.strip(),
                                                            context)
    names, ex_uses_vml = _names_cache[expr_key]
    return names


def vcolcalc(vname, vlayer, ctype, expr, condition=lambda x: x is None,
             notfinitesubstitute=None, **kwargs):
    equal = expr.index('=')
    if equal < 0:
        raise
    cname = expr[:equal].strip()
    expr = expr[(equal + 1):].strip()
    cnames = get_cnames(expr)
    with VectorTopo(vname, layer=vlayer, mode='r') as vect:
        if vect.table is None:
            msg = 'Vector: {vname} is without table.'
            raise TypeError(msg.format(vname=vname))

        cols = vect.table.columns
        # check if the column in the expressions exist or not
        for col in cnames:
            if col not in cols:
                msg = 'Vector: {vname} has not column: {col} in layer: {layer}'
                raise  TypeError(msg.format(vname=vname, col=col,
                                            layer=vlayer))
        if cname not in cols:
            vect.table.columns.add(cname, ctype)
        # extract value from the attribute table
        if cnames[0] != vect.table.key:
            cnames.insert(0, vect.table.key)
        # TODO: find a more elegant way to do it
        sql = vect.table.filters.select(', '.join(cnames)).where(' is not NULL AND '.join(cnames)).get_sql()[:-1] + ' is not NULL;'
        data = np.array(list(vect.table.execute(sql)))
        # create a dictionary with local variables
        lvars = {col: array for col, array in zip(cnames, data.T)}
        # compute the result with numexpr
        res = ne.evaluate(expr, local_dict=lvars, **kwargs)
        if notfinitesubstitute is not None:
            res[~np.isfinite(res)] = notfinitesubstitute
        # save the result to the vector point
        cur = vect.table.conn.cursor()
        upstr = 'UPDATE {tname} SET {cname}=? WHERE {key} == ?;'
        cur.executemany(upstr.format(tname=vect.table.name, cname=cname,
                                     key=vect.table.key),
                        zip(res, lvars[vect.table.key]))
        # save changes
        vect.table.conn.commit()


def electromechanical_cost(vname, power, head,
                           gamma=15600., alpha=0.56, beta=0.112, const=0.,
                           vlayer=1, cname='em_cost',
                           ctype='double precision',
                           overwrite=False):
    expr = "{cname} = {gamma} * {power}**{alpha} * {head}**{beta} + {const}"
    vcolcalc(vname, vlayer, ctype, notfinitesubstitute=0.,
             expr=expr.format(cname=cname, gamma=gamma, power=power,
                              alpha=alpha, head=head, beta=beta, const=const))


def col_exist(vname, cname, ctype='double precision', vlayer=1, create=False):
    with VectorTopo(vname, layer=vlayer, mode='r') as vect:
        if vect.table is None:
            msg = 'Vector: {vname} is without table.'
            raise TypeError(msg.format(vname=vname))
        res = cname in vect.table.columns
        if res is False:
            vect.table.columns.add(cname, ctype)
        return res


def linear_cost(vname, cname='lin_cost', alpha=310., length='length', vlayer=1,
                ctype='double precision',  overwrite=False):
    # check if length it is alread in the db
    if not col_exist(vname, 'length', create=True):
        v.to_db(map=vname, type='line', layer=vlayer, option='length',
                columns='length')
    expr = "{cname} = {alpha} * {length}"
    vcolcalc(vname, vlayer, ctype, notfinitesubstitute=0.,
             expr=expr.format(cname=cname, alpha=alpha, length=length))


def get_electro_length(opts):
    # open vector plant
    with VectorTopo(opts['plant'], layer=int(opts['plant_layer']),
                    mode='r') as vect:
        kcol = opts['plant_kind_column']
        ktype = opts['plant_kind_turbine']
        # check if electro_length it is alredy in the table
        if 'electro_length' not in vect.table.columns:
            vect.table.columns.add('electro_length', 'double precision')
        # open vector map with the existing electroline
        with VectorTopo(opts['electro'], layer=int(opts['electro_layer']),
                        mode='r') as electro:
            for line in vect:
                if line.attrs[kcol] == ktype:
                    # the turbine is the last point of the penstock
                    turbine = line[-1]
                    # find the closest electro line
                    eline = electro.find['by_point'].geo(turbine, maxdist=1e6)
                    dist = eline.distance(turbine)
                    line.attrs['electro_length'] = dist.dist
                else:
                    line.attrs['electro_length'] = 0.
            vect.table.conn.commit()


def get_gamma_NPV(r=0.03, y=30):
    """gamma it is a coefficient define as:

        $\gamma = 1 - \frac{1 - (1+r)^y}{r(1+r)^y}$

    with $r$ as the interest rate (default value: 0.03) and
    $y$ as the number of years of the plant [years] (default value: 30);
    """
    return 1 - (1 - (1 + r)**y) / (r * (1 + r)**y)


def group_by(vinput, voutput, isolate=None, aggregate=None,
             function='sum', vtype='lines',
             where='',  group_by=None, linput=1, loutput=1):
    with VectorTopo(vinput, mode='r') as vin:
        columns = ['cat', ]
        vincols = vin.table.columns
        types = ['PRIMARY KEY', ]
        siso = ''
        if isolate is not None:
            columns += list(isolate)
            types += [vincols[c] for c in isolate]
            siso = ', '.join(isolate)
        sagg = ''
        if aggregate is not None:
            ct = '{func}({col}) as {col}'
            sagg = ', '.join([ct.format(func=function, col=col)
                              for col in aggregate])
            columns += list(aggregate)
            types += [vincols[c] for c in aggregate]

        scols = "%s, %s" % (siso, sagg) if siso and sagg else siso + sagg
        base = "SELECT {cols} FROM {tin}"
        bwhere = " WHERE %s" % where if where else ''
        bgroup = " GROUP BY %s" % ', '.join(group_by) if group_by else ''
        grp = (base + bwhere + bgroup + ';').format(cols=scols,
                                                    tin=vin.table.name,
                                                    tout=voutput)
        bqry = "SELECT {cat} FROM {tin} WHERE {cond};"
        qry = bqry.format(cat=vin.table.key, tin=vin.table.name,
                          cond=' AND '.join(['%s=?' % g for g in group_by]))
        selcols = columns[1:]
        gindexs = [selcols.index(col) for col in group_by]
        insrt = sql.INSERT.format(tname=voutput,
                                  values=','.join(['?', ] * len(columns)))
        with VectorTopo(voutput, mode='w', tab_name=voutput, layer=loutput,
                        tab_cols=list(zip(columns, types)), link_key='cat',
                        overwrite=True) as vout:
            cur = vout.table.conn.cursor()
            ncat = 1
            #import ipdb; ipdb.set_trace()
            # TODO: why do I need to use list(cur) and I can not iterate directly
            for row in list(cur.execute(grp)):
                # add the new line to table
                print(row)
                cur.execute(insrt, tuple([ncat, ] + list(row)))
                for cat in cur.execute(qry, tuple([row[i] for i in gindexs])):
                    for line in vin.cat(cat[0], vtype):
                        # set the new category
                        category = Cats(line.c_cats)
                        category.reset()
                        category.set(ncat, loutput)
                        # write geometry
                        vout.write(line, set_cats=False)
                ncat += 1
            vout.table.conn.commit()


def main(opts, flgs):
    # check or generate raster map from rules files
    ecovalues = ['landvalue', 'tributes', 'stumpage', 'rotation', 'age',
                 'min_exc', 'max_exc']
    (lan, tri, stu, rot, age,
     excmin, excmax) = check_raster_or_landuse(opts, ecovalues)
    upper = opts['upper'] if opts['upper'] else 'tmp_upper'
    comp = opts['compensation'] if opts['compensation'] else 'tmp_compensation'
    exc = opts['excavation'] if opts['excavation'] else 'tmp_excavation'
    vlayer = int(opts['plant_layer'])

    # read common scalar parameters
    irate = float(opts['interest_rate'])
    life = float(opts['life'])
    width = float(opts['width'])
    depth = float(opts['depth'])
    slim = float(opts['slope_limit'])
    overw = overwrite()

    # RASTERS
    # Start computing the raster map of the costs
    # Upper value
    upper_value(upper, stu, lan, rot, age, irate, overw)
    # Compensation raster costs
    compensation_cost(comp, lan, tri, upper,
                      irate, float(opts['gamma_comp']), life, width, overw)
    # Excavation raster costs
    excavation_cost(exc, excmin, excmax, opts['slope'],
                    slim, width, depth, overw)
    # TODO: extra cost when crossing roads and rivers are missing

    # VECTOR
    # add columns with costs from rasters
    # add compensation costs
    v.rast_stats(map=opts['plant'], layer=vlayer, flags='c',
                 raster=comp, column_prefix='comp_cost', method='sum')
    # add excavation costs
    v.rast_stats(map=opts['plant'], layer=vlayer, flags='c',
                 raster=exc, column_prefix='exc_cost', method='sum')

    # add elecro-mechanical costs
    electromechanical_cost(opts['plant'],
                           power=opts['plant_power_column'],
                           head=opts['plant_head_column'],
                           gamma=float(opts['gamma_em']),
                           alpha=float(opts['alpha_em']),
                           beta=float(opts['beta_em']),
                           const=float(opts['const_em']),
                           vlayer=vlayer, cname='em_cost',
                           ctype='double precision',
                           overwrite=overw)

    # add linear cost for pipeline
    linear_cost(vname=opts['plant'], cname='lin_pipe_cost',
                alpha=float(opts['lc_pipe']), vlayer=vlayer,
                ctype='double precision',  overwrite=overw)

    # add linear for for electroline
    get_electro_length(opts)
    linear_cost(vname=opts['plant'], cname='lin_electro_cost',
                alpha=float(opts['lc_electro']), length='electro_length',
                vlayer=vlayer, ctype='double precision',  overwrite=overw)

    xcost = "{cname} = {alpha} * {em}"
    # add power station costs
    vcolcalc(vname=opts['plant'], vlayer=vlayer,
             ctype='double precision',
             expr=xcost.format(cname='station_cost', em='em_cost',
                               alpha=opts['alpha_station']))
    # add inlet costs
    vcolcalc(vname=opts['plant'], vlayer=vlayer,
             ctype='double precision', notfinitesubstitute=0.,
             expr=xcost.format(cname='inlet_cost', em='em_cost',
                               alpha=opts['alpha_inlet']))
    # add total inlet costs
    # TODO: to be check to avoid to count cost more than one time I have moltiplied by 0.5
    tot = ('tot_cost = (comp_cost_sum + em_cost + '
           'lin_pipe_cost + lin_electro_cost + '
           'station_cost + inlet_cost + {grid}*0.5) * '
           '(1 + {general} + {hindrances})')
    vcolcalc(vname=opts['plant'], vlayer=vlayer,
             ctype='double precision', notfinitesubstitute=0.,
             expr=tot.format(grid=opts['grid'], general=opts['general'],
                             hindrances=opts['hindrances']))

    # TODO: produce a new vector map (output), with the conduct + penstock in
    # a unique line and sum the costs grouping by intake_id and side
    # SELECT {key} FROM {tname}
    group_by(opts['plant'], opts['output'],
             isolate=['intake_id', 'plant_id', 'side', 'power',
                      'head', 'discharge'],
             aggregate=['tot_cost', ],
             function='sum',
             group_by=['intake_id', 'side'])

    """
    where these values (3871.2256 and -0.45) are coming from?
    import numpy as np
    from scipy import stats

    power= np.array([50., 100., 200., 400., 600., 1000., 5000.])
    maint = np.array([707., 443., 389., 261., 209., 163., 88.])

    plt.plot(np.log(power), np.log(maint))
    plt.show()
    slope, intercept, r_value, p_value, std_err = stats.linregress(np.log(power), np.log(maint))
    #slope -0.45000431409701719
    #intercept 8.2613264284076049
    np.exp(intercept) * power ** slope

    """
#    maint = "{cname} = {alpha} * {power} ** (1 + {beta}) + {const}"
    maint = "{cname} = {cost_per_kW} * {power} * {alpha}) + {const}"
    # compute yearly maintenance costs
    vcolcalc(vname=opts['output'], vlayer=vlayer,
             ctype='double precision', notfinitesubstitute=0.,
             expr=maint.format(cname='maintenance',
                               cost_per_kw=opts['cost_maintenance_per_kw'],
                               alpha=opts['alpha_maintenance'],
                               power=opts['plant_power_column'],
                               beta=opts['beta_maintenance'],
                               const=opts['const_maintenance']))

    # compute yearly revenues
    rev = "{cname} = {eta} * {power} * {eprice} * {ophours} * {alpha} + {const}"
    vcolcalc(vname=opts['output'], vlayer=vlayer,
             ctype='double precision', notfinitesubstitute=0.,
             expr=rev.format(cname='revenue',
                             eta=opts['eta'],
                             power=opts['plant_power_column'],
                             eprice=opts['energy_price'],
                             ophours=opts['operative_hours'],
                             alpha=opts['alpha_revenue'],
                             const=opts['const_revenue']))

    # compute the Net Present Value
    npv = "{cname} = {gamma} * ({revenue} - {maintenance}) - {tot}"
    gamma_npv = get_gamma_NPV(irate, life)
    vcolcalc(vname=opts['output'], vlayer=vlayer,
             ctype='double precision', notfinitesubstitute=0.,
             expr=npv.format(cname='NPV',
                             gamma=gamma_npv,
                             revenue='revenue',
                             maintenance='maintenance',
                             tot='tot_cost'))


if __name__ == "__main__":
    main(*parser())
