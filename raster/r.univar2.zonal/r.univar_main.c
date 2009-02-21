/*
 * r.univar
 *
 *  Calculates univariate statistics from the non-null cells of a GRASS raster map
 *
 *   Copyright (C) 2004-2006 by the GRASS Development Team
 *   Author(s): Hamish Bowman, University of Otago, New Zealand
 *              Extended stats: Martin Landa
 *
 *      This program is free software under the GNU General Public
 *      License (>=v2). Read the file COPYING that comes with GRASS
 *      for details.
 *
 *   This program is a replacement for the r.univar shell script
 */

#include <assert.h>
#include <string.h>
#define MAIN
#include "globals.h"

/* local proto */
void set_params();

/* ************************************************************************* */
/* Set up the arguments we are expecting ********************************** */
/* ************************************************************************* */
void set_params()
{
    param.inputfile = G_define_standard_option(G_OPT_R_INPUT);

    param.zonefile = G_define_standard_option(G_OPT_R_MAP);
    param.zonefile->key = "zones";
    param.zonefile->required = YES;
    param.zonefile->description =
	_("Raster map used for zoning, must be of type CELL");

    param.output_file = G_define_standard_option(G_OPT_F_OUTPUT);
    param.output_file->required = YES;
    param.output_file->description =
	_("Name for output file (if omitted or \"-\" output to stdout)");

    param.percentile = G_define_option();
    param.percentile->key = "percentile";
    param.percentile->type = TYPE_INTEGER;
    param.percentile->required = NO;
    param.percentile->multiple = YES;
    param.percentile->options = "0-100";
    param.percentile->answer = "90";
    param.percentile->description =
	_("Percentile to calculate (requires extended statistics flag)");

    param.shell_style = G_define_flag();
    param.shell_style->key = 'g';
    param.shell_style->description =
	_("Print the stats in shell script style");

    param.extended = G_define_flag();
    param.extended->key = 'e';
    param.extended->description = _("Calculate extended statistics");

    param.table = G_define_flag();
    param.table->key = 't';
    param.table->description = _("Table output format instead of r.univar like output format");

    return;
}

static int open_raster(const char *infile);
static univar_stat *univar_stat_with_percentiles(int map_type, int size);
static void process_raster(univar_stat * stats, int fd, int fdz,
			   const struct Cell_head *region);

/* *************************************************************** */
/* **** the main functions for r.univar ************************** */
/* *************************************************************** */
int main(int argc, char *argv[])
{
    unsigned int rows, cols;	/*  totals  */
    /* int rasters; */

    struct Cell_head region;
    struct GModule *module;
    univar_stat *stats;
    char *p, *z;
    int fd, fdz, cell_type, min, max;
    struct Range zone_range;
    char *mapset, *name;


    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster, statistics");
    module->description =
	_("Calculates univariate statistics from the non-null cells of a raster map.");

    /* Define the different options */
    set_params();

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    name = param.output_file->answer;
    if (name != NULL && strcmp(name, "-") != 0) {
	if (NULL == freopen(name, "w", stdout)) {
	    G_fatal_error(_("Unable to open file <%s> for writing"), name);
	}
    }

    /* TODO: make it an option */
    zone_info.sep = ";";

    G_get_window(&region);
    rows = region.rows;
    cols = region.cols;

    zone_info.min = 0.0 / 0.0;	/*set to nan as default */
    zone_info.max = 0.0 / 0.0;	/*set to nan as default */
    zone_info.n_zones = 0;

    /* open zoning raster */
    z = param.zonefile->answer;
    mapset = G_find_cell2(z, "");

    fdz = open_raster(z);
    
    cell_type = G_get_raster_map_type(fdz);
    if (cell_type != CELL_TYPE)
	G_fatal_error("Zoning raster must be of type CELL");

    if (G_read_range(z, mapset, &zone_range) == -1)
	G_fatal_error("Can not read range for zoning raster");
    if (G_get_range_min_max(&zone_range, &min, &max))
	G_fatal_error("Can not read range for zoning raster");
    if (G_read_raster_cats(z, mapset, &(zone_info.cats)))
	G_warning("no category support for zoning raster");

    zone_info.min = min;
    zone_info.max = max;
    zone_info.n_zones = max - min + 1;

    /* process input raster */
    size_t cells = cols * rows;
    int map_type = param.extended->answer ? -2 : -1;

    stats = ((map_type == -1)
	     ? create_univar_stat_struct(-1, cells, 0)
	     : 0);

    p = param.inputfile->answer;
    fd = open_raster(p);

    if (map_type != -1) {
	/* NB: map_type must match when doing extended stats */
	int this_type = G_get_raster_map_type(fd);

	assert(this_type > -1);
	if (map_type < -1) {
	    assert(stats == 0);
	    map_type = this_type;
	    stats = univar_stat_with_percentiles(map_type, cells);
	}
	else if (this_type != map_type) {
	    G_fatal_error(_("Raster <%s> type mismatch"), p);
	}
    }

    process_raster(stats, fd, fdz, &region);

    /* closing raster maps */
    G_close_cell(fd);
    G_close_cell(fdz);

    /* create the output */
    if (param.table->answer)
	print_stats2(stats);
    else
	print_stats(stats);
	
    /* release memory */
    free_univar_stat_struct(stats);

    exit(EXIT_SUCCESS);
}

