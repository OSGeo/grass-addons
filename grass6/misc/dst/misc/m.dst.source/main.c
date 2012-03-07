#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

#include <grass/gis.h>

#define MAX_GROUP_CHARS 32

/* TODO:
	- update number of groups after deletion!
*/

int N_SINGLETONS = 0; /* number of singletons in knowledge base */
int N_HYPOTHESES = 0; /* number of hypotheses in knowledge base */
int N_GROUPS = 0; /* number of groups in knowledge base */
char *xmlfile; /* file name of knowledge base */
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

/* returns 1, if name is rast,vect or const */
/* 0 otherwise */
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

	/* get a fully qualified, absolute path and filename for */
	/* reading/writing the XML database file. */
	/* What to do on a DOS system? Let's hope that libxml handles it!*/
	xmlfile=G_strdup(filename );
	
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
	N_GROUPS = atoi (xmlGetProp(cur, "N_GROUPS"));		
}


void add_group (char *name) {
	
	xmlNodePtr cur;
	xmlChar *tmp;
	
	/* parse all group nodes */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while (cur != NULL) {
		/* found a Hypothesis node! */
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) name, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				/* there already is a group with this name! */
				G_fatal_error ("Group '%s' already exists in the knowledge base.\n",
					(const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));
			}
		}
	cur = cur->next;
	}
	
	/* add new group to root of XML doc */
	cur = xmlDocGetRootElement(doc);
	xmlNewTextChild (cur, NULL, (xmlChar*) "grp", (xmlChar*) name);
	/* increase number of stored groups by one */
	N_GROUPS ++;
	tmp = G_malloc (sizeof (xmlChar) * 100);
	sprintf (tmp,"%i",N_GROUPS);
	xmlSetProp(cur,(xmlChar*) "N_GROUPS", (xmlChar*) tmp);
	G_free (tmp);	
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);	
}


void del_group ( char *name ) {
	int i = 0;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr hypNode;
	xmlNodePtr evidenceNode;	

	prev = NULL;
	hypNode = NULL;
	evidenceNode = NULL;
	
	/* PASS 1: delete the group itself */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) name, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}	
	
	if ( i != 1 ) {
		G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",name);
	}

	xmlUnlinkNode (prev);
	xmlFreeNode (prev);
	
	
	/* PASS 2: delete all references to the group */	
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
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
							if ( !xmlStrcmp ( (xmlChar*) name, (const xmlChar *) 
								xmlNodeListGetString(doc, evidenceNode->xmlChildrenNode, 1)) ) {
									i = 1;									
							}
						}
						prev = evidenceNode;
						evidenceNode = evidenceNode->next;
						if ( i == 1 ) { /* delayed deletion */
							xmlUnlinkNode (prev);
							xmlFreeNode (prev);			
							i = 0;
						}						
					}					
				}
				hypNode = hypNode->next;
			}			
		}
		prev = cur;
		cur = cur->next;
	}		
	
	
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);		
}


void ren_group ( char *name, char *newname ) {

	int i = 0;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr hypNode;
	xmlNodePtr evidenceNode;	

	prev = NULL;
	hypNode = NULL;
	evidenceNode = NULL;
	
	/* PASS 1: rename the group itself */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) name, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}	
	
	if ( i != 1 ) {
		G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",name);
	}
	
	xmlNodeSetContent(prev->xmlChildrenNode, newname);
	
	/* PASS 2: rename all references to the group */
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
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
							if ( !xmlStrcmp ( (xmlChar*) name, (const xmlChar *) 
								xmlNodeListGetString(doc, evidenceNode->xmlChildrenNode, 1)) ) {
									i = 1;									
							}
						}
						prev = evidenceNode;
						evidenceNode = evidenceNode->next;
						if ( i == 1 ) { /* delayed renaming */
							xmlNodeSetContent(prev->xmlChildrenNode, newname);							
							i = 0;
						}						
					}					
				}
				hypNode = hypNode->next;
			}			
		}
		prev = cur;
		cur = cur->next;
	}		


	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);	
}

