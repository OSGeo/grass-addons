#!/usr/bin/env python
# -*- coding: utf-8 -*-
############################################################################
#
# MODULE:       t.rast.what.aggr
# AUTHOR(S):    Luca Delucchi
#
# PURPOSE:      Sample a space time raster dataset at specific vector point
#               map returning aggregate values and write the output to stdout
#               or to attribute table
#
# COPYRIGHT:    (C) 2017 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Sample a space time raster dataset at specific vector point map returning aggregate values and write the output to stdout or to attribute table
#% keyword: temporal
#% keyword: sampling
#% keyword: raster
#% keyword: time
#%end

#%option G_OPT_V_INPUT
#%end

#%option G_OPT_STRDS_INPUT
#% key: strds
#%end

#%option G_OPT_DB_COLUMN
#% key: date_column
#% description: Name of the input column containing dates for aggregates
#% required: no
#%end

#%option
#% key: date
#% type: string
#% description: The date for aggregates
#% required: no
#% multiple: no
#%end

#%option G_OPT_F_OUTPUT
#% required: no
#% description: Name for the output file or "-" in case stdout should be used
#% answer: -
#%end

#%option G_OPT_DB_COLUMNS
#%end

#%option
#% key: granularity
#% type: string
#% description: Aggregation granularity, format absolute time "x years, x months, x weeks, x days, x hours, x minutes, x seconds" or an integer value for relative time
#% required: yes
#% multiple: no
#%end

#%option
#% key: method
#% type: string
#% description: Aggregate operation to be performed on the raster maps
#% required: yes
#% multiple: yes
#% options: average,median,mode,minimum,maximum,stddev,sum,variance,quart1,quart3,perc90,quantile
#% answer: average
#%end

#%option G_OPT_F_SEP
#%end

#%option
#% key: nprocs
#% type: integer
#% description: Number of processes to run in parallel
#% required: no
#% multiple: no
#% answer: 1
#%end

#%option
#% key: date_format
#% type: string
#% description: Tha date format
#% required: no
#% answer: %Y-%m-%d
#%end

#%flag
#% key: u
#% label: Update attribute table of input vector map
#% description: Instead of creating a new vector map update the attribute table with value(s)
#%end

#%flag
#% key: a
#% label: Query STRDS with dates after the 'date' or 'column_date' value
#% description: Usually t.rast.what.aggr aggregate values before the selected dates, using a flag it will query values after the selected dates
#%end

#%flag
#% key: c
#% label: Create new columns, it combine STRDS and method names
#% description: Create new columns for the selected methods, it combine STRDS and method names
#%end

from datetime import datetime
from datetime import timedelta
from subprocess import PIPE as PI
import numpy as np
import grass.script as gscript
from grass.exceptions import CalledModuleError


def return_value(vals, met):
    """Return the value according the choosen method"""
    if met == 'average':
        return vals.mean()
    elif met == 'median':
        return np.median(vals)
    elif met == 'mode':
        try:
            from scipy import stats
            m = stats.mode(vals)
            return m.mode[0]
        except ImportError:
            gscript.fatal(_("For method 'mode' you need to install scipy"))
    elif met == 'minimum':
        return vals.min()
    elif met == 'maximum':
        return vals.max()
    elif met == 'stddev':
        return vals.std()
    elif met == 'sum':
        return vals.sum()
    elif met == 'variance':
        return vals.var()
    elif met == 'quart1':
        return np.percentile(vals, 25)
    elif met == 'quart3':
        return np.percentile(vals, 75)
    elif met == 'perc90':
        return np.percentile(vals, 90)
    elif met == 'quantile':
        return

