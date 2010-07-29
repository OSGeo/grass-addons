#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include <math.h>
#include "local_proto.h"

/*
	Fragmentation analysis - basic indices in r.pi.index
	
	by Elshad Shirinov.
*/

typedef int (*f_func)(DCELL*, Coords**, int);

struct menu
{
	f_func method;		/* routine to compute new value */
	char *name;		/* method name */
	char *text;		/* menu display - full description */
};

static struct menu menu[] =
{
	{f_area, "area", "area of specified patches"},
	{f_perim, "perimeter", "perimeter of specified patches"},
	{f_shapeindex, "shape", "shape index of specified patches"},
	{f_borderindex, "border", "border index of specified patches"},
	{f_compactness, "compactness", "compactness of specified patches"},
	{f_asymmetry, "asymmetry", "asymmetry of specified patches"},
	{f_area_perim_ratio, "area-perimeter", "area-perimeter ratio of specified patches"},
	{f_frac_dim, "fractal", "fractal dimension of specified patches"},
	{f_nearest_dist, "ENN", "euclidean distance to nearest patch"},
	{0,0,0}
};

int main (int argc, char *argv[])
{
	/* input */
	char *newname, *oldname, *newmapset, *oldmapset;
	char title[1024];

	/* in and out file pointers */
	int in_fd;
	int out_fd;
	DCELL *result, res[30];
	
	/* map_type and categories */
	RASTER_MAP_TYPE map_type;
	struct Categories cats;
	
	int method;
	f_func compute_values;
	
	/* neighbors count */
	int neighb_count;

	char *p;

	int row, col, i, j;
	int readrow;
	int keyval;
	DCELL range = MAX_DOUBLE;
	
	int n;
	int copycolr;
	struct Colors colr;
	struct GModule *module;
	struct
	{
		struct Option *input, *output;
		struct Option *keyval, *method;
		struct Option *title;
	} parm;
	struct
	{
		struct Flag *adjacent, *quiet;
	} flag;

	DCELL *values;
	Coords *cells;
	int fragcount = 0;
	
	struct Cell_head ch, window;

	G_gisinit (argv[0]);

	module = G_define_module();
	module->keywords = _("raster");
	module->description =
		_("Provides basic patch based indices, like area, SHAPE or Nearest Neighbour distance.");

	parm.input = G_define_option() ;
	parm.input->key        = "input" ;
	parm.input->type       = TYPE_STRING ;
	parm.input->required   = YES ;
	parm.input->gisprompt  = "old,cell,raster" ;
	parm.input->description= _("Raster map containing categories") ;

	parm.output = G_define_option() ;
	parm.output->key        = "output" ;
	parm.output->type       = TYPE_STRING ;
	parm.output->required   = YES ;
	parm.output->gisprompt  = "new,cell,raster" ;
	parm.output->description= _("Output patch-based result as raster map") ;

	parm.keyval = G_define_option() ;
	parm.keyval->key        = "keyval" ;
	parm.keyval->type       = TYPE_INTEGER ;
	parm.keyval->required   = YES ;
	parm.keyval->description= _("The value of the class to be analysed") ;

	parm.method = G_define_option() ;
	parm.method->key        = "method" ;
	parm.method->type       = TYPE_STRING ;
	parm.method->required   = YES ;
	p = parm.method->options  = G_malloc(1024);
	for (n = 0; menu[n].name; n++)
	{
		if (n)
			strcat (p, ",");
		else
			*p = 0;
		strcat (p, menu[n].name);
	}
	parm.method->description= _("Operation to perform on fragments") ;

	parm.title = G_define_option() ;
	parm.title->key        = "title" ;
	parm.title->key_desc   = "\"phrase\"" ;
	parm.title->type       = TYPE_STRING ;
	parm.title->required   = NO ;
	parm.title->description= _("Title of the output raster file") ;

	flag.adjacent = G_define_flag() ;
	flag.adjacent->key        = 'a' ;
	flag.adjacent->description= _("Set for 8 cell-neighbors. 4 cell-neighbors are default.") ;
	
	flag.quiet = G_define_flag();
	flag.quiet->key = 'q';
	flag.quiet->description = _("Run quietly");

	if (G_parser(argc,argv))
		exit(1);

	/* get names of input files */
	oldname = parm.input->answer;

	/* test input files existance */
	if(NULL == (oldmapset = G_find_cell2(oldname,"")))
	{
		fprintf (stderr, "%s: <%s> raster file not found\n",
			 G_program_name(), oldname);
		exit(1);
	}

	/* check if the new file name is correct */
	newname = parm.output->answer;
	if (G_legal_filename(newname) < 0)
	{
		fprintf (stderr, "%s: <%s> illegal file name\n",
			 G_program_name(), newname);
		exit(1);
	}
	newmapset = G_mapset();

	/* get size */
	nrows = G_window_rows();
	ncols = G_window_cols();
	
	/* open cell files */
	if ((in_fd = G_open_cell_old (oldname, oldmapset)) < 0)
	{
		char msg[200];
		sprintf(msg,"can't open cell file <%s> in mapset %s\n",
			oldname, oldmapset);
		G_fatal_error (msg);
		exit(-1);
	}

	/* get map type */
	map_type = DCELL_TYPE;//G_raster_map_type(oldname, oldmapset);

	/* copy color table */
	copycolr = (G_read_colors (oldname, oldmapset, &colr) > 0);
	
	/* get key value */
	sscanf(parm.keyval->answer, "%d", &keyval);

	/* get the method */
	for (method = 0; (p = menu[method].name); method++)
		if ((strcmp(p, parm.method->answer) == 0))
			break;
	if (!p)
	{
		G_warning (_("<%s=%s> unknown %s"),
			 parm.method->key, parm.method->answer, parm.method->key);
		G_usage();
		exit(EXIT_FAILURE);
	}

	/* establish the newvalue routine */
	compute_values = menu[method].method;
	
	/* get number of cell-neighbors */
	neighb_count = flag.adjacent->answer ? 8 : 4;
		
	/* allocate the cell buffers */
	cells = (Coords *) G_malloc ( nrows * ncols * sizeof(Coords));
	actpos = cells;
	fragments = (Coords **) G_malloc (nrows * ncols * sizeof (Coords*));
	fragments[0] = cells;
	flagbuf = (int *) G_malloc (nrows * ncols * sizeof (int));
	result = G_allocate_d_raster_buf();

	/* get title, initialize the category and stat info */
	if (parm.title->answer)
		strcpy (title, parm.title->answer);
	else
		sprintf (title,"Fragmentation of file: %s", oldname);

	/* open the new cellfile  */
	out_fd = G_open_raster_new (newname, map_type);
	if (out_fd < 0) {
		char msg[200];
		sprintf(msg,"can't create new cell file <%s> in mapset %s\n",
			newname, newmapset);
		G_fatal_error (msg);
		exit(1);
	}

	if (verbose = !flag.quiet->answer)
		fprintf (stderr, "Loading Patches ... ");

	/* find fragments */
	for (row = 0; row < nrows; row++) {
		G_get_d_raster_row (in_fd, result, row);
		for (col = 0; col < ncols; col++) {
			if(result[col] == keyval)
				flagbuf[row * ncols + col] = 1;
		}
		
		if (verbose)
			G_percent (row, nrows, 2);
	}

	for(row = 0; row < nrows; row++) {
		for(col = 0; col < ncols; col++) {
			if(flagbuf[row * ncols + col] == 1) {
				fragcount++;
				writeFrag(row, col, neighb_count);
				fragments[fragcount] = actpos;
			}
		}
	}
	if (verbose)
		G_percent (nrows, nrows, 2);	

	/* perform actual function on the patches */
	if (verbose = !flag.quiet->answer)
		fprintf (stderr, "Performing operation ... ");
	values = (DCELL *) G_malloc ( fragcount * sizeof(DCELL));
	compute_values(values, fragments, fragcount);
	if (verbose)
		G_percent (fragcount, fragcount, 2);

	/* write the output file */
	if (verbose = !flag.quiet->answer)
		fprintf (stderr, "Writing output ... ");
	for(row = 0; row < nrows; row++) {
		G_set_d_null_value(result, ncols);
	
		for(i = 0; i < fragcount; i++) {
			for(actpos = fragments[i]; actpos < fragments[i+1]; actpos++) {
				if(actpos->y == row) {
					result[actpos->x] = values[i];
				}
			}
		}
		
		G_put_d_raster_row(out_fd, result);
		
		if (verbose)
			G_percent (row, nrows, 2);
	}
	
	if (verbose)
		G_percent (nrows, nrows, 2);
		
	G_close_cell (out_fd);
	G_close_cell (in_fd);

	G_free(cells);
	G_free(fragments);
	G_free(flagbuf);

	G_init_cats (0, title, &cats);
	G_write_cats (newname, &cats);

	if(copycolr)
		G_write_colors (newname, newmapset, &colr);

	exit(0);
}
