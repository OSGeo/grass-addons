#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <errno.h>

#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/globals.h>

#include <grass/gis.h>

#define MAX_HYPOTHESES 12 /* hard-coded limit for the number of hypotheses
						  anything more than this will overflow the
						  LONG variable needed to caluclate combinatorics
						  (facultary function) */

#define MAX_HYP_CHARS 32 /* hard-coded limit for hypothesis name strings */
#define TMP_SIZE 4096

/* TODO:

	- interface redesign
		- the interface needs to be redesigned, because it must be possible to achieve the following:
			1. Allow the user to attach external files as evidence
			2. Force the user to assign every evidence to a source of evidence when attaching
			3. Clean up the current mess of options, especially the many cleaning tools
		- it must not be allowed to perform any operation on the "NULL" (not case-sensitive) hypothesis!
		  -> currently, it's allowed to attach evidence to it!
		- we must allow for external files to be attached/detached
		- it would be better to have simple names as evidence and the data source names as an XML property
		  (long file names!)
		  Evidence names should be unique across all types of evidence. That way, we can greatly simplify
		  m.dst.source, too.
		- WHY can we attach more than one evidence to a hypothesis?
		- introduce new actions "attach/detach"
		- introduce new action "check" to validate the contents of knowledge base file
		- remove actions "const,rast,vect,att", they are types
		- add ACTIONS "file-rast","file-vect" to attach external file data sources
		- rename type=* to type=all
		- type=all is an error for all actions except prune
		- rework the prune= logics. All we need is the name of a hypothesis, and a type.
		  for single evidences, we have "detach"
		- there is also a "clean=" option ("parm.null"). That's one too much!
		- delete anything to do with const type evidence: we do not need this
		- support voxel type evidence
	- Improve checking in attach_vect():
		vector evidence: needs to consist of a map and attribute name.
		vector evidence: can only be a double type attribute.
		vector evidence: attribute values must be in range (0;1)
	- Improve checking in attach_rast():
		raster evidence: must be floating point
		raster evidence: must be in range (0;1)
	- Clean-ups:
		- replace strcpy, strcmp, strcat with XML functions
		- call xmlFree(cur,...) at the end of functions
		- user should be able to specify hyp=b,a AS WELL as hyp=a,b - it's the same!
	- Other improvements:
		- tighter checking for correct command line
		- differentiate between BPNs and BPAs a BPA consists of several BPNs!
	- Testing:
		- rigorous testing of all ops (especially prune)
	- Documentation:
		- hypothesis names are case sensitive (also in m.dst.source)!

*/

char *xmlfile; /* store absolute pathname of XML file */
xmlDocPtr doc;
xmlNodePtr cur;
int N_SINGLETONS = 0; /* number of singletons in knowledge base */
int N_HYPOTHESES = 0;

/* calculate facultary function for n */
long fac (long n) {
  long i,result=1;
	
  for (i=1;i<=n;i++) 
	  result=result*i;
  return result;
}


