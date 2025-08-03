#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <grass/glocale.h>
#include "global.h"

int parse_units();
int parse_option();
int match();

int parse_command_line(int argc, char *argv[])
{
    struct {
        struct Option *vect;
        struct Option *field;
        struct Option *output;
        struct Option *separator;
    } parms;

    struct {
        struct Flag *shell_style;
        struct Flag *extended;
        struct Flag *table;
    } flags;

    parms.vect = G_define_standard_option(G_OPT_V_MAP);

    parms.field = G_define_standard_option(G_OPT_V_FIELD);
    parms.field->label = _("Layer number or name (write to)");

    parms.output = G_define_standard_option(G_OPT_F_OUTPUT);
    parms.output->required = NO;
    parms.output->description =
        _("Name for output file (if omitted or \"-\" output to stdout)");
    parms.output->guisection = _("Output settings");

    parms.separator = G_define_standard_option(G_OPT_F_SEP);
    parms.separator->guisection = _("Formatting");

    flags.shell_style = G_define_flag();
    flags.shell_style->key = 'g';
    flags.shell_style->description = _("Print the stats in shell script style");
    flags.shell_style->guisection = _("Formatting");

    flags.extended = G_define_flag();
    flags.extended->key = 'e';
    flags.extended->description = _("Calculate extended statistics");
    flags.extended->guisection = _("Extended");

    flags.table = G_define_flag();
    flags.table->key = 't';
    flags.table->description =
        _("Table output format instead of standard output format");
    flags.table->guisection = _("Formatting");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* check for required options */
    if (!parms.vect->answer)
        G_fatal_error(_("Required parameter <%s> not set:\n\t(%s)"),
                      parms.vect->key, parms.vect->description);

    options.name = parms.vect->answer;
    options.field = atoi(parms.field->answer);

    options.out = parms.output->answer;
    options.separator = ";"; /* G_option_to_separator(parms.separator); */
    G_debug(1, _("The separator is: <%s>"), options.separator);

    return 0;
}
