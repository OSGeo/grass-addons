/*

 MODULE:       v.in.geplot

 AUTHOR:       Benjamin Ducke

 PURPOSE:      Import Geoplot 3 data into a GRASS vector map.

 COPYRIGHT:    (c) 2009 Benjamin Ducke
 	       benjamin.ducke@oadigital.net

               This program is free software under the GNU General Public
               License (>=v2). Read the file COPYING that comes with GRASS
               for details.

*/

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <sys/types.h>
#include <unistd.h>

#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>

#define PROGVERSION 1.0

extern int errno;
int cachesize;

int debug_mode = 0;		/* 1 to enable writing debug output to logfile */


void read_data ( char *input, char *output, char *format, char *delim, 
		 char *cref, char *_xref, char *_yref,
		 char *_xinc, char *_yinc, 
		 char *_len, char *_null, int quiet) {
	FILE *fp;
	int i,k;
	int matches;
	struct Cell_head region;
	
	char data [2048];

	struct Map_info out_vect_map;
  	struct line_pnts *vect_points;
	struct line_cats *vect_cats;

	float x,y,z;
	double xd, yd, zd;
	
	dbString sql;
	dbDriver *driver;
	struct field_info *f;
	char   buf[2048];
	
	double xref;
	double yref;
	double xinc;
	double yinc;
	double len;
	float null = 0.0;
	
	int null_data;
		
	/* convert arguments */
	xref = atof ( _xref );
	yref = atof ( _yref );
	if ( _xinc != NULL ) {
		if ( !strcmp ( format, "z" ) ) {
			G_fatal_error ("Option 'xincrement=' is required for Z format input file.\n");
		}
		xinc = atof ( _xinc );
	}	
	if ( _yinc != NULL ) {
		if ( !strcmp ( format, "z" ) ) {
			G_fatal_error ("Option 'yincrement=' is required for Z format input file.\n");
		}	
		yinc = atof ( _yinc );
	}
	if ( _len != NULL ) {
		if ( !strcmp ( format, "z" ) ) {
			G_fatal_error ("Option 'length=' is required for Z format input file.\n");
		}
		len = atof ( _len );
	}
	if ( _null != NULL ) {
		null = (float) atof ( _null );
	}
				
	/* get current region */
	G_get_window (&region);
		
	/* attempt to create new file for output */
	Vect_set_open_level (2);
	if (0 > Vect_open_new (&out_vect_map, output, 0) ) {
		G_fatal_error ("Could not open output vector map.\n");
	}

	/* open input ASCII file */  	
	if ( quiet != 1 ) {
		fprintf (stderr,"Analysing input file..." );
	}
	
	fp = fopen ( input, "r");
	if ( fp == NULL ) {
		fprintf ( stdout, "\n" );
		fflush ( stdout );
		G_fatal_error ("Error opening input file: %s\n", strerror ( errno ));
	}
	
	/* get total number of data points and null data points */
	k = 0;
	null_data = 0;
	while ( fgets ( data, 2048, fp) != NULL ) {
		k ++;
		matches = 0;
		if (!strcmp ( format, "xyz" ) ) {
			if ( !strcmp ( delim, "tab" ) ) {
				matches = sscanf ( data, "%f\t%f\t%f", &x, &y, &z );
			}
			if ( !strcmp ( delim, "space" ) ) {
				matches = sscanf ( data, "%f %f %f", &x, &y, &z );
			}
			if ( !strcmp ( delim, "comma" ) ) {
				matches = sscanf ( data, "%f,%f,%f", &x, &y, &z );
			}
			if ( matches < 3 ) {
				fprintf ( stdout, "\n" );
				fflush ( stdout );
				G_warning ("Got only %i data items on line %i, expected 3.\n"
						, matches,  k);
				continue;
			}
			xd = (double) x;
			yd = (double) y;
			zd = (double) z;
		}
		if ( !strcmp ( format, "z" ) ) {
			matches = sscanf ( data, "%f", &z );
			if ( matches < 1 ) {
				fprintf ( stdout, "\n" );
				fflush ( stdout );
				G_warning ("Got no data on line %i.\n", k);
				continue;
			}
			zd = (double) z;
		}
		
		if ( _null != NULL ) {
			if ( zd == null ) {
				null_data ++;
			}
		}
	}
	
	if ( k < 1 ) {
		fprintf ( stdout, "\n" );
		fflush ( stdout );	
		G_fatal_error ("No lines in input file.\n");
	}
	
	if ( quiet != 1 ) {
		fprintf ( stdout, "\n" );
		fflush ( stdout );	
		fprintf (stderr,"Reading data and writing %i vector points...", k - (null_data) );
	}
	
	rewind ( fp );	
	
	vect_points = Vect_new_line_struct ();
	
	/* create new field to store nT readings */
	vect_cats = Vect_new_cats_struct ();
	db_init_string ( &sql );
      	Vect_hist_command ( &out_vect_map );
      	f = Vect_default_field_info ( &out_vect_map, 1, NULL, GV_1TABLE );
	Vect_map_add_dblink ( &out_vect_map, 1, NULL, f->table, "cat", f->database, f->driver);
      	
	db_zero_string (&sql);
      	sprintf ( buf, "create table %s ( ", f->table );
      	db_append_string ( &sql, buf);
      	db_append_string ( &sql, "cat integer" );
      	db_append_string ( &sql, ", nt double precision" );
      	db_append_string ( &sql, ", x double precision" );	
      	db_append_string ( &sql, ", y double precision" );		
      	db_append_string ( &sql, ")" );
      	G_debug ( 1, db_get_string ( &sql ) );
      	
	driver = db_start_driver_open_database ( f->driver, f->database );
      	if ( driver == NULL ) {
		fprintf ( stdout, "\n" );
		fflush ( stdout );	
      		G_fatal_error ( "Cannot open database %s by driver %s", f->database,f->driver );
	}

      	if (db_execute_immediate (driver, &sql) != DB_OK ) {
              	db_close_database(driver);
              	db_shutdown_driver(driver);
	      	fprintf ( stdout, "\n" );
		fflush ( stdout );
              	G_fatal_error ( "Cannot create table: %s", db_get_string ( &sql )  );
      	}
	

	/* while !EOF */
	i = 0;
	while ( fgets ( data, 2048, fp) != NULL ) {
		i ++;
		/* build point */
		x = 0.0;
		y = 0.0;
		z = 0.0;
		matches = 0;
		if ( !strcmp ( format, "xyz" ) ) {
			if ( !strcmp ( delim, "tab" ) ) {
				matches = sscanf ( data, "%f\t%f\t%f", &x, &y, &z );
			}
			if ( !strcmp ( delim, "space" ) ) {
				matches = sscanf ( data, "%f %f %f", &x, &y, &z );
			}
			if ( !strcmp ( delim, "comma" ) ) {
				matches = sscanf ( data, "%f,%f,%f", &x, &y, &z );
			}
			if ( matches < 3 ) {
				fprintf ( stdout, "\n" );
				fflush ( stdout );
				G_warning ("Got only %i data items on line %i, expected 3.\n"
						, matches, i + 1);
				continue;
			}
			xd = (double) x;
			yd = (double) y;
		}

		if ( !strcmp ( format, "z" ) ) {
			/* create coordinates */
			xd = 0.0;
			yd = 0.0;
			
			matches = sscanf ( data, "%f", &z );
			if ( matches < 1 ) {
				fprintf ( stdout, "\n" );
				fflush ( stdout );
				G_warning ("Got no data on line %i.\n", i+1);
				continue;
			}	
		}		
		
		zd = (double) z;
		Vect_copy_xyz_to_pnts (vect_points, &xd, &yd, NULL, 1);
		
		Vect_reset_line ( vect_points );
		Vect_reset_cats ( vect_cats );
		
		Vect_cat_set ( vect_cats, 1, i );
		
		/* filter out NULL data points if user wants it so */
		if ( _null != NULL ) {
			if ( zd != null ) {
				Vect_write_line (&out_vect_map, GV_POINT, vect_points, vect_cats );
				
				/* write nT value and coords into attribute table */
				db_zero_string ( &sql );
				sprintf (buf, "insert into %s values ( %d ", f->table, i );
				db_append_string ( &sql, buf);
				sprintf (buf, ", %f, %f, %f", zd, xd, yd );
				db_append_string ( &sql, buf);
				db_append_string ( &sql, ")" );
				G_debug ( 3, db_get_string ( &sql ) );

				if (db_execute_immediate (driver, &sql) != DB_OK ) {
        				db_close_database(driver);
        				db_shutdown_driver(driver);
					fprintf ( stdout, "\n" );
					fflush ( stdout );
        				G_fatal_error ( "Cannot insert new row: %s", db_get_string ( &sql ));
				}
			}
		} else {
			Vect_write_line (&out_vect_map, GV_POINT, vect_points, vect_cats );
			/* write nT value into attribute table */
			db_zero_string ( &sql );
			sprintf (buf, "insert into %s values ( %d ", f->table, i );
			db_append_string ( &sql, buf);
			sprintf (buf, ", %f", zd );
			db_append_string ( &sql, buf);
			db_append_string ( &sql, ")" );
			G_debug ( 3, db_get_string ( &sql ) );

			if (db_execute_immediate (driver, &sql) != DB_OK ) {
       				db_close_database(driver);
       				db_shutdown_driver(driver);
				fprintf ( stdout, "\n" );
				fflush ( stdout );
       				G_fatal_error ( "Cannot insert new row: %s", db_get_string ( &sql ));
			}			
		}
	

	
		if ( quiet != 1 ) {
			G_percent(i,k,1);
		}
	}
	/* END OF MAIN LOOP */
	/* need to create new header ? */
	/* Vect_copy_head_data (&in_vect_map, &out_vect_map); */
	
	if ( quiet != 1 ) {
		fflush ( stdout );
		fprintf (stdout, "Building topology for output map...");
	}
	
	db_close_database_shutdown_driver ( driver );

	Vect_build (&out_vect_map);
	Vect_close (&out_vect_map);
	
	if ( quiet != 1 ) {
		fprintf ( stdout, "\n" );
		fflush ( stdout );
		fprintf ( stdout, "DONE.\n" );
	}
}


