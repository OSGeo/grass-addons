#include "local_proto.h"

int parse_rule_file(STRING file)
{
    FILE *fd;
    char buf[1000];
    char tmp[30];
    STRING mapset;
    char map[30];
    fpos_t init;
    int rule_num = 0;
    int n = 0, i;

    fd = fopen(file, "r");
    if (!fd)
        G_fatal_error(_("Cannot open rules file '%s'"), file);

    fgetpos(fd, &init);

    while (fgets(buf, sizeof buf, fd)) {
        G_strip(buf);
        if (*buf != '$')
            continue;
        nrules++;
    }

    s_rules = (RULES *)G_malloc((nrules) * sizeof(RULES));
    rules = (char **)G_malloc((nrules) * sizeof(char *));
    for (i = 0; i < nrules; ++i)
        rules[i] = (char *)G_malloc(21 * sizeof(char));

    fsetpos(fd, &init); /* reset position */

    for (n = nmaps; n > 0; --n)
        if (!strcmp(s_maps[n - 1].name, output))
            break; /*max index of output map */

    if (n == 0)
        G_fatal_error(_("No definition for output map: <%s> in map file"),
                      output);

    while (fgets(buf, sizeof buf, fd)) {
        G_strip(buf);
        if (*buf != '$')
            continue;

        parse_rules(rule_num++, n, buf);

        /* next rule */
    }

    for (i = 0; i < nrules; ++i)
        G_free(rules[i]);
    G_free(rules);
    fclose(fd);
    return 0;

} /* END parse_rule_file */

