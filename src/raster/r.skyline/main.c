/***********************************************************************/
/*
   r.skyline

   *****

   COPYRIGHT:    (C) 2020 by UCL, and the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the COPYING file that comes with GRASS
   for details.

   *****

   REVISIONS

   Written by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   This revision 9/12/2020

   Draws on the 26/07/20017 revision for GRASS 7.x of
   Mark Lake's 15/07/2002 r.horizon for GRASS 5.x (this is not the
   r.horizon that is currently part of the GRASS 7.x main release).

   *****

   AUTHOR

   Mark Lake <mark.lake@ucl.ac.uk>

   University College London
   Institute of Archaeology
   31-34 Gordon Square
   London.  WC1H 0PY
   United Kingdom

   *****

   ACKNOWLEDGEMENTS

   Mergesort in sort.c uses algorithm from R. Sedgewick, 1990,
   'Algorithms in C', Reading, MA: Addison Wesley

   Skyline index emerged out of conversations with Barney Harris
   <barnabas.harris.14@ucl.ac.uk>

   *****

   PURPOSE

   1) Given a viewshed map produced by r.viewshed or r.los, finds the
   cells that fall on the true horizon (within some specified maximum
   viewing distance, which may be equal or less than that used to
   create the viewshed).  Identifies cells that fall on the edge of the
   viewshed because they are on the edge of the region or fall at the
   maximum viewing distance.  Can also output a CSV file listing
   properties of horizon cells, sorted by azimuth.  This is useful for
   drawing a profile.

   2) Given a viewshed map produced by r.viewshed or r.los, which
   records inclination values, can optionally output the skyline index
   for the viewpoint as seen from cells in the viewshed.  This
   requires, that the observer and target offsets have been set
   appropriately so as to model the view towards the 'viewpoint' rather
   than the view from it (i.e. the viewpoint and target offsets should
   have been swapped).  r.los does not currently support this
   because it lacks the option of specifying a target offset.

   *****

   OPTIONS

   Flags:
   --overwrite Allow output files to overwrite existing files
   --help Print usage summary
   --verbose Verbose module output
   --quiet Quiet module output
   --ui Force launching GUI dialog

   Parameters:
   viewshed=name [required] Raster map containing first viewshed map
   viewshed_2=name [required] Raster map containing second viewshed map (for
   skyline index) dem=string Raster map containing elevation data
   hoz_azimuth=string Raster map name for storing far horizon azimuth
   hoz_inclination=string Raster map name for storing far horizon inclination
   hoz_type=string Raster map name for storing horizon type
   edges=string Raster map name for storing viewshed edges
   skyline_index=string Raster map name for storing viewshed skyline index
   profile=string Output text file for profile information
   coordinate=x,y [required] Coordinate identifying the viewing location
   max_dist=float Max viewing distance in meters
   Options: 0.0-100000000.0
   Default: 0


   *****

   NOTES

   *****

   TO DO

   Produce categorised version of skyline index (below, on, above, unknown)?
   Set up sensible colourtable for skyline index
   Allow viewpoint to be specified as point in a vector map


 */

/***********************************************************************/

#define MAIN

#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "global_vars.h"
#include "file.h"
#include "find_edges.h"
#include "find_horizon.h"
#include "raster_file.h"
#include "skyline.h"
#include "sort.h"

