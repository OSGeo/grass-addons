#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

#include <grass/gis.h>

#include "structs.h"
#include "file_io.h"
#include "dst.h"


#define MAX_XML_PATH_LENGTH 4096

/* global XML vars */
int first_allocation = 1;
DCELL *dcell_buf;


/* 
   This starts the XML parser at 'doc' which is an xmlDocPtr that must not have
   have been allocated by the caller. 
   
   This also sets the number of singleton hyps and groups found in the
   knowledge base file.
   
*/
xmlDocPtr stat_XML (char *file, int *no_singletons, int *n ) {
	
	xmlDocPtr root;
	xmlNodePtr cur;
	int check;
	char *xmlfile;
	
	xmlfile = G_malloc ( MAX_XML_PATH_LENGTH * sizeof (char) );
	
	check = snprintf ( xmlfile, MAX_XML_PATH_LENGTH, "%s/%s/DST/%s",G_location_path(),G_mapset(),file );
	if ( check >= MAX_XML_PATH_LENGTH ) {
		G_fatal_error ("XML path too long. Output truncated.\n");
	}
	
	root = xmlParseFile (xmlfile);
	if ( root == NULL ) {
		xmlFreeDoc(root);
		G_fatal_error ("Could not parse XML structure of knowledge base!\n");
	}
	
	cur = xmlDocGetRootElement(root);
	if (cur == NULL) { 
		xmlFreeDoc(root);
		G_fatal_error ("Knowledge base is an empty file!\n");
	}
	
	if (xmlStrcmp(cur->name, (const xmlChar *) "dst-kb")) {
		xmlFreeDoc(root);
		G_fatal_error ("File is not a DST knowledge base!\n"); 
	}		
	
	*no_singletons = atoi ((char*) xmlGetProp(cur, (xmlChar*) "N_SINGLETONS"));
	*n = atoi ((char*) xmlGetProp(cur, (xmlChar*) "N_GROUPS"));
		
	G_free ( xmlfile);	
	
	return ( root );
}



