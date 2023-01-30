/*******************************************************************************
 *
 * MODULE:       i.superpixels.slic
 * AUTHOR(S):    Rashad Kanavath <rashadkm gmail>
 *               Markus Metz
 *               based on the C++ SLIC implementation from:
 *               http://ivrl.epfl.ch/research/superpixels
 * PURPOSE:      Perform superpixel segmentation
 *
 * This code performs superpixel segmentation as explained in the paper:
 * "SLIC Superpixels", Radhakrishna Achanta, Appu Shaji,
 * Kevin Smith, Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk.
 * EPFL Technical Report no. 149300, June 2010.
 * Below code is ported to GRASS GIS from original C++ SLIC implementation
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
#include "cache.h"

#ifndef MAX
#define MAX(x, y) ((x) > (y) ? (x) : (y))
#endif
#ifndef MIN
#define MIN(x, y) ((x) < (y) ? (x) : (y))
#endif

int SLIC_EnforceLabelConnectivity(struct cache *k_seg, int ncols, int nrows,
                                  struct cache *nk_seg, int minsize);

int perturb_seeds(struct cache *bands_seg, int nbands, DCELL **kseedsb,
                  double *kseedsx, double *kseedsy, int numk, int offset);

int merge_small_clumps(struct cache *bands_seg, int nbands, struct cache *k_seg,
                       int nlabels, int diag, int minsize);

int main(int argc, char *argv[])
{
    struct GModule *module; /* GRASS module for parsing arguments */
    struct Option *opt_in;  /* imagery group input option */
    struct Option *opt_iteration, *opt_super_pixels, *opt_step,
        *opt_compactness, *opt_perturb, *opt_minsize, *opt_mem;
    struct Option *opt_out; /* option for output */
    struct Flag *flag_n, *flag_h;

    struct Ref group_ref;
    int *ifd, nbands;
    DCELL **ibuf, *min, *max, *rng;
    struct FPRange drange;
    char *outname;
    int outfd;
    CELL *obuf;
    struct Colors colors;
    struct History hist;

    int seg_size, nseg;
    double segs_mb, k_mb;

    int n_iterations, n_super_pixels, numk, numlabels, slic0;
    int nrows, ncols, row, col, b, k;

    double compactness;
    int superpixelsize, minsize;
    int step;
    int offset;
    DCELL *pdata;
    double *dists;
    struct cache bands_seg, k_seg, nk_seg, dist_seg;
    int schange;

    double xerrperstrip, yerrperstrip;
    int xstrips, ystrips, xoff, yoff, xerr, yerr;

    double xe, ye;
    int x, y, x1, y1, x2, y2, itr;
    short int hexgrid;
    int perturbseeds;
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

    opt_in = G_define_standard_option(G_OPT_R_INPUTS);
    opt_in->description =
        _("Name of two or more input raster maps or imagery group");

    opt_out = G_define_standard_option(G_OPT_R_OUTPUT);

    opt_iteration = G_define_option();
    opt_iteration->key = "iterations";
    opt_iteration->type = TYPE_INTEGER;
    opt_iteration->required = NO;
    opt_iteration->description = _("Maximum number of iterations");
    opt_iteration->answer = "10";

    opt_super_pixels = G_define_option();
    opt_super_pixels->key = "num_pixels";
    opt_super_pixels->type = TYPE_INTEGER;
    opt_super_pixels->required = NO;
    opt_super_pixels->description =
        _("Approximate number of output super pixels");
    opt_super_pixels->answer = "200";

    opt_step = G_define_option();
    opt_step->key = "step";
    opt_step->type = TYPE_INTEGER;
    opt_step->required = NO;
    opt_step->label =
        _("Distance (number of cells) between initial super pixel centers");
    opt_step->description =
        _("A step size > 1 overrides the number of super pixels");
    opt_step->answer = "0";

    opt_perturb = G_define_option();
    opt_perturb->key = "perturb";
    opt_perturb->type = TYPE_INTEGER;
    opt_perturb->required = NO;
    opt_perturb->options = "0-100";
    opt_perturb->label = _("Perturb initial super pixel centers");
    opt_perturb->description = _("Percent of intitial superpixel radius");
    opt_perturb->answer = "0";

    opt_compactness = G_define_option();
    opt_compactness->key = "compactness";
    opt_compactness->type = TYPE_DOUBLE;
    opt_compactness->required = NO;
    opt_compactness->label = _("Compactness");
    opt_compactness->description =
        _("A larger value causes more compact superpixels");
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

    flag_h = G_define_flag();
    flag_h->key = 'h';
    flag_h->label = _("Hexagonal spacing of super pixel centers");
    flag_h->description = _("Default: rectangular spacing");

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    perturbseeds = 0;
    compactness = 0;
    superpixelsize = 0;

    hexgrid = flag_h->answer;

    for (nbands = 0; opt_in->answers[nbands] != NULL; nbands++)
        ;

    I_init_group_ref(&group_ref);
    if (nbands > 1 || !I_find_group(opt_in->answers[0])) {
        /* create group from input is raster map(s) */
        char name[GNAME_MAX];
        const char *mapset;

        for (nbands = 0; opt_in->answers[nbands] != NULL; nbands++) {
            /* strip @mapset, do not modify opt_in->answers */
            strcpy(name, opt_in->answers[nbands]);
            mapset = G_find_raster(name, "");
            if (!mapset)
                G_fatal_error(_("Raster map <%s> not found"),
                              opt_in->answers[nbands]);
            /* Add input to group. */
            I_add_file_to_group_ref(name, mapset, &group_ref);
        }
    }
    else {
        /* input is group. Try to read group file */
        if (!I_get_group_ref(opt_in->answers[0], &group_ref))
            G_fatal_error(_("Group <%s> not found in the current mapset"),
                          opt_in->answers[0]);

        if (group_ref.nfiles <= 0)
            G_fatal_error(_("Group <%s> contains no raster maps"),
                          opt_in->answers[0]);
    }

    nbands = group_ref.nfiles;

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
            G_fatal_error(_("Illegal value for memory (%s)"), opt_mem->answer);
        }
        segs_mb = mb;
    }

    slic0 = flag_n->answer;

    outname = opt_out->answer;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* determine seed grid */
    superpixelsize = step * step;
    if (step < 2) {
        superpixelsize = 0.5 + (double)nrows * ncols / n_super_pixels;

        step = sqrt((double)superpixelsize) + 0.5;
    }

    xstrips = (0.5 + (double)ncols / step);
    ystrips = (0.5 + (double)nrows / step);
    if (hexgrid > 0)
        ystrips = (0.5 + (double)nrows / (step * 1.5 / sqrt(3)));

    xerr = ncols - step * xstrips;
    if (xerr < 0) {
        xstrips--;
        xerr = ncols - step * xstrips;
    }

    yerr = nrows - step * ystrips;
    if (yerr < 0) {
        ystrips--;
        yerr = nrows - step * ystrips;
    }

    /* purpose: cover the whole region
     * if xerrperstrip != yerrperstrip
     * the result are no longer exact squares */
    xerrperstrip = (double)xerr / xstrips;
    yerrperstrip = (double)yerr / ystrips;

    xoff = step / 2;
    yoff = step / 2;

    numk = xstrips * ystrips;

    G_debug(1, "superpixelsize = %d", superpixelsize);
    G_debug(1, "nrows = %d", nrows);
    G_debug(1, "ncols = %d", ncols);
    G_debug(1, "xerrperstrip = %g", xerrperstrip);
    G_debug(1, "yerrperstrip = %g", yerrperstrip);
    G_debug(1, "numk = %d", numk);

    /* segment structures */
    k_mb = 2 * (sizeof(DCELL *) * 2 + sizeof(DCELL) * nbands +
                2 * sizeof(double)) +
           sizeof(double);
    k_mb = k_mb * numk / (1024. * 1024.);

    G_debug(1, "MB for seeds: %g", k_mb);
    if (k_mb >= segs_mb - 10)
        G_fatal_error(_("Not enough memory, increase %s option"),
                      opt_mem->answer);

    G_debug(1, "MB for temporary data: %g", segs_mb);

    segs_mb -= k_mb;

    seg_size = 64;
    nseg = 1024. * 1024. * segs_mb /
           (seg_size * seg_size *
            (sizeof(DCELL) * nbands + sizeof(double) * 2 + sizeof(int)));

    if (cache_create(&bands_seg, nrows, ncols, seg_size, seg_size,
                     sizeof(DCELL) * nbands, nseg) != 1)
        G_fatal_error("Unable to create grid cache");

    if (cache_create(&dist_seg, nrows, ncols, seg_size, seg_size,
                     sizeof(double) * 2, nseg) != 1)
        G_fatal_error("Unable to create grid cache");

    if (cache_create(&k_seg, nrows, ncols, seg_size, seg_size, sizeof(int),
                     nseg) != 1)
        G_fatal_error("Unable to create grid cache");

    /* load input bands */
    G_message(_("Loading input..."));

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
                if (rng[b] != 0)
                    pdata[b] = (ibuf[b][col] - min[b]) / rng[b];
                else
                    pdata[b] = 0;
            }
            cache_put(&bands_seg, pdata, row, col);
            cache_put(&k_seg, &k, row, col);
            cache_put(&dist_seg, dists, row, col);
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
            seedx = (x * step + xoff + xe);
            seedy = (y * step + yoff + ye);
            if (hexgrid > 0) {
                seedx = x * step + (xoff << (y & 0x1)) + xe;
                seedx = MIN(ncols - 1, seedx);
                seedy = (y * step * 1.5 / sqrt(3) + yoff + ye);
            } /* for hex grid sampling */

            cache_get(&bands_seg, pdata, seedy, seedx);
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
        G_message(_("Initialized %d of %d seeds due to input NULL values"), k,
                  numk);

    perturbseeds = 0;
    if (opt_perturb->answer) {
        if (sscanf(opt_perturb->answer, "%d", &perturbseeds) != 1) {
            G_fatal_error(_("Illegal value for <%s>"), opt_perturb->answer);
        }
        if (perturbseeds > 0) {
            perturbseeds = (step - 1) * perturbseeds / (2 * 100);
            if (perturbseeds == 0)
                perturbseeds = 1;
            perturb_seeds(&bands_seg, nbands, kseedsb, kseedsx, kseedsy, numk,
                          perturbseeds);
        }
    }

    maxdistspec = maxdistspecprev = 0;

    offset = step; /* offset could also be step * 1.5 */

    /* 0.1 * compactness as this seems to give nice results for a default value
     * of compactness = 1. */
    /* We do not square compactness as this would make the result very sensitive
     * to small changes   */
    /* of compactness.
     */
    invwt = 0.1 * compactness / (offset * offset);

    G_message(_("Performing K-means segmentation..."));
    schange = 0;
    for (itr = 0; itr < n_iterations; itr++) {
        G_percent(itr, n_iterations, 2);

        schange = 0;

        dists[0] = 0;
        dists[1] = 1E+9;
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                cache_put(&dist_seg, dists, row, col);
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
                    cache_get(&bands_seg, pdata, y, x);
                    if (Rast_is_d_null_value(pdata))
                        continue;

                    cache_get(&dist_seg, dists, y, x);
                    dist = 0.0;
                    for (b = 0; b < nbands; b++) {
                        dist += (pdata[b] - kseedsb[k][b]) *
                                (pdata[b] - kseedsb[k][b]);
                    }
                    dist /= nbands;

                    dx = x - kseedsx[k];
                    distxy = (dx * dx + dy * dy) / 2.0;

                    /* -----------------------------------------------------------------------
                     */
                    distsum = dist / maxdistspeck[k] + distxy * invwt;
                    /* We use a slightly different formula than that of Achanta
                     * et al.:        */
                    /* D^2 = (dc / m)^2 + c * (ds / S)^2
                     */
                    /* This means that m and S are always determined within the
                     * code and c is  */
                    /* a factor to weigh the relative importance between color
                     * similarity and  */
                    /* spatial proximity. Thus user-determined compactness is
                     * always taken     */
                    /* into account, even in SLIC0, and is independent of the
                     * number of bands. */
                    /*------------------------------------------------------------------------
                     */
                    if (distsum < dists[1]) {
                        dists[0] = dist;
                        dists[1] = distsum;

                        cache_put(&dist_seg, dists, y, x);
                        cache_put(&k_seg, &k, y, x);
                    }

                } /* for( x=x1 */
            }     /* for( y=y1 */
        }         /* for (n=0 */

        if (slic0) {
            /* adaptive m for SLIC zero */
            if (itr == 0) {
                for (k = 0; k < numk; k++)
                    maxdistspeck[k] = 0;
            }
            for (row = 0; row < nrows; row++) {
                for (col = 0; col < ncols; col++) {
                    cache_get(&k_seg, &k, row, col);
                    if (k >= 0) {
                        cache_get(&dist_seg, dists, row, col);
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
                    cache_get(&k_seg, &k, row, col);
                    if (k >= 0) {
                        cache_get(&dist_seg, dists, row, col);
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
                cache_get(&k_seg, &k, row, col);
                if (k >= 0) {
                    cache_get(&bands_seg, pdata, row, col);
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
        /* SLIC (K-means) converges */
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
        G_verbose_message(
            _("%d of %d superpixels were modified in the last iteration"),
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

    cache_destroy(&dist_seg);
    cache_create(&nk_seg, nrows, ncols, seg_size, seg_size, sizeof(int), nseg);

    numlabels = SLIC_EnforceLabelConnectivity(&k_seg, ncols, nrows, &nk_seg, 0);
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            cache_get(&k_seg, &k, row, col);
            if (k >= 0) {
                int n;

                cache_get(&nk_seg, &n, row, col);
                cache_put(&k_seg, &n, row, col);
            }
        }
    }

    cache_destroy(&nk_seg);

    if (minsize > 1)
        numlabels = merge_small_clumps(&bands_seg, nbands, &k_seg, numlabels, 0,
                                       minsize);

    cache_destroy(&bands_seg);

    outfd = Rast_open_new(outname, CELL_TYPE);
    obuf = Rast_allocate_c_buf();
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            cache_get(&k_seg, &k, row, col);
            if (k < 0)
                Rast_set_c_null_value(&obuf[col], 1);
            else
                obuf[col] = k + 1; /* +1 to avoid category value 0 */
        }
        Rast_put_row(outfd, obuf, CELL_TYPE);
    }

    Rast_close(outfd);
    cache_destroy(&k_seg);

    /* history */
    Rast_short_history(outname, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(outname, &hist);

    /* random colors */
    if (numlabels > 1) {
        Rast_init_colors(&colors);
        Rast_make_random_colors(&colors, 1, numlabels);
        Rast_write_colors(outname, G_mapset(), &colors);
    }

    G_done_msg(" ");

    exit(EXIT_SUCCESS);
}

int SLIC_EnforceLabelConnectivity(struct cache *k_seg, int ncols, int nrows,
                                  struct cache *nk_seg, /*new labels */
                                  int minsize)
{

    const int dx4[4] = {-1, 0, 1, 0};
    const int dy4[4] = {0, -1, 0, 1};

    int n, label, adjlabel, k, k2, nk;
    int row, col;
    int x, y, c, count;
    int *xvec, *yvec, vec_alloc;

    nk = -1;
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++)
            cache_put(nk_seg, &nk, row, col);
    }
    label = 0;

    vec_alloc = 100;
    xvec = G_malloc(sizeof(int) * vec_alloc);
    yvec = G_malloc(sizeof(int) * vec_alloc);

    adjlabel = 0; /* adjacent label */

    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            cache_get(k_seg, &k, row, col);
            cache_get(nk_seg, &nk, row, col);
            if (k >= 0 && nk < 0) {
                cache_put(nk_seg, &label, row, col);

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
                        cache_get(nk_seg, &nk, y, x);
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

                            cache_get(k_seg, &k2, y, x);
                            cache_get(nk_seg, &nk, y, x);
                            if (0 > nk && k == k2) {
                                if (vec_alloc <= count) {
                                    vec_alloc += 100;
                                    xvec = G_realloc(xvec,
                                                     sizeof(int) * vec_alloc);
                                    yvec = G_realloc(yvec,
                                                     sizeof(int) * vec_alloc);
                                }
                                xvec[count] = x;
                                yvec[count] = y;
                                cache_put(nk_seg, &label, y, x);
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
                        cache_put(nk_seg, &adjlabel, yvec[c], xvec[c]);
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

int perturb_seeds(struct cache *bands_seg, int nbands, DCELL **kseedsb,
                  double *kseedsx, double *kseedsy, int numk, int offset)
{
    int row, col, rown, coln, nrows, ncols, k, b;
    int nperturbed;
    double g, gmin, d, ds;
    int gn;
    int x, y, xmin, ymin;
    DCELL *pdata, *pdatan;

    G_message(_("Perturbing seeds..."));
    G_verbose_message(_("Perturbing distance : %d"), offset);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    pdata = G_malloc(sizeof(DCELL) * nbands);
    pdatan = G_malloc(sizeof(DCELL) * nbands);

    nperturbed = 0;
    for (k = 0; k < numk; k++) {
        x = kseedsx[k];
        y = kseedsy[k];
        xmin = x;
        ymin = y;

        gmin = -1;
        for (row = y - offset; row <= y + offset; row++) {
            if (row < 0 || row >= nrows)
                continue;
            for (col = x - offset; col <= x + offset; col++) {
                if (col < 0 || col >= ncols)
                    continue;

                cache_get(bands_seg, pdata, row, col);

                if (Rast_is_d_null_value(pdata))
                    continue;

                /* get gradient */
                g = 0;
                gn = 0;

                rown = row - 1;
                coln = col;
                if (rown >= 0 && rown < nrows && coln >= 0 && coln < ncols) {
                    cache_get(bands_seg, pdatan, rown, coln);
                    if (!Rast_is_d_null_value(pdatan)) {
                        ds = 0;
                        for (b = 0; b < nbands; b++) {
                            d = pdata[b] - pdatan[b];
                            ds += d * d;
                        }
                        g += ds / nbands;
                        gn++;
                    }
                }
                rown = row + 1;
                coln = col;
                if (rown >= 0 && rown < nrows && coln >= 0 && coln < ncols) {
                    cache_get(bands_seg, pdatan, rown, coln);
                    if (!Rast_is_d_null_value(pdatan)) {
                        ds = 0;
                        for (b = 0; b < nbands; b++) {
                            d = pdata[b] - pdatan[b];
                            ds += d * d;
                        }
                        g += ds / nbands;
                        gn++;
                    }
                }
                rown = row;
                coln = col - 1;
                if (rown >= 0 && rown < nrows && coln >= 0 && coln < ncols) {
                    cache_get(bands_seg, pdatan, rown, coln);
                    if (!Rast_is_d_null_value(pdatan)) {
                        ds = 0;
                        for (b = 0; b < nbands; b++) {
                            d = pdata[b] - pdatan[b];
                            ds += d * d;
                        }
                        g += ds / nbands;
                        gn++;
                    }
                }
                rown = row;
                coln = col + 1;
                if (rown >= 0 && rown < nrows && coln >= 0 && coln < ncols) {
                    cache_get(bands_seg, pdatan, rown, coln);
                    if (!Rast_is_d_null_value(pdatan)) {
                        ds = 0;
                        for (b = 0; b < nbands; b++) {
                            d = pdata[b] - pdatan[b];
                            ds += d * d;
                        }
                        g += ds / nbands;
                        gn++;
                    }
                }

                if (gn > 0) {
                    g /= gn;
                    if (gmin == -1 || gmin > g) {
                        gmin = g;
                        ymin = row;
                        xmin = col;
                    }
                }
            }
        }
        if (xmin != x || ymin != y) {
            kseedsx[k] = xmin;
            kseedsy[k] = ymin;
            cache_get(bands_seg, pdatan, ymin, xmin);
            memcpy(kseedsb[k], pdatan, sizeof(DCELL) * nbands);
            nperturbed++;
        }
    }

    G_free(pdata);
    G_free(pdatan);

    G_verbose_message(_("%d of %d seeds have been perturbed"), nperturbed,
                      numk);

    return nperturbed;
}