/* returns the amount of memory needed to hold the argument string */
/* (to improve readability) of source code */
long int to_alloc (char *string) {
	return (sizeof (xmlChar) * (strlen (string) + 1 ) );
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


/* returns 1, if a singleton is part of a subset, 0 otherwise */
int is_in_subset (char *set, char *singleton) {
	char *tmp;
	char *copy;
		
	/* must copy the argument, because it is going to get crippled */
	/* by strtok ... */		
	copy = (char*) G_malloc ((signed) (sizeof(char) * (strlen (set) * 2)));
	strcpy (copy,set);
	
	/* extract first singleton */
	tmp = strtok (copy,",");
	if (strcmp (tmp,singleton) == 0) {
		G_free (copy);
		return (1);
	}
	
	/* look for further singletons */
	while ( (tmp = strtok (NULL,",")) != NULL ) {
		if (strcmp (tmp,singleton) == 0) {
			G_free (copy);
			return (1);
		}
	}				
	
	G_free (copy);
	return (0);
}

/* returns the singleton at position pos */
/* pos starts at 0 */
/* returns NULL if unsucessfull */

/* caller must free the returned allocated char buffer! */
/* OTHERWISE, THIS LEAKS MEMORY */
char *get_singleton (xmlChar *set, int pos) {
	char *tmp;
	char *tmp2;
	char *copy;
	int i;
	
	tmp2 = NULL;
	
	/* trying to access a set out of bounds */
	if ( ( pos < 0 ) || ( pos >= get_no_singletons (set) ) ) {
		G_fatal_error ("Set index ouf of range\n.");
	}
	
	/* must copy the argument, because it is going to get crippled */
	/* by strtok ... */		
	copy = (char*) G_malloc ((signed) (sizeof(char) * (strlen (set) + 1)));
	strcpy (copy,set);

	i = 0;
	/* extract first singleton */
	tmp = strtok (copy,",");
	if ( i == pos ) {
		tmp2 = G_malloc ((signed) (sizeof(char) * (strlen (tmp) + 1)));
		strcpy (tmp2,tmp);
		G_free (copy);
		return (tmp2);
	}

	/* look for further singletons */
	while ( (tmp = strtok (NULL,",")) != NULL ) {
		i ++;
		if ( pos == i ) {
			tmp2 = G_malloc ((signed) (sizeof(char) * (strlen (tmp) + 1)));
			strcpy (tmp2,tmp);
			G_free (copy);
			return (tmp2);
		}
	}
	
	/* should never get here, but who knows ... */
	G_free (tmp2);
	G_free (copy);
	return (NULL);
}

/* returns 1, if set is in the lookup list, 0 otherwise */
int is_in_list (xmlChar *set, xmlChar **lookup, int len) {
	long i;
	
	for ( i = 0; i < len; i ++ ) {
		if ( !strcmp (set,lookup[i]) ) {
			return (1);
		}
	}	
	return (0);
}



/* returns 1, if name is rast,vect or const */
/* 0 otherwise */
int is_evidence (xmlChar *name) {
	if ( name == NULL ) {
		return (0);
	}
	if ( !strcasecmp (name,"const") ) {
		return (1);
	}
	if ( !strcasecmp (name,"rast") ) {
		return (1);
	}
	if ( !strcasecmp (name,"vect") ) {
		return (1);
	}
	if ( !strcasecmp (name,"NULL") ) {
		return (1);
	}
	return (0);
}

/*
 
 USER-INVOKED ACTIONS

*/

/* user may supply only a singleton hypothesis */
void add_hypothesis (char *name) {
	
	int built_new = 0;
	long hyps_needed;
	long no_unique_sets, no_fac;
	long no_lookups;
	long h, i, j, k, overflow;
	long counter [MAX_HYPOTHESES]; /* could actually be much smaller, but who cares) */
	xmlChar **singleton;
	xmlChar **lookup;
	xmlChar *new_hyp;
	xmlChar tmp [TMP_SIZE] ;
	xmlNodePtr new_node;
	
	lookup = NULL;
	new_hyp = NULL;

	/* hypothesis names must conform to same restrictions as filenames */
	if ( G_legal_filename (name) != 1 ) {
			G_fatal_error ("Hypothesis name invalid (contains special chars, whitespace or other).\n");
	}
	/* hypothesis names cannot have more than 32 chars */
	if ( strlen (name) > (MAX_HYP_CHARS) ) {
			sprintf (tmp,"Hypothesis names cannot be longer than %i characters.\n",
					MAX_HYP_CHARS);
			G_fatal_error ("%s",tmp);
	}
	
	/* cannot use TMP as hypothesis name */
	if ( !strcmp (name,"TMP") ) {
		G_fatal_error ("Hypothesis name 'TMP' is a reserved name.\n");
	}
		
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while (cur != NULL) {
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) name, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* there already is a hypothesis with this name! */
				sprintf (tmp,"Hypothesis '%s' already exists in the knowledge base.\n",
					(const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
				G_fatal_error ("%s",tmp);
			}
		}
		cur = cur->next;
	}
	
	/* insert Hypothesis as a new child of the XML root */
	cur = xmlDocGetRootElement(doc);
	new_node = xmlNewTextChild (cur, NULL, (xmlChar*) "hyp", (xmlChar*) name);
	/* increase number of stored singletons by one */
	N_SINGLETONS ++;
	/* ouch! cannot have that many hypotheses! */
	if (N_SINGLETONS > MAX_HYPOTHESES) {
		sprintf (tmp,"The maximum number of combinable user hypotheses is %i.\n",
				MAX_HYPOTHESES);
		G_fatal_error ("%s",tmp);
	}		
	sprintf (tmp,"%i",N_SINGLETONS);
	xmlSetProp(cur,(xmlChar*) "N_SINGLETONS", (xmlChar*) tmp);
	/* increase number of hypotheses */
	N_HYPOTHESES ++;
	sprintf (tmp,"%i",N_HYPOTHESES);		
	xmlSetProp(cur,(xmlChar*) "N_HYPOTHESES", (xmlChar*) tmp);	
	/* set type of the newly created hyp-node to SINGLETON */
	xmlSetProp(new_node,(xmlChar*) "TYPE", (xmlChar*) "USER");	
	
	/* check if a new subset has to be generated */
	hyps_needed = (int) pow((float) 2, (float) N_SINGLETONS);
	/* build a singleton-list of all singleton hypotheses */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;	
	singleton = (xmlChar**) G_malloc ((signed) (N_SINGLETONS * sizeof (xmlChar*)));	
	
	/* fill singleton list with hypothesis names */
	i = 0;
	while (cur != NULL) {
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			/* is it a singleton ? */
			if (get_no_singletons ((xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) == 1) {
				singleton[i] = (xmlChar*) G_malloc ((signed) ((strlen ((xmlChar*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) + 1 ) * sizeof(xmlChar)));
	 			singleton[i] = (xmlChar*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1); 
				/* jump over empty set */
				if (strcmp ((char*) singleton[i],"NULL") != 0) {
					i ++;
				}
			}
		}
		cur = cur->next;
	}
	
	if (N_HYPOTHESES < hyps_needed) {		
		/* need to generate new subsets! */
		/* for each of the possible different subset-sizes ... */			
		for ( k = 2; k <= N_SINGLETONS; k ++ ) {						
			/* j stores the current subset size */
			/* generate all unique subsets with j members */			
			no_unique_sets = fac(N_SINGLETONS) / ( fac(k) * fac(N_SINGLETONS-k) );			
			no_fac = no_unique_sets;
			cur = xmlDocGetRootElement(doc);
			cur = cur->xmlChildrenNode;
			
			/* CHANGE THIS TO SAVE SOME MEM */
			/* LOOKUP LIST IS ACTUALLY SMALLER */
			no_lookups = no_unique_sets;
			/* DOESN'T REALLY MATTER, THOUGH */
			
			/* determine number of sets size k that need to be generated */
			while (cur != NULL) {
				/* found a Hypothesis node? */
				if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
                	if (get_no_singletons (xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) == k) {						
						/* it is of the size we are currently trying to generate */
						/* that counts as one done! */
						no_unique_sets --;
					}
				}
				cur = cur->next;
			}
			
			/* DEBUG */
			/* fprintf (stderr,"%s: NEED %i (%i) sets of size %i\n", name, no_unique_sets, no_fac, k); */
			
			/*
			   PASS 1: generate needed sets with TMP dummies
				This time through, we will only put k TMP entries
				into the XML tree. In PASS 2, we will fill them
				with hierarchically ordered hypotheses nodes
			*/
			
			for ( i = 0; i < no_unique_sets; i ++ ) {
				/* new hypothesis set has to have at least 2 elements */
				/* if set size > 2, attach more dummies */
				sprintf (tmp,"TMP,TMP");
				for (j = 0; j < (k-2); j++ ) {
					strcat (tmp,",TMP");
				}
				/* attach new hypothesis sets to end of list */
				cur = xmlDocGetRootElement(doc);
				new_node = xmlNewTextChild (cur, NULL, (xmlChar*) "hyp", (xmlChar*) tmp);
				xmlSetProp(new_node,(xmlChar*) "TYPE", (xmlChar*) "AUTO");	
				N_HYPOTHESES ++;				
			}
			
			/* PASS 2: fill in the TMP entries with hypothesis sets */									
			i = 0;			
			new_hyp= G_malloc ((signed) ( (((sizeof (xmlChar) ) * MAX_HYP_CHARS ) * k) + ( sizeof (xmlChar) *  (k + 1))) );			
			while ( i < no_unique_sets ) {
				/* initialise counters */
				for ( j = 0; j < N_SINGLETONS; j ++ ) {
					counter [ j ] = j;
				}
				if (no_lookups > 0) {
					/* build list of all hypotheses for quick lookup */
					lookup = (xmlChar**) G_malloc ((signed) (no_lookups * sizeof (xmlChar*)));	
					/* get names of k-size hypotheses and store in lookup list */
					cur = xmlDocGetRootElement(doc);
					cur = cur->xmlChildrenNode;	
					
					/* generate lookup list */
					j = 0;
					while (cur != NULL) {
						if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
    	            		if (get_no_singletons (xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) == k) {
								lookup[j] = (xmlChar*) G_malloc ((signed) ((strlen ((xmlChar*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) + 1) * sizeof(xmlChar)));
	 							lookup[j] = (xmlChar*) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1); 
								j ++;
							}	
						}
						cur = cur->next;
					}
				}
				
				/* construct initial set */				
				strcpy ( new_hyp, singleton [counter[0]] );
				for ( j = 1; j < k; j ++) {
					strcat ( new_hyp, "," );
					strcat ( new_hyp, singleton [counter[j]] );
				}
				
				while ( is_in_list ( new_hyp, lookup, no_lookups ) ) {										
					
					overflow = 1;
					built_new = 1;
					
					for ( j = k-1; j > -1; j -- ) {
						if ( overflow ) {
							overflow = 0;
							counter [ j ] ++ ;
							if ( counter [ j ] >  (j+(N_SINGLETONS-k)) ) {
								overflow = 1;
								counter [j] = 0;
							}							
						}												
					}						
					
					/* update all counters, so that each counter */
					/* is higher than its left neighbour */												
					for (h = 1; h < k; h ++) {
						if (counter [h] <= counter [h-1] ) {
							counter [h] = counter [h-1] + 1;
						}
					}
					
					/* try to insert this hypothesis */					
					strcpy ( new_hyp, singleton [counter[0]] );
					for ( j = 1; j < k; j ++) {
						strcat ( new_hyp, "," );
						strcat ( new_hyp, singleton [counter[j]] );
					}
				}				
				/* find right node to insert and do so! */
				/* right node is the first TMP node with size = k */
				cur = xmlDocGetRootElement(doc);
				cur = cur->xmlChildrenNode;
				j = 0;
				while ((cur != NULL) && (j == 0)) {
					if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
                		if (get_no_singletons (xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)) == k) {
							if ( strstr ( xmlNodeListGetString(doc, cur->xmlChildrenNode, 1)
								,"TMP") != NULL ) {
								//fprintf (stderr,"\tInserted %s\n",new_hyp);							
								xmlNodeSetContent (cur, new_hyp);	
								j = 1; /* this exits the while loop */
							}
						}
					}
					cur = cur->next;
				}												
								
				for (j = 0; j < no_lookups; j ++) {
					G_free (lookup[j]);
				}
				G_free (lookup);
				i ++;				
				/* update status display only if needed */
				if (built_new == 1) {
					G_percent (N_HYPOTHESES, hyps_needed, 5);
					fflush (stdout);
				}
			}
		}
		
		G_free (new_hyp);
	}
	/* update status display only if needed */
	if (built_new == 1) {
		G_percent (100, 100, 100);
		printf ("\n");
		fflush (stdout);
	}
	
	/* update number of hypotheses */
	sprintf (tmp,"%i",N_HYPOTHESES);
	cur = xmlDocGetRootElement(doc);
	xmlSetProp(cur,(xmlChar*) "N_HYPOTHESES", (xmlChar*) tmp);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);			
	
	/* free memory */
	for (i = 0; i < N_SINGLETONS; i ++) {
		G_free (singleton[i]);
	}	
	G_free (singleton);	
}

