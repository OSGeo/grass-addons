
/****************************************************************
 *
 * MODULE:     v.net.turntable
 *
 * AUTHOR(S):  GRASS Development Team
 *             Štěpán Turek <stepan.turek seznam.cz>
 *             
 * PURPOSE:    Create sql table representing line graph,
 *             which describes possible turns on network.
 *
 * COPYRIGHT:  (C) 2013 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

/*
   IDEA: This module could be included into v.net module 
   (both modules do service for vector network analyses)???
 */


void close_db(void *p)
{
    dbDriver *driver = (dbDriver *) p;

    db_close_database_shutdown_driver(driver);
}

int main(int argc, char *argv[])
{
    struct GModule *module;

    struct Map_info InMap, OutMap;
    struct field_info *fi;

    struct Option *opt_in_map, *opt_out_map;
    struct Option *opt_ttb_name, *opt_afield, *opt_tfield, *opt_tucfield,
	*opt_type;
    char *database_name, *driver_name;

    int i_field_num, field_num, i_field, type;

    char *ttb_name;
    char *key_col;
    int tfield, tucfield, afield;

    char buf[DB_SQL_MAX];
    dbDriver *driver;

    dbString db_buf;

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("network"));
    G_add_keyword(_("turntable"));
    G_add_keyword(_("turns"));
    module->description = _("Create table which represents turns.");

    opt_in_map = G_define_standard_option(G_OPT_V_INPUT);
    opt_out_map = G_define_standard_option(G_OPT_V_OUTPUT);

    opt_type = G_define_standard_option(G_OPT_V_TYPE);
    opt_type->options = "line,boundary";
    opt_type->answer = "line,boundary";
    opt_type->label = _("Arc type");

    opt_afield = G_define_standard_option(G_OPT_V_FIELD);
    opt_afield->description =
	_
	("Arcs layer which will be expanded by turntable. Format: layer number[/layer name]");
    opt_afield->answer = "1";
    opt_afield->key = "alayer";
    opt_afield->required = YES;

    opt_tfield = G_define_standard_option(G_OPT_V_FIELD);
    opt_tfield->description =
	_
	("Layer where turntable will be attached. Format: layer number[/layer name]");
    opt_tfield->answer = "3";
    opt_tfield->key = "tlayer";
    opt_tfield->required = YES;

    opt_tucfield = G_define_standard_option(G_OPT_V_FIELD);
    opt_tucfield->description =
	_
	("Node layer with unique categories for every line in alayer and point. The points are placed on every node. Format: layer number[/layer name]");
    opt_tucfield->answer = "4";
    opt_tucfield->key = "tuclayer";
    opt_tucfield->required = YES;

    opt_ttb_name = G_define_option();
    opt_ttb_name->key = "tname";
    opt_ttb_name->label = _("Turntable name");
    opt_ttb_name->description =
	_
	("If not given, name consists of input vector map name + \"_\" + tlayer + \"_turntable_\" + alayer e. g. roads_3_turntable_1");
    opt_ttb_name->type = TYPE_STRING;

    G_gisinit(argv[0]);

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    if (Vect_open_old(&InMap, opt_in_map->answer, "") < 2) {
	G_fatal_error(_("Unable to open vector map <%s>."),
		      opt_in_map->answer);
    }
    Vect_set_error_handler_io(&InMap, &OutMap);

    type = Vect_option_to_types(opt_type);

    afield = Vect_get_field_number(&InMap, opt_afield->answer);
    tfield = Vect_get_field_number(&InMap, opt_tfield->answer);
    tucfield = Vect_get_field_number(&InMap, opt_tucfield->answer);

    if (!Vect_get_field(&InMap, afield))
	G_fatal_error(_("Arc layer <%s> does not exists in map <%s>."),
		      opt_afield->answer, opt_out_map->answer);

    if (Vect_get_field(&InMap, tfield))
	G_warning(_
		  ("Layer <%s> already exists in map <%s>.\nIt will be overwritten by tlayer data."),
		  opt_tfield->answer, opt_out_map->answer);

    if (Vect_get_field(&InMap, tucfield))
	G_warning(_
		  ("Layer <%s> already exists in map <%s>.\nIt will be overwritten by tuclayer data."),
		  opt_tucfield->answer, opt_out_map->answer);

    ttb_name = NULL;
    if (!opt_ttb_name->answer) {
	G_asprintf(&ttb_name, "%s_%s_turntable_%s",
		   opt_out_map->answer, opt_tfield->answer,
		   opt_afield->answer);
    }
    else {
	ttb_name = G_store(opt_out_map->answer);
    }

    if (Vect_open_new(&OutMap, opt_out_map->answer, WITHOUT_Z) < 1) {
	G_fatal_error(_("Unable to create vector map <%s>."),
		      opt_out_map->answer);
    }

    /*Use database and driver as layer with lowest number, 
       if the layer is not present use def settings. */
    field_num = -1;
    for (i_field = 0; i_field < Vect_cidx_get_num_fields(&InMap); i_field++) {
	i_field_num = Vect_cidx_get_field_number(&InMap, i_field);
	if (Vect_map_check_dblink(&InMap, i_field_num, NULL) == 0)
	    continue;

	if (field_num == -1)
	    field_num = i_field_num;

	if (i_field_num != tfield && i_field_num != tucfield)
	    Vect_copy_tables(&InMap, &OutMap, i_field_num);
    }

    if (field_num < 0) {
	driver_name = (char *)db_get_default_driver_name();
	database_name = (char *)db_get_default_database_name();
    }
    else {
	fi = Vect_get_field(&InMap, field_num);
	driver_name = fi->driver;
	database_name = fi->database;
    }

    driver = db_start_driver_open_database(driver_name, database_name);
    if (driver == NULL)
	G_fatal_error(_("Unable to open database <%s> using driver <%s>"),
		      database_name, driver_name);
    G_add_error_handler(close_db, driver);

    key_col = "cat";
    sprintf(buf,
	    "CREATE TABLE %s (%s INTEGER, ln_from INTEGER, ln_to INTEGER, "
	    "cost DOUBLE PRECISION, isec INTEGER, angle DOUBLE PRECISION)",
	    ttb_name, key_col);

    db_init_string(&db_buf);
    db_set_string(&db_buf, buf);

    if (db_execute_immediate(driver, &db_buf) != DB_OK) {
	db_free_string(&db_buf);
	G_fatal_error(_("Unable to create turntable <%s>."), ttb_name);
    }
    db_free_string(&db_buf);

    if (Vect_map_add_dblink(&OutMap, tfield,
			    NULL, ttb_name, key_col,
			    database_name, driver_name) == -1) {
	G_fatal_error(_("Unable to connect table <%s> to vector map <%s>."),
		      ttb_name, opt_in_map->answer);
    }

    if (db_create_index2(driver, ttb_name, key_col) != DB_OK)
	G_warning(_("Unable to create index for column <%s> in table <%s>."),
		  key_col, ttb_name);

    Vect_build_partial(&OutMap, GV_BUILD_BASE);	/* switch to topological level */

    populate_turntable(driver, &InMap, &OutMap, ttb_name, tfield,
		       tucfield, afield, type);
    Vect_close(&InMap);

    close_db(driver);

    Vect_close(&OutMap);

    /*TODO why must be closed and opened again? */
    Vect_open_old(&OutMap, opt_out_map->answer, G_mapset());
    Vect_build(&OutMap);

    Vect_close(&OutMap);

    exit(EXIT_SUCCESS);
}
