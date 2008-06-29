
/****************************************************************************
 *
 * MODULE:       g.xlist
 *
 * AUTHOR(S):    Huidae Cho
 * 		 Based on general/manage/cmd/list.c by Michael Shapiro.
 *
 * PURPOSE:      Lists available GRASS data base files of the
 *               user-specified data type to standard output
 *
 * COPYRIGHT:    (C) 1999-2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN
#include <stdlib.h>
#include <string.h>
#include <grass/spawn.h>
#include "gisdefs.h"
#include "global.h"

static int parse(const char *);
static int do_list(int, const char *, const char *, int, const char *, int);

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct
    {
	struct Option *type;
	struct Option *pattern;
	struct Option *separator;
	struct Option *mapset;
    } opt;
    struct
    {
	struct Flag *regex;
	struct Flag *type;
	struct Flag *mapset;
	struct Flag *pretty;
	struct Flag *full;
    } flag;
    int i, n, all, num_types, any, flags = 0;
    char **types, *pattern = NULL, separator[2];

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("general, map management");
    module->description =
	_("Lists available GRASS data base files "
	  "of the user-specified data type to standard output.");

    read_list(0);

    opt.type = G_define_option();
    opt.type->key = "type";
    opt.type->key_desc = "datatype";
    opt.type->type = TYPE_STRING;
    opt.type->required = YES;
    opt.type->multiple = YES;
    opt.type->answer = "rast";
    opt.type->description = "Data type";
    for (i = 0, n = 0; n < nlist; n++)
	i += strlen(list[n].alias) + 1;
    opt.type->options = G_malloc(i + 4);

    opt.type->options[0] = 0;
    for (n = 0; n < nlist; n++) {
	G_strcat(opt.type->options, list[n].alias);
	G_strcat(opt.type->options, ",");
    }
    G_strcat(opt.type->options, "all");
#define TYPES opt.type->answers

    opt.pattern = G_define_option();
    opt.pattern->key = "pattern";
    opt.pattern->type = TYPE_STRING;
    opt.pattern->required = NO;
    opt.pattern->multiple = NO;
    opt.pattern->answer = "*";
    opt.pattern->description = _("Map name search pattern (default: all)");
#define PATTERN opt.pattern->answer

    opt.separator = G_define_option();
    opt.separator->key = "separator";
    opt.separator->type = TYPE_STRING;
    opt.separator->required = NO;
    opt.separator->multiple = NO;
    opt.separator->answer = "newline";
    opt.separator->description =
	_("One-character output separator, newline, space, or tab");
#define SEPARATOR opt.separator->answer

    opt.mapset = G_define_option();
    opt.mapset->key = "mapset";
    opt.mapset->type = TYPE_STRING;
    opt.mapset->required = NO;
    opt.mapset->multiple = NO;
    opt.mapset->description =
	_("Mapset to list (default: current search path)");
#define MAPSET opt.mapset->answer

    flag.regex = G_define_flag();
    flag.regex->key = 'r';
    flag.regex->description =
	_("Use extended regular expressions instead of wildcards");
#define FREGEX flag.regex->answer

    flag.type = G_define_flag();
    flag.type->key = 't';
    flag.type->description = _("Print data types");
#define FTYPE flag.type->answer

    flag.mapset = G_define_flag();
    flag.mapset->key = 'm';
    flag.mapset->description = _("Print mapset names");
#define FMAPSET flag.mapset->answer

    flag.pretty = G_define_flag();
    flag.pretty->key = 'p';
    flag.pretty->description = _("Pretty printing in human readable format");
#define FPRETTY flag.pretty->answer

    flag.full = G_define_flag();
    flag.full->key = 'f';
    flag.full->description = _("Verbose listing (also list map titles)");
#define FFULL flag.full->answer

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    if (!FREGEX) {
	pattern = wc2regex(PATTERN);
	G_free(PATTERN);
	PATTERN = pattern;
    }

    G_set_ls_filter(PATTERN);
#if 0
    fprintf(stderr, "%s\n", G_get_ls_filter());
#endif

    if (strcmp(SEPARATOR, "newline") == 0)
	separator[0] = '\n';
    else if (strcmp(SEPARATOR, "space") == 0)
	separator[0] = ' ';
    else if (strcmp(SEPARATOR, "tab") == 0)
	separator[0] = '\t';
    else
	separator[0] = SEPARATOR[0];
    separator[1] = 0;

    if (MAPSET == NULL)
	MAPSET = "";

    if (G_strcasecmp(MAPSET, ".") == 0)
	MAPSET = G_mapset();

    for (i = 0; TYPES[i]; i++) {
	if (strcmp(TYPES[i], "all") == 0)
	    break;
    }
    if (TYPES[i]) {
	all = 1;
	num_types = nlist;
    }
    else {
	all = 0;
	num_types = i;
    }

    if (FTYPE)
	flags |= G_JOIN_ELEMENT_TYPE;
    if (FMAPSET)
	flags |= G_JOIN_ELEMENT_MAPSET;

    for (i = 0; i < num_types; i++) {
	n = all ? i : parse(TYPES[i]);

	if (FFULL) {
	    char lister[300];

	    sprintf(lister, "%s/etc/lister/%s", G_gisbase(),
		    list[n].element[0]);
	    G_debug(3, "lister CMD: %s", lister);
	    if (access(lister, 1) == 0)	/* execute permission? */
		G_spawn(lister, lister, MAPSET, NULL);
	    else
		any = do_list(n, PATTERN, MAPSET, FPRETTY, separator, flags);
	}
	else
	    any = do_list(n, PATTERN, MAPSET, FPRETTY, separator, flags);
    }
    if (!FPRETTY && any)
	fprintf(stdout, "\n");

    if (pattern)
	G_free(pattern);

    exit(EXIT_SUCCESS);
}

static int parse(const char *data_type)
{
    int n;

    for (n = 0; n < nlist; n++) {
	if (G_strcasecmp(list[n].alias, data_type) == 0)
	    break;
    }

    return n;
}

static int do_list(int n, const char *pattern, const char *mapset,
		   int pretty, const char *separator, int flags)
{
    static int any = 0;
    const char *buf;
    int len;

    if (pretty) {
	G_list_element(list[n].element[0], list[n].alias, mapset,
		       (int (*)())0);
	return 1;
    }

    buf =
	G_join_element(list[n].element[0], list[n].alias, mapset, separator,
		       flags, NULL);
    len = strlen(buf);
    if (any && len)
	fprintf(stdout, "%s", separator);
    if (len)
	fprintf(stdout, "%s", buf);
    G_free((char *)buf);

    any += len > 0;

    return any;
}
