/* r.xtent */


/*

	TODO Version 1.0
	
	BUGS:
		- Win32:
		  Complains about not being able to remove fcell element for tmapnames[i]. But there is no
		  fcell element for those maps, anyway !!! Maybe this is just a bug in current CVS		    
        
  	DBF TROUBLES:
    		- column names are limited to 10 chars
	
	TEST:
		- what happens, if some attribute values are bad in the input centers map?
		- does this work with CENTROIDS instead of POINTS, as well ?
		- do line breaks work for the protocol on Win32 (both regular and tabular)?
		- NULL cells in input cost surfaces
		
	General coding
		- VALGRIND
		- replace all G_system() with G_spawn(). G_spawn returns -1 on error, so this can be checked!
        	   -> adjust tools.c run_cmd() to use G_spawn() instead of G_system()
		- improve HTML documentation: math typesetting, better formatting. Pictures. Cross references.
		- make status display work on Win32. [currently impossible?]
		- ATTRIBUTE TYPE CHECKING: SOME COULD BE DOUBLE OR INT, BUT SHOULD ALWAYS BE HANDLED AS DOUBLE
			-> use functions GVT_numeric_exists and GVT_get_numeric (), that always returns a double !!!
			- Currently, only C attribute supports double and int, all other do strict type-checking. Should this
			be relaxed?	
		- replace Posix funcs like strcpy with GRASS funcs, where available
		- make sure that memory is dealloc'd properly for things like cats, labels, colors ...
			
	Program functionality
	  - a switch to output areal calculations in ha
	  - let user define sqkm per cell for areal calculations in non-world systems  

	Documentation updates:
	  - C gets normalized automatically!
	  - territorial partitioning will always be complete, unless 'strict' flag given or reach
	    constraint set
	  - paragraph breaks between figures
	  - add more examples, with strict mode and reach constraints
    	  - reach constraint together with unrestricted formula is the recommended way of defining
      	    territorial reach, as it is easier to control than the original I>=0 contraint!
		
		
	TODO VERSION 2.X
			
		A version 1.x should be done if there is enough user demand	

		Political attributes:
			- Model constraints
				* find a way to store for each site: 
					- allies: cannot claim each other's territory: if second highest I is an ally: do not touch it!
			- if any constraints are given, then there should be a check for validity
					to see if they hold in the model result (?!)				
				
		Misc.:
			- user should be able to provide a map for spatially variable k (?)
			- in very complex situations, the model may produce fragmented territories. E.g.:
			r.xtent cent=sites output=test comp_id=comp comp_str=strength elev=dem -g --o
			(Oaxaca dataset, with region set to extents of 'dem' and res=0:00:59)
				-> Should this be catered for? If so, if a center gets captured, then all of
				its cells in the output map (basic I) should be reclassified to the ID of
				the new "boss" (this will automatically be taken care of in cases where
				there is an a priori boss for that center, specified in the ruler= attribute).
			- latex, html, rtf output style for protocols
			
			


******************************

REVISON 0.99, OCT 2007

******************************


FIX BUGS:

UPDATE DOCUMENTATION!

geom.c: in function get_distance():
	delete line distance measure in case where a cost map is used to derive
	distance: only take the cost value (costs[i]) and return that! [DONE]

xent.c: the debugging output for "I=..." should be set to %.10f to allow floating
	point values in much smaller ranges [DONE]
	

Improvements for the next version of r.xtent:

1. Normalize center weights, so that largest center's weight=1.0
	-> Divide all weights by largest weight. This won't do
	any harm to data that is already normalized, as it just
	divides everything by "1"! This is also what R and L did
	in their original study. [DONE]

2. Use standard weight of "k=0.0001" for regions that use projected
meter systems. This is the same as R and L did (although they used km as
their unit of distance measurements which meant "k=0.1").
Use standard weight of "k=0.000001?" for cost surface maps generated with
r.walk. [DONE]


3. Provide different functions for distance decay:

a. Linear (already DONE)
b. Exponential
c. Sigmoid-function: P(t)=(1)/(1+e^t)
	--> see Wikipedia entry on Sigmoid
	For our purposes : P(t)=( 1- (1)/(1+e^t) )


*** Open questions:


a) How to model the hierarchical relations of sites that form alliances?

b) How to choose "k" for regions that use lat-long and plain x/y systems?

c) what to do with "residual territories", i.e. territories still claimed by a site A that has been
taken over by another site B? Maybe allocate all territory that once belonged to A to B in a
second "clean-up" pass?




		
	
*/

#define LOCAL

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <time.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "globals.h"
#include "at_exit_funcs.h"
#include "gt_vector.h"
#include "xtent.h"
#include "tools.h"


/* variables global in main.c */
GVT_map_s *pmap;
double b_weight; /* weight for boundaries */
double p_weight; /* weight for pathways */
int *costf;
CELL *cell;
CELL *cell_second;
DCELL *dcell;
DCELL *dcell_boundaries;
DCELL **costdcell;
double *costs;
double *reach;
int *ruler;
double *max_cost;

char *boundaries_map;
char *pathways_map;

/* temporary map name strings */
char *cmapname; /* name of a cost map */
char *pseudomap; /* a pseudo friction map (all costs set to 1), used when only boundaries or pathways are supplied */



