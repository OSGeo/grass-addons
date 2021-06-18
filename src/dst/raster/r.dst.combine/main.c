
/* Based on mathematical core routines: */


/* Dempster-Shafer Core Routines

By Gavin Powell, 3d Vision and Geometry, Dept of Computer Science, Cardiff University. g.r.powell@cs.cf.ac.uk

*/

/* Integration into GRASS 5 GIS and conversion to generic GIS module */
/* By Benjamin Ducke, University of Bamberg, Germany, benducke@compuserve.de */
/* */

/* TODO:   */
/*         - make on-demand reading of raster rows work */
/*         - make finding hyp_names independent of singleton order */
/*			- implement warning messages and log to file w/ccordinates */
/*         - OUTPUT MAPS: write different color schemes for different DST metrics? */
/* BUGS: */
/*		    - opening a rast map twice results in weird behavior in GRASS */
/*         - reading CONST evidence from XML file leaks MEM in tiny amounts */


#define LOCAL

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <errno.h>

#include <grass/gis.h>

#include "main.h"
#include "print.h"
#include "dst.h"
#include "file_io.h"
#include "garbage.h"

/* checks if all groups listed by the user do really exist */
/* at the same time, this returns the number of groups */
/* specified on the command line */
int check_groups ( char **groups ) {
	
	int i,j;
	int check = 0;
	int n_groups;
	
	
	i = 0;
	n_groups = 0;
	while ( parm.groups->answers[i] != NULL ) {
		check = 1;
		for ( j=0; j < N; j++ ) {
			if ( strcmp (parm.groups->answers[i], groups[j]) == 0 ) {
				check = 0;
				n_groups ++;
			}
		}
		if (check == 1) {
			G_warning ("Group '%s' does not exist!\n", parm.groups->answers[i]);
		}
		i++;		
	}

	if ( check == 1 ) {
		G_fatal_error ("Please specify only groups declared in the knowledge base.\n");
	}
	
	return (n_groups);
}



/* This parses the list of hypotheses given by the user. */
/* specificially, it tokenises the comma-separated input */
/* and merges tokens that are enclosed by single quotes */
/* into one SET name, such as 'a,b'. */
/* Also removes duplicate specifiations. */
/* This function returns a pointer to an array of hypothesis names which */
/* can then be passed to the check_hyps() function. */
/* The number of unique hypotheses found in the *hypspect string is */
/* written to *num */
char **parse_hyps (char *hypspec, int *num) {
	char *tmp;
	char *hypname;
	char *quotep;
	char **outhyps;
	int i,j;
	int quote_open;
	int quote_closed;
	int duplicate;
		
	quotep = NULL;
	*num = 0;
	j = 0;
	quote_open = 0;
	quote_closed = 0;
	tmp = G_calloc (255, sizeof(char));
	hypname = G_calloc (255, sizeof(char));
	outhyps = G_malloc (sizeof (char*));
	
	/* parse string to detect number of hyps given */
	tmp = strtok (hypspec, ",");
	while ( tmp != NULL ) {
		/* check if it is enclosed in brackets, that is a SET specification like {a,b} */
		if ( strchr (tmp, '{') != NULL ) {
			if (quote_open == 1) {
				/* ERROR: got two opening brackets in a row. */
				G_fatal_error ("Hypotheses specification string is malformed.\nExpected '}' but got '{'.");
			}
			quotep = tmp;				
			if (quote_open == 0) { /* it's an opening bracket */					
				quote_open = 1;
				quotep ++; /* this now points to the token + 1 (skips bracket) */
				strcpy (hypname,"");
			}
		}
		if ( strchr (tmp, '}') != NULL ) {
			if (quote_closed == 1) {
				/* ERROR: got two closing brackets in a row. */
				G_fatal_error ("Hypotheses specification string is malformed.\nExpected '{' but got '}'.");				
			}
			quote_open = 0; /* it's a closing quote */
			quote_closed = 1;					
		}		
		if ( (quote_open) && (!quote_closed) ) {
			/* keep copying tokens into the set */
			strcat (hypname, quotep);
			strcat (hypname, ",");
		}
		if ( (!quote_open) && (quote_closed) ) {
			/* this is the final set */				
			strncat (hypname, tmp, strlen (tmp)-1); /* remove closing quote */
			/* check for duplicates */
			duplicate = 0;
			for (i=0;i<j;i++) {
				if (!strcmp (outhyps[i], hypname)) {
					duplicate = 1;
				}
			}
			if ( duplicate == 0) {
				/* copy into array */
				outhyps = G_realloc (outhyps, (unsigned) (j * sizeof (char*)));
				outhyps [j] = G_calloc ((unsigned) (strlen(hypname)+1), sizeof (char));				
				strcpy (outhyps[j], hypname);
				j ++;								
			}
		}
		if ( (!quote_open) && (!quote_closed) ) {
			strcpy (hypname, tmp);
			/* check for duplicates */
			duplicate = 0;
			for (i=0;i<j;i++) {
				if (!strcmp (outhyps[i], hypname)) {
					duplicate = 1;
				}
			}
			if ( duplicate == 0 ) {			
				/* copy into array */
				outhyps = G_realloc (outhyps, (unsigned)(j * sizeof (char*)));
				outhyps [j] = G_calloc ((unsigned)(strlen(hypname)+1), sizeof (char));
				strcpy (outhyps[j], hypname);
				j ++;
			}
		}
		tmp = strtok (NULL, ",");
		quote_closed = 0;
	}
	
	*num = j;
	G_free (tmp);
	G_free (hypname);
	return (outhyps);
}

