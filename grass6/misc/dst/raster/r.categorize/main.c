/* TODO: - choosable precision for printf */
/*       - test quantifications for integer maps */

/* r.categorize */
/* Purpose: quickly create a categorized CELL raster map from any input map
	In the output CELL map, every cell will belong to a category or be NULL

   Synopsis:
   r.categorize input=<cell|fcell|dcell> [output=<cell] [mode=''] 
   				[min=<num>] [max=<num>] [logfile=<file>] [-cq]
   
   Example:
   
   r.categorize fcell_map mode=num,10 output=tmp
   
   If run only with 'input=' parameter, program will display information
   about categories present in the input map (if any).
   If run with the 'output=' parameter, program will do a default operation,
   according to the type of input map:
   		- if already categorised and no values in the map, that
		  do not have a category assigned: simply copy input to output
		- if categorised, but some values are unassigned:
         replace unassigned values with NULL and copy categories to output map
		- if no categories present:
			input map in CELL format: do a 'scale' categorisation
			input map in FCELL/DCELL format: do a 'trunc' categorisation
			
	If no output name is given, default name of output map will be
	<input_map_name>.categorised.

	The user can also enforce a categorisation operation on any map, by
	specifying the "mode=" argument, which may be:
		for CELL maps:
			- scale
			- width
			- num
		for FCELL or DCELL maps:
			- width
			- num
			- round
			- trunc
		for FCELL and DCELL maps, the user may also specify a round=<int>
		parameter that controls rounding of upper and lower category
		boundaries in modes 'width' and 'num'.
		
	Explanation of 'mode=' choices:
	
	'mode=' is a multiple parameter. Some modes require specification of
	a numerical value to control the operation:
			- width, <float>	set width of categories = <float>, FCELL maps
			- width, <int>	set width of categories = <int>, CELL maps
			- num, <int>		set number of categories = <int>

	If 'logfile=' is given, program output will be written to the specified
	file instead of the screen.
	
	If a range is specified for the input map using 'min=' and 'max=' parameters,
	all cells with values outside this range will be written as NULL cells
	in the output map.
	
	If flag '-c' is given, only a checking of the input map's categories
	will be done and the results printed out.
	The 'q' flag disables on-screen progress display.	
*/



#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <time.h>

#include <grass/gis.h>
#include "gt/cat_engine.h"

#define PROGVERSION 0.91

int skip_display = -1; /* this works together with the 'zeroskip' flag. It prevents
					      categories with zero count from being displayed in the
						   logfile or on screen. */

/* dump additional information to lofile */
void write_logfile ( FILE *printer, char *output, char *mapset, int zeroskip, int ulskip ) {
	
	int i, cats; /* number of categories in output map */
	char **cats_description; /* category labels */
	long *cat_count; /* category counts */
	long null_count; /* number of NULL cells */
	long nocat_count; /* number of cells that do not fall into the category range [0 .. n] */	
	long total; /* for calculating percentages */
	double percentage;		
	
	cats = GT_get_stats (output,mapset,&null_count, &nocat_count, 0);
	if ( cats < 1 ) {
		G_fatal_error ("Logfile: Output map '%s' has no categories (%i).", output, cats);
	}
	cat_count = GT_get_counts (output,mapset, 0);
	total = 0;
	for (i=0; i<cats; i++) {
		total = total + cat_count[i];
	}	
	total = total + nocat_count;
	total = total + null_count;		
	
	cats_description = GT_get_labels (output, mapset);
	fprintf (printer, "\nCreated map '%s@%s' with %i categories:\n", output, mapset, cats);
	if ( !zeroskip && ulskip ) {
		fprintf (printer, "(skipping categories with zero counts)\n");
	}
	if ( !ulskip && zeroskip ) {
		fprintf (printer, "(skipping unlabeled categories)\n");
	}
	if ( !zeroskip && !ulskip) {
		fprintf (printer, "(skipping categories with zero counts and unlabeled categories)\n");
	}
		

	fprintf (printer, "Cat.\tCount\t   (%%)     Description\n");					
	for (i=0; i<cats; i++) {
		percentage = (double) (cat_count[i]*100) / total;
		if ( cat_count[i] > skip_display ) {
			if ( (strlen (cats_description[i]) > 0) && (!ulskip) ) {
				fprintf (printer, "%i\t%8li  %6.2f%%  '%s'\n", i, cat_count[i],
					percentage,cats_description[i]);
			} else {
				/* does user wish to also see unlabeled categories? */
				if (ulskip) {
					fprintf (printer, "%i\t%8li  %6.2f%%  '%s'\n", i, cat_count[i],
						percentage,cats_description[i]);				
				}
			}
		}
	}
	percentage = (double) (nocat_count*100) / total;
	fprintf (printer, "NO CAT\t%8li  %6.2f%%\n", nocat_count, percentage);
	percentage = (double) (null_count*100) / total;
	fprintf (printer, "NULL\t%8li  %6.2f%%\n", null_count, percentage);
	fprintf (printer,"TOTAL\t%8li\n",total);	

	fprintf (printer,"\n Use 'r.info' on result map '%s@%s' for more info.\n",
				output, mapset);	
}


