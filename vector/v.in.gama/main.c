
/************************************************************************/
/*                                                                      */
/* v.in.gama - convert GNU GaMa XML output file to                      */
/*             a GRASS vector map layer                                 */
/*                                                                      */
/* Martin Landa, 5/2006                                                 */
/*                                                                      */
/* This file is part of GRASS GIS. It is free software. You can         */
/* redistribute it and/or modify it under the terms of                  */
/* the GNU General Public License as published by the Free Software     */
/* Foundation; either version 2 of the License, or (at your option)     */
/* any later version.                                                   */
/*                                                                      */

/************************************************************************/

#define MAIN
#include <unistd.h>
#include "global.h"

int main(int argc, char *argv[])
{
    FILE *input_xml_file, *tables_xml_file;

    struct Map_info Map;
    struct GModule *module;

    xmlDoc *doc, *tables_doc;
    dbString path_tables_xml;

    G_gisinit(argv[0]);

    module = G_define_module();

    module->description = _("Converts GNU GaMa XML output file "
			    "to a GRASS vector map layer.");

    /* parse command line */
    parse_command_line(argc, argv);

    /* open temporary file - needed? */
    char *tmp;
    FILE *tmpfile;

    tmp = G_tempfile();
    tmpfile = fopen(tmp, "w+");

    if (tmpfile == NULL) {
	G_fatal_error(_("Unable to open temp file '%s'"), tmp);
    }

    unlink(tmp);
    fclose(tmpfile);

    /*
       this initialize the library and check potential ABI mismatches
       between the version it was compiled for and the actual shared
       library used.
     */
    LIBXML_TEST_VERSION;

    /* read input file 
       open the XML file and get the DOM */
    if (options.input) {
	input_xml_file = fopen(options.input, "r");
	if (!input_xml_file) {
	    G_fatal_error(_("Unable to open input file '%s'"),
			  options.input);
	}
	doc = xmlReadFile(options.input, NULL, 0);
    }
    else {
	/* doc = xmlReadFile ("-", NULL, 0); */
	doc = xmlReadFd(0, NULL, NULL, 0);
    }

    if (doc == NULL) {
	G_fatal_error("Parsing file '%s' failed", options.input);
    }

    G_debug(1, "input XML file opened");

    /* open the output vector map */
    Vect_open_new(&Map, options.output, is_3d_map(doc));

    /* metadata */
    write_head(&Map, doc);

    Vect_hist_command(&Map);

    /* create empty attribute table */
    if (options.dotable) {
	db_init_string(&path_tables_xml);

	db_set_string(&path_tables_xml, G_gisbase());
	db_append_string(&path_tables_xml, "/etc/");
	db_append_string(&path_tables_xml, G_program_name());
	db_append_string(&path_tables_xml, "/tables.xml");

	tables_xml_file = fopen(db_get_string(&path_tables_xml), "r");

	if (!tables_xml_file) {
	    G_fatal_error(_("Unable to open file '%s'"),
			  db_get_string(&path_tables_xml));
	}

	tables_doc = xmlReadFile(db_get_string(&path_tables_xml), NULL, 0);

	if (!tables_doc) {
	    G_fatal_error(_("Unable to parse parse file '%s'"),
			  db_get_string(&path_tables_xml));
	}

	create_tables(&Map, tables_doc);

	xmlFreeDoc(tables_doc);

	if (tables_xml_file) {
	    fclose(tables_xml_file);
	}
    }

    /* point data
       -> insert attribute data (layer 1) and create vector points 
       observation data
       -> insert attribute data (layer 2) and create vector lines */
    create_map(&Map, doc, options.dotable);

    xmlFreeDoc(doc);
    xmlCleanupParser();

    if (options.input) {
	fclose(input_xml_file);
    }

    Vect_build_partial(&Map, GV_BUILD_NONE);
    Vect_build(&Map);

    Vect_close(&Map);

    exit(EXIT_SUCCESS);
}
