#include "global.h"

int write_head(struct Map_info *Map, xmlDoc * doc)
{
    xmlNode *root;
    struct list_nodes *desc;
    dbString val, value;

    int scale;

    root = xmlDocGetRootElement(doc);
    list_init((void **)&desc);
    db_init_string(&val);
    db_init_string(&value);

    if (!root) {
	G_fatal_error(_("Unable to get the root element"));
    }
    else {
	find_nodes(root, "description", &desc);
	if (desc) {
	    if (node_get_value_string(desc->node, NULL, &val)) {
		if (find_substring(&val, "scale", &value)) {
		    scale = atoi(db_get_string(&value));
		    if (scale > 0) {
			Vect_set_scale(Map, scale);
		    }
		}
		else {
		    Vect_set_scale(Map, 1000);	/* default scale 1000 */
		}

		if (find_substring(&val, "date", &value)) {
		    Vect_set_map_date(Map, db_get_string(&value));
		}
		else {
		    Vect_set_map_date(Map, G_date());	/* default map date = date */
		}

		if (find_substring(&val, "name", &value)) {
		    Vect_set_map_name(Map, db_get_string(&value));
		}
		else {
		    Vect_set_map_name(Map, "GNU GaMa network");
		}

		if (find_substring(&val, "organization", &value)) {
		    Vect_set_organization(Map, db_get_string(&value));
		}
		else {
		    char *organization;

		    if ((organization =
			 (char *)G_getenv("GRASS_ORGANIZATION"))) {
			Vect_set_organization(Map, organization);
		    }
		    else {
			Vect_set_organization(Map, "GRASS Development Team");
		    }
		}

		if (find_substring(&val, "person", &value)) {
		    Vect_set_person(Map, db_get_string(&value));
		}
		else {
		    Vect_set_person(Map, G_whoami());
		}

		if (find_substring(&val, "other info", &value)) {
		    const short int odim = 65;
		    char other_info[odim];

		    G_warning(_("Other info is too long, "
				"only first %d chars will be stored"), odim);
		    strncpy(other_info, db_get_string(&value), odim);
		    Vect_set_comment(Map, other_info);
		}
		else {
		    Vect_set_comment(Map, "created by v.in.gama");
		}

	    }
	    Vect_set_date(Map, G_date());
	}
    }

    list_nodes_free(&desc);

    return 0;
}

int find_substring(dbString * str, const char *pattern, dbString * substring)
{
    char *c, *s, z[2];
    dbString buf;

    db_init_string(&buf);

    c = strstr(db_get_string(str), pattern);

    if (c) {
	s = c + strlen(pattern);
	if (*(s++) == ':') {
	    while (*s != '\n' && *s != '\0') {
		z[0] = *(s++);
		z[1] = '\0';
		db_append_string(&buf, z);
	    }
	    db_copy_string(substring, &buf);
	    return 1;
	}
	/* maybe a bit confusing
	   else 
	   {
	   G_warning (_("Cannot recognize substring '%s'."),
	   db_get_string (str));
	   }
	 */
    }

    return 0;
}
