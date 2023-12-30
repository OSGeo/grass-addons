#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#include "local_proto.h"

void write_ply_header(FILE *fp, const struct Map_info *Map,
                      const char *input_opt, const char *field_opt,
                      const char **columns, int n_vertices, int dp)
{
    int num_dblinks, i;

    struct field_info *fi;
    dbDriver *driver = NULL;
    dbHandle handle;
    dbString table_name;
    dbTable *table;
    char *dbltype;

    if (dp > 7)
        dbltype = G_store("double");
    else
        dbltype = G_store("float");

    fprintf(fp, "ply\n");
    fprintf(fp, "format ascii 1.0\n");
    fprintf(fp, "comment GRASS GIS generated\n");
    fprintf(fp, "element vertex %d\n", n_vertices);
    fprintf(fp, "property %s x\n", dbltype);
    fprintf(fp, "property %s y\n", dbltype);
    if (Map->head.with_z)
        fprintf(fp, "property %s z\n", dbltype);

    if (columns) {
        num_dblinks = Vect_get_num_dblinks(Map);

        if (num_dblinks <= 0) {
            G_fatal_error(
                _("Database connection for map <%s> is not defined in DB file"),
                input_opt);
        }

        if ((fi = Vect_get_field2(Map, field_opt)) == NULL)
            G_fatal_error(_("Database connection not defined for layer <%s>"),
                          field_opt);
        driver = db_start_driver(fi->driver);
        if (driver == NULL)
            G_fatal_error(_("Unable to open driver <%s>"), fi->driver);
        db_init_handle(&handle);
        db_set_handle(&handle, fi->database, NULL);
        if (db_open_database(driver, &handle) != DB_OK)
            G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                          fi->database, fi->driver);
        db_init_string(&table_name);
        db_set_string(&table_name, fi->table);
        if (db_describe_table(driver, &table_name, &table) != DB_OK) {
            db_close_database(driver);
            db_shutdown_driver(driver);
            G_fatal_error(_("Unable to describe table <%s>"), fi->table);
        }

        for (i = 0; columns[i]; i++) {

            switch (db_column_Ctype(driver, fi->table, columns[i])) {
            case DB_C_TYPE_INT: {
                if (strcmp(columns[i], "red") == 0 ||
                    strcmp(columns[i], "green") == 0 ||
                    strcmp(columns[i], "blue") == 0 ||
                    strcmp(columns[i], "alpha") == 0)

                    fprintf(fp, "property uchar %s\n", columns[i]);
                else
                    fprintf(fp, "property int %s\n", columns[i]);
                break;
            }
            case DB_C_TYPE_DOUBLE: {
                fprintf(fp, "property %s %s\n", dbltype, columns[i]);
                break;
            }
            case -1: {
                db_close_database(driver);
                db_shutdown_driver(driver);
                G_fatal_error(_("Column <%s> not found in table <%s>"),
                              columns[i], fi->table);
            }
            default: {
                db_close_database(driver);
                db_shutdown_driver(driver);
                G_fatal_error(_("Column <%s>: unsupported data type <%s>"),
                              columns[i],
                              db_sqltype_name(db_column_sqltype(
                                  driver, fi->table, columns[i])));
            }
            }
        }

        db_close_database(driver);
        db_shutdown_driver(driver);
    }

    fprintf(fp, "element face 0\n");
    fprintf(fp, "property list uchar int vertex_indices\n");
    fprintf(fp, "end_header\n");
}