int main(int argc, char *argv[])
{
    FILE *profile_str = NULL;
    char profile_name[256];
    int viewshed_fd = -1, dem_fd = -1;
    int hoz_az_fd = -1, hoz_inc_fd = -1, hoz_type_fd = -1;
    int edges_fd = -1, skyline_fd = -1;
    char view_mapset[GMAPSET_MAX], dem_mapset[GMAPSET_MAX];
    char current_mapset[GMAPSET_MAX];
    RASTER_MAP_TYPE viewshed_map_cell_type;
    RASTER_MAP_TYPE dem_map_cell_type;
    RASTER_MAP_TYPE hoz_inc_map_cell_type;
    RASTER_MAP_TYPE hoz_az_map_cell_type;
    RASTER_MAP_TYPE hoz_type_map_cell_type;
    RASTER_MAP_TYPE edges_map_cell_type;
    RASTER_MAP_TYPE skyline_map_cell_type;
    char message[GMAPSET_MAX + 64];
    int clipped;
    struct Categories cats;
    struct History history;

    /* struct Colors colr; */
    double east, north;
    double e_coord, w_coord, n_coord, s_coord;
    double inclination, skyline_index, min_skyline_index, max_skyline_index;
    void *edges_buf, *viewshed_buf, *hoz_type_buf;
    void *hoz_az_buf, *hoz_inc_buf, *dem_buf;
    int nrows, ncols, row, col;
    int side_ew_cells, side_ns_cells;
    int e_box1, w_box1, n_box1, s_box1;
    struct node edge_tail; /* Dummy tail node common to all lists */
    struct node edge_head, *edge_cur;
    struct node *quad1_hoz_head, *quad2_hoz_head, *quad3_hoz_head,
        *quad4_hoz_head;
    struct GModule *module;
    struct Option *view, *view2, *dem, *hoz_az, *hoz_inc, *hoz_type;
    struct Option *edges, *skyline, *profile, *opt_viewpt, *opt_max_dist;
    int overwrite;

    /***********************************************************************
       Options

    ***********************************************************************/

    /* Initialize the GIS calls and sort out error handling */

    G_gisinit(argv[0]);
    G_sleep_on_error(0);

    /* Declare module info. */

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("viewshed"));
    G_add_keyword(_("horizon"));
    G_add_keyword(_("skyline"));
    module->description = _("Compute the skyline index and / or find the "
                            "horizon cells in a raster viewshed.");

    /* Define the options */

    view = G_define_option();
    view->key = "viewshed";
    view->type = TYPE_STRING;
    view->required = YES;
    view->gisprompt = "old,cell,raster";
    view->key_desc = "name";
    view->description = _("Raster map containing first viewshed map");

    view2 = G_define_option();
    view2->key = "viewshed_2";
    view2->type = TYPE_STRING;
    view2->required = NO;
    view2->gisprompt = "old,cell,raster";
    view2->key_desc = "name";
    view2->description =
        _("Raster map containing second viewshed map (for skyline index)");

    dem = G_define_option();
    dem->key = "dem";
    dem->type = TYPE_STRING;
    dem->required = NO;
    dem->description = _("Raster map containing elevation data");
    dem->gisprompt = "old,cell,raster";

    hoz_az = G_define_option();
    hoz_az->key = "hoz_azimuth";
    hoz_az->type = TYPE_STRING;
    hoz_az->required = NO;
    hoz_az->gisprompt = "new,cell,raster";
    hoz_az->description = _("Raster map name for storing far horizon azimuth");

    hoz_inc = G_define_option();
    hoz_inc->key = "hoz_inclination";
    hoz_inc->type = TYPE_STRING;
    hoz_inc->required = NO;
    hoz_inc->gisprompt = "new,cell,raster";
    hoz_inc->description =
        _("Raster map name for storing far horizon inclination");

    hoz_type = G_define_option();
    hoz_type->key = "hoz_type";
    hoz_type->type = TYPE_STRING;
    hoz_type->required = NO;
    hoz_type->gisprompt = "new,cell,raster";
    hoz_type->description = _("Raster map name for storing horizon type");

    edges = G_define_option();
    edges->key = "edges";
    edges->type = TYPE_STRING;
    edges->required = NO;
    edges->gisprompt = "new,cell,raster";
    edges->description = _("Raster map name for storing viewshed edges");

    skyline = G_define_option();
    skyline->key = "skyline_index";
    skyline->type = TYPE_STRING;
    skyline->required = NO;
    skyline->gisprompt = "new,cell,raster";
    skyline->description =
        _("Raster map name for storing viewshed skyline index");

    profile = G_define_option();
    profile->key = "profile";
    profile->type = TYPE_STRING;
    profile->required = NO;
    profile->description = _("Output text file for profile information");

    opt_viewpt = G_define_option();
    opt_viewpt->key = "coordinate";
    opt_viewpt->type = TYPE_STRING;
    opt_viewpt->required = YES;
    opt_viewpt->key_desc = "x,y";
    opt_viewpt->description = _("Coordinate identifying the viewing location");

    opt_max_dist = G_define_option();
    opt_max_dist->key = "max_dist";
    opt_max_dist->type = TYPE_DOUBLE;
    opt_max_dist->required = NO;
    opt_max_dist->answer = "0";
    opt_max_dist->options = "0.0-100000000.0";
    opt_max_dist->description = _("Max viewing distance in meters");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* Make option choices globally available and check compatability of
       output maps with input viewshed */

    if (hoz_az->answer != NULL)
        do_hoz_az = 1;
    else
        do_hoz_az = 0;

    if (hoz_type->answer != NULL)
        do_hoz_type = 1;
    else
        do_hoz_type = 0;

    if (edges->answer != NULL)
        do_edges = 1;
    else
        do_edges = 0;

    if (profile->answer != NULL)
        do_profile = 1;
    else
        do_profile = 0;

    if (hoz_inc->answer != NULL)
        do_hoz_inc = 1;
    else
        do_hoz_inc = 0;

    if (skyline->answer != NULL)
        do_skyline = 1;
    else
        do_skyline = 0;

    if ((do_hoz_az + do_hoz_inc + do_hoz_type + do_edges + do_skyline +
         do_profile) < 1) {
        G_usage();
        G_fatal_error(_("You haven't requested any output!"));
    }

    /* Make other parameters globally available */

    G_scan_easting(opt_viewpt->answers[0], &east, G_projection());
    G_scan_northing(opt_viewpt->answers[1], &north, G_projection());
    sscanf(opt_max_dist->answer, "%lf", &max_dist);
    overwrite = module->overwrite;

    /* Specify output raster map cell types.  Input map cell types will
       be retrieved by Open_raster_infile */

    hoz_inc_map_cell_type = FCELL_TYPE;
    hoz_az_map_cell_type = FCELL_TYPE;
    hoz_type_map_cell_type = CELL_TYPE;
    edges_map_cell_type = CELL_TYPE;
    skyline_map_cell_type = FCELL_TYPE;

    /* Specify buffer cell types */
    viewshed_buf_cell_type = FCELL_TYPE;
    dem_buf_cell_type = FCELL_TYPE;
    hoz_inc_buf_cell_type = hoz_inc_map_cell_type;
    hoz_az_buf_cell_type = hoz_az_map_cell_type;
    hoz_type_buf_cell_type = hoz_type_map_cell_type;
    edges_buf_cell_type = edges_map_cell_type;
    skyline_buf_cell_type = skyline_map_cell_type;

    /***********************************************************************
       Check region and find bounding box for analysis

    ***********************************************************************/

    /* Get current region */
    G_get_window(&window);
    nrows = Rast_window_rows();
    n_row = 0; /* Origin is top left */
    s_row = nrows - 1;
    ncols = Rast_window_cols();
    w_col = 0;
    e_col = ncols - 1;

    /* Check for appropriate projection.  Code currently does not
       deal Lat/Long  */

    if ((G_projection() == PROJECTION_LL))
        G_fatal_error(
            _("Lat/Long support is not (yet) implemented for this module."));

    /* Check for integer resolution.  Algorithm is not robust in
       cases where resolution is non-integer */

    if ((floor(window.ew_res) != window.ew_res) ||
        (floor(window.ns_res) != window.ns_res)) {
        G_fatal_error(_("please use region with integer resolution "));
    }

    /* Check that viewpoint falls within current region */

    if (east < window.west || east > window.east || north > window.north ||
        north < window.south) {
        G_fatal_error(
            _("Specified observer location outside database region "));
    }

    /* Calculate coordinates of bounding box for analysis */

    e_coord = east + max_dist;
    w_coord = east - max_dist;
    n_coord = north + max_dist;
    s_coord = north - max_dist;

    /* Correct coordinates if max distance >= current region.  Detect =
       because horizon cells that fall on edge of region will not be
       detected as such, so we should warn user */

    clipped = 0;
    if (w_coord <= window.west) {
        clipped = 1;
        w_coord = window.west;
    }
    if (e_coord >= window.east) {
        clipped = 1;
        e_coord = window.east;
    }
    if (s_coord <= window.south) {
        clipped = 1;
        s_coord = window.south;
    }
    if (n_coord >= window.north) {
        clipped = 1;
        n_coord = window.north;
    }

    /* Convert viewpoint coordinates to rows and columns */

    viewpt_col = (int)Rast_easting_to_col(east, &window);
    viewpt_row = (int)Rast_northing_to_row(north, &window);

    G_debug(2, _("\nviewpt_col=%d viewpt_row=%d"), viewpt_col, viewpt_row);

    /* Warn if max distance exceeds current region */

    if (clipped) {
        G_warning(_("Maximum viewing distance exceeds current region.\n    It "
                    "is recommended that you use the option to produce a\n    "
                    "'horizon type' map. "));
    }

    /***********************************************************************
      Open first viewshed map and set up lists for keeping track of edges

    ***********************************************************************/

    viewshed_fd = Open_raster_infile(view->answer, view_mapset, "",
                                     &viewshed_map_cell_type, message);
    if (viewshed_fd < 0)
        G_fatal_error("%s", message);

    G_message(_("\nReading viewshed from <%s@%s> \n"), view->answer,
              view_mapset);

    viewshed_buf = Allocate_raster_buf_with_null(viewshed_buf_cell_type);
    Read_raster_infile(viewshed_buf, viewshed_fd, viewshed_buf_cell_type,
                       viewshed_map_cell_type);
    Close_raster_file(viewshed_fd);