/* delete a hypothesis (singletons only) */
void del_hypothesis ( char *hyp ) {
	int i = 0;
	xmlNodePtr prevNode;

	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
			}
		}
		prevNode = cur;
		cur = cur->next;
	}	
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}

	/* delete every node in the XML tree that has the wanted singleton */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	i = 0;
	while ( cur != NULL ) {
		/* found a Hypothesis node! */
		if ( !xmlStrcmp (cur->name, (const xmlChar *) "hyp" ) ) {
			if ( is_in_subset ( xmlNodeListGetString(doc, cur->xmlChildrenNode, 1), hyp) ) {
				/* Found Hypothesis */
				i = 1; /* signal delayed deletion */
			}
		}
		prevNode = cur;
		cur = cur->next;
		/* delayed deletion */
		if (i == 1) {
			xmlUnlinkNode (prevNode);
			xmlFreeNode	(prevNode);
			i = 0;
		}
	}

	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);	
}

/* rename a SINGLETON hypothesis */
void ren_hypothesis ( char *hyp, char *newname ) {
	int i = 0;
	int j;
	char *tmp;
	char *tmp2;
	char *result;
	xmlNodePtr prevNode;

	tmp2 = NULL;

	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
			}
		}
		prevNode = cur;
		cur = cur->next;
	}	
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* check for legal hypothesis name */
	if (G_legal_filename (newname) == -1 ) {
		G_fatal_error ("Please provide a well-formed hypothesis name (no special chars or whitespace).\n");
	}
	
	/* check for legal length of new name */
	if ( strlen (newname) > MAX_HYP_CHARS ) {
		G_fatal_error ("Hypothesis names my have at most %i characters.\n\tPlease choose a shorter name.\n",MAX_HYP_CHARS);
	}
	
	/* change name(s) of hypoheses */
	/* rename every node in the XML tree that has the wanted name */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	/* parse all hypothesis nodes */
	i = 0;
	while ( cur != NULL ) {
		/* found a Hypothesis node! */
		if ( !xmlStrcmp (cur->name, (const xmlChar *) "hyp" ) ) {
			if ( strstr ( xmlNodeListGetString(doc, cur->xmlChildrenNode, 1), hyp) != NULL ) {
				/* Found Hypothesis */
				i = 1; /* signal delayed renaming */
			}
		}
		prevNode = cur;
		cur = cur->next;
		/* delayed renaming */
		if (i == 1) {
			/* rename */
			tmp = G_malloc ((signed) (sizeof (xmlChar) * (strlen (xmlNodeListGetString(doc, prevNode->xmlChildrenNode, 1)) + 1)));
			tmp = xmlNodeListGetString(doc, prevNode->xmlChildrenNode, 1);
			/* make a buffer large enough to hold new set name */
			result = G_malloc ((sizeof (xmlChar) * (MAX_HYP_CHARS*2)) + 1);
			strcpy (result,"");			
			/* call tokenizer */
			for (j = 0; j < get_no_singletons (tmp); j ++) {
				tmp2 = get_singleton (tmp,j);
				//fprintf (stderr,"\tTOKEN %i of %i: %s\n",j,get_no_singletons (tmp), tmp2);
				if ( !strcmp (tmp2, hyp) ) {
					/* replace this token */
					if ( j > 0 ) strcat (result,",");
					strcat (result,newname);
				} else {
					/* append unmodified token */
					if ( j > 0 ) strcat (result,",");
					strcat (result,tmp2);
				}
				G_free (tmp2);
			}
			strcpy (tmp,result);
			xmlNodeSetContent(prevNode->xmlChildrenNode, result);
			i = 0;
			G_free (tmp);
			G_free (result);
		}
	}
	
	/* save changes */
	xmlSaveFormatFile (xmlfile, doc, 1);		
}

