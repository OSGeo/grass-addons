/*
 * r.univar
 *
 *  Calculates univariate statistics from the non-null cells of a GRASS raster
 * map
 *
 *   Copyright (C) 2004-2006, 2012 by the GRASS Development Team
 *   Author(s): Hamish Bowman, University of Otago, New Zealand
 *              Extended stats: Martin Landa
 *              Zonal stats: Markus Metz
 *
 *      This program is free software under the GNU General Public
 *      License (>=v2). Read the file COPYING that comes with GRASS
 *      for details.
 *
 *   This program is a replacement for the r.univar shell script
 */

#include <assert.h>
#include <string.h>
#include "globals.h"

param_type param;
zone_type zone_info;

/* ************************************************************************* */
/* Set up the arguments we are expecting ********************************** */
/* ************************************************************************* */
void set_params()
{
    param.inputfile = G_define_standard_option(G_OPT_R_MAPS);

    param.zonefile = G_define_standard_option(G_OPT_R_MAP);
    param.zonefile->key = "zones";
    param.zonefile->required = NO;
    param.zonefile->description =
        _("Raster map used for zoning, must be of type CELL");

    param.output_file = G_define_standard_option(G_OPT_F_OUTPUT);
    param.output_file->required = NO;
    param.output_file->description =
        _("Name for output file (if omitted or \"-\" output to stdout)");
    param.output_file->guisection = _("Output settings");

    param.percentile = G_define_option();
    param.percentile->key = "percentile";
    param.percentile->type = TYPE_DOUBLE;
    param.percentile->required = NO;
    param.percentile->multiple = YES;
    param.percentile->options = "0-100";
    param.percentile->answer = "90";
    param.percentile->description =
        _("Percentile to calculate (requires extended statistics flag)");
    param.percentile->guisection = _("Extended");

    param.tolerance = G_define_option();
    param.tolerance->key = "tolerance";
    param.tolerance->type = TYPE_DOUBLE;
    param.tolerance->required = NO;
    param.tolerance->multiple = NO;
    param.tolerance->answer = "0.5";
    param.tolerance->description = _("Tolerance to consider float number equal "
                                     "to another when computing the mode");
    param.tolerance->guisection = _("Extended");

    param.separator = G_define_standard_option(G_OPT_F_SEP);
    param.separator->guisection = _("Formatting");

    param.shell_style = G_define_flag();
    param.shell_style->key = 'g';
    param.shell_style->description = _("Print the stats in shell script style");
    param.shell_style->guisection = _("Formatting");

    param.extended = G_define_flag();
    param.extended->key = 'e';
    param.extended->description = _("Calculate extended statistics");
    param.extended->guisection = _("Extended");

    param.table = G_define_flag();
    param.table->key = 't';
    param.table->description =
        _("Table output format instead of standard output format");
    param.table->guisection = _("Formatting");

    return;
}

static int open_raster(const char *infile);
static univar_stat *univar_stat_with_percentiles();
static void process_raster(univar_stat *stats, int fd, int fdz,
                           const struct Cell_head *region);
static void init_zones(int fdz, const struct Cell_head *region);

void init_zones(int fdz, const struct Cell_head *region)
{
    const unsigned int rows = region->rows;
    const unsigned int cols = region->cols;
    unsigned int row;
    unsigned int col;
    int zone = 0, n_zones = zone_info.n_zones;

    CELL *zoneraster_row;
    CELL *zptr;

    zone_info.n_alloc = 0;
    zone_info.len = (int *)G_calloc(zone_info.n_zones, sizeof(int));

    zoneraster_row = Rast_allocate_c_buf();
    G_message("Reading the zones map.");
    for (row = 0; row < rows; row++) {
        Rast_get_c_row(fdz, zoneraster_row, row);
        zptr = zoneraster_row;

        for (col = 0; col < cols; col++) {
            if (Rast_is_c_null_value(zptr)) {
                zptr++;
                continue;
            }
            zone = *zptr - zone_info.min;
            zone_info.len[zone] += 1;
            zptr++;
        }
        G_percent(row, rows, 2);
    }
    /* find the max lenght to understand how much memory nust be allocated */
    for (zone = 0; zone < n_zones; zone++) {
        if (zone_info.len[zone] > zone_info.n_alloc)
            zone_info.n_alloc = zone_info.len[zone];
    }
    return;
}