int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *input; /* name of input ASCII file */
		struct Option *output; /* name of output vector map */
		struct Option *format;
		struct Option *delim;
		struct Option *cref;
		struct Option *xref;
		struct Option *yref;
		struct Option *xinc;
		struct Option *yinc;
		struct Option *len;
		struct Option *null;
	}
	parm;
	struct
	{
		struct Flag *quiet;
	}
	flag;
	
	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Creates vector points map from a Geoplot export file";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);
	
	/* Module Parameters: */	
	parm.input = G_define_option ();
	parm.input->key = "input";
	parm.input->type = TYPE_STRING;
	parm.input->required = YES;
	parm.input->description = "Geoplot ASCII export file";
	
	/* name of output map */
	parm.output = G_define_standard_option (G_OPT_V_OUTPUT);
	parm.output->key = "output";
	parm.output->type = TYPE_STRING;
	parm.output->required = YES;
	parm.output->description = "Vector map to store data points";
	
	/* format of geoplot file */
	parm.format = G_define_option ();
	parm.format->key ="format";
	parm.format->type = TYPE_STRING;
	parm.format->required = NO;
	parm.format->description = "Format of geoplot data file";
	parm.format->options = "xyz,z";
	parm.format->answer = "xyz";
	
	parm.delim = G_define_option ();
	parm.delim->key = "delimiter";
	parm.delim->type = TYPE_STRING;
	parm.delim->required = NO;
	parm.delim->description = "Data delimiter";
	parm.delim->options = "tab,space,comma";
	parm.delim->answer = "tab";

	parm.cref = G_define_option ();
	parm.cref->key = "creference";
	parm.cref->type = TYPE_STRING;
	parm.cref->required = NO;
	parm.cref->description = "Reference corner (top-left or bottom-left)";	
	parm.cref->options = "tl,bl";
	parm.cref->answer = "bl";

	parm.xref = G_define_option ();
	parm.xref->key = "xreference";
	parm.xref->type = TYPE_DOUBLE;
	parm.xref->required = NO;
	parm.xref->description = "Easting of first data point";
	parm.xref->answer = "0.0";
	
	parm.yref = G_define_option ();
	parm.yref->key = "yreference";
	parm.yref->type = TYPE_DOUBLE;
	parm.yref->required = NO;
	parm.yref->description = "Northing of first data point";	
	parm.yref->answer = "0.0";

	parm.xinc= G_define_option ();
	parm.xinc->key = "xincrement";
	parm.xinc->type = TYPE_DOUBLE;
	parm.xinc->required = NO;
	parm.xinc->description = "Spacing between measurements";

	parm.yinc = G_define_option ();
	parm.yinc->key = "yincrement";
	parm.yinc->type = TYPE_DOUBLE;
	parm.yinc->required = NO;
	parm.yinc->description = "Spacing between lines";

	parm.len = G_define_option ();
	parm.len->key = "length";
	parm.len->type = TYPE_DOUBLE;
	parm.len->required = NO;
	parm.len->description = "number of measurements on one line";
	
	parm.null = G_define_option ();
	parm.null->key = "null";
	parm.null->type = TYPE_DOUBLE;
	parm.null->required = NO;
	parm.null->description = "NULL data value to filter out";
	
	flag.quiet = G_define_flag ();
	flag.quiet->key = 'q';
	flag.quiet->description = "Quiet operation: no progress display";
	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}
		
    	read_data ( parm.input->answer, parm.output->answer, parm.format->answer, parm.delim->answer, 
			parm.cref->answer, parm.xref->answer, parm.yref->answer,
			parm.xinc->answer, parm.yinc->answer,
			parm.len->answer, parm.null->answer, flag.quiet->answer );
	
	return (1);
}
