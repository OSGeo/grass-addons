#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/glocale.h>
#include "global.h"

int init_streams(void)
{
    int d, i;		/* d: direction, i: iteration */
    int r, c;
    int next_stream = -1, cur_stream;
    int out_max = ncols + nrows;
    POINT *outlets;
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    outlets = (POINT *) G_malloc((out_max) * sizeof(POINT));

    outlets_num = 0;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {
		if (outlets_num > (out_max - 1)) {
		    out_max *= 2;
		    outlets =
			(POINT *) G_realloc(outlets, out_max * sizeof(POINT));
		}
		d = abs(dirs[r][c]);	/* abs */
		if (r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||
		    c + nextc[d] < 0 || c + nextc[d] > (ncols - 1)) {
		    next_stream = -1;	/* border */
		}
		else {
		    next_stream = streams[r + nextr[d]][c + nextc[d]];
		    if (next_stream < 1)
			next_stream = -1;
		}
		if (d == 0)
		    next_stream = -1;
		cur_stream = streams[r][c];
		if (cur_stream != next_stream) {	/* is outlet or node! */
		    outlets[outlets_num].r = r;
		    outlets[outlets_num].c = c;

		    if (next_stream == -1)
			outlets[outlets_num].is_outlet = 1;
		    else
			outlets[outlets_num].is_outlet = 0;

		    outlets_num++;
		}
	    }			/* end if streams */
	}			/* end for */
    }				/* end for */

    stat_streams = (STREAM *) G_malloc((outlets_num) * sizeof(STREAM));
    for (i = 0; i < outlets_num; ++i) {
	stat_streams[i].r = outlets[i].r;
	stat_streams[i].c = outlets[i].c;
	stat_streams[i].is_outlet = outlets[i].is_outlet;
	stat_streams[i].index = i;
	stat_streams[i].slope = 0.;
	stat_streams[i].gradient = 0.;
	stat_streams[i].length = 0.;
	stat_streams[i].elev_diff = 0.;
	stat_streams[i].elev_spring = 0.;
	stat_streams[i].elev_outlet = elevation[outlets[i].r][outlets[i].c];
	stat_streams[i].order = streams[outlets[i].r][outlets[i].c];
	stat_streams[i].basin_area = 0.;
	stat_streams[i].cell_num = 0;
    }
    G_free(outlets);
    return 0;
}

int calculate_streams(void)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int i, j, s, d;		/* s - streams index */
    int done = 1;
    int r, c;
    float cur_northing, cur_easting;
    float next_northing, next_easting;
    float diff_elev, cur_length;

    G_begin_distance_calculations();

    for (s = 0; s < outlets_num; ++s) {
	r = stat_streams[s].r;
	c = stat_streams[s].c;

	cur_northing = window.north - (r + .5) * window.ns_res;
	cur_easting = window.west + (c + .5) * window.ew_res;
	d = (dirs[r][c] == 0) ? 2 : abs(dirs[r][c]);

	next_northing = window.north - (r + nextr[d] + .5) * window.ns_res;
	next_easting = window.west + (c + nextc[d] + .5) * window.ew_res;


	/* init length */
	stat_streams[s].length =
	    G_distance(next_easting, next_northing, cur_easting,
		       cur_northing);

	done = 1;

	while (done) {
	    done = 0;
	    cur_northing = window.north - (r + .5) * window.ns_res;
	    cur_easting = window.west + (c + .5) * window.ew_res;

	    stat_streams[s].cell_num++;
	    stat_streams[s].elev_spring = elevation[r][c];

	    for (i = 1; i < 9; ++i) {
		if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		    c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		    continue;	/* border */
		j = (i + 4) > 8 ? i - 4 : i + 4;
		if (streams[r + nextr[i]][c + nextc[i]] ==
		    stat_streams[s].order &&
		    dirs[r + nextr[i]][c + nextc[i]] == j) {

		    next_northing =
			window.north - (r + nextr[i] + .5) * window.ns_res;
		    next_easting =
			window.west + (c + nextc[i] + .5) * window.ew_res;
		    cur_length =
			G_distance(next_easting, next_northing, cur_easting,
				   cur_northing);

		    diff_elev =
			elevation[r + nextr[i]][c + nextc[i]] -
			elevation[r][c];
		    diff_elev = (diff_elev < 0) ? 0. : diff_elev;	/* water cannot flow up */

		    stat_streams[s].length += cur_length;
		    stat_streams[s].slope += (diff_elev / cur_length);

		    r = r + nextr[i];
		    c = c + nextc[i];
		    done = 1;
		    break;
		}		/* end if */
	    }			/* end for i */
	}			/* end while */
    }
    return 0;
}