/* DEFINE FLAGS AND OPTIONS */
void define_opts ( int argc, char *argv[] ) {
	
	module = G_define_module ();
	module->description = "Calculate variations or original version of Renfrew and Level's Xtent model for territorial modeling.";
	module->label = "r.xtent: territorial modelling with boundaries and movement costs";
	module->keywords = _("raster,Xtent,territories,territorial analysis");
				
	/* vector map with centers (sites only or network) */
	parm.centers = G_define_standard_option (G_OPT_V_INPUT);
	parm.centers->key = "centers";
	parm.centers->type = TYPE_STRING;
	parm.centers->required = YES;
	parm.centers->description = _("Input map with vector points representing centers");
	parm.centers->guisection = _("Basic");

	/* Output map name */
	parm.output = G_define_standard_option(G_OPT_R_OUTPUT); 
	parm.output->key = "territories";
	parm.output->description = _("Output raster map showing territories");
	parm.output->guisection = _("Basic");	

	/* attribute that stores C for each center */
	parm.c = G_define_option ();
	parm.c->key = "c";
	parm.c->type = TYPE_STRING;
	parm.c->required = NO;
	parm.c->description = _("Double or integer attribute in 'centers' map with individual 'C' values");
	parm.c->guisection = _("Basic");	

	/* global a */
	parm.a = G_define_option ();
	parm.a->key = "a";
	parm.a->type = TYPE_DOUBLE;
	parm.a->required = YES;
	parm.a->answer = "0.5";
	parm.a->description = _("Global setting for 'a'");
	parm.a->guisection = _("Basic");	
	
	/* global k */
	parm.k = G_define_option ();
	parm.k->key = "k";
	parm.k->type = TYPE_DOUBLE;
	parm.k->required = NO;
	parm.k->description = _("Global setting for 'k'");
	parm.k->guisection = _("Basic");	

	/* cost surface attribute */
	parm.costs_att = G_define_option ();
	parm.costs_att->key = "costs_att";
	parm.costs_att->type = TYPE_STRING;
	parm.costs_att->required = NO;
	parm.costs_att->description = _("Text attribute in 'centers' map that stores names of raster cost maps");
	parm.costs_att->guisection = _("Basic");

	/* write ASCII report file? */
	parm.report = G_define_standard_option (G_OPT_F_OUTPUT);
	parm.report->key = "report";
	parm.report->type = TYPE_STRING;
	parm.report->required = NO;
	parm.report->description = _("Name of ASCII file to write report to");
	parm.report->guisection = _("Basic");
								
	/* impose I >= 0 restriction? */
	flag.strict = G_define_flag ();
	flag.strict->key = 's';
	flag.strict->description = _("Impose original restriction I >= 0");
	flag.strict->guisection = _("Basic");

	/* tabular format report file? */
	flag.tabular = G_define_flag ();
	flag.tabular->key = 't';
	flag.tabular->description = _("Tabular output format for report file");
	flag.tabular->guisection = _("Basic");

	parm.second = G_define_standard_option(G_OPT_R_OUTPUT);
	parm.second->key = "comp_id";
	parm.second->type = TYPE_STRING;
	parm.second->required = NO;
	parm.second->description = _("New raster map to store ID of strongest competitor");
	parm.second->guisection = _("Enhancements");
			
	/* Error map/attribute name */
	parm.errors = G_define_standard_option(G_OPT_R_OUTPUT);
	parm.errors->key = "comp_strength";
	parm.errors->type = TYPE_STRING;
	parm.errors->required = NO;
	parm.errors->description = _("New raster map to store strength of competitor");
	parm.errors->guisection = _("Enhancements");
	
	parm.maxdist = G_define_option ();
	parm.maxdist->key = "reach";
	parm.maxdist->type = TYPE_STRING;
	parm.maxdist->required = NO;
	parm.maxdist->description = _("Double attribute in 'centers' map for maximum distance/cost reach");
	parm.maxdist->guisection = _("Enhancements");
	
	parm.ruler = G_define_option ();
	parm.ruler->key = "ruler";
	parm.ruler->type = TYPE_STRING;
	parm.ruler->required = NO;
	parm.ruler->description = _("Integer attribute in 'centers' map that points to ID of ruling center");
	parm.ruler->guisection = _("Enhancements");
	
	#ifdef EXPERIMENTAL
	parm.ally = G_define_option ();
	parm.ally->key = "ally";
	parm.ally->type = TYPE_STRING;
	parm.ally->required = NO;
	parm.ally->description = _("Text attribute in 'centers' map with comma-separated list of ally IDs");
	parm.ally->guisection = _("Enhancements");
	#endif
	
	/* indexing attribute */
	parm.cats = G_define_option ();
	parm.cats->key = "categories";
	parm.cats->type = TYPE_STRING;
	parm.cats->required = NO;
	parm.cats->answer = "cat";
	parm.cats->description = _("Integer attribute in 'centers' map to use as output raster map categories");
	parm.cats->guisection = _("Mapping");	
	
	/* can be used to label raster categories (mode 'areas') or add a labeling attribute in mode 'sites'*/
	parm.labels = G_define_option ();
	parm.labels->key = "labels";
	parm.labels->type = TYPE_STRING;
	parm.labels->required = NO;
	parm.labels->description = _("Text attribute in 'centers' map for labeling output raster map categories");
	parm.labels->guisection = _("Mapping");		
	
	/* RGB colouring attribute */
	parm.rgbcol = G_define_option ();
	parm.rgbcol->key = "rgb_column";
	parm.rgbcol->type = TYPE_STRING;
	parm.rgbcol->required = NO;
	parm.rgbcol->answer = "GRASSRGB";
	parm.rgbcol->description = _("String attribute (RRR:GGG:BBB) in 'centers' map for category colors");
	parm.rgbcol->guisection = _("Mapping");		
	
	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	if (G_parser(argc, argv))
        	exit(-1);	

	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);	
	
}


/* check for valid combinations of parameters/options */
/* check for valid map and attribute names and types */
void check_params ( void ) {
	
	int num_specs;
	double k_val;
	

	/* enable verbosity, overwrite, progess display? */
	VERBOSE = 0;
	OVERWRITE = 0;
	PROGRESS = 1;
	if ( module->verbose ) {
		VERBOSE = 1;
	}
	if ( module->overwrite ) {
		OVERWRITE = 1;
	}

	/* stuff relating to report file writing */
	if ( flag.tabular->answer ) {
		if ( parm.report->answer == NULL ) {
			G_warning (_("-t flag only makes sense if option 'report=' is specified. Ignoring.\n"));
		}
	}

	/* 1. FORMULA PROPERTIES */	
	if ( (parm.errors->answer) && (parm.second->answer==NULL) ) {
		G_fatal_error (_("Mapping strength of competition requires providing a name for the 'competitor ID' map.\n"));
	}

	/* set appropriate value for k, if user did not provide one! */
	if ( parm.k->answer == NULL ) {
	
		G_warning (_("No value for k given. Will set a default value."));
	
		parm.k->answer = G_malloc ( sizeof (char) * 255 );
		k_val = 0.0001;
	
		/* lat-long system */
		if ( G_projection () == 3 ) {
			G_warning (_("You are working in a lat-long location. Appropriate value for 'k' depends on latitude."));
		} else {
			/* we assume a system based on meters */
			G_warning (_("Assuming meter-based coordinate system."));
		}

		if ( parm.costs_att->answer != NULL ) {
			G_warning (_("Using cost maps. Appropriate value for k depends on cost units."));
		}
		
		sprintf ( parm.k->answer, "%f", k_val);
		G_warning (_("Guessing k = %f. No guarantee this will work"), k_val);
	}
	
		
	/* 3. DISTANCE MODE */
	
	DISTANCE = STRAIGHT; /* default is to use a straight-line distance measure */
	COSTMODE = NONE;
	
	/* check if user specified more than one way of naming cost maps */
	if ( parm.costs_att->answer != NULL ) {
		num_specs ++;
		COSTMODE = ATTNAME;
		DISTANCE = COST;
	}	
}


