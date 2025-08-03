/* grid cache */

struct cache {
    SEGMENT s;
    char *r;
    int n; /* data size per cell in bytes */
    int rows, cols;
    void *(*get)(struct cache *c, void *p, int row, int col);
    void *(*put)(struct cache *c, void *p, int row, int col);
};

int cache_create(struct cache *c, int nrows, int ncols, int srows, int scols,
                 int nbytes, int nseg);
int cache_destroy(struct cache *c);
void *cache_get(struct cache *c, void *p, int row, int col);
void *cache_put(struct cache *c, void *p, int row, int col);