static int open_raster(const char *infile)
{
    char *mapset;
    int fd;

    mapset = G_find_cell2(infile, "");
    if (mapset == NULL) {
	G_fatal_error(_("Raster map <%s> not found"), infile);
    }

    fd = G_open_cell_old(infile, mapset);
    if (fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), infile);

    /* . */
    return fd;
}

static univar_stat *univar_stat_with_percentiles(int map_type, int size)
{
    univar_stat *stats;
    int i, j;

    i = 0;
    while (param.percentile->answers[i])
	i++;
    stats = create_univar_stat_struct(map_type, size, i);
    for (i = 0; i < zone_info.n_zones; i++) {
	for (j = 0; j < stats[i].n_perc; j++) {
	    sscanf(param.percentile->answers[j], "%i", &stats[i].perc[j]);
	}
    }

    /* . */
    return stats;
}

static void
process_raster(univar_stat * stats, int fd, int fdz, const struct Cell_head *region)
{
    /* use G_window_rows(), G_window_cols() here? */
    const int rows = region->rows;
    const int cols = region->cols;
    const int n_zones = zone_info.n_zones;
    int *first, i;

    const RASTER_MAP_TYPE map_type = G_get_raster_map_type(fd);
    const size_t value_sz = G_raster_size(map_type);
    unsigned int row;
    void *raster_row;
    CELL *zoneraster_row;

    switch (map_type) {
	case CELL_TYPE:
	    for (i = 0; i < n_zones; i++) {
		stats[i].nextp
		= ((!param.extended->answer) ? 0 : (void *)stats[i].cell_array);
	    }
	    break;

	case FCELL_TYPE:
	    for (i = 0; i < n_zones; i++) {
		stats[i].nextp
		= ((!param.extended->answer) ? 0 : (void *)stats[i].fcell_array);
	    }
	    break;

	case DCELL_TYPE:
	    for (i = 0; i < n_zones; i++) {
		stats[i].nextp
		= ((!param.extended->answer) ? 0 : (void *)stats[i].dcell_array);
	    }
	    break;

	default:
	    G_fatal_error("input raster has unknown type");
	    break;
    }

    first = (int *) G_malloc((n_zones - 1) * sizeof(int));
    {
	int i;
	for (i = 0; i < n_zones; i++)
	    first[i] = (stats[i].n < 1);
    }


    raster_row = G_calloc(cols, value_sz);
    zoneraster_row = G_allocate_c_raster_buf();

    for (row = 0; row < rows; row++) {
	void *ptr;
	CELL *zptr;
	unsigned int col;
	int zone;

	if (G_get_raster_row(fd, raster_row, row, map_type) < 0)
	    G_fatal_error(_("Reading row %d"), row);
	if (G_get_c_raster_row(fdz, zoneraster_row, row) < 0)
	    G_fatal_error(_("Reading row %d"), row);

	ptr = raster_row;
	zptr = zoneraster_row;

	for (col = 0; col < cols; col++) {

	    if (G_is_c_null_value(zptr)) {
		ptr = G_incr_void_ptr(ptr, value_sz);
		zptr++;
		continue;
	    }

	    /* also count NULL cell in input map */
	    zone = *zptr - zone_info.min;
	    stats[zone].size++;
	    
	    if (G_is_null_value(ptr, map_type)) {
		ptr = G_incr_void_ptr(ptr, value_sz);
		zptr++;
		continue;
	    }

	    if (stats[zone].nextp) {
		/* put the value into stats->XXXcell_array */
		memcpy(stats[zone].nextp, ptr, value_sz);
		stats[zone].nextp = G_incr_void_ptr(stats[zone].nextp, value_sz);
	    }

	    {
		double val = ((map_type == DCELL_TYPE) ? *((DCELL *) ptr)
			      : (map_type == FCELL_TYPE) ? *((FCELL *) ptr)
			      : *((CELL *) ptr));

		stats[zone].sum += val;
		stats[zone].sumsq += val * val;
		stats[zone].sum_abs += fabs(val);

		if (first[zone]) {
		    stats[zone].max = val;
		    stats[zone].min = val;
		    first[zone] = FALSE;
		}
		else {
		    if (val > stats[zone].max)
			stats[zone].max = val;
		    if (val < stats[zone].min)
			stats[zone].min = val;
		}
	    }

	    ptr = G_incr_void_ptr(ptr, value_sz);
	    zptr++;
	    stats[zone].n++;
	}
	G_percent(row, rows, 2);
    }
    G_percent(rows, rows, 2);	/* finish it off */

}
