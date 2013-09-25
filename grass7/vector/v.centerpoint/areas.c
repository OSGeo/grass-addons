#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int areas_center(struct Map_info *In, struct Map_info *Out, int layer, 
                 struct cat_list *cat_list, int mode)
{
    int area, nareas, isle, nisles, nisles_alloc;
    struct line_pnts *Points, **IPoints, *OPoints;
    struct line_cats *Cats;
    struct bound_box box;
    double x, y, z, meanx, meany, meanz;
    double *xp, *yp;
    double w, tot_w;
    int i;
    
    Points = Vect_new_line_struct();
    OPoints = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    
    nisles_alloc = 10;
    IPoints = G_malloc(nisles_alloc * sizeof (struct line_pnts *));
    
    nisles = nisles_alloc;
    for (isle = 0; isle < nisles_alloc; isle++) {
	IPoints[isle] = Vect_new_line_struct();
    } 

    nareas = Vect_get_num_areas(In);
    
    /* arithmetic mean = center of gravity */
    if (mode & A_MEAN) {

	G_message(_("Calculating centers of gravity for areas..."));

	G_percent(0, nareas, 4);

	for (area = 1; area <= nareas; area++) {

	    Vect_reset_cats(Cats);
	    if (layer > 1) {
		Vect_get_area_cats(In, area, Cats);
	        if (!Vect_cats_in_constraint(Cats, layer, cat_list))
		    continue;
	    }
	    
	    Vect_get_area_points(In, area, Points);
	    Vect_line_prune(Points);
	    
	    nisles = Vect_get_area_num_isles(In, area);
	    if (nisles > nisles_alloc) {
		IPoints = G_realloc(IPoints, nisles * sizeof (struct line_pnts *));
		for (isle = nisles_alloc; isle < nisles; isle++) {
		    IPoints[isle] = Vect_new_line_struct();
		}
		nisles_alloc = nisles;
	    }
	    for (isle = 1; isle < nisles; isle++) {
		Vect_get_isle_points(In, isle, IPoints[isle - 1]);
		Vect_line_prune(IPoints[isle - 1]);
	    }

	    /* surveyor's / shoelace formula */
	    /* the surveyor should not be too far away (fp precision limit) */
	    /* surveyor's position: */
	    Vect_line_box(Points, &box);
	    x = (box.W + box.E) / 2.;
	    y = (box.S + box.N) / 2.;
	    z = 0;
	    meanx = meany = meanz = 0.;
	    tot_w = 0.;

	    xp = Points->x;
	    yp = Points->y;
	    for (i = 1; i < Points->n_points; i++) {
		w = (x - xp[i - 1]) * (yp[i] - y) - 
		    (x - xp[i]) * (yp[i - 1] - y);

		meanx += (xp[i - 1] + xp[i] + x) * w;
		meany += (yp[i - 1] + yp[i] + y) * w;
		tot_w += w;
	    }

	    for (isle = 0; isle < nisles; isle++) {
		xp = IPoints[isle]->x;
		yp = IPoints[isle]->y;
		for (i = 1; i < IPoints[isle]->n_points; i++) {
		    w = (x - xp[i - 1]) * (yp[i] - y) - 
			(x - xp[i]) * (yp[i - 1] - y);

		    meanx += (xp[i - 1] + xp[i] + x) * w;
		    meany += (yp[i - 1] + yp[i] + y) * w;
		    tot_w += w;
		}
	    }
	    if (tot_w != 0) {
		x = meanx / (tot_w * 3);
		y = meany / (tot_w * 3);
	    }
	    if (Out) {
		Vect_reset_line(OPoints);
		Vect_append_point(OPoints, x, y, z);
		Vect_write_line(Out, GV_POINT, OPoints, Cats);
	    }
	    else
		fprintf(stdout, "7|%.15g|%.15g|%.15g\n", x, y, z);

	    G_percent(area, nareas, 4);
	}
    }

