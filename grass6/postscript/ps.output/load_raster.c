/* File: load_raster.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */


#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "raster.h"
#include "ps_info.h"
#include "local_proto.h"

/* load three files as RGB */
int load_rgb(char *red, char *green, char *blue)
{
    /* close rasters open */
    raster_close();

    G_message(_("Reading RGB files ..."));

    load_cell(0, red);
    load_cell(1, green);
    load_cell(2, blue);

    PS.rst.title = "RGB Group";

    return 3;
}

/* load a group as RGB */
int load_group(char *name)
{
    int i;
    struct Ref ref;
    char fullname[100];

    /* close open rasters */
    raster_close();

    I_init_group_ref(&ref);

    /* get group info */
    if (I_get_group_ref(PS.rst.title, &ref) == 0) {
	G_fatal_error(_("Can't get group information"));
    }

    G_message(_("Reading map group <%s> ..."), name);

    /* get filenames for R, G, and B */
    I_init_ref_color_nums(&ref);
    PS.rst.name[0] = G_store(ref.file[ref.red.n].name);
    PS.rst.mapset[0] = G_store(ref.file[ref.red.n].mapset);
    PS.rst.name[1] = G_store(ref.file[ref.grn.n].name);
    PS.rst.mapset[1] = G_store(ref.file[ref.grn.n].mapset);
    PS.rst.name[2] = G_store(ref.file[ref.blu.n].name);
    PS.rst.mapset[2] = G_store(ref.file[ref.blu.n].mapset);

    /* check load colors */
    for (i = 0; i < 3; i++) {
	if (G_read_colors
	    (PS.rst.name[i], PS.rst.mapset[i], &(PS.rst.colors[i])) == -1) {
	    sprintf(fullname, "%s in %s", PS.rst.name[i], PS.rst.mapset[i]);
	    error(fullname, "", "can't load color table");
	    return 0;
	}
    }

    /* check open raster maps */
    for (i = 0; i < 3; i++) {
	if ((PS.rst.fd[i] =
	     G_open_cell_old(PS.rst.name[i], PS.rst.mapset[i])) < 0) {
	    sprintf(fullname, "%s in %s", PS.rst.name[i], PS.rst.mapset[i]);
	    error(fullname, "", "can't open raster map");
	    G_free_colors(&(PS.rst.colors[i]));
	    return 0;
	}
    }

    I_free_group_ref(&ref);
    return 3;
}

/* load a cell file in a slot */
int load_cell(int slot, char *name)
{
    char *mapset, *ptr;
    char fullname[100];

    /* close raster cell, if any */
    if (PS.rst.fd[slot] >= 0) {
	G_close_cell(PS.rst.fd[slot]);
	G_free(PS.rst.name[slot]);
	G_free(PS.rst.mapset[slot]);
	G_free_colors(&(PS.rst.colors[slot]));
	PS.rst.fd[slot] = -1;
    }

    /* get mapset */
    ptr = strchr(name, '@');
    if (ptr) {
	*ptr = '\0';
	mapset = ptr + 1;
    }
    else {
	mapset = G_find_file2("cell", name, "");
	if (!mapset) {
	    error(name, "", "not found");
	    return 0;
	}
    }

    /* store data of cell */
    PS.rst.name[slot] = G_store(name);
    PS.rst.mapset[slot] = G_store(mapset);
    sprintf(fullname, "%s in %s", name, mapset);

    G_message(_("  Reading raster map <%s> ..."), fullname);

    /* load colors */
    if (G_read_colors(name, mapset, &PS.rst.colors[slot]) == -1) {
	error(fullname, "", "can't load color table");
	return 0;
    }
    G_get_color_range(&(PS.rst.min), &(PS.rst.max), &(PS.rst.colors[slot]));

    /* open raster map */
    if ((PS.rst.fd[slot] = G_open_cell_old(name, mapset)) < 0) {
	error(fullname, "", "can't open raster map");
	G_free_colors(&PS.rst.colors[slot]);
	return 0;
    }

    return 1;
}
