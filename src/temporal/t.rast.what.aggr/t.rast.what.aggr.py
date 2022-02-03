#!/usr/bin/env python

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

# %module
# % description: Sample a space time raster dataset at specific vector point map returning aggregate values and write the output to stdout or to attribute table
# % keyword: temporal
# % keyword: sampling
# % keyword: raster
# % keyword: time
# %end

# %option G_OPT_V_INPUT
# %end

# %option G_OPT_STRDS_INPUT
# % key: strds
# %end

# %option G_OPT_DB_COLUMN
# % key: date_column
# % description: Name of the column containing starting dates for aggregates
# % required: no
# %end

# %option
# % key: date
# % type: string
# % description: The starting date for aggregation
# % required: no
# % multiple: no
# %end

# %option
# % key: final_date
# % type: string
# % description: The end date for aggregation, requires date option
# % required: no
# % multiple: no
# %end

# %option G_OPT_F_OUTPUT
# % required: no
# % description: Name for the output file or "-" in case stdout should be used
# % answer: -
# %end

# %option G_OPT_DB_COLUMNS
# % key: final_date_column
# % description: Column with ending date for aggregation, requires date_columns option
# %end

# %option G_OPT_DB_COLUMNS
# %end

# %option
# % key: granularity
# % type: string
# % description: Aggregation granularity, format absolute time "x years, x months, x weeks, x days, x hours, x minutes, x seconds" or an integer value for relative time
# % required: no
# % multiple: no
# %end

# %option
# % key: method
# % type: string
# % description: Aggregate operation to be performed on the raster maps
# % required: yes
# % multiple: yes
# % options: average,median,mode,minimum,maximum,stddev,sum,variance,quart1,quart3,perc90,quantile
# % answer: average
# %end

# %option G_OPT_F_SEP
# %end

# %option
# % key: nprocs
# % type: integer
# % description: Number of processes to run in parallel
# % required: no
# % multiple: no
# % answer: 1
# %end

# %option
# % key: date_format
# % type: string
# % description: Tha date format
# % required: no
# % answer: %Y-%m-%d
# %end

# %flag
# % key: u
# % label: Update attribute table of input vector map
# % description: Instead of creating a new vector map update the attribute table with value(s)
# %end

# %flag
# % key: a
# % label: Query STRDS with dates after the 'date' or 'column_date' value
# % description: Usually t.rast.what.aggr aggregate values before the selected dates, using a flag it will query values after the selected dates
# %end

# %flag
# % key: c
# % label: Create new columns, it combine STRDS and method names
# % description: Create new columns for the selected methods, it combine STRDS and method names
# %end

# %rules
# % exclusive: date,date_column
# %end

# %rules
# % requires: date, final_date, granularity
# %end

# %rules
# % requires: date_column, final_date_column, granularity
# %end

# %rules
# % requires: final_date, date
# %end

# %rules
# % requires: final_date_column, date_column
# %end

from datetime import datetime
from datetime import timedelta
from subprocess import PIPE as PI
import numpy as np
import grass.script as gscript
from grass.exceptions import CalledModuleError


def return_value(vals, met):
    """Return the value according the choosen method"""
    if met == "average":
        return vals.mean()
    elif met == "median":
        return np.median(vals)
    elif met == "mode":
        try:
            from scipy import stats

            m = stats.mode(vals)
            return m.mode[0]
        except ImportError:
            gscript.fatal(_("For method 'mode' you need to install scipy"))
    elif met == "minimum":
        return vals.min()
    elif met == "maximum":
        return vals.max()
    elif met == "stddev":
        return vals.std()
    elif met == "sum":
        return vals.sum()
    elif met == "variance":
        return vals.var()
    elif met == "quart1":
        return np.percentile(vals, 25)
    elif met == "quart3":
        return np.percentile(vals, 75)
    elif met == "perc90":
        return np.percentile(vals, 90)
    elif met == "quantile":
        return


