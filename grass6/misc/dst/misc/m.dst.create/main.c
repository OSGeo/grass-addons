/*
	Creates a new XML file on disk with the basic structure
	of a Dempster Shafer knowledge base.

	Any existing file of the same name will be overwritten!

*/


#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

#include <grass/gis.h>

int
main (int argc, char *argv[])
{
	struct GModule *module;
	struct
	{
		struct Option *file;
	}
	parm;
	
	FILE *kb; /* knowledge base */
	
	xmlDocPtr doc;
	xmlNodePtr cur;
	xmlNodePtr root;

	
	/* setup some basic GIS stuff */
	G_gisinit (argv[0]);
	module = G_define_module ();
	module->description = "Creates a new Dempster-Shafer knowledge base file.";
	
	/* do not pause after a warning message was displayes */
	G_sleep_on_error (0);

	/* Parameters */
	parm.file = G_define_option ();
	parm.file->key = "file";
	parm.file->type = TYPE_STRING;
	parm.file->required = YES;
	parm.file->description = "Filename for the new knowledge base";

	/* parse command line */
	if (G_parser (argc, argv))
	{
		exit (-1);
	}
	
	/* existing files will be overwritten! */
	errno = 0;
	kb = fopen (parm.file->answer,"w+");
	if ( kb == NULL ) {
		G_fatal_error ("Cannot open knowledge base file for writing.\nReason: %s.", strerror (errno));
	} else {
		fclose(kb);
	}
	
	/* create basic XML structure */
	root = xmlNewNode(NULL, (xmlChar *) "dst-kb");
	xmlSetProp(root,(xmlChar*) "N_SINGLETONS", (xmlChar*) "0");
	/* the NULL hypotheses (empty set) is implicit */
	xmlSetProp(root,(xmlChar*) "N_HYPOTHESES", (xmlChar*) "1");
	/* initial number of groups in the knowledge base */
	xmlSetProp(root,(xmlChar*) "N_GROUPS", (xmlChar*) "0");
	
	xmlNewTextChild (root, NULL, "hyp", "NULL");
	
	doc = xmlNewDoc("1.0");
	xmlDocSetRootElement(doc, root);
	cur = xmlDocGetRootElement(doc);
	cur = cur->xmlChildrenNode;
	xmlSetProp(cur,(xmlChar*) "TYPE", (xmlChar*) "NULL");
	
	if (xmlSaveFormatFile (parm.file->answer, doc, 1) == -1) {
		G_fatal_error ("Error creating XML file.\n");
	}	
	
	exit (EXIT_SUCCESS));
}
