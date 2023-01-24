/***************************************************************
 *
 * MODULE:       v.greedycolors
 *
 * AUTHOR(S):    Markus Metz (2021)
 *
 * PURPOSE:      Create greedy colors for vector areas
 *
 * COPYRIGHT:    (C) 2021 by the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2).  Read the file COPYING that
 *               comes with GRASS for details.
 *
 **************************************************************/

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "prb.h"

struct area_ngbrs {
    int cat;
    int clr;
    int prio;
    struct ilist *list;
};

static int cmp_an(const void *a, const void *b, void *prb_param)
{
    struct area_ngbrs *as = (struct area_ngbrs *)a;
    struct area_ngbrs *bs = (struct area_ngbrs *)b;

    if (as->prio > bs->prio)
        return -1;

    if (as->prio < bs->prio)
        return 1;

    if (as->list->n_values < bs->list->n_values)
        return -1;

    if (as->list->n_values > bs->list->n_values)
        return 1;

    if (as->clr > bs->clr)
        return -1;

    if (as->clr < bs->clr)
        return 1;

    if (as->cat < bs->cat)
        return -1;

    if (as->cat > bs->cat)
        return 1;

    return 0;
}

static int cmp_int(const void *a, const void *b)
{
    int ai = *(int *)a;
    int bi = *(int *)b;

    if (ai < bi)
        return -1;

    return (ai > bi);
}

