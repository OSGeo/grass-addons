/****************************************************************
 *
 * MODULE:     i.pr
 *
 * AUTHOR(S):  Stefano Merler, ITC-irst
 *             Updated to ANSI C by G. Antoniol <giulio.antoniol@gmail.com>
 *
 * PURPOSE:    i.pr - Pattern Recognition
 *
 * COPYRIGHT:  (C) 2007 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *opt1;
    struct Option *opt2;
    struct Option *opt3;
    struct Option *opt4;
    struct Option *opt5;
    char tempbuf[500];
    char *mapset;
    struct Cell_head cellhd;
    double **matrix;
    DCELL *rowbuf;
    DCELL *tf;
    int fd;
    double minv, maxv;
    int minp, maxp;
    int i, j;
    Blob *blobs;
    int nblobs, npoints;
    BlobSites *sites;

    /* Define the different options */

    opt1 = G_define_option();
    opt1->key = "input_map";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->gisprompt = "old,cell,raster";
    opt1->description = "Input raster map for searching for blobs.";

    opt2 = G_define_option();
    opt2->key = "min_pixels";
    opt2->type = TYPE_INTEGER;
    opt2->required = YES;
    opt2->description = "minimum number of pixels defining a blob";

    opt3 = G_define_option();
    opt3->key = "max_pixels";
    opt3->type = TYPE_INTEGER;
    opt3->required = YES;
    opt3->description = "maximum number of pixels defining a blob";

    opt4 = G_define_option();
    opt4->key = "min_value";
    opt4->type = TYPE_DOUBLE;
    opt4->required = YES;
    opt4->description = "minimum value of the map for defining a blob";

    opt5 = G_define_option();
    opt5->key = "max_value";
    opt5->type = TYPE_DOUBLE;
    opt5->required = YES;
    opt5->description =
        "maximum value of the map for defining a blob\n\n\tThe output is a "
        "site file, BUT it will be printed to standard output.";

    /***** Start of main *****/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to search for blobs. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    if (G_parser(argc, argv) < 0)
        exit(EXIT_FAILURE);

    sscanf(opt2->answer, "%d", &minp);
    sscanf(opt3->answer, "%d", &maxp);
    sscanf(opt4->answer, "%lf", &minv);
    sscanf(opt5->answer, "%lf", &maxv);

    if ((mapset = (char *)G_find_raster2(opt1->answer, "")) == NULL) {
        sprintf(tempbuf, "can't open raster map <%s> for reading",
                opt1->answer);
        G_fatal_error(tempbuf);
    }

    if ((fd = Rast_open_old(opt1->answer, mapset)) < 0) {
        sprintf(tempbuf, "error opening raster map <%s>", opt1->answer);
        G_fatal_error(tempbuf);
    }

    G_get_window(&cellhd);

    rowbuf = (DCELL *)G_calloc(cellhd.cols * cellhd.rows, sizeof(DCELL));
    tf = rowbuf;
    matrix = (double **)G_calloc(cellhd.rows, sizeof(double *));
    for (i = 0; i < cellhd.rows; i++)
        matrix[i] = (double *)G_calloc(cellhd.cols, sizeof(double));

    for (i = 0; i < cellhd.rows; i++) {
        Rast_get_d_row(fd, tf, i);
        for (j = 0; j < cellhd.cols; j++) {
            if (Rast_is_d_null_value(tf))
                *tf = maxv + 1.0;
            matrix[i][j] = *tf;
            tf++;
        }
    }
    Rast_close(fd);

    nblobs = 0;
    npoints = 0;
    find_blob(matrix, cellhd.rows, cellhd.cols, &blobs, &npoints, &nblobs, minv,
              maxv);
    sites = (BlobSites *)G_calloc(nblobs, sizeof(BlobSites));

    extract_sites_from_blob(blobs, npoints, nblobs, &cellhd, sites, matrix);

    for (i = 0; i < nblobs; i++)
        if ((sites[i].n >= minp) && (sites[i].n <= maxp))
            fprintf(stdout, "%f|%f|#%d%s%f\n", sites[i].east, sites[i].north,
                    sites[i].n, "%", sites[i].min);

    return 0;
}
