/****************************************************************************
 *
 * MODULE:       i.rotate
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates an arbitrary rotation of the image from the
 *                  center of the computing window
 *
 * COPYRIGHT:    (C) 2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#include <grass/config.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/gprojects.h>
#include <grass/glocale.h>

double **ad2d(int X, int Y)
{
    int i;
    double **A = (double **)malloc(X * sizeof(double *));

    for (i = 0; i < X; i++)
        A[i] = (double *)malloc(Y * sizeof(double));
    return A;
}

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *in, *out, *n;
    struct History history; /*metadata */
    int infd, outfd;
    DCELL *inrast, *outrast;
    char outName[GNAME_MAX];
    struct Key_Value *proj_info, *unit_info;
    struct pj_info proj;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("rotation"));
    G_add_keyword(_("computation window centre"));
    module->description =
        _("Rotates the image around the centre of the computational window");

    /* Define the different options */
    in = G_define_standard_option(G_OPT_R_INPUT);
    out = G_define_standard_option(G_OPT_R_OUTPUT);
    n = G_define_option();
    n->key = "angle";
    n->key_desc = "degrees";
    n->type = TYPE_DOUBLE;
    n->required = YES;
    n->description = _("Rotation angle");
    n->answer = "20.0";

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    infd = Rast_open_old(in->answer, "");
    inrast = Rast_allocate_d_buf();

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    outrast = Rast_allocate_d_buf();
    outfd = Rast_open_new(out->answer, DCELL_TYPE);

    /*mat_struct *G_matrix_init(int rows, int cols, int ldim) */
    /*Increase dimension of image to > of sqrt(2) to fit rotated angles */
    int matnrows = nrows * 2;
    int matncols = ncols * 2;
    int deltarow = 0.5 * (matnrows - nrows);
    int deltacol = 0.5 * (matncols - ncols);
    double **matin = ad2d(matnrows, matncols);
    double **matout = ad2d(matnrows, matncols);

    for (row = 0; row < matnrows; row++) {
        for (col = 0; col < matncols; col++) {
            matin[row][col] = -999.99;
            matout[row][col] = -999.99;
        }
    }
    DCELL d;

    /* Get projection info for mapset */
    if ((proj_info = G_get_projinfo()) == NULL)
        G_fatal_error(_("Unable to get projection info of raster map"));

    if ((unit_info = G_get_projunits()) == NULL)
        G_fatal_error(_("Unable to get projection units of raster map"));

    if (pj_get_kv(&proj, proj_info, unit_info) < 0)
        G_fatal_error(_("Unable to get projection key values of raster map"));

    /* Load input matrix with row&col shift to keep center of image */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(infd, inrast, row);
        for (col = 0; col < ncols; col++) {
            d = ((DCELL *)inrast)[col];
            if (Rast_is_d_null_value(&d)) {
                /* SKIPIT  */
                /* matin[row+deltarow][col+deltacol]=-999.99; */
            }
            else {
                matin[row + deltarow][col + deltacol] = d;
            }
        }
    }
    double theta = atof(n->answer);
    double thetarad = theta * M_PI / 180;
    double costheta = cos(thetarad);
    double sintheta = sin(thetarad);
    int newrow, newcol;

    /*Rotate the matrix */
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            newcol = (col - 0.5 * ncols) * costheta +
                     (row - 0.5 * nrows) * sintheta + 0.5 * ncols;
            newrow = (row - 0.5 * nrows) * costheta -
                     (col - 0.5 * ncols) * sintheta + 0.5 * nrows;
            matout[newrow][newcol] = matin[row][col];
        }
    }

    /*Output to raster file */
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            if (matout[row][col] == -999.99) {
                Rast_set_d_null_value(&outrast[col], 1);
            }
            else {
                ((DCELL *)outrast)[col] = matout[row][col];
            }
        }
        Rast_put_d_row(outfd, outrast);
    }

    G_free(inrast);
    Rast_close(infd);
    G_free(outrast);
    Rast_close(outfd);
    Rast_short_history(outName, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(outName, &history);
    exit(EXIT_SUCCESS);
}
