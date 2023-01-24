#include "local_proto.h"

int parseToken(int *res, int pos, char *token)
{
    char begin[GNAME_MAX];
    char end[GNAME_MAX];
    char *c, *tb, *te;
    int i, count;

    /* clear begin and end */
    memset(begin, 0, GNAME_MAX);
    memset(end, 0, GNAME_MAX);

    c = token;
    tb = begin;
    while (*c != '-' && *c != 0) {
        *tb = *c;
        c++;
        tb++;
    }
    G_strip(begin);

    if (*c == 0) {
        res[pos] = atoi(begin);
        return 1;
    }
    c++;

    te = end;
    while (*c != 0) {
        *te = *c;
        c++;
        te++;
    }

    G_strip(end);

    for (i = atoi(begin), count = 0; i <= atoi(end); i++, count++) {
        res[pos + count] = i;
    }
    return count;
}

int parseInput(int *res, char *input)
{
    char token[GNAME_MAX];
    char *c, *t;
    int actPos = 0;

    c = input;
    while (*c != 0) {
        /* clear token */
        memset(token, 0, GNAME_MAX);
        t = token;

        /* read token */
        while (*c != ',' && *c != 0) {
            *t = *c;
            c++;
            t++;
        }
        c++;

        actPos += parseToken(res, actPos, token);
    }

    return actPos;
}
