/* lut.c - CN lookup and ARC conversion using embedded lookup tables */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

/* NLCD CN-II lookup table */
static const struct cn_record nlcd_records[] = {
    {11, 1, HC_POOR, 100}, {11, 2, HC_POOR, 100}, {11, 3, HC_POOR, 100},
    {11, 4, HC_POOR, 100}, {11, 1, HC_FAIR, 100}, {11, 2, HC_FAIR, 100},
    {11, 3, HC_FAIR, 100}, {11, 4, HC_FAIR, 100}, {11, 1, HC_GOOD, 100},
    {11, 2, HC_GOOD, 100}, {11, 3, HC_GOOD, 100}, {11, 4, HC_GOOD, 100},
    {12, 1, HC_POOR, 0},   {12, 2, HC_POOR, 0},   {12, 3, HC_POOR, 0},
    {12, 4, HC_POOR, 0},   {12, 1, HC_FAIR, 0},   {12, 2, HC_FAIR, 0},
    {12, 3, HC_FAIR, 0},   {12, 4, HC_FAIR, 0},   {12, 1, HC_GOOD, 0},
    {12, 2, HC_GOOD, 0},   {12, 3, HC_GOOD, 0},   {12, 4, HC_GOOD, 0},
    {21, 1, HC_POOR, 68},  {21, 2, HC_POOR, 79},  {21, 3, HC_POOR, 86},
    {21, 4, HC_POOR, 89},  {21, 1, HC_FAIR, 49},  {21, 2, HC_FAIR, 69},
    {21, 3, HC_FAIR, 79},  {21, 4, HC_FAIR, 84},  {21, 1, HC_GOOD, 39},
    {21, 2, HC_GOOD, 61},  {21, 3, HC_GOOD, 74},  {21, 4, HC_GOOD, 80},
    {22, 1, HC_POOR, 74},  {22, 2, HC_POOR, 86},  {22, 3, HC_POOR, 90},
    {22, 4, HC_POOR, 92},  {22, 1, HC_FAIR, 64},  {22, 2, HC_FAIR, 79},
    {22, 3, HC_FAIR, 86},  {22, 4, HC_FAIR, 89},  {22, 1, HC_GOOD, 55},
    {22, 2, HC_GOOD, 74},  {22, 3, HC_GOOD, 82},  {22, 4, HC_GOOD, 86},
    {24, 1, HC_POOR, 98},  {24, 2, HC_POOR, 98},  {24, 3, HC_POOR, 98},
    {24, 4, HC_POOR, 98},  {24, 1, HC_FAIR, 97},  {24, 2, HC_FAIR, 97},
    {24, 3, HC_FAIR, 97},  {24, 4, HC_FAIR, 97},  {24, 1, HC_GOOD, 95},
    {24, 2, HC_GOOD, 95},  {24, 3, HC_GOOD, 95},  {24, 4, HC_GOOD, 95},
    {31, 1, HC_POOR, 82},  {31, 2, HC_POOR, 87},  {31, 3, HC_POOR, 91},
    {31, 4, HC_POOR, 93},  {31, 1, HC_FAIR, 55},  {31, 2, HC_FAIR, 70},
    {31, 3, HC_FAIR, 80},  {31, 4, HC_FAIR, 85},  {31, 1, HC_GOOD, 45},
    {31, 2, HC_GOOD, 65},  {31, 3, HC_GOOD, 75},  {31, 4, HC_GOOD, 80},
    {41, 1, HC_POOR, 45},  {41, 2, HC_POOR, 66},  {41, 3, HC_POOR, 77},
    {41, 4, HC_POOR, 83},  {41, 1, HC_FAIR, 35},  {41, 2, HC_FAIR, 59},
    {41, 3, HC_FAIR, 72},  {41, 4, HC_FAIR, 78},  {41, 1, HC_GOOD, 30},
    {41, 2, HC_GOOD, 53},  {41, 3, HC_GOOD, 68},  {41, 4, HC_GOOD, 75},
    {42, 1, HC_POOR, 47},  {42, 2, HC_POOR, 68},  {42, 3, HC_POOR, 79},
    {42, 4, HC_POOR, 85},  {42, 1, HC_FAIR, 37},  {42, 2, HC_FAIR, 61},
    {42, 3, HC_FAIR, 74},  {42, 4, HC_FAIR, 80},  {42, 1, HC_GOOD, 30},
    {42, 2, HC_GOOD, 55},  {42, 3, HC_GOOD, 70},  {42, 4, HC_GOOD, 77},
    {43, 1, HC_POOR, 46},  {43, 2, HC_POOR, 67},  {43, 3, HC_POOR, 78},
    {43, 4, HC_POOR, 84},  {43, 1, HC_FAIR, 36},  {43, 2, HC_FAIR, 60},
    {43, 3, HC_FAIR, 73},  {43, 4, HC_FAIR, 79},  {43, 1, HC_GOOD, 30},
    {43, 2, HC_GOOD, 54},  {43, 3, HC_GOOD, 69},  {43, 4, HC_GOOD, 76},
    {51, 1, HC_POOR, 46},  {51, 2, HC_POOR, 65},  {51, 3, HC_POOR, 75},
    {51, 4, HC_POOR, 81},  {51, 1, HC_FAIR, 33},  {51, 2, HC_FAIR, 54},
    {51, 3, HC_FAIR, 68},  {51, 4, HC_FAIR, 75},  {51, 1, HC_GOOD, 30},
    {51, 2, HC_GOOD, 46},  {51, 3, HC_GOOD, 63},  {51, 4, HC_GOOD, 71},
    {52, 1, HC_POOR, 48},  {52, 2, HC_POOR, 67},  {52, 3, HC_POOR, 77},
    {52, 4, HC_POOR, 83},  {52, 1, HC_FAIR, 35},  {52, 2, HC_FAIR, 56},
    {52, 3, HC_FAIR, 70},  {52, 4, HC_FAIR, 77},  {52, 1, HC_GOOD, 30},
    {52, 2, HC_GOOD, 48},  {52, 3, HC_GOOD, 65},  {52, 4, HC_GOOD, 73},
    {71, 1, HC_POOR, 68},  {71, 2, HC_POOR, 79},  {71, 3, HC_POOR, 86},
    {71, 4, HC_POOR, 89},  {71, 1, HC_FAIR, 49},  {71, 2, HC_FAIR, 69},
    {71, 3, HC_FAIR, 79},  {71, 4, HC_FAIR, 84},  {71, 1, HC_GOOD, 39},
    {71, 2, HC_GOOD, 61},  {71, 3, HC_GOOD, 74},  {71, 4, HC_GOOD, 80},
    {72, 1, HC_POOR, 60},  {72, 2, HC_POOR, 75},  {72, 3, HC_POOR, 82},
    {72, 4, HC_POOR, 85},  {72, 1, HC_FAIR, 45},  {72, 2, HC_FAIR, 65},
    {72, 3, HC_FAIR, 75},  {72, 4, HC_FAIR, 80},  {72, 1, HC_GOOD, 35},
    {72, 2, HC_GOOD, 57},  {72, 3, HC_GOOD, 70},  {72, 4, HC_GOOD, 76},
    {73, 1, HC_POOR, 55},  {73, 2, HC_POOR, 70},  {73, 3, HC_POOR, 80},
    {73, 4, HC_POOR, 83},  {73, 1, HC_FAIR, 40},  {73, 2, HC_FAIR, 60},
    {73, 3, HC_FAIR, 72},  {73, 4, HC_FAIR, 78},  {73, 1, HC_GOOD, 30},
    {73, 2, HC_GOOD, 50},  {73, 3, HC_GOOD, 65},  {73, 4, HC_GOOD, 73},
    {74, 1, HC_POOR, 53},  {74, 2, HC_POOR, 68},  {74, 3, HC_POOR, 78},
    {74, 4, HC_POOR, 81},  {74, 1, HC_FAIR, 38},  {74, 2, HC_FAIR, 58},
    {74, 3, HC_FAIR, 70},  {74, 4, HC_FAIR, 76},  {74, 1, HC_GOOD, 30},
    {74, 2, HC_GOOD, 48},  {74, 3, HC_GOOD, 63},  {74, 4, HC_GOOD, 71},
    {81, 1, HC_POOR, 68},  {81, 2, HC_POOR, 79},  {81, 3, HC_POOR, 86},
    {81, 4, HC_POOR, 89},  {81, 1, HC_FAIR, 49},  {81, 2, HC_FAIR, 69},
    {81, 3, HC_FAIR, 79},  {81, 4, HC_FAIR, 84},  {81, 1, HC_GOOD, 30},
    {81, 2, HC_GOOD, 58},  {81, 3, HC_GOOD, 71},  {81, 4, HC_GOOD, 78},
    {82, 1, HC_POOR, 57},  {82, 2, HC_POOR, 73},  {82, 3, HC_POOR, 82},
    {82, 4, HC_POOR, 86},  {82, 1, HC_FAIR, 43},  {82, 2, HC_FAIR, 65},
    {82, 3, HC_FAIR, 76},  {82, 4, HC_FAIR, 82},  {82, 1, HC_GOOD, 32},
    {82, 2, HC_GOOD, 58},  {82, 3, HC_GOOD, 72},  {82, 4, HC_GOOD, 79},
    {90, 1, HC_POOR, 40},  {90, 2, HC_POOR, 60},  {90, 3, HC_POOR, 72},
    {90, 4, HC_POOR, 80},  {90, 1, HC_FAIR, 32},  {90, 2, HC_FAIR, 55},
    {90, 3, HC_FAIR, 68},  {90, 4, HC_FAIR, 75},  {90, 1, HC_GOOD, 30},
    {90, 2, HC_GOOD, 50},  {90, 3, HC_GOOD, 65},  {90, 4, HC_GOOD, 73},
    {95, 1, HC_POOR, 60},  {95, 2, HC_POOR, 75},  {95, 3, HC_POOR, 82},
    {95, 4, HC_POOR, 85},  {95, 1, HC_FAIR, 45},  {95, 2, HC_FAIR, 65},
    {95, 3, HC_FAIR, 75},  {95, 4, HC_FAIR, 80},  {95, 1, HC_GOOD, 30},
    {95, 2, HC_GOOD, 50},  {95, 3, HC_GOOD, 65},  {95, 4, HC_GOOD, 70}};

