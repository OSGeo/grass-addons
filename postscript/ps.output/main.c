/* File: main.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#define MAIN

#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <signal.h>
#include <errno.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "papers.h"
#include "palettes.h"
#include "draws.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)

FILE *inputfd;

int main(int argc, char *argv[])
{
    struct Option *input_file;
    struct Option *output_file;
    struct GModule *module;
    struct Flag *draft, *eps, *ghost, *style;

    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    module->keywords = _("postscript, map, printing");
    module->description = _("PostScript-3 Output.");

    input_file = G_define_option();
    input_file->key = "input";
    input_file->type = TYPE_STRING;
    input_file->description = _("File containing mapping instructions");
    input_file->gisprompt = "code_file,file,input";
    input_file->required = NO;

    output_file = G_define_option();
    output_file->key = "output";
    output_file->type = TYPE_STRING;
    output_file->gisprompt = "new_file,file,output";
    output_file->description = _("PostScript output file");
    output_file->required = YES;

    draft = G_define_flag();
    draft->key = 'd';
    draft->description =
	_("draft: Draw a 1x1 cm grid on paper to help the placement of the elements of the map");

    eps = G_define_flag();
    eps->key = 'e';
    eps->description =
	_("eps: Create output as EPS file for embedding into another ps.out map");

    ghost = G_define_flag();
    ghost->key = 'g';
    ghost->description =
	_("ghostscript: Use the extended PostScript of Ghostscript (for transparent colors)");

    style = G_define_flag();
    style->key = 's';
    style->description =
	_("special: Draw the small digit in the coordinate numbers to lower instead upper position");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    inputfd = stdin;
    signal(SIGINT, exit);
    signal(SIGTERM, exit);
    setbuf(stderr, NULL);

    if (!isatty(0))
	G_disable_interactive();

    if (output_file->answer) {
	if ((PS.fp = fopen(output_file->answer, "w")) == NULL)
	    G_fatal_error("%s - %s: %s", G_program_name(),
			  output_file->answer, strerror(errno));
    }
    else {
	G_message(_("\nERROR: Required parameter <%s> not set:\n    (%s).\n"),
		  output_file->key, output_file->description);
	exit(EXIT_FAILURE);
    }

    /* get current mapset */
    PS.mapset = G_mapset();

    /* set current window */
    G_get_set_window(&PS.map);
    if (G_set_window(&PS.map) == -1)
	G_fatal_error(_("Current region cannot be set."));

    set_paper("A4");
    unset_color(&(PS.page.fcolor));	/* no paper color */
    Palette = NULL;
    /* Set the level of Postscript */
    PS.level = (eps->answer ? 0 : 3);
    PS.flag |= (ghost->answer ? 1 : 0);
    PS.flag |= (style->answer ? 2 : 0);
    /* initialize default ps_info */
    PS.draft = draft->answer ? 1 : 0;
    PS.scale = 0;
    PS.map_top = -1.;
    PS.map_x = PS.map_y = -1.;
    PS.map_w = PS.map_h = -1.;
    unset_color(&(PS.fcolor));	/* no background color in maparea */
    PS.do_border = 0;		/* no border */
    PS.rst.files = 0;		/* no rast files */
    PS.need_mask = 0;		/* select storage in PS_raster_plot */
    PS.do_rlegend = 0;		/* no rlegend */
    PS.vct_files = 0;		/* no include files */
    PS.vct = NULL;		/* no vector files */
    PS.do_vlegend = 0;		/* no vlegend */
    PS.grid.sep = 0;		/* no grid */
    PS.geogrid.sep = 0;		/* no geogrid */
    PS.sbar.segments = 0;	/* no scalebar */
    PS.n_notes = 0;		/* no notes */
    PS.n_draws = 0;		/* no plots */
    /* default font */
    strcpy(PS.font.name, "Helvetica");
    PS.font.size = 10.;
    PS.font.extend = 1.;
    set_color_rgb(&(PS.font.color), 0, 0, 0);

    /* process options */
    char buf[1024];
    double number;

    while (input(1, buf)) {
	char *key;
	char *data;

	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	/* General information */
	if (KEY("paper")) {
	    read_paper(data);
	    continue;
	}
	if (KEY("palette")) {
	    read_palette();
	    continue;
	}
	if (KEY("maparea")) {
	    read_maparea();
	    continue;
	}
	if (KEY("scale")) {
	    if (sscanf(data, "1:%d", &(PS.scale)) != 1) {
		error(key, data, "illegal scale request");
	    }
	    continue;
	}

	/* Raster map related information */
	if (KEY("cell") || KEY("rast") || KEY("raster") || KEY("rgb")) {
	    if (PS.rst.files != 0) {
		error(key, data, "only one raster command");
		continue;
	    }
	    read_raster(data);
	    continue;
	}
	if (KEY("rlegend")) {
	    if (PS.do_rlegend != 0) {
		error(key, data, "only one rlegend command");
	    }
	    read_rlegend(data);
	    continue;
	}

	/* Vector map related information */
	if (KEY("vlines") || KEY("vline")) {
	    G_strip(data);
	    if (*data == 0) {
		error(key, data, "vlines need vector map");
	    }
	    read_vlines(data);
	    continue;
	}
	if (KEY("vareas") || KEY("varea")) {
	    G_strip(data);
	    if (*data == 0) {
		error(key, data, "vareas need vector map");
	    }
	    read_vareas(data);
	    continue;
	}
	if (KEY("vpoints") || KEY("vpoint")) {
	    G_strip(data);
	    if (*data == 0) {
		error(key, data, "vpoints need vector map");
	    }
	    read_vpoints(data);
	    continue;
	}
	if (KEY("vlabels") || KEY("vlabel")) {
	    G_strip(data);
	    if (*data == 0) {
		error(key, data, "vlabels need vector map");
	    }
	    read_vlabels(data);
	    continue;
	}
	if (KEY("vlegend")) {
	    if (PS.do_vlegend != 0) {
		error(key, data, "only one vlegend command");
	    }
	    read_vlegend(data);
	    continue;
	}

	/* Grid and scalebar related */
	if (KEY("grid")) {
	    read_grid(&(PS.grid), 1);
	    continue;
	}
	if (KEY("geogrid")) {
	    if (G_projection() == PROJECTION_XY) {
		error(key, data,
		      "geogrid is not available for XY projection");
	    }
	    else if (G_projection() == PROJECTION_LL) {
		error(key, data, "grid just uses LL projection");
	    }
	    read_grid(&(PS.geogrid), 0);
	    continue;
	}
	if (KEY("scalebar")) {
	    if (G_projection() == PROJECTION_LL) {
		error(key, data,
		      "scalebar is not appropriate for this projection");
	    }
	    if (sscanf(data, "%c", &(PS.sbar.type)) != 1)
		PS.sbar.type = 'I';	/* default new style scalebar */
	    read_scalebar();
	    continue;
	}

	/* Addons related data */
	if (KEY("note")) {
	    if (PS.n_notes >= MAX_NOTES) {
		G_warning("Only %d notes by map", MAX_NOTES);
		continue;
	    }
	    read_note(data);
	    continue;
	}
	if (KEY("draw")) {
	    if (PS.n_draws >= MAX_DRAWS) {
		G_warning("Only %d draw commands by map", MAX_DRAWS);
		continue;
	    }
	    read_draw(data);
	    continue;
	}
	/* oops, no valid command */
	if (*key)
	    error(key, "", "illegal request");
    }

    /* last minute adjust */
    if (PS.grid.format >= 2) {	/* IHO */
	PS.brd.width = 2. * MM_TO_POINT;	/* 12.7 */
    }

    /* Well, go on the map */
    PS3_map();
    G_message(_("PostScript file '%s' finished!"), output_file->answer);
    exit(EXIT_SUCCESS);
}
