
/**
   \file join.c

   \brief Return a string that contains elements

   \author Huidae Cho

   (C) 2008 by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.
*/

#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <sys/types.h>
#include <dirent.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "gisdefs.h"

static int join_element(const char *, const char *, const char *,
			const char *, int, const char **);

/**
   \brief General purpose join function.

   Will collect file names from all mapsets
   in the mapset list for a specified database element
   and join them into a string.

   Note: Use G_(set|get)_ls_filter functions to filter out unwanted file names.

   \param element    Database element (eg, "cell", "cellhd", etc)
   \param alias      Alias for element (if NULL, element is used)
   \param mapset     Mapset to be listed "" to list all mapsets in mapset search list
   "." will list current mapset
   \param separator  Map name separator
   \param flags      G_JOIN_ELEMENT_TYPE   Include alias
                     G_JOIN_ELEMENT_MAPSET Include mapset name
   \param count      Return the number of elements (if NULL, ignored)

   \return String pointer
*/
const char *G_join_element(const char *element,
			   const char *alias,
			   const char *mapset,
			   const char *separator, int flags, int *count)
{
    int c, n;
    const char *buf;

    c = 0;
    if (alias == 0 || *alias == 0)
	alias = element;

    /*
     * if no specific mapset is requested, list the mapsets
     * from the mapset search list
     * otherwise just list the specified mapset
     */
    buf = G_strdup("");
    if (mapset == 0 || *mapset == 0)
	for (n = 0; (mapset = G__mapset_name(n)); n++)
	    c += join_element(element, alias, mapset, separator, flags, &buf);
    else
	c = join_element(element, alias, mapset, separator, flags, &buf);

    if (count)
	*count = c;
    return buf;
}

static int join_element(const char *element,
			const char *alias,
			const char *mapset,
			const char *separator, int flags, const char **buf)
{
    char path[GPATH_MAX], *p;
    int i, count = 0;
    int buf_len, alias_len, list_len, sep_len = strlen(separator), mapset_len;
    char **list;

    /*
     * convert . to current mapset
     */
    if (strcmp(mapset, ".") == 0)
	mapset = G_mapset();

    mapset_len = strlen(mapset);

    /*
     * get the full name of the GIS directory within the mapset
     * and list its contents (if it exists)
     */
    G__file_name(path, element, "", mapset);
    if (access(path, 0) != 0)
	return count;

    list = G__ls(path, &count);

    alias_len = strlen(alias);
    for (i = 0; i < count; i++) {
	buf_len = strlen(*buf);
	list_len = strlen(list[i]);
	*buf = (char *)G_realloc((char *)*buf,
				 (buf_len ? buf_len + sep_len : 0) +
				 (flags & G_JOIN_ELEMENT_TYPE ? alias_len +
				  1 : 0) + list_len +
				 (flags & G_JOIN_ELEMENT_MAPSET ? mapset_len +
				  1 : 0) + 1);
	p = (char *)*buf + buf_len;

	/* looks dirty but fast! */
	if (buf_len) {
	    if (flags & G_JOIN_ELEMENT_TYPE) {
		if (flags & G_JOIN_ELEMENT_MAPSET)
		    sprintf(p, "%s%s/%s@%s", separator, alias, list[i],
			    mapset);
		else
		    sprintf(p, "%s%s/%s", separator, alias, list[i]);
	    }
	    else {
		if (flags & G_JOIN_ELEMENT_MAPSET)
		    sprintf(p, "%s%s@%s", separator, list[i], mapset);
		else
		    sprintf(p, "%s%s", separator, list[i]);
	    }
	}
	else {
	    if (flags & G_JOIN_ELEMENT_TYPE) {
		if (flags & G_JOIN_ELEMENT_MAPSET)
		    sprintf(p, "%s/%s@%s", alias, list[i], mapset);
		else
		    sprintf(p, "%s/%s", alias, list[i]);
	    }
	    else {
		if (flags & G_JOIN_ELEMENT_MAPSET)
		    sprintf(p, "%s@%s", list[i], mapset);
		else
		    sprintf(p, "%s", list[i]);
	    }
	}
    }

    for (i = 0; i < count; i++)
	G_free((char *)list[i]);
    if (list)
	G_free(list);

    return count;
}