/* ESA CN-II lookup table */
static const struct cn_record esa_records[] = {
    {10, 1, HC_POOR, 45},  {10, 2, HC_POOR, 66},  {10, 3, HC_POOR, 77},
    {10, 4, HC_POOR, 83},  {10, 1, HC_FAIR, 36},  {10, 2, HC_FAIR, 60},
    {10, 3, HC_FAIR, 73},  {10, 4, HC_FAIR, 79},  {10, 1, HC_GOOD, 30},
    {10, 2, HC_GOOD, 55},  {10, 3, HC_GOOD, 70},  {10, 4, HC_GOOD, 77},
    {20, 1, HC_POOR, 63},  {20, 2, HC_POOR, 77},  {20, 3, HC_POOR, 85},
    {20, 4, HC_POOR, 88},  {20, 1, HC_FAIR, 55},  {20, 2, HC_FAIR, 72},
    {20, 3, HC_FAIR, 81},  {20, 4, HC_FAIR, 86},  {20, 1, HC_GOOD, 49},
    {20, 2, HC_GOOD, 68},  {20, 3, HC_GOOD, 79},  {20, 4, HC_GOOD, 84},
    {30, 1, HC_POOR, 68},  {30, 2, HC_POOR, 79},  {30, 3, HC_POOR, 86},
    {30, 4, HC_POOR, 89},  {30, 1, HC_FAIR, 49},  {30, 2, HC_FAIR, 69},
    {30, 3, HC_FAIR, 79},  {30, 4, HC_FAIR, 84},  {30, 1, HC_GOOD, 39},
    {30, 2, HC_GOOD, 61},  {30, 3, HC_GOOD, 74},  {30, 4, HC_GOOD, 80},
    {40, 1, HC_POOR, 72},  {40, 2, HC_POOR, 81},  {40, 3, HC_POOR, 88},
    {40, 4, HC_POOR, 91},  {40, 1, HC_FAIR, 70},  {40, 2, HC_FAIR, 80},
    {40, 3, HC_FAIR, 87},  {40, 4, HC_FAIR, 90},  {40, 1, HC_GOOD, 67},
    {40, 2, HC_GOOD, 78},  {40, 3, HC_GOOD, 85},  {40, 4, HC_GOOD, 89},
    {50, 1, HC_POOR, 89},  {50, 2, HC_POOR, 92},  {50, 3, HC_POOR, 94},
    {50, 4, HC_POOR, 95},  {50, 1, HC_FAIR, 89},  {50, 2, HC_FAIR, 92},
    {50, 3, HC_FAIR, 94},  {50, 4, HC_FAIR, 95},  {50, 1, HC_GOOD, 89},
    {50, 2, HC_GOOD, 92},  {50, 3, HC_GOOD, 94},  {50, 4, HC_GOOD, 95},
    {60, 1, HC_POOR, 65},  {60, 2, HC_POOR, 79},  {60, 3, HC_POOR, 87},
    {60, 4, HC_POOR, 90},  {60, 1, HC_FAIR, 65},  {60, 2, HC_FAIR, 79},
    {60, 3, HC_FAIR, 87},  {60, 4, HC_FAIR, 90},  {60, 1, HC_GOOD, 65},
    {60, 2, HC_GOOD, 79},  {60, 3, HC_GOOD, 87},  {60, 4, HC_GOOD, 90},
    {70, 1, HC_POOR, 0},   {70, 2, HC_POOR, 0},   {70, 3, HC_POOR, 0},
    {70, 4, HC_POOR, 0},   {70, 1, HC_FAIR, 0},   {70, 2, HC_FAIR, 0},
    {70, 3, HC_FAIR, 0},   {70, 4, HC_FAIR, 0},   {70, 1, HC_GOOD, 0},
    {70, 2, HC_GOOD, 0},   {70, 3, HC_GOOD, 0},   {70, 4, HC_GOOD, 0},
    {80, 1, HC_POOR, 100}, {80, 2, HC_POOR, 100}, {80, 3, HC_POOR, 100},
    {80, 4, HC_POOR, 100}, {80, 1, HC_FAIR, 100}, {80, 2, HC_FAIR, 100},
    {80, 3, HC_FAIR, 100}, {80, 4, HC_FAIR, 100}, {80, 1, HC_GOOD, 100},
    {80, 2, HC_GOOD, 100}, {80, 3, HC_GOOD, 100}, {80, 4, HC_GOOD, 100},
    {90, 1, HC_POOR, 80},  {90, 2, HC_POOR, 80},  {90, 3, HC_POOR, 80},
    {90, 4, HC_POOR, 80},  {90, 1, HC_FAIR, 80},  {90, 2, HC_FAIR, 80},
    {90, 3, HC_FAIR, 80},  {90, 4, HC_FAIR, 80},  {90, 1, HC_GOOD, 80},
    {90, 2, HC_GOOD, 80},  {90, 3, HC_GOOD, 80},  {90, 4, HC_GOOD, 80},
    {95, 1, HC_POOR, 0},   {95, 2, HC_POOR, 0},   {95, 3, HC_POOR, 0},
    {95, 4, HC_POOR, 0},   {95, 1, HC_FAIR, 0},   {95, 2, HC_FAIR, 0},
    {95, 3, HC_FAIR, 0},   {95, 4, HC_FAIR, 0},   {95, 1, HC_GOOD, 0},
    {95, 2, HC_GOOD, 0},   {95, 3, HC_GOOD, 0},   {95, 4, HC_GOOD, 0},
    {100, 1, HC_POOR, 74}, {100, 2, HC_POOR, 77}, {100, 3, HC_POOR, 78},
    {100, 4, HC_POOR, 79}, {100, 1, HC_FAIR, 74}, {100, 2, HC_FAIR, 77},
    {100, 3, HC_FAIR, 78}, {100, 4, HC_FAIR, 79}, {100, 1, HC_GOOD, 74},
    {100, 2, HC_GOOD, 77}, {100, 3, HC_GOOD, 78}, {100, 4, HC_GOOD, 79},
};