int calculate_basins(void)
{
    int i;

    total_basins = 0.;

    G_begin_cell_area_calculations();
    fifo_max = 4 * (nrows + ncols);
    fifo_outlet = (POINT *) G_malloc((fifo_max + 1) * sizeof(POINT));

    for (i = 0; i < outlets_num; ++i) {
	stat_streams[i].basin_area =
	    fill_basin(stat_streams[i].r, stat_streams[i].c);

	if (stat_streams[i].is_outlet)
	    total_basins += stat_streams[i].basin_area;
    }
    G_free(fifo_outlet);
    return 0;
}


double fill_basin(int r, int c)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int i, j;
    double area;
    POINT n_cell;

    tail = 0;
    head = -1;
    area = G_area_of_cell_at_row(r);

    while (tail != head) {
	for (i = 1; i < 9; ++i) {
	    if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		continue;	/* border */
	    j = (i + 4) > 8 ? i - 4 : i + 4;
	    if (dirs[r + nextr[i]][c + nextc[i]] == j) {	/* countributing cell */

		area += G_area_of_cell_at_row(r);
		n_cell.r = (r + nextr[i]);
		n_cell.c = (c + nextc[i]);
		fifo_insert(n_cell);
	    }
	}			/* end for i... */

	n_cell = fifo_return_del();
	r = n_cell.r;
	c = n_cell.c;

    }
    return area;
}

/* fifo functions */
int fifo_insert(POINT point)
{
    fifo_outlet[tail++] = point;
    if (tail > fifo_max)
	tail = 0;
    return 0;
}

POINT fifo_return_del(void)
{
    if (head >= fifo_max)
	head = -1;
    return fifo_outlet[++head];
}

int max_order(void)
{
    int i;
    int max_order = 0;

    for (i = 0; i < outlets_num; ++i) {
	if (stat_streams[i].order > max_order)
	    max_order = stat_streams[i].order;
    }
    return max_order;
}

