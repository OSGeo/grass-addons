#include "global.h"

int parse_command_line(int argc, char *argv[])
{
    struct
    {
	struct Option *input;
	struct Option *output;
    } parms;

    struct
    {
	struct Flag *t;
    } flags;

    parms.input = G_define_standard_option(G_OPT_F_INPUT);
    parms.input->description =
	_("GNU GaMa XML output file to be converted to "
	  "binary vector file, if not given reads from standard input");

    parms.output = G_define_standard_option(G_OPT_V_OUTPUT);

    flags.t = G_define_flag();
    flags.t->key = 't';
    flags.t->description = _("Do not create attribute table");

    if (G_parser(argc, argv)) {
	exit(EXIT_FAILURE);
    }

    options.input = parms.input->answer;
    options.output = parms.output->answer;
    options.dotable = flags.t->answer ? 0 : 1;

    return 0;
}