/* ARC conversion table */
static const struct arc_entry arc_records[] = {
    {100, 100, 100}, {99, 97, 100}, {98, 94, 99}, {97, 91, 99}, {96, 89, 99},
    {95, 87, 98},    {94, 85, 98},  {93, 83, 98}, {92, 81, 97}, {91, 80, 97},
    {90, 78, 96},    {89, 76, 96},  {88, 75, 95}, {87, 73, 95}, {86, 72, 94},
    {85, 70, 94},    {84, 68, 93},  {83, 67, 93}, {82, 66, 92}, {81, 64, 92},
    {80, 63, 91},    {79, 62, 91},  {78, 60, 90}, {77, 59, 89}, {76, 58, 89},
    {75, 57, 88},    {74, 55, 88},  {73, 54, 87}, {72, 53, 86}, {71, 52, 86},
    {70, 51, 85},    {69, 50, 84},  {68, 48, 84}, {67, 47, 83}, {66, 46, 82},
    {65, 45, 82},    {64, 44, 81},  {63, 43, 80}, {62, 42, 79}, {61, 41, 78},
    {60, 40, 78},    {59, 39, 77},  {58, 38, 76}, {57, 37, 75}, {56, 36, 75},
    {55, 35, 74},    {54, 34, 73},  {53, 33, 72}, {52, 32, 71}, {51, 31, 70},
    {50, 31, 70},    {49, 30, 69},  {48, 29, 68}, {47, 28, 67}, {46, 27, 66},
    {45, 26, 65},    {44, 25, 64},  {43, 25, 63}, {42, 24, 62}, {41, 23, 61},
    {40, 22, 60},    {39, 21, 59},  {38, 21, 58}, {37, 20, 57}, {36, 19, 56},
    {35, 18, 55},    {34, 18, 54},  {33, 17, 53}, {32, 16, 52}, {31, 16, 51},
    {30, 15, 50},    {25, 12, 43},  {20, 9, 37},  {15, 6, 30},  {10, 4, 22},
    {5, 2, 13},      {0, 0, 0},
};

