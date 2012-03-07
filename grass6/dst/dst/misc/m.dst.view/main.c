#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

#include <grass/gis.h>


int N_SINGLETONS = 0; /* number of singletons in knowledge base */
int N_HYPOTHESES = 0; /* number of hypotheses in knowledge base */
xmlDocPtr doc;
FILE *lp;


/* returns the amount of memory needed to hold the argument string */
/* to improve readability */
long int to_alloc (xmlChar *string) {
	return (sizeof (xmlChar) * (xmlStrlen (string) + 1 ) );
}


/* return number of singletons in a hypothesis subset */
int get_no_singletons (xmlChar *set) {
	xmlChar *tmp;
	xmlChar *copy;
	int i;			
	
	/* must copy the argument, because it is going to get crippled */
	/* by strtok ... */
	copy = (xmlChar*) G_malloc ((signed) (sizeof(xmlChar) * strlen (set) * 2));
	strcpy (copy,set);
	
	/* extract first singleton */
	tmp = strtok (copy,",");
	/* don't count the empty set */
	if ( strcmp (copy,"NULL") == 0) {
		return (0);
	}
	i = 1;
	/* look for further singletons */
	while ( (tmp = strtok (NULL,",")) != NULL ) {
		i ++;
	}
	
	G_free (copy);
	return (i);
}

int is_evidence (xmlChar *name) {
	if ( name == NULL ) {
		return (0);
	}
	if ( !strcmp (name,"const") ) {
		return (1);
	}
	if ( !strcmp (name,"rast") ) {
		return (1);
	}
	if ( !strcmp (name,"vect") ) {
		return (1);
	}
	return (0);
}

void open_xml_file ( char* filename ) {
	
	xmlNodePtr cur;
	char *xmlfile; /* file name of knowledge base */

	/* get a fully qualified, absolute path and filename for */
	/* reading/writing the XML database file. */
	/* What to do on a DOS system? Let's hope that libxml handles it!*/
	xmlfile = G_strdup (filename);
	
	/* parse the XML structure; check that we have a valid file */
	doc = xmlParseFile (xmlfile);
	if ( doc == NULL ) {
		xmlFreeDoc(doc);
		G_fatal_error ("Could not parse XML structure of knowledge base file.\n");
	}
	
	cur = xmlDocGetRootElement(doc);
	if (cur == NULL) { 
		xmlFreeDoc(doc);
		G_fatal_error ("Knowledge base is an empty file.\n");
	}
	
	if (xmlStrcmp(cur->name, (const xmlChar *) "dst-kb")) {
		xmlFreeDoc(doc);
		G_fatal_error ("File is not a DST knowledge base.\n");
	}		
	
	N_SINGLETONS = atoi (xmlGetProp(cur, "N_SINGLETONS"));
	N_HYPOTHESES = atoi (xmlGetProp(cur, "N_HYPOTHESES"));		
}


void print_header ( char *filename ) {	
	fprintf (lp,"DEMPSTER-SHAFER KNOWLEDGE BASE INFORMATION\n");
	fprintf (lp,"Filename: %s\n", filename );
	fprintf (lp,"No. of user-supplied singletons:\t%i\n",N_SINGLETONS);
	fprintf (lp,"No. of possible hypotheses overall:\t%i\n",N_HYPOTHESES);
}

void print_hypotheses ( int print_all ) {
	
	int present = 0;
	xmlNodePtr cur;		
	
	fprintf (lp,"\nHYPOTHESES");
	if ( ! print_all == 1 ) {
		fprintf (lp," (type USER only):\n");
	} else {
		fprintf (lp,":\n");
	}
	present = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if it user-supplied */
			if ( xmlStrcmp ( "USER", xmlGetProp (cur, "TYPE")) == 0 ) {
				present ++;
				fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
			} if ( print_all ) {
				/* if print_all flag is active: also dump NULL and AUTO types */
				if ( xmlStrcmp ( "AUTO", xmlGetProp (cur, "TYPE")) == 0 ) {
					present ++;
					fprintf (lp,"   '%s' [AUTO]\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
				}
				if ( xmlStrcmp ( "NULL", xmlGetProp (cur, "TYPE")) == 0 ) {
					present ++;
					fprintf (lp,"   '%s' [NULL]\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
				}				
			}
		}
		cur = cur->next;
	}
	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}	
}


void print_const_evidence ( void ) {
	
	int i = 0;
	int j;
	int present = 0;
	xmlNodePtr cur;		
	xmlNodePtr parentNode;
	
	
	fprintf (lp,"\nCONSTANT EVIDENCE:\n");
	/* 1: print user-supplied stuff */
	fprintf (lp,"A) USER Hypothesis SINGLETONS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a CONST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "const"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {				
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "USER", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the CONST entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "const"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}

	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}
	present = 0;

	/* 2: print auto-generated stuff */
	fprintf (lp,"B) AUTO Hypothesis SETS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a CONST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "const"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {				
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "AUTO", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the CONST entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "const"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}			
	
	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}			
}

void print_rast_evidence ( void ) {
	
	int i = 0;
	int j;
	int present = 0;
	xmlNodePtr cur;		
	xmlNodePtr parentNode;

	
	fprintf (lp,"\nRASTER EVIDENCE:\n");		
	/* 1: print user-supplied stuff */
	fprintf (lp,"A) USER Hypothesis SINGLETONS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a RAST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "rast"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "USER", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the RAST entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "rast"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}		
	
	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}		
	present = 0;	
	
	/* 2: print auto-generated stuff */
	fprintf (lp,"B) AUTO Hypothesis SETS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a RAST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "rast"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {				
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "AUTO", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the RAST entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "rast"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}			

	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}			
}


