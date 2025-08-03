#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "local_proto.h"

void parse_args(int argc, char **argv, char **input, char **output, int *format,
                int *dp, char **field, char ***columns, int *region)
{
    struct Option *input_opt, *output_opt, *dp_opt, *field_opt,
        *column_opt /* , *format_opt */;
    struct Flag *region_flag;

    input_opt = G_define_standard_option(G_OPT_V_INPUT);

    field_opt = G_define_standard_option(G_OPT_V_FIELD);

    output_opt = G_define_standard_option(G_OPT_F_OUTPUT);
    output_opt->label = _("Name for output PLY file");
    output_opt->description = _("'-' for standard output");
    output_opt->required = NO;
    output_opt->answer = "-";

    column_opt = G_define_standard_option(G_OPT_DB_COLUMNS);
    column_opt->description = _("Name of attribute column(s) to be exported");

    /*
        format_opt = G_define_option();
        format_opt->key = "format";
        format_opt->type = TYPE_STRING;
        format_opt->required = YES;
        format_opt->multiple = NO;
        format_opt->options = "ascii,binary";
        format_opt->answer = "ascii";
        format_opt->description = _("Output PLY file format");
    */

    dp_opt = G_define_option();
    dp_opt->key = "dp";
    dp_opt->type = TYPE_INTEGER;
    dp_opt->required = NO;
    dp_opt->options = "0-32";
    dp_opt->answer = "6"; /* This value is taken from the lib settings in
                             G_format_easting() */
    dp_opt->description =
        _("Number of significant digits (floating point only)");

    region_flag = G_define_flag();
    region_flag->key = 'r';
    region_flag->description =
        _("Only export points falling within current 3D region (points mode)");
    region_flag->guisection = _("Points");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    *input = G_store(input_opt->answer);
    *output = G_store(output_opt->answer);

    /*
        if (format_opt->answer[0] == 'b')
            *format = PLY_BINARY;
        else
            *format = PLY_ASCII;
    */

    if (sscanf(dp_opt->answer, "%d", dp) != 1)
        G_fatal_error(_("Failed to interpret 'dp' parameter as an integer"));

    *field = G_store(field_opt->answer);

    *columns = NULL;
    if (column_opt->answer) {
        int i, nopt;
        nopt = 0;
        while (column_opt->answers[nopt++])
            ;

        *columns = (char **)G_malloc(nopt * sizeof(char *));
        for (i = 0; i < nopt - 1; i++)
            (*columns)[i] = G_store(column_opt->answers[i]);
        (*columns)[nopt - 1] = NULL;
    }
    *region = region_flag->answer ? 1 : 0;
}