/*
   This returns an array of group names found in the XML file. Again, memory
   for this must not be allocated by the caller.
   
   n must be set to the number of groups in the XML file; run stat_XML first to know this value!
   
*/
char **get_groups_XML ( int n, xmlDocPtr doc ) {
	
	xmlNodePtr cur;
	int i;	
	char **groups;
	
	/* allocate memory to store group names */
	groups = (char**) G_malloc ( sizeof (char*) * n);
	
	cur = xmlDocGetRootElement(doc);		
	cur = cur->xmlChildrenNode;
	i = 0;
	while ( cur != NULL ) {
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {		
			groups[i] = (char*) G_malloc ( sizeof (char) * (strlen ((char*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) + 1) );
			strcpy (groups[i],(char*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
			i ++;
		}
		cur=cur->next;
	}
	
	if ( i != n ) {
		G_fatal_error ("XML file corruption. Please run m.dst.check on this file.\n");
	}
		
	return ( groups );
}




/* read names of all hypotheses in a knowledge base into a char array */
/* number of names in array is written to *no_all_hyps */
char **get_hyp_names_XML ( int *no_all_hyps, xmlDocPtr doc) {
	
	xmlNodePtr cur;
	char **hyps;
	int no_sets, i;

	cur = xmlDocGetRootElement(doc);	
	
	no_sets = atoi ((char*) xmlGetProp(cur, (xmlChar*) "N_HYPOTHESES"));
	*no_all_hyps = 	no_sets;
	
	/* allocate memory and store hyp names */
	hyps = (char**) G_malloc (sizeof (char*) * no_sets);
	
	cur = cur->xmlChildrenNode;
	i = 0;
	while ( cur != NULL ) {
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
				hyps[i] = (char*) G_malloc ( sizeof (char) * (strlen ((char*)cur->name) ) + 1 );
				hyps[i] = strdup ((char*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
				i ++;			
		}
		cur=cur->next;
	}
			
	return (hyps);
}


/* Retrieve sample bpns from XML knowledge base file */
/* A bpn can be a probability assignment, but does not */
/* necessarily have to be one (could also be, eg. a ranking score) */
/* i.e. any measure of subjective believe in the truth of an evidence */
/* all lines added together must equal "1" */
/* This can always be achieved by simply normalising the evidence */
/* The sample file is read in a specific order. */
/* That order is determined by a simple algorithm: */
/* 1. list = empty set
   2. add next singleton from file to list. EXIT on EOF
   3. try if a subset not currently on the list can 
      be build using the available singletons (w/o the empty set). 
	  YES: build subset, add to list and GOTO 3
	  NO: GOTO 2
*/
/* I.E.: DST needs a Frame of Decision that constitutes a COMPLETE 
   universe of ALL POSSIBLE combinations and their hierarchical
   combinations */

/* e.g. for Omega = {a, b, c}
{0} (empty set)
{a}
{b}
{a, b}
{c}
{a, c}
{b, c}
{a, b, c}
*/
/* in real applications, the bpn for {0} should always be */
/* zero, so that the remaining hypotheses form the COMPLETE */
/* set of all possible outcomes */
/* according to DST rules, {a}*{b} does not have to be equal */
/* to {a,b}! */
/* all SINGLETON hypotheses, however ({a},{b},{c]), MUST be */
/* mutually exclusive! */

/* get all groups with CONST evidence from XML knowledge base */
/* file and store evidence as Shypothesis */

/* TODO: CHECK if const evidence really exists for this group! */
Shypothesis *get_const_samples_XML ( char* group, int norm, BOOL **garbage, xmlDocPtr doc ) {
	
	xmlNodePtr cur, hypNode, evidenceNode;		
	Shypothesis *sample;
	unsigned int no_sets, i; 
	int k;
	double total;		
	
	no_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
			
	sample = frame_discernment( garbage );
			
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;	
	i = 0;
	k = -1; /* position to insert bpa in Omega, set to -1 to discount NULL Hyp */
	sample[0].bpn = 0; /* NULL hypothesis is always = 0 ! */
	while ( (cur != NULL) ) {		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			k ++;
			hypNode = cur->xmlChildrenNode;
			/* check all evidence entries */
			while ( hypNode != NULL ) {
				if ( !strcmp ( (char*) hypNode->name , "const" ) ) {
					/* check all evidence childs */
					evidenceNode = hypNode->xmlChildrenNode;
					while ( evidenceNode != NULL ) {
						/* check all assigns */
						if ( !xmlStrcmp (evidenceNode->name, (xmlChar*)"assign") ) {
							/* check if assignment is to current group */						
							if ( !xmlStrcmp ( (xmlChar*) group, (const xmlChar *) 
								xmlNodeListGetString(doc, evidenceNode->xmlChildrenNode, 1)) ) {
									i = 1; /* signal that an assignment has been made */
									sample[k].bpn = atof 
										((char*)xmlNodeListGetString(doc, hypNode->xmlChildrenNode, 1));									
									if (sample[k].bpn < 0) {
										G_fatal_error ("Negative bpn! Please check your data using m.dst.check.\n");
									}
							}
						}
						evidenceNode = evidenceNode->next;						
						if ( i == 0 ) { /* no assignment for this hyp, so set to 0! */
							sample[k].bpn = 0;
							i = 0;
						}						
					}					
				}
				hypNode = hypNode->next;
			}			
		}
		cur = cur->next;
	}
	
	
	/* normalise sample */	
	total = 0;
	for (i=0; i < no_sets; i++) {
		total = total + sample[i].bpn;
	}
	if ( norm ) {
		for (i=0; i < no_sets; i++) {
			sample[i].bpn = sample[i].bpn / total;
		}		
	}
	
		
	/* user has not given any evidence for this group! */
	if ( total == 0 ) {
		G_fatal_error ("Evidence sums to 0! Please check your data with m.dst.check.\n");
	}
	
	/* if normalisation is turned off, we must check that evidence sums to 1 */
	if ( !norm ) {
		total = 0;
		for (i=0; i < no_sets; i++) {
			total = total + sample[i].bpn;
		}			
		/* sample needs normalisation */
		if ( total != 1 ) {
			G_fatal_error ("Evidence does not sum to 1! Normalisation required.\n");
		}
	}
		
	return ( sample );
}

/* open all raster evidence maps for reading
 has to be called before get_rast_samples_XML can return anything
 useful! 

 This returns an array of file pointers to handle all the raster maps.
 
*/

Sfp_struct* test_rast_XML ( char **groups, xmlDocPtr doc ) {
	
	xmlNodePtr root, cur, hypNode, evidenceNode;	
	int i, k;
	int no_sets;
	Sfp_struct* file_pointers;
		
	root = xmlDocGetRootElement(doc);
	cur = root->xmlChildrenNode;
	
	/* create file pointer structs for all groups */
	no_sets = (int) pow((float) 2, (float) NO_SINGLETONS);
	file_pointers = (Sfp_struct*) G_malloc (sizeof (Sfp_struct) * N+1); /* STRANGE: why does this have to be N+1? Obviously, the size of this struct is not correctly calculated! */
	for (i=0; i<N; i++) {
		file_pointers[i].fp = (int*) G_malloc (sizeof (int) * no_sets);
		file_pointers[i].filename = (char**) G_malloc (sizeof (char*) * no_sets);
		for (k=0; k< no_sets; k++) {
			file_pointers[i].fp[k] = -1;
			file_pointers[i].filename[k] = NULL;
		}
	}
	
	k = -1;
	while ( (cur != NULL) ) {		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			k ++;
			hypNode = cur->xmlChildrenNode;
			/* check all evidence entries */
			while ( hypNode != NULL ) {
				if ( !strcmp ( (char*) hypNode->name , "rast" ) ) {
					/* check all evidence childs */
					evidenceNode = hypNode->xmlChildrenNode;
					while ( evidenceNode != NULL ) {
						/* check all assigns */
						if ( !xmlStrcmp (evidenceNode->name, (xmlChar*)"assign") ) {
							/* check if assignment is to one of the groups */
							for ( i=0; i<N; i++ ) {
								if ( !xmlStrcmp ( (xmlChar*) groups[i], (const xmlChar *) 
									xmlNodeListGetString(doc, evidenceNode->xmlChildrenNode, 1)) ) {
									/* attempt to open raster map and alloc file pointer */									
									if ( G_find_cell ( (char*) xmlNodeListGetString(doc, hypNode->xmlChildrenNode, 1),
										                "") == NULL ) {
										G_fatal_error ("Raster evidence map '%s' not found in search path.", 
														(char*) xmlNodeListGetString
														(doc, hypNode->xmlChildrenNode, 1));
									}
									
									file_pointers[i].fp[k] = G_open_cell_old ((char*) xmlNodeListGetString(doc, hypNode->xmlChildrenNode, 1), 
															G_find_cell ( (char*) xmlNodeListGetString
															(doc, hypNode->xmlChildrenNode, 1),""));
									if ( file_pointers[i].fp[k] < 0 ) {
											G_fatal_error ("Raster evidence map '%s' not readable.", 
														(char*) xmlNodeListGetString(doc, 
															hypNode->xmlChildrenNode, 1));
									}

									/* allocate mem and copy filename into the structure */
									file_pointers[i].filename[k] = G_strdup ((char*) xmlNodeListGetString
														(doc, hypNode->xmlChildrenNode, 1));
																																				
									/* close the connection to this map for now */
									/* we will open it again when we need it */
									/* keeping these handles open will make the prg crash on Win32! */
									G_close_cell (file_pointers[i].fp[k]);																
									file_pointers[i].fp[k] = -1;
																		
								}
							}							
						}
						evidenceNode = evidenceNode->next;						
					}						
				}					
				hypNode = hypNode->next;
			}			
		}			
		cur = cur->next;
	}
		
	return ( file_pointers);
}

/* close all open raster file descriptors */
void close_rasters ( Sfp_struct* file_pointers ) {
	
	int i,k;
	Uint no_sets;
	
	no_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);	
	
	for (i=0; i<N; i++) {
		fprintf (lp,"CLOSING SAMPLE %i:\n",i);
		for (k=0; k< no_sets; k++) {
			if ( file_pointers[i].fp[k] > -1 ) {
				fprintf (lp,"\tHYP=%i\n",k);
				G_close_cell (file_pointers[i].fp[k]);
			}
			if ( file_pointers[i].filename[k] !=NULL ) {
				G_free (file_pointers[i].filename[k]);
			}			
		}
	}	
}

/* get next float value from raster evidence map */
/* hyp_idx runs from 0 to (no_sets-1) */
/* no out of bounds checking is done (performance!) */
DCELL get_next_dcell_rast ( int group_idx, int hyp_idx, Sfp_struct* file_pointers ) {
	
	DCELL dcell_val;	
	
	if (first_allocation == 1) {
		dcell_buf = (DCELL*) G_allocate_d_raster_buf ();
	}
	first_allocation = 0;

	if ( file_pointers[group_idx].fp[hyp_idx] == -1 ) {
		return (0);
	} else {
	
		/* why does on-demand reading of raster row not work? */
		/* if ( ReadX == 0 ) {  */
		  G_get_d_raster_row (file_pointers[group_idx].fp[hyp_idx],dcell_buf,ReadY);
		/*}*/				
		dcell_val = dcell_buf[ReadX];		
		if ( G_is_d_null_value (&dcell_val) ) {
			NULL_SIGNAL = 1;
			return (0);
		}
		return (dcell_val);
	}	
}

/* read a sample from several raster maps */
/* file_pointers have to be assigned using G_open_cell_old before calling this !!! */
Shypothesis *get_rast_samples_XML ( char* group, int group_idx, int norm, Uint *nsets,
  				    BOOL **garbage, xmlDocPtr doc, Sfp_struct* file_pointers ) {
	
	Shypothesis *sample;
	Uint no_sets, i; 
	int k;
	double total;
	struct Cell_head region;
				
	no_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	*nsets = no_sets;
	G_get_window (&region);
	
	sample = frame_discernment( garbage );
		
	for (k=0; k<no_sets; k++) {				
		sample[k].bpn = (double) get_next_dcell_rast (group_idx, k, file_pointers);		
		if (sample[k].bpn < 0) {
			G_warning ("Negative BPN (%.5f) at %.2f, %.2f.\n",
						sample[k].bpn,
						G_col_to_easting ((double) ReadX,&region),
						G_row_to_northing ((double) ReadY,&region));
			NULL_SIGNAL = 1;
			
		}
		sample[k].bpa = sample[k].bpn;
		if ( NULL_SIGNAL ) {
			sample[k].isNull = 1; /* store for debug */
		}
	}		
		
	if ( NULL_SIGNAL == 1 ) {
		return (sample);
	}
	
	/* normalise sample */	
	total = 0;
	for (i=0; i < no_sets; i++) {
		total = total + sample[i].bpn;
	}
	if ( norm ) {
		for (i=0; i < no_sets; i++) {
			sample[i].bpn = sample[i].bpn / total;
		}		
	}
			
	/* user has not given any evidence for this group! */
	if ( total == 0 ) {
			G_warning ("Evidence sums to 0 at %.2f, %.2f.\n",
						G_col_to_easting ((double) ReadX,&region),
						G_row_to_northing ((double) ReadY,&region));
			NULL_SIGNAL = 1;
	}
	
	/* if normalisation is turned off, we must check that evidence sums to 1 */
	if ( !norm ) {
		total = 0;
		for (i=0; i < no_sets; i++) {
			total = total + sample[i].bpn;
		}			
		/* sample needs normalisation */
		if ( total != 1 ) {
			G_warning ("Evidence does not sum to 1 (%f) at %.2f, %.2f.\n",
						total,
						G_col_to_easting ((double) ReadX,&region),
						G_row_to_northing ((double) ReadY,&region));
			
						NULL_SIGNAL = 1;		
		}
	}	
	
	return (sample);
}
