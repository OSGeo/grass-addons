#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

void init_line_list(struct line_list *ll)
{
    ll->nalloc = ll->n = 0;
    ll->lines = NULL;
}

void reset_line_list(struct line_list *ll)
{
    free_line_list(ll);
}

void free_line_list(struct line_list *ll)
{
    if (ll->lines) {
        int i;

        for (i = 0; i < ll->n; i++)
            Vect_destroy_line_struct(ll->lines[i]->Points);
        G_free(ll->lines);
    }
    init_line_list(ll);
}

/* adapted from r.path */
void add_line(struct line_list *ll, struct line *l)
{
    if (ll->n == ll->nalloc) {
        ll->nalloc += REALLOC_INCREMENT;
        ll->lines = (struct line **)G_realloc(
            ll->lines, ll->nalloc * sizeof(struct line *));
        if (!ll->lines)
            G_fatal_error(_("Unable to increase line list"));
    }
    ll->lines[ll->n] = l;
    ll->n++;
}