/* *************************************************************** */
/* **** the main functions for r.univar ************************** */
/* *************************************************************** */
int main(int argc, char *argv[])
{
    int rasters;

    struct Cell_head region;
    struct GModule *module;
    univar_stat *stats;
    char **p, *z;
    int fd, fdz, cell_type, min, max;
    struct Range zone_range;
    const char *mapset, *name;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("univariate statistics"));
    G_add_keyword(_("zonal statistics"));
    module->description = _("Calculates univariate statistics from the "
                            "non-null cells of a raster map.");

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

    G_get_window(&region);

    /* table field separator */
    zone_info.sep = param.separator->answer;
    if (strcmp(zone_info.sep, "\\t") == 0)
        zone_info.sep = "\t";
    if (strcmp(zone_info.sep, "tab") == 0)
        zone_info.sep = "\t";
    if (strcmp(zone_info.sep, "space") == 0)
        zone_info.sep = " ";
    if (strcmp(zone_info.sep, "comma") == 0)
        zone_info.sep = ",";

    zone_info.min = 0.0 / 0.0; /* set to nan as default */
    zone_info.max = 0.0 / 0.0; /* set to nan as default */
    zone_info.n_zones = 0;

    fdz = -1;

    /* open zoning raster */
    z = param.zonefile->answer;
    mapset = G_find_raster2(z, "");

    fdz = open_raster(z);

    cell_type = Rast_get_map_type(fdz);
    if (cell_type != CELL_TYPE)
        G_fatal_error("Zoning raster must be of type CELL");

    if (Rast_read_range(z, mapset, &zone_range) == -1)
        G_fatal_error("Can not read range for zoning raster");
    Rast_get_range_min_max(&zone_range, &min, &max);
    if (Rast_read_cats(z, mapset, &(zone_info.cats)))
        G_warning("no category support for zoning raster");

    zone_info.min = min;
    zone_info.max = max;
    zone_info.n_zones = max - min + 1;

    init_zones(fdz, &region);

    sscanf(param.tolerance->answers[0], "%lf", &param.tol);

    /* count the input rasters given */
    for (p = (char **)param.inputfile->answers, rasters = 0; *p; p++, rasters++)
        ;

    /* process all input rasters */
    int map_type = param.extended->answer ? -2 : -1;

    stats = ((map_type == -1) ? create_univar_stat_struct(-1, 0) : 0);

    for (p = param.inputfile->answers; *p; p++) {
        fd = open_raster(*p);

        if (map_type != -1) {
            /* NB: map_type must match when doing extended stats */
            int this_type = Rast_get_map_type(fd);

            assert(this_type > -1);
            if (map_type < -1) {
                /* extended stats */
                assert(stats == 0);
                map_type = this_type;
                stats = univar_stat_with_percentiles(map_type);
            }
            else if (this_type != map_type) {
                G_fatal_error(_("Raster <%s> type mismatch"), *p);
            }
        }
        process_raster(stats, fd, fdz, &region);

        /* close input raster */
        Rast_close(fd);
    }

    /* close zoning raster */
    if (z)
        Rast_close(fdz);

    /* create the output */
    if (param.table->answer)
        print_stats_table(stats);
    /* else
        print_stats(stats); */

    /* release memory */
    free_univar_stat_struct(stats);

    exit(EXIT_SUCCESS);
}

static int open_raster(const char *infile)
{
    const char *mapset;
    int fd;

    mapset = G_find_raster2(infile, "");
    if (mapset == NULL) {
        G_fatal_error(_("Raster map <%s> not found"), infile);
    }

    fd = Rast_open_old(infile, mapset);

    return fd;
}

static univar_stat *univar_stat_with_percentiles()
{
    univar_stat *stats;
    unsigned int z, p, n_perc = 0;
    unsigned int n_zones = zone_info.n_zones;

    while (param.percentile->answers[n_perc])
        n_perc++;

    /* allocate memory */
    G_debug(3, "Allocate memory for percentile, n_perc=%d", n_perc);
    param.n_perc = n_perc;
    param.index_perc = (int *)G_calloc(n_perc + 1, sizeof(int));
    param.quant_perc = (double *)G_calloc(n_perc + 1, sizeof(double));
    param.perc = (double *)G_calloc(n_perc + 1, sizeof(double));
    for (p = 0; p < n_perc; p++) {
        G_debug(3, "Percentile: %s", param.percentile->answers[p]);
        sscanf(param.percentile->answers[p], "%lf", &(param.perc[p]));
    }

    stats = create_univar_stat_struct();
    for (z = 0; z < n_zones; z++) {
        stats[z].size = zone_info.len[z];
        stats[z].zone = z + zone_info.min;
        stats[z].cat = Rast_get_c_cat(&stats[z].zone, &(zone_info.cats));
        stats[z].perc = (double *)G_calloc(n_perc, sizeof(double));
    }
    return stats;
}

static void process_raster(univar_stat *stats, int fd, int fdz,
                           const struct Cell_head *region)
{
    /* use G_window_rows(), G_window_cols() here? */
    const unsigned int rows = region->rows;
    const unsigned int cols = region->cols;

    const RASTER_MAP_TYPE map_type = Rast_get_map_type(fd);
    const size_t value_sz = Rast_cell_size(map_type);
    unsigned int row;
    void *raster_row;
    CELL *zoneraster_row;

    raster_row = Rast_allocate_buf(map_type);
    zoneraster_row = Rast_allocate_c_buf();

    for (row = 0; row < rows; row++) {
        void *ptr;
        CELL *zptr;
        unsigned int col;

        Rast_get_row(fd, raster_row, row, map_type);
        Rast_get_c_row(fdz, zoneraster_row, row);
        zptr = zoneraster_row;

        ptr = raster_row;

        for (col = 0; col < cols; col++) {
            double val;
            int zone = 0;

            if (Rast_is_c_null_value(zptr)) {
                ptr = G_incr_void_ptr(ptr, value_sz);
                zptr++;
                continue;
            }
            zone = *zptr - zone_info.min;
            /* count all including NULL cells in input map */
            /*stats[zone].size++;
             G _debug(3, "Col: %u, zone: %d", col, zone); */

            /* can't do stats with NULL cells in input map */
            if (Rast_is_null_value(ptr, map_type)) {
                ptr = G_incr_void_ptr(ptr, value_sz);
                zptr++;
                continue;
            }

            if (param.extended->answer && stats[zone].array == NULL) {
                stats[zone].n_alloc = zone_info.len[zone] + 1;
                stats[zone].array =
                    (DCELL *)G_calloc(stats[zone].n_alloc, sizeof(DCELL));
            }

            val = ((map_type == DCELL_TYPE)   ? *((DCELL *)ptr)
                   : (map_type == FCELL_TYPE) ? *((FCELL *)ptr)
                                              : *((CELL *)ptr));

            compute_stats(&stats[zone], val, zone_info.len[zone]);

            ptr = G_incr_void_ptr(ptr, value_sz);
            zptr++;
        }
        G_percent(row, rows, 2);
    }
    G_percent(rows, rows, 2);
    return;
}
