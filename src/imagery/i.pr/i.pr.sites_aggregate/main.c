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
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"
#include <grass/vector.h>

#define MAXPNTS 1000

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *opt1, *opt2, *opt3, *opt4;
    char *line = NULL;
    FILE *fp;
    int i, j, k, npoints;
    double **data;
    int *mark;
    double max_dist, min_dist;
    double tmpx, tmpy;
    int np, np2;
    double tmpdist;
    int *indice, *indice2;
    double *dist;
    int *indxx;
    int count;

    struct Map_info Out;
    struct Map_info Out2;
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct line_pnts *Points2;
    struct line_cats *Cats2;

    opt1 = G_define_option();
    opt1->key = "sites";
    opt1->type = TYPE_STRING;
    opt1->required = YES;
    opt1->description = "site file";

    opt2 = G_define_option();
    opt2->key = "max_dist";
    opt2->type = TYPE_DOUBLE;
    opt2->required = YES;
    opt2->description = "count sites distant less than max_dist";

    opt3 = G_define_option();
    opt3->key = "min_dist";
    opt3->type = TYPE_DOUBLE;
    opt3->required = YES;
    opt3->description = "count sites distant less than min_dist";

    opt4 = G_define_standard_option(G_OPT_V_OUTPUT);
    opt4->key = "link";
    opt4->description = "Output vector with lines";

    /***** Start of main *****/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("image processing"));
    G_add_keyword(_("pattern recognition"));
    module->description =
        _("Module to aggregate sites. "
          "i.pr: Pattern Recognition environment for image processing. "
          "Includes kNN, "
          "Decision Tree and SVM classification techniques. Also includes "
          "cross-validation and bagging methods for model validation.");

    if (G_parser(argc, argv) < 0)
        exit(EXIT_FAILURE);

    sscanf(opt2->answer, "%lf", &max_dist);
    max_dist *= max_dist;
    sscanf(opt3->answer, "%lf", &min_dist);
    min_dist *= min_dist;

    Vect_open_new(&Out2, opt4->answer, 0);
    sprintf(opt4->answer, "%s_graph", opt4->answer);
    Vect_open_new(&Out, opt4->answer, 0);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    Points2 = Vect_new_line_struct();
    Cats2 = Vect_new_cats_struct();

    data = (double **)G_calloc(1, sizeof(double *));
    data[0] = (double *)G_calloc(3, sizeof(double));

    fp = fopen(opt1->answer, "r");

    /* better to use G_tokenize() here? */
    npoints = 0;
    while ((line = GetLine(fp)) != NULL) {
        sscanf(line, "%lf", &(data[npoints][0]));
        line = (char *)strchr(line, '|');
        *line++;
        sscanf(line, "%lf", &(data[npoints][1]));
        line = (char *)strchr(line, '|');
        *line++;
        sscanf(line, "%lf", &(data[npoints][2]));
        npoints++;
        data = (double **)G_realloc(data, (npoints + 1) * sizeof(double *));
        data[npoints] = (double *)G_calloc(3, sizeof(double));
    }

    mark = (int *)G_calloc(npoints, sizeof(int));
    for (i = 0; i < npoints; i++)
        mark[i] = 0;

    indxx = (int *)G_calloc(MAXPNTS, sizeof(int));
    dist = (double *)G_calloc(MAXPNTS, sizeof(double));
    indice = (int *)G_calloc(MAXPNTS, sizeof(int));
    indice2 = (int *)G_calloc(MAXPNTS, sizeof(int));

    for (i = 0; i < npoints; i++) {
        if (mark[i] == 0) {
            np = 0;
            for (j = i; j < npoints; j++) {
                if (np == MAXPNTS) {
                    fprintf(stderr,
                            "Too many nearest points. Maximum allowed (see var "
                            "MAXPNTS): %d\n",
                            MAXPNTS);
                    exit(-1);
                }
                if (mark[j] == 0) {
                    if ((tmpdist = squared_distance(data[i], data[j], 2)) <
                        max_dist) {
                        indice[np] = j;
                        dist[np] = tmpdist;
                        np++;
                    }
                }
            }

            if (np <= 2 * data[i][2]) {

                indexx_1(np, dist, indxx);

                if (np > data[i][2])
                    count = data[i][2];
                else
                    count = np;

                tmpx = 0;
                tmpy = 0;
                for (j = 0; j < count; j++) {
                    if (mark[indice[indxx[j]]] == 0) {
                        tmpx += data[indice[indxx[j]]][0];
                        tmpy += data[indice[indxx[j]]][1];
                        mark[indice[indxx[j]]] = 1;
                    }
                }
                tmpx /= count;
                tmpy /= count;

                Vect_reset_line(Points2);
                Vect_append_point(Points2, tmpx, tmpy, (double)count);
                Vect_write_line(&Out2, GV_POINT, Points2, Cats2);

                for (j = 0; j < count; j++) {
                    Vect_reset_line(Points);
                    Vect_append_point(Points, data[indice[indxx[j]]][0],
                                      data[indice[indxx[j]]][1], 0.0);
                    Vect_append_point(Points, tmpx, tmpy, 0.0);
                    Vect_write_line(&Out, GV_LINE, Points, Cats);
                }
            }
            else {
                for (j = 0; j < np; j++) {
                    if (mark[indice[j]] == 0) {
                        np2 = 0;
                        for (k = 0; k < np; k++) {
                            if (mark[indice[k]] == 0) {
                                if ((tmpdist = squared_distance(
                                         data[indice[j]], data[indice[k]], 2)) <
                                    min_dist) {
                                    indice2[np2] = indice[k];
                                    np2++;
                                }
                            }
                        }

                        tmpx = 0;
                        tmpy = 0;
                        for (k = 0; k < np2; k++) {
                            tmpx += data[indice2[k]][0];
                            tmpy += data[indice2[k]][1];
                            mark[indice2[k]] = 1;
                        }
                        tmpx /= np2;
                        tmpy /= np2;

                        Vect_reset_line(Points2);
                        Vect_append_point(Points2, tmpx, tmpy, np2);
                        Vect_write_line(&Out2, GV_POINT, Points2, Cats2);

                        for (k = 0; k < np2; k++) {
                            Vect_reset_line(Points);
                            Vect_append_point(Points, data[indice2[k]][0],
                                              data[indice2[k]][1], 0.0);
                            Vect_append_point(Points, tmpx, tmpy, 0.0);
                            Vect_write_line(&Out, GV_LINE, Points, Cats);
                        }
                    }
                }
            }
        }
        percent(i, npoints, 1);
    }
    Vect_build(&Out);
    Vect_close(&Out);
    Vect_build(&Out2);
    Vect_close(&Out2);

    return 1;
}