/* assign CONST evidence *evidence from *hyp to *group */
void assign_const ( char *evidence, char *hyp, char *group ) {
		
	int i = 0;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr parent;
	xmlNodePtr hypParent;
	xmlNodePtr cur2;
	xmlNodePtr delete;

	prev = NULL;
	cur2 = NULL;
	delete = NULL;	
		
	/* 1. check, if the group exists */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) group, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",group);
	}
	
	/* 2. check, if the hypothesis exists */
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* 3. check, if the evidence exists in that hypothesis */
	i = 0;
	hypParent = prev;
	cur = prev->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "const"))) {
			if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */				
			}
		}
		prev = cur;
		cur = cur->next;
	}			
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis has no CONST evidence with value '%s'.\n",evidence);
	}	
	parent = prev;
	/* 4. check, if CONST evidence in this hyp has already been assigned to the group */
	/*    if so, delete all old references. */
	i = 0;
	cur = hypParent->xmlChildrenNode;
	while ( (cur != NULL) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "const"))) {
			cur2 = cur->xmlChildrenNode;
			while ( cur2 != NULL ) {
				if ( (!xmlStrcmp((const xmlChar *) "assign", (const xmlChar *) cur2->name ))) {							
					if ((!xmlStrcmp((const xmlChar *) group, (const xmlChar *) 
							xmlNodeListGetString(doc, cur2->xmlChildrenNode, 1) ))) {
						/* found an assignment for this group! */
						/* mark for delayed deletion */
						i = 1;								
					}
				}
				delete = cur2;
				cur2 = cur2->next;
			}
		}
		prev = cur;
		cur = cur->next;
		if ( i == 1 ) {
			G_warning ("Removing old CONST value of '%s' for hyp. '%s', group '%s'.\n",evidence,hyp,group);
			/* remove old assignment */
			xmlUnlinkNode ( delete );
			xmlFreeNode ( delete );
			i = 0;
		}
	}			
	
	/* 5. add a new child to the evidence node that refers to the group */
	cur = xmlNewTextChild (parent, NULL, (xmlChar*) "assign", (xmlChar*) group);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);		
	xmlFree (parent);		
	xmlFree (hypParent);		
}

void assign_rast ( char *evidence, char *hyp, char *group ) {
		
	int i = 0;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr parent;
	xmlNodePtr hypParent;
	xmlNodePtr cur2;
	xmlNodePtr delete;
	
	prev = NULL;
	cur2 = NULL;
	delete = NULL;
		
	/* 1. check, if the group exists */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) group, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",group);
	}
	
	/* 2. check, if the hypothesis exists */
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* 3. check, if the evidence exists in that hypothesis */
	i = 0;
	hypParent = prev;
	cur = prev->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "rast"))) {
			if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */				
			}
		}
		prev = cur;
		cur = cur->next;
	}			
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis has no RAST evidence '%s'.\n",evidence);
	}	
	parent = prev;
	/* 4. check, if RAST evidence in this hyp has already been assigned to the group */
	/*    if so, delete all old references. */
	i = 0;
	cur = hypParent->xmlChildrenNode;
	while ( (cur != NULL) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "rast"))) {
			cur2 = cur->xmlChildrenNode;
			while ( cur2 != NULL ) {
				if ( (!xmlStrcmp((const xmlChar *) "assign", (const xmlChar *) cur2->name ))) {							
					if ((!xmlStrcmp((const xmlChar *) group, (const xmlChar *) 
							xmlNodeListGetString(doc, cur2->xmlChildrenNode, 1) ))) {
						/* found an assignment for this group! */
						/* mark for delayed deletion */
						i = 1;								
					}
				}
				delete = cur2;
				cur2 = cur2->next;
			}
		}
		prev = cur;
		cur = cur->next;
		if ( i == 1 ) {
			G_warning ("Removing RAST link '%s' for hyp. '%s', group '%s'.\n",evidence,hyp,group);
			/* remove old assignment */
			xmlUnlinkNode ( delete );
			xmlFreeNode ( delete );
			i = 0;
		}
	}			
	
	/* 5. add a new child to the evidence node that refers to the group */
	cur = xmlNewTextChild (parent, NULL, (xmlChar*) "assign", (xmlChar*) group);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);
	xmlFree (parent);		
	xmlFree (hypParent);
}

