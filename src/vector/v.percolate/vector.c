/***********************************************************************/
/*
   vector.c

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include "vector.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

long int read_input_vector(char *input_name, char *input_field)
{
    long int numlines = 0;
    long int numpoints = 0;
    long int i;
    int type;
    int attributeType = 0;
    struct Map_info V_points;
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct field_info *FieldInfo = NULL;
    dbDriver *Driver = NULL;
    dbCatValArray AttributeArray;
    dbValue *attributeValue = NULL;
    dbColumn *attributeColumn;
    dbString attributeString;

    Vect_set_open_level(1);

    int temp = Vect_open_old2(&V_points, input_name, "", input_field);

    if (temp == -1) {
        /* Should never get here as Vect_open_old2 exits on failure */
        G_fatal_error(_("Failed to open input map <%s>"), input_name);
    }

    /* If id field specified open database connection */

    if (doName) {
        db_CatValArray_init(&AttributeArray);
        if (!(FieldInfo = Vect_get_field(
                  &V_points, Vect_get_field_number(&V_points, input_field))))
            G_fatal_error(_("Database connection not defined for layer <%s>"),
                          input_field);
        if ((Driver = db_start_driver_open_database(
                 FieldInfo->driver, FieldInfo->database)) == NULL)
            G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                          FieldInfo->database, FieldInfo->driver);
        else {
#ifdef VALIDATE
            fprintf(stderr, "Opened database for attribute table\n");
#endif
            db_set_error_handler_driver(Driver);
        }

        db_get_column(Driver, FieldInfo->table, input_id_col, &attributeColumn);
        if (attributeColumn) {
            attributeType = db_get_column_sqltype(attributeColumn);
            attributeValue = db_get_column_value(attributeColumn);
            db_free_column(attributeColumn);
            db_init_string(&attributeString);
        }
        else {
            G_fatal_error(_("No such column  <%s>"), input_id_col);
        }
    }

    /* Read points from vector map */

    Vect_rewind(&V_points);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    while ((type = Vect_read_next_line(&V_points, Points, Cats)) > 0) {
        numlines++;
        if (type == GV_POINT) {
            numpoints++;
        }
    }

    Vect_rewind(&V_points);
    if (numlines != numpoints) {
        G_fatal_error(_("Input Vector map must only contain GV_POINTs"));
        exit(EXIT_FAILURE);
    }

#ifdef VALIDATE
    fprintf(stderr, "\nNumber of points in input file = %ld\n", numpoints);
    fprintf(stderr, "Number of lines in input file = %ld\n\n", numlines);
    fprintf(stderr, "Points are:\n");
    fflush(stderr);
#endif

    /* Allocate node and group lists */

    nodeList = constructNodeArray(numpoints);
    /*nodeList = (node*) G_malloc(sizeof(node) * numpoints); */
    /* TODO: Waste of memory - replace with dynamically grown linked list? */
    groupList = (node **)G_malloc(sizeof(node *) * (numpoints + 1));

    for (i = 0; i < numpoints; ++i) {
        type = Vect_read_next_line(&V_points, Points, Cats);
        nodeList[i].cat = *Cats->cat;
        nodeList[i].x = *Points->x;
        nodeList[i].y = *Points->y;
        /* strcpy (nodeList[i].name, ""); */

        /* If id field specified then associate attribute value */
        if (doName) {
            /* TODO: Suspect this is inefficient since it runs a query on
               the key for each point.  I'm doing this because I'm not
               certain that the order of points is necesarily preserved in
               all associated database tables */

            if (db_select_value(Driver, FieldInfo->table, FieldInfo->key,
                                *Cats->cat, input_id_col, attributeValue) > 0) {
                db_convert_value_to_string(attributeValue, attributeType,
                                           &attributeString);
                /* TODO: Very low-level access; there must be a better way to do
                 * this! */
                if (strlen(attributeString.string) <= (NAME_LEN)) {
                    strcpy(nodeList[i].name, attributeString.string);
                }
                else {
                    strncpy(nodeList[i].name, attributeString.string,
                            (NAME_LEN));
                    nodeList[i].name[NAME_LEN] = '\0';
                    G_warning(
                        _("ID value %s truncated to %s for point (cat = %d)"),
                        attributeString.string, nodeList[i].name, *Cats->cat);
                }
            }
            else {
                G_warning(_("No ID for point (cat = %d)"), *Cats->cat);
                strcpy(nodeList[i].name, "");
            }
        }

#ifdef VALIDATE
        fprintf(stderr, "%ld\tcat: %ld\tID:%s\tX:%f\tY:%f\t\n", i,
                nodeList[i].cat, nodeList[i].name, nodeList[i].x,
                nodeList[i].y);
#endif
    }

    if (doName) {
        db_free_string(&attributeString);
    }
    db_close_database_shutdown_driver(Driver);
    Vect_close(&V_points);

    G_message(_("\nLoaded %ld points from <%s>"), numpoints, input_name);

    return numpoints;
}