/* checks if all hypotheses specified by the user do exist */
int check_hyps ( char **user_hyps, int no_hyps, xmlDocPtr doc ) {
	
	int i,j;
	int check = 0;
	int n_hyps;
	int no_all_hyps;
	char **all_hyps;
	
	all_hyps = get_hyp_names_XML ( &no_all_hyps, doc );
	n_hyps = 0;	
	for (i=0; i < no_hyps; i++) {
		check = 1;
		for ( j=0; j < no_all_hyps ; j++ ) {			
			if ( strcmp (user_hyps[i], all_hyps[j]) == 0 ) {
				check = 0;
				n_hyps ++;
			}
		}
		if (check == 1) {
			G_warning ("Hypothesis '%s' does not exist!\n", user_hyps[i]);
		}
	}

	if ( check == 1 ) {
		G_fatal_error ("One or more hypotheses were not found in DST knowledge base file.\n");
	}
	
	for ( i=0; i < no_all_hyps; i++ ) {
		G_free (all_hyps[i]);
	}
	G_free (all_hyps);
	return (n_hyps);
}

/* finds index of hyp "hyp_name" in Theta [0..(no_hyps-1)] */
/* returns -1 on error */
long find_hyp_idx ( char *hyp_name, xmlDocPtr doc ) {
	int no_all_hyps;
	long i, j;
	char **all_hyps;
	
	all_hyps = get_hyp_names_XML ( &no_all_hyps, doc );	
	for ( i=0; i < no_all_hyps ; i++ ) {
		if ( strcmp (hyp_name, all_hyps[i]) == 0 ) {
			/* free mem first */
			for ( j=0; j < no_all_hyps; j++ ) {
				G_free (all_hyps[j]);
			}
			G_free (all_hyps);
			return (i);
		}
	}
	
	/* oops, hyp does not exist */
	for ( i=0; i < no_all_hyps; i++ ) {
		G_free (all_hyps[i]);
	}
	G_free (all_hyps);		
	return (-1);
}