/* write a report to an ASCII file on disk */
void write_report ( int *cats, char **labels, int argc, char *argv[] ) {		
	struct report_struct *report;
	FILE *fp;
	int error;
	int i,j;
	int fd_output, fd_second, fd_errors;
	long int total_cells;
	long int *competitor;
	long int max;
	
	char tmp [5000];
	
	time_t systime;
	clock_t proctime;
	unsigned long timeused;
	unsigned int days, hours, mins, secs;
	
	double sqdiff;
	
	struct Cell_head window;
	int row, col;
	int nrows, ncols;
	double east, north;
	
	int boss;


	G_get_window (&window);
	nrows = G_window_rows ();
	ncols = G_window_cols ();		
		
	fp = fopen ( parm.report->answer, "w+" );
	if ( fp == NULL ) {
		G_fatal_error ("Failed to open file '%s' for report writing.\n", parm.report->answer );
	}
	
	report = G_malloc ( num_centers * sizeof ( struct report_struct ) );
		
	fd_output = G_open_cell_old ( parm.output->answer, G_find_cell ( parm.output->answer, "" ) );
	
	fd_second = -1;	
	if ( parm.second->answer ) {
		fd_second = G_open_cell_old ( parm.second->answer, G_find_cell ( parm.second->answer, "" ) );
	}
	fd_errors = -1;
	if ( parm.errors->answer ) {
		fd_errors = G_open_cell_old ( parm.errors->answer, G_find_cell ( parm.errors->answer, "" ) );
	}
	
	if ( PROGRESS )
		G_message (_( "Writing report file to '%s':\n"), parm.report->answer);		

	/* alloc some counter arrays */
	competitor = G_malloc ( sizeof ( long int) * num_centers );

	/* make room for storing subjects */
	for ( i=0; i < num_centers; i ++ ) {
		report[i].num_subjects = 0;
		report[i].subject = G_malloc ( sizeof (int) * num_centers );
		report[i].subject_id = G_malloc ( sizeof (int) * num_centers );
		report[i].subject_name = G_malloc ( sizeof (char*) * num_centers );	
	}
	
	/* init area calculations */
	error = G_begin_cell_area_calculations ();
	
	/* get map statistics */	
	if ( PROGRESS )
		G_message (_("  Getting map statistics:\n" ));
	GVT_rewind ( pmap );
	i = 0;
	while ( GVT_next ( pmap ) ) {
		if ( error == 0 ) {
			/* area cannot be calculated in x/y locations */
			report[i].area = -1.0;
		} else {
			report[i].area = 0.0;
		}
		
		report[i].id = cats[i];
		if ( parm.labels->answer ) {
			report[i].name = strdup ( labels[i] );
		}
		
		/* get basic raster stats */
		report[i].out_count = 0;
		total_cells = 0;
		for (row=0; row < nrows; row ++) {
			G_get_c_raster_row ( fd_output, cell, row );
			for (col=0; col < ncols; col ++) {
				if ( !G_is_c_null_value ( &cell[col]) ) {
					if ( cell[col] == cats[i] ) {
							report[i].out_count ++;
							if ( error > 0 ) {
								/* update area stats */
								report[i].area = report[i].area + G_area_of_cell_at_row ( row );
							}
					}
					total_cells ++;
				}
			}
		}
		
		/* calculate area (km^2), percentage and maximum reach of this center's territory */
		report[i].area = report[i].area / 1000000;
		report[i].percentage =  ( ( (double) report[i].out_count / (double) total_cells) * 100.0 );
		report[i].max_cost = max_cost[i];

		/* get error stats */
		if ( parm.errors->answer ) {
			report[i].err_count = 0;
			report[i].err_sum = 0.0;
			for (row=0; row < nrows; row ++) {
				G_get_c_raster_row ( fd_output, cell, row );
				G_get_d_raster_row ( fd_errors, dcell, row );				
				for (col=0; col < ncols; col ++) {
					if ( !G_is_c_null_value ( &cell[col]) ) {
						if ( cell[col] == cats[i] ) {
								report[i].err_count ++;
								report[i].err_sum = report[i].err_sum + (double) dcell[col];
						}
					}
				}
			}
			report[i].err_avg = ((double) report[i].err_sum / report[i].err_count);
			
			/* now get error var and std */
			report[i].err_var = 0;
			report[i].err_std = 0.0;
			sqdiff = 0.0;
			for (row=0; row < nrows; row ++) {
				G_get_c_raster_row ( fd_output, cell, row );
				G_get_d_raster_row ( fd_errors, dcell, row );				
				for (col=0; col < ncols; col ++) {
					if ( !G_is_c_null_value ( &cell[col]) ) {
						if ( cell[col] == cats[i] ) {
							sqdiff = sqdiff + pow ( ((double) dcell[col] - (double) report[i].err_avg), 2.0 );
						}
					}
				}
			}
			report[i].err_var = (1.0 / (double) report[i].err_count) * sqdiff;
			report[i].err_std = sqrt ( report[i].err_var );			
		}
		
		/* get information about competitors (second highest I) */
		if ( parm.second->answer ) {
			
			/* initialize counters */
			for ( j=0; j < num_centers; j ++ ) {
				competitor[j] = 0;
			}
			report[i].aggressor = 0;
			
			for (row=0; row < nrows; row ++) {
				G_get_c_raster_row ( fd_output, cell, row );
				G_get_c_raster_row ( fd_second, cell_second, row );				
				for (col=0; col < ncols; col ++) {
					if ( !G_is_c_null_value ( &cell[col]) ) {
						if ( cell[col] == cats[i] ) { 
							/* we have a cell that belongs to the current center */
							
							/* which on is the most frequent competitor in current center's territory?
							 
							 * count frequencies for all centers in array of i counters
							 * we'll find the index of the largest counter when the raster map loop is done.
							 *
							 */							 
							 for (j=0; j < num_centers; j++) {
							 	if ( cats[j] == cell_second[col] ) {
							 		competitor [j] ++;
							 	}
							 }
						} else {
							/* we have a cell that is outside the current center's territory */
						
							/* how frequent is the current center second highest I in the territory of another?  */
							if ( cell_second[col] == cats[i] ) {
								/* just sum up and also calculate percentage (against number of cells in foreing territories) */
								report[i].aggressor ++;
							}
						}
					}
				}
			}
			
			/* find most frequent competitor */
			max = -1;
			report[i].competitor = 0;			
			report[i].competitor_id = cats[0];
			for ( j=1; j< num_centers; j ++ ) {
				if ( (competitor[j] > 0) && ( competitor[j] > max ) ) {
					max = competitor[j];
					report[i].competitor = j;
					report[i].competitor_id = cats[j];	
				}
			}
			
			/* no competitor found! */
			if ( max == -1 ) {
				report[i].competitor = -1;
			} else {
				/* get percentage */
				report[i].competitor_p = ((double) max / (double) report[i].out_count) * 100.0;
			}
			report[i].aggressor_p =  ( (double)report[i].aggressor / ((double)total_cells - (double)report[i].out_count) )  * 100.0; 
		}		
		
		if ( PROGRESS ) {
			G_percent (i, num_centers-1, 1);		}
		i ++;
	}
	
	/* now check for boss and/or subjects! */
		
	/* check the cell under each center. If it's not owned by the center, then that
	 * center is dominated by another and we need to store its ID.
	 */
	GVT_rewind ( pmap );
	i = 0;
	while ( GVT_next ( pmap ) ) {
		report[i].boss = -1;
		east = G_easting_to_col ( GVT_get_point_x ( pmap ), &window );
		north = G_northing_to_row ( GVT_get_point_y ( pmap ), &window );
		G_get_c_raster_row ( fd_output, cell, (int) north );
		boss = (CELL) cell[(int) east];
		if ( boss != cats[i] ) {
			/* this center is dominated by another center! Store that center's ID */
			for ( j=0; j < num_centers; j ++ ) {
				if ( cats[j] == boss ) {
					report[i].boss = j;								
					report[i].boss_id = boss;
					if ( parm.labels->answer ) {
						report[i].boss_name = strdup ( labels[j] );
					}
					/* also: append ID and name of this center to the bosse's list */
					report[j].subject[report[j].num_subjects] = i;
					report[j].subject_id[report[j].num_subjects] = cats[i];
					if ( parm.labels->answer ) {
						report[j].subject_name[report[j].num_subjects] = strdup ( labels[i] );			
					}
					report[j].num_subjects ++;
				}
			}
		}
		i++;		
	}
		
	/* write records to ASCII file */
	if ( PROGRESS )
		G_message (_( "  Writing individual records:\n" ));		
	GVT_rewind ( pmap );
	if ( flag.tabular->answer ) {
		/* header line for tabular report output */
		fprintf ( fp, "id\tname\trulerid\trname\tcells\tcellsp\tarea\treach" );
		if ( parm.second->answer ) {
			fprintf ( fp, "\taggressor\taggperc\tcompid\tcompname\tcompperc" );
		}
		if ( parm.errors->answer ) {
			fprintf ( fp, "\tstravg\tstrvar\tstrdev" );
		}
		fprintf ( fp, "\n" );
	}

	if ( !flag.tabular->answer ) {
		/* make a nice header */
		fprintf ( fp, "This is %s version %.2f\n", argv[0], PROGVERSION);
		systime = time (NULL);
		fprintf ( fp, "Calculation started on %s", ctime ( &systime ) );
		fprintf ( fp, "\tlocation   = %s\n", G_location() );
		fprintf ( fp, "\tmapset     = %s\n", G_mapset() );
		sprintf ( tmp, "%s ", argv[0]);
		for ( j=1; j < argc; j ++ ) {
			strcat ( tmp, argv[j] );
			if ( j < (argc - 1) ) {
				strcat ( tmp, " " );
			}
		}
		fprintf ( fp, "\tcommand    = %s\n\n", tmp );
		fprintf ( fp, "===\n\n" );
	}
	
	for ( i=0; i < num_centers; i++ ) {
		if ( flag.tabular->answer ) {
			/* tabular output: one line per center and always with complete fields */
			fprintf ( fp, "%i", report[i].id );
			if ( parm.labels->answer ) {
				fprintf ( fp, "\t%s", report[i].name );
			} else {
				fprintf ( fp, "\tn.a." );				
			}
			if ( report[i].boss > -1 ) {
				fprintf ( fp, "\t%i", report[i].boss_id );
				if ( parm.labels->answer ) {
					fprintf ( fp, "\t%s", report[i].boss_name );
				} else {
					fprintf ( fp, "\tn.a." );
				}
				fprintf ( fp, "\t0" );
				fprintf ( fp, "\t0.0" );
				fprintf ( fp, "\t0.0" );
				fprintf ( fp, "\t0.0" );				
			} else {
				fprintf ( fp, "\t%i", report[i].id );
				if ( parm.labels->answer ) {
					fprintf ( fp, "\t%s", report[i].name );
				} else {
					fprintf ( fp, "\tn.a." );
				}
				fprintf ( fp, "\t%li", report[i].out_count );
				fprintf ( fp, "\t%.3f", report[i].percentage );
				fprintf ( fp, "\t%.3f", report[i].area );
				fprintf ( fp, "\t%.3f", report[i].max_cost );										
			}
			if ( parm.second->answer ) {
				if (( report[i].aggressor > 0 ) && ( report[i].boss < 0 )) {
					fprintf ( fp, "\t%li", report[i].aggressor);
					fprintf ( fp, "\t%.3f", report[i].aggressor_p );
				} else {
					fprintf ( fp, "\t0" );
					fprintf ( fp, "\t0.0" );									
				}
				if (( report[i].competitor > -1 ) && ( report[report[i].competitor].boss != i ) && ( report[i].boss < 0 )) {
					fprintf ( fp, "\t%i", report[i].competitor_id);
					fprintf ( fp, "\t%s", labels[report[i].competitor]);
					fprintf ( fp, "\t%.3f", report[i].competitor_p );
				} else {
					fprintf ( fp, "\t0" );
					fprintf ( fp, "\tn.a." );
					fprintf ( fp, "\t0.0" );					
				}							
			}
			if ( parm.errors->answer ) {
				if (( report[i].competitor > -1 ) && ( report[report[i].competitor].boss != i ) && ( report[i].boss < 0 )) {
					fprintf ( fp, "\t%.3f", report[i].err_avg );
					fprintf ( fp, "\t%.3f", report[i].err_var );
					fprintf ( fp, "\t%.3f", report[i].err_std );								
				} else {
					fprintf ( fp, "\t0.0" );
					fprintf ( fp, "\t0.0" );
					fprintf ( fp, "\t0.0" );												
				}
			}					
			fprintf ( fp, "\n" ) ;
		} else {
			/* this is regular report format: one paragraph per center */
						
			/* write records to report file */
			fprintf ( fp, "(center %i of %i)\n", i + 1, num_centers ); 
			fprintf ( fp, "id:\t\t%i\n", report[i].id );
			if ( parm.labels->answer ) {
				fprintf ( fp, "name:\t\t%s\n", report[i].name );
			} else {
				fprintf ( fp, "name:\t\tn.a.\n" );				
			}
			if ( report[i].num_subjects > 0 ) {
				fprintf ( fp, "dominates:\t" );
				for ( j=0; j<report[i].num_subjects; j ++ ) {
					if ( parm.labels->answer ) {
						fprintf ( fp, "%i (%s)", report[i].subject_id[j], report[i].subject_name[j] );
					} else {
						fprintf ( fp, "%i", report[i].subject_id[j] );						
					}
					if ( j < (report[i].num_subjects-1) ) {
						fprintf ( fp, ", " );
					}
				}
				fprintf ( fp, "\n");
			} else {
				fprintf ( fp, "dominates:\tn.a.\n" );
			}
			if ( report[i].boss > -1 ) {
				if ( parm.labels->answer ) {
					fprintf ( fp, "dominated by:\t%i, %s\n", report[i].boss_id, report[i].boss_name );
				} else {
					fprintf ( fp, "dominated by:\t%i\n", report[i].boss_id );					
				}
			} else {
				fprintf ( fp, "dominated by:\tn.a.\n" );
				fprintf ( fp, "cells:\t\t%li (%.3f%%)\n", report[i].out_count, report[i].percentage );
				if ( report[i].area > -1.0 ) {
					fprintf ( fp, "area:\t\t%.3f sqkm\n", report[i].area );
				}
				if ( DISTANCE == COST ) {
					fprintf ( fp, "reach cost:\t%.3f cells\n", report[i].max_cost );
				} else {
					fprintf ( fp, "reach dist:\t%.3f km\n", report[i].max_cost / 1000 );
				}
			}
			if ( parm.second->answer ) {
				if (( report[i].aggressor > 0 ) && ( report[i].boss < 0 )) {
					fprintf ( fp,"aggressor:\t%li (%.3f%%)\n", report[i].aggressor, report[i].aggressor_p );
				} else {
					fprintf ( fp,"aggressor:\tn.a.\n" );				
				}
				if (( report[i].competitor > -1 ) && ( report[report[i].competitor].boss != i ) && ( report[i].boss < 0 )) {
					fprintf ( fp,"competitor:\t%i, %s (%.3f%%)\n", report[i].competitor_id, labels[report[i].competitor], report[i].competitor_p );
				} else {
					fprintf ( fp,"competitor:\tn.a.\n" );
				}
			}
			if ( parm.errors->answer ) {
				if (( report[i].competitor > -1 ) && ( report[report[i].competitor].boss != i ) && ( report[i].boss < 0 )) {
					fprintf ( fp, "strength avg:\t%.3f\n", report[i].err_avg );
					fprintf ( fp, "strength var:\t%.3f\n", report[i].err_var );
					fprintf ( fp, "strength std:\t%.3f\n", report[i].err_std );								
				} else {
					fprintf ( fp, "strength avg:\tn.a.\n" );
					fprintf ( fp, "strength var:\tn.a.\n" );
					fprintf ( fp, "strength std:\tn.a.\n" );												
				}
			}
			fprintf ( fp, "\n\n" );
			if ( PROGRESS ) {
				G_percent ( i, num_centers-1, 1 );			
			}					
		}
	}

	if ( !flag.tabular->answer ) {	
		/* write a nice footer */		
		/* write processing time to logfile */
		proctime = clock ();
		timeused = (unsigned long) proctime / CLOCKS_PER_SEC;
		days = timeused / 86400;
		hours = (timeused - (days * 86400)) / 3600;
		mins = (timeused - (days * 86400) - (hours * 3600)) / 60;		
		secs = (timeused - (days * 86400) - (hours * 3600) - (mins * 60));
		systime = time (NULL);
		fprintf ( fp, "===" );
		fprintf ( fp, "\n\nCalculation finished %s",ctime(&systime));		
		fprintf ( fp, "Processing time: %id, %ih, %im, %is\n",
				days, hours, mins, secs );				
		fflush ( fp );		
	}
	
	fclose ( fp );
	 
	/* TODO: also release invidual members of the report struct */
	G_free ( report );
	
	/* close output map(s) */
	G_close_cell ( fd_output );
	if ( parm.second->answer ) {
		G_close_cell ( fd_second );
	}
	if ( parm.errors->answer ) {
		G_close_cell ( fd_errors );
	}	
	
}