def main(options, flags):
    import grass.pygrass.modules as pymod
    import grass.temporal as tgis
    from grass.pygrass.vector import VectorTopo

    invect = options["input"]
    if invect.find("@") != -1:
        invect = invect.split("@")[0]
    incol = options["date_column"]
    indate = options["date"]
    endcol = options["final_date_column"]
    enddate = options["final_date"]
    strds = options["strds"]
    nprocs = options["nprocs"]
    if strds.find("@") != -1:
        strds_name = strds.split("@")[0]
    else:
        strds_name = strds
    output = options["output"]
    if options["columns"]:
        cols = options["columns"].split(",")
    else:
        cols = []
    mets = options["method"].split(",")
    gran = options["granularity"]
    dateformat = options["date_format"]
    separator = gscript.separator(options["separator"])
    update = flags["u"]
    create = flags["c"]

    stdout = False
    if output != "-" and update:
        gscript.fatal(_("Cannot combine 'output' option and 'u' flag"))
    elif output != "-" and create:
        gscript.fatal(_("Cannot combine 'output' option and 'c' flag"))
    elif output == "-" and (update or create):
        if update and not cols:
            gscript.fatal(_("Please set 'columns' option"))
        output = invect
    else:
        stdout = True

    if create:
        cols = []
        for m in mets:
            colname = "{st}_{me}".format(st=strds_name, me=m)
            cols.append(colname)
            try:
                pymod.Module(
                    "v.db.addcolumn",
                    map=invect,
                    columns="{col} " "double precision".format(col=colname),
                )
            except CalledModuleError:
                gscript.fatal(
                    _("Not possible to create column " "{col}".format(col=colname))
                )
        gscript.warning(
            _("Attribute table of vector {name} will be updated" "...").format(
                name=invect
            )
        )
    elif update:
        colexist = pymod.Module(
            "db.columns", table=invect, stdout_=PI
        ).outputs.stdout.splitlines()
        for col in cols:
            if col not in colexist:
                gscript.fatal(
                    _("Column '{}' does not exist, please create it first".format(col))
                )
        gscript.warning(
            _("Attribute table of vector {name} will be updated" "...").format(
                name=invect
            )
        )

    if output != "-" and len(cols) != len(mets):
        gscript.fatal(
            _("'columns' and 'method' options must have the same " "number of elements")
        )
    tgis.init()
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()
    sp = tgis.open_old_stds(strds, "strds", dbif)

    if sp.get_temporal_type() == "absolute":
        if gran:
            delta = int(tgis.gran_to_gran(gran, sp.get_granularity(), True))
            if tgis.gran_singular_unit(gran) in ["year", "month"]:
                delta = int(tgis.gran_to_gran(gran, "1 day", True))
                td = timedelta(delta)
            elif tgis.gran_singular_unit(gran) == "day":
                delta = tgis.gran_to_gran(gran, sp.get_granularity(), True)
                td = timedelta(delta)
            elif tgis.gran_singular_unit(gran) == "hour":
                td = timedelta(hours=delta)
            elif tgis.gran_singular_unit(gran) == "minute":
                td = timedelta(minutes=delta)
            elif tgis.gran_singular_unit(gran) == "second":
                td = timedelta(seconds=delta)
        else:
            td = None
    else:
        if sp.get_granularity() >= int(gran):
            gscript.fatal(
                _(
                    "Input granularity is smaller or equal to the {iv}"
                    " STRDS granularity".format(iv=strds)
                )
            )
        td = int(gran)
    if incol and indate:
        gscript.fatal(_("Cannot combine 'date_column' and 'date' options"))
    elif not incol and not indate:
        gscript.fatal(_("You have to fill 'date_column' or 'date' option"))
    if incol:
        if endcol:
            mysql = "SELECT DISTINCT {dc},{ec} from {vmap} order by " "{dc}".format(
                vmap=invect, dc=incol, ec=endcol
            )
        else:
            mysql = "SELECT DISTINCT {dc} from {vmap} order by " "{dc}".format(
                vmap=invect, dc=incol
            )
        try:
            dates = pymod.Module(
                "db.select", flags="c", stdout_=PI, stderr_=PI, sql=mysql
            )
            mydates = dates.outputs["stdout"].value.splitlines()
        except CalledModuleError:
            gscript.fatal(_("db.select return an error"))
    elif indate:
        if enddate:
            mydates = ["{ida}|{eda}".format(ida=indate, eda=enddate)]
        else:
            mydates = [indate]
        mydates = [indate]
        pymap = VectorTopo(invect)
        pymap.open("r")
        if len(pymap.dblinks) == 0:
            try:
                pymap.close()
                pymod.Module("v.db.addtable", map=invect)
            except CalledModuleError:
                dbif.close()
                gscript.fatal(
                    _("Unable to add table <%s> to vector map " "<%s>" % invect)
                )
        if pymap.is_open():
            pymap.close()
        qfeat = pymod.Module(
            "v.category", stdout_=PI, stderr_=PI, input=invect, option="print"
        )
        myfeats = qfeat.outputs["stdout"].value.splitlines()

    if stdout:
        outtxt = ""
    for data in mydates:
        try:
            start, final = data.split("|")
        except ValueError:
            start = data
            final = None
        if sp.get_temporal_type() == "absolute":
            fdata = datetime.strptime(start, dateformat)
        else:
            fdata = int(start)
        if final:
            sdata = datetime.strptime(final, dateformat)
        elif flags["a"]:
            sdata = fdata + td
        else:
            sdata = fdata
            fdata = sdata - td
        mwhere = "start_time >= '{inn}' and start_time < " "'{out}'".format(
            inn=fdata, out=sdata
        )
        lines = None
        try:
            r_what = pymod.Module(
                "t.rast.what",
                points=invect,
                strds=strds,
                layout="timerow",
                separator=separator,
                flags="v",
                where=mwhere,
                quiet=True,
                stdout_=PI,
                stderr_=PI,
                nprocs=nprocs,
            )
            lines = r_what.outputs["stdout"].value.splitlines()
        except CalledModuleError:
            gscript.warning("t.rast.what faild with where='{}'".format(mwhere))
            pass
        if incol:
            if endcol:
                mysql = (
                    "SELECT DISTINCT cat from {vmap} where {dc}='{da}' "
                    "AND {ec}='{ed}' order by cat".format(
                        vmap=invect, da=start, dc=incol, ed=final, ec=endcol
                    )
                )
            else:
                mysql = (
                    "SELECT DISTINCT cat from {vmap} where {dc}='{da}' "
                    "order by cat".format(vmap=invect, da=start, dc=incol)
                )
            try:
                qfeat = pymod.Module(
                    "db.select", flags="c", stdout_=PI, stderr_=PI, sql=mysql
                )
                myfeats = qfeat.outputs["stdout"].value.splitlines()
            except CalledModuleError:
                gscript.fatal(
                    _("db.select returned an error for date " "{da}".format(da=start))
                )
        if not lines and stdout:
            for feat in myfeats:
                outtxt += "{di}{sep}{da}".format(di=feat, da=start, sep=separator)
                for n in range(len(mets)):
                    outtxt += "{sep}{val}".format(val="*", sep=separator)
                outtxt += "\n"
        if not lines:
            continue
        x = 0
        for line in lines:
            vals = line.split(separator)
            if vals[0] in myfeats:
                try:
                    nvals = np.array(vals[3:]).astype(float)
                except ValueError:
                    if stdout:
                        outtxt += "{di}{sep}{da}".format(
                            di=vals[0], da=start, sep=separator
                        )
                        for n in range(len(mets)):
                            outtxt += "{sep}{val}".format(val="*", sep=separator)
                        outtxt += "\n"
                    continue
                if stdout:
                    outtxt += "{di}{sep}{da}".format(
                        di=vals[0], da=start, sep=separator
                    )
                for n in range(len(mets)):
                    result = None
                    if len(nvals) == 1:
                        result = nvals[0]
                    elif len(nvals) > 1:
                        result = return_value(nvals, mets[n])
                    if stdout:
                        if not result:
                            result = "*"
                        outtxt += "{sep}{val}".format(val=result, sep=separator)
                    else:
                        try:
                            if incol:
                                mywhe = "{dc}='{da}' AND ".format(da=start, dc=incol)
                                if endcol:
                                    mywhe += "{dc}='{da}' AND ".format(
                                        da=final, dc=endcol
                                    )

                                mywhe += "cat={ca}".format(ca=vals[0])

                                pymod.Module(
                                    "v.db.update",
                                    map=output,
                                    column=cols[n],
                                    value=str(result),
                                    where=mywhe,
                                )
                            else:
                                pymod.Module(
                                    "v.db.update",
                                    map=output,
                                    column=cols[n],
                                    value=str(result),
                                    where="cat={ca}".format(ca=vals[0]),
                                )
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
