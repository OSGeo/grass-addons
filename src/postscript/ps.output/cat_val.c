/* File: cat_val.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "vector.h"

static char catval_str[128];

/* LOAD CAT_VAL */
int load_catval_array(VECTOR * vector, const char *colname,
		      dbCatValArray * cvarr)
{
    int n_records;
    struct field_info *Fi;
    dbDriver *driver;

    db_CatValArray_init(cvarr);

    Fi = Vect_get_field(&(vector->Map), vector->layer);
    if (Fi == NULL) {
	G_fatal_error(_("Unable to get layer info for vector map"));
    }

    driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (driver == NULL)
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      Fi->database, Fi->driver);

    n_records =
	db_select_CatValArray(driver, Fi->table, Fi->key, colname, NULL,
			      cvarr);

    if (n_records < 0)
	G_fatal_error(_("Unable to select data from table"));

    db_close_database_shutdown_driver(driver);

    return n_records;
}


/* GET CAT_VAL */

/* return a double number from a dbCatValArray */
void get_number(dbCatValArray * cvarr, int cat, double *d)
{
    int ret, int_val;
    dbCatVal *cv = NULL;

    *d = -1.;

    if (cvarr->ctype == DB_C_TYPE_INT) {
	ret = db_CatValArray_get_value_int(cvarr, cat, &int_val);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
	else
	    *d = (double)int_val;
    }
    else if (cvarr->ctype == DB_C_TYPE_DOUBLE) {
	ret = db_CatValArray_get_value_double(cvarr, cat, d);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
    }
    else if (cvarr->ctype == DB_C_TYPE_STRING) {
	ret = db_CatValArray_get_value(cvarr, cat, &cv);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
	else
	    *d = atof(db_get_string(cv->val.s));
    }
}

/* return a string from a dbCatValArray */
char *get_string(dbCatValArray * cvarr, int cat, int dec)
{
    int ret, int_val;
    double double_val;
    dbCatVal *cv = NULL;
    char buf[10], *str = NULL;

    if (cvarr->ctype == DB_C_TYPE_STRING) {
	ret = db_CatValArray_get_value(cvarr, cat, &cv);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
	else
	    str = db_get_string(cv->val.s);
    }
    else if (cvarr->ctype == DB_C_TYPE_INT) {
	ret = db_CatValArray_get_value_int(cvarr, cat, &int_val);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
	else {
	    sprintf(catval_str, "%d", int_val);
	    str = catval_str;
	}
    }
    else if (cvarr->ctype == DB_C_TYPE_DOUBLE) {
	ret = db_CatValArray_get_value_double(cvarr, cat, &double_val);
	if (ret != DB_OK) {
	    G_warning(_("No record for category [%d]"), cat);
	}
	else {
	    sprintf(buf, "%%0.%df", dec);
	    sprintf(catval_str, buf, double_val);
	    str = catval_str;
	}
    }
    return str;
}