    /* approximate point of minimum distance (geometric median) with Weiszfeld's algorithm:
     * iterative least squares reduction */
    if (mode & A_MEDIAN) {
	struct line_pnts *CPoints;
	double sx, sy, cx, cy, dx, dy;
	double medx, medy;
	double *wc;
	int nwc, nwc_alloc, wci;
	double dist, distsum, dist2all, lastdist2all;
	int j, iter, maxiter = 1000;

	G_message(_("Calculating geometric medians for areas..."));
	
	CPoints = Vect_new_line_struct();
	
	nwc_alloc = 100;
	wc = G_malloc(nwc_alloc * sizeof(double));
	
	G_percent(0, nareas, 4);

	for (area = 1; area <= nareas; area++) {

	    Vect_reset_cats(Cats);
	    if (layer > 1) {
		Vect_get_area_cats(In, area, Cats);
	        if (!Vect_cats_in_constraint(Cats, layer, cat_list))
		    continue;
	    }

	    Vect_get_area_points(In, area, Points);
	    Vect_line_prune(Points);
	    nwc = Points->n_points - 1;
	    
	    nisles = Vect_get_area_num_isles(In, area);
	    if (nisles > nisles_alloc) {
		IPoints = G_realloc(IPoints, nisles * sizeof (struct line_pnts *));
		for (isle = nisles_alloc; isle < nisles; isle++) {
		    IPoints[isle] = Vect_new_line_struct();
		}
		nisles_alloc = nisles;
	    }
	    for (isle = 1; isle < nisles; isle++) {
		Vect_get_isle_points(In, isle, IPoints[isle - 1]);
		Vect_line_prune(IPoints[isle - 1]);
		nwc += IPoints[isle - 1]->n_points - 1;
	    }

	    if (nwc_alloc < nwc) {
		nwc_alloc = nwc;
		wc = G_realloc(wc, nwc_alloc * sizeof(double));
	    }
		
	    /* surveyor's / shoelace formula */
	    /* the surveyor should not be too far away (fp precision limit) */
	    /* surveyor's position: */
	    Vect_line_box(Points, &box);
	    sx = (box.W + box.E) / 2.;
	    sy = (box.S + box.N) / 2.;
	    x = y = z = 0;
	    meanx = meany = meanz = 0.;
	    tot_w = 0.;

	    wci = 0;
	    Vect_reset_line(CPoints);
	    xp = Points->x;
	    yp = Points->y;
	    for (i = 1; i < Points->n_points; i++) {
		w = (sx - xp[i - 1]) * (yp[i] - sy) - 
		    (sx - xp[i]) * (yp[i - 1] - sy);
		
		tot_w += w;

		cx = xp[i - 1] + xp[i] + sx;
		cy = yp[i - 1] + yp[i] + sy;
		meanx += cx * w;
		meany += cy * w;

		wc[wci++] = w;
		Vect_append_point(CPoints, cx / 3., cy / 3., 0);
	    }

	    for (isle = 0; isle < nisles; isle++) {
		xp = IPoints[isle]->x;
		yp = IPoints[isle]->y;
		for (i = 1; i < IPoints[isle]->n_points; i++) {
		    w = (sx - xp[i - 1]) * (yp[i] - sy) - 
			(sx - xp[i]) * (yp[i - 1] - sy);

		    tot_w += w;

		    cx = xp[i - 1] + xp[i] + sx;
		    cy = yp[i - 1] + yp[i] + sy;
		    meanx += cx * w;
		    meany += cy * w;

		    wc[wci++] = w;
		    Vect_append_point(CPoints, cx / 3., cy / 3., 0);
		}
	    }
	    if (tot_w != 0) {
		x = meanx / (tot_w * 3);
		y = meany / (tot_w * 3);
	    }

	    medx = x;
	    medy = y;

	    /* update surveyor's point */
	    sx = x;
	    sy = y;

	    x = y = z = 0;
	    meanx = meany = meanz = 0.;
	    tot_w = 0.;

	    wci = 0;
	    Vect_reset_line(CPoints);
	    xp = Points->x;
	    yp = Points->y;
	    for (i = 1; i < Points->n_points; i++) {
		w = (sx - xp[i - 1]) * (yp[i] - sy) - 
		    (sx - xp[i]) * (yp[i - 1] - sy);
		
		tot_w += w;

		cx = xp[i - 1] + xp[i] + sx;
		cy = yp[i - 1] + yp[i] + sy;
		meanx += cx * w;
		meany += cy * w;

		wc[wci++] = w;
		Vect_append_point(CPoints, cx / 3., cy / 3., 0);
	    }

	    for (isle = 0; isle < nisles; isle++) {
		xp = IPoints[isle]->x;
		yp = IPoints[isle]->y;
		for (i = 1; i < IPoints[isle]->n_points; i++) {
		    w = (sx - xp[i - 1]) * (yp[i] - sy) - 
			(sx - xp[i]) * (yp[i - 1] - sy);

		    tot_w += w;

		    cx = xp[i - 1] + xp[i] + sx;
		    cy = yp[i - 1] + yp[i] + sy;
		    meanx += cx * w;
		    meany += cy * w;

		    wc[wci++] = w;
		    Vect_append_point(CPoints, cx / 3., cy / 3., 0);
		}
	    }
	    if (tot_w != 0) {
		x = meanx / (tot_w * 3);
		y = meany / (tot_w * 3);
	    }

	    lastdist2all = -1;

	    G_debug(3, "Approximating geometric median...");
	    /* depends on the location of the surveyor
	     * why? */

	    for (iter = 0; iter < maxiter; iter++) {

		distsum = dist2all = 0.;
		x = y = z = 0.;

		for (j = 0; j < CPoints->n_points; j++) {

		    dx = CPoints->x[j] - medx;
		    dy = CPoints->y[j] - medy;
		    dist = sqrt(dx * dx + dy * dy);

		    if (dist) {
			w = wc[j] / dist;
			x += CPoints->x[j] * w;
			y += CPoints->y[j] * w;

			distsum += w;
		    }
		    if (wc[j])
			dist2all += dist / fabs(wc[j]);
		}
		
		if (distsum) {
		    x /= distsum;
		    y /= distsum;
		}

		G_debug(3, "dist2all: %.15g", dist2all);
		G_debug(3, "lastdist2all: %.15g", lastdist2all);
		if (lastdist2all > 0) {
		    double d = d_ulp(lastdist2all);
		    
		    if (lastdist2all - dist2all < d)
			break;
		}
		if (dist2all == 0.)
		    break;

		lastdist2all = dist2all;

		medx = x;
		medy = y;

		/* update surveyor's point */
		sx = x;
		sy = y;

		x = y = z = 0;
		meanx = meany = meanz = 0.;
		tot_w = 0.;

		wci = 0;
		Vect_reset_line(CPoints);
		xp = Points->x;
		yp = Points->y;
		for (i = 1; i < Points->n_points; i++) {
		    w = (sx - xp[i - 1]) * (yp[i] - sy) - 
			(sx - xp[i]) * (yp[i - 1] - sy);
		    
		    tot_w += w;

		    cx = xp[i - 1] + xp[i] + sx;
		    cy = yp[i - 1] + yp[i] + sy;
		    meanx += cx * w;
		    meany += cy * w;

		    wc[wci++] = w;
		    Vect_append_point(CPoints, cx / 3., cy / 3., 0);
		}

		for (isle = 0; isle < nisles; isle++) {
		    xp = IPoints[isle]->x;
		    yp = IPoints[isle]->y;
		    for (i = 1; i < IPoints[isle]->n_points; i++) {
			w = (sx - xp[i - 1]) * (yp[i] - sy) - 
			    (sx - xp[i]) * (yp[i - 1] - sy);

			tot_w += w;

			cx = xp[i - 1] + xp[i] + sx;
			cy = yp[i - 1] + yp[i] + sy;
			meanx += cx * w;
			meany += cy * w;

			wc[wci++] = w;
			Vect_append_point(CPoints, cx / 3., cy / 3., 0);
		    }
		}
		if (tot_w != 0) {
		    x = meanx / (tot_w * 3);
		    y = meany / (tot_w * 3);
		}
	    }
	    G_debug(3, "Iteration converged after %d passes, dist = %.15g",
		    iter, lastdist2all);

	    x = medx;
	    y = medy;

	    if (Out) {
		Vect_reset_line(OPoints);
		Vect_append_point(OPoints, x, y, 0);
		Vect_write_line(Out, GV_POINT, OPoints, Cats);
	    }
	    else
		fprintf(stdout, "8|%.15g|%.15g|%.15g\n", x, y, 0.);

	    G_percent(area, nareas, 4);
	}
    }

