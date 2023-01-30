#include "local_proto.h"

float implicate(void)
{

    int i, j;

    // float *agregate = NULL;
    int set_index;
    float consequent;
    float max_antecedent = 0;
    float max_agregate = 0;
    float result;

    memset(agregate, 0, resolution * sizeof(float));

    for (j = 0; j < nrules; ++j) {
        antecedents[j] = parse_expression(j);
        max_antecedent =
            (max_antecedent > antecedents[j]) ? max_antecedent : antecedents[j];
    }

    if (max_antecedent == 0. && !coor_proc)
        return -9999; /* for all rules value is 0 */

    for (j = 0; j < nrules; ++j) {

        if (defuzzification > d_BISECTOR && antecedents[j] < max_antecedent &&
            !coor_proc)
            continue;

        set_index = s_rules[j].output_set_index;

        for (i = 0; i < resolution; ++i) {

            consequent =
                fuzzy(universe[i], &s_maps[output_index].sets[set_index]);

            consequent = (!implication) ? MIN(antecedents[j], consequent)
                                        : antecedents[j] * consequent;
            agregate[i] = MAX(agregate[i], consequent);

            max_agregate =
                (max_agregate > agregate[i]) ? max_agregate : agregate[i];

            if (coor_proc)
                visual_output[i][j + 1] = consequent;
        }
    }
    if (coor_proc)
        for (i = 0; i < resolution; ++i)
            visual_output[i][j + 1] = agregate[i];

    result = defuzzify(defuzzification, max_agregate);
    return result;
}

float parse_expression(int n)
{

    /*  tokens and actions must heve the same order */
    actions parse_tab[t_size][t_size] = {
        /* stk -----------INPUT------------------ */
        /*              {   &  | ~   =  (  )  }   */
        /*      --  -- -- -- -- -- -- -- */
        /* { */ {E, S, S, E, E, S, E, A},
        /* & */ {E, R, R, E, E, S, R, R},
        /* | */ {E, R, R, E, E, S, R, R},
        /* ~ */ {E, E, E, E, E, E, E, E},
        /* = */ {E, E, E, E, E, E, E, E},
        /* ( */ {E, S, S, E, E, S, S, E},
        /* ) */ {E, R, R, E, E, E, R, R},
        /* } */ {E, E, E, E, E, E, E, E}};

    tokens operator_stack[STACKMAX];
    float values_stack[STACKMAX];

    int i = 0, k = 0;
    int opr_top = 0;
    int val_top = 0;
    int set_index;
    float f_value;

    do {
        if (s_rules[n].work_queue[i] == t_START) { /* first token */
            if (i > 0)
                G_fatal_error("Operator stack error, contact author");
            operator_stack[opr_top] = t_START;
            continue;
        }

        if (s_rules[n].work_queue[i] == t_VAL) {
            f_value = fuzzy(*s_rules[n].value_queue[i].value,
                            s_rules[n].value_queue[i].set);
            values_stack[++val_top] = (s_rules[n].value_queue[i].oper == '~')
                                          ? f_not(f_value, family)
                                          : f_value;
            continue;
        }

        if (s_rules[n].work_queue[i] < t_size) {
            switch (
                parse_tab[operator_stack[opr_top]][s_rules[n].work_queue[i]]) {

            case E: /* error */
                G_fatal_error("Stack error, contact author");
                break;

            case S: /* shift */
                operator_stack[++opr_top] = s_rules[n].work_queue[i];
                break;

            case R: /* reduce */

                switch (operator_stack[opr_top]) {

                case t_AND:
                    values_stack[val_top - 1] =
                        f_and(values_stack[val_top], values_stack[val_top - 1],
                              family);
                    val_top--;
                    break;

                case t_OR:
                    values_stack[val_top - 1] =
                        f_or(values_stack[val_top], values_stack[val_top - 1],
                             family);
                    val_top--;
                    break;

                case t_RBRC:
                    opr_top--;
                    break;
                }

                opr_top--;
                i--;
                break;

            case A: /* accept */

                if (!val_top)
                    G_fatal_error("Stack error at end, contact author");
                return values_stack[val_top];
            }
        }

    } while (s_rules[n].work_queue[i++] != t_STOP);

    G_fatal_error("Parse Stack empty, contact author");
}

float defuzzify(int defuzzification, float max_agregate)
{
    int i;
    float d_value = 0;
    float sum_agregate = 0;
    float tmp;

    for (i = 0; i < resolution; sum_agregate += agregate[i++])
        ;

    switch (defuzzification) {

    case d_CENTEROID:
        for (i = 0; i < resolution; ++i)
            d_value += (universe[i] * agregate[i]);
        return d_value / sum_agregate;

    case d_BISECTOR:
        for (i = 0, tmp = 0; (tmp += agregate[i]) < sum_agregate / 2; ++i)
            ;
        return universe[i];

    case d_MINOFHIGHEST:
        for (i = 0; agregate[i] < max_agregate; ++i)
            ;
        return universe[i];

    case d_MAXOFHIGHEST:
        for (i = resolution; agregate[i] < max_agregate; --i)
            ;
        return universe[i];

    case d_MEANOFHIGHEST:
        sum_agregate = 0;
        for (i = 0; i < resolution; ++i) {
            if (agregate[i] < max_agregate)
                continue;
            d_value += (universe[i] * agregate[i]);
            sum_agregate += agregate[i];
        }
        return d_value / sum_agregate;
    }

    return -9999;
}