/* attach a constant bpn value to a hypothesis */
void attach_const ( double bpa, char* hyp, int precision ) {	
	char *tmp;
	int i = 0;
	float result;
	xmlNodePtr parentNode;
	xmlNodePtr prevNode;

	prevNode = NULL;
	
	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
			}
		}
		prevNode = cur;
		cur = cur->next;
	}
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
		
	/* convert back to str and store with user-defined precision */
	i = 0;
	result = bpa;
	while ( result > 1 ) {
		result = result / 10;
		i ++;
	}
	/* get enough memory to store the number */
	tmp = G_malloc ((signed) (sizeof (xmlChar) * i * (precision + 2)));
	sprintf (tmp,"%2$.*1$f",precision,bpa);
	
	/* check, if a CONST property already exists. If so, add this one. */
	i = 0;
	parentNode = prevNode;	
	cur = prevNode->xmlChildrenNode; /* go to first child */	
	while ((cur != NULL)){
		/* found an attached const bpa */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "const"))) {
			i = 1;
			/* read attribute value */
			if ( (!xmlStrcmp((const xmlChar *) 
				xmlNodeListGetString(doc, cur->xmlChildrenNode, 1), tmp))) {
				/* Has same value: issue warning */
				G_fatal_error ("Const bpn value '%s' already attached to hypothesis '%s'.\n", tmp,hyp);
			}
		}
		cur = cur->next;
	}
		
	/* add another child node and store CONST bpa */
	xmlNewTextChild (parentNode,NULL,"const",tmp);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	G_free (tmp);
}

