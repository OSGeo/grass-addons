#include "global.h"

int create_tables(struct Map_info *Map, xmlDoc * doc)
{
    int i, num_of_cols, col_type, num_of_tables;

    struct field_info *fi;
    int field;

    dbDriver *driver;
    dbTable *dbtable;
    dbColumn *dbcolumn;
    dbString table_name, col_name, suffix;

    xmlNode *root, *table, *column, *name, *datatype;
    struct list_nodes *tables, *columns, *tmp_col, *tmp_tab;

    num_of_tables = 0;
    field = 1;
    dbtable = NULL;
    db_init_string(&table_name);
    db_init_string(&col_name);
    db_init_string(&suffix);

    list_init((void **)&tables);
    list_init((void **)&columns);

    root = xmlDocGetRootElement(doc);

    if (!root) {
	G_fatal_error(_("Unable to get the root element"));
    }

    if (!find_nodes(root, "table", &tables)) {
	G_fatal_error(_("Invalid table structure"));
    }
    else {
	for (tmp_tab = tables; tmp_tab; tmp_tab = tmp_tab->next) {
	    table = tmp_tab->node;
	    fi = Vect_default_field_info(Map, field, NULL, GV_1TABLE);

	    if (!fi) {
		G_fatal_error(_("Unable to get default vector layer"));
	    }

	    driver = db_start_driver_open_database(fi->driver, fi->database);
	    if (!driver) {
		G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
			      fi->database, fi->driver);
	    }

	    db_begin_transaction(driver);

	    num_of_cols = find_nodes(table, "column", &columns);
	    if (num_of_cols < 1) {
		G_fatal_error(_("Invalid table structure"));
	    }
	    else {
		dbtable = db_alloc_table(num_of_cols);
		for (tmp_col = columns, i = 0; tmp_col;
		     i++, tmp_col = tmp_col->next) {
		    column = tmp_col->node;
		    dbcolumn = db_get_table_column(dbtable, i);
		    if (!find_node(column, "name", &name) ||
			!find_node(column, "datatype", &datatype) ||
			!node_get_value_string(name, NULL, &col_name) ||
			!node_get_value_int(datatype, &col_type)) {
			G_fatal_error(_("Invalid table structure"));
		    }

		    db_set_column_name(dbcolumn, db_get_string(&col_name));
		    db_set_column_sqltype(dbcolumn, col_type);
		    if (db_get_column_sqltype(dbcolumn) ==
			DB_SQL_TYPE_CHARACTER) {
			db_set_column_length(dbcolumn, ID_LENGTH);
		    }
		}

		db_set_string(&table_name, fi->table);
		if (!node_get_value_string(table, "type", &suffix)) {
		    G_fatal_error(_("Invalid table structure"));
		}
		else {
		    db_append_string(&table_name, "_");
		    db_append_string(&table_name, db_get_string(&suffix));
		}

		fi->table = G_store(db_get_string(&table_name));	/* nasty */
		db_set_table_name(dbtable, fi->table);

		if (db_create_table(driver, dbtable) != DB_OK) {
		    G_fatal_error(_("Unable to create table"));
		}

		if (driver) {
		    db_commit_transaction(driver);
		    db_close_database_shutdown_driver(driver);
		}

		Vect_map_add_dblink(Map, field++, NULL, fi->table,
				    fi->key, fi->database, fi->driver);
		num_of_tables++;
	    }
	}
    }

    list_nodes_free(&tables);
    list_nodes_free(&columns);

    return num_of_tables;
}

void insert_point(struct field_info *fi, dbDriver * driver, dbTable * table,
		  Point * point, int cat)
{

    int i, ret;
    double coor_val;

    char *name;
    char buff[1024];

    dbColumn *column;
    dbString sql;

    db_init_string(&sql);

    sprintf(buff, "INSERT INTO %s (", fi->table);
    db_set_string(&sql, buff);

    for (i = 0; i < db_get_table_number_of_columns(table); i++) {
	column = db_get_table_column(table, i);
	if (i > 0) {
	    db_append_string(&sql, ",");
	}
	db_append_string(&sql, db_get_column_name(column));
    }

    db_append_string(&sql, ") VALUES (");

    for (i = 0; i < db_get_table_number_of_columns(table); i++) {
	column = db_get_table_column(table, i);
	name = (char *)db_get_column_name(column);

	if (i > 0) {
	    db_append_string(&sql, ",");
	}
	/* category number */
	if (!G_strcasecmp(name, "cat")) {
	    sprintf(buff, "%d", cat);
	    db_append_string(&sql, buff);
	    continue;
	}
	/* id */
	if (!G_strcasecmp(name, "id")) {
	    if (db_sizeof_string(&(point->id)) > 1) {
		if (db_sizeof_string(&(point->id)) > ID_LENGTH) {
		    G_warning
			("Only first %d characters of point id [%s] will be stored.",
			 ID_LENGTH, db_get_string(&(point->id)));
		}
		db_append_string(&sql, "'");
		db_append_string(&sql, db_get_string(&(point->id)));
		db_append_string(&sql, "'");
	    }
	    else {
		db_append_string(&sql, "NULL");
	    }
	    continue;
	}
	/* coordinates */
	ret = point_get_xyz(point, name, &coor_val);
	if (ret) {
	    if (ret == 1)
		sprintf(buff, "%f", coor_val);
	    else		/* constrained */
		sprintf(buff, "%d", (int)coor_val);

	    db_append_string(&sql, buff);
	}
	else {
	    db_append_string(&sql, "NULL");
	}
    }

    db_append_string(&sql, ")");

    G_debug(3, "SQL: %s", db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	G_fatal_error(_("Unable to insert new row: '%s'"), db_get_string(&sql));
    }

    return;
}