void free_sample (Shypothesis *sample) {
	
	G_free (sample);	
}
	
	
void do_calculations_const (Shypothesis **samples, char **groups, int norm, xmlDocPtr doc) {
	
	int i;
	double woc;
	BOOL **garbage;
	char **hyps;
	int no_hyps;
	
	garbage=garbage_init();
	woc = 0;
	hyps = get_hyp_names_XML ( &no_hyps, doc );
	
	for (i=0; i<N; i++) {
		samples[i] = get_const_samples_XML (groups[i], norm, garbage, doc);
	}	
	
	for(i=0;i<N;i++) /* set the bel and pl */
	{
		set_beliefs(samples[i]);
		set_plausibilities(samples[i]);
	}		
			
	for(i=0;i<N-1;i++) /* combine the sets */
	{		
		woc = combine_bpn(samples[0], samples[i+1], garbage, CONST_MODE );
		set_beliefs(samples[0]);		
		set_plausibilities(samples[0]);		
	}
	
	set_commonalities(samples[0]);
	set_doubts(samples[0]);
	set_bint(samples[0]);
	
	
	fprintf(lp, "\nCONST Evidence Combined:\n");	
	print_frame(samples[0], hyps);
	fprintf (lp, "Weight of Conflict: %.3f\n",woc);	
	
	garbage_free ( garbage );
					
	G_free (samples);
}





 void make_result_row ( int val, char *basename, char **hyps, int no_hyps, Sresult_struct *result_row, xmlDocPtr doc ) {
	int i;
	char* val_names[NUMVALS]={"bel","pl","doubt","common","bint","woc","maxbpa","minbpa",
				  "maxsrc","minsrc"};
	DCELL *v1;
	DCELL *v2;
		
	result_row->use = YES;
	/* need an array of DCELL rows to store bel, pl and other DST values */
	if ( val == WOC ) {
		/* WOC (Weight of Conflict is always treated a bit differently,
		   because we need this only once for all hypotheses in the FOD */
		result_row->row[0] = (DCELL*) G_allocate_d_raster_buf ();
	} else {
		if (( val == MAXSRC) || ( val == MINSRC)) {
			for (i = 0; i < no_hyps; i++ ) {
				result_row->crow[i] = (CELL*) G_allocate_c_raster_buf ();
			}
		} else {						
			for (i = 0; i < no_hyps; i++ ) {
				result_row->row[i] = (DCELL*) G_allocate_d_raster_buf ();
			}
		}
	}
	
	if ( val == WOC ) {
		result_row->filename = (char**) G_calloc ( sizeof (char*), 1);    
		/* there is only one file for storing the WOC */
		result_row->filename[0] = G_malloc ((unsigned) ((sizeof (char) * strlen (basename)) +
											(sizeof (char) * strlen (val_names[val])) +		
											2));		
		strcpy (result_row->filename[0],basename);		
		strcat (result_row->filename[0],".");
		strcat (result_row->filename[0],val_names[val]);	
	} else {
		result_row->filename = (char**) G_calloc ( sizeof (char*), (unsigned) no_hyps);    
		/* for all other metrics, we need one output file per hypothesis */		
		for (i=0; i<no_hyps;i++) {		
			result_row->filename[i] = G_malloc ((unsigned)((sizeof (char) * strlen (basename)) +
										 		(sizeof (char) * strlen (hyps[i])) +	
												(sizeof (char) * strlen (val_names[val])) +		
												3));
			strcpy (result_row->filename[i],basename);
			strcat (result_row->filename[i],".");
			strcat (result_row->filename[i],hyps[i]);
			strcat (result_row->filename[i],".");
			strcat (result_row->filename[i],val_names[val]);
			G_strchg (result_row->filename[i], ',', '.');
		}
	}
	/* allocate file descriptors */
	if ( val == WOC ) {
		result_row->fd = (int*) G_calloc ( sizeof (int), 1);
		result_row->fd[0] = -1;
	} else {
		result_row->fd = (int*) G_calloc ( sizeof (int), (unsigned) no_hyps);
		for (i=0; i<no_hyps;i++) {		
			result_row->fd[i] = -1;
		}
	}
	/* init color tables for output maps */	
	v1 = (DCELL*) G_malloc (sizeof (DCELL));
	v2 = (DCELL*) G_malloc (sizeof (DCELL));
	if ( val == WOC ) {
			result_row->colors = (struct Colors **) G_calloc ( sizeof (struct Colors*), 1);
			result_row->colors[0] = G_malloc ( sizeof (struct Colors));		
			G_init_colors (result_row->colors[0]);
			/* *v1 = (DCELL) WOC_MIN; *v2 = (DCELL) WOC_MAX; */
			*v1 = 0; *v2 = 1.001;
			G_add_d_raster_color_rule (v1,0,0,0,v2,255,0,0, result_row->colors[0]);			
	}
	if (( val == BINT ) || (val==MAXBPA) || (val==MINBPA) ){
		result_row->colors = (struct Colors **) G_calloc ( sizeof (struct Colors*), (unsigned) no_hyps);
		for (i=0; i<no_hyps;i++) {
			result_row->colors[i] = G_malloc ( sizeof (struct Colors));		
			G_init_colors (result_row->colors[i]);
			*v1 = 0; *v2 = 1.001;
			G_add_d_raster_color_rule (v1,0,0,0,v2,255,0,0, result_row->colors[i]);			
		}	
	} 
	if ((val == BEL) || (val==PL) || (val==DOUBT) || (val==COMMON )) {
		result_row->colors = (struct Colors **) G_calloc ( sizeof (struct Colors*), (unsigned) no_hyps);
		for (i=0; i<no_hyps;i++) {
			result_row->colors[i] = G_malloc ( sizeof (struct Colors));		
			G_init_colors (result_row->colors[i]);
			*v1 = 0; *v2 = 0.5;
			G_add_d_raster_color_rule (v1,36,216,72,v2,216,201,36, result_row->colors[i]);						
			*v1 = 0.500001; *v2 = 1.001;
			G_add_d_raster_color_rule (v1,216,201,36,v2,216,36,39, result_row->colors[i]);								
			/*
			*v1 = 0; *v2 = 0.333333;
			G_add_d_raster_color_rule (v1,36,216,072,v2,36,216,072, result_row->colors[i]);			
			*v1 = 0.333334; *v2 = 0.666666;
			G_add_d_raster_color_rule (v1,216,201,36,v2,216,201,36, result_row->colors[i]);			
			*v1 = 0.666667; *v2 = 1;
			G_add_d_raster_color_rule (v1,216,36,39,v2,216,36,39, result_row->colors[i]);			
			*/
		}
	}
	
	/* allocate pointers into array of ordered hypotheses */
	/* this is a look-up table for faster access to the 'real' */
	/* index of a hypothesis in Theta */
	{
		result_row->hyp_idx = (long*) G_calloc ( sizeof (int), (unsigned) no_hyps);
		for (i=0; i<no_hyps;i++) {		
			result_row->hyp_idx[i] = find_hyp_idx( hyps[i], doc );
		}
	}
}


/* writes one GRASS DCELL null value into the output row */
void write_row_null (DCELL *row, long easting) {
	G_set_d_null_value (&row[easting], 1);	
}

void write_crow_null (CELL *row, long easting) {
	G_set_c_null_value (&row[easting], 1);	
}

/* writes a DST metric into the output row */
/* WOC (weight of conflict) is the only metric not directly stored */
/* in the Shypothesis struc. Thus, it must be passed explicitly */
void write_row_val (DCELL *row, long easting, Shypothesis *frame, long hyp, int val
					, double woc) {
	switch ( val ) {
		case BEL:
			row[easting] = get_bel (frame,hyp);
		    break;
		case PL:
			row[easting] = get_pl (frame,hyp);
			break;
		case DOUBT:
			row[easting] = get_doubt (frame,hyp);
			break;
		case COMMON:			
			row[easting] = get_common (frame,hyp);
			break;
		case BINT:
			row[easting] = get_bint (frame,hyp);
			break;
		case WOC:
			/* need to process a bit differently */
			row[easting] = woc;
			break;
		case MAXBPA:
			row[easting] = get_maxbpn (frame,hyp);
			break;
		case MINBPA:
			row[easting] = get_minbpn (frame,hyp);
			break;		
	}
}