/* attach a raster map to a hypothesis */
void attach_rast ( char *rastmap, char* hyp ) {	
	int i = 0;
	xmlNodePtr parentNode;
	xmlNodePtr prevNode;

	prevNode = NULL;
	
	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
			}
		}
		prevNode = cur;
		cur = cur->next;
	}
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* check, if raster map exists in mapset search path */
	if ( G_find_cell (rastmap,"" ) == NULL ) {
		G_fatal_error ("Raster map '%s' not found in current search path.\n",rastmap);
	}	
	
	/* check, if a rast sibling already exists. */
	i = 0;
	parentNode = prevNode;	
	cur = prevNode->xmlChildrenNode; /* go to first child */	
	while ((cur != NULL)){
		/* found an attached raster map */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "rast"))) {
			i = 1;
			/* read text of sibling */
			if ( (!xmlStrcmp((const xmlChar *) 
				xmlNodeListGetString(doc, cur->xmlChildrenNode, 1), rastmap))) {
				/* Has same value: issue warning */
				G_fatal_error ("Raster map '%s' already attached to hypothesis '%s'.\n", rastmap,hyp);
			}
		}
		cur = cur->next;
	}
		
	/* add another child node and store rast map */
	xmlNewTextChild (parentNode,NULL,"rast",rastmap);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);
}

/* attach a vector map to a hypothesis */
void attach_vect ( char *vectmap, char *attname, char* hyp ) {
	int i = 0;
	xmlNodePtr parentNode;
	xmlNodePtr prevNode;

	prevNode = NULL;
	
	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
			}
		}
		prevNode = cur;
		cur = cur->next;
	}
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* check, if vector map exists in mapset search path */
	if ( G_find_vector (vectmap,"" ) == NULL ) {
		G_fatal_error ("Vector map '%s' not found in current search path.\n",vectmap);
	}	
	
	/* check, if a vect sibling already exists.  */
	i = 0;
	parentNode = prevNode;	
	cur = prevNode->xmlChildrenNode; /* go to first child */	
	while ((cur != NULL)){
		/* found an attached vector map */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "vect"))) {
			i = 1;
			/* read text of sibling */
			if ( (!xmlStrcmp((const xmlChar *) 
				xmlNodeListGetString(doc, cur->xmlChildrenNode, 1), vectmap))) {
				/* Has same value: issue warning */
				G_fatal_error ("Vector map '%s' already attached to hypothesis '%s'.\n", vectmap,hyp);
			}
		}
		cur = cur->next;
	}
		
	/* add another child node and store vect map */
	prevNode = xmlNewTextChild (parentNode,NULL,"vect",vectmap);
	
	i = 0;
	/*
	result = fuzzyness;
	while ( result > 1 ) {
		result = result / 10;
		i ++;
	}
	tmp = G_malloc (sizeof (xmlChar) * i * (precision + 2));
	sprintf (tmp,"%2$.*1$f",precision,fuzzyness);	
	*/
			
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);
}


/* remove all evidence from a hypothesis */
void attach_null ( char *hyp ) {
	int i = 0;
	xmlNodePtr prevNode;

	prevNode = NULL;
	
	/* check if Hypothesis exists in knowledge base */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	while ((cur != NULL) && ( i ==0 ) ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* Found Hypothesis */
				i = 1; /* this exits the while loop */
				prevNode = cur;
			}
		}
		cur = cur->next;
	}
	
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}

	i = 0;
	cur = prevNode->xmlChildrenNode; /* go to first child */	
	/* walk through all siblings and delete if necessary */
	while ((cur != NULL)){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "const"))) {
			i = 1; /* this signals delayed deletion */
		}
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "rast"))) {
			i = 1;
		}
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "vect"))) {
			i = 1;
		}
		prevNode = cur;
		cur = cur->next;
		if ( i == 1 ) {
			/* remove evidence from hyp */
			xmlUnlinkNode (prevNode);
			xmlFreeNode (prevNode);
			i = 0;
		}
	}
		
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);		
}


