/****************************************************************************
 *
 * MODULE:       r.seg
 *
 * AUTHOR:       Alfonso Vitti <alfonso.vitti ing.unitn.it>
 *
 * PURPOSE:	 generates a piece-wise smooth approximation of the input 
 *               raster map and a raster map of the discontinuities (edges) of
 *               the output approximation. The discontinuities of the output 
 *               approximation are preserved from being smoothed.
 *
 * REFERENCE:    http://www.ing.unitn.it/~vittia/phd/vitti_phd.pdf
 *
 * COPYRIGHT:    (C) 2007-2010
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/config.h>
#include <grass/glocale.h>
#include "varseg.h"

int main(int argc, char *argv[])
{
    struct Cell_head cellhd;	/* region information */
    char *in_g;			/* input, raster map to be segmented */
    char *out_z;		/* output, raster map with detected discontinuities (edges) */
    char *out_u;		/* output, segmented raster map */
    double lambda;		/* scale coefficient */
    double alpha;		/* elasticity coefficient */
    double kepsilon;		/* discontinuities thickness */
    double beta;		/* rigidity coefficient */
    double tol;			/* convergence tolerance */
    double *mxdf;		/* maximum difference betweed two iteration steps */
    int max_iter;		/* max number of numerical iterations */
    int iter;			/* iteration index */
    char *mapset;		/* current mapset */
    void *g_row;		/* input row buffers */
    void *out_u_row, *out_z_row;	/* output row buffer */
    int nr, nc, nrc;		/* number of rows and colums */
    int i, j;			/* row and column indexes: i=colum=x, j=row=y */
    int jnc;			/* row sequential position, for pointers */
    int g_fd, out_u_fd, out_z_fd;	/* file descriptors */
    int usek;			/* use MSK (MS with the curvature term) */
    RASTER_MAP_TYPE dcell_data_type;	/* GRASS raster data type (for DCELL raster) */
    double *g, *u, *z;		/* the variables for the actual computation */

    struct History history;	/* for map history */
    struct GModule *module;	/* GRASS module for parsing */
    struct
    {
	struct Option *in_g, *out_z, *out_u;	/* parameters */
    } parm;
    struct
    {
	struct Option *lambda, *kepsilon, *alpha, *beta, *tol, *max_iter;	/* other parameters */
    } opts;
    struct Flag *flag_k;	/* flag, k = use MSK instead of MS */


    /* initialize GRASS environment */
    G_gisinit(argv[0]);		/*reads GRASS env */


    /* initialize module */
    module = G_define_module();
    module->keywords = _("image segmentation, edge detection, smooth");
    module->description =
	_("Generates a smooth approximation of the input raster and a discontinuity map");

    parm.in_g = G_define_option();
    parm.in_g->key = "in_g";
    parm.in_g->type = TYPE_STRING;
    parm.in_g->required = YES;
    parm.in_g->description = _("Input raster map to segment");
    parm.in_g->gisprompt = "old,cell,raster";

    parm.out_u = G_define_option();
    parm.out_u->key = "out_u";
    parm.out_u->type = TYPE_STRING;
    parm.out_u->required = YES;
    parm.out_u->description = _("Output segmented raster map");
    parm.out_u->gisprompt = "new,cell,raster";

    parm.out_z = G_define_option();
    parm.out_z->key = "out_z";
    parm.out_z->type = TYPE_STRING;
    parm.out_z->required = YES;
    parm.out_z->description =
	_("Output raster map with detected discontinuities");
    parm.out_z->gisprompt = "new,cell,raster";

    opts.lambda = G_define_option();
    opts.lambda->key = "lambda";
    opts.lambda->type = TYPE_DOUBLE;
    opts.lambda->required = NO;
    opts.lambda->answer = "1.0";
    opts.lambda->description = _("Smoothness coefficient [>0]");

    opts.alpha = G_define_option();
    opts.alpha->key = "alpha";
    opts.alpha->type = TYPE_DOUBLE;
    opts.alpha->required = NO;
    opts.alpha->answer = "1.0";
    opts.alpha->description = _("Discontinuity coefficient [>0]");

    opts.max_iter = G_define_option();
    opts.max_iter->key = "mxi";
    opts.max_iter->type = TYPE_INTEGER;
    opts.max_iter->required = NO;
    opts.max_iter->answer = "100";
    opts.max_iter->description =
	_("Maximal number of numerical iterations");

    opts.tol = G_define_option();
    opts.tol->key = "tol";
    opts.tol->type = TYPE_DOUBLE;
    opts.tol->required = NO;
    opts.tol->answer = "0.001";
    opts.tol->description = _("Convergence tolerance [>0]");

    opts.kepsilon = G_define_option();
    opts.kepsilon->key = "kepsilon";
    opts.kepsilon->type = TYPE_DOUBLE;
    opts.kepsilon->required = NO;
    opts.kepsilon->answer = "1.0";
    opts.kepsilon->description =
	_("Discontinuity thickness [>0]");

    opts.beta = G_define_option();
    opts.beta->key = "beta";
    opts.beta->type = TYPE_DOUBLE;
    opts.beta->required = NO;
    opts.beta->answer = "0.0";
    opts.beta->description = _("Curvature coefficient [>=0]");
    /* 
     * beta = 0 leads to MS
     * beta > 0 leads to MSK
     * Due to a different implementation of MSK wrt MS, 
     * the values of the parameters lambda and alpha in MSK
     * have to be set independently from the values used in MS
     */

    flag_k = G_define_flag();
    flag_k->key = 'k';
    flag_k->description = _("Activate MSK model (Mumford-Shah with curvature term)");


    /* parameters and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* store parameters and flags to variables */
    in_g = parm.in_g->answer;
    out_u = parm.out_u->answer;
    out_z = parm.out_z->answer;

    lambda = atof(opts.lambda->answer);
    kepsilon = atof(opts.kepsilon->answer);
    alpha = atof(opts.alpha->answer);
    beta = atof(opts.beta->answer);
    tol = atof(opts.tol->answer);
    max_iter = atoi(opts.max_iter->answer);

    if (((usek = (flag_k->answer) == 0) && (beta != 0.0)))
	G_warning(_
		  ("Beta is not zero and you have not activated the MSK formulation: \n \
				beta will be ignored and MS (default) will be used."));

    if (((usek = (flag_k->answer) == 1) && (beta == 0.0)))
	G_warning(_
		  ("You have activated the MSK formulation, but beta is zero:\n \
				beta should be greater than zero in MSK."));

    /* check existence and names of raster maps */
    mapset = G_find_cell2(in_g, "");
    if (!mapset)
	G_fatal_error(_("raster file [%s] not found"), in_g);
    if (G_legal_filename(out_u) < 0)
	G_fatal_error(_("[%s] is an illegal file name"), out_u);
    G_check_input_output_name(in_g, out_u, GR_FATAL_EXIT);
    if (G_legal_filename(out_z) < 0)
	G_fatal_error(_("[%s] is an illegal file name"), out_z);
    G_check_input_output_name(in_g, out_z, GR_FATAL_EXIT);
    if (strcmp(out_u, out_z) == 0)
	G_fatal_error(_("Output raster maps have the same name [%s]"), out_u);


    /* -------------------------------------------------------------------- */
    /*      Do the work                                                     */
    /* -------------------------------------------------------------------- */

    /* data type for the computation */
    dcell_data_type = DCELL_TYPE;


    /* get the window dimention */
    nr = G_window_rows();
    nc = G_window_cols();
    nrc = nr * nc;


    /* allocate the memory for the varialbes used in the computation */
    g = (DCELL *) G_malloc(sizeof(DCELL) * nrc);
    u = (DCELL *) G_malloc(sizeof(DCELL) * nrc);
    z = (DCELL *) G_malloc(sizeof(DCELL) * nrc);

    mxdf = (double *)malloc(sizeof(double));


    /* open the input raster map for reading */
    if ((g_fd = G_open_cell_old(in_g, mapset)) < 0)
	G_fatal_error(_("cannot open raster file [%s]"), in_g);
    if (G_get_cellhd(in_g, mapset, &cellhd) < 0)
	G_fatal_error(_("cannot read [%s] header"), in_g);


    /* allocate the buffer for storing the values of the input raster map */
    g_row = G_allocate_raster_buf(dcell_data_type);


    /* read the input raster map + fill up the variable pointers with pixel values */
    for (j = 0; j < nr; j++) {
	jnc = j * nc;

	if (G_get_raster_row(g_fd, g_row, j, dcell_data_type) < 0)
	    G_fatal_error(_("Cannot read from [%s] raster,"), in_g);

	for (i = 0; i < nc; i++) {
	    *(g + jnc + i) = ((DCELL *) g_row)[i];
	    *(u + jnc + i) = ((DCELL *) g_row)[i];
	    *(z + jnc + i) = 1.0;
	}
    }


    /* close the input raster map and free memory */
    G_close_cell(g_fd);
    G_free(g_row);


    /* the first iteration is always performed */
    iter = 1;


    /* call the library function to perform the segmentation */
    if (usek == 0) {
	*mxdf = 0;
	ms_n(g, u, z, lambda, kepsilon, alpha, mxdf, nr, nc);
	while ((*mxdf > tol) && (iter <= max_iter)) {
	    *mxdf = 0;
	    ms_n(g, u, z, lambda, kepsilon, alpha, mxdf, nr, nc);
	    iter += 1;
	}
    }
    else {
	*mxdf = 0;
	msk_n(g, u, z, lambda, kepsilon, alpha, beta, mxdf, nr, nc);
	while ((*mxdf > tol) && (iter <= max_iter)) {
	    *mxdf = 0;
	    msk_n(g, u, z, lambda, kepsilon, alpha, beta, mxdf, nr, nc);
	    iter += 1;
	}
    }


    /* print the total number of iteration performed */
    G_message("\nr.seg iterations: %i\n", iter);
    G_message("\n");

    /* open the output raster maps for writing */
    if ((out_u_fd = G_open_raster_new(out_u, dcell_data_type)) < 0)
	G_fatal_error(_("cannot open raster file [%s]"), out_u);
    if ((out_z_fd = G_open_raster_new(out_z, dcell_data_type)) < 0)
	G_fatal_error(_("cannot open raster file [%s]"), out_z);


    /* allocate the buffer for storing the values of the output raster maps */
    out_u_row = G_allocate_raster_buf(dcell_data_type);
    out_z_row = G_allocate_raster_buf(dcell_data_type);


    /* fill up the output buffers with result values + write the output raster maps */
    for (j = 0; j < nr; j++) {
	jnc = j * nc;
	for (i = 0; i < nc; i++) {
	    ((DCELL *) out_u_row)[i] = *(u + jnc + i);
	    ((DCELL *) out_z_row)[i] = *(z + jnc + i);
	}
	if (G_put_raster_row(out_u_fd, out_u_row, dcell_data_type) < 0)
	    G_fatal_error(_("cannot write [%s] raster"), out_u);
	if (G_put_raster_row(out_z_fd, out_z_row, dcell_data_type) < 0)
	    G_fatal_error(_("cannot write [%s] raster"), out_z);
    }


    /* close the input raster map and free memory */
    G_close_cell(out_u_fd);
    G_free(out_u_row);
    G_close_cell(out_z_fd);
    G_free(out_z_row);
    G_free(g);
    G_free(u);
    G_free(z);


    /* write history file */
    G_short_history(out_u, "raster", &history);
    G_command_history(&history);
    sprintf(history.edhist[3], "iterations = %i", iter);
    history.edlinecnt = 4;
    G_write_history(out_u, &history);
    G_write_history(out_z, &history);


    /* exit */
    exit(EXIT_SUCCESS);
}