void write_row_file ( DCELL *row, int fd) {	
	G_put_d_raster_row (fd, row);
}


/* same as above, for maps of type CELL */
void write_crow_val (CELL *row, long easting, Shypothesis *frame, long hyp, 
			int val) {
	
	switch ( val ) {
		case MAXSRC:
			row[easting] = get_maxbpnev (frame, hyp);
		    	break;
		case MINSRC:
			row[easting] = get_minbpnev (frame, hyp);
			break;	
	}
}


void write_crow_file ( CELL *row, int fd) {	
	G_put_c_raster_row (fd, row);
}


void do_calculations_rast (Shypothesis **samples, char **groups, int norm,
						  char* basename, char **outvals, char *hypspec, int quiet_flag,
						  char *logfile, xmlDocPtr doc, Sfp_struct* file_pointers) {
	
	long y,x;
	int i, j, k, l, m;
	long ymax,xmax;
	double woc;
	struct Categories cats, icats;
	DCELL cmin, cmax;
	Sresult_struct *result_row; /* one result_struct for each DST value */
	BOOL **garbage;
	int no_hyps;
	char* val_names[NUMVALS]={"bel","pl","doubt","common","bint","woc","maxbpa","minbpa",
				  "maxsrc","minsrc"};
	int error;
	char **outhyps;
	int no_sets;
	
	/* for keeping min and max statistics */
	Uint nsets;
	double *min_backup, *max_backup;
	int *minev_backup, *maxev_backup;
	
	woc = 0;

	/* check for output options */
	if ( G_legal_filename(basename) != 1 ) {
		G_fatal_error ("Please provide a legal filename as basename for output maps(s).\n");
	}
	
	if ( hypspec != NULL ) { 
		/* user specified hyps, let's see if they're valid */		
		/* create an outhyps array that has as each of its elements the name
			of one of the hypotheses specified on the command line */
		outhyps = parse_hyps (hypspec, &no_hyps);
		check_hyps ( outhyps, no_hyps, doc );				
	} else {
		/* just process all hypotheses */
		outhyps = get_hyp_names_XML ( &no_hyps, doc );
	}

	if ( logfile != NULL ) {	
		fprintf (lp,"Writing output RASTER maps for: \n");
	}
	
	/* create raster rows to store results */
	result_row = G_malloc ( NUMVALS * sizeof (Sresult_struct) );	
	for (i=0; i<NUMVALS; i++) {
		result_row[i].use = NO;
		strcpy (result_row[i].valname,val_names[i]);
		/* individual raster rows will be alloc'd later */
		result_row[i].row = (DCELL **) G_malloc ( no_hyps * sizeof (DCELL*) ); 
		result_row[i].crow = (CELL **) G_malloc ( no_hyps * sizeof (CELL*) );
		result_row[i].filename = NULL;
	}	
	
	j = 0;
	while ( outvals[j] != NULL ) {
	
		if ( !strcmp (outvals[j],"bel") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'bel' (Believe) values\n");
			make_result_row ( BEL, basename, outhyps, no_hyps, &result_row[BEL], doc );			
		}
		if ( !strcmp (outvals[j],"pl") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'pl' (Plausibility) values\n");
			make_result_row ( PL, basename, outhyps, no_hyps, &result_row[PL], doc );
		}
		if ( !strcmp (outvals[j],"doubt") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'doubt' (Doubt) values\n");
			make_result_row ( DOUBT, basename, outhyps, no_hyps, &result_row[DOUBT], doc );
		}
		if ( !strcmp (outvals[j],"common") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'common' (Commonality) values\n");
			make_result_row ( COMMON, basename, outhyps, no_hyps, &result_row[COMMON], doc );
		}
		if ( !strcmp (outvals[j],"bint") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'bint' (Believe interval) values\n");
			make_result_row ( BINT, basename, outhyps, no_hyps, &result_row[BINT], doc );
		}
		if ( !strcmp (outvals[j],"woc") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'woc' (Weight of conflict) values\n");
			make_result_row ( WOC, basename, outhyps, no_hyps,&result_row[WOC], doc );
		}
		if ( !strcmp (outvals[j],"maxbpa") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'maxbpa' (Maximum BPA) values\n");
			make_result_row ( MAXBPA, basename, outhyps, no_hyps,&result_row[MAXBPA], doc );
		}
		if ( !strcmp (outvals[j],"minbpa") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'minbpa' (Minimum BPA) values\n");
			make_result_row ( MINBPA, basename, outhyps, no_hyps,&result_row[MINBPA], doc );
		}
		if ( !strcmp (outvals[j],"maxsrc") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'maxsrc' (source of highest BPA) values\n");
			make_result_row ( MAXSRC, basename, outhyps, no_hyps,&result_row[MAXSRC], doc );
		}
		if ( !strcmp (outvals[j],"minsrc") ) {
			if ( logfile != NULL ) 
				fprintf (lp,"\t'minsrc' (source of lowest BPA) values\n");
			make_result_row ( MINSRC, basename, outhyps, no_hyps,&result_row[MINSRC], doc );
		}
		j ++;
	}
	
	/* open output maps to store results */
	if ( logfile != NULL ) 
		fprintf (lp,"Opening output maps:\n");
	for (i=0; i<NUMVALS;i++) {
		if (result_row[i].use == YES) {
			if ( i == WOC ) {
				if ( logfile != NULL ) 
					fprintf (lp,"\t%s\n",result_row[i].filename[0]);
				result_row[i].fd[0] = G_open_raster_new (result_row[i].filename[0],DCELL_TYPE);
			} else {
				for (j=0; j < no_hyps; j++) {
					if ( logfile != NULL ) 
						fprintf (lp,"\t%s\n",result_row[i].filename[j]);
					if ((i == MAXSRC) || (i == MINSRC)) {
						result_row[i].fd[j] = G_open_raster_new (result_row[i].filename[j],CELL_TYPE);
					} else {
						result_row[i].fd[j] = G_open_raster_new (result_row[i].filename[j],DCELL_TYPE);
					}
					/* check fd for errors */
					if ( result_row[i].fd[j] < 0 ) {
						G_fatal_error ("Could not create output map for %s\n",
										result_row[i].filename[j]);
					}
				}
			}
		}
	}		
	
	if ( logfile != NULL ) {
		fprintf (lp, "Evidence will be combined for these groups:\n");
		for ( i=0; i < N; i++) {
			fprintf (lp,"\t%s\n",groups[i]);
		}
		fprintf (lp, "Output will be stored in mapset '%s'.\n", G_mapset());
		fprintf (lp,"\nRead output below carefully to detect potential problems:\n");
	}			
			
	/* set start coordinates for reading from raster maps */
    	ReadX = 0;
	ReadY = 0;
	
	ymax = G_window_rows ();
	xmax = G_window_cols ();	
	
	if ( !quiet_flag ) {
		fprintf	(stdout,"Combining RAST evidence: \n");
		fflush (stdout);
	}
	
	/* allocate all file pointers */
	/* open raster maps for this group */
	/* 0 is the NULL hypothesis, so we start at 1 */
	no_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	for (l=0; l<N; l++) {
		for ( m = 1; m < no_sets; m ++ ) {
			file_pointers[l].fp[m] = G_open_cell_old ( file_pointers[l].filename[m], G_find_cell ( file_pointers[l].filename[m],"") );
			if ( file_pointers[l].fp[m] < 0 ) {
				G_fatal_error ("Could not open raster map '%s' for reading.\n", file_pointers[l].filename[m] );
			}
		}
	}	
	
	for (y=0; y<ymax; y++) {
		for (x=0; x<xmax; x++) {
			garbage = garbage_init ();
			NULL_SIGNAL = 0;
			
			for (i=0; i<N; i++) {
				samples[i] = get_rast_samples_XML (groups[i],i, norm, &nsets, garbage, doc, file_pointers );	
			}		

			/* get min and max values */
			for (i=0; i<N; i++) {
				if (NULL_SIGNAL == 0) {
					for (k=0; k < nsets; k++) {
						samples[i][k].minbpn = samples[i][k].bpa;
						samples[i][k].maxbpn = samples[i][k].bpa;
						samples[i][k].minbpnev = i + 1;
						samples[i][k].maxbpnev = i + 1;
					}
				}
								
			}
			
			for (i=0; i<N; i++) {
				if (NULL_SIGNAL == 0) {								
					for (j=0; j < N; j++) {
						for (k=0; k < nsets; k++) {
							if (samples[i][k].bpa < samples[j][k].minbpn) {
								samples[j][k].minbpn = samples[i][k].bpa;
								samples[j][k].minbpnev = i + 1;
							}
							if (samples[i][k].bpa > samples[j][k].maxbpn) {
								samples[j][k].maxbpn = samples[i][k].bpa;
								samples[j][k].maxbpnev = i + 1;
							}
						}
					}					
				}
			}
									
			/* initialise: */
			/* set belief and plausibility before first combination of evidence */
			for(i=0;i<N;i++)
			{
				if ( NULL_SIGNAL == 0 ) {
					set_beliefs(samples[i]);					
					set_plausibilities(samples[i]);
				}
			}
			
								
			/* combine evidence and set bel and pl again */
			/* AFTER COMBINE_BPN(), VALUES IN SAMPLES[0] WILL ALL BE ALTERED */
			/* so we must save min and max values for later use */
			min_backup = G_malloc ((unsigned)(nsets * sizeof(double)));			
			max_backup = G_malloc ((unsigned)(nsets * sizeof(double)));			
			minev_backup = G_malloc ((unsigned)(nsets * sizeof(int)));			
			maxev_backup = G_malloc ((unsigned)(nsets * sizeof(int)));
			for (k=0; k < nsets; k++) {
				min_backup[k] = samples[0][k].minbpn;
				max_backup[k] = samples[0][k].maxbpn;
				minev_backup[k] = samples[0][k].minbpnev;
				maxev_backup[k] = samples[0][k].maxbpnev;
			}

			/* now, do the combination! */
			for(i=0;i<N-1;i++)
			{
				if ( NULL_SIGNAL == 0 ) {
					woc = combine_bpn(samples[0], samples[i+1], garbage, RAST_MODE );					
					set_beliefs(samples[0]);					
					set_plausibilities(samples[0]);
				}
			}
			
			/* restore min and max values */
			for (k=0; k < nsets; k++) {
				samples[0][k].minbpn = min_backup[k];
				samples[0][k].maxbpn = max_backup[k];
				samples[0][k].minbpnev = minev_backup[k];
				samples[0][k].maxbpnev = maxev_backup[k];
			}			
			G_free (min_backup);
			G_free (max_backup);
			G_free (minev_backup);
			G_free (maxev_backup);
			
			/* all other metrics can be derived from bel and pl, no need */
			/* to combine evidence again! */
			if ( NULL_SIGNAL == 0 ) {
				set_commonalities(samples[0]);
				set_doubts(samples[0]);
				set_bint(samples[0]);
			}
			
									
			if ( NULL_SIGNAL == 1 ) {
				for (i=0; i<NUMVALS;i++) {
					if (result_row[i].use == YES) {
						if ( i == WOC) {
								write_row_null (result_row[i].row[0], ReadX);							
						} else {
							if ((i == MAXSRC)||(i == MINSRC)) {
								for (j=0; j < no_hyps; j++) {
									write_crow_null (result_row[i].crow[j], ReadX);
								}
					
							} else {							
								for (j=0; j < no_hyps; j++) {
									write_row_null (result_row[i].row[j], ReadX);							
								}
							}
						}
					}
				}				
			} else {
				for (i=0; i<NUMVALS;i++) {
					if (result_row[i].use == YES) {			
						if ( i == WOC ) {
							write_row_val (result_row[i].row[0], ReadX, samples[0], result_row[i].hyp_idx[0], i, woc);
						} else {
							if (( i == MAXSRC ) || ( i == MINSRC )) {
								for (j=0; j < no_hyps; j++) {
									write_crow_val (result_row[i].crow[j], ReadX, samples[0], result_row[i].hyp_idx[j], i);
								}
							} else {
								for (j=0; j < no_hyps; j++) {
									write_row_val (result_row[i].row[j], ReadX, samples[0], result_row[i].hyp_idx[j], i, woc);							
								}
							}
						}
					}
				}
			}
			ReadX ++;
			garbage_free ( garbage );									
			for (i=0; i<N; i++) {
				free_sample (samples[i]);				
			}					
		}
		ReadY ++; /* go to next row */
		ReadX = 0;				
		/* save this row to the result file */
		for (i=0; i<NUMVALS;i++) {
			if (result_row[i].use == YES) {			
				if ( i == WOC ) {
					write_row_file ( result_row[i].row[0],result_row[i].fd[0]);
				} else {
					if ( ( i == MAXSRC ) || ( i == MINSRC ) ) {
						for (j=0; j<no_hyps; j++) {
							write_crow_file ( result_row[i].crow[j],result_row[i].fd[j]);
						}
					} else {
						for (j=0; j<no_hyps; j++) {
							write_row_file ( result_row[i].row[j],result_row[i].fd[j]);
						}
					}
				}
			}
		}
		if ( !quiet_flag ) {
			G_percent (ReadY,ymax,1);
			fflush (stdout);		
		}
	}
	if ( !quiet_flag ) {
		fprintf (stdout,"\n");
		fflush (stdout);
	}
	for (i=0; i<NUMVALS;i++) {
		if (result_row[i].use == YES) {
			if ( i == WOC ) {
				G_close_cell (result_row[i].fd[0]);
			} else {				
				for (j=0; j<no_hyps; j++) {				
					G_close_cell (result_row[i].fd[j]);
				}
			}
		}
	}			
	
	
	/* close raster maps */
	/* 0 is the NULL hypothesis, so we start at 1 */
	for (l=0; l<N; l++) {
		for ( m = 1; m < no_sets; m ++ ) {
			G_close_cell (file_pointers[l].fp[m]);
		}
	}
	
	/* create a categories structure for output maps */
	/* DCELL maps */
	G_init_cats (3, "Value ranges", &cats);
	cmin = 0;
	cmax = 0.333333;
	G_set_d_raster_cat (&cmin, &cmax, "low", &cats);
	cmin = 0.333334;
	cmax = 0.666666;
	G_set_d_raster_cat (&cmin, &cmax, "medium", &cats);
	cmin = 0.666667;
	cmax = 1;
	G_set_d_raster_cat (&cmin, &cmax, "high", &cats);	

	/* CELL maps */
	G_init_cats (N+1, "Source of evidence", &icats);
	G_set_cat (0,"no data",&icats);
	for (i=1; i<=N; i++) {
		G_set_cat (i,groups[i-1],&icats);
	}

	/* write all color tables, categories information and history metadata */
	for (i=0; i<NUMVALS;i++) {
		if (result_row[i].use == YES) {
			if ( i == WOC ) {
				error = G_write_colors (result_row[i].filename[0], G_mapset(), result_row[i].colors[0]);
				if (error == -1) {
					G_warning ("Could not create color table for map '%s'.\n",result_row[i].filename[j]);
				}
			} else {
				if (( i == MAXSRC ) || ( i == MINSRC )) {					
					for (j=0; j<no_hyps; j++) {
						G_write_cats (result_row[i].filename[j], &icats);
					}
				} else {				
					for (j=0; j<no_hyps; j++) {
						error = G_write_colors (result_row[i].filename[j], G_mapset(), result_row[i].colors[j]);
						if (error == -1) {
							G_warning ("Could not create color table for map '%s'.\n",result_row[i].filename[j]);
						}
						G_write_raster_cats (result_row[i].filename[j], &cats);
					}
				}				
			}
		}
	}					
	G_free (samples);
	for ( i=0; i < no_hyps; i ++ ) {
		G_free ( outhyps[i]);
	}
	G_free (outhyps);
}


