#!/usr/bin/env python

############################################################################
#
# MODULE:       i.histo.match
# AUTHOR(S):    Luca Delucchi, Fondazione E. Mach (Italy)
#               original PERL code was developed by:
#               Laura Zampa (2004) student of Dipartimento di Informatica e
#               Telecomunicazioni, Facoltà di Ingegneria,
#                University of Trento  and ITC-irst, Trento (Italy)
#
# PURPOSE:      Calculate histogram matching of several images
# COPYRIGHT:    (C) 2011 by the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
# TODO: use "BEGIN TRANSACTION" etc?
#############################################################################
# %module
# % description: Calculate histogram matching of several images.
# % keyword: imagery
# % keyword: histogram matching
# %end
# %option G_OPT_R_INPUTS
# % description: Name of raster maps to be analyzed
# % required: yes
# %end
# %option
# % key: suffix
# % type: string
# % gisprompt: Suffix for output maps
# % description: Suffix for output maps
# % required: no
# % answer: match
# %end
# %option G_OPT_R_OUTPUT
# % description: Name for mosaic output map
# % required: no
# %end
# %option G_OPT_DB_DATABASE
# % required : no
# % answer: $GISDBASE/$LOCATION_NAME/$MAPSET/histo.db
# %end
# %option
# % key: max
# % type: integer
# % gisprompt: Number of the maximum value for raster maps
# % description: Number of the maximum value for raster maps
# % required: no
# % answer: 255
# %end


import sys
import os
import sqlite3
import grass.script as grass


