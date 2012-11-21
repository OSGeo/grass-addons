
/****************************************************************************
 *
 * MODULE:       i.rotate
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates an arbitrary rotation of the image from the 
 * 		 center of the computing window
 *
 * COPYRIGHT:    (C) 2002-2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
     
    
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <math.h>
#include <grass/la.h>

int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *output1;
    struct History history;	/*metadata */
    char *result1;		/*output raster name */
    int infd;
    int outfd1;
    char *rnetday;
    void *inrast;

    DCELL * outrast1;
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("rotation"));
    G_add_keyword(_("computation window centre"));
    module->description =
	_("Rotates the image around the centre of the computational window");
    
    /* Define the different options */ 
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    rnetday = input1->answer;
    result1 = output1->answer;
    
    infd = Rast_open_old(rnetday, "");
    inrast = Rast_allocate_d_buf();
    
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast1 = Rast_allocate_d_buf();
    outfd1 = Rast_open_new(result1, DCELL_TYPE);

    /*mat_struct *G_matrix_init(int rows, int cols, int ldim)*/
    /*Increase dimension of image to > of sqrt(2) to fit rotated angles*/
    int matnrows=nrows*1;
    int matncols=ncols*1;
    int matN=matnrows*matncols;
    mat_struct *matin = G_matrix_init (matnrows, matncols, matN);
    G_matrix_zero(matin);
    mat_struct *matout = G_matrix_init (matnrows, matncols, matN);
    G_matrix_zero(matout);
    int deltarow=0.5*(matnrows-nrows);
    int deltacol=0.5*(matncols-ncols);
    DCELL d;
    /* Load input matrix with row&col shift to keep center of image*/ 
    for (row = 0; row < nrows; row++)
	Rast_get_d_row(infd,inrast,row);
    for (col = 0; col < ncols; col++)
    {
            d = ((DCELL *) inrast)[col];
	    if (Rast_is_d_null_value(&d))
		matin[row+deltarow][col+deltacol]=-999.99;
	    else {
		matin[row+deltarow][col+deltacol] = d;
	    }
    }
    double theta=20.0;
    double thetarad=theta*3.1415927/180;
    double costheta=cos(thetarad);
    double sintheta=sin(thetarad);
    int newrow,newcol;
    /*Rotate the matrix*/
    for (row = 0; row < nrows; row++)
    for (col = 0; col < ncols; col++)
    {
	newcol=(col-0.5*ncols)*costheta+(row-0.5*nrows)*sintheta+0.5*ncols;
	newrow=(row-0.5*nrows)*costheta-(col-0.5*ncols)*sintheta+0.5*nrows;
        matout[newrow][newcol] = matin[row][col];
    }

    /*Output to raster file*/
    for (row = 0; row < nrows; row++)
    {
    for (col = 0; col < ncols; col++)
    {
        outrast1[col]=matout[row][col];
    }
    Rast_put_d_row(outfd1,outrast1);
    }

    G_free(inrast);
    Rast_close(infd);
    G_free(outrast1);
    Rast_close(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}