static int parse_hc(const char *s);
static int cn_table_append(struct cn_table *tbl, int lc, int hsg, int hc_idx,
                           int cn_ii);

static int arc_append(struct arc_table *tbl, int cn_ii, int cn_i, int cn_iii);

/* table init / free  */
void init_cn_table(struct cn_table *tbl)
{
    tbl->recs = NULL;
    tbl->n = 0;
    tbl->capacity = 0;
}

void free_cn_table(struct cn_table *tbl)
{
    if (tbl->recs)
        G_free(tbl->recs);
    tbl->recs = NULL;
    tbl->n = 0;
    tbl->capacity = 0;
}

void init_arc_table(struct arc_table *tbl)
{
    tbl->entries = NULL;
    tbl->n = 0;
    tbl->capacity = 0;
}

void free_arc_table(struct arc_table *tbl)
{
    if (tbl->entries)
        G_free(tbl->entries);
    tbl->entries = NULL;
    tbl->n = 0;
    tbl->capacity = 0;
}

/* append helpers */
static int cn_table_append(struct cn_table *tbl, int lc, int hsg, int hc_idx,
                           int cn_ii)
{
    struct cn_record *p;
    int newcap;

    if (tbl->n == tbl->capacity) {
        newcap = tbl->capacity ? tbl->capacity * 2 : 64;
        p = (struct cn_record *)G_realloc(
            tbl->recs, (size_t)newcap * sizeof(struct cn_record));
        if (!p)
            return 0;
        tbl->recs = p;
        tbl->capacity = newcap;
    }

    tbl->recs[tbl->n].lc = lc;
    tbl->recs[tbl->n].hsg = hsg;
    tbl->recs[tbl->n].hc = hc_idx;
    tbl->recs[tbl->n].cn_ii = cn_ii;
    tbl->n++;

    return 1;
}