def main():
    # split input images
    all_images = options["input"]
    images = all_images.split(",")
    # number of images
    n_images = len(images)
    # database path
    dbopt = options["database"]
    # output suffix
    suffix = options["suffix"]
    # output mosaic map
    mosaic = options["output"]
    output_names = []
    # name for average table
    table_ave = "t%s_average" % suffix
    # increment of one the maximum value for a correct use of range function
    max_value = int(options["max"]) + 1
    # if the db path is the default one
    if dbopt.find("$GISDBASE/$LOCATION_NAME/$MAPSET") == 0:
        dbopt_split = dbopt.split("/")[-1]
        env = grass.gisenv()
        path = os.path.join(env["GISDBASE"], env["LOCATION_NAME"], env["MAPSET"])
        dbpath = os.path.join(path, dbopt_split)
    else:
        if os.access(os.path.dirname(dbopt), os.W_OK):
            path = os.path.dirname(dbopt)
            dbpath = dbopt
        else:
            grass.fatal(
                _(
                    "Folder to write database files does not"
                    + " exist or is not writeable"
                )
            )
    # connect to the db
    db = sqlite3.connect(dbpath)
    curs = db.cursor()
    grass.message(_("Calculating Cumulative Distribution Functions ..."))

    # number of pixels per value, summarized for all images
    numPixelValue = list(range(0, max_value))
    for n in range(0, max_value):
        numPixelValue[n] = 0

    # cumulative histogram for each value and each image
    cumulHistoValue = list(range(0, max_value))

    # set up temp region only once
    grass.use_temp_region()

    # for each image
    for i in images:
        iname = i.split("@")[0]
        # drop table if exist
        query_drop = 'DROP TABLE if exists "t%s"' % iname
        curs.execute(query_drop)
        # create table
        query_create = 'CREATE TABLE "t%s" (grey_value integer,pixel_frequency ' % iname
        query_create += "integer, cumulative_histogram integer, cdf real)"
        curs.execute(query_create)
        index_create = 'CREATE UNIQUE INDEX "t%s_grey_value" ON "t%s" (grey_value) ' % (
            iname,
            iname,
        )
        curs.execute(index_create)
        # set the region on the raster
        grass.run_command("g.region", raster=i)
        # calculate statistics
        stats_out = grass.pipe_command("r.stats", flags="cin", input=i, separator=":")
        stats = stats_out.communicate()[0].decode("utf-8").split("\n")[:-1]
        stats_dict = dict(s.split(":", 1) for s in stats)
        cdf = 0
        curs.execute("BEGIN")
        # for each number in the range
        for n in range(0, max_value):
            # try to insert the values otherwise insert 0

            try:
                val = int(stats_dict[str(n)])
                cdf += val
                numPixelValue[n] += val
                insert = 'INSERT INTO "t%s" VALUES (%i, %i, %i, 0.000000)' % (
                    iname,
                    n,
                    val,
                    cdf,
                )
                curs.execute(insert)
            except:
                insert = 'INSERT INTO "t%s" VALUES (%i, 0, %i, 0.000000)' % (
                    iname,
                    n,
                    cdf,
                )
                curs.execute(insert)
            # save cumulative_histogram for the second loop
            cumulHistoValue[n] = cdf
        curs.execute("COMMIT")
        db.commit()
        # number of pixel is the cdf value
        numPixel = cdf
        # for each number in the range
        # cdf is updated using the number of non-null pixels for the current image
        curs.execute("BEGIN")
        for n in range(0, max_value):
            # select value for cumulative_histogram for the range number
            """
            select_ch = "SELECT cumulative_histogram FROM \"t%s\" WHERE " % iname
            select_ch += "(grey_value=%i)" % n
            result = curs.execute(select_ch)
            val = result.fetchone()[0]
            """
            val = cumulHistoValue[n]
            # update cdf with new value
            if val != 0 and numPixel != 0:
                update_cdf = round(float(val) / float(numPixel), 6)
                update_cdf = 'UPDATE "t%s" SET cdf=%s WHERE (grey_value=%i)' % (
                    iname,
                    update_cdf,
                    n,
                )
                curs.execute(update_cdf)

        curs.execute("COMMIT")
        db.commit()
    db.commit()
    pixelTot = 0

    # get total number of pixels divided by number of images
    # for each number in the range
    for n in range(0, max_value):
        """
        numPixel = 0
        # for each image
        for i in images:
            iname = i.split('@')[0]
            pixel_freq = "SELECT pixel_frequency FROM \"t%s\" WHERE (grey_value=%i)" % (
                                                                iname, n)
            result = curs.execute(pixel_freq)
            val = result.fetchone()[0]
            numPixel += val
        """
        # calculate number of pixel divide by number of images
        div = int(numPixelValue[n] / n_images)
        pixelTot += div

    # drop average table
    query_drop = "DROP TABLE if exists %s" % table_ave
    curs.execute(query_drop)
    # create average table
    query_create = "CREATE TABLE %s (grey_value integer,average " % table_ave
    query_create += "integer, cumulative_histogram integer, cdf real)"
    curs.execute(query_create)
    index_create = 'CREATE UNIQUE INDEX "%s_grey_value" ON "%s" (grey_value) ' % (
        table_ave,
        table_ave,
    )
    curs.execute(index_create)
    cHist = 0
    # for each number in the range
    curs.execute("BEGIN")
    for n in range(0, max_value):
        tot = 0
        """
        # for each image
        for i in images:
            iname = i.split('@')[0]
            # select pixel frequency
            pixel_freq = "SELECT pixel_frequency FROM \"t%s\" WHERE (grey_value=%i)" % (
                                                            iname, n)
            result = curs.execute(pixel_freq)
            val = result.fetchone()[0]
            tot += val
        """
        tot = numPixelValue[n]
        # calculate new value of pixel_frequency
        average = tot / n_images
        cHist = cHist + int(average)
        # insert new values into average table
        if cHist != 0 and pixelTot != 0:
            cdf = float(cHist) / float(pixelTot)
            insert = "INSERT INTO %s VALUES (%i, %i, %i, %s)" % (
                table_ave,
                n,
                int(average),
                cHist,
                cdf,
            )
            curs.execute(insert)
    curs.execute("COMMIT")
    db.commit()

    # for each image
    grass.message(_("Reclassifying bands based on average histogram..."))
    for i in images:
        iname = i.split("@")[0]
        grass.run_command("g.region", raster=i)
        # write average rules file
        outfile = open(grass.tempfile(), "w")
        new_grey = 0
        for n in range(0, max_value):
            select_newgrey = 'SELECT b.grey_value FROM "t%s" as a, ' % iname
            select_newgrey += (
                "%s as b WHERE a.grey_value=%i " % (table_ave, n)
                + "ORDER BY abs(a.cdf-b.cdf) LIMIT 1"
            )
            # write line with old and new value
            try:
                result_new = curs.execute(select_newgrey)
                new_grey = result_new.fetchone()[0]
                out_line = "%d = %d\n" % (n, new_grey)
                outfile.write(out_line)
            except:
                out_line = "%d = %d\n" % (n, new_grey)
                outfile.write(out_line)

        outfile.close()
        outname = "%s.%s" % (iname, suffix)
        # check if a output map already exists
        result = grass.core.find_file(outname, element="cell")
        if result["fullname"] and grass.overwrite():
            grass.run_command("g.remove", flags="f", type="raster", name=outname)
            grass.run_command("r.reclass", input=i, out=outname, rules=outfile.name)
        elif result["fullname"] and not grass.overwrite():
            grass.warning(
                _("Raster map %s already exists and will not be overwritten" % i)
            )
        else:
            grass.run_command("r.reclass", input=i, out=outname, rules=outfile.name)
        output_names.append(outname)
        # remove the rules file
        grass.try_remove(outfile.name)
        # write cmd history:
        grass.raster_history(outname)
    db.commit()
    db.close()
    if mosaic:
        grass.message(_("Processing mosaic <%s>..." % mosaic))
        grass.run_command("g.region", raster=all_images)
        grass.run_command("r.patch", input=output_names, output=mosaic)


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