int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *input; /* raster map to work on */
		struct Option *output; /* output map to write */
		struct Option *mode; /* Categorisation mode */
		struct Option *min; /* range of values to categorise ... */
		struct Option *max; /*   .. anything outside will be NULL in output */
		struct Option *logfile; /* log output to this file instead of stdout */
		struct Option *precision; /* decimal digits precision for log file */
	}
	parm;
	struct
	{
		struct Flag *check; /* only check map categories */
		struct Flag *null; /* also count NULL values? */			
		struct Flag *uncat; /* also count uncategorised cells? */		
		struct Flag *zeroskip; /* also show cats with zero count */	
		struct Flag *ulskip; /* also show unlabeled (CELL) cats */					
		struct Flag *intout; /* force integer map output */
		struct Flag *quiet; /* no status display on screen */
	}
	flag;
	
	int i;
	int error;
	time_t systime;
	
	/* these vars are used to store information about the input map */
	int cats; /* number of categories in input map */
	char **cats_description; /* category labels */
	long *cat_count; /* category counts */
	long null_count; /* number of NULL cells */
	long nocat_count; /* number of cells that do not fall into the category range [0 .. n] */
	double min_region; /* store min and max values of input map in current region */
	double max_region;
	
	/* the next two vars are used to specify a cutting range */
	/* all values in the input map outside of [min ... max] will be */
	/* converted to NULL values in the output map */
	double min = 0; /* setting min and max to the same value means that .. */
	double max = 0; /* .. no range cutting will be performed by default */
	
	char *outfile; /* name of output map */
	FILE *printer;
	char *mapset;
	int log_to_file = 0;		/* output is shown on screen per default */
	int show_progress = 1; /* enable progress display by default */
	long total; /* for calculating percentages */
	double percentage;
	
	char mode[255];
	char *numstr;
	double num = 0;
		
	module = G_define_module ();
	module->description = "Creates a fully categorized CELL raster map.";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);
		
	/* DEFINE OPTIONS AND FLAGS */
	/* input raster map */
	parm.input = G_define_standard_option(G_OPT_R_INPUT) ;
	parm.input->key = "input";
	parm.input->type = TYPE_STRING;
	parm.input->required = YES;
	parm.input->description = "Input raster map in CELL, FCELL or DCELL format";	
	parm.input->gisprompt = "old,cell,raster" ;

	/* Output map name */
	parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
	parm.output->key = "output";
	parm.output->type = TYPE_DOUBLE;
	parm.output->required = NO;
	parm.output->description = "Output map name";
	parm.output->gisprompt = "cell,raster" ;

	/* Categorisation mode */
	parm.mode = G_define_option ();
	parm.mode->key = "mode";
	parm.mode->type = TYPE_STRING;
	parm.mode->required = NO;
	parm.mode->description = "Categorization mode (see manual)";

	/* min raster value to categorise */
	parm.min = G_define_option ();
	parm.min->key = "min";
	parm.min->type = TYPE_DOUBLE;
	parm.min->required = NO;
	parm.min->description = "Minimum value in input map to include in categorization";

	/* max raster value to categorise */
	parm.max = G_define_option ();
	parm.max->key = "max";
	parm.max->type = TYPE_DOUBLE;
	parm.max->required = NO;
	parm.max->description = "Maximum value in input map to include in categorization";

	/* optional name of logfile */
	parm.logfile = G_define_option ();
	parm.logfile->key = "logfile";
	parm.logfile->type = TYPE_DOUBLE;
	parm.logfile->required = NO;
	parm.logfile->description = "Name of ASCII logfile, if desired";
	
	/* optional number of decimal digitis to store in logfile/show on screen */
	parm.precision = G_define_option ();
	parm.precision->key = "precision";
	parm.precision->type = TYPE_DOUBLE;
	parm.precision->required = NO;
	parm.precision->answer = "2";
	parm.precision->description = "Number of decimal digits for statistics/logfile";

	/* only check? */
	flag.check = G_define_flag ();
	flag.check->key = 'c';	
	flag.check->description = "Only check categories of input map";

	/* include NULL values in count? */
	flag.null = G_define_flag ();
	flag.null->key = 'n';	
	flag.null->description = "Print count/percentage of NULL cells";

	/* include cells w/o categories in count? */
	flag.uncat = G_define_flag ();
	flag.uncat->key = 'u';	
	flag.uncat->description = "Print count/percentage of uncategorized cells";
	
	/* enable display of cats with zero count? */
	flag.zeroskip = G_define_flag ();
	flag.zeroskip->key = 'z';
	flag.zeroskip->description = "Enable display of categories with zero count";

	/* enable display of cats without labels? */
	flag.ulskip = G_define_flag ();
	flag.ulskip->key = 'l';
	flag.ulskip->description = "Enable display of unlabeled categories";

	/* force integer (CELL) output map, even if input is floating point */
	flag.intout = G_define_flag ();
	flag.intout->key = 'i';
	flag.intout->description = "Force integer output, even if input is floating point";

	/* quiet operation? */
	flag.quiet = G_define_flag ();
	flag.quiet->key = 'q';
	flag.quiet->description = "Disable on-screen progress display";	

	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
		
   	if (G_parser(argc, argv))
        	exit(-1);	
		
	/* check for 'quiet' flag */
	if ( flag.quiet->answer ) {
		show_progress = 0;
	}
	
	/* set skipping of zero counts */
	skip_display = skip_display + (1-flag.zeroskip->answer);
	
	/* where are we going to send output to? */
	if ( parm.logfile->answer != NULL ) {
		printer = fopen (parm.logfile->answer,"w+");
		if ( printer == NULL) {
			G_fatal_error ("Could not open logfile for write access.");
		}
		log_to_file = 1;
	} else {		
		printer = stdout;
	}	
	
	/* check if input file is available */
	mapset = G_find_cell (parm.input->answer,"");
	if ( mapset == NULL) {
		G_fatal_error ("The input map %s does not exist in the current database.",parm.input->answer);
	}
	cats = GT_get_stats (parm.input->answer,mapset,&null_count, &nocat_count, show_progress);
	if ( cats < 0 ) {
		G_fatal_error ("Could not stat input map. Do you have read access?");
	}
	
	/* get minimum and maximum values in current region */
	/* (we need those, anyway) */
	error = GT_get_range (parm.input->answer,mapset,&min_region, &max_region, show_progress);		
	
	/* before we do anything else: check, if -c flag is set */
	/* if so, just display category information and exit. */
	/* Also, if logging to file is activated, this same information will */
	/* be printed to the log file header */
	if ( (flag.check->answer) || (log_to_file) ) {
		if ( log_to_file ) { /* LOGFILE HEADER */
			systime = time (NULL);
			fprintf (printer, "This logfile was created by 'r.categorize', %s", ctime(&systime));
		}		
		fprintf (printer,"\nCategory information for '%s@%s':\n", parm.input->answer, mapset);
		if ( G_raster_map_is_fp (parm.input->answer,mapset)) {
			fprintf (printer,"Input map is a floating point raster.\n");		
		} else {
			fprintf (printer,"Input map is an integer raster.\n");		
		}
		if ( cats == 0 ) {
			fprintf (printer,"Input map has no category definitions.\n");
			if (flag.check->answer) return (0);
		}
		fprintf (printer,"Range of values in current region = %.3f  to %.3f.\n", 
						min_region, max_region);
		cat_count = GT_get_counts (parm.input->answer,mapset, 0);		
		total = 0;
		for (i=0; i<cats; i++) {
			total = total + cat_count[i];
		}
		if ( flag.uncat->answer) {
			total = total + nocat_count;
		}
		if ( flag.null->answer) {
			total = total + null_count;
		}		
		cats_description = GT_get_labels (parm.input->answer,mapset);
		fprintf (printer, "Number of categories = %i\n", cats);
		if ( (cats > 0) ) {
			if ( (!flag.zeroskip->answer) && (flag.ulskip->answer) ) {
				fprintf (printer, "(skipping categories with zero counts)\n");
			}
			if ( (!flag.ulskip->answer) && (flag.zeroskip->answer) ) {
				fprintf (printer, "(skipping unlabeled categories)\n");
			}
			if ( (!flag.zeroskip->answer) && (!flag.ulskip->answer)) {
				fprintf (printer, "(skipping categories with zero counts and unlabeled categories)\n");
			}
			
		}
		fprintf (printer, "Cat.\tCount\t   (%%)     Description\n");			
		for (i=0; i<cats; i++) {
			percentage = (double) (cat_count[i]*100) / total;
			if ( cat_count[i] > skip_display ) {
				/* in CELL maps, there might be unlabeled categories. Skip those. */
				if ( (strlen (cats_description[i]) > 0) && (!flag.ulskip->answer) ) {
					fprintf (printer, "%i\t%8li  %6.2f%%  '%s'\n", i, cat_count[i],
							percentage,cats_description[i]);
				} else {
					/* does user wish to also see unlabeled categories? */
					if (flag.ulskip->answer) {
						fprintf (printer, "%i\t%8li  %6.2f%%  '%s'\n", i, cat_count[i],
							percentage,cats_description[i]);				
					}
				}
			}		

		}
		if ( flag.uncat->answer ) { /* also print uncategorised cells? */
			percentage = (double) (nocat_count*100) / total;
			fprintf (printer, "NO CAT\t%8li  %6.2f%%\n", nocat_count, percentage);
		}
		if ( flag.null->answer ) { /* also print NULL cells? */
			percentage = (double) (null_count*100) / total;
			fprintf (printer, "NULL\t%8li  %6.2f%%\n", null_count, percentage);
		}
		
		fprintf (printer,"TOTAL\t%8li\n",total);
		
		/* if we are in 'check only' mode: just return number of cats and adios */
		if (flag.check->answer) {			
			return (cats);
		}
	}		
		
	/* construct default output file name */
	if ( parm.output->answer == NULL ) {
		outfile = G_calloc ((signed) strlen(parm.input->answer)+13, sizeof(char));
		sprintf (outfile, "%s.categorized", parm.input->answer);
		fprintf (printer, "Result file will be written to: %s\n", outfile);
	} else {
		outfile = parm.output->answer;
	}
	
	/* check for cutting range */
	if ( (parm.min->answer != NULL) && (parm.max->answer == NULL)) {
		min = atof (parm.min->answer);
		max = max_region;
	}
	if ( (parm.max->answer != NULL) && (parm.min->answer == NULL)) {
		max = atof (parm.max->answer);
		min = min_region;
	}
	if ( (parm.max->answer != NULL) && (parm.min->answer != NULL)) {
		max = atof (parm.max->answer);		
		min = atof (parm.min->answer);		
	}
	
	/* write cutting range to logfile, if needed */
	if ( (max != min) && (log_to_file) ) {
		fprintf (printer,"\nCUT RANGE: All values smaller than %.3f and\nlarger than %.3f in the input map will be converted to NULL\nin the output map.\n",
						min, max);
	}
	
	/* set decimal digits precision for history file and category labels */
	GT_set_decdigits ((unsigned) atoi(parm.precision->answer));
	
	/* default operation, if no 'mode' is given or 'clean' */
	if ( (parm.mode->answer == NULL) || (strstr (parm.mode->answer,"clean") != NULL) ) {
		/* clean cats */
		error = GT_set_cats_only (parm.input->answer, mapset, outfile, flag.intout->answer, show_progress);
		switch (error) {
			case -1: G_fatal_error ("Invalid input map format.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
					break;
			case -4: G_fatal_error ("Input map contains no categories.");
		}						
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'clean'.\n" );			
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);			
		}		
		return (0);
	} else {	
		/* if a mode is given: tokenise option string and check */
		/* for valid combination of 'mode' and 'num' */	
		strcpy (mode, parm.mode->answer);
		numstr = G_strstr (mode,",");
		if ( numstr != NULL) {		
			/* convert 'num' option to a double value */
			numstr ++;
			num = strtod (numstr,NULL);
			if ( num <= 0 ) {
				G_fatal_error ("Invalid quantifier (must be a positive value).");
			}
		}
	}

	/* DETERMINE MODE OF OPERATION */
	/* ANY MAP: NUMBER OF CLASSES */	
	if ( strstr (mode,"num") != NULL ) {		
		if ( (int) num <= 1 ) {
			G_fatal_error ("Number of categories must be an integer > 1.\n");
		}
		/* create new map by truncating floating point values */
		error = GT_set_cats_num (parm.input->answer, mapset, outfile, 
									 min, max, (int) num, flag.intout->answer, show_progress);		
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Invalid input map format.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}		
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'num'.\n" );			
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}
		return (0);
	}

	/* ANY MAP: WIDTH OF CLASSES WITH ROUNDED LOWEST CLASS BORDER */
	if ( strstr (mode,"rwidth") != NULL ) {
		if ( num <= 0 ) {
			G_fatal_error ("Category width must be > 0.\n");
		}
		/* create new map by truncating floating point values */
		error = GT_set_cats_width (parm.input->answer, mapset, outfile, 
									 min, max, num, 1, flag.intout->answer, show_progress);
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Invalid input map format.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}			
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'rwidth'.\n" );
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}		
		return (0);
	}
	
	/* ANY MAP: WIDTH OF CLASSES */
	if ( strstr (mode,"width") != NULL ) {
		if ( num <= 0 ) {
			G_fatal_error ("Category width must be > 0.\n");
		}
		/* create new map by truncating floating point values */
		error = GT_set_cats_width (parm.input->answer, mapset, outfile, 
									 min, max, num, 0, flag.intout->answer, show_progress);
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Invalid input map format.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'width'.\n" );
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}		
		return (0);
	}	
	
	/* FP: TRUNCATION */
	if ( strstr (mode,"trunc") != NULL ) {
		/* create new map by truncating floating point values */
		error = GT_set_f_cats_trunc (parm.input->answer, mapset, outfile, 
									 min, max, show_progress);
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Input map must be floating point for 'trunc' mode.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'trunc'.\n" );
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}		
		return (0);
	}
	
	/* FP: ROUNDING */
	if ( strstr (mode,"round") != NULL ) {
		/* create new map by truncating floating point values */
		error = GT_set_f_cats_round (parm.input->answer, mapset, outfile, 
									 min, max, show_progress);
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Input map must be floating point for 'round' mode.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'round'.\n" );
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}		
		return (0);
	}
	
	/* INT: RESCALE */
	if ( strstr (mode,"scale") != NULL ) {
		/* create new map by truncating floating point values */
		error = GT_set_c_cats_scale (parm.input->answer, mapset, outfile, 
									 (int) min, (int) max, show_progress);
		switch (error) {
			case 0: G_fatal_error ("No categories could be created for output map.");
					break;
			case -1: G_fatal_error ("Input must be an integer map for 'scale' mode.");
					break;
			case -2: G_fatal_error ("Input map read error.");
					break;
			case -3: G_fatal_error ("Output map write error.");
		}			
		if ( log_to_file ) {
			fprintf ( printer, "\nMode of operation = 'scale'.\n" );
			write_logfile ( printer, outfile, mapset, flag.zeroskip->answer, flag.ulskip->answer);
		}		
		return (0);
	}	
	
	/* something has been specified for 'mode', but obviously */
	/* nothing correct */
	if ( parm.mode->answer != NULL ) {
		fprintf (stderr,"'%s' is not a valid quantification mode. Choose one of:\n"
						, parm.mode->answer);
		fprintf (stderr,"\tscale\n\tnum,<NUM>\n\twidth,<NUM>\n\trwidth,<NUM>\n\tround\n\ttrunc\n\tclean\n");
		G_fatal_error ("Please refer to manual page.");
	}
			
	return (EXIT_SUCCESS);
}
