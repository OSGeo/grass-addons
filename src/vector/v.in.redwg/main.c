/* **************************************************************
 *
 *  MODULE:       v.in.redwg
 *
 *  AUTHOR:       Rodrigo Rodrigues da Silva
 *                based on original code by Radim Blazek
 *
 *  PURPOSE:      Import of DWG files (using free software lib)
 *
 *  COPYRIGHT:    (C) 2001, 2010 by the GRASS Development Team
 *
 *                This program is free software under the
 *                GNU General Public License (>=v2).
 *                Read the file COPYING that comes with GRASS
 *                for details.
 *
 * **************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fcntl.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include <dwg.h>
#include "global.h"

int cat;
int n_elements; /* number of processed elements (only low level elements) */
int n_skipped; /* number of skipped low level elements (different layer name) */
struct Map_info Map;
dbDriver *driver;
dbString sql;
dbString str;
struct line_pnts *Points;
struct line_cats *Cats;
char *Txt;
char *Block;
struct field_info *Fi;
TRANS *Trans; /* transformation */
int atrans;   /* number of allocated levels */
struct Option *layers_opt;
struct Flag *invert_flag, *circle_flag;

int import_object(Dwg_Object *obj);

void list_layers(Dwg_Data *dwg);

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *out_opt, *in_opt;
    struct Flag *z_flag, *l_flag, *int_flag;
    char buf[2000];
    long unsigned int i;
    short initerror;

    /* DWG */
    Dwg_Data dwg;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("import"));
    G_add_keyword("DWG");
    module->description = _("Converts DWG to GRASS vector map");

    in_opt = G_define_standard_option(G_OPT_F_INPUT);
    in_opt->description = _("Name of DWG file");

    out_opt = G_define_standard_option(G_OPT_V_OUTPUT);
    out_opt->required = YES;

    layers_opt = G_define_option();
    layers_opt->key = "layers";
    layers_opt->type = TYPE_STRING;
    layers_opt->required = NO;
    layers_opt->multiple = YES;
    layers_opt->description = _("List of layers to import");

    invert_flag = G_define_flag();
    invert_flag->key = 'i';
    invert_flag->description =
        _("Invert selection by layers (don't import layers in list)");

    z_flag = G_define_flag();
    z_flag->key = 'z';
    z_flag->description = _("Create 3D vector map");

    circle_flag = G_define_flag();
    circle_flag->key = 'c';
    circle_flag->description = _("Write circles as points (centre)");

    l_flag = G_define_flag();
    l_flag->key = 'l';
    l_flag->description = _("List available layers and exit");

    int_flag = G_define_flag();
    int_flag->key = 'n';
    int_flag->description = _("Use numeric type for attribute \"layer\"");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    db_init_string(&sql);
    db_init_string(&str);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    Block = NULL;

    atrans = 20; /* nested, recursive levels */
    Trans = (TRANS *)G_malloc(atrans * sizeof(TRANS));

    /* Init LibreDWG, load file */

    initerror = dwg_read_file(in_opt->answer, &dwg);

    if (initerror) {
        sprintf(buf, _("Unable to initialize LibreDWG. Error: %d."), initerror);
        sprintf(buf, _("Unable to load file %s"), in_opt->answer);
        G_fatal_error(buf);
    }

    // List layers (if option chosen)
    if (l_flag->answer) {
        list_layers(&dwg);
        // XXX: should I really exit? maybe other options should be checked
        exit(EXIT_SUCCESS);
    }

    /* open output vector */
    Vect_open_new(&Map, out_opt->answer, z_flag->answer);

    Vect_hist_command(&Map);

    /* Add DB link */
    Fi = Vect_default_field_info(&Map, 1, NULL, GV_1TABLE);
    Vect_map_add_dblink(&Map, 1, NULL, Fi->table, "cat", Fi->database,
                        Fi->driver);

    driver = db_start_driver_open_database(Fi->driver,
                                           Vect_subst_var(Fi->database, &Map));
    if (driver == NULL) {
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Vect_subst_var(Fi->database, &Map), Fi->driver);
    }
    db_begin_transaction(driver);

    /* Create table */
    if (int_flag->answer) { /* List layers */
        sprintf(buf,
                "create table %s ( cat integer, entity_name varchar(20), color "
                "int, weight int, "
                "layer real, block varchar(100), txt varchar(100) )",
                Fi->table);
    }
    else {
        sprintf(buf,
                "create table %s ( cat integer, entity_name varchar(20), color "
                "int, weight int, "
                "layer varchar(100), block varchar(100), txt varchar(100) )",
                Fi->table);
    }
    db_set_string(&sql, buf);
    G_debug(3, db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
        db_close_database(driver);
        db_shutdown_driver(driver);
        G_fatal_error(_("Unable to create table: '%s'"), db_get_string(&sql));
    }

    if (db_create_index2(driver, Fi->table, "cat") != DB_OK)
        G_warning(_("Unable to create index for table <%s>, key <%s>"),
                  Fi->table, "cat");

    if (db_grant_on_table(driver, Fi->table, DB_PRIV_SELECT,
                          DB_GROUP | DB_PUBLIC) != DB_OK)
        G_fatal_error(_("Unable to grant privileges on table <%s>"), Fi->table);

    cat = 1;
    n_elements = n_skipped = 0;

    /* Write each entity. Some entities may be composed by other entities (like
     * INSERT or BLOCK) */
    /* Set transformation for first (index 0) level */
    Trans[0].dx = Trans[0].dy = Trans[0].dz = 0;
    Trans[0].xscale = Trans[0].yscale = Trans[0].zscale = 1;
    Trans[0].rotang = 0;

    for (i = 0; i < dwg_get_num_objects(&dwg); i++) {
        fprintf(stdout, "Type: %u\n", dwg.object[i].type);
    }
    fprintf(stdout, "%lu objects\n", dwg_get_num_objects(&dwg));
    fflush(stdout);

    for (i = 0; i < dwg_get_num_objects(&dwg); i++) {
        if (import_object(&dwg.object[i])) {
            // pass i pointer since write_entity may process more than one
            // entity
            write_entity(&dwg.object[i], &dwg.object, &i, 0);
        }
    }

    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    Vect_build(&Map); //, stderr);
    Vect_close(&Map);

    if (n_skipped > 0)
        G_message(_("%d elements skipped (layer name was not in list)"),
                  n_skipped);

    G_done_msg(_("%d elements processed"), n_elements);

    exit(EXIT_SUCCESS);
}

