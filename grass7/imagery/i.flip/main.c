
/****************************************************************************
 *
 * MODULE:       i.vi
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Flips an image North-South.
 *
 * COPYRIGHT:    (C) 2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * Remark:
 *		 Initial need for TRMM import
 *
 * Changelog:	 
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{
    int nrows, ncols;
    int row, col;
    char *desc;
    struct GModule *module;
    struct Option *input, *output;
    struct History history;	/*metadata */
    struct Colors colors;	/*Color rules */

    char *in, *out;		/*in/out raster names */
    int infd, outfd;
    void *inrast, *outrast;
    RASTER_MAP_TYPE data_type_input;
    CELL val1, val2;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("flip"));
    module->label =
	_("Flips an image North-South.");
    module->description = _("Flips an image North-South.");

    /* Define the different options */
    input = G_define_standard_option(G_OPT_R_INPUT);
    output = G_define_standard_option(G_OPT_R_OUTPUT);

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    in=input->answer;
    out=output->answer;
    
    /* Open input raster file */
    infd = Rast_open_old(in, "");
    data_type_input = Rast_map_type(in, "");
    inrast = Rast_allocate_buf(data_type_input);

    /* Create New raster file */
    outfd = Rast_open_new(out, data_type_input);
    outrast = Rast_allocate_buf(data_type_input);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Process pixels */
    for (row = 0; row < nrows; row++)
    {
	G_percent(row, nrows, 2);
	/* read input maps */
	Rast_get_row(infd,inrast,(nrows-1-row),data_type_input);
	/* process the data */
	Rast_put_row(outfd,inrast,data_type_input);
    }

    G_free(inrast);
    Rast_close(infd);
    G_free(outrast);
    Rast_close(outfd);

    /* Color from 0 to +1000 in grey */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 1000;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    Rast_short_history(out, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out, &history);

    exit(EXIT_SUCCESS);
}

