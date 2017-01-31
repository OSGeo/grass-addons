
/*******************************************************************************
 *
 * MODULE:       i.superpixels.slic
 * AUTHOR(S):    Rashad Kanavath <rashadkm gmail>
 *               Markus Metz
 *               based on the C++ SLIC implmenetation from:  
 *               http://ivrl.epfl.ch/research/superpixels
 * PURPOSE:      Perform superpixel segmentation
 *
 * This code performs superpixel segmentation as explained in the paper:
 * "SLIC Superpixels", Radhakrishna Achanta, Appu Shaji, 
 * Kevin Smith, Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk.
 * EPFL Technical Report no. 149300, June 2010. 
 * Below code is ported to grass from original C++ SLIC implmenetation 
 * available at:  http://ivrl.epfl.ch/research/superpixels
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	
#include <grass/imagery.h>
#include <grass/glocale.h>

#ifndef MAX
#define MAX(x,y) ((x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x,y) ((x) < (y) ? (x) : (y))
#endif

int SLIC_EnforceLabelConnectivity(SEGMENT *k_seg, int ncols, int nrows,
				  SEGMENT *nk_seg, int minsize);

int merge_small_clumps(SEGMENT *bands_seg, int nbands,
                       SEGMENT *k_seg, int nlabels,
                       int diag, int minsize);

int main(int argc, char *argv[])
{
    struct GModule *module;	/* GRASS module for parsing arguments */
    struct Option *opt_grp;		/* imagery group input option */
    struct Option *opt_iteration, *opt_super_pixels, *opt_step, 
                  *opt_compactness, *opt_minsize, *opt_mem;
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
    struct Colors colors;
    struct History hist;
    
    int nseg;
    double segs_mb, k_mb;

    int n_iterations, n_super_pixels, numk, numlabels, slic0;
    int nrows, ncols, row, col, b, k;

    double compactness;
    int superpixelsize, minsize;
    int step;
    int offset;
    DCELL *pdata;
    double *dists;
    SEGMENT bands_seg, k_seg, nk_seg, dist_seg;
    int schange;

    double xerrperstrip, yerrperstrip;
    int xstrips, ystrips, xoff, yoff, xerr, yerr;

    double xe, ye;
    int x, y, x1, y1, x2, y2, itr;
    short hexgrid, perturbseeds;
    int seedx, seedy;

    int *clustersize;
    double *kseedsx, *kseedsy, *sigmax, *sigmay;
    DCELL **kseedsb, **sigmab;
    double *maxdistspeck, maxdistspec, maxdistspecprev;

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
    opt_iteration->key = "iterations";
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
    opt_step->label = _("Distance (number of cells) between initial super pixel centers");
    opt_step->description = _("A step size > 0 overrides the number of super pixels");
    opt_step->answer = "0";

    opt_compactness = G_define_option();
    opt_compactness->key = "compactness";
    opt_compactness->type = TYPE_DOUBLE;
    opt_compactness->required = NO;
    opt_compactness->label = _("Compactness");
    opt_compactness->description = _("A larger value causes more compact superpixels");
    opt_compactness->answer = "1";

    opt_minsize = G_define_option();
    opt_minsize->key = "minsize";
    opt_minsize->type = TYPE_INTEGER;
    opt_minsize->required = NO;
    opt_minsize->description = _("Minimum superpixel size");
    opt_minsize->answer = "1";

    opt_mem = G_define_option();
    opt_mem->key = "memory";
    opt_mem->type = TYPE_INTEGER;
    opt_mem->required = NO;
    opt_mem->answer = "300";
    opt_mem->description = _("Memory in MB");

    flag_n = G_define_flag();
    flag_n->key = 'n';
    flag_n->label = _("Normalize spectral distances");
    flag_n->description = _("Equvivalent to SLIC zero (SLIC0)");


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

    segs_mb = 300;
    if (opt_mem->answer) {
	int mb = 300;

	if (sscanf(opt_mem->answer, "%d", &mb) != 1) {
	    G_fatal_error(_("Illegal value for memory (%s)"),
			  opt_mem->answer);
	}
	segs_mb = mb;
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

    /* segment structures */
    k_mb = 2 * (sizeof(DCELL) * nbands + 2 * sizeof(double)) + sizeof(double);
    k_mb = k_mb * numk / (1024. * 1024.);

    G_debug(1, "MB for seeds: %g", k_mb);
    if (k_mb >= segs_mb - 10)
	G_fatal_error(_("Not enough memory, increase %s option"), opt_mem->answer);

    segs_mb -= k_mb;
    G_debug(1, "MB for temporary data: %g", segs_mb);

    nseg = 1024. * 1024. * segs_mb / (64 * 64 * (sizeof(DCELL) * nbands + sizeof(double) * 2 + sizeof(int)));
    G_debug(1, "Number of segments in memory: %d", nseg);

    if (Segment_open(&bands_seg, G_tempfile(), nrows, ncols, 64, 64,
                     sizeof(DCELL) * nbands, nseg) != 1)
	G_fatal_error("Unable to create input temporary file");

    if (Segment_open(&k_seg, G_tempfile(), nrows, ncols, 64, 64,
                     sizeof(int), nseg) != 1)
	G_fatal_error("Unable to create input temporary file");

    if (Segment_open(&dist_seg, G_tempfile(), nrows, ncols, 64, 64,
                     sizeof(double) * 2, nseg) != 1)
	G_fatal_error("Unable to create input temporary file");


    /* load input bands */
    G_message(_("Loading input..."));
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

    pdata = G_malloc(sizeof(DCELL) * nbands);
    dists = G_malloc(sizeof(double) * 2);
    dists[0] = dists[1] = 0;
    k = -1;
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	for (b = 0; b < nbands; b++)
	    Rast_get_d_row(ifd[b], ibuf[b], row);
	for (col = 0; col < ncols; col++) {
	    for (b = 0; b < nbands; b++) {
		if (Rast_is_d_null_value(&ibuf[b][col])) {
		    Rast_set_d_null_value(pdata, nbands);
		    break;
		}
		pdata[b] = (ibuf[b][col] - min[b]) / rng[b];
	    }
	    if (Segment_put(&bands_seg, (void *)pdata, row, col) != 1)
		G_fatal_error(_("Unable to write to temporary file"));

	    if (Segment_put(&k_seg, (void *)&k, row, col) != 1)
		G_fatal_error(_("Unable to write to temporary file"));

	    if (Segment_put(&dist_seg, (void *)&dists, row, col) != 1)
		G_fatal_error(_("Unable to write to temporary file"));
	}
    }
    G_percent(nrows, nrows, 2);

    for (b = 0; b < nbands; b++) {
	Rast_close(ifd[b]);
	G_free(ibuf[b]);
    }
    G_free(ifd);
    G_free(ibuf);

    /* allocate seed variables */
    kseedsb = G_malloc(sizeof(DCELL *) * numk);
    for (k = 0; k < numk; k++) {
	kseedsb[k] = G_malloc(sizeof(DCELL) * nbands);
	memset(kseedsb[k], 0, sizeof(DCELL) * nbands);
    }

    kseedsx = G_malloc(sizeof(double) * numk);
    memset(kseedsx, 0, sizeof(double) * numk);

    kseedsy = G_malloc(sizeof(double) * numk);
    memset(kseedsy, 0, sizeof(double) * numk);

    clustersize = G_malloc(sizeof(int) * numk);
    memset(clustersize, 0, sizeof(int) * numk);

    sigmab = G_malloc(sizeof(DCELL *) * numk);
    for (k = 0; k < numk; k++) {
	sigmab[k] = G_malloc(sizeof(DCELL) * nbands);
	memset(sigmab[k], 0, sizeof(DCELL) * nbands);
    }

    sigmax = G_malloc(sizeof(double) * numk);
    memset(sigmax, 0, sizeof(double) * numk);

    sigmay = G_malloc(sizeof(double) * numk);
    memset(sigmay, 0, sizeof(double) * numk);

    maxdistspeck = G_malloc(sizeof(double) * numk);
    for (k = 0; k < numk; k++)
	maxdistspeck[k] = 1;


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

	    Segment_get(&bands_seg, (void *)pdata, seedy, seedx);
	    if (!Rast_is_d_null_value(pdata)) {
		for (b = 0; b < nbands; b++) {
		    kseedsb[k][b] = pdata[b];
		}
		kseedsx[k] = seedx;
		kseedsy[k] = seedy;
		k++;
	    }
	}
    }
    if (k != numk)
	G_warning(_("Initialized %d of %d seeds"), k, numk);

    maxdistspec = maxdistspecprev = 0;

    /* magic factor */
    invwt = 0.1 * compactness / (offset * offset);

    G_message(_("Performing k mean segmentation..."));
    schange = 0;
    for (itr = 0; itr < n_iterations; itr++) {
	G_percent(itr, n_iterations, 2);

	schange = 0;

	dists[0] = 0;
	dists[1] = 1E+9;
	for (row = 0; row < nrows; row++) {
	    for (col = 0; col < ncols; col++) {
		Segment_put(&dist_seg, (void *)&dists, row, col);
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
		    Segment_get(&bands_seg, (void *)pdata, y, x);
		    if (Rast_is_d_null_value(pdata))
			continue;

		    Segment_get(&dist_seg, (void *)dists, y, x);
		    dist = 0.0;
		    for (b = 0; b < nbands; b++) {
			dist += (pdata[b] - kseedsb[k][b]) *
			        (pdata[b] - kseedsb[k][b]);
		    }
		    dist /= nbands;

		    dx = x - kseedsx[k];
		    distxy = (dx * dx + dy * dy) / 2.0;

		    /* ----------------------------------------------------------------------- */
		    distsum = dist / maxdistspeck[k] + distxy * invwt;
		    /* dist = sqrt(dist) + sqrt(distxy*invwt);  this is more exact */
		    /*------------------------------------------------------------------------ */
		    if (distsum < dists[1]) {
			dists[0] = dist;
			dists[1] = distsum;

			Segment_put(&dist_seg, (void *)dists, y, x);
			Segment_put(&k_seg, (void *)&k, y, x);
		    }

		}		/* for( x=x1 */
	    }			/* for( y=y1 */
	}			/* for (n=0 */

	if (slic0) {
	    /* adaptive m for SLIC zero */
	    if (itr == 0) {
		for (k = 0; k < numk; k++)
		    maxdistspeck[k] = 0;
	    }
	    for (row = 0; row < nrows; row++) {
		for (col = 0; col < ncols; col++) {
		    Segment_get(&k_seg, (void *)&k, row, col);
		    if (k >= 0) {
			Segment_get(&dist_seg, (void *)dists, row, col);
			if (maxdistspeck[k] < dists[0])
			    maxdistspeck[k] = dists[0];
		    }
		}
	    }
	}
	else {
	    maxdistspecprev = maxdistspec;
	    maxdistspec = 0;
	    for (row = 0; row < nrows; row++) {
		for (col = 0; col < ncols; col++) {
		    Segment_get(&k_seg, (void *)&k, row, col);
		    if (k >= 0) {
			Segment_get(&dist_seg, (void *)dists, row, col);
			if (maxdistspec < dists[0])
			    maxdistspec = dists[0];
		    }
		}
	    }
	    for (k = 0; k < numk; k++)
		maxdistspeck[k] = maxdistspec;
	    G_debug(1, "Largest spectral distance = %.15g", maxdistspec);
	}

	for (k = 0; k < numk; k++) {
	    memset(sigmab[k], 0, sizeof(double) * nbands);
	}

	memset(sigmax, 0, sizeof(double) * numk);
	memset(sigmay, 0, sizeof(double) * numk);
	memset(clustersize, 0, sizeof(int) * numk);

	for (row = 0; row < nrows; row++) {
	    for (col = 0; col < ncols; col++) {
		Segment_get(&k_seg, (void *)&k, row, col);
		if (k >= 0) {
		    Segment_get(&bands_seg, (void *)pdata, row, col);
		    for (b = 0; b < nbands; b++) {
			sigmab[k][b] += pdata[b];
		    }
		    sigmax[k] += col;
		    sigmay[k] += row;
		    clustersize[k] += 1;
		}
	    }
	}

	for (k = 0; k < numk; k++) {
	    double newxy;
	    int kchange = 0;

	    if (clustersize[k] <= 0)
		clustersize[k] = 1;

	    for (b = 0; b < nbands; b++) {
		DCELL newb;

		newb = sigmab[k][b] / clustersize[k];
		
		if (kseedsb[k][b] != newb)
		    kchange = 1;

		kseedsb[k][b] = newb;
	    }
	    newxy = sigmax[k] / clustersize[k];
	    if (kseedsx[k] != newxy)
		kchange = 1;
	    kseedsx[k] = newxy;
	    newxy = sigmay[k] / clustersize[k];
	    if (kseedsy[k] != newxy)
		kchange = 1;
	    kseedsy[k] = newxy;

	    if (kchange)
		schange++;
	}
	/* SLIC (k mean) converges */
	G_debug(1, "Number of changed seeds: %d", schange);
	if (schange == 0)
	    break;