void list_layers(Dwg_Data *dwg)
{
    int i;
    long unsigned int l_count = dwg_get_layer_count(dwg);

    G_debug(2, "%lu layers\n", l_count);
    fprintf(stdout, "%lu layers\n", l_count);

    Dwg_Object_LAYER **layers = dwg_get_layers(dwg);

    for (i = 0; i < l_count; i++) {
        fprintf(stdout, "NAME: %s COLOR: %lu STATE: ", layers[i]->name,
                layers[i]->color.rgb);
        if (layers[i]->on)
            fprintf(stdout, "ON, ");
        else
            fprintf(stdout, "OFF, ");
        if (layers[i]->frozen)
            fprintf(stdout, "FROZEN, ");
        else
            fprintf(stdout, "THAWED, ");
        if (layers[i]->locked)
            fprintf(stdout, "LOCKED\n");
        else
            fprintf(stdout, "UNLOCKED\n");
    }
    G_free(layers);
}

int import_object(Dwg_Object *obj)
{
    if (obj->supertype != DWG_SUPERTYPE_ENTITY)
        return 0;

    if (layers_opt->answers) {
        Dwg_Object_LAYER *layer = dwg_get_entity_layer(obj->tio.entity);
        int i = 0;
        int layer_found = 0;
        // FIXME check if layer is purged
        if (42 /*layer->purgedflag*/) {
            while (layers_opt->answers[i]) {
                if (strcmp((char *)layer->name, layers_opt->answers[i]) == 0) {
                    layer_found = 1;
                    break;
                }
                i++;
            }
        }

        if ((!invert_flag->answer && !layer_found) ||
            (invert_flag->answer && layer_found)) {
            if (is_low_level(obj))
                n_skipped++;
            if (obj->type != DWG_TYPE_INSERT &&
                obj->type != DWG_TYPE_POLYLINE_2D &&
                obj->type != DWG_TYPE_POLYLINE_3D &&
                obj->type != DWG_TYPE_POLYLINE_MESH &&
                obj->type != DWG_TYPE_POLYLINE_PFACE)
                return 0;
        }
    }
    return 1;
}
