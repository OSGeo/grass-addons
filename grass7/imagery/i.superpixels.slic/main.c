
/*******************************************************************************
 *
 * MODULE:       i.superpixels.slic
 * AUTHOR(S):    Rashad Kanavath <rashadkm gmail>
 *               Markus Metz
 *               based on the C++ SLIC implmenetation from:  
 *               http://ivrl.epfl.ch/research/superpixels
 * PURPOSE:      Perform superpixel segmenation
 *
 * This code performs superpixel segmentation as explained in the paper:
 * "SLIC Superpixels", Radhakrishna Achanta, Appu Shaji, 
 * Kevin Smith, Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk.
 * EPFL Technical Report no. 149300, June 2010. 
 * Below code is ported to grass from original C++ SLIC implmenetation 
 * available at:  http://ivrl.epfl.ch/research/superpixels
 *
 *****************************************************************************/

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include <float.h>

#ifndef MAX
#define MAX(x,y) ((x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y) ((x) < (y) ? (x) : (y))
#endif

int SLIC_EnforceLabelConnectivity(int **labels, int ncols, int nrows,
				   int **nlabels, int minsize);

int main(int argc, char *argv[])
{
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *opt_grp;		/* imagery group input option */
    struct Option *opt_iteration, *opt_super_pixels, *opt_step, 
                  *opt_compactness, *opt_minsize;
    struct Option *opt_out;	/* option for output */
    struct Flag *flag_n;

    struct Ref group_ref;
    char grp_name[INAME_LEN];
    int *ifd, nbands;
    DCELL **ibuf, *min, *max, *rng;
    struct FPRange drange;
    char *outname;
    int outfd;
    CELL *obuf;

    int n_iterations, n_super_pixels, numk, numlabels, slic0;
    int nrows, ncols, row, col, b, k;

    double compactness;
    int superpixelsize, minsize;
    int step;
    int offset;
    DCELL ***pdata;
    int **klabels, **nlabels;
    double **distvec, **distspec;

    double xerrperstrip, yerrperstrip;
    int xstrips, ystrips, xoff, yoff, xerr, yerr;

    double xe, ye;
    int x, y, x1, y1, x2, y2, itr;
    short hexgrid, perturbseeds;
    int seedx, seedy;

    int *clustersize;
    double *kseedsx, *kseedsy;
    double **kseedsb;
    double **sigmab, *sigmax, *sigmay;
    double *maxdistspec;

    double invwt;
    double dist, distxy, dx, dy;
    double distsum;


    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("segmentation"));
    G_add_keyword(_("superpixels"));
    G_add_keyword(_("SLIC"));
    module->description =
	_("Perform image segmentation using the SLIC segmentation method.");

    opt_grp = G_define_standard_option(G_OPT_I_GROUP);

    opt_out = G_define_standard_option(G_OPT_R_OUTPUT);

    opt_iteration = G_define_option();
    opt_iteration->key = "iter";
    opt_iteration->type = TYPE_INTEGER;
    opt_iteration->required = NO;
    opt_iteration->description = _("Maximum number of iterations");
    opt_iteration->answer = "10";

    opt_super_pixels = G_define_option();
    opt_super_pixels->key = "k";
    opt_super_pixels->type = TYPE_INTEGER;
    opt_super_pixels->required = NO;
    opt_super_pixels->description = _("Number of super pixels");
    opt_super_pixels->answer = "200";

    opt_step = G_define_option();
    opt_step->key = "step";
    opt_step->type = TYPE_INTEGER;
    opt_step->required = NO;
    opt_step->label = _("Step size between super pixels");
    opt_step->description = _("Step size has precedence of number of super pixels");
    opt_step->answer = "0";

    opt_compactness = G_define_option();
    opt_compactness->key = "co";
    opt_compactness->type = TYPE_DOUBLE;
    opt_compactness->required = NO;
    opt_compactness->description = _("Compactness");
    opt_compactness->answer = "1";

    opt_minsize = G_define_option();
    opt_minsize->key = "min";
    opt_minsize->type = TYPE_INTEGER;
    opt_minsize->required = NO;
    opt_minsize->description = _("Minimum superpixel size");
    opt_minsize->answer = "1";

    flag_n = G_define_flag();
    flag_n->key = 'n';
    flag_n->label = _("Normalize spectral distances");
    flag_n->description = _("Equvivalent to SLIC zero (SCLI0)");


    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    perturbseeds = 0;
    hexgrid = 0;
    compactness = 0;
    superpixelsize = 0;

    G_strip(opt_grp->answer);
    strcpy(grp_name, opt_grp->answer);

    /* find group */
    if (!I_find_group(grp_name))
	G_fatal_error(_("Group <%s> not found"), grp_name);

    /* get the group ref */
    if (!I_get_group_ref(grp_name, (struct Ref *)&group_ref))
	G_fatal_error(_("Could not read REF file for group <%s>"), grp_name);

    nbands = group_ref.nfiles;
    if (nbands <= 0) {
	G_important_message(_("Group <%s> contains no raster maps; run i.group"),
			    opt_grp->answer);
	exit(EXIT_SUCCESS);
    }

    n_iterations = 10;
    if (opt_iteration->answer) {
	if (sscanf(opt_iteration->answer, "%d", &n_iterations) != 1) {
	    G_fatal_error(_("Illegal value for iter (%s)"),
			  opt_iteration->answer);
	}
    }

    n_super_pixels = 200;
    if (opt_super_pixels->answer) {
	if (sscanf(opt_super_pixels->answer, "%d", &n_super_pixels) != 1) {
	    G_fatal_error(_("Illegal value for k (%s)"),
			  opt_super_pixels->answer);
	}
    }

    step = 0;
    if (opt_step->answer) {
	if (sscanf(opt_step->answer, "%d", &step) != 1) {
	    G_fatal_error(_("Illegal value for step size (%s)"),
			  opt_step->answer);
	}
    }

    compactness = 1;
    if (opt_compactness->answer) {
	if (sscanf(opt_compactness->answer, "%lf", &compactness) != 1) {
	    G_fatal_error(_("Illegal value for co (%s)"),
			  opt_compactness->answer);
	}
    }

    minsize = 1;
    if (opt_minsize->answer) {
	if (sscanf(opt_minsize->answer, "%d", &minsize) != 1) {
	    G_fatal_error(_("Illegal value for minsize (%s)"),
			  opt_minsize->answer);
	}
    }

    slic0 = flag_n->answer;

    outname = opt_out->answer;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* determine seed grid */
    offset = step;
    superpixelsize = step * step;
    if (step < 5) {
	superpixelsize = 0.5 + (double)nrows * ncols / n_super_pixels;

	offset = sqrt((double)superpixelsize) + 0.5;
    }

    xstrips = (0.5 + (double)ncols / offset);
    ystrips = (0.5 + (double)nrows / offset);

    xerr = ncols - offset * xstrips;
    if (xerr < 0) {
	xstrips--;
	xerr = ncols - offset * xstrips;
    }

    yerr = nrows - offset * ystrips;
    if (yerr < 0) {
	ystrips--;
	yerr = nrows - offset * ystrips;
    }

    xerrperstrip = (double)xerr / xstrips;
    yerrperstrip = (double)yerr / ystrips;

    xoff = offset / 2;
    yoff = offset / 2;

    numk = xstrips * ystrips;

    G_debug(1, "superpixelsize = %d", superpixelsize);
    G_debug(1, "nrows = %d", nrows);
    G_debug(1, "ncols = %d", ncols);
    G_debug(1, "xerrperstrip = %g", xerrperstrip);
    G_debug(1, "yerrperstrip = %g", yerrperstrip);
    G_debug(1, "numk = %d", numk);

    /* load input bands */
    pdata = G_malloc(sizeof(DCELL *) * nbands);

    ifd = G_malloc(sizeof(int *) * nbands);
    ibuf = G_malloc(sizeof(DCELL **) * nbands);
    min = G_malloc(sizeof(DCELL) * nbands);
    max = G_malloc(sizeof(DCELL) * nbands);
    rng = G_malloc(sizeof(DCELL) * nbands);

    for (b = 0; b < nbands; b++) {
	ibuf[b] = Rast_allocate_d_buf();
	ifd[b] =
	    Rast_open_old(group_ref.file[b].name, group_ref.file[b].mapset);

	Rast_read_fp_range(group_ref.file[b].name, group_ref.file[b].mapset,
			   &drange);
	Rast_get_fp_range_min_max(&drange, &min[b], &max[b]);
	rng[b] = max[b] - min[b];

    }

    pdata = G_malloc(sizeof(DCELL **) * nrows);
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	pdata[row] = G_malloc(sizeof(DCELL *) * ncols);

	for (b = 0; b < nbands; b++)
	    Rast_get_d_row(ifd[b], ibuf[b], row);
	for (col = 0; col < ncols; col++) {

	    pdata[row][col] = G_malloc(sizeof(DCELL) * nbands);

	    for (b = 0; b < nbands; b++) {
		if (Rast_is_d_null_value(&ibuf[b][col])) {
		    Rast_set_d_null_value(pdata[row][col], nbands);
		    break;
		}
		pdata[row][col][b] = (ibuf[b][col] - min[b]) / rng[b];
	    }
	}
    }

    for (b = 0; b < nbands; b++) {
	Rast_close(ifd[b]);
	G_free(ibuf[b]);
    }
    G_free(ifd);
    G_free(ibuf);

    /* allocate seed variables */
    kseedsb = G_malloc(sizeof(double *) * numk);
    for (k = 0; k < numk; k++) {
	kseedsb[k] = G_malloc(sizeof(double) * nbands);
	memset(kseedsb[k], 0, sizeof(double) * nbands);
    }

    kseedsx = G_malloc(sizeof(double) * numk);
    memset(kseedsx, 0, sizeof(double) * numk);

    kseedsy = G_malloc(sizeof(double) * numk);
    memset(kseedsy, 0, sizeof(double) * numk);

    /* initial seed values */
    k = 0;
    for (y = 0; y < ystrips; y++) {
	ye = y * yerrperstrip;
	for (x = 0; x < xstrips; x++) {
	    xe = x * xerrperstrip;
	    seedx = (x * offset + xoff + xe);
	    if (hexgrid > 0) {
		seedx = x * offset + (xoff << (y & 0x1)) + xe;
		seedx = MIN(ncols - 1, seedx);
	    }			/* for hex grid sampling */

	    seedy = (y * offset + yoff + ye);

	    if (!Rast_is_d_null_value(pdata[seedy][seedx])) {
		for (b = 0; b < nbands; b++) {
		    kseedsb[k][b] = pdata[seedy][seedx][b];
		}
		kseedsx[k] = seedx;
		kseedsy[k] = seedy;
		k++;
	    }
	}
    }
    if (k != numk)
	G_warning(_("Initialized %d of %d seeds"), k, numk);

    clustersize = G_malloc(sizeof(int) * numk);
    memset(clustersize, 0, sizeof(int) * numk);

    sigmab = G_malloc(sizeof(double *) * numk);
    for (k = 0; k < numk; k++) {
	sigmab[k] = G_malloc(sizeof(double) * nbands);
	memset(sigmab[k], 0, sizeof(double) * nbands);
    }

    sigmax = G_malloc(sizeof(double) * numk);
    memset(sigmax, 0, sizeof(double) * numk);

    sigmay = G_malloc(sizeof(double) * numk);
    memset(sigmay, 0, sizeof(double) * numk);


    /* allocate cell variables */
    klabels = G_malloc(sizeof(int *) * nrows);

    for (row = 0; row < nrows; row++) {
	klabels[row] = G_malloc(sizeof(int) * ncols);
	for (col = 0; col < ncols; col++)
	    klabels[row][col] = -1;
    }

    distvec = G_malloc(sizeof(double *) * nrows);
    for (row = 0; row < nrows; row++)
	distvec[row] = G_malloc(sizeof(double) * ncols);

    distspec = G_malloc(sizeof(double *) * nrows);
    for (row = 0; row < nrows; row++) {
	distspec[row] = G_malloc(sizeof(double) * ncols);
	for (col = 0; col < ncols; col++)
	    distspec[row][col] = 0;
    }

    maxdistspec = G_malloc(sizeof(double) * numk);

    for (k = 0; k < numk; k++)
	maxdistspec[k] = 1;

    /* magic factor */
    invwt = 0.1 * compactness / (offset * offset);

    for (itr = 0; itr < n_iterations; itr++) {
	G_percent(itr, n_iterations, 2);

	for (row = 0; row < nrows; row++) {
	    for (col = 0; col < ncols; col++) {
		distvec[row][col] = 1E+9;
		distspec[row][col] = 0;
	    }
	}

	for (k = 0; k < numk; k++) {
	    y1 = (int)MAX(0.0, kseedsy[k] - offset);
	    y2 = (int)MIN(nrows - 1, kseedsy[k] + offset);
	    x1 = (int)MAX(0.0, kseedsx[k] - offset);
	    x2 = (int)MIN(ncols - 1, kseedsx[k] + offset);

	    for (y = y1; y <= y2; y++) {
		dy = y - kseedsy[k];
		
		for (x = x1; x <= x2; x++) {
		    if (Rast_is_d_null_value(pdata[y][x]))
			continue;
		    
		    dist = 0.0;
		    for (b = 0; b < nbands; b++) {
			dist += (pdata[y][x][b] - kseedsb[k][b]) *
			        (pdata[y][x][b] - kseedsb[k][b]);
		    }
		    dist /= nbands;

		    dx = x - kseedsx[k];
		    distxy = (dx * dx + dy * dy) / 2.0;

		    /* ----------------------------------------------------------------------- */
		    distsum = dist / maxdistspec[k] + distxy * invwt;
		    /* dist = sqrt(dist) + sqrt(distxy*invwt);  this is more exact */
		    /*------------------------------------------------------------------------ */
		    if (distsum < distvec[y][x]) {
			distvec[y][x] = distsum;
			distspec[y][x] = dist;
			klabels[y][x] = k;
		    }

		}		/* for( x=x1 */
	    }			/* for( y=y1 */
	}			/* for (n=0 */

	if (slic0) {
	    /* adaptive m for SLIC zero */
	    if (itr == 0) {
		for (k = 0; k < numk; k++)
		    maxdistspec[k] = 1.0 / nbands;
	    }
	    for (row = 0; row < nrows; row++) {
		for (col = 0; col < ncols; col++) {
		    k = klabels[row][col];
		    if (k >= 0) {
			if (maxdistspec[k] < distspec[row][col])
			    maxdistspec[k] = distspec[row][col];
		    }
		}
	    }
	}

	for (k = 0; k < numk; k++) {
	    memset(sigmab[k], 0, sizeof(double) * nbands);
	}

	memset(sigmax, 0, sizeof(double) * numk);
	memset(sigmay, 0, sizeof(double) * numk);
	memset(clustersize, 0, sizeof(int) * numk);

	for (row = 0; row < nrows; row++) {
	    for (col = 0; col < ncols; col++) {
		if (klabels[row][col] >= 0) {
		    for (b = 0; b < nbands; b++) {
			sigmab[klabels[row][col]][b] += pdata[row][col][b];
		    }
		    sigmax[klabels[row][col]] += col;
		    sigmay[klabels[row][col]] += row;

	    /*-------------------------------------------*/
		    /* edgesum[klabels[ind]] += edgemag[ind];    */

	    /*-------------------------------------------*/
		    clustersize[klabels[row][col]] += 1;
		}
	    }
	}

	for (k = 0; k < numk; k++) {
	    if (clustersize[k] <= 0)
		clustersize[k] = 1;

	    for (b = 0; b < nbands; b++) {
		kseedsb[k][b] = sigmab[k][b] / clustersize[k];
	    }
	    kseedsx[k] = sigmax[k] / clustersize[k];
	    kseedsy[k] = sigmay[k] / clustersize[k];

      /*------------------------------------*/
	    /* edgesum[k] *= inv[k];              */

      /*------------------------------------*/
	}
    }
    G_percent(1, 1, 1);

    nlabels = G_malloc(sizeof(int *) * nrows);
    for (row = 0; row < nrows; row++) {
	nlabels[row] = G_malloc(sizeof(int) * ncols);
	memset(nlabels[row], 0, sizeof(int) * ncols);
    }

    numlabels = SLIC_EnforceLabelConnectivity(klabels, ncols, nrows, 
                                              nlabels, minsize);

    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    if (klabels[row][col] >= 0)
		klabels[row][col] = nlabels[row][col];
	}
    }

    outfd = Rast_open_new(outname, CELL_TYPE);
    obuf = Rast_allocate_c_buf();
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    if (klabels[row][col] < 0)
		Rast_set_c_null_value(&obuf[col], 1);
	    else
		obuf[col] = klabels[row][col] + 1;	/* +1 to avoid category value 0 */
	}
	Rast_put_row(outfd, obuf, CELL_TYPE);
    }

    Rast_close(outfd);

    /* history */

    /* random colors */

    exit(EXIT_SUCCESS);
}