    /* approximate geometric median with Weiszfeld's algorithm:
     * iterative least squares reduction */
    if (mode & A_MEDIAN_B) {
	struct line_pnts *CPoints;
	double cx, cy, dx, dy;
	double medx, medy;
	double *wb, tot_w;
	int nw, nw_alloc, wi;
	double dist, distsum, dist2all, lastdist2all;
	int j, iter, maxiter = 1000;

	G_message(_("Calculating geometric medians for area boundaries..."));
	
	CPoints = Vect_new_line_struct();
	
	nw_alloc = 100;
	wb = G_malloc(nw_alloc * sizeof(double));
	
	G_percent(0, nareas, 4);

	for (area = 1; area <= nareas; area++) {

	    Vect_reset_cats(Cats);
	    if (layer > 1) {
		Vect_get_area_cats(In, area, Cats);
	        if (!Vect_cats_in_constraint(Cats, layer, cat_list))
		    continue;
	    }

	    Vect_get_area_points(In, area, Points);
	    Vect_line_prune(Points);
	    nw = Points->n_points - 1;
	    
	    nisles = Vect_get_area_num_isles(In, area);
	    if (nisles > nisles_alloc) {
		IPoints = G_realloc(IPoints, nisles * sizeof (struct line_pnts *));
		for (isle = nisles_alloc; isle < nisles; isle++) {
		    IPoints[isle] = Vect_new_line_struct();
		}
		nisles_alloc = nisles;
	    }
	    for (isle = 1; isle < nisles; isle++) {
		Vect_get_isle_points(In, isle, IPoints[isle - 1]);
		Vect_line_prune(IPoints[isle - 1]);
		nw += IPoints[isle - 1]->n_points - 1;
	    }

	    if (nw_alloc < nw) {
		nw_alloc = nw;
		wb = G_realloc(wb, nw_alloc * sizeof(double));
	    }

	    /* segment lengths */
	    meanx = meany = 0.;
	    tot_w = 0.;
	    wi = 0;
	    Vect_reset_line(CPoints);
	    xp = Points->x;
	    yp = Points->y;
	    for (i = 1; i < Points->n_points; i++) {
		dx = xp[i] - xp[i - 1];
		dy = yp[i] - yp[i - 1];
		w = sqrt(dx * dx + dy * dy);

		cx = xp[i - 1] + xp[i];
		meanx += cx * w;
		cy = yp[i - 1] + yp[i];
		meany += cy * w;

		wb[wi++] = w;
		tot_w += w;

		Vect_append_point(CPoints, cx / 2., cy / 2., 0);
	    }

	    for (isle = 0; isle < nisles; isle++) {
		xp = IPoints[isle]->x;
		yp = IPoints[isle]->y;
		for (i = 1; i < IPoints[isle]->n_points; i++) {
		    dx = xp[i] - xp[i - 1];
		    dy = yp[i] - yp[i - 1];
		    w = sqrt(dx * dx + dy * dy);

		    cx = xp[i - 1] + xp[i];
		    meanx += cx * w;
		    cy = yp[i - 1] + yp[i];
		    meany += cy * w;

		    wb[wi++] = w;
		    tot_w += w;

		    Vect_append_point(CPoints, cx / 2., cy / 2., 0);
		}
	    }
	    if (tot_w != 0) {
		meanx /= (tot_w * 2);
		meany /= (tot_w * 2);
	    }

	    medx = meanx;
	    medy = meany;

	    G_debug(3, "Approximating geometric median...");

	    lastdist2all = -1;
	    for (iter = 0; iter < maxiter; iter++) {

		distsum = dist2all = 0.;
		x = y = z = 0.;

		for (j = 0; j < CPoints->n_points; j++) {

		    dx = CPoints->x[j] - medx;
		    dy = CPoints->y[j] - medy;
		    dist = sqrt(dx * dx + dy * dy);

		    if (dist) {
			w = wb[j] / dist;
			x += CPoints->x[j] * w;
			y += CPoints->y[j] * w;

			distsum += w;
		    }
		    if (wb[j])
			dist2all += dist / wb[j];
		}
		
		if (distsum) {
		    x /= distsum;
		    y /= distsum;
		}

		G_debug(3, "dist2all: %.15g", dist2all);
		G_debug(3, "lastdist2all: %.15g", lastdist2all);
		if (lastdist2all > 0) {
		    double d = d_ulp(lastdist2all);
		    
		    if (lastdist2all - dist2all < d)
			break;
		}
		if (dist2all == 0.)
		    break;

		lastdist2all = dist2all;

		medx = x;
		medy = y;
	    }
	    G_debug(3, "Iteration converged after %d passes, dist = %.15g",
		    iter, lastdist2all);

	    x = meanx;
	    y = meany;

	    x = medx;
	    y = medy;

	    if (Out) {
		Vect_reset_line(OPoints);
		Vect_append_point(OPoints, x, y, 0);
		Vect_write_line(Out, GV_POINT, OPoints, Cats);
	    }
	    else
		fprintf(stdout, "9|%.15g|%.15g|%.15g\n", x, y, 0.);

	    G_percent(area, nareas, 4);
	}
    }

    return 1;
}