void assign_vect ( char *evidence, char *hyp, char *group ) {
		
	int i = 0;
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr parent;
	xmlNodePtr hypParent;
	xmlNodePtr cur2;
	xmlNodePtr delete;
	
	prev = NULL;
	cur2 = NULL;
	delete = NULL;
		
	/* 1. check, if the group exists */
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
			if ( (!xmlStrcmp((const xmlChar *) group, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",group);
	}
	
	/* 2. check, if the hypothesis exists */
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */
				
			}
		}
		prev = cur;
		cur = cur->next;
	}		
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
	}
	
	/* 3. check, if the evidence exists in that hypothesis */
	i = 0;
	hypParent = prev;
	cur = prev->xmlChildrenNode;
	while ((cur != NULL) && ( i ==0 ) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "vect"))) {
			if ( (!xmlStrcmp((const xmlChar *) evidence, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
				i = 1; /* this exits the while loop */				
			}
		}
		prev = cur;
		cur = cur->next;
	}			
	if ( i != 1 ) {
		G_fatal_error ("Hypothesis has no VECT evidence '%s'.\n",evidence);
	}	
	parent = prev;
	/* 4. check, if VECT evidence in this hyp has already been assigned to the group */
	/*    if so, delete all old references. */
	i = 0;
	cur = hypParent->xmlChildrenNode;
	while ( (cur != NULL) ){
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "vect"))) {
			cur2 = cur->xmlChildrenNode;
			while ( cur2 != NULL ) {
				if ( (!xmlStrcmp((const xmlChar *) "assign", (const xmlChar *) cur2->name ))) {							
					if ((!xmlStrcmp((const xmlChar *) group, (const xmlChar *) 
							xmlNodeListGetString(doc, cur2->xmlChildrenNode, 1) ))) {
						/* found an assignment for this group! */
						/* mark for delayed deletion */
						i = 1;								
					}
				}
				delete = cur2;
				cur2 = cur2->next;
			}
		}
		prev = cur;
		cur = cur->next;
		if ( i == 1 ) {
			G_warning ("Removing VECT link '%s' for hyp. '%s', group '%s'.\n",evidence,hyp,group);
			/* remove old assignment */
			xmlUnlinkNode ( delete );
			xmlFreeNode ( delete );
			i = 0;
		}
	}			
	
	/* 5. add a new child to the evidence node that refers to the group */
	cur = xmlNewTextChild (parent, NULL, (xmlChar*) "assign", (xmlChar*) group);
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);		
	xmlFree (parent);		
	xmlFree (hypParent);	
}


