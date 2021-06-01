#ifndef GISDEFS_H
#define GISDEFS_H

#define G_JOIN_ELEMENT_TYPE 0x1
#define G_JOIN_ELEMENT_MAPSET 0x2

/* join.c */
const char *G_join_element(const char *, const char *, const char *,
			   const char *, int, int *);

/* ls.c */
void G_set_ls_filter(int (*)(const char *, void *), void *);
char **G__ls(const char *, int *);

#endif
