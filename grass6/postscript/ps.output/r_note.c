/* File: r_note.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */



#include <stdlib.h>
#include <string.h>
#include "notes.h"
#include "ps_info.h"
#include "local_proto.h"

#define KEY(x) (strcmp(key,x)==0)


int read_note(char *name)
{
    char buf[1024];
    char *key, *data;

    G_debug(1, "Reading note settings ..");

    /* default values */
    PS.note[PS.n_notes].text[0] = 0;
    PS.note[PS.n_notes].width = 0.;
    PS.note[PS.n_notes].angle = 0.;
    default_font(&(PS.note[PS.n_notes].font));
    default_frame(&(PS.note[PS.n_notes].box), LEFT, UPPER);

    /* inline argument */
    if (*name != 0) {
	strncpy(PS.note[PS.n_notes].text, name, 1024);
	PS.note[PS.n_notes].text[1023] = 0;
    }

    /* process options */
    while (input(2, buf)) {
	if (!key_data(buf, &key, &data)) {
	    continue;
	}
	if (KEY("frame")) {
	    read_frame(&(PS.note[PS.n_notes].box));
	    continue;
	}
	if (KEY("font")) {
	    read_font(data, &(PS.note[PS.n_notes].font));
	    continue;
	}
	if (KEY("text")) {
	    if (sscanf(data, "%s", PS.note[PS.n_notes].text) != 1) {
		PS.note[PS.n_notes].text[0] = 0;
		error(key, data, "illegal note sub-request");
	    }
	    else {
		strncpy(PS.note[PS.n_notes].text, data, 1024);
		PS.note[PS.n_notes].text[1023] = 0;
	    }
	    continue;
	}
	if (KEY("width")) {
	    if (scan_dimen(data, &(PS.note[PS.n_notes].width)) != 1) {
		PS.note[PS.n_notes].width = 0.;
		error(key, data, "illegal width sub-request");
	    }
	    continue;
	}
	if (KEY("angle")) {
	    if (sscanf(data, "%lf", &(PS.note[PS.n_notes].angle)) != 1) {
		PS.note[PS.n_notes].angle = 0.;
		error(key, data, "illegal angle sub-request");
	    }
	    continue;
	}
	error(key, data, "illegal note sub-request");
    }

    ++PS.n_notes;

    return 0;
}