def main(options, flags):
    import grass.pygrass.modules as pymod
    import grass.temporal as tgis
    from grass.pygrass.vector import VectorTopo

    invect = options["input"]
    if invect.find('@') != -1:
        invect = invect.split('@')[0]
    incol = options["date_column"]
    indate = options["date"]
    strds = options["strds"]
    if strds.find('@') != -1:
        strds_name = strds.split('@')[0]
    else:
        strds_name = strds
    output = options["output"]
    cols = options["columns"].split(',')
    mets = options["method"].split(',')
    gran = options["granularity"]
    dateformat = options["date_format"]
    separator = gscript.separator(options["separator"])

    stdout = False
    if output != '-' and flags['u']:
        gscript.fatal(_("Cannot combine 'output' option and 'u' flag"))
    elif output != '-' and flags['c']:
        gscript.fatal(_("Cannot combine 'output' option and 'c' flag"))
    elif output == '-' and (flags['u'] or flags['c']):
        output = invect
        gscript.warning(_("Attribute table of vector {name} will be updated"
                          "...").format(name=invect))
    else:
        stdout = True
    if flags['c']:
        cols = []
        for m in mets:
            colname = "{st}_{me}".format(st=strds_name, me=m)
            cols.append(colname)
            try:
                pymod.Module("v.db.addcolumn", map=invect, columns="{col} "
                             "double precision".format(col=colname))
            except CalledModuleError:
                gscript.fatal(_("Not possible to create column "
                                "{col}".format(col=colname)))

    if output != '-' and len(cols) != len(mets):
        gscript.fatal(_("'columns' and 'method' options must have the same "
                        "number of elements"))
    tgis.init()
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()
    sp = tgis.open_old_stds(strds, "strds", dbif)

    if sp.get_temporal_type() == 'absolute':
        delta = int(tgis.gran_to_gran(gran, sp.get_granularity(), True))
        if tgis.gran_singular_unit(gran) in ['year', 'month']:
            delta = int(tgis.gran_to_gran(gran, '1 day', True))
            td = timedelta(delta)
        elif tgis.gran_singular_unit(gran) == 'day':
            delta = tgis.gran_to_gran(gran, sp.get_granularity(), True)
            td = timedelta(delta)
        elif tgis.gran_singular_unit(gran) == 'hour':
            td = timedelta(hours=delta)
        elif tgis.gran_singular_unit(gran) == 'minute':
            td = timedelta(minutes=delta)
        elif tgis.gran_singular_unit(gran) == 'second':
            td = timedelta(seconds=delta)
    else:
        if sp.get_granularity() >= int(gran):
            gscript.fatal(_("Input granularity is smaller or equal to the {iv}"
                            " STRDS granularity".format(iv=strds)))
        td = int(gran)
    if incol and indate:
        gscript.fatal(_("Cannot combine 'date_column' and 'date' options"))
    elif not incol and not indate:
        gscript.fatal(_("You have to fill 'date_column' or 'date' option"))
    elif incol:
        try:
            dates = pymod.Module("db.select", flags='c', stdout_=PI,
                                 stderr_=PI, sql="SELECT DISTINCT {dc} from "
                                   "{vmap} order by {dc}".format(vmap=invect,
                                                                 dc=incol))
            mydates = dates.outputs["stdout"].value.splitlines()
        except CalledModuleError:
            gscript.fatal(_("db.select return an error"))
    elif indate:
        mydates = [indate]
        pymap = VectorTopo(invect)
        pymap.open('r')
        if len(pymap.dblinks) == 0:
            try:
                pymap.close()
                pymod.Module("v.db.addtable", map=invect)
            except CalledModuleError:
                dbif.close()
                gscript.fatal(_("Unable to add table <%s> to vector map "
                                "<%s>" % invect))
        if pymap.is_open():
            pymap.close()
        qfeat = pymod.Module("v.category", stdout_=PI, stderr_=PI,
                             input=invect, option='print')
        myfeats = qfeat.outputs["stdout"].value.splitlines()

    if stdout:
        outtxt = ''
    for data in mydates:
        if sp.get_temporal_type() == 'absolute':
            fdata = datetime.strptime(data, dateformat)
        else:
            fdata = int(data)
        if flags['a']:
            sdata = fdata + td
            mwhere = "start_time >= '{inn}' and end_time < " \
                   "'{out}'".format(inn=fdata, out=sdata)
        else:
            sdata = fdata - td
            mwhere = "start_time >= '{inn}' and end_time < " \
                   "'{out}'".format(inn=sdata, out=fdata)
        lines = None
        try:
            r_what = pymod.Module("t.rast.what", points=invect, strds=strds,
                                  layout='timerow', separator=separator,
                                  flags="v", where=mwhere, quiet=True,
                                  stdout_=PI, stderr_=PI)
            lines = r_what.outputs["stdout"].value.splitlines()
        except CalledModuleError:
            pass
        if incol:
            try:
                qfeat = pymod.Module("db.select", flags='c', stdout_=PI,
                                     stderr_=PI, sql="SELECT DISTINCT cat from"
                                     " {vmap} where {dc}='{da}' order by "
                                     "cat".format(vmap=invect, da=data,
                                                  dc=incol))
                myfeats = qfeat.outputs["stdout"].value.splitlines()
            except CalledModuleError:
                gscript.fatal(_("db.select returned an error for date "
                                "{da}".format(da=data)))
        if not lines and stdout:
            for feat in myfeats:
                outtxt += "{di}{sep}{da}".format(di=feat, da=data,
                                                   sep=separator)
                for n in range(len(mets)):
                    outtxt += "{sep}{val}".format(val='*', sep=separator)
                outtxt += "\n"
        if not lines:
            continue
        x = 0
        for line in lines:
            vals = line.split(separator)
            if vals[0] in myfeats:
                try:
                    nvals = np.array(vals[4:]).astype(np.float)
                except ValueError:
                    if stdout:
                        outtxt += "{di}{sep}{da}".format(di=vals[0],
                                                         da=data,
                                                         sep=separator)
                        for n in range(len(mets)):
                            outtxt += "{sep}{val}".format(val='*',
                                                          sep=separator)
                        outtxt += "\n"
                    continue
                if stdout:
                    outtxt += "{di}{sep}{da}".format(di=vals[0], da=data,
                                                     sep=separator)
                for n in range(len(mets)):
                    result = return_value(nvals, mets[n])
                    if stdout:
                        outtxt += "{sep}{val}".format(val=result,
                                                      sep=separator)
                    else:
                        try:
                            if incol:
                                pymod.Module("v.db.update", map=output,
                                             column=cols[n], value=str(result),
                                             where="{dc}='{da}' AND cat="
                                             "{ca}".format(da=data, ca=vals[0],
                                                           dc=incol))
                            else:
                                pymod.Module("v.db.update", map=output,
                                             column=cols[n], value=str(result),
                                             where="cat={ca}".format(ca=vals[0]))
                        except CalledModuleError:
                            gscript.fatal(_("v.db.update return an error"))
                if stdout:
                    outtxt += "\n"
                if x == len(myfeats):
                    break
                else:
                    x += 1
    if stdout:
        print(outtxt)

if __name__ == "__main__":
    options, flags = gscript.parser()
    main(options, flags)