void print_vect_evidence ( void ) {
	
	int i = 0;
	int j;
	int present = 0;
	xmlNodePtr cur;		
	xmlNodePtr parentNode;
	
	
	fprintf (lp,"\nVECTOR EVIDENCE\n");
	/* 1: print user-supplied stuff */
	fprintf (lp,"A) USER Hypothesis SINGLETONS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a CONST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "vect"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "USER", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the VECT entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "vect"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}		
	
	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}		
	present = 0;
	
	/* 2: print auto-generated stuff */
	fprintf (lp,"B) AUTO Hypothesis SETS:\n");
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) ) {
		/* found a Hypothesis node! */		
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* check if there is a CONST evidence attached */
			i = 0;			
			parentNode = cur->xmlChildrenNode;
			while ((parentNode != NULL)){
				if ((!xmlStrcmp(parentNode->name, "vect"))) {
					i ++;					
				}
				parentNode = parentNode->next;
			}			
			if ( i > 0 ) {				
				/* get name of Hypothesis */
				if ( xmlStrcmp ( "AUTO", xmlGetProp (cur, "TYPE")) == 0 ) {
					present = 1;
					fprintf (lp,"   '%s'\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));				
					/* now get all the VECT entries */
					parentNode = cur->xmlChildrenNode;
					j = 1;
					while ((parentNode != NULL)){						
						if ((!xmlStrcmp(parentNode->name, "vect"))) {
							fprintf (lp,"\t%i. %s\n",j,xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1));				
							j ++;
						}
						parentNode = parentNode->next;
					}
				}
			}			
		}
		cur = cur->next;
	}			

	if ( present == 0 ) {
		fprintf (lp," - NONE - \n" );
	}			
}



void print_groups ( void ) {
	
	int i = 0;
	int j = 0;
	xmlNodePtr top;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr hypNode;
	xmlNodePtr evidenceNode;

	fprintf (lp,"\nUSER-DEFINED GROUPS:\n");
	
	top = xmlDocGetRootElement(doc);
	top = top->xmlChildrenNode;
	while ((top != NULL) ){
		if ((!xmlStrcmp(top->name, (const xmlChar *) "grp"))) {			
			i ++;
			fprintf (lp,"   %i: '%s'\n",i,xmlNodeListGetString(doc, top->xmlChildrenNode, 1));			
			/* found a group: must process whole tree for this group! */
			cur = xmlDocGetRootElement(doc);
			cur = cur->xmlChildrenNode;
			j = 0;
			while ( (cur != NULL) ) {
				if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
					hypNode = cur->xmlChildrenNode;
					/* check all evidence entries */
					while ( hypNode != NULL ) {
						if ( is_evidence ( (xmlChar*) hypNode->name) ) {
							/* check all evidence childs */
							evidenceNode = hypNode->xmlChildrenNode;
							while ( evidenceNode != NULL ) {
								/* check all assigns */
								if ( !xmlStrcmp (evidenceNode->name, "assign") ) {
									/* check if assignment is to current group */						
									if ( !xmlStrcmp ( (xmlChar*) xmlNodeListGetString(doc, top->xmlChildrenNode, 1), 
										(const xmlChar *) 
										xmlNodeListGetString(doc, evidenceNode->xmlChildrenNode, 1)) ) {
										fprintf (lp,"\t'%s' = '%s'\n", 
											xmlNodeListGetString(doc, cur->xmlChildrenNode, 1),
											xmlNodeListGetString(doc, hypNode->xmlChildrenNode, 1));
											j = 1;											
									}
								}
								evidenceNode = evidenceNode->next;
							}					
						}
						hypNode = hypNode->next;
					}			
				}
				prev = cur;
				cur = cur->next;
			}
			if ( j == 0 ) {
				fprintf (lp,"\t- NONE - \n");
			}				
		}
		top = top->next;
	}
	if ( i == 0 ) {
		/* no groups defined */
		fprintf (lp," - NONE - \n");
	}		
}

int
main (int argc, char *argv[])
{
	FILE *kb;
	
	struct GModule *module;
	struct
	{
		struct Option *file;
		struct Option *log;
	}
	parm;
	struct
	{
		struct Flag *all;
	}
	flag;

	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);	
	module = G_define_module ();
	module->description = "Displays structured contents of a Dempster-Shafer knowledge base";
	
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);

	/* Parameters */
	parm.file = G_define_option ();
	parm.file->key = "file";
	parm.file->type = TYPE_STRING;
	parm.file->required = YES;
	parm.file->description = "Name of the knowledge base file to display";

	parm.log = G_define_option ();
	parm.log->key = "output";
	parm.log->type = TYPE_STRING;
	parm.log->required = NO;
	parm.log->description = "File to write contents to (default: display on screen)";
	
	/* Flags */
	flag.all = G_define_flag ();
	flag.all->key='a';
	flag.all->description = "Show all hypotheses (including type AUTO)";
	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}

	/* check if we have read/write access to knowledge base */
	errno = 0;
	kb = fopen (parm.file->answer, "r");
	if ( kb == NULL ) {
		G_fatal_error ("Cannot open knowledge base file for reading.\nReason: %s.", strerror (errno));
	} else {
		fclose(kb);
	}
	
	open_xml_file ( parm.file->answer );
	
	if ( parm.log->answer != NULL ) {
		errno = 0;
		lp = fopen (parm.log->answer,"w+");
		if ( lp == NULL ) {
			G_fatal_error ("Cannot create output file for writing.\nReason: %s.", strerror (errno));
		}
	} else {	
		/* send output to terminal */
		lp = stdout;
	}
	
	/* now output information */
	print_header ( parm.file->answer );
	print_hypotheses ( flag.all->answer );
	print_const_evidence ();
	print_rast_evidence ();
	print_vect_evidence ();
	print_groups ();

	exit (EXIT_SUCCESS);
}