#ifdef DEBUG
    fprintf(stdout, "\nIn function main: contents of 'viewshed_buf'\n");
    Print_raster_buf_row_col(viewshed_buf, viewshed_buf_cell_type, stderr);
#endif

    /***********************************************************************
      Find viewshed edges and, if requested, write them

    ***********************************************************************/

    G_message(_("Finding edges of viewshed\n"));

    List_init(&edge_head, &edge_tail);
    find_edges(nrows, ncols, viewshed_buf, &edge_head);

    /* Random access to viewshed no longer needed so free memory */

    G_free(viewshed_buf);

    /* Nothing else to do if no edges detected */

    if (edge_head.next_smallest == &edge_tail)
        G_fatal_error(_("No edges detected "));

    /* Write raster map of edges if requested */

    if (do_edges) {
        /* Open raster map and allocate memory */

        edges_fd = Open_raster_outfile(edges->answer, current_mapset,
                                       edges_map_cell_type, overwrite, message);
        if (edges_fd < 0)
            G_warning("%s", message);
        else {
            edges_buf = Allocate_raster_buf_with_null(edges_buf_cell_type);

            /* Write edges to output buffer */

            edge_cur = List_next_smallest(&edge_head);
            while (edge_cur != edge_cur->next_smallest) {
                List_write_type_to_buf(edges_buf, edge_cur,
                                       edges_buf_cell_type);
                edge_cur = List_next_smallest(edge_cur);
            }

            /* Write and close output file */

            Write_raster_outfile(edges_buf, edges_fd, edges_buf_cell_type,
                                 edges_map_cell_type);
            Close_raster_file(edges_fd);
            G_free(edges_buf);
        }
    }

    /***********************************************************************
      Find horizon and write horizon azimuth map

    ***********************************************************************/

    if (do_hoz_az | do_hoz_inc | do_profile | do_skyline) {
        G_message(_("Finding horizon\n"));

        if (!Find_horizon(&edge_head, &edge_tail))
            G_fatal_error(_("No edges detected ")); /* Should never get here */

        if (do_hoz_az) {
            /* Open raster map and allocate memory */

            hoz_az_fd =
                Open_raster_outfile(hoz_az->answer, current_mapset,
                                    hoz_az_map_cell_type, overwrite, message);
            if (hoz_az_fd < 0)
                G_warning("%s", message);
            else {
                hoz_az_buf =
                    Allocate_raster_buf_with_null(hoz_az_buf_cell_type);

                /* Write horizon azimuths to output buffer */

                edge_cur = List_next_horizon(&edge_head);
                while (edge_cur != edge_cur->next_horizon) {
                    List_write_azimuth_to_buf(hoz_az_buf, edge_cur,
                                              hoz_az_buf_cell_type);
                    edge_cur = List_next_horizon(edge_cur);
                }

                /* Write and close output horizon file */

                Write_raster_outfile_with_rounding(hoz_az_buf, hoz_az_fd,
                                                   hoz_az_buf_cell_type,
                                                   hoz_az_map_cell_type);
                Close_raster_file(hoz_az_fd);
                G_free(hoz_az_buf);
            }
        }

        /***********************************************************************
          Write horizon inclination map if requested

        ***********************************************************************/

        if (do_hoz_inc) {
            /* Open raster map and allocate memory */

            hoz_inc_fd =
                Open_raster_outfile(hoz_inc->answer, current_mapset,
                                    hoz_inc_map_cell_type, overwrite, message);
            if (hoz_inc_fd < 0)
                G_warning("%s", message);
            else {
                hoz_inc_buf =
                    Allocate_raster_buf_with_null(hoz_inc_buf_cell_type);

                /* Write horizon inclinations to output buffer */

                edge_cur = List_next_horizon(&edge_head);
                while (edge_cur != edge_cur->next_horizon) {
                    List_write_inclination_to_buf(hoz_inc_buf, edge_cur,
                                                  hoz_inc_buf_cell_type);
                    edge_cur = List_next_horizon(edge_cur);
                }

                /* Write and close output horizon file */

                Write_raster_outfile(hoz_inc_buf, hoz_inc_fd,
                                     hoz_inc_buf_cell_type,
                                     hoz_inc_map_cell_type);
                Close_raster_file(hoz_inc_fd);
                G_free(hoz_inc_buf);
            }
        }

        /***********************************************************************
           Write horizon type map if requested

        ***********************************************************************/

        if (do_hoz_type) {
            /* Open raster map and allocate memory */

            hoz_type_fd =
                Open_raster_outfile(hoz_type->answer, current_mapset,
                                    hoz_type_map_cell_type, overwrite, message);
            if (hoz_type_fd < 0)
                G_warning("%s", message);
            else {
                hoz_type_buf =
                    Allocate_raster_buf_with_null(hoz_type_buf_cell_type);

                /* Write horizon type to output file */

                edge_cur = List_next_horizon(&edge_head);
                while (edge_cur != edge_cur->next_horizon) {
                    List_write_type_to_buf(hoz_type_buf, edge_cur,
                                           hoz_type_buf_cell_type);
                    edge_cur = List_next_horizon(edge_cur);
                }

                /* Write and close output file */

                Write_raster_outfile(hoz_type_buf, hoz_type_fd,
                                     hoz_type_buf_cell_type,
                                     hoz_type_map_cell_type);
                Close_raster_file(hoz_type_fd);
                G_free(hoz_type_buf);
            }
        }

        /***********************************************************************
                 Compute and write skyline index if requested

                   If only one viewshed map has been specified we use this, but
        print a warning.  If a second viewshed map has been specified we assume
                   that this was created using observer and target offsets such
        that the inclination values are those from each cell in the viewshed
                   looking back towards the 'viewpoint'.



        ***********************************************************************/

        if (do_skyline) {
            /* Open, read inclination values and close viewshed map */

            if (view2->answer != NULL)
                viewshed_fd =
                    Open_raster_infile(view2->answer, view_mapset, "",
                                       &viewshed_map_cell_type, message);
            else {
                viewshed_fd =
                    Open_raster_infile(view->answer, view_mapset, "",
                                       &viewshed_map_cell_type, message);
                G_warning(
                    _("Computing skyline index using same viewshed maps for "
                      "horizon and line-of-sight from viewshed cells - is this "
                      "really what you want (see manual page)"));
            }

            if (viewshed_fd < 0)
                G_warning("%s", message);
            else {
                if (view2->answer != NULL)
                    G_message(_("Reading viewshed from <%s@%s>\n"),
                              view2->answer, view_mapset);
                else
                    G_message(_("Re-reading viewshed from <%s@%s>\n"),
                              view->answer, view_mapset);

                viewshed_buf =
                    Allocate_raster_buf_with_null(viewshed_buf_cell_type);
                Read_raster_infile(viewshed_buf, viewshed_fd,
                                   viewshed_buf_cell_type,
                                   viewshed_map_cell_type);
                Close_raster_file(viewshed_fd);

                /* Retrieve inclination value for all points on horizon */

                G_message(_("Computing skyline index\n"));

                edge_cur = List_next_horizon(&edge_head);
                while (edge_cur != edge_cur->next_horizon) {
                    List_retrieve_inclination_from_buf(viewshed_buf, edge_cur,
                                                       viewshed_buf_cell_type);
                    edge_cur = List_next_horizon(edge_cur);
                }

                /* Calc outer bounding box for cells that could be visible given
                   max distance.  There is no point in processing cells outside
                   that. */

                side_ew_cells = floor(max_dist / window.ew_res);
                e_box1 = viewpt_col + side_ew_cells; /* col origin at west */
                w_box1 = viewpt_col - side_ew_cells;
                side_ns_cells = floor(max_dist / window.ns_res);
                n_box1 = viewpt_row - side_ns_cells; /* row origin at north */
                s_box1 = viewpt_row + side_ns_cells;

                /* Adjust outer bounding box if it is clipped by current region
                 */

                if (e_box1 >= e_col)
                    e_box1 = e_col;
                if (w_box1 <= w_col)
                    w_box1 = w_col;
                if (n_box1 <= n_row)
                    n_box1 = n_row;
                if (s_box1 >= s_row)
                    s_box1 = s_row;

                /* Build index to list of horizon cells to speed search */

                /* edge_cur = List_next_horizon (&edge_head); */
                /* while (edge_cur != edge_cur->next_horizon) */
                /*        { */
                /*          List_print_entry_all (stderr, edge_cur); */
                /*          edge_cur = List_next_horizon (edge_cur); */
                /*        } */

                quad1_hoz_head = List_first_horizon_quad1(&edge_head);
                quad2_hoz_head = List_first_horizon_quad2(&edge_head);
                quad3_hoz_head = List_first_horizon_quad3(&edge_head);
                quad4_hoz_head = List_first_horizon_quad4(&edge_head);

                /* Traverse all cells in viewshed and replace inclination with
                   skyline index */

                min_skyline_index = 360.0;
                max_skyline_index = -360.0;
                for (row = n_box1; row <= s_box1;
                     row++) { /* row origin at north */
                    for (col = w_box1; col <= e_box1; col++) {
                        inclination = Get_buffer_value_d_row_col(
                            viewshed_buf, viewshed_buf_cell_type, row, col);
                        if (!(Rast_is_null_value(&inclination,
                                                 viewshed_buf_cell_type))) {
                            skyline_index = compute_skyline_index(
                                row, col, inclination, &edge_head,
                                quad1_hoz_head, quad2_hoz_head, quad3_hoz_head,
                                quad4_hoz_head);

                            /* skyline_index = compute_skyline_index_simple
                             * (row, col, inclination, */
                            /*                                            &edge_head);
                             */

                            Set_buffer_value_d_row_col(
                                viewshed_buf, skyline_index,
                                viewshed_buf_cell_type, row, col);

                            if (skyline_index < min_skyline_index)
                                min_skyline_index = skyline_index;
                            if (skyline_index > max_skyline_index)
                                max_skyline_index = skyline_index;
                        }
                    }
                }

                /* Mark the original viewpoint, only needed if using
                   compute_skyline_index_simple () */
                /* Set_buffer_value_d_row_col (viewshed_buf, VIEWPT_SKYLINE, */
                /*                                  viewshed_buf_cell_type,
                 * viewpt_row, viewpt_col); */

                /* Write all the skyline index values out to a new raster map */

                skyline_fd = Open_raster_outfile(
                    skyline->answer, current_mapset, skyline_map_cell_type,
                    overwrite, message);
                if (skyline_fd < 0)
                    G_warning("%s", message);
                else {
                    /* Write data from viewshed_buf (now contains the
                       skyline index values) and close output file */

                    Write_raster_outfile(viewshed_buf, skyline_fd,
                                         viewshed_buf_cell_type,
                                         skyline_map_cell_type);
                    Close_raster_file(skyline_fd);

                    /* Random access to viewshed map no longer needed so free
                     * memory */
                    G_free(viewshed_buf);
                }
            }
        }

        /***********************************************************************
           Write ASCII file of sorted azimuths if requested

        ***********************************************************************/

        if (do_profile) {
            /* If map of elevation values provided */

            if (dem->answer != NULL) {
                /* Open, read and close dem */

                dem_fd = Open_raster_infile(dem->answer, dem_mapset, "",
                                            &dem_map_cell_type, message);
                if (dem_fd < 0)
                    G_warning("%s", message);
                else {
                    G_message(_("Reading elevation from <%s@%s>\n"),
                              dem->answer, dem_mapset);

                    dem_buf = Allocate_raster_buf_with_null(dem_buf_cell_type);
                    Read_raster_infile(dem_buf, dem_fd, dem_buf_cell_type,
                                       dem_map_cell_type);
                    Close_raster_file(dem_fd);

                    /* Retrieve elevation value for all points on horizon */

                    edge_cur = List_next_horizon(&edge_head);
                    while (edge_cur != edge_cur->next_horizon) {
                        List_retrieve_elevation_from_buf(dem_buf, edge_cur,
                                                         dem_buf_cell_type);
                        edge_cur = List_next_horizon(edge_cur);
                    }

                    /* Random access to dem no longer needed so free memory */

                    G_free(dem_buf);
                }
            }

            /* Open ASCII text file */

            strcpy(profile_name, profile->answer);
            profile_str = Create_file(profile_name, ".csv", message, overwrite);
            if (profile_str == NULL)
                G_warning("%s", message);
            else {

                /* Write azimuth, inclination, elevation and type to file */

                if ((dem->answer != NULL) && (dem_fd >= 0))
                    fprintf(profile_str,
                            "Azimuth,Inclination,Distance,Elevation,Type\n");
                else
                    fprintf(profile_str, "Azimuth,Inclination,Distance,Type\n");

                edge_cur = List_next_horizon(&edge_head);
                while (edge_cur != edge_cur->next_horizon) {
                    if ((dem->answer != NULL) && (dem_fd >= 0))
                        List_print_entry(profile_str, edge_cur);
                    else
                        List_print_entry_no_elev(profile_str, edge_cur);
                    edge_cur = List_next_horizon(edge_cur);
                }

                /* Close file */

                fclose(profile_str);
            }
        }
    }

    /***********************************************************************
      Create support files

    ***********************************************************************/

    G_message(_("Creating support files\n"));

    if (do_hoz_az) {
        /* Create history support file for horizon azimuth map */

        Rast_short_history(hoz_az->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, view->answer);
        Rast_command_history(&history);
        Rast_write_history(hoz_az->answer, &history);

        /* Create category file for horizon azimuth map */

        Rast_read_cats(hoz_az->answer, current_mapset, &cats);
        Rast_set_cats_fmt("$1 degree$?s", 1.0, 0.0, 0.0, 0.0, &cats);
        Rast_write_cats(hoz_az->answer, &cats);
        Rast_free_cats(&cats);
    }

    if (do_hoz_inc) {
        /* Create history support file for horizon inclination map */

        Rast_short_history(hoz_inc->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, view->answer);
        Rast_command_history(&history);
        Rast_write_history(hoz_inc->answer, &history);

        /* Create category file for horizon inclination map */

        Rast_read_cats(hoz_inc->answer, current_mapset, &cats);
        Rast_set_cats_fmt("$1 degree$?s", 1.0, 0.0, 0.0, 0.0, &cats);
        Rast_write_cats(hoz_inc->answer, &cats);
        Rast_free_cats(&cats);
    }

    if (hoz_type->answer != NULL) {
        /* Create history support file for hoz_type map */

        Rast_short_history(hoz_type->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, view->answer);
        Rast_command_history(&history);
        Rast_write_history(hoz_type->answer, &history);

        /* Create category file for horizon type map */

        /* TO DO */
    }

    if (edges->answer != NULL) {
        /* Create history support file for edges map */

        Rast_short_history(edges->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, view->answer);
        Rast_command_history(&history);
        Rast_write_history(edges->answer, &history);

        /* Create category file for edges map */

        /* TO DO */
    }

    if (do_skyline) {
        /* Create history support file for skyline map */

        Rast_short_history(skyline->answer, "raster", &history);
        Rast_set_history(&history, HIST_DATSRC_1, view->answer);
        Rast_command_history(&history);
        Rast_write_history(skyline->answer, &history);

        /* Create category file for skyline map */

        /* TO DO */

        /* Create colour ramp for skyline map */
        /* fprintf(stderr,"\nmin_skyline_index %.3lf ", min_skyline_index); */
        /* fprintf(stderr,"\nmax_skyline_index %.3lf ", max_skyline_index); */

        /* double val1= -180; */
        /* double* val1_ptr = &val1;  */
        /* double val2= 1000.0; */
        /* double* val2_ptr = &val2;  */
        /* Rast_init_colors (&colr); */
        /* Rast_add_color_rule (val1_ptr, 255,0,0, val2_ptr, 0,0,0, */
        /*                           &colr, skyline_map_cell_type); */
        /* Rast_write_colors(skyline->answer, G_mapset(), &colr); */
    }

    G_message(_("Job finished\n"));

    return (EXIT_SUCCESS);
}