void insert_obs(struct field_info *fi, dbDriver * driver, dbTable * table,
		xmlNode * node, int cat)
{
    /*
       column name | xml
       -----------------
       from_id     | from
       to_id       | to
       left_id     | left
       right_id    | right
       _           | -
     */

    int i;
    double val;
    char *c, *cnxml, *cnxml_tmp;
    char buf[512];

    dbColumn *column;
    dbString sql, sval, col_name_xml;
    xmlNode *obs_val;

    db_init_string(&sql);
    db_init_string(&sval);
    db_init_string(&col_name_xml);

    db_set_string(&sql, "INSERT INTO ");
    db_append_string(&sql, fi->table);
    db_append_string(&sql, " (");

    for (i = 0; i < db_get_table_number_of_columns(table); i++) {
	column = db_get_table_column(table, i);
	if (i > 0) {
	    db_append_string(&sql, ",");
	}
	db_append_string(&sql, db_get_column_name(column));
    }

    db_append_string(&sql, ") VALUES (");
    sprintf(buf, "%d", cat);
    db_append_string(&sql, buf);

    for (i = 1; i < db_get_table_number_of_columns(table); i++) {
	column = db_get_table_column(table, i);
	db_set_string(&col_name_xml, db_get_column_name(column));
	cnxml = db_get_string(&col_name_xml);

	if (!G_strcasecmp(cnxml, "obs_type")) {
	    db_append_string(&sql, ",'");
	    db_append_string(&sql, (char *)node->name);
	    db_append_string(&sql, "'");
	    continue;
	}

	/* remove "_id" from original (xml) column name */
	if (!G_strcasecmp(cnxml, "from_id") ||
	    !G_strcasecmp(cnxml, "to_id") ||
	    !G_strcasecmp(cnxml, "left_id") ||
	    !G_strcasecmp(cnxml, "right_id")) {
	    cnxml_tmp = G_str_replace(cnxml, "_id", "");
	    db_set_string(&col_name_xml, cnxml_tmp);
	}

	/* replace '_' -> '-' */
	c = strstr(cnxml, "_");
	if (c) {
	    cnxml_tmp = G_str_replace(cnxml, "_", "-");
	    db_set_string(&col_name_xml, cnxml_tmp);
	}

	if (find_node(node, cnxml, &obs_val)) {
	    switch (db_get_column_sqltype(column)) {
	    case DB_SQL_TYPE_CHARACTER:
		{
		    if (node_get_value_string(obs_val, NULL, &sval)) {
			db_append_string(&sql, ",");
			sprintf(buf, "'%s'", db_get_string(&sval));
			db_append_string(&sql, buf);
		    }
		    else {
			db_append_string(&sql, ",NULL");
		    }
		    break;
		}
	    case DB_SQL_TYPE_DOUBLE_PRECISION:
		{
		    if (node_get_value_double(obs_val, &val)) {
			db_append_string(&sql, ",");
			sprintf(buf, "%f", val);
			db_append_string(&sql, buf);
		    }
		    else {
			db_append_string(&sql, ",NULL");
		    }
		    break;
		}
	    default:
		{
		    G_fatal_error(_("Unable to determine data type of the column <%s>"),
				  db_get_column_name(column));
		    break;
		}
	    }
	}
	else {
	    db_append_string(&sql, ",NULL");
	}
    }

    db_append_string(&sql, ")");

    G_debug(3, "SQL: %s", db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	G_fatal_error(_("Unable to insert new row: '%s'"), db_get_string(&sql));
    }

    return;
}
