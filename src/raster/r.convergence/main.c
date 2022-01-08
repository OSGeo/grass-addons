
/****************************************************************************
 *
 * MODULE:		r.convergence
 * AUTHOR(S):		Jarek Jasiewicz jarekj amu.edu.pl
 * 			Original convergence index in SAGA GIS sofware: Olaf Conrad
 *							 
 * PURPOSE:		Calculate convergence index (parameter defining the local convergence of the relief)
*								
*
* COPYRIGHT:		(C) 2002,2010 by the GRASS Development Team
*
*		 This program is free software under the GNU General Public
*		 License (>=v2). Read the file COPYING that comes with GRASS
*								 for details.
*
 *****************************************************************************/

#define MAIN
#include "local_proto.h"

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *map_dem,
	*map_slope,
	*map_aspect, *par_window, *par_method, *par_differnce, *map_output;

    struct History history;
    struct Colors colors;
    struct Flag *flag_slope, *flag_circular;

    int out_fd;
    float tmp;
    FCELL *out_buf;

    int i, j, n;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("terrain"));
    module->description =
        _("Calculate convergence index.");

    map_dem = G_define_standard_option(G_OPT_R_INPUT);
    map_dem->description = _("Digital elevation model map");

    map_output = G_define_standard_option(G_OPT_R_OUTPUT);
    map_output->description = _("Output convergence index map");

    par_window = G_define_option();
    par_window->key = "window";
    par_window->type = TYPE_INTEGER;
    par_window->answer = "3";
    par_window->required = YES;
    par_window->description = _("Window size");

    par_method = G_define_option();
    par_method->key = "weights";
    par_method->type = TYPE_STRING;
    par_method->options = "standard,inverse,power,square,gentle";
    par_method->answer = "standard";
    par_method->required = YES;
    par_method->description =
	_("Method for reducing the impact of the cell due to distance");

    flag_circular = G_define_flag();
    flag_circular->key = 'c';
    flag_circular->description = _("Use circular window (default: square)");

    flag_slope = G_define_flag();
    flag_slope->key = 's';
    flag_slope->description =
	_("Add slope convergence (radically slows down calculation time)");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    window_size = atoi(par_window->answer);
    if (window_size < 3 || window_size % 2 == 0)
	G_fatal_error(_("Window size must be odd and at least 3"));

    if (!strcmp(par_method->answer, "standard"))
	f_method = m_STANDARD;
    else if (!strcmp(par_method->answer, "inverse"))
	f_method = m_INVERSE;
    else if (!strcmp(par_method->answer, "power"))
	f_method = m_POWER;
    else if (!strcmp(par_method->answer, "square"))
	f_method = m_SQUARE;
    else if (!strcmp(par_method->answer, "gentle"))
	f_method = m_GENTLE;

    f_circular = (flag_circular->answer != 0);
    f_slope = (flag_slope->answer != 0);

    /* align window */
    G_check_input_output_name(map_dem->answer, map_output->answer,
			      G_FATAL_EXIT);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    Rast_get_window(&window);
    radius = window_size / 2;


    {
	int row, col;
	int cur_row;
	int i_row, i_col, j_row, j_col;
	float contr_aspect;
	float dir;
	int n = 0;
	float *local_aspect;
	float convergence;

	out_fd = Rast_open_new(map_output->answer, FCELL_TYPE);
	out_buf = Rast_allocate_buf(FCELL_TYPE);

	strcpy(elevation.elevname, map_dem->answer);
	open_map(&elevation);
	create_maps();

	/* create aspect matrix and distance_matrix */
	create_distance_aspect_matrix(0);

	/* cur_row: current to row in the buffer */
	/* open_map and create_maps create data for first pass */


	for (row = 0; row < nrows; ++row) {
	    G_percent(row, nrows, 2);
	    cur_row = (row < radius) ? row :
		((row >=
		  nrows - radius) ? window_size - (nrows - row) : radius);

	    if (row < radius || row > nrows - radius) {
		Rast_set_f_null_value(out_buf, ncols);
		Rast_put_row(out_fd, out_buf, FCELL_TYPE);
		continue;
	    }

	    for (col = 0; col < ncols; ++col) {
		if (col < radius || col > ncols - radius) {
		    Rast_set_f_null_value(&out_buf[col], 1);
		    continue;
		}
		out_buf[col] =
		    PI2PERCENT * calculate_convergence(row, cur_row, col);
	    }

	    if (row > radius && row < nrows - (radius + 1))
		shift_buffers(row);

	    Rast_put_row(out_fd, out_buf, FCELL_TYPE);

	}			/* end for row */
	G_percent(row, nrows, 2);
    }				/* end block */

    {
	FCOLORS fcolr[7] = {
	    {-100, 56, 0, 0}
	    ,
	    {-70, 128, 0, 0}
	    ,
	    {-50, 255, 0, 0}
	    ,
	    {0, 255, 255, 255}
	    ,
	    {50, 0, 0, 255}
	    ,
	    {70, 0, 0, 128}
	    ,
	    {100, 0, 0, 56}
	};

	Rast_init_colors(&colors);
	for (i = 0; i < 6; ++i)
	    Rast_add_d_color_rule(&fcolr[i].cat, fcolr[i].r, fcolr[i].g,
				  fcolr[i].b, &fcolr[i + 1].cat,
				  fcolr[i + 1].r, fcolr[i + 1].g,
				  fcolr[i + 1].b, &colors);
	Rast_write_colors(map_output->answer, G_mapset(), &colors);
    }

    free_map(slope, window_size);
    free_map(aspect, window_size);
    free_map(elevation.elev, window_size + 1);
    G_free(distance_matrix);
    G_free(aspect_matrix);
    G_free(out_buf);
    Rast_close(out_fd);

    Rast_short_history(map_output->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(map_output->answer, &history);


    G_message("Done!");
    exit(EXIT_SUCCESS);

}