int stats(void)
{
    int i;
    int num, ord_num;
    float snum, ord_snum;
    float tmp_num;

    order_max = max_order();

    ord_stats = (STATS *) G_malloc((order_max + 1) * sizeof(STATS));

    stats_total.order = 0;
    stats_total.stream_num = 0;
    stats_total.sum_length = 0.;
    stats_total.avg_length = 0.;
    stats_total.std_length = 0.;
    stats_total.avg_slope = 0.;
    stats_total.std_slope = 0.;
    stats_total.avg_gradient = 0.;
    stats_total.std_gradient = 0.;
    stats_total.sum_area = 0.;
    stats_total.avg_area = 0.;
    stats_total.std_area = 0.;
    stats_total.avg_elev_diff = 0.;
    stats_total.std_elev_diff = 0.;
    stats_total.bifur_ratio = 0.;
    stats_total.std_bifur_ratio = 0.;
    stats_total.length_ratio = 0.;
    stats_total.std_length_ratio = 0.;
    stats_total.area_ratio = 0.;
    stats_total.std_area_ratio = 0.;
    stats_total.slope_ratio = 0.;
    stats_total.std_slope_ratio = 0.;
    stats_total.gradient_ratio = 0.;
    stats_total.std_gradient_ratio = 0.;
    stats_total.stream_frequency = 0.;
    stats_total.drainage_density = 0.;

    for (i = 0; i <= order_max; ++i) {
	ord_stats[i].order = i;
	ord_stats[i].stream_num = 0;
	ord_stats[i].sum_length = 0.;
	ord_stats[i].avg_length = 0.;
	ord_stats[i].std_length = 0.;
	ord_stats[i].avg_slope = 0.;
	ord_stats[i].std_slope = 0.;
	ord_stats[i].avg_gradient = 0.;
	ord_stats[i].std_gradient = 0.;
	ord_stats[i].sum_area = 0.;
	ord_stats[i].avg_area = 0.;
	ord_stats[i].std_area = 0.;
	ord_stats[i].avg_elev_diff = 0.;
	ord_stats[i].std_elev_diff = 0.;
	ord_stats[i].bifur_ratio = 0.;
	ord_stats[i].std_bifur_ratio = 0.;
	ord_stats[i].length_ratio = 0.;
	ord_stats[i].std_length_ratio = 0.;
	ord_stats[i].area_ratio = 0.;
	ord_stats[i].std_area_ratio = 0.;
	ord_stats[i].slope_ratio = 0.;
	ord_stats[i].std_slope_ratio = 0.;
	ord_stats[i].gradient_ratio = 0.;
	ord_stats[i].std_gradient_ratio = 0.;
	ord_stats[i].stream_frequency = 0.;
	ord_stats[i].drainage_density = 0.;
    }
    for (i = 0; i < outlets_num; ++i) {	/* recalculate and unify */
	stat_streams[i].elev_diff =
	    stat_streams[i].elev_spring - stat_streams[i].elev_outlet;
	tmp_num =
	    ((stat_streams[i].cell_num - 1) <
	     1) ? 1 : stat_streams[i].cell_num - 1;
	stat_streams[i].slope /= tmp_num;
	stat_streams[i].gradient =
	    stat_streams[i].elev_diff / stat_streams[i].length;

	/* calculation */
	ord_stats[stat_streams[i].order].stream_num++;
	ord_stats[stat_streams[i].order].sum_length += stat_streams[i].length;
	ord_stats[stat_streams[i].order].std_length +=
	    (stat_streams[i].length * stat_streams[i].length);
	ord_stats[stat_streams[i].order].avg_slope += stat_streams[i].slope;
	ord_stats[stat_streams[i].order].std_slope +=
	    (stat_streams[i].slope * stat_streams[i].slope);
	ord_stats[stat_streams[i].order].avg_gradient +=
	    stat_streams[i].gradient;
	ord_stats[stat_streams[i].order].std_gradient +=
	    (stat_streams[i].gradient * stat_streams[i].gradient);
	ord_stats[stat_streams[i].order].sum_area +=
	    stat_streams[i].basin_area;
	ord_stats[stat_streams[i].order].std_area +=
	    (stat_streams[i].basin_area * stat_streams[i].basin_area);
	ord_stats[stat_streams[i].order].avg_elev_diff +=
	    stat_streams[i].elev_diff;
	ord_stats[stat_streams[i].order].std_elev_diff +=
	    (stat_streams[i].elev_diff * stat_streams[i].elev_diff);
    }

    for (i = 1; i <= order_max; ++i) {

	num = ord_stats[i].stream_num;
	snum = (ord_stats[i].stream_num > 1) ?
	    ((float)ord_stats[i].stream_num) / (ord_stats[i].stream_num -
						1) : 0.;

	ord_stats[i].avg_length = ord_stats[i].sum_length / num;
	ord_stats[i].avg_slope = ord_stats[i].avg_slope / num;
	ord_stats[i].avg_gradient = ord_stats[i].avg_gradient / num;
	ord_stats[i].avg_area = ord_stats[i].sum_area / num;
	ord_stats[i].avg_elev_diff = ord_stats[i].avg_elev_diff / num;

	ord_stats[i].std_length = sqrt((ord_stats[i].std_length / num -
					(ord_stats[i].avg_length *
					 ord_stats[i].avg_length)) * snum);

	ord_stats[i].std_slope = sqrt((ord_stats[i].std_slope / num -
				       (ord_stats[i].avg_slope *
					ord_stats[i].avg_slope)) * snum);

	ord_stats[i].std_gradient = sqrt((ord_stats[i].std_gradient / num -
					  (ord_stats[i].avg_gradient *
					   ord_stats[i].avg_gradient)) *
					 snum);

	ord_stats[i].std_area = sqrt((ord_stats[i].std_area / num -
				      (ord_stats[i].avg_area *
				       ord_stats[i].avg_area)) * snum);

	ord_stats[i].std_elev_diff = sqrt((ord_stats[i].std_elev_diff / num -
					   (ord_stats[i].avg_elev_diff *
					    ord_stats[i].avg_elev_diff)) *
					  snum);

	ord_stats[i - 1].bifur_ratio =
	    ord_stats[i - 1].stream_num / (float)ord_stats[i].stream_num;

	ord_stats[i - 1].length_ratio =
	    (i == 1) ? 0 :
	    ord_stats[i].avg_length / ord_stats[i - 1].avg_length;

	ord_stats[i].area_ratio =
	    (i == 1) ? 0 : ord_stats[i].avg_area / ord_stats[i - 1].avg_area;

	ord_stats[i - 1].slope_ratio =
	    ord_stats[i - 1].avg_slope / ord_stats[i].avg_slope;

	ord_stats[i - 1].gradient_ratio =
	    ord_stats[i - 1].avg_gradient / ord_stats[i].avg_gradient;

	ord_stats[i].stream_frequency =
	    ord_stats[i].stream_num / ord_stats[i].sum_area;

	ord_stats[i].drainage_density =
	    ord_stats[i].sum_length / ord_stats[i].sum_area;

	/* total */
	stats_total.stream_num += ord_stats[i].stream_num;
	stats_total.sum_length += ord_stats[i].sum_length;

	stats_total.bifur_ratio += ord_stats[i - 1].bifur_ratio;
	stats_total.length_ratio += ord_stats[i - 1].length_ratio;
	stats_total.area_ratio += ord_stats[i - 1].area_ratio;
	stats_total.slope_ratio += ord_stats[i - 1].slope_ratio;
	stats_total.gradient_ratio += ord_stats[i - 1].gradient_ratio;

	stats_total.std_bifur_ratio +=
	    (ord_stats[i - 1].bifur_ratio * ord_stats[i - 1].bifur_ratio);
	stats_total.std_length_ratio +=
	    (ord_stats[i - 1].length_ratio * ord_stats[i - 1].length_ratio);
	stats_total.std_area_ratio +=
	    (ord_stats[i - 1].area_ratio * ord_stats[i - 1].area_ratio);
	stats_total.std_slope_ratio +=
	    (ord_stats[i - 1].slope_ratio * ord_stats[i - 1].slope_ratio);
	stats_total.std_gradient_ratio +=
	    (ord_stats[i - 1].gradient_ratio *
	     ord_stats[i - 1].gradient_ratio);

    }				/* end for ... orders */
    ord_num = order_max - 1;
    ord_snum = (ord_num == 1) ? 0 : (float)ord_num / (ord_num - 1);

    stats_total.order = order_max;
    stats_total.sum_area = total_basins;
    stats_total.sum_length = stats_total.sum_length;

    stats_total.bifur_ratio = stats_total.bifur_ratio / ord_num;
    stats_total.length_ratio = stats_total.length_ratio / ord_num;
    stats_total.area_ratio = stats_total.area_ratio / ord_num;
    stats_total.slope_ratio = stats_total.slope_ratio / ord_num;
    stats_total.gradient_ratio = stats_total.gradient_ratio / ord_num;


    stats_total.std_bifur_ratio =
	sqrt((stats_total.std_bifur_ratio / ord_num -
	      (stats_total.bifur_ratio * stats_total.bifur_ratio)) *
	     ord_snum);

    stats_total.std_length_ratio =
	sqrt((stats_total.std_length_ratio / ord_num -
	      (stats_total.length_ratio * stats_total.length_ratio)) *
	     ord_snum);

    stats_total.std_area_ratio = sqrt((stats_total.std_area_ratio / ord_num -
				       (stats_total.area_ratio *
					stats_total.area_ratio)) * ord_snum);

    stats_total.std_slope_ratio =
	sqrt((stats_total.std_slope_ratio / ord_num -
	      (stats_total.slope_ratio * stats_total.slope_ratio)) *
	     ord_snum);

    stats_total.std_gradient_ratio =
	sqrt((stats_total.std_gradient_ratio / ord_num -
	      (stats_total.gradient_ratio * stats_total.gradient_ratio)) *
	     ord_snum);

    stats_total.stream_frequency =
	stats_total.stream_num / stats_total.sum_area;
    stats_total.drainage_density =
	stats_total.sum_length / stats_total.sum_area;

    return 0;
}
