/*****************************************************************************
 *
 * MODULE:       r.pi.corr.mw
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Moving window correlation analysis
 *               Put together from pieces of r.covar and r.neighbors
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "ncb.h"
#include "local_proto.h"

typedef int(ifunc)(void);

struct ncb ncb;

int main(int argc, char *argv[])
{
    char *p, *p1, *p2;
    int in_fd1, in_fd2;
    int out_fd;
    DCELL *result;
    RASTER_MAP_TYPE map_type;
    int row, col, i;
    int readrow;
    int maxval;
    int nrows, ncols;
    int copycolr;
    struct Colors colr;
    struct GModule *module;
    struct {
        struct Option *input1, *input2, *output;
        struct Option *size, *max;
        struct Option *title;
    } parm;
    DCELL *values1, *values2; /* list of neighborhood values */

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("correlation analysis"));
    module->description = _("Moving window correlation analysis.");

    parm.input1 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input1->key = "input1";
    parm.input1->gisprompt = "old,cell,raster,1";

    parm.input2 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input2->key = "input2";
    parm.input2->gisprompt = "old,cell,raster,2";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.size = G_define_option();
    parm.size->key = "size";
    parm.size->type = TYPE_INTEGER;
    parm.size->required = YES;
    parm.size->options = "1,3,5,7,9,11,13,15,17,19,21,23,25";
    parm.size->description = _("Neighborhood size");

    parm.max = G_define_option();
    parm.max->key = "max";
    parm.max->type = TYPE_INTEGER;
    parm.max->required = YES;
    parm.max->description = _("Scaling factor for results");
    parm.max->description = _("In order to receive more information of the "
                              "decimal places, set it to e.g. 1000");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get names of input files */
    p1 = ncb.oldcell1.name = parm.input1->answer;
    p2 = ncb.oldcell2.name = parm.input2->answer;
    /* test input files existance */
    ncb.oldcell1.mapset = G_find_raster2(p1, "");
    if (ncb.oldcell1.mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), p1);
    ncb.oldcell2.mapset = G_find_raster2(p2, "");
    if (ncb.oldcell2.mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), p2);

    /* check if new file name is correct */
    p = ncb.newcell.name = parm.output->answer;
    if (G_legal_filename(p) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), p);
    ncb.newcell.mapset = G_mapset();

    /* get window size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_debug(1, "%d x %d ", nrows, ncols);

    /* open cell files */
    in_fd1 = Rast_open_old(ncb.oldcell1.name, ncb.oldcell1.mapset);
    if (in_fd1 < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), ncb.oldcell1.name);
    in_fd2 = Rast_open_old(ncb.oldcell2.name, ncb.oldcell2.mapset);
    if (in_fd2 < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), ncb.oldcell2.name);

    /* get map type */
    map_type = Rast_map_type(ncb.oldcell1.name, ncb.oldcell1.mapset);

    /* copy color table? */
    copycolr =
        (Rast_read_colors(ncb.oldcell1.name, ncb.oldcell1.mapset, &colr) > 0);

    /* get the neighborhood size */
    sscanf(parm.size->answer, "%d", &ncb.nsize);
    ncb.dist = ncb.nsize / 2;

    /* get correlation maximum */
    sscanf(parm.max->answer, "%d", &maxval);

    /* allocate the cell buffers */
    allocate_bufs();
    values1 = (DCELL *)G_malloc(ncb.nsize * ncb.nsize * sizeof(DCELL));
    values2 = (DCELL *)G_malloc(ncb.nsize * ncb.nsize * sizeof(DCELL));
    result = Rast_allocate_d_buf();

    /* get title, initialize the category and stat info */
    if (parm.title->answer)
        strcpy(ncb.title, parm.title->answer);
    else
        sprintf(ncb.title, "%dx%d neighborhood correlation: %s and %s",
                ncb.nsize, ncb.nsize, ncb.oldcell1.name, ncb.oldcell2.name);

    /* initialize the cell bufs with 'dist' rows of the old cellfile */

    readrow = 0;
    for (row = 0; row < ncb.dist; row++) {
        readcell(in_fd1, 1, readrow, nrows, ncols);
        readcell(in_fd2, 2, readrow, nrows, ncols);
        readrow++;
    }

    /* open the new cellfile */
    out_fd = Rast_open_new(ncb.newcell.name, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), ncb.newcell.name);

    G_message(_("Percent complete ... "));

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);
        /* read the next row into buffer */
        readcell(in_fd1, 1, readrow, nrows, ncols);
        readcell(in_fd2, 2, readrow, nrows, ncols);
        readrow++;
        for (col = 0; col < ncols; col++) {
            DCELL sum1 = 0;
            DCELL sum2 = 0;
            DCELL mul, mul1, mul2;
            double count = 0;
            DCELL ii, jj;

            /* set pointer to actual position in the result */
            DCELL *rp = &result[col];

            mul = mul1 = mul2 = 0;

            /* gather values from actual window */
            gather(values1, 1, col);
            gather(values2, 2, col);
            /* go through all values of the window */
            for (i = 0; i < ncb.nsize * ncb.nsize; i++) {
                /* ignore values if both are nan */
                if (!(Rast_is_d_null_value(&values1[i]) &&
                      Rast_is_d_null_value(&values2[i]))) {
                    if (!Rast_is_d_null_value(&values1[i])) {
                        sum1 += values1[i];
                        mul1 += values1[i] * values1[i];
                    }
                    if (!Rast_is_d_null_value(&values2[i])) {
                        sum2 += values2[i];
                        mul2 += values2[i] * values2[i];
                    }
                    if (!Rast_is_d_null_value(&values1[i]) &&
                        !Rast_is_d_null_value(&values2[i]))
                        mul += values1[i] * values2[i];
                    /* count the number of values actually processed */
                    count++;
                }
            }
            if (count <= 1.1) {
                *rp = 0;
                continue;
            }
            /* calculate normalization */
            ii = sqrt((mul1 - sum1 * sum1 / count) / (count - 1.0));
            jj = sqrt((mul2 - sum2 * sum2 / count) / (count - 1.0));

            /* set result */
            *rp = maxval * (mul - sum1 * sum2 / count) /
                  (ii * jj * (count - 1.0));
            if (Rast_is_d_null_value(rp))
                Rast_set_d_null_value(rp, 1);
        }
        /* write actual result row to the output file */
        Rast_put_d_row(out_fd, result);
    }
    G_percent(row, nrows, 2);

    Rast_close(in_fd1);
    Rast_close(in_fd2);
    Rast_close(out_fd);

    if (copycolr)
        Rast_write_colors(ncb.newcell.name, ncb.newcell.mapset, &colr);

    exit(EXIT_SUCCESS);
}
