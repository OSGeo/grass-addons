#include <grass/gis.h>

#include "gt/gstats_global.h"

void gstats_error ( char *message ) {
	if (GSTATS_FATAL) {
		G_fatal_error ("GSTATS: %s", message);
	} else {
		G_warning ("GSTATS: %s", message);
	}
}

void gstats_error_warning ( void ) {
	GSTATS_FATAL = 0;
}

void gstats_error_fatal ( void ) {
	GSTATS_FATAL = 1;
}

