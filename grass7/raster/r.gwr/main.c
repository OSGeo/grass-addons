
/****************************************************************************
 *
 * MODULE:       r.gwr
 * 
 * AUTHOR(S):    Markus Metz
 * 
 * PURPOSE:      Geographically weighted regression
 *               Calculates multiple linear regression from raster maps:
 *               y = b0 + b1*x1 + b2*x2 + ... +  bn*xn + e
 *               with localized b coefficients 
 * 
 * COPYRIGHT:    (C) 2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "local_proto.h"


int main(int argc, char *argv[])
{
    unsigned int r, c, rows, cols, count;
    int *mapx_fd, mapy_fd, mapres_fd, mapest_fd;
    int i, j, k, n_predictors;
    double yres;
    double *B, *Bmin, *Bmax, *Bsum, *Bsumsq, *Bmean, Bstddev;
    int bcount;
    DCELL *yest;
    double sumY, meanY;
    double SStot, SSerr, SSreg, *SSerr_without;
    double Rsq, Rsqadj, SE, F, t, AIC, AICc, BIC;
    DCELL *mapx_val, mapy_val, *mapy_buf, *mapres_buf, *mapest_buf;
    struct rb *xbuf, ybuf;
    struct outputb {
	int fd;
	char name[GNAME_MAX];
	DCELL *buf;
    } *outb, *outbp;
    double **weights;
    int bw;
    char *name;
    struct Option *input_mapx, *input_mapy,
                  *output_res, *output_est, *output_b, *output_opt,
		  *bw_opt, *kernel_opt, *vf_opt;
    struct Flag *shell_style, *estimate;
    /*struct Flag *adaptive;*/
    struct Cell_head region;
    struct GModule *module;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    module->description =
	_("Calculates geographically weighted regression from raster maps.");

    /* Define the different options */
    input_mapx = G_define_standard_option(G_OPT_R_INPUTS);
    input_mapx->key = "mapx";
    input_mapx->description = (_("Map(s) with X variables"));

    input_mapy = G_define_standard_option(G_OPT_R_INPUT);
    input_mapy->key = "mapy";
    input_mapy->description = (_("Map with Y variable"));

    output_res = G_define_standard_option(G_OPT_R_OUTPUT);
    output_res->key = "residuals";
    output_res->required = NO;
    output_res->description = (_("Map to store residuals"));

    output_est = G_define_standard_option(G_OPT_R_OUTPUT);
    output_est->key = "estimates";
    output_est->required = NO;
    output_est->description = (_("Map to store estimates"));

    output_b = G_define_option();
    output_b->key = "coefficients";
    output_b->type = TYPE_STRING;
    output_b->required = NO;
    output_b->description = (_("Prefix for maps to store coefficients"));

    output_opt = G_define_standard_option(G_OPT_F_OUTPUT);
    output_opt->key = "output";
    output_opt->required = NO;
    output_opt->description =
	(_("ASCII file for storing regression coefficients (output to screen if file not specified)."));

    kernel_opt = G_define_option();
    kernel_opt->key = "kernel";
    kernel_opt->type = TYPE_STRING;
    kernel_opt->options = "gauss,epanechnikov,bisquare,tricubic";
    kernel_opt->answer = "gauss";
    kernel_opt->required = NO;
    kernel_opt->description =
	(_("Weighing kernel function."));

    bw_opt = G_define_option();
    bw_opt->key = "bandwidth";
    bw_opt->type = TYPE_INTEGER;
    bw_opt->answer = "10";
    bw_opt->required = YES;
    bw_opt->description =
	(_("Bandwidth of the weighing kernel."));

    vf_opt = G_define_option();
    vf_opt->key = "vf";
    vf_opt->type = TYPE_INTEGER;
    vf_opt->options = "1,2,4,8";
    vf_opt->answer = "1";
    vf_opt->required = NO;
    vf_opt->description =
	(_("Variance factor for Gaussian kernel: variance = bandwith / factor."));

    shell_style = G_define_flag();
    shell_style->key = 'g';
    shell_style->description = _("Print in shell script style");

    estimate = G_define_flag();
    estimate->key = 'e';
    estimate->description = _("Estimate optimal bandwidth");

    /*adaptive = G_define_flag();
    adaptive->key = 'a';
    adaptive->description = _("Adaptive kernel size");*/

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    name = output_opt->answer;
    if (name != NULL && strcmp(name, "-") != 0) {
	if (NULL == freopen(name, "w", stdout)) {
	    G_fatal_error(_("Unable to open file <%s> for writing"), name);
	}
    }

    G_get_window(&region);
    rows = region.rows;
    cols = region.cols;

    /* count x maps */
    for (i = 0; input_mapx->answers[i]; i++);
    n_predictors = i;
    
    /* allocate memory for x maps */
    mapx_fd = (int *)G_malloc(n_predictors * sizeof(int));
    SSerr_without = (double *)G_malloc(n_predictors * sizeof(double));
    mapx_val = (DCELL *)G_malloc((n_predictors + 1) * sizeof(DCELL));
    yest = G_malloc(sizeof(DCELL) * (n_predictors + 1));

    bw = atoi(bw_opt->answer);
    if (bw < 2)
	G_fatal_error(_("Option <%s> must be > 1"), bw_opt->key);

    /*if(adaptive->answer)*/
        /*IN MAKING*/

    set_wfn(kernel_opt->answer, atoi(vf_opt->answer));

    /* open maps */
    G_debug(1, "open maps");

    for (i = 0; i < n_predictors; i++) {
	mapx_fd[i] = Rast_open_old(input_mapx->answers[i], "");
    }
    mapy_fd = Rast_open_old(input_mapy->answer, "");

    for (i = 0; i < n_predictors; i++) {
	SSerr_without[i] = 0.0;
    }
    meanY = sumY = 0.0;

    if (estimate->answer) {
	bw = estimate_bandwidth(mapx_fd, n_predictors, mapy_fd, rows, cols,
				yest, bw);
	if (shell_style->answer)
	    fprintf(stdout, "estimate=%d\n", bw);
	else
	    G_message("Estimated optimal bandwidth: %d", bw);

	exit(EXIT_SUCCESS);
    }

    xbuf = (struct rb *)G_malloc(n_predictors * sizeof(struct rb));

    for (i = 0; i < n_predictors; i++) {
	allocate_bufs(&xbuf[i], cols, bw, mapx_fd[i]);
    }
    allocate_bufs(&ybuf, cols, bw, mapy_fd);

    meanY = sumY = 0.0;

    G_message(_("Calculating average..."));
    count = 0;
    mapy_buf = Rast_allocate_d_buf();

    for (r = 0; r < rows; r++) {
	G_percent(r, rows, 2);

	Rast_get_d_row(mapy_fd, mapy_buf, r);

	for (c = 0; c < cols; c++) {

	    mapy_val = mapy_buf[c];

	    if (!Rast_is_d_null_value(&mapy_val)) {
		sumY += mapy_val;
		count++;
	    }
	}
    }
    G_percent(rows, rows, 2);

    if (count < (unsigned int) (n_predictors + 1))
	G_fatal_error(_("Not enough valid cells available"));

    meanY = sumY / count;

    /* residuals output */
    if (output_res->answer) {
	mapres_fd = Rast_open_new(output_res->answer, DCELL_TYPE);
	mapres_buf = Rast_allocate_d_buf();
    }
    else {
	mapres_fd = -1;
	mapres_buf = NULL;
    }

    /* estimates output */
    if (output_est->answer) {
	mapest_fd = Rast_open_new(output_est->answer, DCELL_TYPE);
	mapest_buf = Rast_allocate_d_buf();
    }
    else {
	mapest_fd = -1;
	mapest_buf = NULL;
    }

    /* gwr for each cell: get estimate */
    G_message(_("Geographically weighted regression..."));

    weights = w_fn(bw);
    count = 0;
    mapx_val[0] = 1.0;
    SStot = SSerr = SSreg = 0.0;
    for (i = 0; i < n_predictors; i++) {
	SSerr_without[i] = 0.0;
    }

    /* initialize the raster buffers with 'bw' rows */
    for (i = 0; i < bw; i++) {
	for (j = 0; j < n_predictors; j++)
	    readrast(&(xbuf[j]), rows, cols);
	readrast(&ybuf, rows, cols);
    }

    /* initialize coefficient statistics */
    Bmin = G_malloc((n_predictors + 1) * sizeof(double));
    Bmax = G_malloc((n_predictors + 1) * sizeof(double));
    Bsum = G_malloc((n_predictors + 1) * sizeof(double));
    Bsumsq = G_malloc((n_predictors + 1) * sizeof(double));
    Bmean = G_malloc((n_predictors + 1) * sizeof(double));
    
    /* localized coefficients */
    for (i = 0; i <= n_predictors; i++) {
	Bmin[i] = 1.0 / 0.0;	/* inf */
	Bmax[i] = -1.0 / 0.0;	/* -inf */
	Bsum[i] = Bsumsq[i] = Bmean[i] = 0;
    }
    bcount = 0;

    outb = outbp = NULL;
    if (output_b->answer) {
	outb = G_malloc((n_predictors + 1) * sizeof(struct outputb));

	for (i = 0; i <= n_predictors; i++) {
	    outbp = &outb[i];
	    sprintf(outbp->name, "%s.%d", output_b->answer, i);
	    
	    outbp->fd = Rast_open_new(outbp->name, DCELL_TYPE);
	    outbp->buf = Rast_allocate_d_buf();
	}
    }

    for (r = 0; r < rows; r++) {
	G_percent(r, rows, 2);

	for (i = 0; i < n_predictors; i++) {
	    readrast(&(xbuf[i]), rows, cols);
	}

	readrast(&ybuf, rows, cols);

	if (mapres_buf)
	    Rast_set_d_null_value(mapres_buf, cols);
	if (mapest_buf)
	    Rast_set_d_null_value(mapest_buf, cols);

	if (outb) {
	    for (i = 0; i <= n_predictors; i++) {
		outbp = &outb[i];
		Rast_set_d_null_value(outbp->buf, cols);
	    }
	}

	for (c = 0; c < cols; c++) {
	    int isnull = 0;

	    for (i = 0; i < n_predictors; i++) {
		mapx_val[i + 1] = xbuf[i].buf[bw][c + bw];
		if (Rast_is_d_null_value(&(mapx_val[i + 1]))) {
		    isnull = 1;
		    break;
		}
	    }
	    if (isnull)
		continue;

	    if (!gwr(xbuf, n_predictors, &ybuf, c, bw, weights, yest, &B)) {
		G_warning(_("Unable to determine coefficients. Consider increasing the bandwidth."));
		continue;
	    }
	    
	    /* coefficient stats */
	    for (i = 0; i <= n_predictors; i++) {
		if (Bmin[i] > B[i])
		    Bmin[i] = B[i];
		if (Bmax[i] < B[i])
		    Bmax[i] = B[i];
		Bsum[i] += B[i];
		Bsumsq[i] += B[i] * B[i];

		/* output raster for coefficients */
		if (outb) {
		    outbp = &outb[i];
		    outbp->buf[c] = B[i];
		}
	    }
	    bcount++;

	    /* set estimate */
	    if (mapest_buf)
		mapest_buf[c] = yest[0];

	    mapy_val = ybuf.buf[bw][c + bw];
	    if (Rast_is_d_null_value(&mapy_val))
		continue;

	    /* set residual */
	    yres = mapy_val - yest[0];
	    if (mapres_buf)
		mapres_buf[c] = yres;

	    SStot += (mapy_val - meanY) * (mapy_val - meanY);
	    SSreg += (yest[0] - meanY) * (yest[0] - meanY);
	    SSerr += yres * yres;

	    for (k = 1; k <= n_predictors; k++) {

		/* linear model without predictor k */
		yres = mapy_val - yest[k];

		/* linear model without predictor k */
		SSerr_without[k - 1] += yres * yres;
	    }
	    count++;
	}
	if (mapres_buf)
	    Rast_put_d_row(mapres_fd, mapres_buf);
	if (mapest_buf)
	    Rast_put_d_row(mapest_fd, mapest_buf);
	if (outb) {
	    for (i = 0; i <= n_predictors; i++) {
		outbp = &outb[i];
		Rast_put_d_row(outbp->fd, outbp->buf);
	    }
	}
    }
    G_percent(rows, rows, 2);

    fprintf(stdout, "n=%d\n", count);
    /* coefficient of determination aka R squared */
    Rsq = 1 - (SSerr / SStot);
    fprintf(stdout, "Rsq=%g\n", Rsq);
    /* adjusted coefficient of determination */
    Rsqadj = 1 - ((SSerr * (count - 1)) / (SStot * (count - n_predictors - 1)));
    fprintf(stdout, "Rsqadj=%g\n", Rsqadj);
    /* F statistic */
    /* F = ((SStot - SSerr) / (n_predictors)) / (SSerr / (count - n_predictors));
     * , or: */
    F = ((SStot - SSerr) * (count - n_predictors - 1)) / (SSerr * (n_predictors));
    fprintf(stdout, "F=%g\n", F);

    i = 0;
    /* constant aka estimate for intercept in R */
    Bmean[i] = Bsum[i] / bcount;
    fprintf(stdout, "bmean%d=%g\n", i, Bmean[i]);
    Bstddev = sqrt(Bsumsq[i] / bcount - (Bmean[i] * Bmean[i]));
    fprintf(stdout, "bstddev%d=%g\n", i, Bstddev);
    fprintf(stdout, "bmin%d=%g\n", i, Bmin[i]);
    fprintf(stdout, "bmax%d=%g\n", i, Bmax[i]);
    /* t score for R squared of the full model, unused */
    t = sqrt(Rsq) * sqrt((count - 2) / (1 - Rsq));
    /*
    fprintf(stdout, "t%d=%f\n", i, t);
    */

    /* AIC, corrected AIC, and BIC information criteria for the full model */
    AIC = count * log(SSerr / count) + 2 * (n_predictors + 1);
    fprintf(stdout, "AIC=%g\n", AIC);
    AICc = AIC + (2 * n_predictors * (n_predictors + 1)) / (count - n_predictors - 1);
    fprintf(stdout, "AICc=%g\n", AICc);
    BIC = count * log(SSerr / count) + log(count) * (n_predictors + 1);
    fprintf(stdout, "BIC=%g\n", BIC);

    /* error variance of the model, identical to R */
    SE = SSerr / (count - n_predictors - 1);
    /*
    fprintf(stdout, "SE=%f\n", SE);
    fprintf(stdout, "SSerr=%f\n", SSerr);
    */

    /* variance = sumsq - (sum / n)^2 */

    for (i = 0; i < n_predictors; i++) {

	fprintf(stdout, "predictor%d=%s\n", i + 1, input_mapx->answers[i]);
	Bmean[i + 1] = Bsum[i + 1] / bcount;
	fprintf(stdout, "bmean%d=%g\n", i + 1, Bmean[i + 1]);
	Bstddev = sqrt(Bsumsq[i + 1] / bcount - (Bmean[i + 1] * Bmean[i + 1]));
	fprintf(stdout, "bstddev%d=%g\n", i + 1, Bstddev);
	fprintf(stdout, "bmin%d=%g\n", i + 1, Bmin[i + 1]);
	fprintf(stdout, "bmax%d=%g\n", i + 1, Bmax[i + 1]);

	if (n_predictors > 1) {
	    double Rsqi;

	    /* corrected sum of squares for predictor [i] */
	    /* sumsqX_corr = sumsqX[i] - sumX[i] * sumX[i] / (count - n_predictors - 1); */

	    /* standard error SE for predictor [i] */

	    /* SE[i] with only one predictor: sqrt(SE / sumsqX_corr)
	     * this does not work with more than one predictor */
	    /* in R, SEi is sqrt(diag(R) * resvar) with
	     * R = ???
	     * resvar = rss / rdf = SE global
	     * rss = sum of squares of the residuals
	     * rdf = residual degrees of freedom = count - n_predictors - 1 */
	    /* SEi = sqrt(SE / (Rsq * sumsqX_corr)); */
	    /*
	    fprintf(stdout, "SE%d=%f\n", i + 1, SEi);
	    */

	    /* Sum of squares for predictor [i] */
	    /*
	    fprintf(stdout, "SSerr%d=%f\n", i + 1, SSerr_without[i] - SSerr);
	    */

	    /* R squared of the model without predictor [i] */
	    /* Rsqi = 1 - SSerr_without[i] / SStot; */
	    /* the additional amount of variance explained
	     * when including predictor [i] :
	     * Rsq - Rsqi */
	    Rsqi = (SSerr_without[i] - SSerr) / SStot;
	    fprintf(stdout, "Rsq%d=%g\n", i + 1, Rsqi);

	    /*
	    fprintf(stdout, "t%d=%f\n", i + 1, t);
	    */

	    /* F score for Fisher's F distribution
	     * here: F score to test if including predictor [i]
	     * yields a significant improvement
	     * after Lothar Sachs, Angewandte Statistik:
	     * F = (Rsq - Rsqi) * (count - n_predictors - 1) / (1 - Rsq) */
	    /* same like Sumsq / SE */
	    /* same like (SSerr_without[i] / SSerr - 1) * (count - n_predictors - 1) */
	    /* same like R-stats when entered in R-stats as last predictor */
	    F = (SSerr_without[i] / SSerr - 1) * (count - n_predictors - 1);
	    fprintf(stdout, "F%d=%g\n", i + 1, F);

	    /* AIC, corrected AIC, and BIC information criteria for
	     * the model without predictor [i] */
	    AIC = count * log(SSerr_without[i] / count) + 2 * (n_predictors);
	    fprintf(stdout, "AIC%d=%g\n", i + 1, AIC);
	    AICc = AIC + (2 * (n_predictors - 1) * n_predictors) / (count - n_predictors - 2);
	    fprintf(stdout, "AICc%d=%g\n", i + 1, AICc);
	    BIC = count * log(SSerr_without[i] / count) + (n_predictors - 1) * log(count);
	    fprintf(stdout, "BIC%d=%g\n", i + 1, BIC);
	}
    }
    

    for (i = 0; i < n_predictors; i++) {
	Rast_close(mapx_fd[i]);
    }
    Rast_close(mapy_fd);
    G_free(mapy_buf);
    
    if (mapres_fd > -1) {
	struct History history;

	Rast_close(mapres_fd);
	G_free(mapres_buf);

	Rast_short_history(output_res->answer, "raster", &history);
	Rast_command_history(&history);
	Rast_write_history(output_res->answer, &history);
    }

    if (mapest_fd > -1) {
	struct History history;

	Rast_close(mapest_fd);
	G_free(mapest_buf);

	Rast_short_history(output_est->answer, "raster", &history);
	Rast_command_history(&history);
	Rast_write_history(output_est->answer, &history);
    }

    if (outb) {
	for (i = 0; i <= n_predictors; i++) {
	    struct History history;

	    outbp = &outb[i];
	    Rast_close(outbp->fd);
	    G_free(outbp->buf);

	    Rast_short_history(outbp->name, "raster", &history);
	    Rast_command_history(&history);
	    Rast_write_history(outbp->name, &history);
	}
    }

    exit(EXIT_SUCCESS);
}