/* detaches an evidence from ALL hypotheses
 detaches an evidence from ONE selected hypothesis, if *hyp != NULL, i.e.
 if the user has specified a hypothesis name on the command line
 type may be: const,rast,vect,*
 use prune=* to prune all evidence of a specified type
 use hyp=* to prune evidence from all Hyps
 use type=* to prune evidence of all types
 use any combination of the above (with care)!
*/
void prune ( char *evidence, char *hyp, char *type ) {

	int i = 0;
	xmlNodePtr parentNode;
	xmlNodePtr prevNode;
	
	//fprintf (stderr,"PRUNE: EVI=%s, HYP=%s, TYP=%s\n",evidence, hyp, type);
	
	if ( strcmp (hyp,"*") != 0 ) {
		/* user wants to prune only a single hypothesis: check if it exists */
		/* check if Hypothesis exists in knowledge base */
		/* start at the root of the XML file */
		cur = xmlDocGetRootElement(doc);
		/* get the first child node of the root */
		/* the child nodes contain the hypotheses */
		cur = cur->xmlChildrenNode;
		/* parse all hypotheses nodes */
		while ((cur != NULL) && ( i ==0 ) ){
			/* found a Hypothesis node! */
			if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
				if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
					/* Found Hypothesis */
					i = 1; /* this exits the while loop */
				}
			}
			prevNode = cur;
			cur = cur->next;
		}	
	
		if ( i != 1 ) {
			G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
		}		
	}
	
	/* traverse the XML tree and delete all references to evidence */
	/* start at the root of the XML file */
	cur = xmlDocGetRootElement(doc);
	/* get the first child node of the root */
	/* the child nodes contain the hypotheses */
	cur = cur->xmlChildrenNode;
	/* parse all hypotheses nodes */
	i = 0;
	while ( cur != NULL ){
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			parentNode = cur->xmlChildrenNode; /* go to first child */						
			if ( strcmp (hyp,"*") != 0 ) { /* user has specified a hyp to prune */
				fprintf (stderr,"HYP=%s\n",hyp);
				if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) 
					  xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				    /* only delete from user-specified hypothesis */					
					while ((parentNode != NULL)){
						/* walk through all siblings and delete if necessary */
						if ((!xmlStrcmp(parentNode->name, (const xmlChar *) type))) {
							fprintf (stderr,"\tTYPE=%s\n",type);
							/* found evidence of the type to be deleted */
							if ( strcmp (evidence,"*") != 0 ) { /* delete only specified evidence */
								fprintf (stderr,"\t\tEVI=%s\n",evidence);
								if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) 
					  			xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1) ))) {
									i = 1;								
								} 
							}
							else { /* delete all evidence */	
								fprintf (stderr,"\t\tEVI=ALL\n");
								if ( is_evidence (xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1)) ) {
									i = 1; /* this signals delayed deletion */
									fprintf (stderr,"\t\t\tPRUNE\n");
								}								
							}
						}
						if ( !strcmp (type,"*") ) { /* user wants to prune all types! */
							fprintf (stderr,"\tTYPE=ALL\n");
							if ( strcmp (evidence,"*") != 0 ) { /* delete only specified evidence */
								if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) 
					  				xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1) ))) {
									i = 1;								
								} 
							}
							else { /* delete all evidence */	
								fprintf (stderr,"\t\tEVI=ALL\n");
								if ( is_evidence (xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1)) ) {								
									i = 1; /* this signals delayed deletion */
								}
							}							
						}
						prevNode = parentNode;
						parentNode = parentNode->next;
						if ( i == 1 ) {
							/* remove evidence from hyp */
							xmlUnlinkNode (prevNode);
							xmlFreeNode (prevNode);
							i = 0;
						}
					}
				}
			} 
			else { /* prune all hyps */
				fprintf (stderr,"HYP=ALL\n");				
				while ((parentNode != NULL)){
					/* walk through all siblings and delete if necessary */
					if ((!xmlStrcmp(parentNode->name, (const xmlChar *) type))) {
						/* found evidence of the type to be deleted */
						if ( strcmp (evidence,"*") != 0 ) {
							fprintf (stderr,"\tTYPE=%s\n",type);
							if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) 
					  		xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1) ))) {
								i = 1;
							}
						} else { /* user wants to delete all evidences */
							fprintf (stderr,"\t\tEVI=ALL\n");
							if ( is_evidence (xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1)) ) {
								i = 1; /* this signals delayed deletion */
							}
						}
					}
					if ( !strcmp (type,"*") ) { /* user wants to prune all types! */
						fprintf (stderr,"\tTYPE=ALL\n");
						if ( strcmp (evidence,"*") != 0 ) { /* delete only specified evidence */
							fprintf (stderr,"\t\tEVI=%s\n",evidence);
							if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) 
					 				xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1) ))) {
								i = 1;								
							} 
						}
						else { /* delete all type of evidence */
							fprintf (stderr,"\t\tEVI=ALL\n");							
							if ( is_evidence (xmlNodeListGetString(doc, parentNode->xmlChildrenNode, 1)) ) {							
								i = 1; /* this signals delayed deletion */
							}
						}							
					}					
					prevNode = parentNode;
					parentNode = parentNode->next;
					if ( i == 1 ) {
						/* remove evidence from hyp */
						xmlUnlinkNode (prevNode);
						xmlFreeNode (prevNode);
						i = 0;
					}
				}				
			}	
		}
		cur = cur->next;
	}

	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);		
	
}