static int first_available_clr(struct ilist *list)
{
    int free_clr = 1;
    int i;

    if (list->n_values == 0)
        return free_clr;

    if (list->n_values == 2) {
        if (list->value[0] > list->value[1]) {
            int tmpi;

            tmpi = list->value[0];
            list->value[0] = list->value[1];
            list->value[1] = tmpi;
        }
    }
    else if (list->n_values > 2) {
        qsort(list->value, list->n_values, sizeof(int), cmp_int);
    }

    if (list->value[0] > 1)
        return list->value[0] - 1;

    for (i = 0; i < list->n_values; i++) {
        if (free_clr < list->value[i])
            return free_clr;
        if (free_clr == list->value[i])
            free_clr++;
    }

    return free_clr;
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *input_opt, *field_opt, *col_opt;
    struct Map_info Map;
    const char *mapset;
    int area, nareas;
    int *areaclr, maxclr;
    int maxnbrs;
    struct ilist clrlist, bndlist;
    int line;
    int i, j, left, right, neighbor;
    int isle, nisles;
    char *outcol;
    int fieldnr;
    struct field_info *Fi;
    char buf[4096];
    dbString stmt, dbstr;
    dbDriver *driver;
    dbColumn *column;
    int cat, mincat, maxcat, catrange;
    int *area_cats;

    struct area_ngbrs *an, *anpop, *ansearch, *anreinsert;
    struct ilist *nlist, *list;
    struct prb_table *lexbfs;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("color table"));

    module->description = _("Create greedy colors for vector areas.");

    input_opt = G_define_standard_option(G_OPT_V_MAP);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);

    col_opt = G_define_standard_option(G_OPT_DB_COLUMN);
    col_opt->answer = "greedyclr";

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    mapset = G_find_vector(input_opt->answer, "");
    if (!mapset)
        G_fatal_error(_("Vector map <%s> not found"), input_opt->answer);

    if (strcmp(mapset, G_mapset()))
        G_fatal_error(_("Vector map <%s> is not in current mapset"),
                      input_opt->answer);

    /* topology required */
    if (Vect_open_old2(&Map, input_opt->answer, mapset, field_opt->answer) <
        2) {
        G_fatal_error(_("Vector map <%s> has no topology"), input_opt->answer);
    }

    nareas = Vect_get_num_areas(&Map);
    if (nareas == 0)
        G_fatal_error(_("No areas in vector map <%s>"), input_opt->answer);

    fieldnr = Vect_get_field_number(&Map, field_opt->answer);

    /* greedy colors
     * adjacent areas must have different attribute values
     * different areas can have the same attribute value,
     * as long as they are not adjacent */

    /* graph ordering:
     * the order of areas is important for a small number of greedy colors */

    /* use area cats in case different areas have the same cat */
    G_message("Collecting category values for areas");

    area_cats = G_calloc(nareas + 1, sizeof(int));

    mincat = maxcat = -1;
    for (area = 1; area <= nareas; area++) {

        G_percent(area, nareas, 4);

        cat = Vect_get_area_cat(&Map, area, fieldnr);
        area_cats[area] = cat;
        if (cat >= 0) {
            if (mincat > cat || mincat == -1)
                mincat = cat;
            if (maxcat < cat)
                maxcat = cat;
        }
    }

    if (mincat == -1) {
        G_fatal_error(
            _("Areas in vector map <%s> don't have categories in layer %d"),
            input_opt->answer, fieldnr);
    }

    if (mincat == maxcat) {
        G_fatal_error(_("All areas in vector map <%s> have the same category "
                        "in layer %d"),
                      input_opt->answer, fieldnr);
    }

    catrange = maxcat - mincat + 1;

    an = G_calloc(catrange, sizeof(struct area_ngbrs));
    nlist = G_calloc(catrange, sizeof(struct ilist));
    areaclr = G_calloc(catrange, sizeof(int));

    for (i = 0; i < catrange; i++) {
        an[i].cat = -1;
        an[i].clr = 0;
        an[i].prio = 0;
        an[i].list = &nlist[i];
        an[i].list->value = NULL;
        G_init_ilist(an[i].list);

        areaclr[i] = 0;
    }

    G_message("Collecting neighbors for areas");

    clrlist.value = NULL;
    bndlist.value = NULL;
    G_init_ilist(&clrlist);
    G_init_ilist(&bndlist);

    for (area = 1; area <= nareas; area++) {

        G_percent(area, nareas, 4);

        cat = area_cats[area];
        /* skip areas without category in current layer */
        if (cat < 0)
            continue;

        an[cat - mincat].cat = cat;

        /* outer neighbors */
        Vect_get_area_boundaries(&Map, area, &bndlist);
        for (i = 0; i < bndlist.n_values; i++) {
            line = bndlist.value[i];

            Vect_get_line_areas(&Map, abs(line), &left, &right);
            if (line > 0)
                neighbor = left;
            else
                neighbor = right;

            if (neighbor < 0) {
                neighbor = Vect_get_isle_area(&Map, -neighbor);
            }

            if (neighbor > 0 && area_cats[neighbor] >= 0 &&
                area_cats[neighbor] != area_cats[area]) {
                G_ilist_add(an[cat - mincat].list, area_cats[neighbor]);
            }
        }

        /* inner neighbors */
        nisles = Vect_get_area_num_isles(&Map, area);
        for (i = 0; i < nisles; i++) {
            isle = Vect_get_area_isle(&Map, area, i);
            Vect_get_isle_boundaries(&Map, isle, &bndlist);
            for (j = 0; j < bndlist.n_values; j++) {
                line = bndlist.value[j];

                Vect_get_line_areas(&Map, abs(line), &left, &right);
                if (line > 0)
                    neighbor = left;
                else
                    neighbor = right;

                if (neighbor < 0) {
                    neighbor = Vect_get_isle_area(&Map, -neighbor);
                }

                if (neighbor > 0 && area_cats[neighbor] >= 0 &&
                    area_cats[neighbor] != area_cats[area]) {
                    G_ilist_add(an[cat - mincat].list, area_cats[neighbor]);
                }
            }
        }
    }

    /* sort and prune neighbor lists, assign initial greedy colors */
    G_message("Assigning initial greedy colors");

    maxclr = 1;
    maxnbrs = 0;

    for (cat = 0; cat < catrange; cat++) {
        G_percent(cat, catrange, 4);

        if (an[cat].cat < 0)
            continue;

        list = an[cat].list;
        if (list->n_values == 2) {
            if (list->value[0] > list->value[1]) {
                int tmpi;

                tmpi = list->value[0];
                list->value[0] = list->value[1];
                list->value[1] = tmpi;
            }
        }
        else if (list->n_values > 2) {
            qsort(list->value, list->n_values, sizeof(int), cmp_int);
        }

        if (list->n_values > 1) {
            j = 1;
            for (i = 1; i < list->n_values; i++) {
                if (list->value[j - 1] != list->value[i]) {
                    list->value[j] = list->value[i];
                    j++;
                }
            }
            list->n_values = j;
        }
        if (maxnbrs < list->n_values)
            maxnbrs = list->n_values;

        /* collect colors assigned to neighbors */
        clrlist.n_values = 0;

        for (i = 0; i < list->n_values; i++) {
            neighbor = list->value[i] - mincat;
            if (areaclr[neighbor] > 0)
                G_ilist_add(&clrlist, areaclr[neighbor]);
        }

        /* assign initial greedy color */
        areaclr[cat] = first_available_clr(&clrlist);
        an[cat].clr = areaclr[cat];
        if (maxclr < areaclr[cat])
            maxclr = areaclr[cat];
    }
    G_percent(cat, catrange, 4);

    G_message("Maximum number of adjacent areas: %d", maxnbrs);
    G_message("Number of initial greedy colors: %d", maxclr);

    /* build initial queue for lexicographic breadth-first search */
    G_message("Initializing queue");

    lexbfs = prb_create(cmp_an, NULL, NULL);

    for (cat = 0; cat < catrange; cat++) {
        G_percent(cat, catrange, 4);

        areaclr[cat] = 0;

        if (an[cat].cat < 0)
            continue;

        if (an[cat].clr < maxclr - 2)
            an[cat].clr = 0;

        if (prb_insert(lexbfs, &an[cat]))
            G_fatal_error("Failed to insert area into queue");
    }
    G_percent(cat, catrange, 4);

    G_message("Assigning greedy color numbers to areas");

    maxclr = 1;

    i = 0;
    while ((anpop = prb_delete_first(lexbfs)) != NULL) {

        G_percent(i++, catrange, 4);

        cat = anpop->cat;
        list = anpop->list;

        /* collect colors assigned to neighbors */
        clrlist.n_values = 0;

        for (j = 0; j < list->n_values; j++) {
            neighbor = list->value[j] - mincat;
            if (areaclr[neighbor] > 0)
                G_ilist_add(&clrlist, areaclr[neighbor]);
            else {
                /* lexicographic breadth-first search:
                 * update sorting criteria */

                /* remove neighbor from queue */
                ansearch = &an[neighbor];
                anreinsert = prb_delete(lexbfs, ansearch);
                if (!anreinsert)
                    G_fatal_error("Neighbor %d is not in the queue!", neighbor);
                /* increase priority */
                anreinsert->prio++;
                /* re-insert into queue */
                if (prb_insert(lexbfs, anreinsert))
                    G_fatal_error("Failed to re-insert neighbor %d into queue",
                                  neighbor);
            }
        }
        /* assign greedy color */
        areaclr[cat - mincat] = first_available_clr(&clrlist);
        if (maxclr < areaclr[cat - mincat])
            maxclr = areaclr[cat - mincat];
    }
    G_percent(catrange, catrange, 4);

    G_message("Updating table with greedy color numbers");

    outcol = col_opt->answer;

    /* Open database driver */
    db_init_string(&stmt);
    db_init_string(&dbstr);
    driver = NULL;
    Fi = NULL;
    column = NULL;

    Fi = Vect_get_field(&Map, fieldnr);
    if (Fi == NULL)
        G_fatal_error(_("Database connection not defined for layer <%s>"),
                      field_opt->answer);

    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL)
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);

    /* check if to_column exists */
    db_get_column(driver, Fi->table, outcol, &column);
    if (column) {
        int ctype;

        ctype = db_column_Ctype(driver, Fi->table, outcol);
        if (ctype != DB_C_TYPE_INT)
            G_fatal_error("Column '%s' must be of type integer", outcol);
    }
    else {
        /* create column */
        sprintf(buf, "ALTER TABLE '%s' ADD COLUMN '%s' integer", Fi->table,
                outcol);
        db_set_string(&stmt, buf);

        db_begin_transaction(driver);
        if (db_execute_immediate(driver, &stmt) != DB_OK)
            G_fatal_error(_("Unable to add column '%s'"), outcol);

        db_commit_transaction(driver);
    }

    db_begin_transaction(driver);

    for (i = 0; i < catrange; i++) {

        G_percent(i, catrange, 4);

        cat = an[i].cat;

        if (cat < 0)
            continue;

        sprintf(buf, "update %s set %s = %d where %s = %d", Fi->table, outcol,
                areaclr[cat - mincat], Fi->key, cat);
        db_set_string(&stmt, buf);

        if (db_execute_immediate(driver, &stmt) != DB_OK)
            G_fatal_error(_("Unable to update column '%s'"), outcol);
    }
    G_percent(i, catrange, 4);

    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    Vect_close(&Map);

    G_done_msg(_("Assigned %d greedy colors."), maxclr);

    exit(EXIT_SUCCESS);
}
