
/****************************************************************
 *
 * MODULE:     v.generalize
 *
 * AUTHOR(S):  Daniel Bundala
 *
 * PURPOSE:    Module for line simplification and smoothing
 *
 * COPYRIGHT:  (C) 2002-2005 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include "point.h"

/* boyle's forward looking algorithm
 * return the number of points in the result = Points->n_points
 */
int boyle(struct line_pnts *Points, int look_ahead, int with_z)
{
    POINT last, npoint, ppoint;
    int next, n, i, p;
    double c1, c2;

    n = Points->n_points;

    /* if look_ahead is too small or line too short, there's nothing
     * to smooth */
    if (look_ahead < 2 || look_ahead > n) {
	return n;
    };

    point_assign(Points, 0, with_z, &last);
    c1 = (double)1 / (double)(look_ahead - 1);
    c2 = (double)1 - c1;
    next = 1;

    for (i = 0; i < n - 2; i++) {
	p = i + look_ahead;
	if (p >= n)
	    p = n - 1;
	point_assign(Points, p, with_z, &ppoint);
	point_scalar(ppoint, c1, &ppoint);
	point_scalar(last, c2, &last);
	point_add(last, ppoint, &npoint);
	Points->x[next] = npoint.x;
	Points->y[next] = npoint.y;
	Points->z[next] = npoint.z;
	next++;
	last = npoint;
    };

    points_copy_last(Points, next);
    return Points->n_points;

};

int distance_weighting(struct line_pnts *Points, double slide, int look_ahead,
		       int with_z)
{
    POINT p, c, s, tmp;
    int n, i, next, half, j;
    double dists, d;
    POINT *res;

    n = Points->n_points;

    if (look_ahead % 2 == 0) {
	G_warning(_("Look ahead parameter must be odd"));
	return n;
    };

    res = (POINT *) G_malloc(sizeof(POINT) * n);
    if (!res){
        G_fatal_error(_("Out of memory"));
        return n;
    };  

    point_assign(Points, 0, with_z, &res[0]);

    next = 1;
    half = look_ahead / 2;

    for (i = half; i + half < n; i++) {
	point_assign(Points, i, with_z, &c);
	s.x = s.y = s.z = 0;
	dists = 0;


	for (j = i - half; j <= i + half; j++) {
	    if (j == i)
		continue;
	    point_assign(Points, j, with_z, &p);
	    d = point_dist(p, c);
	    if (d < 0.0000000001)
		continue;
	    d = (double)1.0 / d;
	    dists += d;
	    point_scalar(p, d, &tmp);
	    s.x += tmp.x;
	    s.y += tmp.y;
	    s.z += tmp.z;
	};
	point_scalar(s, slide / dists, &tmp);
	point_scalar(c, (double)1.0 - slide, &s);
	point_add(s, tmp, &res[next]);
	next++;
    };

    for (i = 0; i < next; i++) {
	Points->x[i] = res[i].x;
	Points->y[i] = res[i].y;
	Points->z[i] = res[i].z;
    };

    G_free(res);

    points_copy_last(Points, next);
    return Points->n_points;
};


/* Chaiken's algorithm. Return the number of points in smoothed line 
 * TODO: remove sqrt from the distance test
 */
int chaiken(struct line_pnts *Points, double thresh, int with_z)
{

    int n, i;
    POINT_LIST head, *cur;
    POINT p0, p1, p2, m1, m2, tmp;

    n = Points->n_points;

    /* line is too short */
    if (n < 3)
	return n;

    //  thresh *= thresh;

    head.next = NULL;
    cur = &head;
    point_assign(Points, 0, with_z, &head.p);
    point_assign(Points, 0, with_z, &p0);

    for (i = 2; i <= n; i++) {
	if (i == n)
	    point_assign(Points, i - 1, with_z, &p2);
	else
	    point_assign(Points, i, with_z, &p2);
	point_assign(Points, i - 1, with_z, &p1);

	while (1) {
	    point_add(p1, p2, &tmp);
	    point_scalar(tmp, 0.5, &m1);

	    point_list_add(cur, m1);

	    if (point_dist(p0, m1) > thresh) {
		point_add(p1, m1, &tmp);	/* need to refine the partition */
		point_scalar(tmp, 0.5, &p2);
		point_add(p1, p0, &tmp);
		point_scalar(tmp, 0.5, &p1);
	    }
	    else {
		break;		/* good approximatin */
	    };
	};

	while (cur->next != NULL)
	    cur = cur->next;

	p0 = cur->p;
    };

    point_assign(Points, n - 1, with_z, &p0);
    point_list_add(cur, p0);

    if (point_list_copy_to_line_pnts(head, Points) == -1) {
	G_fatal_error(_("Out of Memory"));
	exit(1);
    };

    return Points->n_points;
};