int SLIC_EnforceLabelConnectivity(int **labels, int ncols, int nrows,
                                  int **nlabels,	/*new labels */
				  int minsize)
{

    const int dx4[4] = { -1, 0, 1, 0 };
    const int dy4[4] = { 0, -1, 0, 1 };

    int n, label, adjlabel;
    int row, col;
    int x, y, c, count;
    int *xvec, *yvec, vec_alloc;

    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++)
	    nlabels[row][col] = -1;
    }
    label = 0;

    vec_alloc = 100;
    xvec = G_malloc(sizeof(int) * vec_alloc);
    yvec = G_malloc(sizeof(int) * vec_alloc);

    adjlabel = 0;		/* adjacent label */

    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    if (labels[row][col] >= 0 && nlabels[row][col] < 0) {
		nlabels[row][col] = label;

		/*--------------------
		 Start a new segment
		 --------------------*/
		xvec[0] = col;
		yvec[0] = row;

		/*-------------------------------------------------------
		 Quickly find an adjacent label for use later if needed
		 -------------------------------------------------------*/

		for (n = 0; n < 4; n++) {
		    x = xvec[0] + dx4[n];
		    y = yvec[0] + dy4[n];
		    if ((x >= 0 && x < ncols) && (y >= 0 && y < nrows)) {
			if (nlabels[y][x] >= 0)
			    adjlabel = nlabels[y][x];
		    }
		}

		count = 1;
		for (c = 0; c < count; c++) {
		    for (n = 0; n < 4; n++) {
			x = xvec[c] + dx4[n];
			y = yvec[c] + dy4[n];

			if ((x >= 0 && x < ncols) && (y >= 0 && y < nrows)) {

			    if (0 > nlabels[y][x] &&
				labels[row][col] == labels[y][x]) {
				if (vec_alloc <= count) {
				    vec_alloc += 100;
				    xvec =
					G_realloc(xvec,
						  sizeof(int) * vec_alloc);
				    yvec =
					G_realloc(yvec,
						  sizeof(int) * vec_alloc);
				}
				xvec[count] = x;
				yvec[count] = y;
				nlabels[y][x] = label;
				count++;
			    }
			}
		    }
		}

		/*-------------------------------------------------------
		 If segment size is less than a limit, assign an
		 adjacent label found before, and decrement label count.
		-------------------------------------------------------*/
		if (count < minsize) {
		    for (c = 0; c < count; c++) {
			nlabels[yvec[c]][xvec[c]] = adjlabel;
		    }
		    label--;
		}
		label++;
	    }
	}
    }

    G_free(xvec);
    G_free(yvec);

    return label;
}