static int arc_append(struct arc_table *tbl, int cn_ii, int cn_i, int cn_iii)
{
    struct arc_entry *p;
    int newcap;

    if (tbl->n == tbl->capacity) {
        newcap = tbl->capacity ? tbl->capacity * 2 : 64;
        p = (struct arc_entry *)G_realloc(
            tbl->entries, (size_t)newcap * sizeof(struct arc_entry));
        if (!p)
            return 0;
        tbl->entries = p;
        tbl->capacity = newcap;
    }

    tbl->entries[tbl->n].cn_ii = cn_ii;
    tbl->entries[tbl->n].cn_i = cn_i;
    tbl->entries[tbl->n].cn_iii = cn_iii;
    tbl->n++;

    return 1;
}

static int parse_hc(const char *s)
{
    if (G_strcasecmp(s, "poor") == 0)
        return HC_POOR;
    if (G_strcasecmp(s, "fair") == 0)
        return HC_FAIR;
    if (G_strcasecmp(s, "good") == 0)
        return HC_GOOD;
    return -1;
}

/* file-based cn loader for custom csv: lc,hsg,hc,cn */
int load_custom_lut(struct cn_table *tbl, const char *path)
{
    FILE *fp;
    char buf[1024];
    int line_no = 0;
    int loaded = 0;

    fp = fopen(path, "r");
    if (!fp) {
        G_warning(_("Cannot open lookup file <%s>"), path);
        return -1;
    }

    while (G_getl2(buf, sizeof(buf), fp) > 0) {
        char *line = buf;
        int lc, hsg, cn_ii;
        char hc_buf[32];
        int n, hc_idx;

        line_no++;

        G_strip(line);
        if (!*line)
            continue;
        if (*line == '#')
            continue;

        if (line_no == 1 && (strstr(line, "lc") || strstr(line, "hsg") ||
                             strstr(line, "hc") || strstr(line, "cn")))
            continue;

        n = sscanf(line, "%d,%d,%31[^,],%d", &lc, &hsg, hc_buf, &cn_ii);
        if (n != 4) {
            G_warning(_("Invalid lookup line %d in <%s>: '%s'"), line_no, path,
                      line);
            continue;
        }

        hc_idx = parse_hc(hc_buf);
        if (hc_idx < 0) {
            G_warning(_("Invalid hydrologic condition '%s' in <%s> line %d"),
                      hc_buf, path, line_no);
            continue;
        }

        if (!cn_table_append(tbl, lc, hsg, hc_idx, cn_ii)) {
            fclose(fp);
            return -1;
        }
        loaded++;
    }

    fclose(fp);

    if (loaded == 0) {
        G_warning(_("lookup file <%s> contained no usable records"), path);
        return -1;
    }

    return 0;
}

