#include <grass/gis.h>
#include <grass/glocale.h>

struct list
{
    char **element;		/* list of related elements */
    char *alias;		/* element alias */
    char **desc;		/* description of elements */
    char *text;			/* menu text */
    int nelem;			/* number of elements */
    char status;
    char *mainelem;		/* main element */
    char *maindesc;		/* main element description */
};

/* read_list.c */
int read_list(int);

/* wc2regex.c */
char *wc2regex(const char *);

/* check_reclass.c */
int check_reclass(const char *, const char *, int);

/* sighold.c */
int hold_signals(int);

/* do_remove.c */
int do_remove(int, char *);

#ifdef MAIN
#	define GLOBAL
#else
#	define GLOBAL extern
#endif

GLOBAL int nlist;
GLOBAL struct list *list;