int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *file;
		struct Option *add;
		struct Option *del;
		struct Option *ren;
		struct Option *newname;
		struct Option *cnst;
		struct Option *rast;
		struct Option *vect;
		struct Option *att;
		struct Option *null;
		struct Option *prune;		
		struct Option *hyp;
		struct Option *type;		
		struct Option *precision;
	}
	parm;

	FILE *kb; /* knowledge base */
	char *tmp;
	
	G_gisinit ( argv[0] );

	tmp = (char*) G_malloc (255 * sizeof(char));

	int num_actions;

	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Manages the contents of a Dempster-Shafer knowledge base.";
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);

	/* Parameters */
	parm.file = G_define_option ();
	parm.file->key = "file";
	parm.file->type = TYPE_STRING;
	parm.file->required = YES;
	parm.file->description = "Filename of the knowledge base to modify";
	
	parm.add = G_define_option ();
	parm.add->key = "add";
	parm.add->type = TYPE_STRING;
	parm.add->required = NO;
	parm.add->description = "Add a user (singleton) hypothesis to the knowledge base";
		
	parm.del = G_define_option ();
	parm.del->key = "delete";
	parm.del->type = TYPE_STRING;
	parm.del->required = NO;
	parm.del->description = "Delete a hypothesis from the knowledge base";
	
	parm.ren = G_define_option ();
	parm.ren->key = "rename";
	parm.ren->type = TYPE_STRING;
	parm.ren->required = NO;
	parm.ren->description = "Rename a hypothesis in the knowledge base";
	
	parm.newname = G_define_option ();
	parm.newname->key = "to";
	parm.newname->type = TYPE_STRING;
	parm.newname->required = NO;
	parm.newname->description = "New name for hypothesis (use with 'rename=')";

	parm.cnst = G_define_option ();	
	parm.cnst->key = "const";
	parm.cnst->type = TYPE_DOUBLE;
	parm.cnst->options = "0-1";
	parm.cnst->required = NO;
	parm.cnst->description = "Attach constant evidence to a hypothesis";
	
	parm.rast = G_define_standard_option (G_OPT_R_INPUT);
	parm.rast->key = "rast";
	parm.rast->type = TYPE_STRING;
	parm.rast->required = NO;
	parm.rast->description = "Attach a GRASS raster map as evidence to a hypothesis";
	parm.rast->gisprompt = "old,fcell,raster";

	parm.vect = G_define_standard_option (G_OPT_V_INPUT);
	parm.vect->key = "vect";
	parm.vect->type = TYPE_STRING;
	parm.vect->required = NO;
	parm.vect->description = "Attach a GRASS vector map as evidence to a hypothesis (use with 'att=')";

	parm.att = G_define_option ();
	parm.att->key = "att";
	parm.att->type = TYPE_STRING;
	parm.att->required = NO;
	parm.att->description = "Attach an attribute field as evidence to a hypothesis (use with 'vect=')";
	
	parm.null = G_define_option ();
	parm.null->key = "clean";
	parm.null->type = TYPE_STRING;
	parm.null->required = NO;
	parm.null->description = "Remove all attached evidence from a hypothesis";

	parm.prune = G_define_option ();
	parm.prune->key = "prune";
	parm.prune->type = TYPE_STRING;
	parm.prune->required = NO;
	parm.prune->description = "Remove multiple evidences from one or more hypotheses";

	parm.hyp = G_define_option ();
	parm.hyp->key = "hypothesis";
	parm.hyp->type = TYPE_STRING;
	parm.hyp->required = NO;
	parm.hyp->description = "Name of hypothesis to operate on";
	
	parm.type = G_define_option ();
	parm.type->key = "type";
	parm.type->type = TYPE_STRING;
	parm.type->required = NO;
	parm.type->options = "const,rast,vect,*";
	parm.type->description = "Type of evidence to remove (use with 'prune=')";
	
	parm.precision = G_define_option ();
	parm.precision->key = "precision";
	parm.precision->type = TYPE_INTEGER;
	parm.precision->required = NO;
	parm.precision->description = "Decimal places to store for constant evidence";
	parm.precision->answer = "3";
	parm.precision->options = "0-10";
			
	/* disable interactive mode */
	G_disable_interactive ();
	
	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}
	
	/* check if we have read/write access to knowledge base file */
	errno = 0;
	kb = fopen (parm.file->answer,"r+");
	if ( kb == NULL ) {
		G_fatal_error ("Cannot open knowledge base file for reading and writing.\nReason: %s.", strerror (errno));
	} else {
		fclose(kb);
	}
	
	/* this is necessary to produce nicely formatted output */
	xmlKeepBlanksDefault (0);
	
	xmlfile=G_strdup(parm.file->answer);
	
	/* parse the XML structure; check that we have a valid file */
	doc = xmlParseFile (xmlfile);
	if ( doc == NULL ) {
		xmlFreeDoc(doc);
		G_fatal_error ("Could not parse XML structure of knowledge base.\n");
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
	

	/* check basic parameter logic */
	num_actions = 0;

	/* add a hypothesis */	
	if ( parm.add->answer != NULL)  {
		/* user may not supply more than a singleton hypothesis */
		/* all combinations will be built automatically */
		if ( strchr (parm.add->answer, (int) ',') != NULL ) {
			G_fatal_error ("Only SINGLETON hypotheses can be created by the user.\n");
		}
		/* the NULL has a special meaning! */
		if ( strcasecmp (parm.add->answer,"NULL") == 0 ) {
			G_fatal_error ("User cannot supply a 'NULL' hypothesis; it is implicit.\n");
		}
		if ( is_evidence (parm.add->answer) ) {
			G_fatal_error ("The keyword '%s' cannot be used as a hypothesis name.\n",parm.add->answer);
		}
		num_actions ++;
	}
	
	/* delete a hypothesis */
	if ( parm.del->answer != NULL ) {
		/* user may not supply more than a singleton hypothesis */
		/* all combinations will be built automatically */
		if ( strchr (parm.del->answer, (int) ',') != NULL ) {
			G_fatal_error ("Only SINGLETON hypotheses can be deleted by the user.\n");
		}
		/* the NULL has a special meaning! */
		if ( strcasecmp (parm.del->answer,"NULL") == 0 ) {
			G_fatal_error ("User cannot delete the 'NULL' hypothesis; it is implicit.\n");
		}
		num_actions ++;
	}
	
	/* rename a hypothesis */
	if ( parm.ren->answer != NULL ) {
		/* user may not supply more than a singleton hypothesis */
		/* all combinations will be built automatically */
		if ( strchr (parm.ren->answer, (int) ',') != NULL ) {
			G_fatal_error ("Only SINGLETON hypotheses can be renamed by the user.\n");
		}
		/* the NULL has a special meaning! */
		if ( strcmp (parm.ren->answer,"NULL") == 0 ) {
			G_fatal_error ("User cannot rename the 'NULL' hypothesis; it is implicit.\n");
		}		
		/* a new filename must also be provided */
		if ( parm.newname->answer == NULL ) {
			G_fatal_error ("Please also provide a new name using 'new='.\n");
		}
		if ( is_evidence (parm.newname->answer) ) {
			G_fatal_error ("The keyword '%s' cannot be used as a hypothesis name.\n",parm.newname->answer);
		}
		num_actions ++;
	}

	/* attach evidence of different types */
	/* CONST value */
	if ( parm.cnst->answer !=  NULL ) {
	 	if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis using 'hyp='.\n");
		}
	 	num_actions ++;
	}

	/* RAST */
	if ( parm.rast->answer != NULL ) {
	 	if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis using 'hyp='.\n");
		}
	 	num_actions ++;
	}

	/* ATTRIBUTE NAME */
	if ( parm.att->answer != NULL ) {
	 	if ( parm.vect->answer == NULL ) {
			G_fatal_error ("Please provide a vector map using 'vect='.\n");
		}
	 	num_actions ++;
	}

	/* VECT */
	if ( parm.vect->answer != NULL ) {
	 	if ( parm.att->answer == NULL ) {
			G_fatal_error ("Please provide an attribute field using 'att='.\n");
		}
	 	if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis using 'hyp='.\n");
		}
	 	num_actions ++;
	}

	/* NULL = remove all evidence from a hypothesis */
	if ( parm.null->answer != NULL ) {
		/* user wants to remove evidence from a hypothesis */
		num_actions ++;
	}

	/* prune evidence */
	if ( parm.prune->answer != NULL ) {
		if ( parm.hyp->answer == NULL ) {
			G_fatal_error
			("Please provide name of hypothesis to prune (or '*' for all) using 'hyp='.\n");
		}
		if ( parm.type->answer == NULL ) {
			G_fatal_error ("Provide type of evidence to prune (or '*' for all) using 'type='.\n");
		}
		/* NULL has a special meaning! */
		if ( parm.hyp->answer != NULL ) {
			if ( strcmp (parm.hyp->answer,"NULL") == 0 ) {
				G_fatal_error ("Evidence cannot be pruned from the 'NULL' hypothesis.\n");
			}
		}
		num_actions ++;
	}

	/* Exactly one action given? */
	if ( num_actions != 1 ) {
		G_fatal_error ("Please specify exactly one action to perform on the knowledge base.\n");
	}

	/* Run the chosen action */
	if ( parm.add->answer != NULL)  {
		add_hypothesis (parm.add->answer);
	}
	if ( parm.del->answer != NULL ) {
		del_hypothesis (parm.del->answer);
	}
	if ( parm.ren->answer != NULL ) {
		ren_hypothesis (parm.ren->answer, parm.newname->answer);
	}
	if ( parm.cnst->answer !=  NULL ) {
		/* user wants to attach a constant bpa value to a hypothesis */
		attach_const (atof (parm.cnst->answer),parm.hyp->answer,atoi(parm.precision->answer));
	}
	if ( parm.rast->answer != NULL ) {
		/* user wants to attach a raster map to a hypothesis */
		attach_rast ( parm.rast->answer, parm.hyp->answer);
	}
	if ( parm.vect->answer != NULL ) {
		attach_vect ( parm.vect->answer, parm.att->answer, parm.hyp->answer );
	}
	if ( parm.null->answer != NULL ) {
		attach_null (parm.null->answer);
	}
	if ( parm.prune->answer != NULL ) {
		prune ( parm.prune->answer, parm.hyp->answer, parm.type->answer );
	}
		
	G_free (tmp);
	xmlFree(cur);
	xmlFree(doc);		
	G_free (xmlfile);
	
	exit (EXIT_SUCCESS);
}
