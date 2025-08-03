struct ncb /* neighborhood control block */
{
    DCELL **buf1, **buf2; /* for reading cell file */
    int *value;           /* neighborhood values */
    int nsize;            /* size of the neighborhood */
    int dist;             /* nsize/2 */
    struct Categories cats;
    char title[1024];
    FILE *out;
    struct {
        char *name;
        const char *mapset;
    } oldcell1, oldcell2, newcell;
};

extern struct ncb ncb;
