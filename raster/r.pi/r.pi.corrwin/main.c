#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "ncb.h"
#include "local_proto.h"
#include <math.h>

/*
	Moving window correlation analyse.
	
	Put together from pieces of r.covar and r.neighbors by Elshad Shirinov.
*/

typedef int (*ifunc)(void);

struct ncb ncb;

int main (int argc, char *argv[])
{
	char *p, *p1, *p2;
	int verbose;
	// in and out file pointers
	int in_fd1, in_fd2;
	int out_fd;
	DCELL *result;
	
	RASTER_MAP_TYPE map_type1, map_type2;
	
	int row, col, i, j;
	int readrow;
	int maxval;
	
	int nrows, ncols;
	int n;
	int copycolr;
	struct Colors colr;
	struct GModule *module;
	struct
	{
		struct Option *input1, *input2, *output;
		struct Option *size, *max;
		struct Option *title;
	} parm;
	struct
	{
		struct Flag *quiet;
	} flag;

	DCELL *values1, *values2;   /* list of neighborhood values */

	G_gisinit (argv[0]);

	module = G_define_module();
	module->keywords = _("raster");
    module->description =
		_("Calculates correlation of two raster maps "
		  "by calculating correlation function of two "
		  "corresponding rectangular areas for each "
		  "raster point and writing the result into a new raster map.");

	parm.input1 = G_define_option() ;
	parm.input1->key        = "input1" ;
	parm.input1->type       = TYPE_STRING ;
	parm.input1->required   = YES ;
	parm.input1->gisprompt  = "old,cell,raster,1" ;
	parm.input1->description= _("Name of existing raster file") ;

	parm.input2 = G_define_option() ;
	parm.input2->key        = "input2" ;
	parm.input2->type       = TYPE_STRING ;
	parm.input2->required   = YES ;
	parm.input2->gisprompt  = "old,cell,raster,2" ;
	parm.input2->description= _("Name of existing raster file") ;

	parm.output = G_define_option() ;
	parm.output->key        = "output" ;
	parm.output->type       = TYPE_STRING ;
	parm.output->required   = YES ;
	parm.output->gisprompt  = "new,cell,raster" ;
	parm.output->description= _("Name of the new raster file") ;

	parm.size = G_define_option() ;
	parm.size->key        = "size" ;
	parm.size->type       = TYPE_INTEGER ;
	parm.size->required   = YES ;
	parm.size->options    = "1,3,5,7,9,11,13,15,17,19,21,23,25" ;
	parm.size->description= _("Neighborhood size") ;

	parm.max = G_define_option() ;
	parm.max->key        = "max" ;
	parm.max->type       = TYPE_INTEGER ;
	parm.max->required   = YES ;
	parm.max->description= _("Correlation maximum value") ;

	parm.title = G_define_option() ;
	parm.title->key        = "title" ;
	parm.title->key_desc   = "\"phrase\"" ;
	parm.title->type       = TYPE_STRING ;
	parm.title->required   = NO ;
	parm.title->description= _("Title of the output raster file") ;

	flag.quiet = G_define_flag();
	flag.quiet->key = 'q';
	flag.quiet->description = _("Run quietly");

	if (G_parser(argc,argv))
		exit(1);

	// get names of input files
	p1 = ncb.oldcell1.name = parm.input1->answer;
	p2 = ncb.oldcell2.name = parm.input2->answer;
	// test input files existance
	if(NULL == (ncb.oldcell1.mapset = G_find_cell2(p1,"")))
	{
		fprintf (stderr, "%s: <%s> raster file not found\n",
			 G_program_name(), p1);
		exit(1);
	}
	if(NULL == (ncb.oldcell2.mapset = G_find_cell2(p2,"")))
	{
		fprintf (stderr, "%s: <%s> raster file not found\n",
			 G_program_name(), p2);
		exit(1);
	}
	// check if new file name is correct
	p = ncb.newcell.name = parm.output->answer;
	if (G_legal_filename(p) < 0)
	{
		fprintf (stderr, "%s: <%s> illegal file name\n",
			 G_program_name(), p);
		exit(1);
	}
	ncb.newcell.mapset = G_mapset();

	// get window size
	nrows = G_window_rows();
	ncols = G_window_cols();
	
	fprintf(stderr, "%d x %d ", nrows, ncols);

	/* open cell files */
	if ((in_fd1 = G_open_cell_old (ncb.oldcell1.name, ncb.oldcell1.mapset)) < 0)
	{
		char msg[200];
		sprintf(msg,"can't open cell file <%s> in mapset %s\n",
			ncb.oldcell1.name, ncb.oldcell1.mapset);
		G_fatal_error (msg);
		exit(-1);
	}
	if ((in_fd2 = G_open_cell_old (ncb.oldcell2.name, ncb.oldcell2.mapset)) < 0)
	{
		char msg[200];
		sprintf(msg,"can't open cell file <%s> in mapset %s\n",
			ncb.oldcell2.name, ncb.oldcell2.mapset);
		G_fatal_error (msg);
		exit(-1);
	}
	
	// get map types
	map_type1 = G_raster_map_type(ncb.oldcell1.name, ncb.oldcell1.mapset);
	map_type2 = G_raster_map_type(ncb.oldcell2.name, ncb.oldcell2.mapset);

	/* copy color table? */
	copycolr = (G_read_colors (ncb.oldcell1.name, ncb.oldcell1.mapset, &colr) > 0);
	
	/* get the neighborhood size */
	sscanf (parm.size->answer, "%d", &ncb.nsize);
	ncb.dist = ncb.nsize/2;
	
	/* get correlation maximum */
	sscanf(parm.max->answer, "%d", &maxval);
	
	/* allocate the cell buffers */
	allocate_bufs ();
	values1 = (DCELL *) G_malloc (ncb.nsize * ncb.nsize * sizeof (DCELL));
	values2 = (DCELL *) G_malloc (ncb.nsize * ncb.nsize * sizeof (DCELL));
	result = G_allocate_d_raster_buf();

	/* get title, initialize the category and stat info */
	if (parm.title->answer)
		strcpy (ncb.title, parm.title->answer);
	else
		sprintf (ncb.title,"%dx%d neighborhood correlation: %s and %s",
			 ncb.nsize, ncb.nsize, ncb.oldcell1.name, ncb.oldcell2.name);


	/* initialize the cell bufs with 'dist' rows of the old cellfile */

	readrow = 0;
	for (row = 0; row < ncb.dist; row++) {
		readcell (in_fd1, 1, readrow, nrows, ncols);
		readcell (in_fd2, 2, readrow, nrows, ncols);
		readrow++;
	}

	/*open the new cellfile */
	out_fd = G_open_raster_new (ncb.newcell.name, map_type1);
	if (out_fd < 0)
		exit(1);

	if (verbose = !flag.quiet->answer)
		fprintf (stderr, "Percent complete ... ");
	
	for (row = 0; row < nrows; row++)
	{
		if (verbose)
			G_percent (row, nrows, 2);
		// read the next row into buffer
		readcell (in_fd1, 1, readrow, nrows, ncols);
		readcell (in_fd2, 2, readrow, nrows, ncols);
		readrow++;
		for (col = 0; col < ncols; col++)
		{
			DCELL sum1 = 0;
			DCELL sum2 = 0;
			DCELL mul, mul1, mul2; 
			mul = mul1 = mul2 = 0;
			double count = 0;
			DCELL ii, jj;

			// set pointer to actual position in the result
			DCELL *rp = &result[col];
			// gather values from actual window
			gather(values1, 1, col);
			gather(values2, 2, col);
			// go through all values of the window
			for (i = 0; i < ncb.nsize * ncb.nsize; i++) {
				// ignore values if both are nan
				if (!(G_is_d_null_value(&values1[i]) && G_is_d_null_value(&values2[i]))) {
					if (!G_is_d_null_value(&values1[i])) {
						sum1 += values1[i];
						mul1 += values1[i] * values1[i];
					}
					if (!G_is_d_null_value(&values2[i])) {
						sum2 += values2[i];
						mul2 += values2[i] * values2[i];
					}
					if (!G_is_d_null_value(&values1[i]) && !G_is_d_null_value(&values2[i]))
						mul += values1[i] * values2[i];
					// count the number of values actually processed
					count++;
				}
			}
			if (count <= 1.1) {
				*rp = 0;
				continue;
			}
			// calculate normalization
			ii = sqrt((mul1 - sum1 * sum1 / count) / (count - 1.0));
			jj = sqrt((mul2 - sum2 * sum2 / count) / (count - 1.0));
			
			// set result
			*rp = maxval * (mul - sum1 * sum2 / count) / (ii * jj * (count - 1.0));
			if (G_is_d_null_value(rp)) 
				G_set_d_null_value(rp, 1);
		}
		// write actual result row to the output file
		G_put_d_raster_row(out_fd, result);
	}
	if (verbose)
		G_percent (row, nrows, 2);

	G_close_cell (out_fd);
	G_close_cell (in_fd1);
	G_close_cell (in_fd2);

	if(copycolr)
		G_write_colors (ncb.newcell.name, ncb.newcell.mapset, &colr);

	exit(0);
}
