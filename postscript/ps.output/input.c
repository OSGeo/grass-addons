/* File: input.c
 *
 *  COPYRIGHT: (c) GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <grass/gis.h>
#include "local_proto.h"

extern FILE *inputfd;

/* Get line to buffer */
int input(int level, char *buf)
{
    int i;
    char command[20], empty[3];

    if (level && isatty(fileno(inputfd)))
	fprintf(stdout, "enter 'end' when done, 'exit' to quit\n");

    do {
	if (level && isatty(fileno(inputfd))) {
	    fprintf(stdout, "%s ", level == 1 ? ">" : ">>");
	}
	if (!G_getl2(buf, 1024, inputfd)) {
	    if (inputfd != stdin) {
		fclose(inputfd);
		inputfd = stdin;
	    }
	    return 0;
	}
	if (sscanf(buf, "%5s %1s", command, empty) == 1) {
	    if (strcmp(command, "end") == 0)
		return 0;
	    if (strcmp(command, "exit") == 0)
		exit(0);
	}
    }
    while (*buf == '#');

    return 1;
}

/* Point to key and data */
int key_data(char *buf, char **k, char **d)
{
    char *key, *data;

    key = buf;
    while (*key && *key <= ' ')
	key++;

    if (*key == 0) {
	*k = *d = key;
	return 0;
    }

    data = key;
    while (*data && *data > ' ')
	data++;

    if (*data)
	*data++ = 0;

    *k = key;
    *d = data;

    return 1;
}

/* Print a error message, and stop */
int error(char *a, char *b, char *c)
{
    char msg[2000];

    sprintf(msg, "%s%s%s : %s", a, *b ? " " : "", b, c);

    if (isatty(0))
	fprintf(stderr, "%s\n", msg);
    else
	G_fatal_error(msg);

    exit(0);

    return 0;
}