int main( int argc, char *argv[] )
{
	Shypothesis **samples; /* Data to be combined */
	unsigned int i;
	FILE *kb;
	char **groups;
	int norm = 1; /* turn on normalisation of evidence by default */
	/* these are for time keeping in the logfile */	
	time_t systime;
	clock_t proctime;
	unsigned long timeused;
	unsigned int days, hours, mins, secs;
	
	xmlDocPtr dstXMLFile;
	Sfp_struct* file_pointers;	
	
	G_gisinit ( argv[0] );		
	
	module = G_define_module ();
	module->description = "Combines evidences from a DST knowledge base";
		
	parm.file = G_define_option ();
	parm.file->key = "file";
	parm.file->type = TYPE_STRING;
	parm.file->required = YES;
	parm.file->description = "Name of the knowledge base that contains the evidence";
	
	parm.groups = G_define_option ();
	parm.groups->key = "sources";
	parm.groups->type = TYPE_STRING;
	parm.groups->required = NO;
	parm.groups->multiple = YES;
	parm.groups->description = "Evidences to be combined (default: all)";
			
	parm.type = G_define_option ();
	parm.type->key = "type";
	parm.type->type = TYPE_STRING;
	parm.type->required = NO;
	parm.type->options = "const,rast,vect";
	parm.type->answer = "rast";
	parm.type->description = "Type(s) of evidences to combine";	
	
	parm.output = G_define_option ();
	parm.output->key = "output";
	parm.output->type = TYPE_STRING;
	parm.output->required = NO;
	parm.output->answer = G_location ();
	parm.output->description = "Prefix for result maps (dflt: location name)";

	parm.vals = G_define_option ();
	parm.vals->key = "values";
	parm.vals->type = TYPE_STRING;
	parm.vals->required = NO;
	parm.vals->multiple = YES;
	parm.vals->options = "bel,pl,doubt,common,bint,woc,maxbpa,minbpa,maxsrc,minsrc";
	parm.vals->answer = "bel";
	parm.vals->description = "Dempster-Shafer values to map";

	parm.hyps = G_define_option ();
	parm.hyps->key = "hypotheses";
	parm.hyps->type = TYPE_STRING;
	parm.hyps->required = NO;
	parm.hyps->multiple = NO;
	parm.hyps->description = "Hypotheses to map (default: all)";

	parm.logfile = G_define_option ();
	parm.logfile->key = "logfile";
	parm.logfile->type = TYPE_STRING;
	parm.logfile->required = NO;
	parm.logfile->description = "Name of logfile";

	/* TODO: not implemented yet
	parm.warnings = G_define_option ();
	parm.warnings->key = "warnings";
	parm.warnings->type = TYPE_STRING;
	parm.warnings->required = NO;
	parm.warnings->description = "Name of site list to store locations of warnings." ;
	*/

	flag.norm = G_define_flag ();
	flag.norm->key = 'n';
	flag.norm->description = "Turn off normalisation";

	flag.quiet = G_define_flag ();
	flag.quiet->key = 'q';
	flag.quiet->description = "Quiet operation: no progress diplay";

	/* append output to existing logfile ? */
	flag.append = G_define_flag ();
	flag.append->key = 'a';
	flag.append->description = "Append log output to existing file";
	
	no_assigns = 0;
	
	/* INIT GLOBAL VARS */
	WOC_MIN = 0;
	WOC_MAX = 0;
	
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);
	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}			
	
	/* check if given parameters are valid */
	if (G_legal_filename (parm.file->answer) == -1) {
		G_fatal_error ("Please provide the name of an existing DST knowledge base.\n");
	}
	
	if (G_find_file ("DST",parm.file->answer,G_mapset()) == NULL) {
		G_fatal_error ("Knowledge base does not exist in user's MAPSET!\n");
	}
	
	/* check logfile */
	if (parm.logfile->answer != NULL) {		
		if ( !G_legal_filename (parm.logfile->answer) ) {
			G_fatal_error ("Please specify a legal filename for the logfile.\n");
		}
		/* attempt to write to logfile */
		if (flag.append->answer) {
			if (fopen (parm.logfile->answer, "r") == NULL) {
				lp = fopen (parm.logfile->answer, "w+");
				if (lp == NULL) {
					G_fatal_error ("Logfile error: %s\n", strerror (errno));
				}				
			} else {
				lp = fopen (parm.logfile->answer, "a");
				if (lp == NULL) {
					G_fatal_error ("Logfile error: %s\n", strerror (errno));
				}
				fprintf (lp,"\n\n * * * * * \n\n");
			}
		} else {
			if ( (lp = fopen ( parm.logfile->answer, "w+" ) ) == NULL ) {
				G_fatal_error ("Logfile error: %s\n", strerror (errno));
			}
		}
		/* we want unbuffered output for the logfile */
		setvbuf (lp,NULL,_IONBF,0);
	} else {		
		/* log output to stderr by default */
		lp = stderr;
	}
		
	/* setup coordinate file storage, if desired */
	/* try to create a sites file to store coordinates */
	/* set 'warn' to point to the user-defined sites file */	
	/*
	warn = NULL;
	if ( parm.warnings != NULL ) {
	}
	*/
			
	/* check if we have read/write access to knowledge base */
	kb = G_fopen_old ("DST",parm.file->answer,G_mapset());
	if ( kb == NULL ) {
		G_fatal_error ("Cannot open knowledge base file for reading and writing!\n");
	}
	fclose(kb);
	
	/* start logfile */
	if ( parm.logfile->answer != NULL) {
		fprintf (lp,"This is %s, version %.2f\n",argv[0],PROGVERSION);
		systime = time (NULL);
		fprintf (lp,"Calculation started on %s\n",ctime(&systime));
	}		
		
	/* open DST file and get basic evidence group information */
	dstXMLFile = stat_XML ( parm.file->answer, &NO_SINGLETONS, &N );
	groups = get_groups_XML ( N, dstXMLFile );
	
	if ( NO_SINGLETONS == 1 ) {
		G_fatal_error ("Knowledge base does not contain any user-supplied hypotheses.\n");
	}

	if ( parm.groups->answer != NULL ) {
		/* user specified a subset of groups */
		N = check_groups ( groups );
	}
		
	if ( N < 2 ) {
		G_fatal_error ("At least two groups of evidences must be present in the knowledge base.\n");
	}				

	/* allocate memory for all samples 
	 a sample holds one double for bel, pl and bpn for each
	 piece of evidence. The number of pieces of evidence is
	 the number of possible subsets in Theta 
	 = 2^NO_SINGLETONS ! 
	
	 The number of samples is = number of groups in the XML
	 knowledge base file (N) !
	*/
	samples = (Shypothesis**) G_malloc ((N * sizeof(Shypothesis*)));
	for ( i=0; i < N; i ++ ) {
		samples[i] = (Shypothesis*) G_malloc (sizeof(Shypothesis));
	}
	
	
	/* turn off normalisation if user wants it so */
	if ( flag.norm->answer == 1 ) {
		norm = 0;
	}	
			
	/* do some type-dependant checking */
	/* and open file pointers for all the maps to read! */
	file_pointers = NULL;
	if ( !strcmp (parm.type->answer,"rast") ) {
		if ( parm.groups->answer != NULL ) {
			/* check only user-specified groups */
			file_pointers = test_rast_XML ( parm.groups->answers, dstXMLFile );			
		} else {
			/* check all groups */
			file_pointers = test_rast_XML ( groups, dstXMLFile );
		}
	}	
	
	/* read in all samples in a type-dependant manner */
	if ( parm.groups->answer != NULL ) {
		/* read only user-specified groups */
		if ( !strcmp (parm.type->answer,"const") ) {
			if ( strcmp (parm.output->answer,G_location ()) != 0) {
				G_warning ("Ignoring parameter 'output='.\n");
			}
			if ( strcmp (parm.vals->answer,"bel") !=0 ) {
				G_warning ("Ignoring parameter 'values='.\n");
			}
			if ( parm.hyps->answer != NULL ) {
				G_warning ("Ignoring parameter 'hypotheses='.\n");
			}
			do_calculations_const (samples,parm.groups->answers, norm, dstXMLFile);
		}
		if ( !strcmp (parm.type->answer,"rast") ) {
			do_calculations_rast (samples,parm.groups->answers, norm,
								  parm.output->answer, parm.vals->answers, 
								  parm.hyps->answer, flag.quiet->answer,
							      parm.logfile->answer, dstXMLFile, file_pointers );
		}			
	} else {
		/* read all groups */
		if ( !strcmp (parm.type->answer,"const") ) {
			if ( strcmp (parm.output->answer,G_location ()) != 0) {
				G_warning ("Ignoring parameter 'output='.\n");
			}
			if ( strcmp (parm.vals->answer,"bel") !=0 ) {
				G_warning ("Ignoring parameter 'values='.\n");
			}
			if ( parm.hyps->answer != NULL ) {
				G_warning ("Ignoring parameter 'hypotheses='.\n");
			}
			do_calculations_const (samples,groups, norm, dstXMLFile);
		}
		if ( !strcmp (parm.type->answer,"rast") ) {
			do_calculations_rast (samples,groups, norm,
								  parm.output->answer, parm.vals->answers, 
							      parm.hyps->answer, flag.quiet->answer,
								  parm.logfile->answer, dstXMLFile, file_pointers );
		}			
	}	
		
	/* close logfile */
	/* write processing time to logfile */
	proctime = clock ();
	timeused = (unsigned long) proctime / CLOCKS_PER_SEC;
	days = timeused / 86400;
	hours = (timeused - (days * 86400)) / 3600;
	mins = (timeused - (days * 86400) - (hours * 3600)) / 60;		
	secs = (timeused - (days * 86400) - (hours * 3600) - (mins * 60));
	systime = time (NULL);
	
	if ( parm.logfile->answer != NULL ) {
		fprintf (lp,"\nCalculation finished on %s",ctime(&systime));		
		fprintf (lp,"Processing time: %id, %ih, %im, %is\n",
				days, hours, mins, secs );
		fflush (lp);
	}
	
	for (i=0; i<N; i++) {
		G_free (groups[i]);		
	}
	G_free (groups);
	
	return (EXIT_SUCCESS);
}