#if 0
	if (!slic0 && maxdistspecprev == maxdistspec)
	    break;
#endif
    }
    G_percent(1, 1, 1);

    if (itr < n_iterations)
	G_message(_("SLIC converged after %d iterations"), itr);
    if (schange > 0)
	G_verbose_message(_("%d of %d superpixels were modified in the last iteration"),
	                  schange, numk);

    /* free */

    for (k = 0; k < numk; k++) {
	G_free(kseedsb[k]);
	G_free(sigmab[k]);
    }
    G_free(kseedsb);
    G_free(kseedsx);
    G_free(kseedsy);
    G_free(sigmab);
    G_free(sigmax);
    G_free(sigmay);
    G_free(clustersize);

    Segment_close(&dist_seg);

    if (Segment_open(&nk_seg, G_tempfile(), nrows, ncols, 64, 64,
                     sizeof(int), nseg) != 1)
	G_fatal_error("Unable to create input temporary file");

    numlabels = SLIC_EnforceLabelConnectivity(&k_seg, ncols, nrows, 
                                              &nk_seg, 0);
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    Segment_get(&k_seg, (void *)&k, row, col);
	    if (k >= 0) {
		int n;

		Segment_get(&nk_seg, (void *)&n, row, col);
		Segment_put(&k_seg, (void *)&n, row, col);
	    }
	}
    }

    Segment_close(&nk_seg);

    if (minsize > 1)
	numlabels = merge_small_clumps(&bands_seg, nbands, &k_seg,
	                               numlabels, 0, minsize);

    Segment_close(&bands_seg);

    outfd = Rast_open_new(outname, CELL_TYPE);
    obuf = Rast_allocate_c_buf();
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    Segment_get(&k_seg, (void *)&k, row, col);
	    if (k < 0)
		Rast_set_c_null_value(&obuf[col], 1);
	    else
		obuf[col] = k + 1;	/* +1 to avoid category value 0 */
	}
	Rast_put_row(outfd, obuf, CELL_TYPE);
    }

    Rast_close(outfd);
    Segment_close(&k_seg);

    /* history */
    Rast_short_history(outname, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(outname, &hist);

    /* random colors */
    Rast_init_colors(&colors);
    Rast_make_random_colors(&colors, 1, numlabels);
    Rast_write_colors(outname, G_mapset(), &colors);

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}


