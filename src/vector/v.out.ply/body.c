#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int write_ply_body_ascii(FILE *fp, struct Map_info *Map, int dp, int region,
                         int field, const char **columns, struct bound_box *box)
{
    int type, i, cat, n_lines, line;
    static struct line_pnts *Points;
    struct line_cats *Cats;
    char *fs = G_store(" ");
    struct ilist *fcats;

    /* columns */
    struct field_info *Fi = NULL;
    dbDriver *driver = NULL;
    dbValue value;
    dbHandle handle;
    int ncats, more;
    dbTable *Table;
    dbString dbstring;
    dbColumn *Column;
    dbValue *Value;
    char buf[2000];
    dbCursor cursor;
    int *coltypes = NULL;
    char *all_columns = NULL;

    n_lines = ncats = 0;

    G_zero(&value, sizeof(dbValue));
    db_init_string(&dbstring);

    if (columns) {
        int len_all = 0;

        Fi = Vect_get_field(Map, field);
        if (!Fi) {
            G_fatal_error(_("Database connection not defined for layer %d"),
                          field);
        }

        driver = db_start_driver(Fi->driver);
        if (!driver)
            G_fatal_error(_("Unable to start driver <%s>"), Fi->driver);

        db_init_handle(&handle);
        db_set_handle(&handle, Fi->database, NULL);

        if (db_open_database(driver, &handle) != DB_OK)
            G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                          Fi->database, Fi->driver);

        i = 0;
        while (columns[i])
            len_all += strlen(columns[i++]);

        coltypes = G_malloc(i * sizeof(int));

        all_columns = G_malloc(len_all + i + 2);

        i = 0;
        strcpy(all_columns, columns[0]);
        while (columns[i]) {
            coltypes[i] = db_column_Ctype(driver, Fi->table, columns[i]);
            if (i > 0) {
                strcat(all_columns, ",");
                strcat(all_columns, columns[i]);
            }
            i++;
        }
        G_debug(1, "all column string: %s", all_columns);
    }

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    fcats = Vect_new_list();

    /* by default, read_next_line will NOT read Dead lines */
    /* but we can override that (in Level I only) by specifying */
    /* the type  -1, which means match all line types */

    Vect_rewind(Map);

    line = 0;
    while (TRUE) {
        type = Vect_read_next_line(Map, Points, Cats);
        if (type == -1) { /* failure */
            if (columns) {
                db_close_database(driver);
                db_shutdown_driver(driver);
            }

            return -1;
        }

        if (type == -2) { /* EOF */
            if (columns) {
                db_close_database(driver);
                db_shutdown_driver(driver);
            }
            break;
        }
        if (!(type & GV_POINT))
            continue;

        if (region &&
            !Vect_point_in_box(Points->x[0], Points->y[0], Points->z[0], box))
            continue;

        if (field > 0 && !(Vect_cat_get(Cats, field, &cat)))
            continue;

        line++;

        sprintf(buf, "%.*f", dp, Points->x[0]);
        G_trim_decimal(buf);
        fprintf(fp, "%s", buf);

        sprintf(buf, "%.*f", dp, Points->y[0]);
        G_trim_decimal(buf);
        fprintf(fp, "%s%s", fs, buf);

        /* z coord */
        if (Map->head.with_z) {
            sprintf(buf, "%.*f", dp, Points->z[0]);
            G_trim_decimal(buf);
            fprintf(fp, "%s%s", fs, buf);
        }

        Vect_reset_list(fcats);
        Vect_field_cat_get(Cats, field, fcats);

        if (fcats->n_values > 1) {
            G_warning(_("Feature has more categories. Only first category (%d) "
                        "is exported."),
                      fcats->value[0]);
        }

        /* print attributes */
        if (columns) {

            sprintf(buf, "SELECT %s FROM %s WHERE %s = %d", all_columns,
                    Fi->table, Fi->key, fcats->value[0]);
            G_debug(2, "SQL: %s", buf);
            db_set_string(&dbstring, buf);

            if (db_open_select_cursor(driver, &dbstring, &cursor,
                                      DB_SEQUENTIAL) != DB_OK) {
                db_close_database(driver);
                db_shutdown_driver(driver);
                G_fatal_error(_("Cannot select attributes for cat = %d"),
                              fcats->value[0]);
            }
            if (db_fetch(&cursor, DB_NEXT, &more) != DB_OK) {
                db_close_database(driver);
                db_shutdown_driver(driver);
                G_fatal_error(_("Unable to fetch data from table"));
            }

            Table = db_get_cursor_table(&cursor);

            for (i = 0; columns[i]; i++) {

                /* original
                if (db_select_value(driver, Fi->table, Fi->key, fcats->value[0],
                                    columns[i], &value) < 0)
                    G_fatal_error(_("Unable to select record from table <%s>
                (key %s, column %s)"), Fi->table, Fi->key, columns[i]);
                */

                Column = db_get_table_column(Table, i);
                Value = db_get_column_value(Column);

                if (db_test_value_isnull(Value)) {
                    fprintf(fp, "%s", fs);
                }
                else {
                    switch (coltypes[i]) {
                    case DB_C_TYPE_INT: {
                        if (strcmp(columns[i], "red") == 0 ||
                            strcmp(columns[i], "green") == 0 ||
                            strcmp(columns[i], "blue") == 0 ||
                            strcmp(columns[i], "alpha") == 0)

                            fprintf(fp, "%s%d", fs, db_get_value_int(Value));
                        else
                            fprintf(fp, "%s%d", fs, db_get_value_int(Value));
                        break;
                    }
                    case DB_C_TYPE_DOUBLE: {
                        fprintf(fp, "%s%.*f", fs, dp,
                                db_get_value_double(Value));
                        break;
                    }
                    case DB_C_TYPE_STRING: {
                        break;
                    }
                    case DB_C_TYPE_DATETIME: {
                        break;
                    }
                    case -1: {
                        db_close_database(driver);
                        db_shutdown_driver(driver);
                        G_fatal_error(_("Column <%s> not found in table <%s>"),
                                      columns[i], Fi->table);
                    }
                    default: {
                        db_close_database(driver);
                        db_shutdown_driver(driver);
                        G_fatal_error(_("Column <%s>: unsupported data type"),
                                      columns[i]);
                    }
                    }
                }
            }
            db_close_cursor(&cursor);
        }

        fprintf(fp, "\n");
        n_lines++;
    }

    db_free_string(&dbstring);
    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    return n_lines;
}