/* public loaders */
int load_nlcd_lut(struct cn_table *tbl)
{
    int i;
    int n = (int)(sizeof(nlcd_records) / sizeof(nlcd_records[0]));

    for (i = 0; i < n; i++) {
        if (!cn_table_append(tbl, nlcd_records[i].lc, nlcd_records[i].hsg,
                             nlcd_records[i].hc, nlcd_records[i].cn_ii))
            return -1;
    }

    return 0;
}

int load_esa_lut(struct cn_table *tbl)
{
    int i;
    int n = (int)(sizeof(esa_records) / sizeof(esa_records[0]));

    for (i = 0; i < n; i++) {
        if (!cn_table_append(tbl, esa_records[i].lc, esa_records[i].hsg,
                             esa_records[i].hc, esa_records[i].cn_ii))
            return -1;
    }

    return 0;
}

int load_builtin_arc(struct arc_table *tbl)
{
    int i;
    int n = (int)(sizeof(arc_records) / sizeof(arc_records[0]));

    for (i = 0; i < n; i++) {
        if (!arc_append(tbl, arc_records[i].cn_ii, arc_records[i].cn_i,
                        arc_records[i].cn_iii))
            return -1;
    }

    return 0;
}

/* resolve dual HSG codes to single codes */
int resolve_dual_hsg(int hsg, int drained)
{
    switch (hsg) {
    case 1:
    case 2:
    case 3:
    case 4:
        return hsg;
    case 11: /* A/D */
        return drained ? 1 : 4;
    case 12: /* B/D */
        return drained ? 2 : 4;
    case 13: /* C/D */
        return drained ? 3 : 4;
    case 14: /* D/D */
        return 4;
    default:
        return -1;
    }
}

/* lookups */
int lookup_lut_cn_ii(const struct cn_table *tbl, int lc, int hsg, int hc_idx,
                     int *cn_ii_out)
{
    int i;

    for (i = 0; i < tbl->n; i++) {
        const struct cn_record *r = &tbl->recs[i];
        if (r->lc == lc && r->hsg == hsg && r->hc == hc_idx) {
            *cn_ii_out = r->cn_ii;
            return 1;
        }
    }

    return 0;
}

/* table-based arc conversion:
   if cn_ii exists: return corresponding arc_i/ii/iii if not: return cn_ii
*/
int convert_arc_from_table(const struct arc_table *tbl, int cn_ii, int arc_idx)
{
    int i;

    if (cn_ii <= 0)
        return cn_ii;

    for (i = 0; i < tbl->n; i++) {
        const struct arc_entry *e = &tbl->entries[i];
        if (e->cn_ii == cn_ii) {
            switch (arc_idx) {
            case ARC_I:
                return e->cn_i;
            case ARC_II:
                return e->cn_ii;
            case ARC_III:
                return e->cn_iii;
            default:
                G_fatal_error(_("invalid arc index %d"), arc_idx);
            }
        }
    }

    return cn_ii;
}