void prune ( char* group, char* hyp, char* type ) {
	
	xmlNodePtr cur;
	xmlNodePtr prev;
	xmlNodePtr hypNode;
	xmlNodePtr typeNode;
	int i = 0;
		
	prev = NULL;
	hypNode = NULL;
	typeNode = NULL;	
		
	/* 1. check, if the group exists */
	if ( strcmp ("*",group) != 0 ) {
		cur = xmlDocGetRootElement(doc);
		cur = cur->xmlChildrenNode;
		while ((cur != NULL) && ( i ==0 ) ){
			if ((!xmlStrcmp(cur->name, (const xmlChar *) "grp"))) {
				if ( (!xmlStrcmp((const xmlChar *) group, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
					i = 1; /* this exits the while loop */					
				}
			}
			prev = cur;
			cur = cur->next;
		}		
		if ( i != 1 ) {
			G_fatal_error ("Group '%s' does not exist in the knowledge base.\n",group);
		}
	}
	
	if ( strcmp ("*",hyp) != 0 ) {
	/* 2. check, if the hypothesis exists */
		i = 0;
		cur = xmlDocGetRootElement(doc);
		cur = cur->xmlChildrenNode;
		while ((cur != NULL) && ( i ==0 ) ){
			if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
				if ( (!xmlStrcmp((const xmlChar *) hyp, (const xmlChar *) xmlNodeListGetString(doc, cur->xmlChildrenNode, 1) ))) {
					i = 1; /* this exits the while loop */				
				}
			}
			prev = cur;
			cur = cur->next;
		}		
		if ( i != 1 ) {
			G_fatal_error ("Hypothesis '%s' does not exist in the knowledge base.\n",hyp);
		}
	}
	
	/* walk thru whole XML tree and delete all references if necessary */
	i = 0;
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	while ( (cur != NULL) ) {
		if ((!xmlStrcmp(cur->name, (const xmlChar *) "hyp"))) {
			hypNode = cur->xmlChildrenNode;
			fprintf (lp,"HYP\n");
			/* check all evidence entries */
			while ( hypNode != NULL ) {
				if ( is_evidence ( (xmlChar*) hypNode->name) ) {
					fprintf (lp,"\tEVIDENCE\n");
					/* check all evidence childs */
					typeNode = hypNode->xmlChildrenNode;
					while ( typeNode != NULL ) {
						/* check all assigns */
						if ( !xmlStrcmp (typeNode->name, "assign") ) {
								fprintf (lp,"\t\tEVIDENCE\n");
								i = 1;									
						}
						prev = typeNode;
						typeNode = typeNode->next;
						if ( i == 1 ) { /* delayed deletion */
							fprintf (lp,"\t\tCHECK:\n");
							/* check if assignment is to current group */
							fprintf (lp,"\t\t\t1. GROUP (%s) ?\n",xmlNodeListGetString(doc, prev->xmlChildrenNode, 1));							
							if ( (!xmlStrcmp ( (xmlChar*) group, (const xmlChar *) 
								xmlNodeListGetString(doc, prev->xmlChildrenNode, 1))) ||
								(strcmp (group,"*") ) ) {									
									fprintf (lp,"\t\t\t1. GROUP=YES\n");
									fprintf (lp,"\t\t\t2. TYPE (%s) ?\n",hypNode->name);							
								if ( (!strcmp (hypNode->name,type)) || (!strcmp (type,"*")) ) {
									fprintf (lp,"\t\t\t2. TYPE = YES\n");
									fprintf (lp,"\t\t\t3. HYP (%s) ?\n",xmlNodeListGetString(doc, cur->xmlChildrenNode, 1));							
									if ( (!xmlStrcmp ( (xmlChar*) hyp, (const xmlChar *) 
										xmlNodeListGetString(doc, cur->xmlChildrenNode, 1))) ||
										(strcmp (group,"*") ) ) {
										fprintf (lp,"\t\t\t3. HYP = YES\n");
										fprintf (lp,"\t\t\t->PURGE\n");
									}
								}
							}							
							i = 0;
						}						
					}					
				}
				hypNode = hypNode->next;
			}			
		}
		prev = cur;
		cur = cur->next;
	}	
	
	
	/* save changes to XML file */
	xmlSaveFormatFile (xmlfile, doc, 1);

	xmlFree (cur);				
}

int
main (int argc, char *argv[])
{
	FILE *kb;
	
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
		struct Option *null; /* delete all references to a group from a hyp */
		struct Option *prune; /* group, hyp, type */						
		struct Option *group;
		struct Option *hyp;
		struct Option *type;	
	}
	parm;

	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);	
	module = G_define_module ();
	module->description = "Manages sources of evidence in a DST knowledge base file.";
	
	/* do not pause after a warning message was displayed */
	G_sleep_on_error (0);

	/* Parameters */
	parm.file = G_define_option ();
	parm.file->key = "file";
	parm.file->type = TYPE_STRING;
	parm.file->required = YES;
	parm.file->description = "Name of the knowledge base file";

	parm.add = G_define_option ();
	parm.add->key = "add";
	parm.add->type = TYPE_STRING;
	parm.add->required = NO;
	parm.add->description = "Source of evidence to add to the knowledge base";
	
	parm.del = G_define_option ();
	parm.del->key = "delete";
	parm.del->type = TYPE_STRING;
	parm.del->required = NO;
	parm.del->description = "Source of evidence to delete from the knowledge base";
	
	parm.ren = G_define_option ();
	parm.ren->key = "rename";
	parm.ren->type = TYPE_STRING;
	parm.ren->required = NO;
	parm.ren->description = "Source of evidence to rename in the knowledge base";
	
	parm.newname = G_define_option ();
	parm.newname->key = "new";
	parm.newname->type = TYPE_STRING;
	parm.newname->required = NO;
	parm.newname->description = "New name for source of evidence (use with 'ren=')";

	parm.cnst = G_define_option ();
	parm.cnst->key = "const";
	parm.cnst->type = TYPE_DOUBLE;
	parm.cnst->required = NO;
	parm.cnst->description = "Attach constant value evidence to a source of evidence";

	parm.rast = G_define_standard_option (G_OPT_R_INPUT);
	parm.rast->key = "rast";
	parm.rast->type = TYPE_STRING;
	parm.rast->required = NO;
	parm.rast->description = "Attach a GRASS raster map to a source of evidence";
	parm.rast->gisprompt = "old,fcell,raster";

	parm.vect = G_define_standard_option (G_OPT_V_INPUT);
	parm.vect->key = "vect";
	parm.vect->type = TYPE_STRING;
	parm.vect->required = NO;
	parm.vect->description = "Attach a GRASS vector map to a source of evidence";
		
	parm.null = G_define_option ();
	parm.null->key = "clean";
	parm.null->type = TYPE_STRING;
	parm.null->required = NO;
	parm.null->description = "Remove all sources of evidence from a hypothesis";

	parm.prune = G_define_option ();
	parm.prune->key = "prune";
	parm.prune->type = TYPE_STRING;
	parm.prune->required = NO;
	parm.prune->description = "Remove multiple sources of evidence from one or more hypotheses";

	parm.group = G_define_option ();
	parm.group->key = "source";
	parm.group->type = TYPE_STRING;
	parm.group->required = NO;
	parm.group->description = "Source of evidence to operate on";
	
	parm.hyp = G_define_option ();
	parm.hyp->key = "hypothesis";
	parm.hyp->type = TYPE_STRING;
	parm.hyp->required = NO;
	parm.hyp->description = "Hypothesis to operate on";
	
	parm.type = G_define_option ();
	parm.type->key = "type";
	parm.type->type = TYPE_STRING;
	parm.type->required = NO;
	parm.type->options = "const,rast,vect,*";
	parm.type->description = "Type of evidence to remove (use with 'prune=')";
		
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
	open_xml_file ( parm.file->answer );
	
	/* send output to terminal */
	lp = stderr;
	
	/* get action from command line */
	/* add a group */	
	if ( parm.add->answer != NULL)  {
		/* the NULL has a special meaning! */
		if ( strcmp (parm.add->answer,"NULL") == 0 ) {
			G_fatal_error ("'NULL' cannot be used as group name.\n");
		}
		if ( is_evidence (parm.add->answer) ) {
			G_fatal_error ("The keyword '%s' cannot be used as a group name.\n",parm.add->answer);
		}	
		/* hypothesis names must conform to same restrictions as filenames */
		if ( G_legal_filename (parm.add->answer) != 1 ) {
			G_fatal_error ("Group name invalid (contains special chars, whitespace or other).\n");
		}
		/* hypothesis names cannot have more than 32 chars */
		if ( strlen (parm.add->answer) > (MAX_GROUP_CHARS) ) {
			G_fatal_error ("Group names cannot be longer than %i characters.\n",
							MAX_GROUP_CHARS);
		}	
		/* cannot use TMP as hypothesis name */
		if ( !strcmp (parm.add->answer,"TMP") ) {
			G_fatal_error ("Group name 'TMP' is a reserved name. Please choose another one.\n");
		}		
		add_group (parm.add->answer);
	}	
	/* delete a group */
	if ( parm.del->answer != NULL ) {
		del_group (parm.del->answer);
	}
	/* rename a group */
	if ( parm.ren->answer != NULL)  {
		if ( parm.newname->answer == NULL ) {
			G_fatal_error ("Please provide a new group name using 'newname='.\n");
		}
		/* the NULL has a special meaning! */
		if ( strcmp (parm.newname->answer,"NULL") == 0 ) {
			G_fatal_error ("'NULL' cannot be used as group name.\n");
		}
		if ( is_evidence (parm.newname->answer) ) {
			G_fatal_error ("The keyword '%s' cannot be used as a group name.\n",parm.add->answer);
		}	
		/* hypothesis names must conform to same restrictions as filenames */
		if ( G_legal_filename (parm.newname->answer) != 1 ) {
			G_fatal_error ("Group name invalid (contains special chars, whitespace or other).\n");
		}
		/* hypothesis names cannot have more than 32 chars */
		if ( strlen (parm.newname->answer) > (MAX_GROUP_CHARS) ) {
			G_fatal_error ("Group names cannot be longer than %i characters.\n",
							MAX_GROUP_CHARS);
		}	
		/* cannot use TMP as hypothesis name */
		if ( !strcmp (parm.newname->answer,"TMP") ) {
			G_fatal_error ("Group name 'TMP' is a reserved name. Please choose another one.\n");
		}		
		ren_group (parm.ren->answer, parm.newname->answer);
	}		
	/* define CONST evidence for group */
	if ( parm.cnst->answer !=  NULL ) {
		if ( parm.group->answer == NULL ) {
			G_fatal_error ("Please provide a group name using 'group='.\n");
		}
		if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis name using 'hyp='.\n");
		}		
		assign_const ( parm.cnst->answer, parm.hyp->answer, parm.group->answer);
	}	
	
	/* define RAST evidence for group */
	if ( parm.rast->answer !=  NULL ) {
		if ( parm.group->answer == NULL ) {
			G_fatal_error ("Please provide a group name using 'group='.\n");
		}
		if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis name using 'hyp='.\n");
		}		
		assign_rast ( parm.rast->answer, parm.hyp->answer, parm.group->answer);
	}

	/* define VECT evidence for group */
	if ( parm.vect->answer !=  NULL ) {
		if ( parm.group->answer == NULL ) {
			G_fatal_error ("Please provide a group name using 'group='.\n");
		}
		if ( parm.hyp->answer == NULL ) {
			G_fatal_error ("Please provide a hypothesis name 'hyp='.\n");
		}		
		assign_vect ( parm.vect->answer, parm.hyp->answer, parm.group->answer );
	}
	
	/* prune group assignment(s) */
	if ( parm.prune->answer != NULL ) {
		if ( parm.hyp->answer == NULL ) {			
			G_fatal_error ("Please provide a hypothesis name (or '*' for all hypotheses) using 'hyp='.\n");
		}
		if ( parm.type->answer == NULL ) {
			G_fatal_error ("Please provide a type name (or '*' for all types) using 'type='.\n");
		}
		prune ( parm.prune->answer, parm.hyp->answer, parm.type->answer);
	}		

	xmlFree(doc);

	G_free (xmlfile);
	
	exit (EXIT_SUCCESS);
}
