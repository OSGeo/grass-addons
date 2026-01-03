#ifndef _GLOBAL_H
#define _GLOBAL_H

/* hydrologic condition indices */
enum { HC_POOR = 0, HC_FAIR = 1, HC_GOOD = 2 };

/* antecedent runoff condition indices */
enum { ARC_I = 0, ARC_II = 1, ARC_III = 2 };

struct cn_record {
    int lc;
    int hsg;
    int hc;
    int cn_ii;
};

struct cn_table {
    struct cn_record *recs;
    int n;
    int capacity;
};

/* arc conversion table: cn_ii -> (cn_i, cn_iii) */
struct arc_entry {
    int cn_ii;
    int cn_i;
    int cn_iii;
};

struct arc_table {
    struct arc_entry *entries;
    int n;
    int capacity;
};

/* cn table init/free */
void init_cn_table(struct cn_table *tbl);
void free_cn_table(struct cn_table *tbl);

/* arc table init/free */
void init_arc_table(struct arc_table *tbl);
void free_arc_table(struct arc_table *tbl);

/* lookup tables */
int load_nlcd_lut(struct cn_table *tbl);
int load_esa_lut(struct cn_table *tbl);
int load_custom_lut(struct cn_table *tbl, const char *path);

/* arc conversion table */
int load_builtin_arc(struct arc_table *tbl);

/* lookup cn_ii; returns 1 on success, 0 if no match */
int lookup_lut_cn_ii(const struct cn_table *tbl, int lc, int hsg, int hc_idx,
                     int *cn_ii_out);

/* convert cn_ii to requested arc using table
   returns cn_ii unchanged if not found in table */
int convert_arc_from_table(const struct arc_table *tbl, int cn_ii, int arc_idx);

#endif