int SLIC_EnforceLabelConnectivity(SEGMENT *k_seg, int ncols, int nrows,
                                  SEGMENT *nk_seg,	/*new labels */
				  int minsize)
{

    const int dx4[4] = { -1, 0, 1, 0 };
    const int dy4[4] = { 0, -1, 0, 1 };

    int n, label, adjlabel, k, k2, nk;
    int row, col;
    int x, y, c, count;
    int *xvec, *yvec, vec_alloc;

    nk = -1;
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++)
	    Segment_put(nk_seg, (void *)&nk, row, col);
    }
    label = 0;

    vec_alloc = 100;
    xvec = G_malloc(sizeof(int) * vec_alloc);
    yvec = G_malloc(sizeof(int) * vec_alloc);

    adjlabel = 0;		/* adjacent label */

    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    Segment_get(k_seg, (void *)&k, row, col);
	    Segment_get(nk_seg, (void *)&nk, row, col);
	    if (k >= 0 && nk < 0) {
		Segment_put(nk_seg, (void *)&label, row, col);

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
			Segment_get(nk_seg, (void *)&nk, y, x);
			if (nk >= 0)
			    adjlabel = nk;
		    }
		}

		count = 1;
		for (c = 0; c < count; c++) {
		    for (n = 0; n < 4; n++) {
			x = xvec[c] + dx4[n];
			y = yvec[c] + dy4[n];

			if ((x >= 0 && x < ncols) && (y >= 0 && y < nrows)) {

			    Segment_get(k_seg, (void *)&k2, y, x);
			    Segment_get(nk_seg, (void *)&nk, y, x);
			    if (0 > nk && k == k2) {
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
				Segment_put(nk_seg, (void *)&label, y, x);
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
			Segment_put(nk_seg, (void *)&adjlabel, yvec[c], xvec[c]);
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