int parse_rules(int rule_num, int n, char buf[])
{

    int i, j, l, o;
    int done = 1;
    int stack_top;
    char tmp[30];
    char opr[] = {'=', '&', '|', '~', '(', ')', '{', '}'};

    i = j = stack_top = 0; /* variables of the while loop */
    char_strip(buf, '$');

    { /* check the name of fuzzy value (must be defined in rules) */
        int s, p;

        sscanf(buf, "%[^{] %[^\n]", tmp, buf);
        G_strip(buf);
        G_strip(tmp);

        for (p = 0; p <= rule_num; ++p)
            strcpy(rules[p], "");

        done = 1;
        for (s = 0; s <= s_maps[n - 1].nsets; ++s) { /* output map */

            if (!strcmp(s_maps[n - 1].sets[s].setname, tmp)) {

                for (p = 0; p <= rule_num; ++p) /* check if values are unique */
                    if (!strcmp(tmp, rules[p]))
                        G_fatal_error(_("Variable value <%s> exist, Variable "
                                        "values must be unique"),
                                      tmp);

                strcpy(rules[rule_num], tmp);
                done = 0;
                break;
            }
        }
        if (done)
            G_fatal_error(_("Output map do not have variable value <%s>"), tmp);
        strcpy(s_rules[rule_num].outname, tmp);
        s_rules[rule_num].output_set_index = s;

    } /* check the name of fuzzy value */

    /* ******************************************************************* */

    { /* parse rule expression and create parse stack */

        do {
            for (o = 0; o < (sizeof opr); ++o) {
                if (buf[i] == opr[o]) {
                    char_copy(buf, tmp, j, i);
                    if (i > 0) {
                        char_strip(tmp, buf[j]);
                        s_rules[rule_num].parse_queue[stack_top][0] = buf[j];
                        s_rules[rule_num].parse_queue[stack_top++][1] = '\0';
                        G_strip(tmp);
                    }
                    if (strlen(tmp)) /* is not blank */
                        strcpy(s_rules[rule_num].parse_queue[stack_top++], tmp);

                    j = i;
                    break;
                }
            }
            if (i > 999)
                G_fatal_error(
                    _("rule string is too long or lack of closing element"));

        } while (buf[i++] != '}'); /* rule has been read */

        strcpy(s_rules[rule_num].parse_queue[stack_top++],
               "}"); /* add closing element only if OK */

    } /* end parse rule expression and create parse stack */

    /* ******************************************************************* */

    /*    {                          adding weight: not implemented yet

       char local[900];
       char weight[10];

       sscanf(buf, "%[^}] %[^;]", local, weight);
       char_strip(weight, '}');
       G_strip(weight);
       if (strlen(weight) == 0)
       strcpy(weight, "1");
       s_rules[rule_num].weight = atof(weight);
       if (s_rules[rule_num].weight <= 0.)
       G_fatal_error(_("Weight must be grater than 0 or non-number character"));

       } */

    { /* check if rule syntax is proper and map names and vars values exist */
        int k;
        int work_queue_pos = 0;
        int lbrc = 0, rbrc = 0; /* left and right braces */

        done = 1;
        for (i = 0; i < stack_top; ++i) { /* most external loop */
            if (*s_rules[rule_num].parse_queue[i] == '{') {

                s_rules[rule_num].work_queue[work_queue_pos] = t_START;

                if (i > 0)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END { */

            if (*s_rules[rule_num].parse_queue[i] == '=' ||
                *s_rules[rule_num].parse_queue[i] == '~') { /* =, ~ */

                for (j = 0; j < nmaps; ++j) {
                    if (!strcmp(s_rules[rule_num].parse_queue[i - 1],
                                s_maps[j].name)) {
                        for (k = 0; k < s_maps[j].nsets; ++k) {
                            if (!strcmp(s_rules[rule_num].parse_queue[i + 1],
                                        s_maps[j].sets[k].setname)) {

                                s_rules[rule_num].work_queue[work_queue_pos] =
                                    t_VAL;
                                s_rules[rule_num]
                                    .value_queue[work_queue_pos]
                                    .value = &s_maps[j].cell;
                                s_rules[rule_num]
                                    .value_queue[work_queue_pos]
                                    .set = &s_maps[j].sets[k];
                                s_rules[rule_num]
                                    .value_queue[work_queue_pos]
                                    .oper = *s_rules[rule_num].parse_queue[i];
                                done = 0;
                                break;
                            }
                        }
                    }
                } /* END for j */

                if (done)
                    G_fatal_error(_("There is no map <%s> or variable <%s>"),
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i + 1]);
                /* end for j */

                if (s_rules[rule_num].work_queue[work_queue_pos - 1] != t_AND &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_OR &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] !=
                        t_START &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_LBRC)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END =, ~ */

            if (*s_rules[rule_num].parse_queue[i] == '&' ||
                *s_rules[rule_num].parse_queue[i] == '|') { /* operators &, | */

                s_rules[rule_num].work_queue[work_queue_pos] =
                    (*s_rules[rule_num].parse_queue[i] == '|') ? t_OR : t_AND;

                if (s_rules[rule_num].work_queue[work_queue_pos - 1] != t_VAL &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_RBRC)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END &, | */

            if (*s_rules[rule_num].parse_queue[i] == '(') {

                s_rules[rule_num].work_queue[work_queue_pos] = t_LBRC;
                lbrc++;

                if (s_rules[rule_num].work_queue[work_queue_pos - 1] != t_AND &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_OR &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] !=
                        t_START &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_LBRC)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END ( */

            if (*s_rules[rule_num].parse_queue[i] == ')') {

                s_rules[rule_num].work_queue[work_queue_pos] = t_RBRC;
                rbrc++;

                if (s_rules[rule_num].work_queue[work_queue_pos - 1] != t_VAL &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_RBRC)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END ) */

            if (*s_rules[rule_num].parse_queue[i] == '}') {

                s_rules[rule_num].work_queue[work_queue_pos] = t_STOP;

                if (s_rules[rule_num].work_queue[work_queue_pos - 1] != t_VAL &&
                    s_rules[rule_num].work_queue[work_queue_pos - 1] != t_RBRC)
                    G_fatal_error(_("line %d Syntax error near <%s %s>"),
                                  rule_num + 1,
                                  s_rules[rule_num].parse_queue[i - 1],
                                  s_rules[rule_num].parse_queue[i]);

                work_queue_pos++;
                continue;
            } /* END } */

        } /* most external loop */

        if (lbrc != rbrc)
            G_fatal_error(_("line %d Left and right of braces do not match"),
                          rule_num + 1);

    } /* END check if rule syntax is proper and map names and vars values exist
       */

    return 0;
} /* END parse_rules */