/* ================================================================================

				MAIN

===================================================================================*/
int main (int argc, char *argv[]) {

	int i,j;
	char tmp[5000];
		
	struct Cell_head window;
	int row, col;
	int nrows, ncols;
	double east, north;
	
	int fd, fd_temp, fd_error;
	int fd_second;
	int fd_boundaries;
	
	double x, y;
	double max_d;
	double max_c;
	double C_total;		
			
	/* for raster map categories, labels and colours */
	int *cats;
	char **labels;
	struct Categories pcats;
	char **rgb;
	int r,g,b;

	/* map history */
	struct History hist;
	
	/* color map rules */
	struct Colors *colors;
	DCELL *v1, *v2;
		
	int error;
	double diff;
	double max_diff;
	double dist;
	
	int valid_I;	/* this var is set to "1", if at least one cell was found to belong to the territory of any
					   any center in the input map. Its purpose is to guard against cases, where strict mode
					   is used (-s) and the model parameters are set badly, so that the user is presented
					   with an all NULL output map
					*/				
	int matched;
	int boss;
					
					
	define_opts ( argc, argv );

	G_get_window (&window);
    	nrows = G_window_rows ();
	ncols = G_window_cols ();	

	check_params ();
		
	GVT_init ();	
	pmap = GVT_new_map ( );
	GVT_open_map ( parm.centers->answer, GV_POINT , pmap );	
			
	a = atof ( parm.a->answer );
	k = atof ( parm.k->answer );
			
	C = G_malloc ( sizeof (double) * pmap->num_records );
	
	/* init file descriptors */
	fd_temp = -1;
	fd_second = -1;
	fd_boundaries = -1;	
	
	if ( parm.c->answer != NULL ) {
		/* check if C attribute exists */
		if ( GVT_any_exists ( parm.c->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading C attribute: '%s' does not exist in input vector map '%s'.\n"),
						parm.c->answer, parm.centers->answer );			
		}
		if ( GVT_numeric_exists ( parm.c->answer, pmap) == FALSE ) {
						G_fatal_error (_("Error reading C attribute: '%s' is not of type double or integer in input vector map '%s'.\n"),
						parm.c->answer, parm.centers->answer );
		}
		i = 0;
		GVT_rewind ( pmap );
		C_total = 0;
		while ( GVT_next ( pmap ) ) {
			C[i] = GVT_get_numeric ( parm.c->answer, pmap );			
			if ( DEBUG > 1 ) {
				G_message (_( " %i: C=%.f\n"), i, C[i]);
			}
			C_total = C_total + C[i];
			i ++;			
		}
		num_centers = i;
		
		/* normalize C attributes */
		C_norm = G_malloc ( sizeof (double) * num_centers );
		for ( i = 0; i < num_centers; i ++ ) {
			C_norm [i] = (double) C[i] / (double) C_total;
		}
		
	} else {
		/* we still need to know at least the number of centers (sites) in the input map! */
		num_centers = 0;
		GVT_rewind ( pmap );
		while ( GVT_next ( pmap ) ) {
			num_centers ++;
		}		
	}
		
  	
	/* if no attribute for C given: set it to 1.0 for each center */	
	if (parm.c->answer == NULL ) {
		G_warning (_("No C attribute specified. Assuming constant C=1.0.\n"));
		for ( i=0; i<pmap->num_records; i++) {
			C[i] = 1.0;
		}
	}

	cats = NULL;
	/* no categories attribute specified? create a new index starting at 1! */
	if ( parm.cats->answer == NULL ) {
		cats = G_malloc ( sizeof (int) * num_centers );
		for ( i = 0; i < num_centers; i ++ ) {
			cats[i] = i + 1;
		}
	}
	
	/* check if cats attribute exists and is of type integer */
	if ( parm.cats->answer != NULL ) {
		if ( GVT_any_exists ( parm.cats->answer, pmap) == FALSE ) {
			G_warning (_("Error reading categories attribute: '%s' does not exist in input vector map '%s'.\n"),
					parm.cats->answer, parm.centers->answer );
			cats = G_malloc ( sizeof (int) * num_centers );
			for ( i = 0; i < num_centers; i ++ ) {
				cats[i] = i + 1;
			}				
		} else {
		if ( GVT_int_exists ( parm.cats->answer, pmap) == FALSE ) {
				G_warning (_("Error reading categories attribute: '%s' is not of integer type in input vector map '%s'.\n"),
						parm.cats->answer, parm.centers->answer );
				cats = G_malloc ( sizeof (int) * num_centers );
				for ( i = 0; i < num_centers; i ++ ) {
					cats[i] = i + 1;
				}
			}
		}
		if ( GVT_int_exists ( parm.cats->answer, pmap) == TRUE ) {		
			/* categories label is cool, so let's read in all category values in input vector map */
			cats = G_malloc ( sizeof (int) * num_centers );
			GVT_rewind ( pmap );
			i = 0;
			while ( GVT_next ( pmap ) ) {
				cats[i] = GVT_get_int ( parm.cats->answer, pmap);
				i ++;
			}
		}
	}

	labels = NULL;
	/* labeling attribute? */
	if ( parm.labels->answer != NULL ) {
		if ( GVT_any_exists ( parm.labels->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading label attribute: '%s' does not exist in input vector map '%s'.\n"),
						parm.labels->answer, parm.centers->answer );			
		}		
		if ( GVT_string_exists ( parm.labels->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading label attribute: '%s' is not of text type in input vector map '%s'.\n"),
						parm.labels->answer, parm.centers->answer );
		}
	}
	
	colors = NULL;
	/* colouring attribute? */
	make_colors = 0;
	if ( parm.rgbcol->answer ) {
		if ( GVT_any_exists ( parm.rgbcol->answer, pmap) == FALSE ) {
				if ( strcmp ( parm.rgbcol->answer, "GRASSRGB" ) ) {
					G_warning (_("Colors attribute: '%s' does not exist in input vector map '%s'. Using default colors.\n"),
						parm.rgbcol->answer, parm.centers->answer );			
				}
		} else {	
			if ( GVT_string_exists ( parm.rgbcol->answer, pmap) == FALSE ) {
					G_warning (_("Colors attribute: '%s' is not of text type in input vector map '%s'. Using default colors.\n"),
							parm.rgbcol->answer, parm.centers->answer );
			}
		}
						
		if ( GVT_string_exists ( parm.rgbcol->answer, pmap) == TRUE ) {
		  /* colouring attribute is cool, so read in colours */
			rgb = G_malloc ( sizeof (char*) * num_centers );
			GVT_rewind ( pmap );
			i = 0;
			while ( GVT_next ( pmap ) ) {
				rgb[i] = GVT_get_string ( parm.rgbcol->answer, pmap);
				i ++;
			}
			make_colors = 1;
		}
	}
	
	/* allocate an array of center reaches (max cost/dist from a center to claim a cell) */
	reach = G_malloc ( sizeof (double) * pmap->num_records );
	for ( i=0; i < num_centers; i ++ ) {
		reach[i] = -1.0; /* set all centers to unconstrained reach by default */
	}
	
	/* maximum cost/distance attribute specified ? */
	if ( parm.maxdist->answer ) {
		/* check for valid attribute */
		if ( GVT_any_exists ( parm.maxdist->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading max reach attribute: '%s' does not exist in input vector map '%s'.\n"),
								parm.maxdist->answer, parm.centers->answer );
		}
		if ( GVT_double_exists ( parm.maxdist->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading max reach attribute: '%s' exists in input vector map '%s' but is not of type double.\n"),
								parm.maxdist->answer, parm.centers->answer );
		}
		/* read in all reach values */
		i = 0;
		GVT_rewind ( pmap );
		while ( GVT_next ( pmap ) ) {
			reach[i] = GVT_get_double ( parm.maxdist->answer, pmap );
			i ++;
		}
	}

	/* allocate an array of ruler pointers */
	ruler = G_malloc ( sizeof (int) * pmap->num_records );
	for ( i=0; i < num_centers; i ++ ) {
		ruler[i] = i; /* set all centers to be their own rulers by default */
	}
	
	/* ruler attribute specified ? */
	if ( parm.ruler->answer ) {
		/* check for valid attribute */
		if ( GVT_any_exists ( parm.ruler->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading ruler attribute: '%s' does not exist in input vector map '%s'.\n"),
								parm.ruler->answer, parm.centers->answer );
		}
		if ( GVT_int_exists ( parm.ruler->answer, pmap) == FALSE ) {
				G_fatal_error (_("Error reading ruler attribute: '%s' exists in input vector map '%s' but is not of type integer.\n"),
								parm.ruler->answer, parm.centers->answer );
		}
		/* read in all reach values */
		i = 0;
		GVT_rewind ( pmap );
		while ( GVT_next ( pmap ) ) {
			ruler[i] = GVT_get_int ( parm.ruler->answer, pmap );
			i ++;
		}
		/* now translate the category IDs to the sequential IDs in pmap */
		for ( i=0; i < num_centers; i ++ ) {
			matched = 0;
			for ( j=0; j < num_centers; j ++ ) {
				if ( cats[j] == ruler[i] ) {
					ruler[i] = j;
					matched = 1;
				}
			}
			if ( matched == 0 ) {
				G_fatal_error (_("Ruler ID in record no. %i in input map '%s' points to a non-existing record.\n"),
									i+1, parm.centers->answer );
			}
		}
	}
	
	/* register an AT EXIT function that will make sure temp maps
	 * get deleted
	 */
	atexit ( clean_tmpfiles );	
		
	/* cost surface mode? check for valid maps or create them ad hoc !!! */
	if ( DISTANCE == COST ) {
		
		make_pseudo = 0;
				
		if ( COSTMODE == ATTNAME ) { /* User has specified an attribute name for cost surfaces */
			/* check if map name attribute exists */
			if ( GVT_any_exists ( parm.costs_att->answer, pmap) == FALSE ) {
					G_fatal_error (_("Error reading map name attribute: '%s' does not exist in input vector map '%s'.\n"),
									parm.costs_att->answer, parm.centers->answer );			
			}
			if ( GVT_string_exists ( parm.costs_att->answer, pmap) == FALSE ) {
					G_fatal_error (_("Error reading map name attribute: '%s' is not of string type in input vector map '%s'.\n"),
									parm.costs_att->answer, parm.centers->answer );
			}
			/* allocate mem for pointers to cost maps and open all maps */
			costf = G_calloc ( (unsigned) num_centers, sizeof (int));
			GVT_rewind ( pmap );			
			i = 0;
			while ( GVT_next ( pmap ) ) {
				cmapname = GVT_get_string ( parm.costs_att->answer, pmap );
				costf[i] = G_open_cell_old ( cmapname, G_find_cell ( cmapname, "" ) );
				if ( costf[i] < 0 ) {
					G_fatal_error (_("Error opening cost surface raster '%s').\n"),cmapname);
				}
				i ++;
				G_free ( cmapname );
			}		
			/* allocate mem for raster map buffers to read data from cost maps */
			costdcell = G_calloc ( (unsigned) num_centers, sizeof (DCELL*) );
			for ( i = 0; i < num_centers; i++ ) {
				costdcell[i] = G_allocate_d_raster_buf();
			}
			/* allocate an array of doubles for storing cost values */
			costs = G_calloc ( (unsigned) num_centers, sizeof (double));
		}		
	}

	/*
	 * CALCULATE XTENT MODEL
	 */

	if ( PROGRESS )
		G_message (_("Calculating Xtent model for %i centers:\n"), num_centers);
	
	valid_I = 0;
	
	/* this globally tracks the maximum distance to each center from within
	 * any cell in its territory. We may need this for report writing later
	 */
	max_cost = G_malloc ( num_centers * sizeof ( double ) );
	for ( i = 0; i < num_centers; i ++ ) {
		max_cost[i] = -1.0;
	}
	
	cell = G_allocate_c_raster_buf();		
	fd = G_open_cell_new ( parm.output->answer );
	if ( fd < 0 ) {
		G_fatal_error (_("Could not open output map %s for writing.\n"), parm.output->answer);
	}
	
	/* also output a map of "second best" centers?*/
	if ( parm.second->answer != NULL ) {
		cell_second = G_allocate_c_raster_buf();
		fd_second = G_open_cell_new ( parm.second->answer );
		if ( fd_second < 0 ) {
			G_fatal_error (_("Could not open 'second highest I' map %s for writing.\n"), parm.second->answer);
		}
	}
	
	/* also output a map of error probability ? */
	if ( parm.errors->answer != NULL ) {
		/* for now, we'll just create a temporary map to store the
		 * unnormalized error
		 */
		temapname = mktmpmap ( "XTENTtmp" );
		dcell = G_allocate_d_raster_buf();
		G_set_fp_type(DCELL_TYPE);
		fd_temp = G_open_fp_cell_new ( temapname );
		if ( fd_temp < 0 ) {
			G_fatal_error (_("Could not open temporary error map %s for writing.\n"), temapname );
		}
		make_error = 1;
	}
		
	max_c = 1;
	max_d = 1;
			
	/* write a raster map with an I value for each cell */
	if ( PROGRESS )
		G_message (_(" Calculating I values for all cells in region:\n"));		
	for (row=0; row < nrows; row ++) {
		G_set_c_null_value ( cell, ncols );
		if ( parm.errors->answer != NULL ) {
			G_set_d_null_value ( dcell, ncols );
		}
		if ( DISTANCE == COST ) {
			/* if we have cost surfaces, we need to read one row from each map */
			for ( i = 0; i < num_centers; i++ ) {
				G_get_d_raster_row ( costf[i], costdcell[i], row );
			}
		}
		y = G_row_to_northing ( (double) row, &window );
		for (col=0; col < ncols; col ++) {
			if ( DISTANCE == COST ) {
				/* if we have cost surfaces, we need to read the cost value for each center in this column */
				for ( i = 0; i < num_centers; i++ ) {
					costs[i] = (double) costdcell[i][col];
				}										
			}
			x = G_col_to_easting ( (double) col, &window );
			
			/* calculate XTENT value I at current coordinates */
			if ( parm.c->answer != NULL ) {			
				I = get_center_xtent_original ( x, y, C_norm, a, k, costs, reach, ruler, pmap );
			} else {
				I = get_center_xtent_original ( x, y, C, a, k, costs, reach, ruler, pmap );
			}
				
			/* update max cost value for this center if necessary */
			if ( I >= 0 ) {
				if ( DISTANCE == COST ) {
					if ( max_cost[I] < costs[I] ) {
						if ( !G_is_d_null_value ( (DCELL*) &costs[I] ) ) {
							max_cost[I] = costs[I];
						}
					}
				}
				if ( DISTANCE == STRAIGHT ) {
					dist = GVT_get_2D_point_distance ( x, y, pmap );
					if ( dist > max_cost[I] ) {
						max_cost[I] = dist;
					}
				}
			}
				
			if ( I < 0 ) {
				/* this can only happen if there is an error calculating I or strict mode is turned on */
				/* otherwise, the return value of I will be the INDEX of the dominant center ! */
				G_set_c_null_value ( &cell[col], 1 );
			} else {
				cell[col] = (CELL) cats[I];
			}
				
			/* this signals that the model has managed to produce at least one center index ;) */				
			if ( (!G_is_c_null_value ( &cell[col] )) && ( I >= 0 ) ) {
				valid_I = 1;
			}				
				
			/* if one of the cost surfaces has a NULL value here, we will copy it thru, as well! */
			if ( DISTANCE == COST ) {
				for ( i = 0; i < num_centers; i++ ) {
					if ( G_is_d_null_value (&costdcell[i][col])) {
						G_set_c_null_value ( &cell[col], 1 );
					}
				}
			}
		}
		
		G_put_map_row ( fd, cell );
		
		if ( PROGRESS ) {
			G_percent (row, (nrows-1), 2);
		}
	}

	/* close basic output map for now */
	G_close_cell ( fd );

	/* Now we make a second pass to find the strongest competitor for each cell.
	 * This code is full of redundant terminology. The following are all
	 * basically the same: second I, second biggest I, competitor
	 * 
	 * The competitor is the center which would have claimed a cell if another,
	 * more dominant center had not taken it. The difference between the influences
	 * of the dominant center and the competitor is stored in the 'errors' map.
	 * It can be interpreted both as the strength of competition and the likelihood
	 * of making an error when claiming that a specific cell is in the territory of
	 * center A rather then B.
	 * 
	 * The error (= competition strength) measure is normalized in another pass after this loop.
	 * 
	 */
	 max_diff = 0;
	if ( parm.second->answer ) {
		
		/* re-open basic output map */
		fd = G_open_cell_old ( parm.output->answer, G_find_cell ( parm.output->answer, "" ) );
		
		if ( PROGRESS )
			G_message ( " Finding competitors for all cells in region:\n");
			
		/* If center A is dominated by center B, then it can no longer be a competitor of center B !
	 	* So we need to first identify all such situations and update the 'ruler' array accordingly.
	 	*/
		GVT_rewind ( pmap );
		i = 0;
		while ( GVT_next ( pmap ) ) {
			east = G_easting_to_col ( GVT_get_point_x ( pmap ), &window );
			north = G_northing_to_row ( GVT_get_point_y ( pmap ), &window );
			G_get_c_raster_row ( fd, cell, (int) north );
			boss = (CELL) cell[(int) east];
			if ( boss != cats[i] ) {
				/* this center is dominated by another center! Store that center's ID */
				for ( j=0; j < num_centers; j ++ ) {
					if ( cats[j] == boss ) {
						ruler[i] = j;
					}
				}
			}
			i++;		
		}
	 				
		for (row=0; row < nrows; row ++) {
			
			/* initialize error map to be all NULL cells */
			if ( parm.errors->answer != NULL ) {
				G_set_d_null_value ( dcell, ncols );
			}
			
			if ( DISTANCE == COST ) {
				/* if we have cost surfaces, we need to read one row from each map */
				for ( i = 0; i < num_centers; i++ ) {
					G_get_d_raster_row ( costf[i], costdcell[i], row );
				}
			}
			
			y = G_row_to_northing ( (double) row, &window );
			
			for (col=0; col < ncols; col ++) {
				if ( DISTANCE == COST ) {
					/* if we have cost surfaces, we need to read the cost value for each center in this column */
					for ( i = 0; i < num_centers; i++ ) {
						costs[i] = (double) costdcell[i][col];
					}										
				}
				x = G_col_to_easting ( (double) col, &window );
							
				/* get second highest I */
				if ( parm.second->answer ) {
					if ( parm.c->answer != NULL ) {
						I_second = get_center_xtent_second ( x, y, C_norm, a, k, &diff, costs, ruler, pmap );
					} else {
						I_second = get_center_xtent_second ( x, y, C, a, k, &diff, costs, ruler, pmap );
					}
					if ( diff > max_diff ) {
						max_diff = diff;
					}				
				}						

				if ( G_is_c_null_value ( &cell[col] ) ) { 
					/* if I map has a NULL val here, we need to copy it through */
					/* because by definition: if I is invalid, then so is 'second I' (competitor) */
					G_set_c_null_value ( &cell_second[col], 1 );
					if ( parm.errors->answer != NULL ) {
						G_set_d_null_value ( &dcell[col], 1 );
					}
				} else {
					/* if not, we set the current cell to the second biggest I (=ID of competitor) */
					cell_second[col] = (CELL) cats[I_second];
					if ( parm.errors->answer != NULL ) {
						/* at this point: just store the unnormalized strength of competition 
						 * We will make a second pass later of the 'errors' map to normalize this measure
						 */
						dcell[col] = diff;
					}
				}
					
				/* a competitor and competitor's strength (error) can only be calculated where at least
				 * two territories overlap!
				 */
				if ( I_second < 0 ) {
					/* this can only happen if there is an error calculating second I or strict mode is turned on */
					/* otherwise, the return value of I will be the ID of the second most dominant center
					 * as set above */
					G_set_c_null_value ( &cell_second[col], 1 );
					if ( parm.errors->answer != NULL ) {
						G_set_d_null_value ( &dcell[col], 1 );
					}						
				}
								
				/* if one of the cost surfaces has a NULL value here, we will copy it thru, as well! */
				if ( DISTANCE == COST ) {
					for ( i = 0; i < num_centers; i++ ) {
						if ( G_is_d_null_value (&costdcell[i][col])) {
							G_set_c_null_value ( &cell_second[col], 1 );
							if ( parm.errors->answer != NULL ) {
								/* also: copy thru to error map! */
								G_set_d_null_value ( &dcell[col], 1 );
							}
						}
					}
				}
			}
			
			G_put_map_row ( fd_second, cell_second );
			
			if ( parm.errors->answer != NULL ) {
				G_put_d_raster_row ( fd_temp, dcell );
			}
			
			if ( PROGRESS ) {
				G_percent (row, (nrows-1), 2);
			}
		}
		
		G_close_cell ( fd );
		G_close_cell ( fd_second );
	}
			
	/* Normalize values in error output map ! */
	if ( parm.errors->answer != NULL ) {
		/* we need to make a second pass and normalize the error
		 * measuere over the whole error map
		 */
		
		/* close and re-open the (temporary ) error map */
		G_close_cell ( fd_temp );
		fd_temp = G_open_cell_old ( temapname, G_find_cell ( temapname, "" ) );
		if ( fd_temp < 0 ) {
			G_fatal_error (_("Could not open temporary error map %s for reading.\n"), temapname );
		}
				
		/* create the new final (normalized) error map for writing */
		G_set_fp_type(DCELL_TYPE);
		fd_error = G_open_fp_cell_new ( parm.errors->answer );
		if ( fd_error < 0 ) {
			G_fatal_error (_("Could not open error map %s for writing.\n"), parm.errors->answer );
		}
		
		if ( max_diff == 0 ) { /* protect against extreme cases and divisio by zero */
			G_warning (_("The maximum difference between I and second highest I in your map is 0.\n"));
			if ( PROGRESS )
				G_message (_( " Setting all error measures to 1.0:\n"));			
			for (row=0; row < nrows; row ++) {
				G_get_d_raster_row ( fd_temp, dcell, row );
				for (col=0; col < ncols; col ++) {
					if ( !G_is_d_null_value ( &dcell[col]) ) {
							dcell[col] = 1.0;
					}
				}
				G_put_d_raster_row ( fd_error, dcell );		
				if ( PROGRESS ) {
					G_percent (row, (nrows-1), 2);				}
			}			
		} else {
			if ( PROGRESS )
				G_message ( " Normalizing error measures:\n");
			for (row=0; row < nrows; row ++) {
				G_get_d_raster_row ( fd_temp, dcell, row );
				for (col=0; col < ncols; col ++) {
					if ( !G_is_d_null_value ( &dcell[col]) ) {
							/* this is the normalized error measure:
							 * the closer to "1", the higher the risk of error
							 */
							dcell[col] = 1 - dcell[col] / max_diff;
					}
				}
				G_put_d_raster_row ( fd_error, dcell );		
				if ( PROGRESS ) {
					G_percent (row, (nrows-1), 2);				}
			}
		}
		
		/* close raster maps */
		G_close_cell ( fd_error );		
		G_close_cell ( fd_temp );
		
		/* make a nice gray-shade color table for output map */
		colors = G_malloc ( sizeof (struct Colors));
		G_init_colors ( colors );
		v1 = (DCELL*) G_malloc (sizeof (DCELL));
		v2 = (DCELL*) G_malloc (sizeof (DCELL));
		*v1 = 1.0; *v2 = 0.0;
		G_add_d_raster_color_rule ( v1,0,0,0,v2,255,255,255, colors );			
		G_write_colors ( parm.errors->answer, G_mapset (), colors );
	}
	
	if ( parm.labels->answer ) {
		G_init_cats ( num_centers, "Name of dominant center", &pcats );
		/* write map labels */
		labels = G_malloc ( num_centers * sizeof (char* ) );
		GVT_rewind ( pmap ); i = 0;
		while ( GVT_next ( pmap ) ) {
			labels[i] = GVT_get_string ( parm.labels->answer, pmap );
			i ++;
		}
		/* add labels to output map categories */
		error = 0;
		for ( i=0; i < num_centers; i ++ ) {
			error = G_set_cat ( cats[i], labels[i], &pcats );
			if ( error == -1 ) {
				G_warning (_("Error writing category label '%s': too many categories.\n"), labels[i] );
			}
			if ( error == 0 ) {
					G_warning (_("Error writing category label '%s': got NULL category.\n"), labels[i] );			
			}			
		}
		if ( error == 1 ) {	
			error = G_write_cats ( parm.output->answer, &pcats );
			if ( error != 1 ) {
				G_warning (_("Error writing categories for output map '%s'.\n"), parm.output->answer );
			}
			if ( parm.second->answer ) {
				error = G_write_cats ( parm.second->answer, &pcats );
				if ( error != 1 ) {
					G_warning (_("Error writing categories for 'second highest I' map '%s'.\n"), parm.second->answer );
				}
			}			
		}
		G_free_cats ( &pcats );
	}	
			
	/* write raster map history */
	G_short_history ( parm.output->answer, "raster", &hist );
	sprintf ( hist.title, "XTENT: ID of center with highest local I" );
	error = G_write_history (parm.output->answer, &hist);
	if ( error == -1 ) {
		G_warning (_("Could not write history file for output raster map '%s'.\n"), parm.output->answer );
	}
	
	if ( parm.second->answer ) {
		G_short_history ( parm.second->answer, "raster", &hist );
		G_command_history ( &hist );
		sprintf ( hist.title, "XTENT: ID of center with second highest local I" );		
		error = G_write_history (parm.second->answer, &hist);
		if ( error == -1 ) {
			G_warning (_("Could not write history file for 'competitor ID' raster map '%s'.\n"), parm.second->answer );
		}
	}

	if ( parm.errors->answer ) {
		G_short_history ( parm.errors->answer, "raster", &hist );
		G_command_history ( &hist );
		sprintf ( hist.title, "XTENT: competition strength" );		
		error = G_write_history (parm.errors->answer, &hist);
		if ( error == -1 ) {
			G_warning (_("Could not write history file for 'errors' raster map '%s'.\n"), parm.errors->answer );
		}
	}	

	
	/* make colour map for output maps if RGB attribute given */
	if ( make_colors ) {
		if ( parm.errors->answer == NULL ) {
			/* we don't have a color table yet, because there is no error map */
			colors = G_malloc ( sizeof (struct Colors));
		}
		G_init_colors ( colors );
		GVT_rewind ( pmap );
		i = 0;
		while ( GVT_next ( pmap ) ) {
			if ( sscanf ( GVT_get_string ( parm.rgbcol->answer, pmap),"%i:%i:%i", &r, &g, &b ) != 3 ) {
				G_warning ( "Malformed RGB attribute string in record no. %i.\n", i + 1 );
			} else {
				G_set_color ( (CELL) cats[i], r, g, b, colors );
			}
			i ++;
		}
		G_write_colors ( parm.output->answer, G_mapset (), colors );
		if ( parm.second->answer ) {
			G_write_colors ( parm.second->answer, G_mapset (), colors );
		}		
	}

	/* if user requested a report file to be written: do so now! */
	if ( parm.report->answer ) {
		write_report ( cats, labels, argc, argv );
	}
	
	/* warn, if model output is entirely empty! */
	if ( flag.strict->answer ) {
		if ( valid_I == 0 ) {
			G_warning ("All cells in output map are NULL. You need to adjust your model parameters (C,a,k) or do not run in 'strict' mode.\n");
		}
	}
	
	/* TODO: free colors struct */
	
	/* free cell handles */
	G_free ( cell );
	if ( parm.second->answer ) {
		G_free ( cell_second );
	}
	if ( parm.errors->answer ) {
		G_free ( dcell );
	}
	
	/* free other arrays */
	G_free ( cats );
	
	/* close input vector map 'centers' */
	GVT_close_map ( pmap );		
	GVT_free_map ( pmap );
					
	/* THAT'S IT, FOLKS! */	
	if ( PROGRESS ) {
		G_message ("\nJOB DONE.\n");
	}
								
	return (0);
}
