
/****************************************************************************
 *
 * MODULE:       i.vi
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Flips an image North-South, East-West (-w) or both (-b).
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
    struct History history;	/*Metadata */
    struct Colors colors;	/*Color rules */
    struct Flag *flag1, *flag2; /*Flags */

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

    /* define the different flags */
    flag1 = G_define_flag();
    flag1->key = 'w';
    flag1->description = _("East-West flip");

    flag2 = G_define_flag();
    flag2->key = 'b';
    flag2->description = _("Both N-S and E-W flip");

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

    if(flag1->answer)
    {
        /* Process pixels for E-W flip*/
        for (row = 0; row < nrows; row++)
        {
            G_percent(row, nrows, 2);
            /* read input maps */
            Rast_get_row(infd,inrast,row,data_type_input);
            for (col = 0; col < ncols; col++)
            {
	        switch(data_type_input){
		    case CELL_TYPE:
			((CELL *)outrast)[ncols-1-col]=((CELL *)inrast)[col];
			break;
		    case FCELL_TYPE:
			((FCELL *)outrast)[ncols-1-col]=((FCELL *)inrast)[col];
			break;
		    case DCELL_TYPE:
			((DCELL *)outrast)[ncols-1-col]=((DCELL *)inrast)[col];
			break;
	        }
            }
            /* process the data */
            Rast_put_row(outfd,outrast,data_type_input);
        }
    }else if(flag2->answer)
    {
        /* Process pixels for both N-S and E-W flip*/
        for (row = 0; row < nrows; row++)
        {
            G_percent(row, nrows, 2);
            /* read input maps */
            Rast_get_row(infd,inrast,(nrows-1-row),data_type_input);
            for (col = 0; col < ncols; col++)
            {
	        switch(data_type_input){
		    case CELL_TYPE:
			((CELL *)outrast)[ncols-1-col]=((CELL *)inrast)[col];
			break;
		    case FCELL_TYPE:
			((FCELL *)outrast)[ncols-1-col]=((FCELL *)inrast)[col];
			break;
		    case DCELL_TYPE:
			((DCELL *)outrast)[ncols-1-col]=((DCELL *)inrast)[col];
			break;
	        }
            }
            /* process the data */
            Rast_put_row(outfd,outrast,data_type_input);
        }
    }else
    {
        /* Process pixels for default N-S flip*/
        for (row = 0; row < nrows; row++)
        {
            G_percent(row, nrows, 2);
            /* read input maps */
            Rast_get_row(infd,inrast,(nrows-1-row),data_type_input);
            /* process the data */
            Rast_put_row(outfd,inrast,data_type_input);
        }
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

